from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import create_tenant_schema, get_platform_session, get_tenant_session, tenant_schema
from app.core.deps import CurrentContext, resolve_context
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.schemas import LoginRequest, MeResponse, RegisterRequest, TenantOut, TokenResponse, UserOut
from app.seed import seed_catalog
from app.tenants.models import Tenant, TenantMembership, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_platform_session),
):
    if not body.email:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="email_required")
    existing = (await session.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email_exists")

    user = User(
        email=body.email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.flush()

    tenant_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        name=body.company_name,
        company_name=body.company_name,
        schema_name=tenant_schema(tenant_id),
        is_active=True,
    )
    session.add(tenant)
    await session.flush()

    membership = TenantMembership(tenant_id=tenant.id, user_id=user.id, role="admin")
    session.add(membership)
    await session.commit()

    # provision the tenant's operational schema + tables
    await create_tenant_schema(tenant.id)

    # seed the default catalog (cabinets/materials/appliances) for the tenant
    async for ts in get_tenant_session(tenant.schema_name):
        await seed_catalog(ts)
        await ts.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserOut(id=user.id, email=user.email, full_name=user.full_name),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_platform_session)):
    user = (await session.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserOut(id=user.id, email=user.email, full_name=user.full_name),
    )


@router.get("/me", response_model=MeResponse)
async def me(ctx: CurrentContext = Depends(resolve_context)):
    return MeResponse(
        user=UserOut(id=ctx.user.id, email=ctx.user.email, full_name=ctx.user.full_name),
        tenant=TenantOut(
            id=ctx.tenant.id,
            name=ctx.tenant.name,
            company_name=ctx.tenant.company_name,
            role=ctx.membership.role if ctx.membership else None,
        )
        if ctx.tenant
        else None,
    )


@router.post("/logout", status_code=204)
async def logout(ctx: CurrentContext = Depends(resolve_context)):
    # Stateless JWT; client discards the token. Endpoint exists for parity.
    return None
