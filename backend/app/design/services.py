"""Design generation service: loads room + catalog from the tenant DB and
invokes the KitchenDesignEngine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import Appliance, CabinetItem, Material
from app.design.engine import KitchenDesignEngine
from app.design.parametric import RoomParam, DesignModel
from app.rooms.models import Obstacle, Opening, Room, Wall
from app.projects.models import Project


async def build_room_param(session: AsyncSession, room_id: uuid.UUID) -> RoomParam:
    room = await session.get(Room, room_id)
    if room is None:
        raise ValueError("room_not_found")
    walls = (await session.execute(select(Wall).where(Wall.room_id == room_id))).scalars().all()
    openings = (await session.execute(select(Opening).where(Opening.room_id == room_id))).scalars().all()
    obstacles = (await session.execute(select(Obstacle).where(Obstacle.room_id == room_id))).scalars().all()
    return RoomParam(
        id=str(room.id),
        name=room.name,
        width_mm=room.width_mm,
        length_mm=room.length_mm,
        height_mm=room.height_mm,
        walls=[{"side": w.side, "length_mm": w.length_mm, "thickness_mm": w.thickness_mm} for w in walls],
        openings=[
            {
                "id": str(o.id),
                "kind": o.kind,
                "wall": o.wall,
                "position_mm": o.position_mm,
                "width_mm": o.width_mm,
                "height_mm": o.height_mm,
                "sill_height_mm": o.sill_height_mm,
                "swing": o.swing,
            }
            for o in openings
        ],
        obstacles=[
            {
                "id": str(ob.id),
                "kind": ob.kind,
                "wall": ob.wall,
                "position_mm": ob.position_mm,
                "width_mm": ob.width_mm,
                "depth_mm": ob.depth_mm,
                "height_mm": ob.height_mm,
                "notes": ob.notes,
            }
            for ob in obstacles
        ],
    )


async def load_catalog(session: AsyncSession) -> tuple[list[dict], dict[str, dict]]:
    cabs = (await session.execute(select(CabinetItem))).scalars().all()
    apps = (await session.execute(select(Appliance))).scalars().all()
    cabinet_rows = [
        {
            "id": str(c.id),
            "code": c.code,
            "name": c.name,
            "cabinet_type": c.cabinet_type,
            "width_mm": c.width_mm,
            "height_mm": c.height_mm,
            "depth_mm": c.depth_mm,
            "base_price": float(c.base_price),
            "is_active": c.is_active,
        }
        for c in cabs
    ]
    appliance_rows = {
        a.appliance_type: {
            "id": str(a.id),
            "code": a.code,
            "name": a.name,
            "brand": a.brand,
            "model": a.model,
            "width_mm": a.width_mm,
            "height_mm": a.height_mm,
            "depth_mm": a.depth_mm,
            "price": float(a.price),
        }
        for a in apps
    }
    return cabinet_rows, appliance_rows


async def load_materials(session: AsyncSession) -> dict[str, Material]:
    mats = (await session.execute(select(Material))).scalars().all()
    return {m.code: m for m in mats}


async def generate_design(
    session: AsyncSession,
    project_id: uuid.UUID,
    room_id: uuid.UUID,
    layout: str,
    countertop_material_id: uuid.UUID | None = None,
    cabinet_material_id: uuid.UUID | None = None,
) -> DesignModel:
    room_param = await build_room_param(session, room_id)
    cabinet_rows, appliance_rows = await load_catalog(session)

    countertop_material = None
    cabinet_material = None
    if countertop_material_id:
        m = await session.get(Material, countertop_material_id)
        if m:
            countertop_material = {"id": str(m.id), "name": m.name, "code": m.code}
    if cabinet_material_id:
        m = await session.get(Material, cabinet_material_id)
        if m:
            cabinet_material = {"id": str(m.id), "name": m.name, "code": m.code}

    engine = KitchenDesignEngine(
        room=room_param,
        layout=layout,
        cabinets=cabinet_rows,
        appliances=appliance_rows,
        countertop_material=countertop_material,
        cabinet_material=cabinet_material,
    )
    design = engine.generate()
    return design
