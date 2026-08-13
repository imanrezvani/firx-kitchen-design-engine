import uuid

from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import TenantBase
from app.core.models import PKMixin, TimestampMixin


class CabinetItem(TenantBase, PKMixin, TimestampMixin):
    """Tenant-specific cabinet catalog entry."""

    __tablename__ = "cabinet_catalog"

    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # base|wall|tall|corner|sink|drawer|oven|fridge
    cabinet_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    height_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    depth_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Material(TenantBase, PKMixin, TimestampMixin):
    __tablename__ = "materials"

    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # mdf|particleboard|melamine|plywood
    material_type: Mapped[str] = mapped_column(String(30), nullable=False)
    thickness_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str | None] = mapped_column(String(80))
    price_per_sqm: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)


class Appliance(TenantBase, PKMixin, TimestampMixin):
    __tablename__ = "appliances"

    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(120))
    # fridge|cooktop|oven|hood|dishwasher|sink|faucet
    appliance_type: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    height_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    depth_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
