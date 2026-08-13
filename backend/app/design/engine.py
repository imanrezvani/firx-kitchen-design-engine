"""Deterministic, rule-based KitchenDesignEngine.

The engine converts a structured Room + Layout + Catalog selection into a real
parametric DesignModel: positioned cabinets, appliances, countertops,
clearances, warnings and a score. No AI, no optimization yet — deterministic
rules only, matching the product requirement for MVP phase 1.
"""

from __future__ import annotations

import uuid

from app.design import rules as R
from app.design.parametric import (
    AppliancePos,
    Cabinet,
    Countertop,
    DesignModel,
    RoomParam,
)

# ---------------------------------------------------------------------------
# layout run definitions
# ---------------------------------------------------------------------------

LAYOUT_WALLS = {
    "linear": ["north"],
    "L": ["north", "west"],
    "U": ["north", "west", "east"],
    "galley": ["west", "east"],
    "island": ["north", "west"],  # + island in the middle
    "peninsula": ["north", "west"],  # + peninsula off north run
}

LAYOUT_FA_NAME = {
    "linear": "خطی",
    "L": "L شکل",
    "U": "U شکل",
    "galley": "دوطرفه / گالی",
    "island": "جزیره",
    "peninsula": "شبه‌جزیره",
}


class KitchenDesignEngine:
    def __init__(
        self,
        room: RoomParam,
        layout: str,
        cabinets: list[dict],
        appliances: dict[str, dict],
        countertop_material: dict | None = None,
        cabinet_material: dict | None = None,
    ):
        self.room = room
        self.layout = layout
        self.cabinets = cabinets
        self.appliances = appliances
        self.countertop_material = countertop_material or {}
        self.cabinet_material = cabinet_material or {}
        self.W = room.width_mm
        self.L = room.length_mm
        self.H = room.height_mm
        self.design_cabinets: list[Cabinet] = []
        self.design_appliances: list[AppliancePos] = []
        self.countertops: list[Countertop] = []
        self.clearances: list[dict] = []
        self.warnings: list[str] = []
        self._cooktop_cab_ids: set[str] = set()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _door_walls(self) -> set[str]:
        return {o.wall for o in self.room.openings if o.kind == "door"}

    def _window_on(self, wall: str) -> dict | None:
        for o in self.room.openings:
            if o.kind == "window" and o.wall == wall:
                return o.model_dump()
        return None

    def _filler_widths(self) -> list[int]:
        widths = sorted(
            {
                int(c["width_mm"])
                for c in self.cabinets
                if c["cabinet_type"] in ("base", "drawer")
            },
            reverse=True,
        )
        if not widths:
            widths = [600, 400, 300]
        return widths

    def _cat(self, cabinet_type: str) -> dict | None:
        for c in self.cabinets:
            if c["cabinet_type"] == cabinet_type and c.get("is_active", True):
                return c
        return None

    def _app(self, kind: str) -> dict | None:
        return self.appliances.get(kind)

    # ------------------------------------------------------------------
    # placement
    # ------------------------------------------------------------------
    def _place_base(
        self,
        wall: str,
        a: float,
        cabinet_type: str,
        width: int | None = None,
        catalog: dict | None = None,
    ) -> Cabinet:
        tpl = R.run_axis(wall, self.W, self.L)
        cat = catalog or self._cat(cabinet_type) or {}
        w = width or int(cat.get("width_mm") or R.SINK_WIDTH)
        d = int(cat.get("depth_mm") or R.BASE_DEPTH)
        h = int(cat.get("height_mm") or R.BASE_HEIGHT)
        if tpl["along"] == "x":
            x, y = tpl["x0"] + a, tpl["y0"]
        else:
            x, y = tpl["x0"], tpl["y0"] + a
        cab = Cabinet(
            id=str(uuid.uuid4()),
            type=cabinet_type,
            catalog_item_id=cat.get("id") or None,
            width_mm=w,
            height_mm=h,
            depth_mm=d,
            x=float(x),
            y=float(y),
            z=R.TOE_KICK,
            rotation=tpl["rot"],
            material_id=self.cabinet_material.get("id") or None,
            material_name=self.cabinet_material.get("name"),
            name=cat.get("name") or cabinet_type,
        )
        self.design_cabinets.append(cab)
        return cab

    def _place_upper(self, wall: str, a: float, width: int, catalog: dict | None = None) -> Cabinet:
        tpl = R.run_axis(wall, self.W, self.L)
        cat = catalog or self._cat("wall") or {}
        w = width or int(cat.get("width_mm") or 600)
        d = int(cat.get("depth_mm") or R.UPPER_DEPTH)
        h = int(cat.get("height_mm") or R.UPPER_HEIGHT)
        # upper cabinets sit INSIDE the room along the run wall; depth = 350
        if tpl["along"] == "x":
            x, y = tpl["x0"] + a, tpl["y0"]
        else:
            x, y = tpl["x0"], tpl["y0"] + a
        cab = Cabinet(
            id=str(uuid.uuid4()),
            type="wall",
            catalog_item_id=cat.get("id") or None,
            width_mm=w,
            height_mm=h,
            depth_mm=d,
            x=float(x),
            y=float(y),
            z=float(R.UPPER_BOTTOM),
            rotation=tpl["rot"],
            material_id=self.cabinet_material.get("id") or None,
            material_name=self.cabinet_material.get("name"),
            name=cat.get("name") or "کابینت دیواری",
        )
        self.design_cabinets.append(cab)
        return cab

    def _place_tall(self, wall: str, a: float, width: int, catalog: dict | None = None) -> Cabinet:
        tpl = R.run_axis(wall, self.W, self.L)
        cat = catalog or self._cat("tall") or {}
        w = width or int(cat.get("width_mm") or R.FRIDGE_WIDTH)
        d = int(cat.get("depth_mm") or R.BASE_DEPTH)
        h = int(cat.get("height_mm") or R.TALL_HEIGHT)
        if tpl["along"] == "x":
            x, y = tpl["x0"] + a, tpl["y0"]
        else:
            x, y = tpl["x0"], tpl["y0"] + a
        cab = Cabinet(
            id=str(uuid.uuid4()),
            type="tall",
            catalog_item_id=cat.get("id") or None,
            width_mm=w,
            height_mm=h,
            depth_mm=d,
            x=float(x),
            y=float(y),
            z=0.0,
            rotation=tpl["rot"],
            material_id=self.cabinet_material.get("id") or None,
            material_name=self.cabinet_material.get("name"),
            name=cat.get("name") or "کابینت بلند",
        )
        self.design_cabinets.append(cab)
        return cab

    def _place_appliance(self, kind: str, x: float, y: float, rotation: int, catalog: dict | None = None) -> AppliancePos:
        cat = catalog or self._app(kind) or {}
        w = int(cat.get("width_mm") or {"fridge": 700, "dishwasher": 600, "cooktop": 600, "oven": 600}.get(kind, 600))
        h = int(cat.get("height_mm") or {"fridge": 1780, "dishwasher": 820, "cooktop": 60, "oven": 600}.get(kind, 600))
        d = int(cat.get("depth_mm") or {"fridge": 600, "dishwasher": 600, "cooktop": 520, "oven": 550}.get(kind, 600))
        z = 0.0
        if kind in ("cooktop", "sink", "faucet"):
            z = float(R.COUNTER_TOP_Z - R.COUNTER_THICKNESS)
        ap = AppliancePos(
            id=str(uuid.uuid4()),
            appliance_type=kind,
            catalog_item_id=cat.get("id") or None,
            width_mm=w,
            height_mm=h,
            depth_mm=d,
            x=float(x),
            y=float(y),
            z=z,
            rotation=rotation,
            name=cat.get("name") or kind,
        )
        self.design_appliances.append(ap)
        return ap

    # ------------------------------------------------------------------
    # runs
    # ------------------------------------------------------------------
    def _base_run_span(self, wall: str) -> tuple[float, float]:
        """(start_a, end_a) usable span of a wall run. Only DOOR swings shrink
        the span; windows are kept (the sink is placed under the window)."""
        axis_len = self.L if wall in ("west", "east") else self.W
        start, end = 100.0, float(axis_len - 100)
        for o in self.room.openings:
            if o.wall != wall or o.kind != "door":
                continue
            start = max(start, float(o.position_mm))
            end = min(end, float(o.position_mm + o.width_mm))
        return start, end

    def _fill(self, wall: str, a: float, length: float, skip_types: set[str]) -> float:
        """Fill a segment with base cabinets from the catalog. Returns the
        along-wall offset after the last placed cabinet."""
        while length >= 300 and length >= min(self._filler_widths(), default=1000):
            widths = [w for w in self._filler_widths() if w <= length]
            if not widths:
                break
            w = widths[0]
            cat = self._cat_by_width("base", w) or self._cat("base")
            self._place_base(wall, a, "base", w, catalog=cat)
            a += w + R.GAP
            length -= w + R.GAP
        return a

    def _cat_by_width(self, cabinet_type: str, width: int) -> dict | None:
        for c in self.cabinets:
            if (
                c["cabinet_type"] == cabinet_type
                and c.get("is_active", True)
                and int(c["width_mm"]) == width
            ):
                return c
        return None

    # ------------------------------------------------------------------
    # main generate()
    # ------------------------------------------------------------------
    def generate(self) -> DesignModel:
        layout = self.layout
        walls = LAYOUT_WALLS.get(layout, ["north"])

        # 1) cooking / sink / fridge anchor positions
        sink_wall = self._sink_wall()
        cook_wall = self._cook_wall(sink_wall)

        # 2) place runs
        if layout in ("L", "U", "island", "peninsula"):
            self._build_angled(sink_wall, cook_wall, walls)
        elif layout == "galley":
            self._build_galley(sink_wall, walls)
        else:  # linear
            self._build_linear(cook_wall, sink_wall)

        # 3) island
        if layout == "island":
            self._add_island()
        if layout == "peninsula":
            self._add_peninsula()

        # 4) upper wall cabinets above base runs
        self._build_uppers()

        # 5) countertops
        self._build_countertops()

        # 6) clearances, warnings, score
        self._compute_clearances()
        self._compute_warnings()

        score = 100 - (len(self.warnings) * 5) - self._error_count() * 10
        return DesignModel(
            id=str(uuid.uuid4()),
            name=LAYOUT_FA_NAME.get(layout, layout),
            layout=layout,
            room=self.room,
            cabinets=self.design_cabinets,
            appliances=self.design_appliances,
            countertops=self.countertops,
            clearances=self.clearances,
            warnings=self.warnings,
            score=max(0, score),
        )

    # -- sink / cook wall ---------------------------------------------------
    def _sink_wall(self) -> str:
        for w in ("west", "north", "east", "south"):
            if self._window_on(w):
                return w
        if "south" not in self._door_walls():
            return "north"
        return "west"

    def _cook_wall(self, sink_wall: str) -> str:
        for w in ("north", "east", "south", "west"):
            if w != sink_wall and w not in self._door_walls():
                return w
        return "north"

    def _build_angled(self, sink_wall: str, cook_wall: str, walls: list[str]) -> None:
        """Shared builder for L / U / island / peninsula base runs."""
        # cooking run
        self._cook_run(cook_wall, sink_wall)
        # sink run
        if sink_wall in walls:
            self._sink_run(sink_wall, cook_wall)
        # extra walls (U-shape: east wall prep/storage)
        for w in walls:
            if w not in (sink_wall, cook_wall):
                self._extra_run(w, sink_wall, cook_wall)

    def _cook_run(self, cook_wall: str, sink_wall: str) -> None:
        start, end = self._base_run_span(cook_wall)
        if end - start < 900:
            self.warnings.append("دیوار پخت‌وپز برای قرارگیری اجاق کوتاه است.")
            return
        a = float(start)
        # corner cabinet if the sink wall is perpendicular and adjacent
        if cook_wall in ("north", "south") and sink_wall in ("west", "east"):
            corner = self._cat("corner")
            if corner:
                self._place_base(cook_wall, a, "corner", int(corner["width_mm"]), corner)
                a += int(corner["width_mm"]) + R.GAP
        # cooktop
        cooktop = self._app("cooktop")
        cw = int(cooktop.get("width_mm") or R.COOKTOP_WIDTH) if cooktop else R.COOKTOP_WIDTH
        cook_cab = self._place_base(cook_wall, a, "oven", cw + 100)
        self._place_appliance("cooktop", cook_cab.x, cook_cab.y, cook_cab.rotation, cooktop)
        self._cooktop_cab_ids.add(cook_cab.id)
        # oven below (tall or under-counter)
        a += cw + 100 + R.GAP
        oven = self._app("oven")
        ow = int(oven.get("width_mm") or R.OVEN_WIDTH) if oven else R.OVEN_WIDTH
        oven_cab = self._place_base(cook_wall, a, "oven", ow)
        self._place_appliance("oven", oven_cab.x, oven_cab.y, oven_cab.rotation, oven)
        a += ow + R.GAP
        # fridge at run end (away from door)
        fridge = self._app("fridge")
        fw = int(fridge.get("width_mm") or R.FRIDGE_WIDTH) if fridge else R.FRIDGE_WIDTH
        a = self._fill(cook_wall, a, end - R.GAP - a - fw - 100, set())
        self._place_tall(cook_wall, a, fw, self._cat("tall"))
        self._place_appliance("fridge", 0, 0, 0, fridge)  # position fixed below
        # fix fridge appliance position to the tall cabinet
        fridge_ap = self.design_appliances[-1]
        fridge_ap.x, fridge_ap.y, fridge_ap.rotation = (
            self.design_cabinets[-1].x,
            self.design_cabinets[-1].y,
            self.design_cabinets[-1].rotation,
        )

    def _sink_run(self, sink_wall: str, cook_wall: str) -> None:
        start, end = self._base_run_span(sink_wall)
        # L/corner layouts: the perpendicular run occupies the corner up to
        # BASE_DEPTH, so the sink run must begin past it.
        if cook_wall in ("north", "south") and sink_wall in ("west", "east"):
            start = max(start, float(R.BASE_DEPTH))
        if end - start < 700:
            return
        win = self._window_on(sink_wall)
        axis_len = self.L if sink_wall in ("west", "east") else self.W
        center = win["position_mm"] + win["width_mm"] / 2 if win else axis_len / 2
        sink = self._app("sink")
        sink_cab = self._cat("sink")
        sw = int((sink or {}).get("width_mm") or (sink_cab or {}).get("width_mm") or R.SINK_WIDTH)
        a0 = max(start, center - sw / 2)
        # fill before sink
        a = self._fill(sink_wall, start, a0 - start, set())
        cab = self._place_base(sink_wall, a, "sink", sw, sink_cab)
        self._place_appliance("sink", cab.x, cab.y, cab.rotation, sink)
        a += sw + R.GAP
        # dishwasher beside sink
        dw = self._app("dishwasher")
        if dw:
            dw_cab = self._place_base(sink_wall, a, "drawer", int(dw.get("width_mm") or R.DISHWASHER_WIDTH))
            self._place_appliance("dishwasher", dw_cab.x, dw_cab.y, dw_cab.rotation, dw)
            a += int(dw.get("width_mm") or R.DISHWASHER_WIDTH) + R.GAP
        # fill after
        self._fill(sink_wall, a, end - a, set())

    def _extra_run(self, wall: str, sink_wall: str, cook_wall: str) -> None:
        """U-shape extra prep/storage run."""
        start, end = self._base_run_span(wall)
        if end - start < 600:
            return
        # reserve the corner adjacent to a perpendicular cook/sink run
        if cook_wall in ("north", "south") and wall in ("west", "east"):
            start = max(start, float(R.BASE_DEPTH))
        if sink_wall in ("north", "south") and wall in ("west", "east"):
            start = max(start, float(R.BASE_DEPTH))
        self._fill(wall, float(start), end - start, set())

    def _build_galley(self, sink_wall: str, walls: list[str]) -> None:
        if sink_wall not in ("west", "east"):
            sink_wall = "west"
        other = "east" if sink_wall == "west" else "west"
        self._sink_run(sink_wall, other)
        self._cook_run(other, sink_wall)

    def _build_linear(self, cook_wall: str, sink_wall: str) -> None:
        start, end = self._base_run_span(cook_wall)
        a = float(start)
        cooktop = self._app("cooktop")
        cw = int(cooktop.get("width_mm") or R.COOKTOP_WIDTH) if cooktop else R.COOKTOP_WIDTH
        cook_cab = self._place_base(cook_wall, a, "oven", cw + 100)
        self._place_appliance("cooktop", cook_cab.x, cook_cab.y, cook_cab.rotation, cooktop)
        a += cw + 100 + R.GAP
        oven = self._app("oven")
        ow = int(oven.get("width_mm") or R.OVEN_WIDTH) if oven else R.OVEN_WIDTH
        oven_cab = self._place_base(cook_wall, a, "oven", ow)
        self._place_appliance("oven", oven_cab.x, oven_cab.y, oven_cab.rotation, oven)
        a += ow + R.GAP
        fridge = self._app("fridge")
        fw = int(fridge.get("width_mm") or R.FRIDGE_WIDTH) if fridge else R.FRIDGE_WIDTH
        a = self._fill(cook_wall, a, end - a - fw - 100, set())
        self._place_tall(cook_wall, a, fw, self._cat("tall"))
        fridge_ap = self._place_appliance("fridge", 0, 0, 0, fridge)
        fridge_ap.x, fridge_ap.y, fridge_ap.rotation = (
            self.design_cabinets[-1].x,
            self.design_cabinets[-1].y,
            self.design_cabinets[-1].rotation,
        )
        # sink on the same wall after the run
        self._sink_run(sink_wall, cook_wall)

    def _build_uppers(self) -> None:
        """Place wall (upper) cabinets above base runs. Skipped over the sink
        (window zone), corner, cooktop (hood zone), tall/fridge and any window
        column."""
        window_cols: dict[str, tuple[int, int]] = {}
        for o in self.room.openings:
            if o.kind == "window":
                window_cols[o.wall] = (o.position_mm, o.position_mm + o.width_mm)

        for c in list(self.design_cabinets):
            if c.type in ("sink", "corner", "tall", "wall"):
                continue
            if c.id in self._cooktop_cab_ids:
                continue
            wall = self._wall_for_run(c)
            if not wall:
                continue
            # skip if this upper would overlap a window column
            col = window_cols.get(wall)
            along = c.x if wall in ("north", "south") else c.y
            if col and along < col[1] and along + c.width_mm > col[0]:
                continue
            self._place_upper(wall, along, c.width_mm)

    def _wall_for_run(self, c: Cabinet) -> str | None:
        if c.y <= 0.5 and c.rotation == 0:
            return "north"
        if c.rotation == 180:
            return "south"
        if c.rotation == 270:
            return "west"
        if c.rotation == 90:
            return "east"
        # island / peninsula (rotation 0, y > 0): no wall
        return None

    # -- island / peninsula --------------------------------------------------
    def _add_island(self) -> None:
        island_w, island_d = 1500, 900
        cx, cy = self.W / 2, self.L / 2
        cab = Cabinet(
            id=str(uuid.uuid4()),
            type="base",
            width_mm=island_w,
            height_mm=R.BASE_HEIGHT,
            depth_mm=island_d,
            x=cx - island_w / 2,
            y=cy - island_d / 2,
            z=R.TOE_KICK,
            rotation=0,
            material_id=self.cabinet_material.get("id"),
            material_name=self.cabinet_material.get("name"),
            name="جزیره",
        )
        self.design_cabinets.append(cab)
        self.countertops.append(
            Countertop(
                id=str(uuid.uuid4()),
                x=cx - island_w / 2,
                y=cy - island_d / 2,
                width_mm=island_w,
                depth_mm=island_d,
                thickness_mm=R.COUNTER_THICKNESS,
                z=R.COUNTER_TOP_Z - R.COUNTER_THICKNESS,
                material_id=self.countertop_material.get("id"),
                material_name=self.countertop_material.get("name"),
            )
        )

    def _add_peninsula(self) -> None:
        pen_w, pen_d = 1200, 900
        # attach to the north run's east end, extending south
        x0 = self.W - 600 - pen_w
        y0 = R.BASE_DEPTH
        cab = Cabinet(
            id=str(uuid.uuid4()),
            type="base",
            width_mm=pen_w,
            height_mm=R.BASE_HEIGHT,
            depth_mm=pen_d,
            x=float(x0),
            y=float(y0),
            z=R.TOE_KICK,
            rotation=0,
            material_id=self.cabinet_material.get("id"),
            material_name=self.cabinet_material.get("name"),
            name="شبه‌جزیره",
        )
        self.design_cabinets.append(cab)
        self.countertops.append(
            Countertop(
                id=str(uuid.uuid4()),
                x=float(x0),
                y=float(y0),
                width_mm=pen_w,
                depth_mm=pen_d,
                thickness_mm=R.COUNTER_THICKNESS,
                z=R.COUNTER_TOP_Z - R.COUNTER_THICKNESS,
                material_id=self.countertop_material.get("id"),
                material_name=self.countertop_material.get("name"),
            )
        )

    def _build_countertops(self) -> None:
        """One countertop per base run, plus island/peninsula already added."""
        runs: dict[str, tuple[float, float, float, float]] = {}
        for c in self.design_cabinets:
            if c.type in ("wall", "tall"):
                continue
            if c.name in ("جزیره", "شبه‌جزیره"):
                continue  # already have their own countertop
            # identify run by back-edge: y==0 north, y==L-BASE_DEPTH south, x==0 west, x==W-BASE_DEPTH east
            if c.y == 0:
                key = "north"
            elif c.y >= self.L - R.BASE_DEPTH - 1:
                key = "south"
            elif c.x == 0:
                key = "west"
            else:
                key = "east"
            x0, y0 = min(c.x, 0), min(c.y, 0)
            runs.setdefault(key, [x0, y0, 0, 0])
            runs[key][2] = max(runs[key][2], c.x + c.width_mm)
            runs[key][3] = max(runs[key][3], c.y + c.depth_mm)
        for key, (x0, y0, x1, y1) in runs.items():
            w = x1 - x0
            d = y1 - y0
            if w <= 0 or d <= 0:
                continue
            self.countertops.append(
                Countertop(
                    id=str(uuid.uuid4()),
                    x=float(x0),
                    y=float(y0),
                    width_mm=int(w),
                    depth_mm=int(d),
                    thickness_mm=R.COUNTER_THICKNESS,
                    z=R.COUNTER_TOP_Z - R.COUNTER_THICKNESS,
                    material_id=self.countertop_material.get("id"),
                    material_name=self.countertop_material.get("name"),
                )
            )

    # ------------------------------------------------------------------
    # clearances / warnings / score
    # ------------------------------------------------------------------
    def _compute_clearances(self) -> None:
        """Measure walkway gaps between base runs on OPPOSITE walls only.

        Adjacent cabinets within one run share a wall (back edge), so their
        10 mm joint gap is NOT a walkway. Only runs whose fronts face each
        other across the room produce an aisle.
        """
        runs: dict[str, dict] = {}
        for c in self.design_cabinets:
            if c.type in ("wall", "tall"):
                continue
            fw, fd = R.footprint(c.width_mm, c.depth_mm, c.rotation)
            x0, y0, x1, y1 = c.x, c.y, c.x + fw, c.y + fd
            key = {0: "north", 180: "south", 270: "west", 90: "east"}.get(c.rotation, "north")
            r = runs.setdefault(key, {"x0": x0, "y0": y0, "x1": x1, "y1": y1})
            r["x0"] = min(r["x0"], x0); r["y0"] = min(r["y0"], y0)
            r["x1"] = max(r["x1"], x1); r["y1"] = max(r["y1"], y1)

        opposite = {"north": "south", "south": "north", "west": "east", "east": "west"}
        checked: set[tuple] = set()
        for wall, r in runs.items():
            ow = opposite.get(wall)
            if not ow or ow not in runs or (wall, ow) in checked:
                continue
            checked.add((wall, ow))
            checked.add((ow, wall))
            other = runs[ow]
            if wall in ("north", "south"):
                gap = abs(r["y1"] - other["y0"]) if wall == "north" else abs(r["y0"] - other["y1"])
            else:
                gap = abs(r["x1"] - other["x0"]) if wall == "west" else abs(r["x0"] - other["x1"])
            self.clearances.append(
                {
                    "type": "aisle",
                    "gap_mm": round(float(gap), 1),
                    "between": (wall, ow),
                }
            )

    def _compute_warnings(self) -> None:
        # walkway / aisle checks
        for cl in self.clearances:
            gap = cl["gap_mm"]
            if gap < R.WALKWAY_MIN:
                self.warnings.append(
                    f"فاصله عبور بین کابینت‌ها {int(gap)} میلی‌متر است که کمتر از {R.WALKWAY_MIN} میلی‌متر پیشنهادی است."
                )
            elif gap < R.WALKWAY_PREFERRED:
                self.warnings.append(
                    f"فاصله عبور {int(gap)} میلی‌متر کمتر از مقدار پیشنهادی {R.WALKWAY_PREFERRED} میلی‌متر است."
                )
        # door / window conflicts
        for o in self.room.openings:
            if o.kind != "window":
                continue
            win_a = o.position_mm
            win_b = o.position_mm + o.width_mm
            for c in self.design_cabinets:
                if c.type == "wall":
                    # upper cabinet overlapping the window column
                    c_a, c_b = c.x, c.x + c.width_mm
                    if o.wall == "north" and not (c_b <= win_a or c_a >= win_b):
                        self.warnings.append("پنجره با کابینت دیواری تداخل دارد.")
                        break
        # dimension limits
        for c in self.design_cabinets:
            if c.width_mm < 100 or c.width_mm > 1500:
                self.warnings.append(
                    f"ابعاد کابینت {c.name} از محدوده مجاز خارج است."
                )

    def _error_count(self) -> int:
        return sum(1 for w in self.warnings if "تداخل" in w or "خطا" in w or "کوتاه" in w)
