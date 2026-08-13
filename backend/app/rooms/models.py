import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import TenantBase
from app.core.models import PKMixin, TimestampMixin


class Room(TenantBase, PKMixin, TimestampMixin):
    __tablename__ = "rooms"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), default="آشپزخانه", nullable=False)
    width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    length_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    height_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class Wall(TenantBase, PKMixin, TimestampMixin):
    __tablename__ = "walls"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id"), index=True, nullable=False
    )
    # side: north|south|east|west
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    length_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    thickness_mm: Mapped[int] = mapped_column(Integer, default=150, nullable=False)


class Opening(TenantBase, PKMixin, TimestampMixin):
    __tablename__ = "openings"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # door|window
    wall: Mapped[str] = mapped_column(String(10), nullable=False)  # north|south|east|west
    # position along the wall, start offset (mm)
    position_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    height_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    # sill height from floor (windows); doors = 0
    sill_height_mm: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # swing direction for doors: in|out|left|right (optional)
    swing: Mapped[str | None] = mapped_column(String(10))


class Obstacle(TenantBase, PKMixin, TimestampMixin):
    __tablename__ = "obstacles"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id"), index=True, nullable=False
    )
    # column|radiator|water|drain|electrical|gas|other
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    wall: Mapped[str | None] = mapped_column(String(10))
    position_mm: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    width_mm: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    depth_mm: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    height_mm: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
