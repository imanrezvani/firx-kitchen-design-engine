from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentContext, get_tenant_db, resolve_context
from app.projects.models import Project
from app.schemas import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    return (await db.execute(select(Project).order_by(Project.created_at.desc()))).scalars().all()


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    project = Project(**body.model_dump())
    db.add(project)
    await db.flush()
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="project_not_found")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="project_not_found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(project, k, v)
    await db.flush()
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="project_not_found")
    await db.delete(project)
    await db.flush()
