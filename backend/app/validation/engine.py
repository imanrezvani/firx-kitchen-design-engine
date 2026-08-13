"""ConstraintEngine — deterministic validation of a parametric design.

Returns structured results in Persian:
    ok | warning | error
Checks: cabinet-wall collision, cabinet-appliance collision, door/window
conflict, walkway clearance, cabinet dimension limits.
"""

from __future__ import annotations

from app.design import rules as R
from app.design.parametric import DesignModel


class ConstraintEngine:
    def __init__(self, design: DesignModel):
        self.design = design
        self.results: list[dict] = []

    def _rect(self, x, y, w, d, rotation):
        fw, fd = R.footprint(int(w), int(d), rotation)
        return (x, y, x + fw, y + fd)

    def _overlap(self, a, b) -> bool:
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        return ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0

    def validate(self) -> dict:
        self._room_bounds()
        self._cabinets_vs_cabinets()
        self._cabinets_vs_appliances()
        self._openings_conflict()
        self._walkway()
        self._dimension_limits()
        score = max(0, 100 - self._error_count() * 10 - self._warning_count() * 5)
        return {"results": self.results, "score": score}

    def _room_bounds(self) -> None:
        W, L = self.design.room.width_mm, self.design.room.length_mm
        for c in self.design.cabinets:
            x0, y0, x1, y1 = self._rect(c.x, c.y, c.width_mm, c.depth_mm, c.rotation)
            if x1 > W + 5 or y1 > L + 5 or x0 < -5 or y0 < -5:
                self.results.append(
                    {"level": "error", "message": f"کابینت «{c.name}» از محدوده دیوارهای اتاق خارج است."}
                )

    def _cabinets_vs_cabinets(self) -> None:
        # Group by layer: base/tall vs wall. Cabinets on different Z layers
        # legitimately share a footprint in plan view.
        by_layer: dict[str, list] = {}
        for c in self.design.cabinets:
            layer = "wall" if c.type == "wall" else "base"
            by_layer.setdefault(layer, []).append(
                (c.id, c.name, self._rect(c.x, c.y, c.width_mm, c.depth_mm, c.rotation))
            )
        for layer, rects in by_layer.items():
            for i in range(len(rects)):
                for j in range(i + 1, len(rects)):
                    if self._overlap(rects[i][2], rects[j][2]):
                        self.results.append(
                            {
                                "level": "error",
                                "message": f"کابینت‌های «{rects[i][1]}» و «{rects[j][1]}» با یکدیگر تداخل دارند.",
                            }
                        )

    def _cabinets_vs_appliances(self) -> None:
        for ap in self.design.appliances:
            if ap.appliance_type in ("cooktop", "sink", "faucet"):
                continue  # intentionally mounted on top of a base cabinet
            ap_r = self._rect(ap.x, ap.y, ap.width_mm, ap.depth_mm, ap.rotation)
            hosted = False
            for c in self.design.cabinets:
                if c.type == "tall" and ap.appliance_type == "fridge":
                    if self._overlap(ap_r, self._rect(c.x, c.y, c.width_mm, c.depth_mm, c.rotation)):
                        hosted = True
                        break
                if c.type == "drawer" and ap.appliance_type == "dishwasher":
                    if self._overlap(ap_r, self._rect(c.x, c.y, c.width_mm, c.depth_mm, c.rotation)):
                        hosted = True
                        break
            if not hosted and ap.appliance_type in ("fridge", "dishwasher"):
                self.results.append(
                    {"level": "warning", "message": f"لوازم «{ap.name}» در کابینت جایگیری نشده است."}
                )

    def _openings_conflict(self) -> None:
        W, L = self.design.room.width_mm, self.design.room.length_mm
        for o in self.design.room.openings:
            if o.kind == "window":
                continue
            # door — check cabinets do not sit inside the door swing area
            door_rect = self._rect(
                float(o.position_mm),
                float(L - 900),
                o.width_mm,
                900,
                0,
            )
            for c in self.design.cabinets:
                if self._overlap(self._rect(c.x, c.y, c.width_mm, c.depth_mm, c.rotation), door_rect):
                    self.results.append(
                        {
                            "level": "warning",
                            "message": f"کابینت «{c.name}» با محدوده بازشدن درب ورودی تداخل دارد.",
                        }
                    )
                    break

    def _walkway(self) -> None:
        base_rects = [
            (c.name, self._rect(c.x, c.y, c.width_mm, c.depth_mm, c.rotation))
            for c in self.design.cabinets
            if c.type not in ("wall", "tall")
        ]
        for i in range(len(base_rects)):
            for j in range(i + 1, len(base_rects)):
                a, b = base_rects[i][1], base_rects[j][1]
                # runs on opposite walls
                if (a[0] == b[0] and a[2] == b[2]) or (a[1] == b[1] and a[3] == b[3]):
                    # parallel runs: vertical gap or horizontal gap
                    if a[1] == b[1] and a[3] == b[3]:
                        gap = abs(a[0] - b[2]) if a[2] <= b[0] else abs(b[0] - a[2])
                    else:
                        gap = abs(a[1] - b[3]) if a[3] <= b[1] else abs(b[1] - a[3])
                    if 0 < gap < R.WALKWAY_MIN:
                        self.results.append(
                            {
                                "level": "warning",
                                "message": f"فاصله عبور بین کابینت‌های «{base_rects[i][0]}» و «{base_rects[j][0]}» حدود {int(gap)} میلی‌متر است که کمتر از حد پیشنهادی {R.WALKWAY_MIN} میلی‌متر است.",
                            }
                        )

    def _dimension_limits(self) -> None:
        for c in self.design.cabinets:
            if c.width_mm < 100 or c.width_mm > 1500:
                self.results.append(
                    {
                        "level": "error",
                        "message": f"ابعاد کابینت «{c.name}» ({c.width_mm} میلی‌متر) از محدوده مجاز (۱۰۰ تا ۱۵۰۰ میلی‌متر) خارج است.",
                    }
                )

    def _error_count(self) -> int:
        return sum(1 for r in self.results if r["level"] == "error")

    def _warning_count(self) -> int:
        return sum(1 for r in self.results if r["level"] == "warning")
