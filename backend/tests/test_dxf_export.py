"""Tests for DXF R12 export derived from the parametric model.

The DXF must be produced purely from the drawing geometry functions — never a
separate source of truth — and be structurally valid enough for CAD import.
"""

from __future__ import annotations

from app.design.dxf_export import design_to_dxf
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
        z=100.0,
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


def test_dxf_has_valid_structure():
    design = _design(_cab("base", 800), _cab("wall", 600, h=900, d=350))
    dxf = design_to_dxf(design)
    assert dxf.startswith("0\nSECTION\n2\nHEADER")
    assert dxf.rstrip().endswith("0\nEOF")
    # sections present
    assert "SECTION\n2\nTABLES" in dxf
    assert "SECTION\n2\nENTITIES" in dxf
    # named layers defined
    for layer in ("CABINETS", "DIMENSIONS", "TEXT", "REFLINE", "ROOM"):
        assert f"2\n{layer}" in dxf


def test_dxf_contains_plan_and_elevations_for_each_cabinet():
    design = _design(
        _cab("base", 800),
        _cab("wall", 600, h=900, d=350),
        _cab("tall", 600, h=2200, rotation=270),
    )
    dxf = design_to_dxf(design)
    # every cabinet label appears as TEXT
    for label in ("B1", "W1", "T1"):
        assert f"1\n{label}" in dxf
    # elevation opening summary text present
    assert "1\n2d/0dr/2s" in dxf  # base double doors by default


def test_dxf_is_deterministic():
    design = _design(_cab("base", 800), _cab("tall", 600, h=2200))
    assert design_to_dxf(design) == design_to_dxf(design)


def test_dxf_derives_only_from_drawing_geometry():
    """The DXF must not introduce its own geometry logic — it serializes the
    plan/elevation functions. Each cabinet's label appears once in the plan
    and once in its elevation (2 per cabinet)."""
    design = _design(_cab("base", 800), _cab("wall", 600, h=900, d=350))
    dxf = design_to_dxf(design)
    entities = dxf.split("SECTION\n2\nENTITIES")[1].split("ENDSEC")[0]
    assert entities.count("1\nB1") == 2  # plan + elevation
    assert entities.count("1\nW1") == 2
