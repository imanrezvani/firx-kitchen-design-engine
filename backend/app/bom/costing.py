"""Deterministic costing engine, derived from the parametric/BOM model.

Cost is a pure function of the DesignModel's derived outputs (material
estimate, hardware breakdown, cut parts, sheet usage, cabinet counts) combined
with a *configurable* PricingConfig. Business prices never live in the design
engine — they are supplied here as config, overridable per project
(see docs/firx-parametric-model.md §9).

Chain:
  material_estimate + sheet_usage ─► materials cost
  hardware breakdown             ─► hardware cost
  cut parts (edge banding)       ─► edge banding cost
  cabinet counts by type         ─► labor (machining/assembly/finishing/install)
  appliances + countertops       ─► purchased/installed items
  overhead% + contingency% + margin% + tax% + delivery ─► retail price
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.bom.components import derive_components
from app.bom.hardware import derive_hardware_breakdown
from app.design.cabinet_types import spec_for
from app.design.derive import material_estimate, sheet_usage
from app.design.parametric import DesignModel

# ---------------------------------------------------------------------------
# Config (defaults are sensible estimates; per-project overrides supported)
# ---------------------------------------------------------------------------
class PricingConfig(BaseModel):
    """Configurable pricing inputs. Nothing here is hard-coded in the engine."""

    # materials: price per square metre keyed by material name/code.
    # Keys are matched case-insensitively; a default covers unknown materials.
    material_price_per_sqm: dict[str, float] = Field(default_factory=dict)
    default_material_price_per_sqm: float = 180_000.0  # تومان
    # hardware unit prices (codes from app/bom/hardware.py)
    hinge_price: float = 25_000.0
    slide_price: float = 90_000.0       # per pair
    pull_price: float = 15_000.0
    shelf_pin_price: float = 1_500.0
    # edge banding price per linear metre
    edge_banding_price_per_m: float = 8_000.0
    # accessories: per-cabinet allowance (organizers, baskets, ...)
    accessories_per_cabinet: float = 20_000.0
    # countertop price per sqm; appliances come from the catalog
    countertop_price_per_sqm: float = 1_200_000.0

    # labour: hours by cabinet group (base/wall/tall)
    labor_hours_by_group: dict[str, float] = Field(default_factory=lambda: {
        "base": 2.5, "wall": 1.5, "tall": 3.5,
    })
    machining_rate: float = 350_000.0   # تومان/hour
    assembly_rate: float = 320_000.0
    finishing_rate: float = 280_000.0
    install_rate: float = 300_000.0

    # markup / margin / tax
    waste_pct: float = 12.0
    overhead_pct: float = 15.0
    contingency_pct: float = 5.0
    margin_pct: float = 35.0
    material_tax_pct: float = 9.0
    delivery_fee: float = 500_000.0

    # optional raw catalog costs (appliances) injected from the tenant DB
    appliance_prices: dict[str, float] = Field(default_factory=dict)


DEFAULT_CONFIG = PricingConfig()


# ---------------------------------------------------------------------------
# Cost derivation
# ---------------------------------------------------------------------------
def _material_lookup(name: str | None, cfg: PricingConfig) -> float:
    if name:
        key = name.strip().lower()
        for k, v in cfg.material_price_per_sqm.items():
            if k.strip().lower() == key:
                return v
    return cfg.default_material_price_per_sqm


def _edge_banding_meters(design: DesignModel) -> float:
    """Total linear metres of edge banding from cut parts.

    For each banded edge of a part, the banded length is the face dimension
    the edge runs along: front/back edges run along the part width, left/right
    edges along the part length (see app/bom/components.py geometry notes).
    """
    total = 0.0
    for cab in design.cabinets:
        for p in derive_components(cab):
            for edge in p.edge_banding:
                length = p.width_mm if edge in ("front", "back") else p.length_mm
                total += length * p.qty
    return total / 1000.0


def derive_cost(
    design: DesignModel,
    cfg: PricingConfig | None = None,
    appliance_prices: dict[str, float] | None = None,
) -> dict:
    """Compute the full cost/quote breakdown for a design.

    Returns line items, subtotals, margin/overhead/tax and the final retail
    price plus price-per-linear-metre. Deterministic: same design + config
    always yields the same numbers.
    """
    cfg = cfg or DEFAULT_CONFIG
    if appliance_prices:
        cfg = cfg.model_copy(update={"appliance_prices": appliance_prices})

    # --- materials ---------------------------------------------------------
    mat_rows = material_estimate(design)
    materials_cost = 0.0
    materials_items = []
    for r in mat_rows:
        price = _material_lookup(r["material"], cfg)
        cost = r["area_m2"] * price * (1 + cfg.waste_pct / 100.0)
        materials_cost += cost
        materials_items.append({
            "material": r["material"],
            "thickness_mm": r["thickness_mm"],
            "area_m2": r["area_m2"],
            "unit_price": round(price, 2),
            "total_price": round(cost, 2),
        })

    # --- hardware ----------------------------------------------------------
    hw = derive_hardware_breakdown(design)
    prices = {
        "HINGE": cfg.hinge_price,
        "SLIDE": cfg.slide_price,
        "PULL": cfg.pull_price,
        "PIN": cfg.shelf_pin_price,
    }
    hardware_cost = 0.0
    hardware_items = []
    for item in hw["items"]:
        cost = item["qty"] * prices.get(item["code"], 0.0)
        hardware_cost += cost
        hardware_items.append({
            "code": item["code"],
            "name": item["name"],
            "qty": item["qty"],
            "unit_price": prices.get(item["code"], 0.0),
            "total_price": round(cost, 2),
        })

    # --- edge banding ------------------------------------------------------
    band_m = _edge_banding_meters(design)
    edge_banding_cost = band_m * cfg.edge_banding_price_per_m

    # --- accessories -------------------------------------------------------
    n_cab = len(design.cabinets)
    accessories_cost = n_cab * cfg.accessories_per_cabinet

    # --- labour ------------------------------------------------------------
    hours_by_group: dict[str, float] = {}
    for cab in design.cabinets:
        group = spec_for(cab.type).group
        hours_by_group[group] = hours_by_group.get(group, 0.0) + cfg.labor_hours_by_group.get(group, 2.0)
    machining_h = hours_by_group.get("base", 0.0) + hours_by_group.get("tall", 0.0)
    assembly_h = sum(hours_by_group.values())
    finishing_h = n_cab * 0.75
    install_h = n_cab * 0.5
    machining_cost = machining_h * cfg.machining_rate
    assembly_cost = assembly_h * cfg.assembly_rate
    finishing_cost = finishing_h * cfg.finishing_rate
    install_cost = install_h * cfg.install_rate
    labor_cost = machining_cost + assembly_cost + finishing_cost + install_cost

    # --- appliances + countertops ------------------------------------------
    appliance_cost = sum(
        cfg.appliance_prices.get(a.catalog_item_id or "", 0.0) for a in design.appliances
    )
    countertop_cost = sum(
        (c.width_mm / 1000) * (c.depth_mm / 1000) * cfg.countertop_price_per_sqm
        for c in design.countertops
    )

    # --- bottom-up rollup --------------------------------------------------
    cost_before_markup = (
        materials_cost + hardware_cost + edge_banding_cost
        + accessories_cost + labor_cost + appliance_cost + countertop_cost
    )
    overhead = cost_before_markup * cfg.overhead_pct / 100.0
    contingency = cost_before_markup * cfg.contingency_pct / 100.0
    cost_plus_overhead = cost_before_markup + overhead + contingency
    # margin applied on top of cost (retail = cost / (1 - margin))
    retail_before_tax = cost_plus_overhead / (1 - cfg.margin_pct / 100.0)
    tax = (materials_cost + hardware_cost + appliance_cost) * cfg.material_tax_pct / 100.0
    total_retail = retail_before_tax + tax + cfg.delivery_fee

    # price per linear metre of base run (sanity check metric)
    run_len = sum(
        c.width_mm for c in design.cabinets
        if spec_for(c.type).group in ("base", "tall")
    ) / 1000.0

    return {
        "items": {
            "materials": materials_items,
            "hardware": hardware_items,
            "edge_banding": [{"meters": round(band_m, 2),
                              "total_price": round(edge_banding_cost, 2)}],
            "accessories": [{"cabinet_count": n_cab,
                             "unit_price": cfg.accessories_per_cabinet,
                             "total_price": round(accessories_cost, 2)}],
            "labor": {
                "machining_hours": round(machining_h, 2),
                "assembly_hours": round(assembly_h, 2),
                "finishing_hours": round(finishing_h, 2),
                "install_hours": round(install_h, 2),
                "machining": round(machining_cost, 2),
                "assembly": round(assembly_cost, 2),
                "finishing": round(finishing_cost, 2),
                "install": round(install_cost, 2),
                "total_price": round(labor_cost, 2),
            },
            "appliances": [{"count": len(design.appliances),
                            "total_price": round(appliance_cost, 2)}],
            "countertops": [{"total_price": round(countertop_cost, 2)}],
        },
        "subtotals": {
            "materials": round(materials_cost, 2),
            "hardware": round(hardware_cost, 2),
            "edge_banding": round(edge_banding_cost, 2),
            "accessories": round(accessories_cost, 2),
            "labor": round(labor_cost, 2),
            "appliances": round(appliance_cost, 2),
            "countertops": round(countertop_cost, 2),
            "cost_before_markup": round(cost_before_markup, 2),
        },
        "markup": {
            "overhead_pct": cfg.overhead_pct,
            "overhead": round(overhead, 2),
            "contingency_pct": cfg.contingency_pct,
            "contingency": round(contingency, 2),
            "margin_pct": cfg.margin_pct,
            "margin_amount": round(retail_before_tax - cost_plus_overhead, 2),
            "tax_pct": cfg.material_tax_pct,
            "tax": round(tax, 2),
            "delivery_fee": round(cfg.delivery_fee, 2),
        },
        "summary": {
            "total_retail": round(total_retail, 2),
            "price_per_linear_m": round(total_retail / run_len, 2) if run_len > 0 else 0.0,
            "run_length_m": round(run_len, 2),
            "cabinet_count": n_cab,
        },
        "config": cfg.model_dump(),
    }
