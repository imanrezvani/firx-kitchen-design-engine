"""Parametric kitchen model — the single source of truth.

The browser is NOT the source of truth. The generated image is NOT the
source of truth. Every design, version, validation and BOM is derived from
this structured model, which is persisted as a JSON snapshot per design.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

WallSide = Literal["north", "south", "east", "west"]
OpeningKind = Literal["door", "window"]


class Wall(BaseModel):
    side: WallSide
    length_mm: int
    thickness_mm: int = 150


class Opening(BaseModel):
    id: str = ""
    kind: OpeningKind
    wall: WallSide
    position_mm: int  # start offset along the wall
    width_mm: int
    height_mm: int
    sill_height_mm: int = 0
    swing: str | None = None


class Obstacle(BaseModel):
    id: str = ""
    kind: str  # column|radiator|water|drain|electrical|gas|other
    wall: WallSide | None = None
    position_mm: int = 0
    width_mm: int = 0
    depth_mm: int = 0
    height_mm: int = 0
    notes: str | None = None


class RoomParam(BaseModel):
    id: str = ""
    name: str = "آشپزخانه"
    width_mm: int = Field(gt=0)
    length_mm: int = Field(gt=0)
    height_mm: int = Field(gt=0)
    walls: list[Wall] = Field(default_factory=list)
    openings: list[Opening] = Field(default_factory=list)
    obstacles: list[Obstacle] = Field(default_factory=list)


class Cabinet(BaseModel):
    id: str = ""
    type: str  # base|wall|tall|corner|sink|drawer|oven|fridge|...
    catalog_item_id: str | None = None
    # --- editable parameters (explicit, per task) ---
    width_mm: int
    height_mm: int
    depth_mm: int
    # position of the cabinet's near (back-corner) point in room coords (mm)
    x: float
    y: float
    z: float = 0  # bottom z (toe kick sits below)
    rotation: int = 0  # degrees, direction the front faces: 0=S, 90=W, 180=N, 270=E
    material_id: str | None = None
    material_name: str | None = None
    box_thickness: int | None = None   # default 18 (¾″) via type spec
    back_thickness: int | None = None  # default 16 (½″) via type spec
    name: str = "کابینت"
    # --- interior configuration (editable; drives derived components) ---
    # When None, the type registry supplies defaults / width heuristics.
    door_config: str | None = None  # none|single|double|lift_up|split|drawers_top
    drawer_count: int | None = None
    shelf_count: int | None = None
    toe_kick_height: int | None = None  # 0 disables; None => type default
    end_panel_left: str | None = None  # not_exposed|standard|stained|furniture
    end_panel_right: str | None = None
    # appliance hook: embedded appliance this cabinet integrates (sink/oven/
    # fridge/microwave/hood/...). Present only where the type allows it.
    appliance_hook: str | None = None


class AppliancePos(BaseModel):
    id: str = ""
    appliance_type: str  # fridge|cooktop|oven|hood|dishwasher|sink|faucet
    catalog_item_id: str | None = None
    width_mm: int
    height_mm: int
    depth_mm: int
    x: float
    y: float
    z: float = 0
    rotation: int = 0
    name: str = ""


class Countertop(BaseModel):
    id: str = ""
    x: float
    y: float
    width_mm: int
    depth_mm: int
    thickness_mm: int = 40
    z: float = 860
    material_id: str | None = None
    material_name: str | None = None


class ValidationIssue(BaseModel):
    level: Literal["ok", "warning", "error"]
    message: str


class DesignModel(BaseModel):
    id: str = ""
    name: str
    layout: str  # linear|L|U|galley|island|peninsula
    room: RoomParam
    cabinets: list[Cabinet] = Field(default_factory=list)
    appliances: list[AppliancePos] = Field(default_factory=list)
    countertops: list[Countertop] = Field(default_factory=list)
    clearances: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    score: int = 0
    generated_at: str = ""
    # derived, model-fed AI visualization prompt (see app/design/derive.py).
    # Set at generation/save time; the AI renderer consumes it as input and
    # never becomes a source of truth.
    visual_prompt: str = ""


class DesignVersionOut(BaseModel):
    id: str = ""
    version_no: int
    change_desc: str | None
    snapshot: DesignModel
    created_by: str | None = None
    created_at: str = ""
