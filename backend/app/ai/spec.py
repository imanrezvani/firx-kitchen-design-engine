"""Strongly typed KitchenSpecification — the contract between the frontend
form, the 2D spatial editor and future AI services.

The KitchenSpecification is the Source of Truth. It is produced from the
structured kitchen-input form + room photos + the 2D spatial editor, and it is
the only input the AI pipeline is allowed to rely on. No free-form prompt is
accepted as the primary input.

Units are millimetres by default. All positions are along-wall offsets in the
same unit as the room. Walls are named from a top-down map: north = y=0,
south = y=length, west = x=0, east = x=width.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

WallSide = Literal["north", "south", "east", "west"]
Unit = Literal["mm", "cm", "m"]
SwingDirection = Literal["left", "right", "double", "none"]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class LayoutKind(str, Enum):
    SINGLE_WALL = "SINGLE_WALL"
    L_SHAPE = "L_SHAPE"
    U_SHAPE = "U_SHAPE"
    G_SHAPE = "G_SHAPE"
    ISLAND = "ISLAND"
    PENINSULA = "PENINSULA"

    @property
    def engine_layout(self) -> str:
        """Map to the deterministic rule engine layout key."""
        return {
            "SINGLE_WALL": "linear",
            "L_SHAPE": "L",
            "U_SHAPE": "U",
            "G_SHAPE": "galley",
            "ISLAND": "island",
            "PENINSULA": "peninsula",
        }[self.value]

    @property
    def fa(self) -> str:
        return {
            "SINGLE_WALL": "خطی (یک دیوار)",
            "L_SHAPE": "ال",
            "U_SHAPE": "یو",
            "G_SHAPE": "جی",
            "ISLAND": "جزیره",
            "PENINSULA": "شبه‌جزیره",
        }[self.value]


class StyleKind(str, Enum):
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMAL = "minimal"
    CONTEMPORARY = "contemporary"

    @property
    def fa(self) -> str:
        return {
            "modern": "مدرن",
            "classic": "کلاسیک",
            "minimal": "مینیمال",
            "contemporary": "معاصر",
        }[self.value]


# ---------------------------------------------------------------------------
# Room / architecture
# ---------------------------------------------------------------------------
class RoomSpec(BaseModel):
    """Gross room dimensions."""

    width: float = Field(gt=0)
    length: float = Field(gt=0)
    height: float = Field(gt=0)
    unit: Unit = "mm"


class WallSpec(BaseModel):
    side: WallSide
    length: float = Field(gt=0)
    thickness: float = Field(default=150, ge=0)


class DoorSpec(BaseModel):
    id: str = ""
    wall: WallSide
    offset: float = Field(ge=0)  # along-wall start offset
    width: float = Field(gt=0)
    height: float = Field(default=2100, gt=0)
    swing: SwingDirection = "right"


class WindowSpec(BaseModel):
    id: str = ""
    wall: WallSide
    offset: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(default=1500, gt=0)
    sill_height: float = Field(default=900, ge=0)


# ---------------------------------------------------------------------------
# Cabinets
# ---------------------------------------------------------------------------
class CabinetSpec(BaseModel):
    type: Literal["base", "wall", "tall", "corner", "drawer"]
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    depth: float = Field(gt=0)
    count: int = Field(default=1, ge=1)


# ---------------------------------------------------------------------------
# Appliances (strongly typed discriminated union on `type`)
# ---------------------------------------------------------------------------
class _ApplianceBase(BaseModel):
    type: str
    width: float | None = Field(default=None, gt=0)
    height: float | None = Field(default=None, gt=0)
    depth: float | None = Field(default=None, gt=0)


class Refrigerator(_ApplianceBase):
    type: Literal["refrigerator"] = "refrigerator"
    variant: Literal["single_door", "double_door", "side_by_side", "built_in"] = "double_door"


class Dishwasher(_ApplianceBase):
    type: Literal["dishwasher"] = "dishwasher"
    variant: Literal["45cm", "60cm"] = "60cm"


class WashingMachine(_ApplianceBase):
    type: Literal["washing_machine"] = "washing_machine"
    variant: Literal["front_load", "top_load"] = "front_load"


class Oven(_ApplianceBase):
    type: Literal["oven"] = "oven"
    variant: Literal["built_in", "countertop"] = "built_in"


class Cooktop(_ApplianceBase):
    type: Literal["cooktop"] = "cooktop"
    variant: Literal["built_in", "freestanding"] = "built_in"


class Hood(_ApplianceBase):
    type: Literal["hood"] = "hood"
    variant: Literal["wall_mounted", "built_in", "island"] = "wall_mounted"


Appliance = Annotated[
    Union[Refrigerator, Dishwasher, WashingMachine, Oven, Cooktop, Hood],
    Field(discriminator="type"),
]


class SinkSpec(BaseModel):
    type: Literal["single_bowl", "double_bowl"] = "double_bowl"
    width: float = Field(default=900, gt=0)
    depth: float = Field(default=500, gt=0)


# ---------------------------------------------------------------------------
# Spatial object positions
# ---------------------------------------------------------------------------
class ObjectPosition(BaseModel):
    """Every important object carries a structured spatial position."""

    type: str  # refrigerator|sink|dishwasher|washing_machine|oven|cooktop|hood|island
    wall: WallSide | None = None  # None for freestanding island objects
    offset: float = Field(default=0, ge=0)  # along-wall offset from wall start
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    height: float | None = None
    rotation: int = Field(default=0, ge=0, le=360)


# ---------------------------------------------------------------------------
# Style / materials / colors
# ---------------------------------------------------------------------------
class ColorsSpec(BaseModel):
    cabinet_color: str = "سفید"
    cabinet_finish: str = "مات"
    handle_style: str = "بدون دستگیره"


class CountertopSpec(BaseModel):
    material: str = "کوارتز"
    color: str = "سفید"
    thickness: float = Field(default=40, gt=0)


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------
class PhotoSpec(BaseModel):
    id: str = ""
    storage_key: str = ""
    url: str = ""
    caption: str | None = None
    content_type: str | None = None


# ---------------------------------------------------------------------------
# User requirements
# ---------------------------------------------------------------------------
class UserRequirements(BaseModel):
    notes: str = ""
    preferences: list[str] = Field(default_factory=list)
    must_include: list[str] = Field(default_factory=list)
    must_avoid: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# KitchenSpecification — the Source of Truth
# ---------------------------------------------------------------------------
class KitchenSpecification(BaseModel):
    version: str = "1.0"
    project_id: str = ""
    project_name: str = "آشپزخانه"
    room: RoomSpec
    walls: list[WallSpec] = Field(default_factory=list)
    doors: list[DoorSpec] = Field(default_factory=list)
    windows: list[WindowSpec] = Field(default_factory=list)
    layout: LayoutKind
    cabinets: list[CabinetSpec] = Field(default_factory=list)
    appliances: list[Appliance] = Field(default_factory=list)
    sink: SinkSpec | None = None
    objects: list[ObjectPosition] = Field(default_factory=list)
    style: StyleKind = StyleKind.MODERN
    colors: ColorsSpec = Field(default_factory=ColorsSpec)
    countertop: CountertopSpec = Field(default_factory=CountertopSpec)
    photos: list[PhotoSpec] = Field(default_factory=list)
    user_requirements: UserRequirements = Field(default_factory=UserRequirements)
