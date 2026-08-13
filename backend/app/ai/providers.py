"""AI provider abstraction — the real AI design pipeline.

Each provider converts a KitchenSpecification into a validated
DesignSpecification. The base class owns the shared flow:

    KitchenSpecification
        → PromptBuilder                  (deterministic, fixed sections)
        → AIProvider._request_content    (structured JSON from the model)
        → parse + DesignSpecification validation
        → on failure: retry ONCE with a structured correction instruction
        → on second failure: controlled InvalidDesignResponse

Providers never see free-form user prompts; the prompt is built ONLY from the
KitchenSpecification and fixed system instructions.

    AIProvider
    ├── GPTProvider     (official OpenAI SDK)
    ├── GeminiProvider  (official Google GenAI SDK)
    └── MockAIProvider  (deterministic rule engine, no credentials)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from pydantic import ValidationError

from app.ai.cameras import CameraView, default_views, render_camera_instruction
from app.ai.design_spec import DesignElement, DesignSpecification, MaterialRef, RenderInstruction
from app.ai.errors import (
    AIProviderError,
    InvalidDesignResponse,
    ProviderAPIError,
    ProviderNotConfigured,
    ProviderTimeout,
)
from app.ai.prompt_builder import PromptBuilder, PromptDocument
from app.ai.spec import KitchenSpecification
from app.core.config import settings
from app.design.engine import KitchenDesignEngine
from app.design.parametric import RoomParam

logger = logging.getLogger(__name__)

# Fixed system instruction: the model always returns the structured JSON
# contract, never free-form prose. Model-specific system prompts extend this.
SYSTEM_INSTRUCTION = (
    "You are Firx, an expert kitchen design system. "
    "You convert a structured kitchen specification into a kitchen design. "
    "Respond ONLY with a single valid JSON object that matches the "
    "DesignSpecification schema. Do NOT add markdown, prose, explanation or "
    "any text outside the JSON object. The JSON object must contain the keys: "
    "version, source_spec_version, layout, style, room, cabinets, appliances, "
    "countertops, object_positions, materials, colors, render_instructions, "
    "rationale, warnings, score. "
    "Use millimetres for every dimension. layout and style must match the "
    "input values exactly. score is an integer from 0 to 100."
)


def _fmt(value: float) -> str:
    """Render a float dimension without a trailing .0 when it is integral."""
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def _parse_json(content: str) -> dict:
    """Parse a model response into a dict, tolerating markdown fences."""
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    if text.startswith("```"):
        text = text.strip("`")
    text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidDesignResponse(f"model returned non-JSON content: {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidDesignResponse("model returned a JSON value that is not an object")
    return data


# Map spec appliance types to engine appliance keys.
_APP_MAP = {
    "refrigerator": "fridge",
    "dishwasher": "dishwasher",
    "washing_machine": "washing_machine",
    "oven": "oven",
    "cooktop": "cooktop",
    "hood": "hood",
}

_CABINET_FA = {
    "base": "کابینت پایه",
    "wall": "کابینت دیواری",
    "tall": "کابینت بلند",
    "corner": "کابینت گوشه",
    "drawer": "کشو",
}

_APP_FA = {
    "refrigerator": "یخچال",
    "dishwasher": "ظرفشویی",
    "washing_machine": "ماشین لباسشویی",
    "oven": "فر",
    "cooktop": "اجاق گاز",
    "hood": "هود",
    "sink": "سینک",
}


class AIProvider(ABC):
    """Interface every provider implements.

    Public API
    ----------
    ``name``        stable provider id (``mock``, ``gpt``, ``gemini``)
    ``model``       concrete model identifier
    ``timeout``     per-call timeout in seconds
    ``generate_design(spec, camera_views=None)``
                    KitchenSpecification → validated DesignSpecification

    Subclasses implement ``_request_content``: send the prompt to the model and
    return the raw text. Parsing, validation and single retry are shared.
    """

    name: str = "ai"
    default_model: str = ""

    def __init__(self, model: str | None = None, timeout: float | None = None):
        self.model = model or self.default_model
        self.timeout = timeout or settings.ai_timeout or 60.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def generate_design(
        self,
        spec: KitchenSpecification,
        camera_views: list[CameraView] | None = None,
    ) -> DesignSpecification:
        prompt = PromptBuilder().build(spec, camera_views)
        raw = await self._call_with_timeout(prompt, spec, correction=None)
        return await self._validate_with_retry(prompt, spec, raw)

    async def generate(
        self,
        spec: KitchenSpecification,
        camera_views: list[CameraView] | None = None,
    ) -> DesignSpecification:
        """Backwards-compatible alias of ``generate_design``."""
        return await self.generate_design(spec, camera_views)

    async def generate_from_prompt(
        self,
        prompt: PromptDocument,
        spec: KitchenSpecification,
    ) -> DesignSpecification:
        return await self.generate_design(spec, prompt.camera_views)

    # ------------------------------------------------------------------
    # Shared validation + retry
    # ------------------------------------------------------------------
    async def _call_with_timeout(
        self,
        prompt: PromptDocument,
        spec: KitchenSpecification,
        correction: str | None,
    ) -> str:
        try:
            return await asyncio.wait_for(
                self._request_content(prompt, spec, correction),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError as exc:
            raise ProviderTimeout(
                f"{self.name} ({self.model}) timed out after {self.timeout}s"
            ) from exc

    async def _validate_with_retry(
        self,
        prompt: PromptDocument,
        spec: KitchenSpecification,
        raw: str,
    ) -> DesignSpecification:
        try:
            data = _parse_json(raw)
            return DesignSpecification.model_validate(data)
        except (InvalidDesignResponse, ValidationError) as first_error:
            correction = self._correction_message(first_error)
            logger.info(
                "provider=%s model=%s: first response invalid (%s), retrying with correction",
                self.name,
                self.model,
                type(first_error).__name__,
            )
            raw2 = await self._call_with_timeout(prompt, spec, correction=correction)
            try:
                data2 = _parse_json(raw2)
                return DesignSpecification.model_validate(data2)
            except (InvalidDesignResponse, ValidationError) as second_error:
                raise InvalidDesignResponse(
                    f"{self.name} returned an invalid DesignSpecification after retry: "
                    f"{self._correction_message(second_error)}"
                ) from second_error

    @staticmethod
    def _correction_message(error: Exception) -> str:
        if isinstance(error, ValidationError):
            issues = [
                f"path={'.'.join(str(x) for x in err.get('loc', []))} msg={err.get('msg')}"
                for err in error.errors()
            ]
            detail = " ; ".join(issues[:10])
        else:
            detail = str(error)
        return (
            "Your previous response failed validation. Return ONLY corrected, "
            f"complete DesignSpecification JSON. Issues: {detail}"
        )

    # ------------------------------------------------------------------
    # Subclass contract
    # ------------------------------------------------------------------
    @abstractmethod
    async def _request_content(
        self,
        prompt: PromptDocument,
        spec: KitchenSpecification,
        correction: str | None,
    ) -> str:
        """Send the prompt to the model and return the raw response text.

        ``correction`` is a structured instruction appended when retrying an
        invalid first response.
        """


class GPTProvider(AIProvider):
    """Official OpenAI provider using structured JSON output."""

    name = "gpt"
    default_model = "gpt-4o-mini"

    def __init__(self, model: str | None = None, timeout: float | None = None):
        super().__init__(model or settings.openai_model, timeout)

    async def _request_content(
        self,
        prompt: PromptDocument,
        spec: KitchenSpecification,
        correction: str | None,
    ) -> str:
        import openai

        if not settings.openai_api_key:
            raise ProviderNotConfigured(
                "OpenAI provider is not configured. Set APP_OPENAI_API_KEY or use the mock provider."
            )
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key, timeout=self.timeout)
        user_content = prompt.text()
        if correction:
            user_content = f"{user_content}\n\nCORRECTION:\n{correction}"
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": user_content},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
        except openai.APIError as exc:
            raise ProviderAPIError(f"OpenAI API error: {exc}") from exc
        finally:
            await client.close()
        return response.choices[0].message.content or ""


class GeminiProvider(AIProvider):
    """Official Google Gemini provider using structured JSON output."""

    name = "gemini"
    default_model = "gemini-2.0-flash"

    def __init__(self, model: str | None = None, timeout: float | None = None):
        super().__init__(model or settings.gemini_model, timeout)

    async def _request_content(
        self,
        prompt: PromptDocument,
        spec: KitchenSpecification,
        correction: str | None,
    ) -> str:
        from google import genai

        if not settings.gemini_api_key:
            raise ProviderNotConfigured(
                "Gemini provider is not configured. Set APP_GEMINI_API_KEY or use the mock provider."
            )
        client = genai.Client(api_key=settings.gemini_api_key)
        user_content = prompt.text()
        if correction:
            user_content = f"{user_content}\n\nCORRECTION:\n{correction}"
        try:
            response = await client.aio.models.generate_content(
                model=self.model,
                contents=user_content,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:  # noqa: BLE001 — SDK raises a wide net
            raise ProviderAPIError(f"Gemini API error: {exc}") from exc
        return response.text or ""


class MockAIProvider(AIProvider):
    """Deterministic provider: runs the rule-based kitchen engine and returns
    its output as structured JSON so the exact same validation path as the
    real providers is exercised. No credentials required."""

    name = "mock"
    default_model = "firx-rule-engine-v1"

    async def _request_content(
        self,
        prompt: PromptDocument,
        spec: KitchenSpecification,
        correction: str | None,
    ) -> str:
        views = prompt.camera_views or default_views()
        design = _build_mock_design(spec, views)
        return design.model_dump_json()


def _build_mock_design(
    spec: KitchenSpecification,
    views: list[CameraView],
) -> DesignSpecification:
    """Normalize the rule engine output into a DesignSpecification."""
    room_param = _spec_to_room(spec)
    cabinets = _spec_to_cabinet_catalog(spec)
    appliances = _spec_to_appliance_catalog(spec)

    engine = KitchenDesignEngine(
        room=room_param,
        layout=spec.layout.engine_layout,
        cabinets=cabinets,
        appliances=appliances,
    )
    model = engine.generate()

    elements = {
        "cabinet": [_to_element(c, f"cab-{i}") for i, c in enumerate(model.cabinets)],
        "appliance": [_to_element(a, f"app-{i}") for i, a in enumerate(model.appliances)],
        "countertop": [_to_element(c, f"ct-{i}") for i, c in enumerate(model.countertops)],
    }

    object_positions = [obj.model_dump() for obj in spec.objects]

    materials = [
        MaterialRef(code="", name="کانترتاپ", category="countertop"),
        MaterialRef(code="", name=spec.countertop.material, category="countertop"),
    ]

    instructions = [
        RenderInstruction(
            view=v.value,
            name=v.value,
            instruction=render_camera_instruction(v, spec),
        )
        for v in views
    ]

    rationale = (
        f"چیدمان {spec.layout.fa} بر اساس ابعاد اتاق "
        f"({_fmt(spec.room.width)}×{_fmt(spec.room.length)} میلی‌متر) و سبک {spec.style.fa} "
        f"با {len(model.cabinets)} کابینت و {len(model.appliances)} وسیله تولید شد."
    )

    return DesignSpecification(
        version="1.0",
        source_spec_version=spec.version,
        layout=spec.layout,
        style=spec.style,
        room=spec.room.model_dump(),
        cabinets=elements["cabinet"],
        appliances=elements["appliance"],
        countertops=elements["countertop"],
        object_positions=object_positions,
        materials=materials,
        colors={
            "cabinet_color": spec.colors.cabinet_color,
            "cabinet_finish": spec.colors.cabinet_finish,
            "handle_style": spec.colors.handle_style,
            "countertop_color": spec.countertop.color,
        },
        render_instructions=instructions,
        rationale=rationale,
        warnings=list(model.warnings),
        score=model.score,
    )


def get_provider(name: str | None = None) -> AIProvider:
    """Resolve a provider by name, falling back to environment configuration.

    Selection order:
        1. explicit ``name`` argument (from the request)
        2. ``AI_PROVIDER`` / ``APP_AI_PROVIDER`` environment variable
        3. ``APP_AI_DEFAULT_PROVIDER`` (back-compat)
        4. ``mock`` — the default when nothing is configured
    """
    import os

    chosen = (
        (name or "")
        or os.environ.get("AI_PROVIDER", "")
        or os.environ.get("APP_AI_PROVIDER", "")
        or settings.ai_default_provider
        or "mock"
    ).lower()
    try:
        return {
            "gpt": GPTProvider(),
            "openai": GPTProvider(),
            "gemini": GeminiProvider(),
            "mock": MockAIProvider(),
        }[chosen]
    except KeyError:
        raise ValueError(f"unknown AI provider: {name}")


# ---------------------------------------------------------------------------
# spec -> engine input converters (deterministic)
# ---------------------------------------------------------------------------
def _spec_to_room(spec: KitchenSpecification) -> RoomParam:
    return RoomParam(
        id=str(uuid.uuid4()),
        name=spec.project_name,
        width_mm=int(spec.room.width),
        length_mm=int(spec.room.length),
        height_mm=int(spec.room.height),
        walls=[
            {"side": w.side, "length_mm": int(w.length), "thickness_mm": int(w.thickness)}
            for w in spec.walls
        ],
        openings=[
            {
                "id": d.id or str(uuid.uuid4()),
                "kind": "door",
                "wall": d.wall,
                "position_mm": int(d.offset),
                "width_mm": int(d.width),
                "height_mm": int(d.height),
                "sill_height_mm": 0,
                "swing": d.swing,
            }
            for d in spec.doors
        ]
        + [
            {
                "id": w.id or str(uuid.uuid4()),
                "kind": "window",
                "wall": w.wall,
                "position_mm": int(w.offset),
                "width_mm": int(w.width),
                "height_mm": int(w.height),
                "sill_height_mm": int(w.sill_height),
                "swing": None,
            }
            for w in spec.windows
        ],
        obstacles=[],
    )


def _spec_to_cabinet_catalog(spec: KitchenSpecification) -> list[dict]:
    """Build engine catalog rows from the spec's cabinet configuration.

    When the spec does not list cabinets, fall back to the standard width set
    so the engine always has something to place.
    """
    if spec.cabinets:
        return [
            {
                "id": str(uuid.uuid4()),
                "code": f"{c.type}-{int(c.width)}",
                "name": _CABINET_FA.get(c.type, c.type),
                "cabinet_type": c.type,
                "width_mm": int(c.width),
                "height_mm": int(c.height),
                "depth_mm": int(c.depth),
                "base_price": 0.0,
                "is_active": True,
            }
            for c in spec.cabinets
        ]
    defaults = [
        {"cabinet_type": "base", "width_mm": 300},
        {"cabinet_type": "base", "width_mm": 400},
        {"cabinet_type": "base", "width_mm": 600},
        {"cabinet_type": "base", "width_mm": 800},
        {"cabinet_type": "corner", "width_mm": 300},
        {"cabinet_type": "sink", "width_mm": 900},
        {"cabinet_type": "drawer", "width_mm": 600},
        {"cabinet_type": "wall", "width_mm": 600},
        {"cabinet_type": "tall", "width_mm": 700},
    ]
    return [
        {
            "id": str(uuid.uuid4()),
            "code": f"{c['cabinet_type']}-{c['width_mm']}",
            "name": _CABINET_FA.get(c["cabinet_type"], c["cabinet_type"]),
            "cabinet_type": c["cabinet_type"],
            "width_mm": c["width_mm"],
            "height_mm": 720 if c["cabinet_type"] != "wall" else 900,
            "depth_mm": 600 if c["cabinet_type"] != "wall" else 350,
            "base_price": 0.0,
            "is_active": True,
        }
        for c in defaults
    ]


def _spec_to_appliance_catalog(spec: KitchenSpecification) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for a in spec.appliances:
        rows[_APP_MAP.get(a.type, a.type)] = {
            "id": str(uuid.uuid4()),
            "code": a.type,
            "name": _APP_FA.get(a.type, a.type),
            "width_mm": int(a.width or _default_app_width(a.type)),
            "height_mm": int(a.height or _default_app_height(a.type)),
            "depth_mm": int(a.depth or _default_app_depth(a.type)),
            "price": 0.0,
        }
    if spec.sink is not None:
        rows["sink"] = {
            "id": str(uuid.uuid4()),
            "code": "sink",
            "name": "سینک",
            "width_mm": int(spec.sink.width),
            "height_mm": 200,
            "depth_mm": int(spec.sink.depth),
            "price": 0.0,
        }
    return rows


def _default_app_width(kind: str) -> int:
    return {
        "refrigerator": 700,
        "dishwasher": 600,
        "washing_machine": 600,
        "oven": 600,
        "cooktop": 600,
        "hood": 900,
    }.get(kind, 600)


def _default_app_height(kind: str) -> int:
    return {
        "refrigerator": 1780,
        "dishwasher": 820,
        "washing_machine": 850,
        "oven": 600,
        "cooktop": 60,
        "hood": 150,
    }.get(kind, 600)


def _default_app_depth(kind: str) -> int:
    return {
        "refrigerator": 700,
        "dishwasher": 600,
        "washing_machine": 600,
        "oven": 550,
        "cooktop": 520,
        "hood": 600,
    }.get(kind, 600)


def _to_element(obj: object, element_id: str = "") -> DesignElement:
    """Normalize an engine Cabinet/AppliancePos/Countertop into DesignElement."""
    o = obj
    return DesignElement(
        id=element_id or getattr(o, "id", ""),
        type=getattr(o, "appliance_type", None) or getattr(o, "type", ""),
        name=getattr(o, "name", ""),
        x=float(getattr(o, "x", 0)),
        y=float(getattr(o, "y", 0)),
        z=float(getattr(o, "z", 0)),
        rotation=int(getattr(o, "rotation", 0)),
        width_mm=float(getattr(o, "width_mm", 0)),
        height_mm=float(getattr(o, "height_mm", 0)),
        depth_mm=float(getattr(o, "depth_mm", 0)),
    )
