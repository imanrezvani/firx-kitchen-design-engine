"""Deterministic cabinet component (cut-part) derivation.

Every cabinet is decomposed into manufactured parts — case sides, top/bottom,
back, shelves, drawer boxes, doors, toe kick, fillers. Each part carries the
data a cut list needs: material, dimensions, qty, grain and the edge banding
spec, which is *derived from exposure* (which edges are visible after
accounting for end panels, adjacency and wall contact).

Parts are pure functions of the Cabinet model, resolved through the cabinet
type registry (app.design.cabinet_types). They are computed, never stored, so
a single edit flows through to the cut list, sheet count and BOM
(see docs/firx-parametric-model.md §4.5, §10).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.design.cabinet_types import resolve_interior, spec_for
from app.design.parametric import Cabinet

DOOR_THK = 18      # door/drawer-front thickness (sheet good)
SHELF_THK = 18     # shelf thickness (may be overridden by resolve_interior
                   # box_thickness in future; kept distinct for open shelves)
DRAWER_THK = 16    # drawer box thickness


@dataclass(frozen=True)
class CutPart:
    cabinet_id: str
    cabinet_label: str
    part_name: str          # e.g. "Left Side"
    kind: str               # side|top|bottom|back|shelf|drawer_box|door|toe_kick|filler
    material_key: str | None
    thickness_mm: int
    width_mm: int           # in-material width (across the face)
    length_mm: int          # in-material length
    qty: int
    grain: str              # vertical|horizontal|any
    edge_banding: list[str]  # exposed faces: front/left/right/etc.


def _doors_for(cab: Cabinet) -> int:
    return resolve_interior(cab).door_count


def _drawers_for(cab: Cabinet) -> int:
    return resolve_interior(cab).drawer_count


def _shelves_for(cab: Cabinet) -> int:
    return resolve_interior(cab).shelf_count


def derive_components(cab: Cabinet) -> list[CutPart]:
    """Decompose a cabinet into cut parts with grain and edge banding.

    Geometry conventions (mm):
      - carcass depth is the cabinet depth; sides are depth × height,
        top/bottom are (width - 2×thk) × depth
      - back is (width - 2×thk) × (height - 2×thk)
      - doors cover the full front; drawer fronts/bodies are sized per drawer
      - a toe kick adds a single front board for floor cabinets
    Edge banding is derived from exposure: the front is always banded (unless
    a door covers it), and each side is banded unless the box has an end panel
    or sits against a wall/neighbour.
    """
    interior = resolve_interior(cab)
    w, h, d = cab.width_mm, cab.height_mm, cab.depth_mm
    t = interior.box_thickness
    label = cab.name or "کابینت"
    spec = spec_for(cab.type)

    # non-structural fillers produce no cut parts.
    if cab.type == "filler":
        return []

    # exposed sides: banded when no end panel is declared on that side.
    end_l = getattr(cab, "end_panel_left", None) or "not_exposed"
    end_r = getattr(cab, "end_panel_right", None) or "not_exposed"
    band_l = end_l == "not_exposed"
    band_r = end_r == "not_exposed"

    parts: list[CutPart] = []

    def add(kind, name, thickness, width_mm, length_mm, qty, grain, edges):
        parts.append(CutPart(
            cabinet_id=cab.id,
            cabinet_label=label,
            part_name=name,
            kind=kind,
            material_key=cab.material_name or cab.material_id,
            thickness_mm=thickness,
            width_mm=width_mm,
            length_mm=length_mm,
            qty=qty,
            grain=grain,
            edge_banding=sorted(set(edges)),
        ))

    is_wall = spec.group == "wall"

    # case
    if not is_wall:
        add("side", "Left Side", t, d, h, 1, "horizontal",
            ["front"] + (["left"] if band_l else []))
        add("side", "Right Side", t, d, h, 1, "horizontal",
            ["front"] + (["right"] if band_r else []))
    add("top", "Top", t, w - 2 * t, d, 1, "any",
        ["front"] + (["left", "right"] if not is_wall else []))
    add("bottom", "Bottom", t, w - 2 * t, d, 1, "any",
        ["front"] + (["left", "right"] if not is_wall else []))

    # back
    add("back", "Back", interior.back_thickness, w - 2 * t, h - 2 * t, 1, "any", [])

    # shelves (adjustable → grain any, thin banded front)
    shelves = interior.shelf_count
    if shelves:
        add("shelf", "Shelf", SHELF_THK, w - 2 * t, d - 2 * t, shelves, "any", ["front"])

    # doors
    doors = interior.door_count
    if doors:
        door_w = w // doors
        add("door", "Door", DOOR_THK, door_w, h, doors, "vertical", ["front", "left", "right"])

    # drawers
    drawers = interior.drawer_count
    if drawers:
        add("drawer_box", "Drawer Box", DRAWER_THK, w - 2 * t, d - 4, drawers, "any", ["front"])
        add("drawer_front", "Drawer Front", DOOR_THK, w - 2, h // drawers - 2, drawers, "vertical", ["front", "left", "right"])

    # toe kick (floor cabinets only, per type registry)
    if interior.toe_kick_height > 0 and not is_wall:
        add("toe_kick", "Toe Kick", t, w - 2 * t, interior.toe_kick_height, 1, "any", ["front"])

    return parts


def aggregate_parts(cabinets: list[Cabinet], labels: dict[str, str] | None = None) -> list[dict]:
    """Flatten component derivation across cabinets into BOM rows.

    ``labels`` maps cabinet id -> cut-list label (e.g. "B1"); when omitted,
    parts carry the cabinet's name. Each row carries a stable part identifier
    "<cabinet-label>.<part-name>" (e.g. "B1.Left Side") matching the cut-list
    convention.
    """
    labels = labels or {}
    rows: list[dict] = []
    for cab in cabinets:
        for p in derive_components(cab):
            clabel = labels.get(cab.id, p.cabinet_label)
            rows.append({
                "id": f"{clabel}.{p.part_name}",
                "cabinet": clabel,
                "part": p.part_name,
                "kind": p.kind,
                "material": p.material_key,
                "thickness_mm": p.thickness_mm,
                "width_mm": p.width_mm,
                "length_mm": p.length_mm,
                "qty": p.qty,
                "grain": p.grain,
                "edge_banding": p.edge_banding,
            })
    return rows


def sheet_count(cabinets: list[Cabinet], sheet_w_mm: int = 1220, sheet_h_mm: int = 2440) -> dict:
    """Minimum sheet count from a shelf-based bin pack per thickness.

    This is a conservative estimate (no grain-locked nesting yet). It replaces
    the previous front-face-only area heuristic with real part footprints.
    """
    by_thickness: dict[int, list[tuple[int, int, int]]] = {}
    for cab in cabinets:
        for p in derive_components(cab):
            pw, ph = p.width_mm, p.length_mm
            if pw <= 0 or ph <= 0:
                continue
            rotatable = p.grain != "vertical"
            by_thickness.setdefault(p.thickness_mm, []).append((pw, ph, 1 if rotatable else 0))

    total_m2 = 0.0
    sheets_by_thk: dict[int, int] = {}
    for thk, parts in by_thickness.items():
        total_m2 += sum((pw * ph) / 1_000_000 for pw, ph, _ in parts)
        sheets_by_thk[thk] = _bin_pack_sheets(parts, sheet_w_mm, sheet_h_mm)
    return {
        "total_m2": round(total_m2, 2),
        "sheets_by_thickness": sheets_by_thk,
        "total_sheets": sum(sheets_by_thk.values()),
    }


def _bin_pack_sheets(parts: list[tuple[int, int, int]], sheet_w: int, sheet_h: int) -> int:
    """Shelf-based first-fit bin pack. Returns the sheet count.

    Sort parts by descending height and pack left-to-right along the current
    shelf, starting a new shelf row (on the same or a new sheet) when the row
    is full. Parts marked non-rotatable (grain vertical) are not flipped.
    """
    if not parts:
        return 0
    items = sorted(parts, key=lambda p: -max(p[0], p[1]))
    sheets: list[list[tuple[int, int, int, int]]] = [[]]

    def try_place(sheet_rects: list[tuple[int, int, int, int]], w: int, h: int) -> bool:
        """Place w×h into the first open shelf row that fits, else a new row."""
        rows: dict[int, int] = {}
        for rx, ry, rw, rh in sheet_rects:
            rows[ry] = max(rows.get(ry, 0), rx + rw)
        # attempt existing rows
        for y, x in sorted(rows.items()):
            if x + w <= sheet_w and y + h <= sheet_h:
                sheet_rects.append((x, y, w, h))
                return True
        # start a new shelf row on the lowest free band
        if sheet_rects:
            max_y = max(ry + rh for _, ry, _, rh in sheet_rects)
            if w <= sheet_w and max_y + h <= sheet_h:
                sheet_rects.append((0, max_y, w, h))
                return True
        return False

    for pw, ph, rotatable in items:
        placed = False
        for sheet_rects in sheets:
            for w, h in ((pw, ph), (ph, pw)) if rotatable else ((pw, ph),):
                if w > sheet_w or h > sheet_h:
                    continue
                if try_place(sheet_rects, w, h):
                    placed = True
                    break
            if placed:
                break
        if not placed:
            sheets.append([(0, 0, pw, ph)])
    return len(sheets)
