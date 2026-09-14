from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bom.costing import derive_cost
from app.bom.services import generate_bom
from app.catalog.models import Appliance, CabinetItem, Material
from app.catalog.schemas import DesignEditRequest, DesignGenerateRequest, VersionCreateRequest
from app.core.deps import CurrentContext, get_tenant_db, resolve_context
from app.design.drawings import plan_geometry, run_elevations
from app.design.dxf_export import design_to_dxf
from app.design.models import BOMItem, Design, DesignVersion, ValidationResult
from app.design.parametric import DesignModel, DesignVersionOut
from app.design.services import generate_design
from app.projects.models import Project
from app.rooms.models import Room
from app.validation.engine import ConstraintEngine

router = APIRouter(prefix="/api/v1", tags=["design"])


def _catalog_by_id(db_rows) -> dict[str, dict]:
    out = {}
    for c in db_rows:
        out[str(c.id)] = {
            "id": str(c.id),
            "code": c.code,
            "name": c.name,
            "cabinet_type": c.cabinet_type,
            "width_mm": c.width_mm,
            "height_mm": c.height_mm,
            "depth_mm": c.depth_mm,
            "base_price": float(c.base_price),
        }
    return out


async def _build_cost_config(
    db: AsyncSession,
    project_id,
    design: DesignModel,
) -> tuple:
    """Shared cost config for a design: project override merged over defaults
    plus tenant appliance and material prices. Returns (config, appliance_prices)."""
    from app.bom.costing import DEFAULT_CONFIG

    appliances = (await db.execute(select(Appliance))).scalars().all()
    appliance_prices = {str(a.id): float(a.price) for a in appliances}
    materials = (await db.execute(select(Material))).scalars().all()
    material_prices: dict[str, float] = {}
    for m in materials:
        material_prices[m.name] = float(m.price_per_sqm)
        material_prices[m.code] = float(m.price_per_sqm)

    cfg = DEFAULT_CONFIG.model_copy(deep=True)
    project = await db.get(Project, project_id)
    if project and project.costing_config:
        cfg = cfg.model_copy(update=project.costing_config)
    cfg = cfg.model_copy(update={
        "material_price_per_sqm": {**material_prices, **cfg.material_price_per_sqm},
    })
    return cfg, appliance_prices


async def _appliance_by_id(db_rows) -> dict[str, dict]:
    out = {}
    for a in db_rows:
        out[str(a.id)] = {
            "id": str(a.id),
            "code": a.code,
            "name": a.name,
            "brand": a.brand,
            "appliance_type": a.appliance_type,
            "width_mm": a.width_mm,
            "height_mm": a.height_mm,
            "depth_mm": a.depth_mm,
            "price": float(a.price),
        }
    return out


def _appliance_map_sync(db_rows) -> dict[str, dict]:
    return {
        str(a.id): {
            "id": str(a.id),
            "code": a.code,
            "name": a.name,
            "brand": a.brand,
            "appliance_type": a.appliance_type,
            "width_mm": a.width_mm,
            "height_mm": a.height_mm,
            "depth_mm": a.depth_mm,
            "price": float(a.price),
        }
        for a in db_rows
    }


@router.get("/projects/{project_id}/designs")
async def list_project_designs(
    project_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    """Designs belonging to a project, with deterministic derived cost."""
    from app.bom.costing import DEFAULT_CONFIG, derive_cost

    designs = (await db.execute(
        select(Design).where(Design.project_id == uuid.UUID(project_id)).order_by(Design.updated_at.desc())
    )).scalars().all()
    if not designs:
        return []

    cfg = DEFAULT_CONFIG.model_copy(deep=True)
    project = await db.get(Project, uuid.UUID(project_id))
    if project and project.costing_config:
        cfg = cfg.model_copy(update=project.costing_config)
    appliances = (await db.execute(select(Appliance))).scalars().all()
    appliance_prices = {str(a.id): float(a.price) for a in appliances}
    materials = (await db.execute(select(Material))).scalars().all()
    material_prices: dict[str, float] = {}
    for m in materials:
        material_prices[m.name] = float(m.price_per_sqm)
        material_prices[m.code] = float(m.price_per_sqm)
    cfg = cfg.model_copy(update={"material_price_per_sqm": material_prices})

    rows = []
    for d in designs:
        try:
            design = DesignModel.model_validate(d.snapshot)
            retail = derive_cost(design, cfg, appliance_prices=appliance_prices)["summary"]["total_retail"]
        except Exception:
            retail = 0.0
        rows.append({
            "id": str(d.id),
            "name": d.name,
            "layout": d.layout,
            "current_version": d.current_version,
            "updated_at": d.updated_at.isoformat(),
            "total_retail": round(retail, 2),
        })
    return rows


@router.post("/projects/{project_id}/designs/generate", response_model=DesignModel)
async def generate(
    project_id: str,
    body: DesignGenerateRequest,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="project_not_found")
    design = await generate_design(
        db, project_id, body.room_id, body.layout,
        countertop_material_id=body.countertop_material_id,
        cabinet_material_id=body.cabinet_material_id,
    )

    # persist as a Design + Version 1
    d = Design(
        project_id=uuid.UUID(project_id),
        room_id=body.room_id,
        name=design.name,
        layout=design.layout,
        snapshot=design.model_dump(mode="json"),
        current_version=1,
    )
    db.add(d)
    await db.flush()
    db.add(DesignVersion(design_id=d.id, version_no=1, snapshot=d.snapshot, change_desc="تولید اولیه طرح"))
    design.id = str(d.id)
    await db.flush()
    return design


@router.get("/designs/{design_id}", response_model=DesignModel)
async def get_design(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    return d.snapshot


@router.put("/designs/{design_id}", response_model=DesignModel)
async def edit_design(
    design_id: str,
    body: DesignEditRequest,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    """Client submits edited parametric entities; backend merges and re-validates."""
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    snap = dict(d.snapshot)
    if body.cabinets is not None:
        snap["cabinets"] = body.cabinets
    if body.appliances is not None:
        snap["appliances"] = body.appliances
    # assign a NEW dict so SQLAlchemy's JSON change detection fires (mutating
    # the loaded dict in place would never persist).
    d.snapshot = snap
    await db.flush()
    return snap


@router.get("/designs/{design_id}/validate")
async def validate_design(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    design = DesignModel.model_validate(d.snapshot)
    engine = ConstraintEngine(design)
    result = engine.validate()
    # persist latest
    existing = (await db.execute(
        select(ValidationResult).where(ValidationResult.design_id == d.id)
    )).scalars().first()
    if existing:
        existing.results = result["results"]
        existing.score = result["score"]
    else:
        db.add(ValidationResult(design_id=d.id, results=result["results"], score=result["score"]))
    await db.flush()
    return result


@router.get("/designs/{design_id}/bom")
async def bom(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    design = DesignModel.model_validate(d.snapshot)
    cabs = (await db.execute(select(CabinetItem))).scalars().all()
    apps = (await db.execute(select(Appliance))).scalars().all()
    catalog = _catalog_by_id(cabs)
    catalog.update(_appliance_map_sync(apps))
    return generate_bom(design, catalog)


@router.get("/designs/{design_id}/cut-list")
async def cut_list(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    """Manufacturing cut list, derived from Cabinet params → components.

    Every part carries cabinet number, stable part id, dimensions, thickness,
    material, quantity, grain direction and edge banding spec. No CNC output.
    """
    from app.bom.components import aggregate_parts, sheet_count
    from app.design.derive import number_cabinets

    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    design = DesignModel.model_validate(d.snapshot)
    labels = number_cabinets(design)
    parts = aggregate_parts(design.cabinets, labels)
    return {
        "design_id": design_id,
        "parts": parts,
        "part_count": len(parts),
        "total_qty": sum(p["qty"] for p in parts),
        "sheets": sheet_count(design.cabinets),
    }


@router.get("/designs/{design_id}/visualization")
async def visualization_input(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    """Model-derived AI visualization input for a saved design.

    Returns the stored `visual_prompt` (generated from the parametric model)
    plus a structured summary the AI renderer can consume. The AI output is
    ONLY an image view — it never writes geometry back into the model.
    """
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    design = DesignModel.model_validate(d.snapshot)
    labels = None
    from app.design.derive import build_visual_prompt, number_cabinets
    labels = number_cabinets(design)
    cabinets = [
        {
            "id": c.id,
            "label": labels.get(c.id, c.name),
            "type": c.type,
            "width_mm": c.width_mm,
            "height_mm": c.height_mm,
            "depth_mm": c.depth_mm,
            "material": c.material_name,
            "door_config": c.door_config,
            "drawers": c.drawer_count,
            "shelves": c.shelf_count,
        }
        for c in design.cabinets
    ]
    return {
        "design_id": design_id,
        "prompt": design.visual_prompt or build_visual_prompt(design),
        "cabinets": cabinets,
        "appliances": [
            {"type": a.appliance_type, "name": a.name or a.appliance_type}
            for a in design.appliances
        ],
        "layout": design.layout,
        "note": "خروجی هوش مصنوعی فقط یک نمای تصویری است؛ منبع هندسی مدل پارامتریک است.",
    }


@router.get("/designs/{design_id}/cost")
async def cost(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    """Deterministic cost/quote for a saved design, derived from the model.

    Pricing comes from the configurable PricingConfig: the project's per-
    project override (if any) merged over shop defaults, plus tenant appliance
    prices. The quote is a pure function of the snapshot + config.
    """
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    design = DesignModel.model_validate(d.snapshot)
    cfg, appliance_prices = await _build_cost_config(db, d.project_id, design)
    return derive_cost(design, cfg, appliance_prices=appliance_prices)


@router.get("/designs/{design_id}/quote.html")
async def quote_html(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    """Printable client-facing quote (RTL HTML) derived from the same cost
    breakdown the /cost endpoint returns. Save-as-PDF from the browser."""
    from app.bom.quote import quote_html as build_quote_html

    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    design = DesignModel.model_validate(d.snapshot)
    cfg, appliance_prices = await _build_cost_config(db, d.project_id, design)
    cost = derive_cost(design, cfg, appliance_prices=appliance_prices)
    html = build_quote_html(design, cost)
    return HTMLResponse(
        html,
        headers={"Content-Disposition": f'inline; filename="quote_{design_id[:8]}.html"'},
    )


@router.get("/designs/{design_id}/drawings")
async def drawings(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    """Derived technical-drawing geometry: plan view + per-wall-run elevations.

    Pure functions of the saved parametric snapshot; nothing stored.
    """
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    design = DesignModel.model_validate(d.snapshot)
    return {
        "design_id": design_id,
        "plan": plan_geometry(design),
        "elevations": run_elevations(design),
    }


@router.get("/designs/{design_id}/drawings.dxf")
async def export_dxf(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    """DXF R12 shop drawing, serialized from the same drawing geometry."""
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    design = DesignModel.model_validate(d.snapshot)
    return PlainTextResponse(
        design_to_dxf(design),
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="design_{design_id[:8]}.dxf"'},
    )


@router.get("/designs/{design_id}/versions", response_model=list[DesignVersionOut])
async def list_versions(
    design_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    versions = (await db.execute(
        select(DesignVersion).where(DesignVersion.design_id == d.id).order_by(DesignVersion.version_no.desc())
    )).scalars().all()
    return [
        DesignVersionOut(
            id=str(v.id),
            version_no=v.version_no,
            change_desc=v.change_desc,
            snapshot=v.snapshot,
            created_by=str(v.created_by) if v.created_by else None,
            created_at=v.created_at.isoformat(),
        )
        for v in versions
    ]


@router.post("/designs/{design_id}/versions", response_model=DesignVersionOut, status_code=201)
async def save_version(
    design_id: str,
    body: VersionCreateRequest,
    ctx: CurrentContext = Depends(resolve_context),
    db: AsyncSession = Depends(get_tenant_db),
):
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    d.current_version += 1
    v = DesignVersion(
        design_id=d.id,
        version_no=d.current_version,
        snapshot=d.snapshot,
        change_desc=body.change_desc or f"نسخه {d.current_version}",
        created_by=ctx.user_id,
    )
    db.add(v)
    await db.flush()
    return DesignVersionOut(
        id=str(v.id),
        version_no=v.version_no,
        change_desc=v.change_desc,
        snapshot=v.snapshot,
        created_by=str(v.created_by),
        created_at=v.created_at.isoformat(),
    )


@router.post("/designs/{design_id}/restore/{version_no}", response_model=DesignModel)
async def restore_version(
    design_id: str,
    version_no: int,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    d = await db.get(Design, design_id)
    if not d:
        raise HTTPException(404, detail="design_not_found")
    v = (await db.execute(
        select(DesignVersion).where(DesignVersion.design_id == d.id, DesignVersion.version_no == version_no)
    )).scalar_one_or_none()
    if not v:
        raise HTTPException(404, detail="version_not_found")
    d.snapshot = v.snapshot
    d.current_version += 1
    db.add(DesignVersion(
        design_id=d.id,
        version_no=d.current_version,
        snapshot=d.snapshot,
        change_desc=f"بازیابی نسخه {version_no}",
        created_by=None,
    ))
    await db.flush()
    return d.snapshot
