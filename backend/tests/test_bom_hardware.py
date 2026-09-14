"""Tests for deterministic hardware derivation (bom.hardware)."""

from __future__ import annotations

from app.bom.hardware import derive_cabinet_hardware, derive_hardware_breakdown
from app.design.parametric import Cabinet, DesignModel, RoomParam


def _cab(cab_type: str, w: int, h: int = 720, **kw) -> Cabinet:
    return Cabinet(
        id=f"c-{cab_type}-{w}",
        type=cab_type,
        width_mm=w,
        height_mm=h,
        depth_mm=600,
        x=0.0,
        y=0.0,
        **kw,
    )


def test_narrow_base_gets_single_door_and_two_hinges():
    cab = _cab("base", 400)
    lines = derive_cabinet_hardware(cab)
    hinge = [l for l in lines if l.code == "HINGE"]
    pull = [l for l in lines if l.code == "PULL"]
    assert hinge[0].qty == 2  # 1 door × 2 hinges
    assert pull[0].qty == 1   # 1 pull for the single door


def test_wide_base_gets_double_doors():
    cab = _cab("base", 800)
    lines = derive_cabinet_hardware(cab)
    hinge = [l for l in lines if l.code == "HINGE"][0]
    assert hinge.qty == 4  # 2 doors × 2 hinges


def test_door_config_none_suppresses_hinges():
    cab = _cab("base", 800, door_config="none")
    lines = derive_cabinet_hardware(cab)
    assert all(l.code != "HINGE" for l in lines)


def test_drawer_base_gets_three_slides_and_three_pulls():
    cab = _cab("drawer", 600)
    lines = derive_cabinet_hardware(cab)
    slide = [l for l in lines if l.code == "SLIDE"][0]
    pull = [l for l in lines if l.code == "PULL"][0]
    assert slide.qty == 3
    assert pull.qty == 3


def test_explicit_drawer_count_overrides_heuristic():
    cab = _cab("drawer", 600, drawer_count=4)
    lines = derive_cabinet_hardware(cab)
    assert [l for l in lines if l.code == "SLIDE"][0].qty == 4


def test_tall_pantry_gets_shelf_pins():
    cab = _cab("tall", 600, h=2200)
    lines = derive_cabinet_hardware(cab)
    pin = [l for l in lines if l.code == "PIN"][0]
    assert pin.qty == 4 * 4  # 4 shelves (registry default) × 4 pins
    assert pin.qty >= 8


def test_filler_has_no_hardware():
    cab = _cab("base", 100)
    cab.type = "filler"
    assert derive_cabinet_hardware(cab) == []


def test_breakdown_aggregates_across_cabinets():
    design = DesignModel(
        id="d1",
        name="test",
        layout="L",
        room=RoomParam(width_mm=4200, length_mm=3600, height_mm=2700),
        cabinets=[
            _cab("base", 800),
            _cab("base", 800),
            _cab("drawer", 600),
        ],
    )
    hw = derive_hardware_breakdown(design)
    by_code = {i["code"]: i for i in hw["items"]}
    assert by_code["HINGE"]["qty"] == 8          # 2+2 doors × 2 hinges
    assert by_code["SLIDE"]["qty"] == 3          # drawer base
    assert by_code["PULL"]["qty"] == 7           # 2+2 doors + 3 drawers
    assert hw["total"] > 0
