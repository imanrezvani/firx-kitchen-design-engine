"""Tests for technical-drawing derivation from the parametric model.

Drawings must be pure functions of the DesignModel: same model, same
geometry; labels must match the cut-list numbering; nothing stored.
"""

from __future__ import annotations

from app.design.drawings import plan_geometry, run_elevations
from app.design.parametric import Cabinet, DesignModel, RoomParam


def _cab(cab_type: str, w: int, h: int = 720, d: int = 600,
         rotation: int = 0, x: float = 0.0, y: float = 0.0, z: float = 100.0,
         **kw) -> Cabinet:
    return Cabinet(
        id=f"c-{cab_type}-{w}",
        type=cab_type,
        width_mm=w,
        height_mm=h,
        depth_mm=d,
        x=x,
        y=y,
        z=z,
        rotation=rotation,
        **kw,
    )


def _design(*cabs: Cabinet) -> DesignModel:
    return DesignModel(
        id="d1",
        name="تست",
        layout="L",
        room=RoomParam(width_mm=4200, length_mm=3600, height_mm=2700),
        cabinets=list(cabs),
    )


def test_plan_geometry_carries_room_and_cabinet_rects():
    design = _design(
        _cab("base", 800, x=0, y=0),
        _cab("wall", 600, h=900, d=350, x=810, y=0, z=1350),
    )
    plan = plan_geometry(design)
    assert plan["room"]["width_mm"] == 4200
    assert len(plan["cabinets"]) == 2
    by_label = {c["label"]: c for c in plan["cabinets"]}
    assert set(by_label) == {"B1", "W1"}
    assert by_label["B1"]["w"] == 800 and by_label["B1"]["d"] == 600


def test_plan_rotation_swaps_footprint():
    cab = _cab("base", 800, d=600, rotation=90)
    plan = plan_geometry(_design(cab))
    c = plan["cabinets"][0]
    assert c["w"] == 600 and c["d"] == 800


def test_run_elevations_groups_by_wall_and_sorts_along_axis():
    design = _design(
        _cab("base", 800, x=0, y=0, rotation=0),       # north
        _cab("base", 600, x=900, y=0, rotation=0),     # north
        _cab("tall", 600, h=2200, x=0, y=0, rotation=270),  # west
    )
    sheets = run_elevations(design)
    walls = [s["wall"] for s in sheets]
    assert walls == ["north", "west"]
    north = next(s for s in sheets if s["wall"] == "north")
    alongs = [c["along_mm"] for c in north["cabinets"]]
    assert alongs == sorted(alongs)  # B1 before B2
    assert [c["label"] for c in north["cabinets"]] == ["B1", "B2"]


def test_elevation_entry_carries_dimensions_and_openings():
    design = _design(_cab("base", 800, door_config="double", shelf_count=3))
    sheets = run_elevations(design)
    north = next(s for s in sheets if s["wall"] == "north")
    c = north["cabinets"][0]
    assert c["width_mm"] == 800 and c["height_mm"] == 720
    assert c["door_config"] == "double" and c["doors"] == 2
    assert c["shelves"] == 3 and c["z_mm"] == 100


def test_drawings_labels_match_cut_list_numbering():
    from app.bom.components import aggregate_parts
    from app.design.derive import number_cabinets
    design = _design(
        _cab("base", 800, x=0, y=0),
        _cab("wall", 600, h=900, d=350, x=810, y=0, z=1350),
    )
    labels = number_cabinets(design)
    plan = plan_geometry(design)
    parts = aggregate_parts(design.cabinets, labels)
    plan_labels = {c["label"] for c in plan["cabinets"]}
    part_labels = {p["cabinet"] for p in parts}
    assert plan_labels == part_labels == set(labels.values())


def test_drawings_are_deterministic_pure_functions():
    design = _design(
        _cab("base", 800, door_config="double"),
        _cab("tall", 600, h=2200, rotation=270),
    )
    assert run_elevations(design) == run_elevations(design)
    assert plan_geometry(design) == plan_geometry(design)


def test_plan_includes_openings_and_appliances_from_model():
    from app.design.parametric import AppliancePos, Opening
    design = _design(_cab("base", 800))
    design.room.openings.append(Opening(
        id="w1", kind="window", wall="north",
        position_mm=1400, width_mm=1400, height_mm=1500, sill_height_mm=900,
    ))
    design.appliances.append(AppliancePos(
        id="a1", appliance_type="fridge", width_mm=700, height_mm=1780,
        depth_mm=600, x=100, y=100,
    ))
    plan = plan_geometry(design)
    assert plan["openings"] and plan["openings"][0]["kind"] == "window"
    assert plan["appliances"] and plan["appliances"][0]["type"] == "fridge"


def test_parameter_change_changes_drawing():
    """Changing a cabinet dimension must change the derived elevation."""
    narrow = _design(_cab("base", 600))
    wide = _design(_cab("base", 1400))
    e_narrow = run_elevations(narrow)[0]["cabinets"][0]
    e_wide = run_elevations(wide)[0]["cabinets"][0]
    assert e_narrow["width_mm"] == 600
    assert e_wide["width_mm"] == 1400
    assert e_narrow != e_wide


def test_type_change_changes_elevation_height():
    base = run_elevations(_design(_cab("base", 600)))[0]["cabinets"][0]
    tall = run_elevations(_design(_cab("tall", 600, h=2200, z=0)))[0]["cabinets"][0]
    assert tall["height_mm"] == 2200
    assert base["height_mm"] == 720
    assert base["z_mm"] != tall["z_mm"]
