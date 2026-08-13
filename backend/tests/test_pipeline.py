"""End-to-end pipeline tests: Form → Spec → Prompt → Mock AI → DesignSpecification."""

from __future__ import annotations

import pytest

from app.ai.cameras import CameraView
from app.ai.pipeline import AIPipeline, PipelineResult
from app.ai.prompt_builder import PromptDocument
from app.ai.providers import MockAIProvider
from app.ai.spec import KitchenSpecification


@pytest.mark.asyncio
async def test_full_pipeline_returns_all_stages(example_spec):
    pipeline = AIPipeline(provider=MockAIProvider())
    result = await pipeline.run(example_spec)
    assert isinstance(result, PipelineResult)
    assert isinstance(result.spec, KitchenSpecification)
    assert isinstance(result.prompt, PromptDocument)
    # the design spec carries the same layout + room geometry
    assert result.design.layout == example_spec.layout
    assert result.design.room["width"] == example_spec.room.width
    assert result.design.room["length"] == example_spec.room.length
    assert result.design.render_instructions


@pytest.mark.asyncio
async def test_pipeline_deterministic(example_spec):
    pipeline = AIPipeline(provider=MockAIProvider())
    a = await pipeline.run(example_spec)
    b = await pipeline.run(example_spec)
    assert a.prompt.text() == b.prompt.text()
    assert a.design == b.design


@pytest.mark.asyncio
async def test_pipeline_works_for_every_layout():
    from app.ai.spec import LayoutKind

    pipeline = AIPipeline(provider=MockAIProvider())
    base = example_spec_model()
    for layout in LayoutKind:
        spec = base.model_copy(deep=True)
        spec.layout = layout
        result = await pipeline.run(spec)
        assert result.design.layout == layout
        assert result.design.cabinets, f"no cabinets for {layout}"


@pytest.mark.asyncio
async def test_pipeline_honors_custom_views(example_spec):
    pipeline = AIPipeline(provider=MockAIProvider())
    views = [CameraView.ENTRANCE_VIEW, CameraView.WIDE_ROOM_VIEW]
    result = await pipeline.run(example_spec, views)
    assert [v.value for v in result.prompt.camera_views] == [v.value for v in views]
    assert [r.view for r in result.design.render_instructions] == [v.value for v in views]


def test_prompt_is_deterministic_and_structured(example_spec):
    # prompt must have the fixed section titles and be independent of free text
    from app.ai.prompt_builder import PromptBuilder

    doc = PromptBuilder().build(example_spec)
    titles = [s.title for s in doc.sections]
    for required in ("ROOM GEOMETRY", "HARD CONSTRAINTS", "NEGATIVE CONSTRAINTS"):
        assert required in titles


def example_spec_model():
    """A minimal valid spec for layout-parameterized pipeline runs."""
    return KitchenSpecification.model_validate(
        {
            "room": {"width": 4200, "length": 3600, "height": 2700},
            "layout": "L_SHAPE",
        }
    )
