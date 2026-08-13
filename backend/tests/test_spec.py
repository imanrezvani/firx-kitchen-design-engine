"""KitchenSpecification schema tests."""

from __future__ import annotations

from pydantic import ValidationError

import pytest

from app.ai.spec import KitchenSpecification, LayoutKind, ObjectPosition, RoomSpec
from app.ai.spec import Cooktop, Dishwasher, Refrigerator


def test_example_from_product_contract_parses():
    """The example payload from the task must validate against the schema."""
    spec = KitchenSpecification.model_validate(
        {
            "room": {"width": 4200, "length": 3600, "height": 2700, "unit": "mm"},
            "layout": "L_SHAPE",
            "objects": [
                {"type": "refrigerator", "wall": "north", "offset": 3200, "width": 900, "depth": 700}
            ],
        }
    )
    assert spec.room.width == 4200
    assert spec.room.length == 3600
    assert spec.room.unit == "mm"
    assert spec.layout == LayoutKind.L_SHAPE
    assert spec.objects[0].type == "refrigerator"
    assert spec.objects[0].wall == "north"


def test_layout_enum_maps_to_engine_layout():
    assert LayoutKind.SINGLE_WALL.engine_layout == "linear"
    assert LayoutKind.L_SHAPE.engine_layout == "L"
    assert LayoutKind.U_SHAPE.engine_layout == "U"
    assert LayoutKind.G_SHAPE.engine_layout == "galley"
    assert LayoutKind.ISLAND.engine_layout == "island"
    assert LayoutKind.PENINSULA.engine_layout == "peninsula"


def test_room_requires_positive_dimensions():
    with pytest.raises(ValidationError):
        RoomSpec(width=-1, length=3600, height=2700)


def test_discriminated_union_appliances():
    spec = KitchenSpecification.model_validate(
        {
            "room": {"width": 4000, "length": 3000, "height": 2700},
            "layout": "U_SHAPE",
            "appliances": [
                {"type": "refrigerator", "variant": "side_by_side"},
                {"type": "dishwasher", "variant": "45cm"},
                {"type": "cooktop", "variant": "freestanding"},
            ],
        }
    )
    assert isinstance(spec.appliances[0], Refrigerator)
    assert isinstance(spec.appliances[1], Dishwasher)
    assert isinstance(spec.appliances[2], Cooktop)


def test_invalid_appliance_type_rejected():
    with pytest.raises(ValidationError):
        KitchenSpecification.model_validate(
            {
                "room": {"width": 4000, "length": 3000, "height": 2700},
                "layout": "U_SHAPE",
                "appliances": [{"type": "teleporter"}],
            }
        )


def test_sink_defaults(example_spec):
    assert example_spec.sink is not None
    assert example_spec.sink.type == "double_bowl"
    assert example_spec.sink.width == 900


def test_object_position_shape(example_spec):
    obj = example_spec.objects[0]
    assert isinstance(obj, ObjectPosition)
    assert {"type", "wall", "offset", "width", "depth"}.issubset(obj.model_dump().keys())


def test_roundtrip_json(example_spec):
    payload = example_spec.model_dump()
    restored = KitchenSpecification.model_validate(payload)
    assert restored == example_spec
