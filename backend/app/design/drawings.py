"""Technical-drawing derivation from the parametric model.

Produces plan-view and per-wall-run elevation geometry as pure functions of
the DesignModel — no 3D/rendering engine involved. Everything a shop drawing
needs (cabinet outlines, per-cabinet dimensions and labels, run extents) is
derived from the source of truth (see docs/firx-parametric-model.md §10).

Drawings are *derived views*: they hold no authoritative state. A later PDF /
DXF exporter only needs to serialize these structures.
"""

from __future__ import annotations

from app.design.cabinet_types import spec_for
from app.design.derive import number_cabinets
from app.design.parametric import Cabinet, DesignModel

WALL_ORDER = ["north", "east", "south", "west"]


def plan_geometry(design: DesignModel) -> dict:
    """Plan (top-down) view: room outline, every cabinet's rect + label, plus
    openings and appliance positions (from the same parametric model)."""
    labels = number_cabinets(design)
    cabinets = []
    for c in design.cabinets:
        fw, fd = _footprint(c)
        cabinets.append({
            "id": c.id,
            "label": labels.get(c.id, c.name),
            "x": round(c.x, 1),
            "y": round(c.y, 1),
            "w": fw,
            "d": fd,
            "rotation": c.rotation,
            "type": c.type,
        })
    return {
        "room": {
            "width_mm": design.room.width_mm,
            "length_mm": design.room.length_mm,
            "height_mm": design.room.height_mm,
        },
        "cabinets": cabinets,
        "openings": [
            {
                "id": o.id,
                "kind": o.kind,
                "wall": o.wall,
                "position_mm": o.position_mm,
                "width_mm": o.width_mm,
                "height_mm": o.height_mm,
                "sill_height_mm": o.sill_height_mm,
            }
            for o in design.room.openings
        ],
        "appliances": [
            {
                "id": a.id,
                "type": a.appliance_type,
                "name": a.name or a.appliance_type,
                "x": round(a.x, 1),
                "y": round(a.y, 1),
                "w": a.width_mm,
                "d": a.depth_mm,
                "rotation": a.rotation,
            }
            for a in design.appliances
        ],
    }


def run_elevations(design: DesignModel) -> list[dict]:
    """Front elevations, one sheet per wall run.

    Cabinets are projected onto their run wall and sorted along the wall axis.
    Each elevation entry carries the cabinet label, its along-wall offset and
    width, height, bottom offset (z) and opening summary — everything a
    dimensioned elevation drawing needs.
    """
    labels = number_cabinets(design)
    runs: dict[str, list[dict]] = {w: [] for w in WALL_ORDER}
    for c in design.cabinets:
        wall = _wall_of(c)
        if wall is None:
            continue
        along, depth = _along_and_depth(c)
        runs[wall].append({
            "id": c.id,
            "label": labels.get(c.id, c.name),
            "type": c.type,
            "along_mm": round(along, 1),
            "width_mm": _footprint(c)[0],
            "height_mm": c.height_mm,
            "depth_mm": depth,
            "z_mm": int(c.z),
            "door_config": _resolved_door_config(c),
            "doors": _door_count(c),
            "drawers": _drawer_count(c),
            "shelves": _shelf_count(c),
        })

    sheets = []
    for wall in WALL_ORDER:
        cabs = runs[wall]
        if not cabs:
            continue
        cabs.sort(key=lambda e: e["along_mm"])
        sheets.append({"wall": wall, "cabinets": cabs})
    return sheets


def _footprint(c: Cabinet) -> tuple[int, int]:
    if c.rotation in (90, 270):
        return c.depth_mm, c.width_mm
    return c.width_mm, c.depth_mm


def _wall_of(c: Cabinet) -> str | None:
    r = c.rotation
    if r == 0:
        return "north"
    if r == 180:
        return "south"
    if r == 270:
        return "west"
    if r == 90:
        return "east"
    return None


def _along_and_depth(c: Cabinet) -> tuple[float, int]:
    """(along-wall offset, depth into room) for a cabinet on its run wall."""
    fw, fd = _footprint(c)
    r = c.rotation
    if r in (0, 180):
        return c.x, fd
    return c.y, fd


def _resolved_door_config(c: Cabinet) -> str:
    from app.design.cabinet_types import resolve_interior
    return resolve_interior(c).door_config


def _door_count(c: Cabinet) -> int:
    from app.design.cabinet_types import resolve_interior
    return resolve_interior(c).door_count


def _drawer_count(c: Cabinet) -> int:
    from app.design.cabinet_types import resolve_interior
    return resolve_interior(c).drawer_count


def _shelf_count(c: Cabinet) -> int:
    from app.design.cabinet_types import resolve_interior
    return resolve_interior(c).shelf_count
