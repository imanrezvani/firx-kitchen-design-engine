from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_platform_session, get_tenant_session, tenant_schema
from app.core.security import decode_token
from app.tenants.models import Tenant, TenantMembership, User

bearer = HTTPBearer(auto_error=False)


class CurrentContext:
    """Resolved tenant + user for the current request."""

    def __init__(self, user: User, tenant: Tenant | None, membership: TenantMembership | None):
        self.user = user
        self.tenant = tenant
        self.membership = membership
        self.schema = tenant_schema(tenant.id) if tenant else "public"

    @property
    def user_id(self) -> uuid.UUID:
        return self.user.id

    @property
    def tenant_id(self) -> uuid.UUID | None:
        return self.tenant.id if self.tenant else None


async def resolve_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_platform_session),
) -> CurrentContext:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="unauthenticated")
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_token")

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="user_inactive")

    mem = (
        await session.execute(
            select(TenantMembership)
            .where(TenantMembership.user_id == user_id)
            .order_by(TenantMembership.created_at)
        )
    ).scalars().first()

    tenant = None
    if mem:
        tenant = await session.get(Tenant, mem.tenant_id)
        if tenant and not tenant.is_active:
            tenant = None

    return CurrentContext(user=user, tenant=tenant, membership=mem)


async def get_tenant_db(ctx: CurrentContext = Depends(resolve_context)):
    """Tenant-scoped session pinned to the tenant schema."""
    if ctx.tenant is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="no_tenant")
    async for session in get_tenant_session(ctx.schema):
        yield session
