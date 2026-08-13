from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import CurrentContext, get_tenant_db, resolve_context
from app.files.models import ProjectFile

router = APIRouter(prefix="/api/v1", tags=["files"])


def _storage() -> Path:
    p = Path(settings.file_storage_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.post("/projects/{project_id}/files", status_code=201)
async def upload_file(
    project_id: str,
    ctx: CurrentContext = Depends(resolve_context),
    db: AsyncSession = Depends(get_tenant_db),
    file: UploadFile = File(...),
):
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, detail="file_too_large")

    key = f"tnt/{ctx.tenant_id}/{project_id}/{uuid.uuid4().hex}_{file.filename}"
    path = _storage() / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

    record = ProjectFile(
        project_id=uuid.UUID(project_id),
        kind="room_photo",
        original_name=file.filename or "photo.jpg",
        content_type=file.content_type,
        size_bytes=len(data),
        storage_key=key,
        uploaded_by=ctx.user_id,
    )
    db.add(record)
    await db.flush()
    return {
        "id": str(record.id),
        "original_name": record.original_name,
        "content_type": record.content_type,
        "size_bytes": record.size_bytes,
        "uploaded_at": record.uploaded_at.isoformat(),
    }


@router.get("/projects/{project_id}/files")
async def list_files(
    project_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    from sqlalchemy import select

    from app.files.models import ProjectFile as PF

    rows = (await db.execute(select(PF).where(PF.project_id == project_id))).scalars().all()
    return [
        {
            "id": str(r.id),
            "original_name": r.original_name,
            "content_type": r.content_type,
            "size_bytes": r.size_bytes,
            "uploaded_at": r.uploaded_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/files/{file_id}/content")
async def download_file(
    file_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    rec = await db.get(ProjectFile, file_id)
    if not rec:
        raise HTTPException(404, detail="file_not_found")
    path = _storage() / rec.storage_key
    if not path.exists():
        raise HTTPException(404, detail="file_missing")
    return FileResponse(path, filename=rec.original_name)
