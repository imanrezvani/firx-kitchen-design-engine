from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bom.costing import DEFAULT_CONFIG, derive_cost
from app.catalog.models import Appliance, Material
from app.core.deps import CurrentContext, get_tenant_db, resolve_context
from app.design.models import Design
from app.design.parametric import DesignModel
from app.projects.models import Customer, Project

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/dashboard/stats")
async def dashboard_stats(
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    project_count = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    customer_count = (await db.execute(select(func.count(Customer.id)))).scalar() or 0
    design_count = (await db.execute(select(func.count(Design.id)))).scalar() or 0

    statuses = (await db.execute(
        select(Project.status, func.count(Project.id)).group_by(Project.status)
    )).all()
    active_projects = sum(c for s, c in statuses if s not in ("completed", "archived"))
    recent_projects = (
        (await db.execute(select(Project).order_by(Project.created_at.desc()).limit(5))).scalars().all()
    )
    recent_designs = (
        (await db.execute(select(Design).order_by(Design.updated_at.desc()).limit(5))).scalars().all()
    )

    # deterministic cost per recent design (model-derived; project override applied)
    appliances = (await db.execute(select(Appliance))).scalars().all()
    appliance_prices = {str(a.id): float(a.price) for a in appliances}
    materials = (await db.execute(select(Material))).scalars().all()
    material_prices: dict[str, float] = {}
    for m in materials:
        material_prices[m.name] = float(m.price_per_sqm)
        material_prices[m.code] = float(m.price_per_sqm)
    cfg = DEFAULT_CONFIG.model_copy(deep=True)
    cfg = cfg.model_copy(update={"material_price_per_sqm": material_prices})

    design_rows = []
    for d in recent_designs:
        try:
            design = DesignModel.model_validate(d.snapshot)
            project = await db.get(Project, d.project_id)
            pc = cfg
            if project and project.costing_config:
                pc = cfg.model_copy(update=project.costing_config)
            cost = derive_cost(design, pc, appliance_prices=appliance_prices)
            retail = cost["summary"]["total_retail"]
        except Exception:
            retail = 0.0
        design_rows.append({
            "id": str(d.id),
            "project_id": str(d.project_id),
            "name": d.name,
            "layout": d.layout,
            "updated_at": d.updated_at.isoformat(),
            "total_retail": round(retail, 2),
        })

    return {
        "total_projects": project_count,
        "active_projects": active_projects,
        "customers": customer_count,
        "designs": design_count,
        "recent_projects": [
            {
                "id": str(p.id),
                "name": p.name,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in recent_projects
        ],
        "recent_designs": design_rows,
    }
