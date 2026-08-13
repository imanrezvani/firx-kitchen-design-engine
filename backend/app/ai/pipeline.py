"""AI design pipeline orchestration.

    Form
      → KitchenSpecification
      → PromptBuilder        (deterministic structured prompt)
      → AIProvider           (Mock / GPT / Gemini)
      → validated DesignSpecification

This is the deterministic, testable core of the architecture. The image, the
browser and any free-form text are never the source of truth — the
KitchenSpecification is.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from app.ai.cameras import CameraView, default_views
from app.ai.design_spec import DesignSpecification
from app.ai.errors import AIProviderError
from app.ai.providers import AIProvider, get_provider
from app.ai.prompt_builder import PromptBuilder, PromptDocument
from app.ai.spec import KitchenSpecification

logger = logging.getLogger(__name__)


class PipelineResult(BaseModel):
    spec: KitchenSpecification
    prompt: PromptDocument
    design: DesignSpecification
    provider: str = "mock"
    model: str = ""

    @property
    def debug(self) -> dict[str, Any]:
        """Structured, credential-free summary for debugging/diagnostics."""
        return {
            "provider": self.provider,
            "model": self.model,
            "spec_version": self.spec.version,
            "layout": self.spec.layout.value,
            "style": self.spec.style.value,
            "room": self.spec.room.model_dump(),
            "prompt_sections": [s.title for s in self.prompt.sections],
            "design_score": self.design.score,
            "cabinets": len(self.design.cabinets),
            "appliances": len(self.design.appliances),
            "countertops": len(self.design.countertops),
            "warnings": list(self.design.warnings),
        }


class AIPipeline:
    def __init__(
        self,
        provider: AIProvider | None = None,
        builder: PromptBuilder | None = None,
    ):
        self.provider = provider or get_provider()
        self.builder = builder or PromptBuilder()

    async def run(
        self,
        spec: KitchenSpecification,
        camera_views: list[CameraView] | None = None,
    ) -> PipelineResult:
        views = camera_views or default_views()
        prompt = self.builder.build(spec, views)
        design = await self.provider.generate_design(spec, views)
        result = PipelineResult(
            spec=spec,
            prompt=prompt,
            design=design,
            provider=self.provider.name,
            model=self.provider.model,
        )
        logger.info(
            "pipeline ok provider=%s model=%s layout=%s score=%s cabinets=%s appliances=%s",
            result.provider,
            result.model,
            spec.layout.value,
            design.score,
            len(design.cabinets),
            len(design.appliances),
        )
        return result

    @staticmethod
    def map_error(exc: AIProviderError) -> tuple[int, str]:
        """Map a provider error to a stable (status_code, detail) pair."""
        from app.ai.errors import (
            InvalidDesignResponse,
            ProviderAPIError,
            ProviderNotConfigured,
            ProviderTimeout,
        )

        if isinstance(exc, ProviderNotConfigured):
            return (503, str(exc))
        if isinstance(exc, ProviderTimeout):
            return (504, str(exc))
        if isinstance(exc, ProviderAPIError):
            return (502, str(exc))
        if isinstance(exc, InvalidDesignResponse):
            return (502, str(exc))
        return (500, str(exc))


# Re-export for callers that import directly from pipeline.
__all__ = ["PipelineResult", "AIPipeline", "AIProviderError"]
