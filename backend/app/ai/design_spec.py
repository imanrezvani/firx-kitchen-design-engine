"""DesignSpecification — the normalized AI output contract.

The AI response (real or mock) is normalized into this structured format. It
will later feed: Render Prompt, Technical Drawing Generator and Material
Estimator. It is a pure data schema — no rendering or CAD logic lives here.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.ai.spec import LayoutKind, StyleKind, WallSide


class DesignElement(BaseModel):
    """A single positioned cabinet or appliance in the design."""

    id: str = ""
    type: str
    name: str = ""
    wall: WallSide | None = None
    offset: float = 0
    x: float = 0
    y: float = 0
    z: float = 0
    rotation: int = 0
    width_mm: float
    height_mm: float
    depth_mm: float


class MaterialRef(BaseModel):
    code: str = ""
    name: str = ""
    category: str = ""  # cabinet|countertop|hardware|handle


class RenderInstruction(BaseModel):
    view: str  # CameraView value
    name: str = ""
    instruction: str = ""


class DesignSpecification(BaseModel):
    version: str = "1.0"
    source_spec_version: str = "1.0"
    layout: LayoutKind
    style: StyleKind
    room: dict = Field(default_factory=dict)  # mirrors KitchenSpecification.room
    cabinets: list[DesignElement] = Field(default_factory=list)
    appliances: list[DesignElement] = Field(default_factory=list)
    countertops: list[DesignElement] = Field(default_factory=list)
    object_positions: list[dict] = Field(default_factory=list)
    materials: list[MaterialRef] = Field(default_factory=list)
    colors: dict = Field(default_factory=dict)
    render_instructions: list[RenderInstruction] = Field(default_factory=list)
    rationale: str = ""
    warnings: list[str] = Field(default_factory=list)
    score: int = 0
