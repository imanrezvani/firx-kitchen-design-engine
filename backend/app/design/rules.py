"""Engineering constants and geometry helpers shared by the design engine,
validation and BOM modules. All units are millimetres unless noted."""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Standard dimensions (mm) — can be overridden per tenant later.
# ---------------------------------------------------------------------------
TOE_KICK = 100
BASE_HEIGHT = 720          # cabinet body
COUNTER_THICKNESS = 40     # countertop
COUNTER_TOP_Z = TOE_KICK + BASE_HEIGHT + COUNTER_THICKNESS  # 860
COUNTERTOP_DEPTH = 620     # 600 carcass + 20 overhang
BASE_DEPTH = 600
UPPER_DEPTH = 350
UPPER_BOTTOM = 1350        # to underside of upper cabinet
UPPER_HEIGHT = 900
TALL_HEIGHT = 2200         # tall cabinets / fridge housing
DEFAULT_WALL_THICKNESS = 150

# Functional default widths (mm)
SINK_WIDTH = 900
DISHWASHER_WIDTH = 600
COOKTOP_WIDTH = 600
OVEN_WIDTH = 600
FRIDGE_WIDTH = 700
HOOD_WIDTH = 900
GAP = 10                  # clearance between adjacent cabinets

# Clearance rules (mm)
WALKWAY_MIN = 900
WALKWAY_PREFERRED = 1060
ISLAND_AISLE = 1000
WORK_TRIANGLE_MAX = 7900

# Standard cabinet height classes
BASE_TOTAL_HEIGHT = TOE_KICK + BASE_HEIGHT  # 820 to top of carcass

# ---------------------------------------------------------------------------
# Wall geometry: north at y=0, south at y=L, west at x=0, east at x=W.
# rotation is the direction the cabinet FRONT faces:
#   0 -> south (+y), 90 -> west (-x), 180 -> north (-y), 270 -> east (+x)
# ---------------------------------------------------------------------------
FRONT_VECTOR = {0: (0, 1), 90: (-1, 0), 180: (0, -1), 270: (1, 0)}


def footprint(w: int, d: int, rotation: int) -> tuple[int, int]:
    """Footprint (fw, fd) of a cabinet with nominal width w / depth d."""
    if rotation in (90, 270):
        return d, w
    return w, d


def run_axis(wall: str, room_w: int, room_l: int) -> dict:
    """Geometric template for placing a run against a wall.

    Returns origin (x0, y0) = the corner from which along-wall coordinate `a`
    grows, the base rotation for the run, and the axis lengths.
    """
    if wall == "north":      # y=0, run grows along +x, front faces +y
        return {"x0": 0, "y0": 0, "rot": 0, "along": "x", "axis_len": room_w}
    if wall == "south":      # y=L, run grows along +x, front faces -y
        return {"x0": 0, "y0": room_l - BASE_DEPTH, "rot": 180, "along": "x", "axis_len": room_w}
    if wall == "west":       # x=0, run grows along +y, front faces +x
        return {"x0": 0, "y0": 0, "rot": 270, "along": "y", "axis_len": room_l}
    # east
    return {"x0": room_w - BASE_DEPTH, "y0": 0, "rot": 90, "along": "y", "axis_len": room_l}


def along_wall_pos(pos_mm: float, wall: str, room_w: int, room_l: int) -> tuple[float, float]:
    """Convert an along-wall offset into an (x, y) footprint top-left corner."""
    tpl = run_axis(wall, room_w, room_l)
    if tpl["along"] == "x":
        return tpl["x0"] + pos_mm, tpl["y0"]
    return tpl["x0"], tpl["y0"] + pos_mm


def wall_center(window: dict | None, wall: str, room_w: int, room_l: int) -> float:
    """Along-wall offset of the centre of a wall segment."""
    if wall == "north":
        return window["position_mm"] + window["width_mm"] / 2 if window else room_w / 2
    if wall == "south":
        return window["position_mm"] + window["width_mm"] / 2 if window else room_w / 2
    return window["position_mm"] + window["width_mm"] / 2 if window else room_l / 2


def dist_pt(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
