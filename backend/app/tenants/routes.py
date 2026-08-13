from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentContext, resolve_context
from app.schemas import TenantOut

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.get("/me", response_model=TenantOut)
async def my_tenant(ctx: CurrentContext = Depends(resolve_context)):
    return TenantOut(
        id=ctx.tenant.id,
        name=ctx.tenant.name,
        company_name=ctx.tenant.company_name,
        role=ctx.membership.role if ctx.membership else None,
    )
