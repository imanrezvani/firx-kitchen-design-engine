"""AI provider abstraction tests."""

from __future__ import annotations

import pytest

from app.ai.design_spec import DesignSpecification
from app.ai.errors import AIProviderError
from app.ai.providers import GeminiProvider, GPTProvider, MockAIProvider, get_provider


def test_get_provider_default_is_mock():
    assert isinstance(get_provider(None), MockAIProvider)
    assert isinstance(get_provider("mock"), MockAIProvider)


def test_get_provider_supported_names():
    assert isinstance(get_provider("gpt"), GPTProvider)
    assert isinstance(get_provider("gemini"), GeminiProvider)


def test_get_provider_unknown_raises():
    with pytest.raises(ValueError):
        get_provider("nope")


@pytest.mark.asyncio
async def test_mock_provider_returns_design_spec(example_spec):
    provider = MockAIProvider()
    design = await provider.generate(example_spec)
    assert isinstance(design, DesignSpecification)
    assert design.layout == example_spec.layout
    assert design.style == example_spec.style
    assert design.cabinets
    assert design.score >= 0


@pytest.mark.asyncio
async def test_mock_provider_deterministic(example_spec):
    provider = MockAIProvider()
    a = await provider.generate(example_spec)
    b = await provider.generate(example_spec)
    assert a.cabinets == b.cabinets
    assert a.appliances == b.appliances
    assert a.score == b.score


@pytest.mark.asyncio
async def test_mock_provider_respects_camera_views(example_spec):
    from app.ai.cameras import CameraView

    provider = MockAIProvider()
    design = await provider.generate(example_spec, [CameraView.ENTRANCE_VIEW])
    assert [r.view for r in design.render_instructions] == [CameraView.ENTRANCE_VIEW.value]


@pytest.mark.asyncio
async def test_real_providers_require_credentials(example_spec):
    # Without configured keys both real providers must raise clear errors.
    from app.core.config import settings

    expected_key = {"gpt": "openai_api_key", "gemini": "gemini_api_key"}
    for provider in (GPTProvider(), GeminiProvider()):
        if getattr(settings, expected_key[provider.name]):
            pytest.skip(f"{provider.name} key configured in env")
        with pytest.raises(AIProviderError):
            await provider.generate_design(example_spec)
