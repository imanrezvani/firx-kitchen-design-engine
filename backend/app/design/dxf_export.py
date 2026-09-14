"""DXF R12 export derived from the parametric model's drawing geometry.

This serializes the *same* plan/elevation geometry produced by
``app.design.drawings`` (plan_geometry / run_elevations) — no separate
geometry source exists. The output is an ASCII DXF R12 file (AutoCAD
import-compatible), organised into named layers, exactly as documented for
the benchmark product's drawing export.

This is an export serializer, not a CAD engine.
"""

from __future__ import annotations

from app.design.drawings import plan_geometry, run_elevations
from app.design.parametric import DesignModel

LAYERS = ["CABINETS", "DIMENSIONS", "TEXT", "REFLINE", "ROOM", "OPENINGS", "APPLIANCES"]


def design_to_dxf(design: DesignModel) -> str:
    """Build a full DXF R12 document (plan + elevations) for a design."""
    out: list[str] = []
    _header(out)
    _tables(out)
    _entities(out, design)
    out.append("0")
    out.append("EOF")
    return "\n".join(out)


# ---------------------------------------------------------------------------
def _header(out: list[str]) -> None:
    out += ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4",
            "0", "ENDSEC"]


def _tables(out: list[str]) -> None:
    out += ["0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LTYPE",
            "70", "1", "0", "LTYPE", "2", "CONTINUOUS", "70", "0", "3", "",
            "72", "65", "73", "0", "40", "0.0", "0", "ENDTAB"]
    out += ["0", "TABLE", "2", "LAYER", "70", str(len(LAYERS))]
    for i, layer in enumerate(LAYERS, start=1):
        out += ["0", "LAYER", "2", layer, "70", "0", "62", str(i), "6", "CONTINUOUS"]
    out += ["0", "ENDTAB", "0", "ENDSEC"]


def _entities(out: list[str], design: DesignModel) -> None:
    out += ["0", "SECTION", "2", "ENTITIES"]

    # --- plan view ----------------------------------------------------------
    plan = plan_geometry(design)
    r = plan["room"]
    _line(out, "ROOM", 0, 0, r["width_mm"], 0)
    _line(out, "ROOM", r["width_mm"], 0, r["width_mm"], r["length_mm"])
    _line(out, "ROOM", r["width_mm"], r["length_mm"], 0, r["length_mm"])
    _line(out, "ROOM", 0, r["length_mm"], 0, 0)
    for cab in plan["cabinets"]:
        x, y, w, d = cab["x"], cab["y"], cab["w"], cab["d"]
        _rect(out, "CABINETS", x, y, w, d)
        cx, cy = x + w / 2, y + d / 2
        _text(out, "TEXT", cab["label"], cx, cy)

    # openings (windows/doors) on the plan
    for o in plan["openings"]:
        if o["wall"] in ("north", "south"):
            ox = o["position_mm"]
            ow = o["width_mm"]
            oy = 0.0 if o["wall"] == "north" else r["length_mm"]
            _line(out, "OPENINGS", ox, oy - 40, ox + ow, oy - 40)
        else:
            oy = o["position_mm"]
            ow = o["width_mm"]
            ox = 0.0 if o["wall"] == "west" else r["width_mm"]
            _line(out, "OPENINGS", ox - 40, oy, ox - 40, oy + ow)

    # appliance positions on the plan
    for a in plan["appliances"]:
        _rect(out, "APPLIANCES", a["x"], a["y"], a["w"], a["d"])
        _text(out, "TEXT", a["type"], a["x"] + a["w"] / 2, a["y"] + a["d"] / 2)

    # --- elevations (offset down the Y axis) --------------------------------
    elev = run_elevations(design)
    for idx, sheet in enumerate(elev):
        base_y = -r["length_mm"] - 400 - idx * (r["height_mm"] + 600)
        _line(out, "REFLINE", 0, base_y, r["width_mm"] + r["length_mm"], base_y)
        for cab in sheet["cabinets"]:
            x = cab["along_mm"]
            y0 = base_y
            y1 = base_y + cab["height_mm"]
            _rect(out, "CABINETS", x, y0, cab["width_mm"], cab["height_mm"])
            _text(out, "TEXT", cab["label"], x + cab["width_mm"] / 2, y1 + 60)
            # opening summary
            _text(out, "TEXT",
                  f"{cab['doors']}d/{cab['drawers']}dr/{cab['shelves']}s",
                  x + cab["width_mm"] / 2, y0 + cab["height_mm"] / 2)
            # dimension line
            _line(out, "DIMENSIONS", x, y1 + 120, x + cab["width_mm"], y1 + 120)
            _text(out, "DIMENSIONS", str(cab["width_mm"]),
                  x + cab["width_mm"] / 2, y1 + 160)

    out += ["0", "ENDSEC"]


def _rect(out: list[str], layer: str, x: float, y: float, w: float, h: float) -> None:
    _line(out, layer, x, y, x + w, y)
    _line(out, layer, x + w, y, x + w, y + h)
    _line(out, layer, x + w, y + h, x, y + h)
    _line(out, layer, x, y + h, x, y)


def _line(out: list[str], layer: str, x1: float, y1: float, x2: float, y2: float) -> None:
    out += ["0", "LINE", "8", layer, "10", _f(x1), "20", _f(y1), "11", _f(x2), "21", _f(y2)]


def _text(out: list[str], layer: str, value: str, x: float, y: float) -> None:
    out += ["0", "TEXT", "8", layer, "10", _f(x), "20", _f(y), "40", "50", "1", value]


def _f(v: float) -> str:
    return f"{float(v):.3f}"
