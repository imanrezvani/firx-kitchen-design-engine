"""Design-level derivation bundle: numbering, materials, AI prompts.

Everything here is a pure function of the parametric DesignModel — it is the
layer that lets the *same* model feed costing, technical drawings, cabinet
numbering, material estimation and AI-visualization prompts without any
duplication of state (see docs/firx-parametric-model.md §10, §13).
"""

from __future__ import annotations

from app.bom.components import aggregate_parts, derive_components, sheet_count
from app.design.cabinet_types import spec_for
from app.design.parametric import DesignModel

# ---------------------------------------------------------------------------
# Cabinet numbering (B1, B2, W1, T1 …)
# ---------------------------------------------------------------------------
def number_cabinets(design: DesignModel) -> dict[str, str]:
    """Assign stable cut-list labels per cabinet group.

    Labels are "<PREFIX><ordinal>" where the prefix comes from the cabinet
    type registry (B=base, W=wall, T=tall, V=vanity, I=island, F=filler) and
    the ordinal counts per group in design order. Used by the cut list, BOM,
    drawings and labels so every artifact refers to the same cabinet.
    """
    counters: dict[str, int] = {}
    labels: dict[str, str] = {}
    for cab in design.cabinets:
        prefix = spec_for(cab.type).label_prefix
        counters[prefix] = counters.get(prefix, 0) + 1
        labels[cab.id] = f"{prefix}{counters[prefix]}"
    return labels


# ---------------------------------------------------------------------------
# Material estimation (feeds costing + buying guides)
# ---------------------------------------------------------------------------
def material_estimate(design: DesignModel) -> list[dict]:
    """Per-material sheet-good consumption from cut parts.

    Aggregates part area by material key and thickness, plus the sheet count
    from the bin packer. This is the same cut-list-derived number the costing
    engine will multiply by material price (see docs §8, §9).
    """
    parts = aggregate_parts(design.cabinets)
    by_mat: dict[tuple[str | None, int], dict] = {}
    for p in parts:
        key = (p["material"], p["thickness_mm"])
        row = by_mat.setdefault(key, {
            "material": p["material"],
            "thickness_mm": p["thickness_mm"],
            "area_m2": 0.0,
            "parts": 0,
        })
        row["area_m2"] += (p["width_mm"] * p["length_mm"] * p["qty"]) / 1_000_000
        row["parts"] += p["qty"]
    for row in by_mat.values():
        row["area_m2"] = round(row["area_m2"], 2)
    return sorted(by_mat.values(), key=lambda r: -r["area_m2"])


def sheet_usage(design: DesignModel) -> dict:
    """Sheet-level material summary (used by the cut planner)."""
    return sheet_count(design.cabinets)


# ---------------------------------------------------------------------------
# AI visualization prompt (derived, not stored)
# ---------------------------------------------------------------------------
def build_visual_prompt(design: DesignModel) -> str:
    """A structured, model-derived prompt for AI visualization.

    Everything in the prompt is read from the parametric model — room
    dimensions, layout, cabinet run, door/drawer counts, finishes, appliances
    and countertops. The image generator never becomes a source of truth; it
    is fed by the model and its output is only a view.
    """
    labels = number_cabinets(design)
    room = design.room
    lines = [
        f"آشپزخانه با ابعاد {room.width_mm}×{room.length_mm}×{room.height_mm} میلی‌متر",
        f"چیدمان: {design.name}",
    ]

    by_wall: dict[str, list] = {}
    for cab in design.cabinets:
        wall = _cabinet_wall(cab)
        by_wall.setdefault(wall, []).append(cab)

    if by_wall:
        for wall, cabs in sorted(by_wall.items()):
            names = ", ".join(f"{labels.get(c.id, c.name)}" for c in cabs)
            lines.append(f"خط {wall}: {names}")

    front = []
    for cab in design.cabinets:
        desc = _cabinet_description(cab, labels.get(cab.id, cab.name))
        if desc:
            front.append(desc)
    if front:
        lines.append("کابینت‌ها: " + "؛ ".join(front))

    if design.appliances:
        apps = ", ".join(
            f"{a.name or a.appliance_type}" for a in design.appliances
        )
        lines.append(f"لوازم: {apps}")

    if design.countertops:
        tops = ", ".join(
            f"صفحه {c.width_mm}×{c.depth_mm} ({c.material_name or 'کورین'})"
            for c in design.countertops
        )
        lines.append(f"صفحه‌ها: {tops}")

    lines.append("نمای داخلی مدرن، نورپردازی زیر کابینت، رندر واقع‌گرایانه")
    return "\n".join(lines)


def _cabinet_wall(cab) -> str:
    """Coarse wall placement label for grouping cabinets in a prompt."""
    r = cab.rotation
    if r == 0:
        return "شمال"
    if r == 180:
        return "جنوب"
    if r == 270:
        return "غرب"
    return "شرق"


def _cabinet_description(cab, label: str) -> str:
    """Human-readable single-cabinet description derived from its params."""
    spec = spec_for(cab.type)
    bits = [label, spec.group, f"{cab.width_mm}×{cab.height_mm}×{cab.depth_mm}"]
    if cab.door_config and cab.door_config != "none":
        bits.append({"single": "تک‌در", "double": "دو‌در", "lift_up": "درب بالارو",
                     "split": "درب دولایه", "drawers_top": "کشو بالا + درب"}.get(
            cab.door_config, cab.door_config))
    if (cab.drawer_count or 0) > 0:
        bits.append(f"{cab.drawer_count} کشو")
    if (cab.shelf_count or 0) > 0:
        bits.append(f"{cab.shelf_count} طبقه")
    if cab.appliance_hook:
        bits.append(f"هماهنگ با {cab.appliance_hook}")
    if cab.material_name:
        bits.append(cab.material_name)
    return " ".join(bits)
