import uuid
from typing import AsyncGenerator

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class PlatformBase(DeclarativeBase):
    """Tables that live in the central platform database (public schema)."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TenantBase(DeclarativeBase):
    """Tables that are re-created inside each tenant's own schema.

    Tenant tables deliberately have NO explicit schema: they are resolved at
    runtime through PostgreSQL ``search_path`` which we pin to the current
    tenant schema for the lifetime of the request's transaction. This keeps
    the models identical whether a tenant lives in a schema today or in its
    own physical database tomorrow (Database-per-Tenant).
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    # Multi-tenant: search_path is switched per request, so asyncpg's
    # prepared-statement cache (which bakes in the schema at prepare time)
    # must be disabled to avoid cross-tenant statement reuse.
    connect_args={"prepared_statement_cache_size": 0},
)

# Sessions for platform-level queries (auth, tenants, memberships).
PlatformSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sessions for tenant data. search_path is pinned per request via a dependency.
TenantSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def tenant_schema(tenant_id: uuid.UUID) -> str:
    """Schema name for a tenant: tnt_<uuid hex>. Valid unquoted identifier."""
    return f"tnt_{tenant_id.hex}"


async def init_platform_db() -> None:
    """Create the public schema tables (idempotent)."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        await conn.run_sync(PlatformBase.metadata.create_all)


async def create_tenant_schema(tenant_id: uuid.UUID) -> None:
    """Create a tenant schema and its operational tables (idempotent)."""
    schema = tenant_schema(tenant_id)
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        await conn.execute(text(f'SET search_path = "{schema}", public'))
        await conn.run_sync(TenantBase.metadata.create_all)
        # Restore for the pooled connection: everything else runs through
        # explicit search_path pinning in the request dependency.
        await conn.execute(text("SET search_path = public"))


async def get_platform_session() -> AsyncGenerator[AsyncSession, None]:
    async with PlatformSession() as session:
        yield session


async def get_tenant_session(schema: str) -> AsyncGenerator[AsyncSession, None]:
    """Yields a session pinned to a tenant schema for this transaction."""
    async with TenantSession() as session:
        async with session.begin():
            await session.execute(text(f'SET search_path = "{schema}", public'))
            yield session
