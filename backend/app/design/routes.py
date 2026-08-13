from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bom.services import generate_bom
from app.catalog.models import Appliance, CabinetItem
from app.catalog.schemas import DesignEditRequest, DesignGenerateRequest, VersionCreateRequest
from app.core.deps import CurrentContext, get_tenant_db, resolve_context
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
    snap = d.snapshot
    if body.cabinets is not None:
        snap["cabinets"] = body.cabinets
    if body.appliances is not None:
        snap["appliances"] = body.appliances
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
