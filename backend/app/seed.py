"""Seed a realistic demo: tenant + user + catalogs + demo project with a
generated parametric kitchen design.

Run:  .venv/bin/python -m app.seed
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import Appliance, CabinetItem, Material
from app.core.database import (
    TenantBase,
    create_tenant_schema,
    engine,
    get_tenant_session,
    init_platform_db,
    tenant_schema,
)
from app.core.security import hash_password
from app.design.models import Design, DesignVersion
from app.design.services import generate_design
from app.projects.models import Customer, Project
from app.rooms.models import Obstacle, Opening, Room, Wall
from app.tenants.models import Tenant, TenantMembership, User

DEMO_EMAIL = "demo@firx.ir"
DEMO_PASSWORD = "demo1234"
DEMO_COMPANY = "شرکت طراحی آشپزخانه فرکس"


async def seed_platform() -> User:
    await init_platform_db()
    from app.core.database import PlatformSession

    async with PlatformSession() as s:
        user = (await s.execute(select(User).where(User.email == DEMO_EMAIL))).scalar_one_or_none()
        if user:
            return user
        user = User(
            email=DEMO_EMAIL,
            full_name="کاربر نمایشی",
            password_hash=hash_password(DEMO_PASSWORD),
        )
        s.add(user)
        await s.flush()
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            name=DEMO_COMPANY,
            company_name=DEMO_COMPANY,
            schema_name=tenant_schema(tenant_id),
        )
        s.add(tenant)
        await s.flush()
        s.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role="admin"))
        await s.commit()
        await create_tenant_schema(tenant.id)
        return user


async def seed_catalog(s: AsyncSession) -> None:
    cabinets = [
        ("BASE-300", "کابینت زمینی ۳۰۰", "base", 300, 720, 600, 120),
        ("BASE-400", "کابینت زمینی ۴۰۰", "base", 400, 720, 600, 140),
        ("BASE-600", "کابینت زمینی ۶۰۰", "base", 600, 720, 600, 160),
        ("BASE-800", "کابینت زمینی ۸۰۰", "base", 800, 720, 600, 180),
        ("WALL-600", "کابینت دیواری ۶۰۰", "wall", 600, 900, 350, 110),
        ("WALL-800", "کابینت دیواری ۸۰۰", "wall", 800, 900, 350, 130),
        ("TALL-600", "کابینت بلند ۶۰۰", "tall", 600, 2200, 600, 220),
        ("CORNER-300", "کابینت گوشه ۳۰۰", "corner", 300, 720, 600, 190),
        ("SINK-900", "کابینت سینک ۹۰۰", "sink", 900, 720, 600, 200),
        ("DRAWER-600", "کابینت کشویی ۶۰۰", "drawer", 600, 720, 600, 190),
        ("OVEN-600", "کابینت فر ۶۰۰", "oven", 600, 720, 600, 210),
        ("FRIDGE-700", "جای یخچال ۷۰۰", "fridge", 700, 2200, 600, 0),
    ]
    for code, name, ctype, w, h, d, price in cabinets:
        if not (await s.execute(select(CabinetItem).where(CabinetItem.code == code))).scalar_one_or_none():
            s.add(CabinetItem(code=code, name=name, cabinet_type=ctype, width_mm=w, height_mm=h, depth_mm=d, base_price=price))

    materials = [
        ("MDF-18", "ام‌دی‌اف ۱۸ میلی‌متر", "mdf", 18, "کرم", 45),
        ("MDF-16", "ام‌دی‌اف ۱۶ میلی‌متر", "mdf", 16, "سفید", 42),
        ("PB-16", "نئوپان ۱۶ میلی‌متر", "particleboard", 16, "بلوط", 28),
        ("MEL-16", "ملامین ۱۶ میلی‌متر", "melamine", 16, "گرافیت", 32),
        ("PLY-18", "پلای‌وود ۱۸ میلی‌متر", "plywood", 18, "توس", 55),
    ]
    for code, name, mtype, t, color, price in materials:
        if not (await s.execute(select(Material).where(Material.code == code))).scalar_one_or_none():
            s.add(Material(code=code, name=name, material_type=mtype, thickness_mm=t, color=color, price_per_sqm=price))

    appliances = [
        ("FRIDGE", "یخچال فریزر", "Bosch", "KIR81AF30", "fridge", 700, 1780, 600, 980),
        ("COOKTOP", "اجاق گازی", "Beko", "HIC64401", "cooktop", 600, 60, 520, 380),
        ("OVEN", "فر توکار", "Beko", "OIM24500", "oven", 600, 595, 550, 560),
        ("HOOD", "هود", "Elica", "Pixie", "hood", 900, 300, 500, 260),
        ("DISHWASHER", "ماشین ظرفشویی", "Beko", "DFS26010", "dishwasher", 600, 820, 600, 520),
        ("SINK", "سینک استیل", "Blanco", "Subline", "sink", 800, 200, 500, 160),
        ("FAUCET", "شیر آب", "Grohe", "Euro", "faucet", 200, 300, 200, 140),
    ]
    for code, name, brand, model, atype, w, h, d, price in appliances:
        if not (await s.execute(select(Appliance).where(Appliance.code == code))).scalar_one_or_none():
            s.add(Appliance(code=code, name=name, brand=brand, model=model, appliance_type=atype, width_mm=w, height_mm=h, depth_mm=d, price=price))


async def seed_demo_project(user: User) -> None:
    tenant = None
    from app.core.database import PlatformSession

    async with PlatformSession() as ps:
        mem = (await ps.execute(select(TenantMembership).where(TenantMembership.user_id == user.id))).scalar_one()
        tenant = await ps.get(Tenant, mem.tenant_id)

    async for s in get_tenant_session(tenant.schema_name):
        await seed_catalog(s)
        await s.flush()

        # customer
        customer = Customer(first_name="علی", last_name="محمدی", phone="۰۹۱۲۳۴۵۶۷۸۹", email="ali@example.ir", notes="مشتری نمایشی")
        s.add(customer)
        await s.flush()

        # project
        project = Project(name="آشپزخانه آپارتمان مدرن", customer_id=customer.id, status="designing", notes="پروژه نمایشی")
        s.add(project)
        await s.flush()

        # room: 4200 x 3600 x 2800, west window, south door
        room = Room(project_id=project.id, name="آشپزخانه", width_mm=4200, length_mm=3600, height_mm=2800)
        s.add(room)
        await s.flush()
        walls = [
            ("north", 4200, 150), ("south", 4200, 150), ("west", 3600, 150), ("east", 3600, 150),
        ]
        for side, length, th in walls:
            s.add(Wall(room_id=room.id, side=side, length_mm=length, thickness_mm=th))
        s.add(Opening(room_id=room.id, kind="window", wall="west", position_mm=1050, width_mm=1500, height_mm=1500, sill_height_mm=900))
        s.add(Opening(room_id=room.id, kind="door", wall="south", position_mm=3300, width_mm=900, height_mm=2100, sill_height_mm=0, swing="in"))
        s.add(Obstacle(room_id=room.id, kind="radiator", wall="east", position_mm=400, width_mm=1200, depth_mm=120, height_mm=900, notes="رادیاتور"))
        await s.flush()

        # generate a design
        design = await generate_design(s, project.id, room.id, "L")
        d = Design(
            project_id=project.id,
            room_id=room.id,
            name=design.name,
            layout=design.layout,
            snapshot=design.model_dump(mode="json"),
            current_version=1,
        )
        s.add(d)
        await s.flush()
        s.add(DesignVersion(design_id=d.id, version_no=1, snapshot=d.snapshot, change_desc="تولید اولیه طرح"))
        await s.flush()
        print("demo design id:", d.id)


async def main() -> None:
    user = await seed_platform()
    await seed_demo_project(user)
    print("seed complete. login with", DEMO_EMAIL, "/", DEMO_PASSWORD)


if __name__ == "__main__":
    asyncio.run(main())
