"""PromptBuilder determinism + fixed-section tests."""

from __future__ import annotations

from app.ai.prompt_builder import PromptBuilder, PromptSection
from app.ai.cameras import CameraView

EXPECTED_SECTIONS = {
    "ROOM GEOMETRY",
    "ARCHITECTURAL ELEMENTS",
    "KITCHEN LAYOUT",
    "APPLIANCE CONFIGURATION",
    "OBJECT POSITIONS",
    "CABINET CONFIGURATION",
    "MATERIALS",
    "COLORS",
    "DESIGN STYLE",
    "USER REQUIREMENTS",
    "ENVIRONMENT PHOTOS",
    "CAMERA / VIEW REQUIREMENTS",
    "HARD CONSTRAINTS",
    "NEGATIVE CONSTRAINTS",
}


def test_all_fixed_sections_present(example_spec):
    builder = PromptBuilder()
    doc = builder.build(example_spec)
    titles = {s.title for s in doc.sections}
    assert titles == EXPECTED_SECTIONS


def test_prompt_is_deterministic(example_spec):
    builder = PromptBuilder()
    a = builder.build(example_spec).text()
    b = builder.build(example_spec).text()
    assert a == b


def test_prompt_same_for_same_spec_different_instance(example_spec):
    builder = PromptBuilder()
    doc1 = builder.build(example_spec)
    doc2 = builder.build(example_spec.model_copy(deep=True))
    assert doc1.text() == doc2.text()


def test_prompt_changes_with_layout(example_spec):
    builder = PromptBuilder()
    spec1 = builder.build(example_spec.model_copy(deep=True))
    modified = example_spec.model_copy(deep=True)
    from app.ai.spec import LayoutKind

    modified.layout = LayoutKind.ISLAND
    spec2 = builder.build(modified)
    assert spec1.text() != spec2.text()


def test_camera_views_default(example_spec):
    builder = PromptBuilder()
    doc = builder.build(example_spec)
    assert CameraView.MAIN_PERSPECTIVE in doc.camera_views
    assert CameraView.WIDE_ROOM_VIEW in doc.camera_views


def test_custom_camera_views_respected(example_spec):
    builder = PromptBuilder()
    views = [CameraView.ENTRANCE_VIEW]
    doc = builder.build(example_spec, views)
    assert doc.camera_views == views


def test_camera_geometry_injected(example_spec):
    builder = PromptBuilder()
    doc = builder.build(example_spec, [CameraView.MAIN_PERSPECTIVE])
    cam = next(s for s in doc.sections if s.title == "CAMERA / VIEW REQUIREMENTS")
    assert "4200x3600x2700" in cam.body
    assert "MAIN_PERSPECTIVE" in cam.body


def test_freeform_notes_are_auxiliary_not_primary(example_spec):
    builder = PromptBuilder()
    doc = builder.build(example_spec)
    req = next(s for s in doc.sections if s.title == "USER REQUIREMENTS")
    # structured sections must exist independent of any free-form note
    assert "family" not in req.body.lower() or "خانواده" in req.body
    assert example_spec.user_requirements.notes in req.body


def test_sections_have_nonempty_bodies(example_spec):
    builder = PromptBuilder()
    for s in builder.build(example_spec).sections:
        assert isinstance(s, PromptSection)
        assert s.title
        assert s.body.strip()
