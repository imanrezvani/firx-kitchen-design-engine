"""Shared fixtures for the AI pipeline tests."""

from __future__ import annotations

import pytest

from app.ai.spec import (
    CabinetSpec,
    Cooktop,
    Dishwasher,
    DoorSpec,
    KitchenSpecification,
    ObjectPosition,
    PhotoSpec,
    Refrigerator,
    RoomSpec,
    SinkSpec,
    UserRequirements,
    WallSpec,
    WindowSpec,
)
from app.ai.spec import LayoutKind, StyleKind


@pytest.fixture
def example_spec() -> KitchenSpecification:
    """A realistic kitchen spec matching the product contract example."""
    return KitchenSpecification(
        version="1.0",
        project_id="p-001",
        project_name="آشپزخانه نمونه",
        room=RoomSpec(width=4200, length=3600, height=2700, unit="mm"),
        walls=[
            WallSpec(side="north", length=4200),
            WallSpec(side="south", length=4200),
            WallSpec(side="east", length=3600),
            WallSpec(side="west", length=3600),
        ],
        doors=[DoorSpec(id="d1", wall="north", offset=3200, width=900, height=2100, swing="right")],
        windows=[WindowSpec(id="w1", wall="south", offset=1400, width=1400, height=1500, sill_height=900)],
        layout=LayoutKind.L_SHAPE,
        cabinets=[
            CabinetSpec(type="base", width=600, height=720, depth=600, count=6),
            CabinetSpec(type="wall", width=600, height=900, depth=350, count=3),
        ],
        appliances=[
            Refrigerator(type="refrigerator", variant="double_door"),
            Dishwasher(type="dishwasher", variant="60cm"),
            Cooktop(type="cooktop", variant="built_in"),
        ],
        sink=SinkSpec(type="double_bowl", width=900, depth=500),
        objects=[
            ObjectPosition(
                type="refrigerator",
                wall="east",
                offset=3000,
                width=700,
                depth=700,
                height=1780,
            ),
            ObjectPosition(
                type="island",
                wall=None,
                offset=0,
                width=1500,
                depth=900,
                height=900,
            ),
        ],
        style=StyleKind.MODERN,
        colors={"cabinet_color": "سفید", "cabinet_finish": "مات", "handle_style": "بدون دستگیره"},
        countertop={"material": "کوارتز", "color": "سفید", "thickness": 40},
        photos=[PhotoSpec(id="ph1", storage_key="rooms/ph1.jpg", caption="کابینت قدیمی")],
        user_requirements=UserRequirements(
            notes="خانواده چهار نفره",
            preferences=["نورپردازی زیر کابینت"],
            must_include=["ظرفشویی"],
            must_avoid=["جزیره"],
        ),
    )
