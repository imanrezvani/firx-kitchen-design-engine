from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import Appliance, CabinetItem, Material
from app.catalog.schemas import (
    ApplianceCreate,
    ApplianceOut,
    ApplianceUpdate,
    CabinetItemCreate,
    CabinetItemOut,
    CabinetItemUpdate,
    MaterialCreate,
    MaterialOut,
    MaterialUpdate,
)
from app.core.deps import CurrentContext, get_tenant_db, resolve_context

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


def _crud(cls, create, update, out):
    """Build a small generic CRUD trio bound to a SQLAlchemy model."""

    async def _list(db: AsyncSession = Depends(get_tenant_db), _ctx: CurrentContext = Depends(resolve_context)):
        return (await db.execute(select(cls).order_by(cls.created_at.desc()))).scalars().all()

    async def _create(body: create, db: AsyncSession = Depends(get_tenant_db),
                      _ctx: CurrentContext = Depends(resolve_context)):
        obj = cls(**body.model_dump())
        db.add(obj)
        await db.flush()
        return obj

    async def _get(item_id: str, db: AsyncSession = Depends(get_tenant_db),
                   _ctx: CurrentContext = Depends(resolve_context)):
        obj = await db.get(cls, item_id)
        if not obj:
            raise HTTPException(404, detail="not_found")
        return obj

    async def _update(item_id: str, body: update, db: AsyncSession = Depends(get_tenant_db),
                      _ctx: CurrentContext = Depends(resolve_context)):
        obj = await db.get(cls, item_id)
        if not obj:
            raise HTTPException(404, detail="not_found")
        for k, v in body.model_dump(exclude_none=True).items():
            setattr(obj, k, v)
        await db.flush()
        return obj

    async def _delete(item_id: str, db: AsyncSession = Depends(get_tenant_db),
                      _ctx: CurrentContext = Depends(resolve_context)):
        obj = await db.get(cls, item_id)
        if not obj:
            raise HTTPException(404, detail="not_found")
        await db.delete(obj)
        await db.flush()

    return out, _list, _create, _get, _update, _delete


for model, create_s, update_s, out_s, prefix in [
    (CabinetItem, CabinetItemCreate, CabinetItemUpdate, CabinetItemOut, "/cabinets"),
    (Material, MaterialCreate, MaterialUpdate, MaterialOut, "/materials"),
    (Appliance, ApplianceCreate, ApplianceUpdate, ApplianceOut, "/appliances"),
]:
    out_s, list_f, create_f, get_f, update_f, delete_f = _crud(model, create_s, update_s, out_s)
    router.add_api_route(prefix, list_f, response_model=list[out_s], methods=["GET"])
    router.add_api_route(prefix, create_f, response_model=out_s, methods=["POST"], status_code=201)
    router.add_api_route(prefix + "/{item_id}", get_f, response_model=out_s, methods=["GET"])
    router.add_api_route(prefix + "/{item_id}", update_f, response_model=out_s, methods=["PUT"])
    router.add_api_route(prefix + "/{item_id}", delete_f, status_code=204, methods=["DELETE"])
