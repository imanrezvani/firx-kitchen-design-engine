"""Deterministic hardware derivation for a parametric design.

Hardware counts are pure functions of the cabinet model (type, width, and
optional door/drawer/shelf configuration). They are computed, never stored,
so a single edit to the kitchen flows through to hinges, slides, pins, pulls
and the BOM automatically (see docs/firx-parametric-model.md §11).

Default per-unit costs are estimates used when a tenant has not configured a
hardware library. A unit price of 0.0 suppresses the line item.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.design.cabinet_types import resolve_interior
from app.design.parametric import Cabinet, DesignModel

# ---------------------------------------------------------------------------
# Default per-unit costs (estimated; overridable by a future hardware library)
# ---------------------------------------------------------------------------
HINGE_COST = 3.5          # soft-close 110° hinge
SLIDE_COST = 12.0         # undermount soft-close slide (pair)
PULL_COST = 2.0           # standard pull
SHELF_PIN_COST = 0.2      # 5mm/7mm shelf pin

# Cabinet types that carry doors by default (used only when door_config is
# unset and the type registry has no explicit default).
_DOOR_TYPES = {
    "base", "sink", "oven", "tall", "wall", "corner",
    "pantry", "wardrobe", "fridge", "vanity", "linen",
}
# Cabinet types that carry drawers by default.
_DRAWER_TYPES = {"base", "drawer"}


def _doors_for(cab: Cabinet) -> int:
    return resolve_interior(cab).door_count


def _drawers_for(cab: Cabinet) -> int:
    return resolve_interior(cab).drawer_count


def _shelves_for(cab: Cabinet) -> int:
    return resolve_interior(cab).shelf_count


@dataclass(frozen=True)
class HardwareLine:
    code: str
    name_fa: str
    qty: int
    unit_price: float
    cost: float
    cabinet_id: str


def derive_cabinet_hardware(cab: Cabinet) -> list[HardwareLine]:
    """Hardware lines for one cabinet.

    Rules (documented in docs/firx-parametric-model.md §4.5, §8):
      - hinges   = 2 per door
      - slides   = 1 pair per drawer
      - pins     = 4 per adjustable shelf
      - pulls    = 1 per door + 1 per drawer front
    """
    lines: list[HardwareLine] = []
    doors = _doors_for(cab)
    drawers = _drawers_for(cab)
    shelves = _shelves_for(cab)
    if doors:
        lines.append(HardwareLine(
            code="HINGE", name_fa="لولا", qty=doors * 2,
            unit_price=HINGE_COST, cost=doors * 2 * HINGE_COST,
            cabinet_id=cab.id,
        ))
    if drawers:
        lines.append(HardwareLine(
            code="SLIDE", name_fa="ریل کشو", qty=drawers,
            unit_price=SLIDE_COST, cost=drawers * SLIDE_COST,
            cabinet_id=cab.id,
        ))
    if shelves:
        lines.append(HardwareLine(
            code="PIN", name_fa="پین طبقه", qty=shelves * 4,
            unit_price=SHELF_PIN_COST, cost=shelves * 4 * SHELF_PIN_COST,
            cabinet_id=cab.id,
        ))
    pulls = doors + drawers
    if pulls:
        lines.append(HardwareLine(
            code="PULL", name_fa="دستگیره", qty=pulls,
            unit_price=PULL_COST, cost=pulls * PULL_COST,
            cabinet_id=cab.id,
        ))
    return lines


def derive_hardware_breakdown(design: DesignModel) -> dict:
    """Aggregated hardware breakdown across all cabinets in the design.

    Returns a dict with per-code rows and a total, suitable for the BOM.
    """
    aggregate: dict[str, HardwareLine] = {}
    for cab in design.cabinets:
        for line in derive_cabinet_hardware(cab):
            if line.code in aggregate:
                agg = aggregate[line.code]
                aggregate[line.code] = HardwareLine(
                    code=line.code,
                    name_fa=line.name_fa,
                    qty=agg.qty + line.qty,
                    unit_price=line.unit_price,
                    cost=round(agg.cost + line.cost, 2),
                    cabinet_id="",
                )
            else:
                aggregate[line.code] = line

    rows = [
        {
            "code": l.code,
            "name": l.name_fa,
            "qty": l.qty,
            "unit_price": l.unit_price,
            "total_price": round(l.cost, 2),
        }
        for l in sorted(aggregate.values(), key=lambda x: -x.cost)
    ]
    return {
        "items": rows,
        "total": round(sum(l.cost for l in aggregate.values()), 2),
    }
