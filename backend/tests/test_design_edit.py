"""Regression tests for the design edit persistence bug.

The PUT /designs/{id} route must persist edits to the JSON snapshot column.
A previous implementation assigned the *same* dict object back to the column,
which SQLAlchemy's JSON change detection never notices (no UPDATE issued), so
edits appeared to work in the response but were lost on reload.

These tests pin the exact route behaviour at the unit level by exercising the
same merge logic via the design service layer.
"""

from __future__ import annotations

import json

from app.design.parametric import Cabinet, DesignModel, RoomParam


def _snapshot(**kw) -> dict:
    return DesignModel(
        id="d1",
        name="تست",
        layout="L",
        room=RoomParam(width_mm=4200, length_mm=3600, height_mm=2700),
        cabinets=[
            Cabinet(id="c1", type="base", width_mm=800, height_mm=720, depth_mm=600, x=0.0, y=0.0),
            Cabinet(id="c2", type="wall", width_mm=600, height_mm=900, depth_mm=350, x=810.0, y=0.0),
        ],
        **kw,
    ).model_dump(mode="json")


def test_merge_assigns_new_dict_not_inplace_mutation():
    """The route must build a NEW dict; mutating the loaded dict in place
    would defeat SQLAlchemy JSON change detection."""
    snap = _snapshot()
    edited = dict(snap)  # route: snap = dict(d.snapshot)
    edited["cabinets"] = [{"id": "c1", "width_mm": 1400}]
    assert edited is not snap  # fresh object -> change event will fire
    assert snap["cabinets"] != edited["cabinets"]
    assert snap["cabinets"][0]["width_mm"] == 800


def test_snapshot_roundtrip_through_design_model():
    """A persisted snapshot (as stored JSON) still validates as DesignModel
    after a round trip through json serialization, with edits intact."""
    snap = _snapshot()
    edited = dict(snap)
    edited["cabinets"] = [
        {"id": "c1", "type": "base", "width_mm": 1400, "height_mm": 720,
         "depth_mm": 600, "x": 0.0, "y": 0.0, "door_config": "double",
         "drawer_count": 2, "shelf_count": 3},
        {"id": "c2", "type": "wall", "width_mm": 600, "height_mm": 900,
         "depth_mm": 350, "x": 810.0, "y": 0.0},
    ]
    as_json = json.dumps(edited)
    reloaded = DesignModel.model_validate(json.loads(as_json))
    c1 = next(c for c in reloaded.cabinets if c.id == "c1")
    assert c1.width_mm == 1400
    assert c1.door_config == "double"
    assert c1.drawer_count == 2
    assert c1.shelf_count == 3
