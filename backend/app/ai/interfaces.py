"""AI / CAD / Optimization interfaces — placeholders for future phases.

Per MVP phase-1 requirements, only *interfaces* are created here. Real AI
vision, image generation, Open CASCADE and OR-Tools integration are NOT
implemented. The product must prove the core loop without AI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PerceptionResult:
    room: dict | None = None
    confidence: float = 0.0
    message: str = ""


class RoomPerceptionService(ABC):
    """Future: extract room dimensions/openings from a photo."""

    @abstractmethod
    async def perceive(self, image_path: str) -> PerceptionResult:
        ...


class MockRoomPerceptionService(RoomPerceptionService):
    async def perceive(self, image_path: str) -> PerceptionResult:
        # Returns no perception: the MVP relies on manual room entry.
        return PerceptionResult(
            room=None,
            confidence=0.0,
            message="تشخیص خودکار فضا در این نسخه فعال نیست؛ لطفاً ابعاد را دستی وارد کنید.",
        )


class AIProvider(ABC):
    """Future: LLM-based Persian recommendations and design descriptions."""

    @abstractmethod
    async def explain(self, prompt: str, lang: str = "fa") -> str:
        ...


class MockAIProvider(AIProvider):
    async def explain(self, prompt: str, lang: str = "fa") -> str:
        return (
            "با توجه به ابعاد فضای شما، چیدمان L شکل برای این آشپزخانه مناسب است. "
            "این چیدمان دسترسی کوتاه به سینک، اجاق و یخچال را فراهم می‌کند."
        )


class ImageGenerationService(ABC):
    """Future: photorealistic render generation."""

    @abstractmethod
    async def generate(self, design_json: dict) -> bytes:
        ...


class MockImageGenerationService(ImageGenerationService):
    async def generate(self, design_json: dict) -> bytes:
        raise NotImplementedError("رندر تصویری در این نسخه فعال نیست.")


class CADGeometryService(ABC):
    """Future: Open CASCADE-based solid modelling (do NOT implement yet)."""


class OptimizationEngine(ABC):
    """Future: OR-Tools-based layout optimization (do NOT implement yet)."""
