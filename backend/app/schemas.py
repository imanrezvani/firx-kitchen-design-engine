from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth / users / tenants
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    full_name: str | None = None


class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    company_name: str | None = None
    role: str | None = None


class MeResponse(BaseModel):
    user: UserOut
    tenant: TenantOut | None = None


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
class CustomerCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None


class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None


class CustomerOut(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    customer_id: UUID | None = None
    status: str = "draft"
    notes: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    customer_id: UUID | None = None
    status: str | None = None
    notes: str | None = None


class ProjectOut(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Rooms / walls / openings / obstacles
# ---------------------------------------------------------------------------
class WallCreate(BaseModel):
    side: str
    length_mm: int
    thickness_mm: int = 150


class WallOut(WallCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class OpeningCreate(BaseModel):
    kind: str
    wall: str
    position_mm: int
    width_mm: int
    height_mm: int
    sill_height_mm: int = 0
    swing: str | None = None


class OpeningOut(OpeningCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class ObstacleCreate(BaseModel):
    kind: str
    wall: str | None = None
    position_mm: int = 0
    width_mm: int = 0
    depth_mm: int = 0
    height_mm: int = 0
    notes: str | None = None


class ObstacleOut(ObstacleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class RoomCreate(BaseModel):
    project_id: UUID
    name: str = "آشپزخانه"
    width_mm: int
    length_mm: int
    height_mm: int
    notes: str | None = None
    walls: list[WallCreate] = []
    openings: list[OpeningCreate] = []
    obstacles: list[ObstacleCreate] = []


class RoomUpdate(BaseModel):
    name: str | None = None
    width_mm: int | None = None
    length_mm: int | None = None
    height_mm: int | None = None
    notes: str | None = None


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    name: str
    width_mm: int
    length_mm: int
    height_mm: int
    notes: str | None = None
    walls: list[WallOut] = []
    openings: list[OpeningOut] = []
    obstacles: list[ObstacleOut] = []
    created_at: datetime
