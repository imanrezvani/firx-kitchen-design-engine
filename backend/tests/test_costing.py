"""Tests for the deterministic costing engine (bom.costing).

Cost must be a pure function of the parametric design + config: editing any
editable parameter (dimensions, type, material, hardware) must automatically
reflow through to the quote.
"""

from __future__ import annotations

from app.bom.costing import DEFAULT_CONFIG, PricingConfig, derive_cost
from app.design.parametric import Cabinet, Countertop, DesignModel, RoomParam


def _cab(cab_type: str, w: int, h: int = 720, d: int = 600, **kw) -> Cabinet:
    return Cabinet(
        id=f"c-{cab_type}-{w}",
        type=cab_type,
        width_mm=w,
        height_mm=h,
        depth_mm=d,
        x=0.0,
        y=0.0,
        z=100.0,
        **kw,
    )


def _design(*cabs: Cabinet, countertops: list[Countertop] | None = None) -> DesignModel:
    return DesignModel(
        id="d1",
        name="تست",
        layout="L",
        room=RoomParam(width_mm=4200, length_mm=3600, height_mm=2700),
        cabinets=list(cabs),
        countertops=countertops or [],
    )


def test_cost_is_deterministic():
    design = _design(_cab("base", 800), _cab("wall", 600, h=900, d=350))
    a = derive_cost(design)
    b = derive_cost(design)
    assert a == b


def test_basic_cost_structure():
    design = _design(_cab("base", 800))
    c = derive_cost(design)
    # every required line item present
    for key in ("materials", "hardware", "edge_banding", "accessories",
                "labor", "appliances", "countertops"):
        assert key in c["items"]
    assert c["summary"]["cabinet_count"] == 1
    assert c["summary"]["total_retail"] > 0
    # markup rollup sanity: retail > cost_before_markup
    assert c["summary"]["total_retail"] > c["subtotals"]["cost_before_markup"]
    assert c["markup"]["margin_amount"] > 0


def test_material_change_updates_materials_cost():
    cheap = _design(_cab("base", 800, material_name="ام‌دی‌اف"))
    expensive = _design(_cab("base", 800, material_name="تخته بلوط"))
    cfg = PricingConfig(
        material_price_per_sqm={"ام‌دی‌اف": 100_000, "تخته بلوط": 400_000},
    )
    c_cheap = derive_cost(cheap, cfg)
    c_expensive = derive_cost(expensive, cfg)
    assert c_expensive["subtotals"]["materials"] > c_cheap["subtotals"]["materials"]
    # total retail must rise too
    assert c_expensive["summary"]["total_retail"] > c_cheap["summary"]["total_retail"]


def test_dimension_change_updates_material_and_retail():
    small = _design(_cab("base", 400))
    large = _design(_cab("base", 1400))
    c_small = derive_cost(small)
    c_large = derive_cost(large)
    assert c_large["subtotals"]["materials"] > c_small["subtotals"]["materials"]
    assert c_large["summary"]["total_retail"] > c_small["summary"]["total_retail"]


def test_cabinet_type_change_updates_labor():
    base = _design(_cab("base", 600))
    tall = _design(_cab("tall", 600, h=2200))
    c_base = derive_cost(base)
    c_tall = derive_cost(tall)
    # tall has more labour hours than base (3.5 vs 2.5)
    assert c_tall["items"]["labor"]["total_price"] > c_base["items"]["labor"]["total_price"]
    assert c_tall["items"]["labor"]["assembly_hours"] > c_base["items"]["labor"]["assembly_hours"]


def test_door_config_change_updates_hardware_and_cost():
    single = _design(_cab("base", 800, door_config="single"))
    double = _design(_cab("base", 800, door_config="double"))
    c_single = derive_cost(single)
    c_double = derive_cost(double)
    hw_single = {i["code"]: i["total_price"] for i in c_single["items"]["hardware"]}
    hw_double = {i["code"]: i["total_price"] for i in c_double["items"]["hardware"]}
    assert hw_double["HINGE"] > hw_single["HINGE"]
    assert c_double["subtotals"]["hardware"] > c_single["subtotals"]["hardware"]


def test_drawer_count_change_updates_hardware_and_cost():
    d2 = _design(_cab("drawer", 600, drawer_count=2))
    d4 = _design(_cab("drawer", 600, drawer_count=4))
    c2 = derive_cost(d2)
    c4 = derive_cost(d4)
    assert c4["subtotals"]["hardware"] > c2["subtotals"]["hardware"]
    assert c4["summary"]["total_retail"] > c2["summary"]["total_retail"]


def test_adding_cabinet_increases_total():
    one = _design(_cab("base", 600))
    two = _design(_cab("base", 600), _cab("wall", 600, h=900, d=350))
    assert derive_cost(two)["summary"]["total_retail"] > derive_cost(one)["summary"]["total_retail"]


def test_appliance_prices_flow_through():
    from app.design.parametric import AppliancePos
    design = _design(_cab("base", 600))
    design.appliances.append(AppliancePos(
        id="ap1", appliance_type="fridge", catalog_item_id="a1",
        width_mm=700, height_mm=1780, depth_mm=600, x=0, y=0,
    ))
    c0 = derive_cost(_design(_cab("base", 600)))
    c1 = derive_cost(design, appliance_prices={"a1": 50_000_000})
    assert c1["subtotals"]["appliances"] == 50_000_000
    assert c1["summary"]["total_retail"] > c0["summary"]["total_retail"]


def test_countertop_price_flows_through():
    ct = Countertop(id="ct1", x=0.0, y=0.0, width_mm=2000, depth_mm=600)
    design = _design(_cab("base", 600), countertops=[ct])
    c = derive_cost(design)
    area = 2.0 * 0.6
    assert c["subtotals"]["countertops"] == round(area * DEFAULT_CONFIG.countertop_price_per_sqm, 2)


def test_config_overrides_change_totals():
    design = _design(_cab("base", 800))
    default = derive_cost(design)
    custom = derive_cost(design, PricingConfig(
        overhead_pct=0.0, margin_pct=0.0, material_tax_pct=0.0, delivery_fee=0.0,
    ))
    # removing all markup must reduce retail well below the default quote
    assert custom["summary"]["total_retail"] < default["summary"]["total_retail"]
    assert custom["markup"]["margin_amount"] == 0
    assert custom["markup"]["tax"] == 0


def test_price_per_linear_meter_sane():
    # run length counts base + tall runs; wall cabinets are excluded
    design = _design(_cab("base", 600), _cab("base", 800), _cab("wall", 600, h=900, d=350))
    c = derive_cost(design)
    assert c["summary"]["run_length_m"] == 1.4  # 0.6 + 0.8 bases
    assert c["summary"]["price_per_linear_m"] == round(
        c["summary"]["total_retail"] / 1.4, 2)


def test_material_estimate_drives_edge_banding_and_materials_consistency():
    """Regression: cost's material subtotal == material_estimate × price."""
    from app.design.derive import material_estimate
    design = _design(_cab("base", 800, material_name="X"))
    cfg = PricingConfig(material_price_per_sqm={"X": 50_000}, waste_pct=0.0)
    c = derive_cost(design, cfg)
    est_area = sum(e["area_m2"] for e in material_estimate(design))
    assert c["subtotals"]["materials"] == round(est_area * 50_000, 2)


def test_project_config_merge_layers_defaults_then_overrides():
    """Per-project costing config merges over the shop defaults (partial update
    must only touch the keys provided)."""
    from app.bom.costing import DEFAULT_CONFIG
    # simulate GET /projects/{id}/costing: defaults + stored override
    stored = {"margin_pct": 50.0}
    cfg = DEFAULT_CONFIG.model_copy(deep=True)
    cfg = cfg.model_copy(update=stored)
    assert cfg.margin_pct == 50.0
    assert cfg.overhead_pct == DEFAULT_CONFIG.overhead_pct  # untouched
    # simulate PUT merge on top of stored
    patch = {"delivery_fee": 0.0}
    cfg = cfg.model_copy(update=patch)
    assert cfg.delivery_fee == 0.0
    assert cfg.margin_pct == 50.0


def test_project_config_override_changes_quote():
    """The cost endpoint uses the project override: raising margin raises the
    retail price for the same design."""
    design = _design(_cab("base", 800))
    default = derive_cost(design)
    custom = derive_cost(design, PricingConfig(margin_pct=60.0))
    assert custom["markup"]["margin_amount"] > default["markup"]["margin_amount"]
    assert custom["summary"]["total_retail"] > default["summary"]["total_retail"]


def test_quote_html_is_self_contained_and_derived():
    """The quote HTML must embed the same derived numbers and render RTL."""
    from app.bom.quote import quote_html
    design = _design(_cab("base", 800), _cab("wall", 600, h=900, d=350))
    cost = derive_cost(design)
    html = quote_html(design, cost)
    assert '<html lang="fa" dir="rtl">' in html
    assert "جمع نهایی" in html
    assert "تومان" in html
    # total retail from the derived cost appears in the document (Persian digits)
    fa_total = str(round(cost["summary"]["total_retail"])).translate(
        str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    assert fa_total in html
    # escape() applied to user text; no raw user injection markers
    assert "<script" not in html
