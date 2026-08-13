"""HTTP surface for the AI pipeline.

Exposes the deterministic pipeline to the frontend:

    POST /api/v1/ai/pipeline   KitchenSpecification → PipelineResult
    POST /api/v1/ai/spec        validate a KitchenSpecification and echo it
    GET  /api/v1/ai/providers   list available providers
    GET  /api/v1/ai/debug       diagnostic dump (never exposes credentials)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.cameras import CameraView
from app.ai.errors import AIProviderError, ProviderNotConfigured
from app.ai.pipeline import AIPipeline
from app.ai.providers import get_provider
from app.ai.spec import KitchenSpecification
from app.core.config import settings
from app.core.deps import resolve_context

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/pipeline")
async def run_pipeline(
    body: KitchenSpecification,
    provider_name: Annotated[str | None, Query()] = None,
    camera_views: Annotated[list[CameraView] | None, Query()] = None,
    _ctx=Depends(resolve_context),
):
    try:
        provider = get_provider(provider_name)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="unknown_provider")
    pipeline = AIPipeline(provider=provider)
    try:
        return await pipeline.run(body, camera_views)
    except AIProviderError as exc:
        code, detail = pipeline.map_error(exc)
        raise HTTPException(code, detail=detail)


@router.post("/spec")
async def validate_spec(body: KitchenSpecification, _ctx=Depends(resolve_context)):
    return {"valid": True, "spec": body}


@router.get("/providers")
async def list_providers(_ctx=Depends(resolve_context)):
    return {
        "providers": ["mock", "gpt", "gemini"],
        "default": "mock",
        "selected": get_provider().name,
    }


def _provider_status() -> dict:
    """Credential-free status of each provider (never exposes key values)."""
    statuses = {}
    for name, configured in (
        ("mock", True),
        ("gpt", bool(settings.openai_api_key)),
        ("gemini", bool(settings.gemini_api_key)),
    ):
        statuses[name] = {
            "configured": configured,
            "model": get_provider(name).model,
        }
    return statuses


@router.get("/debug")
async def pipeline_debug(_ctx=Depends(resolve_context)):
    """Diagnostic dump: normalized spec, prompt, selected provider, model and
    a validated DesignSpecification produced by the mock provider.

    API keys are NEVER included in this response or in any log line.
    """
    example = KitchenSpecification.model_validate(
        {
            "room": {"width": 4200, "length": 3600, "height": 2700, "unit": "mm"},
            "layout": "L_SHAPE",
            "doors": [{"wall": "north", "offset": 3200, "width": 900}],
            "windows": [{"wall": "south", "offset": 1400, "width": 1400, "sill_height": 900}],
            "cabinets": [
                {"type": "base", "width": 600, "height": 720, "depth": 600, "count": 6},
                {"type": "wall", "width": 600, "height": 900, "depth": 350, "count": 3},
            ],
            "appliances": [
                {"type": "refrigerator", "variant": "double_door"},
                {"type": "cooktop", "variant": "built_in"},
            ],
            "style": "modern",
        }
    )
    pipeline = AIPipeline(provider=get_provider("mock"))
    try:
        result = await pipeline.run(example)
    except ProviderNotConfigured:  # pragma: no cover — mock never fails
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="mock unavailable")

    return {
        "selected": {
            "provider": get_provider().name,
            "configured_providers": _provider_status(),
        },
        "pipeline": result.debug,
        "spec": example.model_dump(),
        "prompt": result.prompt.model_dump(),
        "design": result.design.model_dump(),
    }
