"""Propagation tests for the parametric Cabinet model.

These verify the core guarantee: the parametric model is the single source of
truth, and changing one editable parameter deterministically regenerates every
dependent derived output (components, hardware, cut list, materials,
numbering). See docs/firx-parametric-model.md §11 (change propagation).
"""

from __future__ import annotations

from app.bom.components import derive_components, sheet_count
from app.bom.hardware import derive_cabinet_hardware
from app.design.cabinet_types import resolve_interior
from app.design.derive import (
    build_visual_prompt,
    material_estimate,
    number_cabinets,
)
from app.design.parametric import Cabinet, DesignModel, RoomParam


def _cab(cab_type: str, w: int, h: int = 720, d: int = 600, **kw) -> Cabinet:
    return Cabinet(
        id=f"c-{cab_type}-{w}",
        type=cab_type,
        width_mm=w,
        height_mm=h,
        depth_mm=d,
        x=0.0,
        y=0.0,
        **kw,
    )


def _kinds(cab: Cabinet) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in derive_components(cab):
        out[p.kind] = out.get(p.kind, 0) + p.qty
    return out


def _hw(cab: Cabinet) -> dict[str, int]:
    return {l.code: l.qty for l in derive_cabinet_hardware(cab)}


def _design(*cabs: Cabinet) -> DesignModel:
    return DesignModel(
        id="d1",
        name="تست",
        layout="L",
        room=RoomParam(width_mm=4200, length_mm=3600, height_mm=2700),
        cabinets=list(cabs),
    )


# ---------------------------------------------------------------------------
# Width → door configuration → hinges (dependency chain)
# ---------------------------------------------------------------------------
def test_width_change_crosses_single_double_threshold():
    narrow = _cab("base", 400)
    wide = _cab("base", 800)
    assert resolve_interior(narrow).door_config == "single"
    assert resolve_interior(wide).door_config == "double"
    assert _kinds(narrow)["door"] == 1
    assert _kinds(wide)["door"] == 2
    assert _hw(narrow)["HINGE"] == 2   # 1 door × 2 hinges
    assert _hw(wide)["HINGE"] == 4     # 2 doors × 2 hinges


def test_door_config_explicit_overrides_width_heuristic():
    cab = _cab("base", 800, door_config="single")
    assert resolve_interior(cab).door_count == 1
    assert _kinds(cab)["door"] == 1
    assert _hw(cab)["HINGE"] == 2


def test_door_config_none_removes_doors_and_hinges():
    cab = _cab("base", 800, door_config="none")
    assert "door" not in _kinds(cab)
    assert "HINGE" not in _hw(cab)


# ---------------------------------------------------------------------------
# Drawer count → drawer parts + slides
# ---------------------------------------------------------------------------
def test_drawer_count_propagates_to_components_and_hardware():
    cab = _cab("drawer", 600, drawer_count=4)
    kinds = _kinds(cab)
    assert kinds["drawer_box"] == 4
    assert kinds["drawer_front"] == 4
    assert _hw(cab)["SLIDE"] == 4
    assert _hw(cab)["PULL"] == 4


def test_increasing_drawer_count_only_grows_drawer_derived_outputs():
    d3 = _cab("drawer", 600, drawer_count=3)
    d5 = _cab("drawer", 600, drawer_count=5)
    k3, k5 = _kinds(d3), _kinds(d5)
    # shared structural parts unchanged
    for kind in ("side", "top", "bottom", "back"):
        assert k3[kind] == k5[kind]
    assert k5["drawer_box"] == 5 and k3["drawer_box"] == 3
    assert _hw(d5)["SLIDE"] == 5 and _hw(d3)["SLIDE"] == 3


# ---------------------------------------------------------------------------
# Shelf count → shelf parts + pins
# ---------------------------------------------------------------------------
def test_shelf_count_propagates_to_shelf_and_pins():
    cab = _cab("base", 600, shelf_count=3)
    kinds = _kinds(cab)
    assert kinds["shelf"] == 3
    assert _hw(cab)["PIN"] == 12  # 3 shelves × 4 pins


def test_shelf_count_zero_removes_pins_and_shelves():
    cab = _cab("base", 600, shelf_count=0)
    assert "shelf" not in _kinds(cab)
    assert "PIN" not in _hw(cab)


# ---------------------------------------------------------------------------
# End panels → edge banding (exposure derivation)
# ---------------------------------------------------------------------------
def test_end_panel_suppresses_side_edge_banding():
    cab = _cab("base", 600, end_panel_left="standard")
    left = [p for p in derive_components(cab) if p.part_name == "Left Side"][0]
    right = [p for p in derive_components(cab) if p.part_name == "Right Side"][0]
    assert "left" not in left.edge_banding
    assert "right" in right.edge_banding


def test_removing_end_panel_restores_banding():
    none = _cab("base", 600, end_panel_right="not_exposed")
    right_none = [p for p in derive_components(none) if p.part_name == "Right Side"][0]
    assert "right" in right_none.edge_banding


# ---------------------------------------------------------------------------
# Toe kick → component presence and height
# ---------------------------------------------------------------------------
def test_toe_kick_height_drives_part_dimension():
    base = _cab("base", 600, toe_kick_height=150)
    tk = [p for p in derive_components(base) if p.kind == "toe_kick"][0]
    assert tk.length_mm == 150
    assert tk.width_mm == 600 - 2 * 18


def test_toe_kick_zero_disables_for_floor_cabinet():
    cab = _cab("base", 600, toe_kick_height=0)
    assert "toe_kick" not in _kinds(cab)


# ---------------------------------------------------------------------------
# Material thickness → part thickness + sheet count
# ---------------------------------------------------------------------------
def test_box_thickness_propagates_to_structural_parts():
    thin = _cab("base", 600, box_thickness=12, back_thickness=12)
    thick = _cab("base", 600, box_thickness=18, back_thickness=16)
    side_thin = [p for p in derive_components(thin) if p.part_name == "Left Side"][0]
    side_thick = [p for p in derive_components(thick) if p.part_name == "Left Side"][0]
    assert side_thin.thickness_mm == 12
    assert side_thick.thickness_mm == 18
    back_thin = [p for p in derive_components(thin) if p.kind == "back"][0]
    back_thick = [p for p in derive_components(thick) if p.kind == "back"][0]
    assert back_thin.thickness_mm == 12
    assert back_thick.thickness_mm == 16


def test_box_thickness_changes_sheet_usage():
    thin = _design(_cab("base", 800), _cab("base", 800))
    thick = _design(_cab("base", 800, box_thickness=25), _cab("base", 800, box_thickness=25))
    st = sheet_count(thin.cabinets)
    stk = sheet_count(thick.cabinets)
    assert st["sheets_by_thickness"] != stk["sheets_by_thickness"]


# ---------------------------------------------------------------------------
# Cabinet type → defaults (registry)
# ---------------------------------------------------------------------------
def test_each_registry_type_resolves_deterministically():
    from app.design.cabinet_types import CABINET_TYPES
    for t in CABINET_TYPES:
        spec = CABINET_TYPES[t]
        cab = _cab(t, spec.default_width, spec.default_height, spec.default_depth)
        r1 = resolve_interior(cab)
        r2 = resolve_interior(cab)
        assert r1 == r2  # deterministic
        assert r1.door_config in spec.door_configs
        assert r1.shelf_count >= 0 and r1.drawer_count >= 0


# ---------------------------------------------------------------------------
# Appliance hook
# ---------------------------------------------------------------------------
def test_appliance_hook_carried_and_drives_prompt():
    cab = _cab("sink", 900, appliance_hook="sink")
    assert cab.appliance_hook == "sink"
    prompt = build_visual_prompt(_design(cab))
    assert "sink" in prompt


# ---------------------------------------------------------------------------
# Constraints (parameter out of range → Constraint record)
# ---------------------------------------------------------------------------
def test_out_of_range_dimension_produces_constraint_and_clamps():
    cab = _cab("base", 5000)  # over max 1500
    r = resolve_interior(cab)
    errs = [c for c in r.constraints if c.code == "cabinet.param.max"]
    assert any(c.param == "width_mm" and c.nominal == 5000 and c.effective == 1500
               for c in errs)
    assert errs[0].level == "warning"


def test_min_dimension_clamps_upward():
    cab = _cab("wall", 50, h=900, d=350)  # under min 100
    r = resolve_interior(cab)
    assert any(c.code == "cabinet.param.min" and c.param == "width_mm"
               for c in r.constraints)


def test_door_config_not_allowed_for_type_errors():
    cab = _cab("fridge", 900, door_config="double")  # fridge only allows none
    r = resolve_interior(cab)
    assert any(c.code == "cabinet.door_config.invalid" for c in r.constraints)


# ---------------------------------------------------------------------------
# Cabinet numbering (stable labels per group)
# ---------------------------------------------------------------------------
def test_numbering_per_group_in_design_order():
    design = _design(
        _cab("base", 600),        # B1
        _cab("wall", 600, h=900, d=350),  # W1
        _cab("base", 800),        # B2
        _cab("tall", 600, h=2200),        # T1
        _cab("drawer", 600),      # B3
    )
    labels = number_cabinets(design)
    ids = [c.id for c in design.cabinets]
    assert labels[ids[0]] == "B1"
    assert labels[ids[1]] == "W1"
    assert labels[ids[2]] == "B2"
    assert labels[ids[3]] == "T1"
    assert labels[ids[4]] == "B3"


def test_numbering_used_in_cut_list_labels():
    from app.bom.components import aggregate_parts
    design = _design(_cab("base", 800), _cab("wall", 600, h=900, d=350))
    labels = number_cabinets(design)
    rows = aggregate_parts(design.cabinets, labels)
    assert all(r["cabinet"] in ("B1", "W1") for r in rows)
    assert any(r["cabinet"] == "B1" for r in rows)
    assert any(r["cabinet"] == "W1" for r in rows)


# ---------------------------------------------------------------------------
# Material estimation + AI prompt derive from the model
# ---------------------------------------------------------------------------
def test_material_estimate_aggregates_by_material_thickness():
    design = _design(
        _cab("base", 800, material_name="پلای‌وود", box_thickness=18),
        _cab("base", 800, material_name="پلای‌وود", box_thickness=18),
        _cab("base", 800, material_name="ام‌دی‌اف", box_thickness=16),
    )
    est = material_estimate(design)
    # grouping is by (material, thickness): plywood 18mm + plywood 16mm back +
    # MDF 16mm back. The two plywood 18mm cabinets must share one row.
    ply18 = [e for e in est if e["material"] == "پلای‌وود" and e["thickness_mm"] == 18][0]
    mdf16 = [e for e in est if e["material"] == "ام‌دی‌اف" and e["thickness_mm"] == 16][0]
    # two 800-wide plywood boxes -> at least twice the area of a single box
    one = _design(_cab("base", 800, material_name="پلای‌وود", box_thickness=18))
    single_ply18 = [e for e in material_estimate(one)
                    if e["material"] == "پلای‌وود" and e["thickness_mm"] == 18][0]
    assert ply18["area_m2"] >= 2 * single_ply18["area_m2"]
    assert ply18["parts"] > mdf16["parts"]


def test_visual_prompt_contains_model_derived_facts():
    design = _design(_cab("base", 800, door_config="double", material_name="بلوط"),
                     _cab("wall", 600, h=900, d=350))
    prompt = build_visual_prompt(design)
    assert "4200×3600×2700" in prompt
    assert "B1" in prompt and "W1" in prompt
    assert "بلوط" in prompt
    assert "دو‌در" in prompt


# ---------------------------------------------------------------------------
# End-to-end: single param edit propagates through the whole chain
# ---------------------------------------------------------------------------
def test_edit_drawer_count_flows_to_parts_hardware_materials():
    base = _design(_cab("drawer", 600, drawer_count=3, material_name="پلای‌وود"))
    edited = _design(_cab("drawer", 600, drawer_count=4, material_name="پلای‌وود"))

    def total_parts(cab: Cabinet) -> int:
        return sum(p.qty for p in derive_components(cab))

    parts_b = total_parts(base.cabinets[0])
    parts_e = total_parts(edited.cabinets[0])
    assert parts_e == parts_b + 2  # +1 drawer box +1 drawer front

    assert _hw(edited.cabinets[0])["SLIDE"] == 4

    def total_m2(design: DesignModel) -> float:
        return sum(e["area_m2"] for e in material_estimate(design))

    assert total_m2(edited) > total_m2(base)  # more material consumed


# ---------------------------------------------------------------------------
# Downstream readiness: the SAME parametric model feeds costing, drawings,
# numbering, materials and AI prompts — verified with zero state duplication.
# ---------------------------------------------------------------------------
def test_model_feeds_all_downstream_consumers_consistently():
    design = _design(
        _cab("base", 800, door_config="double", material_name="پلای‌وود"),
        _cab("wall", 600, h=900, d=350, door_config="double"),
        _cab("tall", 600, h=2200, door_config="split", shelf_count=5),
    )

    # costing: hardware counts + material area are exactly derivable
    hw = {l.code: l.qty for l in derive_cabinet_hardware(design.cabinets[0])}
    assert hw["HINGE"] == 4  # 2 doors

    # cut list: every part carries the full manufacturing dataset
    from app.bom.components import aggregate_parts
    rows = aggregate_parts(design.cabinets, number_cabinets(design))
    assert rows and all(
        r["id"] and r["cabinet"] and r["part"] and r["thickness_mm"] > 0
        and r["width_mm"] > 0 and r["length_mm"] > 0 and r["qty"] > 0
        and r["grain"] in ("vertical", "horizontal", "any")
        and isinstance(r["edge_banding"], list)
        for r in rows
    )

    # technical drawings: every part carries geometric dimensions
    parts = [p for c in design.cabinets for p in derive_components(c)]
    assert all(p.width_mm > 0 and p.length_mm > 0 and p.thickness_mm > 0 for p in parts)

    # cabinet numbering: stable and unique per design
    labels = number_cabinets(design)
    assert len(labels) == len(set(labels.values())) == 3

    # material estimation: every part accounted for in per-material area
    est = material_estimate(design)
    total_area = sum(e["area_m2"] for e in est)
    part_area = sum(
        (p.width_mm * p.length_mm * p.qty) / 1_000_000
        for c in design.cabinets for p in derive_components(c)
    )
    assert round(total_area, 2) == round(part_area, 2)

    # AI visualization: prompt is fully derived from model facts
    prompt = build_visual_prompt(design)
    for fact in ("B1", "W1", "T1", "پلای‌وود", "دو‌در", "5 طبقه", "4200×3600×2700"):
        assert fact in prompt

    # technical drawings: plan + per-wall elevations share the same numbering
    from app.design.drawings import plan_geometry, run_elevations
    plan = plan_geometry(design)
    plan_labels = {c["label"] for c in plan["cabinets"]}
    assert plan_labels == set(labels.values())
    elev = run_elevations(design)
    assert sum(len(s["cabinets"]) for s in elev) == 3  # every cabinet drawn
    assert all(any(e["label"] == l for s in elev for e in s["cabinets"])
               for l in labels.values())


def test_material_estimate_partial_change_only_touches_affected_rows():
    """Regression guard: editing one cabinet must not change other rows."""
    a = _design(_cab("base", 600, material_name="M1"),
                _cab("tall", 600, h=2200, material_name="M2"))
    b = _design(_cab("base", 600, material_name="M1", shelf_count=3),
                _cab("tall", 600, h=2200, material_name="M2"))

    ea = {e["material"]: e for e in material_estimate(a)}
    eb = {e["material"]: e for e in material_estimate(b)}
    # M2 (tall) untouched
    for key in ea:
        if key in eb and key == "M2":
            assert ea[key] == eb[key]
