"""Deterministic PromptBuilder.

Converts a KitchenSpecification into a fixed-structure AI prompt. The prompt
has a stable set of sections, each rendered deterministically from the
structured spec. It never relies on free-form user descriptions as the primary
input; free-form notes are included only as an auxiliary "user requirements"
section.

The output is deterministic: identical specs always produce identical prompts
for the same camera view.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.ai.cameras import CameraView, default_views, render_camera_instruction
from app.ai.spec import KitchenSpecification


def _fmt(value: float) -> str:
    """Render a float dimension without a trailing .0 when it is integral."""
    if float(value).is_integer():
        return str(int(value))
    return str(value)

# Hard constraints injected verbatim into every prompt.
HARD_CONSTRAINTS = [
    "گام تمامی کابینت‌ها و لوازم باید با ابعاد ورودی مطابقت داشته باشد.",
    "هیچ کابینتی نباید با پنجره، در یا مانع تداخل کند.",
    "فاصله عبور بین ردیف‌های کابینت حداقل 90 سانتی‌متر باشد.",
    "مثلث کار (سینک، اجاق، یخچال) باید در دسترس و بدون مانع باشد.",
    "ارتفاع سطوح کار بر اساس ضخامت کانترتاپ و پایه‌ها محاسبه شود.",
    "تعداد و نوع لوازم باید دقیقاً برابر انتخاب‌های کاربر باشد.",
    "نوع چیدمان (layout) باید دقیقاً مطابق انتخاب کاربر باشد.",
]

NEGATIVE_CONSTRAINTS = [
    "هیچ لوازمی که در ورودی مشخص نشده اضافه نکن.",
    "هیچ کابینت اضافه‌ای خارج از ابعاد اتاق رسم نکن.",
    "از عناصر تزئینی غیرواقعی و غیرقابل ساخت خودداری کن.",
    "پنجره‌ها و درها را جابه‌جا یا حذف نکن.",
    "ابعاد را تغییر نده؛ فقط بر اساس ورودی طراحی کن.",
    "از متریال‌ها و رنگ‌هایی که توسط کاربر انتخاب نشده استفاده نکن.",
]


class PromptSection(BaseModel):
    title: str
    body: str


class PromptDocument(BaseModel):
    spec_version: str = "1.0"
    layout: str
    camera_views: list[CameraView] = Field(default_factory=default_views)
    sections: list[PromptSection] = Field(default_factory=list)

    def text(self) -> str:
        blocks = [f"## {s.title}\n{s.body}" for s in self.sections]
        return "\n\n".join(blocks)


class PromptBuilder:
    """Builds the deterministic AI prompt from a KitchenSpecification."""

    def build(
        self,
        spec: KitchenSpecification,
        camera_views: list[CameraView] | None = None,
    ) -> PromptDocument:
        views = camera_views or default_views()
        sections = [
            self._room_geometry(spec),
            self._architectural_elements(spec),
            self._kitchen_layout(spec),
            self._appliance_config(spec),
            self._object_positions(spec),
            self._cabinet_config(spec),
            self._materials(spec),
            self._colors(spec),
            self._design_style(spec),
            self._user_requirements(spec),
            self._environment_photos(spec),
            self._camera_requirements(views, spec),
            self._hard_constraints(),
            self._negative_constraints(),
        ]
        return PromptDocument(
            spec_version=spec.version,
            layout=spec.layout.value,
            camera_views=views,
            sections=sections,
        )

    # ------------------------------------------------------------------
    # section renderers — deterministic, one line per fact
    # ------------------------------------------------------------------
    @staticmethod
    def _room_geometry(spec: KitchenSpecification) -> PromptSection:
        lines = [
            f"اتاق: عرض {_fmt(spec.room.width)} {spec.room.unit}، طول {_fmt(spec.room.length)} {spec.room.unit}، "
            f"ارتفاع {_fmt(spec.room.height)} {spec.room.unit}",
        ]
        return PromptSection(title="ROOM GEOMETRY", body="\n".join(lines))

    @staticmethod
    def _architectural_elements(spec: KitchenSpecification) -> PromptSection:
        lines = ["درها:"]
        if spec.doors:
            for d in spec.doors:
                lines.append(
                    f"- در {d.id or '?'}: دیوار {d.wall}، آفست {_fmt(d.offset)}، عرض {_fmt(d.width)}، "
                    f"ارتفاع {_fmt(d.height)}، لولا {d.swing}"
                )
        else:
            lines.append("- در: ندارد")
        lines.append("پنجره‌ها:")
        if spec.windows:
            for w in spec.windows:
                lines.append(
                    f"- پنجره {w.id or '?'}: دیوار {w.wall}، آفست {_fmt(w.offset)}، عرض {_fmt(w.width)}، "
                    f"ارتفاع {_fmt(w.height)}، کف پنجره {_fmt(w.sill_height)}"
                )
        else:
            lines.append("- پنجره: ندارد")
        lines.append("دیوارها:")
        if spec.walls:
            for wall in spec.walls:
                lines.append(
                    f"- دیوار {wall.side}: طول {_fmt(wall.length)}، ضخامت {_fmt(wall.thickness)}"
                )
        return PromptSection(title="ARCHITECTURAL ELEMENTS", body="\n".join(lines))

    @staticmethod
    def _kitchen_layout(spec: KitchenSpecification) -> PromptSection:
        return PromptSection(
            title="KITCHEN LAYOUT",
            body=f"چیدمان: {spec.layout.value} ({spec.layout.fa})",
        )

    @staticmethod
    def _appliance_config(spec: KitchenSpecification) -> PromptSection:
        lines = []
        if not spec.appliances:
            lines.append("- هیچ لوازمی انتخاب نشده است.")
        for a in spec.appliances:
            dims = (
                f"ابعاد {a.width or '?'}x{a.height or '?'}x{a.depth or '?'}"
                if any([a.width, a.height, a.depth])
                else "ابعاد پیش‌فرض"
            )
            variant = getattr(a, "variant", None)
            lines.append(f"- {a.type} ({variant or 'پیش‌فرض'}) — {dims}")
        return PromptSection(title="APPLIANCE CONFIGURATION", body="\n".join(lines))

    @staticmethod
    def _object_positions(spec: KitchenSpecification) -> PromptSection:
        lines = []
        if not spec.objects:
            lines.append("- هیچ موقعیت دستی ثبت نشده؛ موقعیت‌ها طبق قواعد چیدمان تعیین شود.")
        for o in spec.objects:
            wall = o.wall or "مرکز فضا"
            lines.append(
                f"- {o.type}: دیوار {wall}، آفست {_fmt(o.offset)}، عرض {_fmt(o.width)}، "
                f"عمق {_fmt(o.depth)}{f'، ارتفاع {_fmt(o.height)}' if o.height else ''}"
            )
        return PromptSection(title="OBJECT POSITIONS", body="\n".join(lines))

    @staticmethod
    def _cabinet_config(spec: KitchenSpecification) -> PromptSection:
        lines = []
        if not spec.cabinets:
            lines.append("- پیکربندی کابینت طبق قواعد چیدمان و ابعاد اتاق تولید شود.")
        for c in spec.cabinets:
            lines.append(
                f"- {c.type}: عرض {_fmt(c.width)}، ارتفاع {_fmt(c.height)}، عمق {_fmt(c.depth)}، تعداد {c.count}"
            )
        return PromptSection(title="CABINET CONFIGURATION", body="\n".join(lines))

    @staticmethod
    def _materials(spec: KitchenSpecification) -> PromptSection:
        return PromptSection(
            title="MATERIALS",
            body=(
                f"کابینت: {spec.colors.cabinet_finish}\n"
                f"کانترتاپ: {spec.countertop.material}، ضخامت {spec.countertop.thickness}"
            ),
        )

    @staticmethod
    def _colors(spec: KitchenSpecification) -> PromptSection:
        return PromptSection(
            title="COLORS",
            body=(
                f"رنگ کابینت: {spec.colors.cabinet_color}\n"
                f"رنگ کانترتاپ: {spec.countertop.color}\n"
                f"دستگیره: {spec.colors.handle_style}"
            ),
        )

    @staticmethod
    def _design_style(spec: KitchenSpecification) -> PromptSection:
        return PromptSection(
            title="DESIGN STYLE",
            body=f"سبک طراحی: {spec.style.value} ({spec.style.fa})",
        )

    @staticmethod
    def _user_requirements(spec: KitchenSpecification) -> PromptSection:
        lines = []
        req = spec.user_requirements
        if req.notes:
            lines.append(f"یادداشت کاربر: {req.notes}")
        if req.preferences:
            lines.append(f"ترجیحات: {'؛ '.join(req.preferences)}")
        if req.must_include:
            lines.append(f"الزامات: {'؛ '.join(req.must_include)}")
        if req.must_avoid:
            lines.append(f"موارد ممنوع: {'؛ '.join(req.must_avoid)}")
        if not lines:
            lines.append("- هیچ ترجیح آزادی ثبت نشده است.")
        return PromptSection(title="USER REQUIREMENTS", body="\n".join(lines))

    @staticmethod
    def _environment_photos(spec: KitchenSpecification) -> PromptSection:
        lines = []
        if not spec.photos:
            lines.append("- عکسی از محیط بارگذاری نشده است.")
        for p in spec.photos:
            lines.append(
                f"- عکس: {p.storage_key or p.url or p.id}{' — ' + p.caption if p.caption else ''}"
            )
        return PromptSection(title="ENVIRONMENT PHOTOS", body="\n".join(lines))

    @staticmethod
    def _camera_requirements(
        views: list[CameraView], spec: KitchenSpecification
    ) -> PromptSection:
        lines = [render_camera_instruction(v, spec) for v in views]
        return PromptSection(title="CAMERA / VIEW REQUIREMENTS", body="\n".join(lines))

    @staticmethod
    def _hard_constraints() -> PromptSection:
        return PromptSection(title="HARD CONSTRAINTS", body="\n".join(f"- {c}" for c in HARD_CONSTRAINTS))

    @staticmethod
    def _negative_constraints() -> PromptSection:
        return PromptSection(
            title="NEGATIVE CONSTRAINTS", body="\n".join(f"- {c}" for c in NEGATIVE_CONSTRAINTS)
        )
