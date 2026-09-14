"""Tests for deterministic cabinet component derivation (bom.components)."""

from __future__ import annotations

from app.bom.components import aggregate_parts, derive_components, sheet_count
from app.design.parametric import Cabinet


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


def _kinds(cab: Cabinet) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in derive_components(cab):
        out[p.kind] = out.get(p.kind, 0) + p.qty
    return out


def test_base_cabinet_has_case_back_shelf_door_toe():
    cab = _cab("base", 800, door_config="double")
    kinds = _kinds(cab)
    assert kinds["side"] == 2
    assert kinds["top"] == 1 and kinds["bottom"] == 1
    assert kinds["back"] == 1
    assert kinds["door"] == 2
    assert kinds["toe_kick"] == 1
    assert kinds["shelf"] == 2  # registry default for base


def test_drawer_cabinet_has_drawer_boxes_and_fronts():
    cab = _cab("drawer", 600, drawer_count=3)
    kinds = _kinds(cab)
    assert kinds["drawer_box"] == 3
    assert kinds["drawer_front"] == 3
    assert "door" not in kinds


def test_wall_cabinet_has_no_toe_kick_and_no_sides():
    cab = _cab("wall", 600, h=900, d=350, door_config="double")
    kinds = _kinds(cab)
    assert "toe_kick" not in kinds
    assert "side" not in kinds
    assert kinds["door"] == 2


def test_end_panel_suppresses_side_edge_banding():
    cab = _cab("base", 600, end_panel_left="standard")
    left = [p for p in derive_components(cab) if p.part_name == "Left Side"][0]
    right = [p for p in derive_components(cab) if p.part_name == "Right Side"][0]
    assert "left" not in left.edge_banding
    assert "right" in right.edge_banding


def test_shelf_count_override():
    cab = _cab("base", 600, shelf_count=5)
    kinds = _kinds(cab)
    assert kinds["shelf"] == 5


def test_door_config_none_no_doors():
    cab = _cab("base", 800, door_config="none")
    kinds = _kinds(cab)
    assert "door" not in kinds


def test_aggregate_parts_flattens_cabinets():
    cabs = [_cab("base", 600), _cab("drawer", 600, drawer_count=3)]
    rows = aggregate_parts(cabs)
    assert all("part" in r and "edge_banding" in r and "grain" in r for r in rows)
    assert sum(r["qty"] for r in rows) > 0


def test_part_identifier_includes_cabinet_label():
    cabs = [_cab("base", 600), _cab("wall", 600, h=900, d=350)]
    labels = {"c-base-600": "B1", "c-wall-600": "W1"}
    rows = aggregate_parts(cabs, labels)
    ids = {r["id"] for r in rows}
    assert "B1.Left Side" in ids
    assert "B1.Top" in ids
    assert "W1.Top" in ids
    assert any(r["id"].startswith("W1.") and r["cabinet"] == "W1" for r in rows)


def test_sheet_count_finite_and_positive():
    cabs = [_cab("base", 800), _cab("base", 800), _cab("tall", 600, h=2200)]
    sc = sheet_count(cabs)
    assert sc["total_sheets"] >= 1
    assert sc["total_m2"] > 0
    assert sc["sheets_by_thickness"]
    assert sum(sc["sheets_by_thickness"].values()) == sc["total_sheets"]
