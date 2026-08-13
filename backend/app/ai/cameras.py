"""Fixed camera/view templates for render generation.

Each template carries fixed, deterministic camera instructions so that outputs
across different users remain visually consistent. The pipeline injects
project-specific geometry (room dimensions, entrance position, window wall,
layout) into these templates — the template text itself never changes.

These templates only describe the *view* — they are not a rendering engine and
never become the source of truth.
"""

from __future__ import annotations

from enum import Enum

from app.ai.spec import KitchenSpecification, LayoutKind


def _fmt(value: float) -> str:
    """Render a float dimension without a trailing .0 when it is integral."""
    if float(value).is_integer():
        return str(int(value))
    return str(value)


class CameraView(str, Enum):
    MAIN_PERSPECTIVE = "MAIN_PERSPECTIVE"
    LEFT_PERSPECTIVE = "LEFT_PERSPECTIVE"
    RIGHT_PERSPECTIVE = "RIGHT_PERSPECTIVE"
    ENTRANCE_VIEW = "ENTRANCE_VIEW"
    WIDE_ROOM_VIEW = "WIDE_ROOM_VIEW"


CAMERA_TEMPLATES: dict[str, dict[str, str]] = {
    CameraView.MAIN_PERSPECTIVE.value: {
        "name": "نمای اصلی پرسپکتیو",
        "angle": "یک پرسپکتیو تک‌نقطه از گوشه مقابل ورودی آشپزخانه.",
        "height": "دوربین در ارتفاع 160 سانتی‌متر (قد انسان نشسته).",
        "fov": "لنز 35 میلی‌متری، زاویه دید 45 درجه.",
        "subject": "نمای کامل سطوح کار و کابینت‌های اصلی از نزدیک‌ترین گوشه.",
    },
    CameraView.LEFT_PERSPECTIVE.value: {
        "name": "پرسپکتیو چپ",
        "angle": "پرسپکتیو از سمت چپ فضای آشپزخانه، متمایل 30 درجه.",
        "height": "دوربین در ارتفاع 150 سانتی‌متر.",
        "fov": "لنز 28 میلی‌متری، زاویه دید 60 درجه.",
        "subject": "نمای سمت چپ چیدمان شامل دیوار چپ و کف.",
    },
    CameraView.RIGHT_PERSPECTIVE.value: {
        "name": "پرسپکتیو راست",
        "angle": "پرسپکتیو از سمت راست فضای آشپزخانه، متمایل 30 درجه.",
        "height": "دوربین در ارتفاع 150 سانتی‌متر.",
        "fov": "لنز 28 میلی‌متری، زاویه دید 60 درجه.",
        "subject": "نمای سمت راست چیدمان شامل دیوار راست و کف.",
    },
    CameraView.ENTRANCE_VIEW.value: {
        "name": "نمای ورودی",
        "angle": "نمای مستقیم از درگاه ورودی آشپزخانه به سمت داخل.",
        "height": "دوربین در ارتفاع 165 سانتی‌متر.",
        "fov": "لنز 24 میلی‌متری، زاویه دید 70 درجه.",
        "subject": "نمای کلی فضا از نقطه ورودی، تأکید بر مسیر دسترسی.",
    },
    CameraView.WIDE_ROOM_VIEW.value: {
        "name": "نمای وسیع فضا",
        "angle": "نمای باز و فراگیر از گوشه بالایی، زاویه 45 درجه رو به پایین.",
        "height": "دوربین در ارتفاع 220 سانتی‌متر.",
        "fov": "لنز 20 میلی‌متری، زاویه دید 85 درجه.",
        "subject": "تمام اجزای آشپزخانه (کابینت‌ها، جزیره، لوازم) در یک قاب.",
    },
}


def default_views() -> list[CameraView]:
    return [CameraView.MAIN_PERSPECTIVE, CameraView.WIDE_ROOM_VIEW]


def render_camera_instruction(view: CameraView, spec: KitchenSpecification) -> str:
    """Inject the fixed camera template with project geometry.

    Returns the complete camera instruction block for the given view.
    """
    tpl = CAMERA_TEMPLATES.get(view.value)
    if tpl is None:
        raise ValueError(f"unknown camera view: {view.value}")

    entrance_wall = spec.doors[0].wall if spec.doors else None
    window_wall = spec.windows[0].wall if spec.windows else None

    return (
        f"VIEW: {view.value} ({tpl['name']})\n"
        f"  angle: {tpl['angle']}\n"
        f"  height: {tpl['height']}\n"
        f"  fov: {tpl['fov']}\n"
        f"  subject: {tpl['subject']}\n"
        f"  geometry: room {_fmt(spec.room.width)}x{_fmt(spec.room.length)}x{_fmt(spec.room.height)} {spec.room.unit}, "
        f"layout {spec.layout.value}, entrance on {entrance_wall or 'unknown'}, "
        f"main window on {window_wall or 'none'}."
    )
