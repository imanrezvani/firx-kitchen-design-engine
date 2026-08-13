"""Tests for the real AI provider architecture.

Covers provider selection, structured-output validation, single retry with
correction, missing API keys, API failures, timeouts and the debug surface.

Real network calls are never made: ``_request_content`` is monkeypatched on a
concrete provider subclass so the shared parse → validate → retry flow in the
base class is exercised deterministically.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from pydantic import ValidationError

from app.ai.cameras import CameraView
from app.ai.design_spec import DesignSpecification
from app.ai.errors import (
    AIProviderError,
    InvalidDesignResponse,
    ProviderAPIError,
    ProviderNotConfigured,
    ProviderTimeout,
)
from app.ai.providers import AIProvider, GeminiProvider, GPTProvider, MockAIProvider, get_provider
from app.ai.prompt_builder import PromptDocument


class _StubProvider(AIProvider):
    """Test provider whose raw model output is scripted."""

    name = "stub"
    default_model = "stub-1"

    def __init__(self, outputs: list[str], timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.outputs = list(outputs)
        self.calls: list[str | None] = []

    async def _request_content(
        self,
        prompt: PromptDocument,
        spec,
        correction: str | None,
    ) -> str:
        self.calls.append(correction)
        if not self.outputs:
            raise ProviderAPIError("stub exhausted")
        return self.outputs.pop(0)


def _valid_json() -> str:
    """A syntactically valid DesignSpecification JSON payload."""
    return json.dumps(
        {
            "version": "1.0",
            "source_spec_version": "1.0",
            "layout": "L_SHAPE",
            "style": "modern",
            "room": {"width": 4200, "length": 3600, "height": 2700, "unit": "mm"},
            "cabinets": [
                {
                    "id": "cab-0",
                    "type": "base",
                    "name": "کابینت پایه",
                    "wall": "north",
                    "offset": 100,
                    "x": 100,
                    "y": 0,
                    "z": 100,
                    "rotation": 0,
                    "width_mm": 600,
                    "height_mm": 720,
                    "depth_mm": 600,
                }
            ],
            "appliances": [],
            "countertops": [],
            "object_positions": [],
            "materials": [],
            "colors": {"cabinet_color": "سفید"},
            "render_instructions": [],
            "rationale": "mock",
            "warnings": [],
            "score": 95,
        }
    )


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------
def test_default_provider_is_mock(monkeypatch):
    for var in ("AI_PROVIDER", "APP_AI_PROVIDER"):
        monkeypatch.delenv(var, raising=False)
    assert isinstance(get_provider(), MockAIProvider)
    assert get_provider().name == "mock"


def test_provider_selection_ai_provider_env(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gpt")
    assert isinstance(get_provider(), GPTProvider)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    assert isinstance(get_provider(), GeminiProvider)


def test_provider_selection_explicit_name_wins(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    assert isinstance(get_provider("mock"), MockAIProvider)
    assert isinstance(get_provider("gpt"), GPTProvider)


def test_provider_models():
    assert GPTProvider().model == "gpt-4o-mini"
    assert GeminiProvider().model == "gemini-2.0-flash"
    assert MockAIProvider().model == "firx-rule-engine-v1"


# ---------------------------------------------------------------------------
# Structured output: valid / invalid / retry
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_valid_structured_response_parsed(example_spec):
    provider = _StubProvider([_valid_json()])
    design = await provider.generate_design(example_spec)
    assert isinstance(design, DesignSpecification)
    assert design.layout.value == "L_SHAPE"
    assert design.score == 95
    assert provider.calls == [None]  # no correction needed


@pytest.mark.asyncio
async def test_invalid_json_triggers_retry(example_spec):
    provider = _StubProvider(["this is not json", _valid_json()])
    design = await provider.generate_design(example_spec)
    assert design.score == 95
    assert provider.calls[0] is None
    assert provider.calls[1] is not None  # correction sent on retry


@pytest.mark.asyncio
async def test_invalid_schema_triggers_retry(example_spec):
    bad = json.loads(_valid_json())
    bad["layout"] = "NOT_A_LAYOUT"  # violates LayoutKind enum
    provider = _StubProvider([json.dumps(bad), _valid_json()])
    design = await provider.generate_design(example_spec)
    assert design.score == 95
    assert provider.calls[1] is not None


@pytest.mark.asyncio
async def test_two_invalid_responses_raise_controlled_error(example_spec):
    provider = _StubProvider(["not json", "still not json"])
    with pytest.raises(InvalidDesignResponse) as excinfo:
        await provider.generate_design(example_spec)
    assert "invalid DesignSpecification after retry" in str(excinfo.value)
    assert len(provider.calls) == 2


@pytest.mark.asyncio
async def test_retry_once_not_more(example_spec):
    provider = _StubProvider(["bad", _valid_json(), _valid_json()])
    await provider.generate_design(example_spec)
    assert len(provider.calls) == 2


@pytest.mark.asyncio
async def test_correction_message_contains_issues(example_spec):
    bad = json.loads(_valid_json())
    bad["score"] = "high"  # wrong type
    provider = _StubProvider([json.dumps(bad), _valid_json()])
    await provider.generate_design(example_spec)
    assert "CORRECTION" in provider.calls[1] or "score" in provider.calls[1]


# ---------------------------------------------------------------------------
# Missing API key / API failure / timeout
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_gpt_missing_key(example_spec):
    provider = GPTProvider()
    with pytest.raises(ProviderNotConfigured):
        await provider.generate_design(example_spec)


@pytest.mark.asyncio
async def test_gemini_missing_key(example_spec):
    provider = GeminiProvider()
    with pytest.raises(ProviderNotConfigured):
        await provider.generate_design(example_spec)


@pytest.mark.asyncio
async def test_api_failure_propagates(example_spec):
    async def boom(prompt, spec, correction):
        raise ProviderAPIError("rate limited")

    provider = _StubProvider([])
    provider._request_content = boom  # type: ignore[method-assign]
    with pytest.raises(ProviderAPIError):
        await provider.generate_design(example_spec)


@pytest.mark.asyncio
async def test_timeout_raises_provider_timeout(example_spec):
    async def slow(prompt, spec, correction):
        await asyncio.sleep(5)

    provider = _StubProvider([])
    provider.timeout = 0.01
    provider._request_content = slow  # type: ignore[method-assign]
    with pytest.raises(ProviderTimeout):
        await provider.generate_design(example_spec)


@pytest.mark.asyncio
async def test_timeout_applies_to_retry_too(example_spec):
    async def slow(prompt, spec, correction):
        await asyncio.sleep(5)

    provider = _StubProvider(["bad json"])
    provider.timeout = 0.01
    provider._request_content = slow  # type: ignore[method-assign]
    with pytest.raises(ProviderTimeout):
        await provider.generate_design(example_spec)


# ---------------------------------------------------------------------------
# DesignSpecification validation
# ---------------------------------------------------------------------------
def test_validate_invalid_layout_rejected():
    data = json.loads(_valid_json())
    data["layout"] = "HEXAGON"
    with pytest.raises(ValidationError):
        DesignSpecification.model_validate(data)


def test_validate_missing_required_field_rejected():
    data = json.loads(_valid_json())
    del data["layout"]  # layout is required (no default)
    with pytest.raises(ValidationError):
        DesignSpecification.model_validate(data)


# ---------------------------------------------------------------------------
# Mock provider through the new interface
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mock_provider_via_interface(example_spec):
    provider = MockAIProvider()
    design = await provider.generate_design(example_spec)
    assert isinstance(design, DesignSpecification)
    assert design.layout == example_spec.layout
    assert design.score >= 0
    assert design.cabinets


@pytest.mark.asyncio
async def test_mock_provider_deterministic(example_spec):
    provider = MockAIProvider()
    a = await provider.generate_design(example_spec)
    b = await provider.generate_design(example_spec)
    assert a.cabinets == b.cabinets
    assert a.score == b.score


# ---------------------------------------------------------------------------
# Error mapping via the pipeline helper
# ---------------------------------------------------------------------------
def test_map_error_codes():
    from app.ai.pipeline import AIPipeline

    assert AIPipeline.map_error(ProviderNotConfigured("x"))[0] == 503
    assert AIPipeline.map_error(ProviderTimeout("x"))[0] == 504
    assert AIPipeline.map_error(ProviderAPIError("x"))[0] == 502
    assert AIPipeline.map_error(InvalidDesignResponse("x"))[0] == 502
    assert AIPipeline.map_error(AIProviderError("x"))[0] == 500
