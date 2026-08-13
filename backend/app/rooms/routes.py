from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentContext, get_tenant_db, resolve_context
from app.projects.models import Project
from app.rooms.models import Obstacle, Opening, Room, Wall
from app.schemas import (
    ObstacleCreate,
    ObstacleOut,
    OpeningCreate,
    OpeningOut,
    RoomCreate,
    RoomOut,
    RoomUpdate,
    WallCreate,
    WallOut,
)

router = APIRouter(prefix="/api/v1", tags=["rooms"])


async def _get_room(db: AsyncSession, room_id: str) -> Room:
    try:
        room = await db.get(Room, uuid.UUID(room_id))
    except ValueError:
        raise HTTPException(404, detail="room_not_found")
    if not room:
        raise HTTPException(404, detail="room_not_found")
    return room


async def _room_out(db: AsyncSession, room: Room) -> RoomOut:
    walls = (await db.execute(select(Wall).where(Wall.room_id == room.id))).scalars().all()
    openings = (await db.execute(select(Opening).where(Opening.room_id == room.id))).scalars().all()
    obstacles = (await db.execute(select(Obstacle).where(Obstacle.room_id == room.id))).scalars().all()
    return RoomOut(
        id=room.id,
        project_id=room.project_id,
        name=room.name,
        width_mm=room.width_mm,
        length_mm=room.length_mm,
        height_mm=room.height_mm,
        notes=room.notes,
        walls=[WallOut.model_validate(w) for w in walls],
        openings=[OpeningOut.model_validate(o) for o in openings],
        obstacles=[ObstacleOut.model_validate(o) for o in obstacles],
        created_at=room.created_at,
    )


@router.get("/projects/{project_id}/room", response_model=RoomOut | None)
async def get_project_room(
    project_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    room = (await db.execute(select(Room).where(Room.project_id == project_id))).scalars().first()
    if not room:
        return None
    return await _room_out(db, room)


@router.post("/projects/{project_id}/room", response_model=RoomOut, status_code=201)
async def create_or_replace_room(
    project_id: str,
    body: RoomCreate,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="project_not_found")

    existing = (await db.execute(select(Room).where(Room.project_id == project_id))).scalars().first()
    if existing:
        await db.execute(delete(Wall).where(Wall.room_id == existing.id))
        await db.execute(delete(Opening).where(Opening.room_id == existing.id))
        await db.execute(delete(Obstacle).where(Obstacle.room_id == existing.id))
        room = existing
        room.name = body.name
        room.width_mm = body.width_mm
        room.length_mm = body.length_mm
        room.height_mm = body.height_mm
        room.notes = body.notes
    else:
        room = Room(
            project_id=uuid.UUID(project_id),
            name=body.name,
            width_mm=body.width_mm,
            length_mm=body.length_mm,
            height_mm=body.height_mm,
            notes=body.notes,
        )
        db.add(room)
        await db.flush()

    for w in body.walls:
        db.add(Wall(room_id=room.id, **w.model_dump()))
    for o in body.openings:
        db.add(Opening(room_id=room.id, **o.model_dump()))
    for ob in body.obstacles:
        db.add(Obstacle(room_id=room.id, **ob.model_dump()))
    await db.flush()
    return await _room_out(db, room)


@router.put("/projects/{project_id}/room", response_model=RoomOut)
async def update_room(
    project_id: str,
    body: RoomUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    room = (await db.execute(select(Room).where(Room.project_id == project_id))).scalars().first()
    if not room:
        raise HTTPException(404, detail="room_not_found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(room, k, v)
    await db.flush()
    return await _room_out(db, room)


# --- walls / openings / obstacles sub-resources -----------------------------
@router.post("/rooms/{room_id}/walls", response_model=WallOut, status_code=201)
async def add_wall(room_id: str, body: WallCreate, db: AsyncSession = Depends(get_tenant_db),
                   _ctx: CurrentContext = Depends(resolve_context)):
    await _get_room(db, room_id)
    w = Wall(room_id=uuid.UUID(room_id), **body.model_dump())
    db.add(w)
    await db.flush()
    return w


@router.delete("/rooms/{room_id}/walls/{wall_id}", status_code=204)
async def delete_wall(room_id: str, wall_id: str, db: AsyncSession = Depends(get_tenant_db),
                      _ctx: CurrentContext = Depends(resolve_context)):
    w = await db.get(Wall, wall_id)
    if not w:
        raise HTTPException(404, detail="wall_not_found")
    await db.delete(w)
    await db.flush()


@router.post("/rooms/{room_id}/openings", response_model=OpeningOut, status_code=201)
async def add_opening(room_id: str, body: OpeningCreate, db: AsyncSession = Depends(get_tenant_db),
                      _ctx: CurrentContext = Depends(resolve_context)):
    await _get_room(db, room_id)
    o = Opening(room_id=uuid.UUID(room_id), **body.model_dump())
    db.add(o)
    await db.flush()
    return o


@router.delete("/rooms/{room_id}/openings/{opening_id}", status_code=204)
async def delete_opening(room_id: str, opening_id: str, db: AsyncSession = Depends(get_tenant_db),
                         _ctx: CurrentContext = Depends(resolve_context)):
    o = await db.get(Opening, opening_id)
    if not o:
        raise HTTPException(404, detail="opening_not_found")
    await db.delete(o)
    await db.flush()


@router.post("/rooms/{room_id}/obstacles", response_model=ObstacleOut, status_code=201)
async def add_obstacle(room_id: str, body: ObstacleCreate, db: AsyncSession = Depends(get_tenant_db),
                       _ctx: CurrentContext = Depends(resolve_context)):
    await _get_room(db, room_id)
    ob = Obstacle(room_id=uuid.UUID(room_id), **body.model_dump())
    db.add(ob)
    await db.flush()
    return ob


@router.delete("/rooms/{room_id}/obstacles/{obstacle_id}", status_code=204)
async def delete_obstacle(room_id: str, obstacle_id: str, db: AsyncSession = Depends(get_tenant_db),
                          _ctx: CurrentContext = Depends(resolve_context)):
    ob = await db.get(Obstacle, obstacle_id)
    if not ob:
        raise HTTPException(404, detail="obstacle_not_found")
    await db.delete(ob)
    await db.flush()
