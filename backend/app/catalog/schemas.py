from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CabinetItemCreate(BaseModel):
    code: str
    name: str
    cabinet_type: str
    width_mm: int
    height_mm: int
    depth_mm: int
    base_price: float = 0
    is_active: bool = True


class CabinetItemUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    cabinet_type: str | None = None
    width_mm: int | None = None
    height_mm: int | None = None
    depth_mm: int | None = None
    base_price: float | None = None
    is_active: bool | None = None


class CabinetItemOut(CabinetItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class MaterialCreate(BaseModel):
    code: str
    name: str
    material_type: str
    thickness_mm: int
    color: str | None = None
    price_per_sqm: float = 0


class MaterialUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    material_type: str | None = None
    thickness_mm: int | None = None
    color: str | None = None
    price_per_sqm: float | None = None


class MaterialOut(MaterialCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class ApplianceCreate(BaseModel):
    code: str
    name: str
    brand: str | None = None
    model: str | None = None
    appliance_type: str
    width_mm: int
    height_mm: int
    depth_mm: int
    price: float = 0


class ApplianceUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    brand: str | None = None
    model: str | None = None
    appliance_type: str | None = None
    width_mm: int | None = None
    height_mm: int | None = None
    depth_mm: int | None = None
    price: float | None = None


class ApplianceOut(ApplianceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


# Design generation input
class DesignGenerateRequest(BaseModel):
    room_id: UUID
    layout: str = Field(..., description="linear|L|U|galley|island|peninsula")
    countertop_material_id: UUID | None = None
    cabinet_material_id: UUID | None = None


class DesignEditRequest(BaseModel):
    """Client edits the parametric model; backend validates it as source of truth."""

    cabinets: list[dict] = Field(default_factory=list)
    appliances: list[dict] = Field(default_factory=list)
    change_desc: str | None = None


class VersionCreateRequest(BaseModel):
    change_desc: str | None = None
