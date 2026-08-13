import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import TenantBase
from app.core.models import PKMixin, TimestampMixin


class Design(TenantBase, PKMixin, TimestampMixin):
    """A design attached to a project. The *current* version is stored in
    ``snapshot``; history lives in ``design_versions``."""

    __tablename__ = "designs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), index=True, nullable=False
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    layout: Mapped[str] = mapped_column(String(30), nullable=False)
    # full parametric design snapshot (DesignOut JSON): the source of truth.
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    current_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class DesignVersion(TenantBase, PKMixin, TimestampMixin):
    __tablename__ = "design_versions"

    design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designs.id"), index=True, nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    change_desc: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class BOMItem(TenantBase, PKMixin):
    __tablename__ = "bom_items"

    design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designs.id"), index=True, nullable=False
    )
    # cabinet|material|appliance|countertop
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str | None] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    width_mm: Mapped[int] = mapped_column(Integer, default=0)
    height_mm: Mapped[int] = mapped_column(Integer, default=0)
    depth_mm: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[float] = mapped_column(nullable=False, default=0)
    total_price: Mapped[float] = mapped_column(nullable=False, default=0)


class ValidationResult(TenantBase, PKMixin, TimestampMixin):
    __tablename__ = "validation_results"

    design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designs.id"), index=True, nullable=False
    )
    # JSON list of {level, message} where level in ok|warning|error
    results: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    score: Mapped[int] = mapped_column(Integer, default=0)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
