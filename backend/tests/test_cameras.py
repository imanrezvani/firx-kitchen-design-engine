"""Camera/view template tests."""

from __future__ import annotations

import pytest

from app.ai.cameras import CAMERA_TEMPLATES, CameraView, default_views, render_camera_instruction

ALL_VIEWS = [
    CameraView.MAIN_PERSPECTIVE,
    CameraView.LEFT_PERSPECTIVE,
    CameraView.RIGHT_PERSPECTIVE,
    CameraView.ENTRANCE_VIEW,
    CameraView.WIDE_ROOM_VIEW,
]


def test_all_fixed_views_defined():
    assert set(CAMERA_TEMPLATES.keys()) == {v.value for v in ALL_VIEWS}


def test_each_template_has_required_keys():
    required = {"name", "angle", "height", "fov", "subject"}
    for tpl in CAMERA_TEMPLATES.values():
        assert required.issubset(tpl.keys())


def test_render_injects_geometry(example_spec):
    text = render_camera_instruction(CameraView.MAIN_PERSPECTIVE, example_spec)
    assert "MAIN_PERSPECTIVE" in text
    assert "4200x3600x2700" in text
    assert "L_SHAPE" in text


def test_render_is_deterministic(example_spec):
    a = render_camera_instruction(CameraView.ENTRANCE_VIEW, example_spec)
    b = render_camera_instruction(CameraView.ENTRANCE_VIEW, example_spec)
    assert a == b


def test_unknown_view_rejected(example_spec):
    # unknown view values are never renderable
    assert "NOPE" not in CAMERA_TEMPLATES
    with pytest.raises(ValueError):
        render_camera_instruction(_fake_view("NOPE"), example_spec)


class _fake_view:
    def __init__(self, value: str):
        self.value = value


def test_default_views_include_main():
    assert CameraView.MAIN_PERSPECTIVE in default_views()
