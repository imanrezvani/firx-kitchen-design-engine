"""Cabinet type registry — the deterministic heart of the parametric model.

Every cabinet type declares its editable parameters (defaults + allowed
values) and the derivation rules that turn those parameters into components,
hardware, materials, numbering and constraints. Derivation is a pure function
of the Cabinet model; changing one parameter re-resolves everything.

See docs/firx-parametric-model.md §4 (Cabinet), §4.5 (components), §12
(constraints).
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Supported door configurations. The door *count* each implies:
#   none        -> 0 doors (open or drawer-only fronts)
#   single      -> 1 door
#   double      -> 2 doors
#   lift_up     -> 1 lift-up (tambour/flap) front
#   split       -> 2 stacked door sections (tall pantry upper/lower)
#   drawers_top -> drawers above a door below (base), door count = 1
# ---------------------------------------------------------------------------
DOOR_CONFIGS = ("none", "single", "double", "lift_up", "split", "drawers_top")
DOOR_COUNT = {
    "none": 0,
    "single": 1,
    "double": 2,
    "lift_up": 1,
    "split": 2,
    "drawers_top": 1,
}


@dataclass(frozen=True)
class CabinetTypeSpec:
    type: str
    group: str                       # base|wall|tall
    label_prefix: str                # B / W / T  (cabinet numbering)
    default_width: int
    default_height: int
    default_depth: int
    door_configs: tuple[str, ...]    # allowed door configs
    default_door_config: str | None  # None => auto by width (<=450 single)
    supports_drawers: bool
    default_drawer_count: int
    supports_shelves: bool
    default_shelf_count: int
    default_toe_kick: int            # mm; 0 = no toe kick
    appliance_hook: str | None       # e.g. "sink", "oven", "fridge"
    min_width: int = 100
    max_width: int = 1500
    min_height: int = 100
    max_height: int = 2600
    min_depth: int = 50
    max_depth: int = 900


def _auto_door(width_mm: int) -> str:
    """Width heuristic: narrow boxes get one door, wider boxes two."""
    return "single" if width_mm <= 450 else "double"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
CABINET_TYPES: dict[str, CabinetTypeSpec] = {
    # --- base group --------------------------------------------------------
    "base": CabinetTypeSpec(
        type="base", group="base", label_prefix="B",
        default_width=600, default_height=720, default_depth=600,
        door_configs=("none", "single", "double", "drawers_top"),
        default_door_config=None,  # auto by width
        supports_drawers=True, default_drawer_count=0,
        supports_shelves=True, default_shelf_count=2,
        default_toe_kick=100, appliance_hook=None,
    ),
    "drawer": CabinetTypeSpec(
        type="drawer", group="base", label_prefix="B",
        default_width=600, default_height=720, default_depth=600,
        door_configs=("none",),
        default_door_config="none",
        supports_drawers=True, default_drawer_count=3,
        supports_shelves=False, default_shelf_count=0,
        default_toe_kick=100, appliance_hook=None,
    ),
    "sink": CabinetTypeSpec(
        type="sink", group="base", label_prefix="B",
        default_width=900, default_height=720, default_depth=600,
        door_configs=("none", "single", "double"),
        default_door_config="double",
        supports_drawers=False, default_drawer_count=0,
        supports_shelves=False, default_shelf_count=0,
        default_toe_kick=100, appliance_hook="sink",
    ),
    "corner": CabinetTypeSpec(
        type="corner", group="base", label_prefix="B",
        default_width=1000, default_height=720, default_depth=600,
        door_configs=("single", "double"),
        default_door_config="single",
        supports_drawers=False, default_drawer_count=0,
        supports_shelves=True, default_shelf_count=1,
        default_toe_kick=100, appliance_hook=None,
    ),
    "vanity": CabinetTypeSpec(
        type="vanity", group="base", label_prefix="V",
        default_width=600, default_height=600, default_depth=480,
        door_configs=("none", "single", "double"),
        default_door_config=None,
        supports_drawers=True, default_drawer_count=0,
        supports_shelves=True, default_shelf_count=1,
        default_toe_kick=100, appliance_hook="faucet",
    ),
    "island": CabinetTypeSpec(
        type="island", group="base", label_prefix="I",
        default_width=1500, default_height=720, default_depth=900,
        door_configs=("none", "double", "drawers_top"),
        default_door_config="none",
        supports_drawers=True, default_drawer_count=2,
        supports_shelves=False, default_shelf_count=0,
        default_toe_kick=100, appliance_hook=None,
        max_depth=1200,
    ),
    # --- wall group --------------------------------------------------------
    "wall": CabinetTypeSpec(
        type="wall", group="wall", label_prefix="W",
        default_width=600, default_height=900, default_depth=350,
        door_configs=("none", "single", "double", "lift_up"),
        default_door_config=None,
        supports_drawers=False, default_drawer_count=0,
        supports_shelves=True, default_shelf_count=2,
        default_toe_kick=0, appliance_hook=None,
    ),
    "microwave": CabinetTypeSpec(
        type="microwave", group="wall", label_prefix="W",
        default_width=600, default_height=700, default_depth=350,
        door_configs=("single", "double"),
        default_door_config="single",
        supports_drawers=False, default_drawer_count=0,
        supports_shelves=True, default_shelf_count=1,
        default_toe_kick=0, appliance_hook="microwave",
    ),
    "hood": CabinetTypeSpec(
        type="hood", group="wall", label_prefix="W",
        default_width=900, default_height=700, default_depth=350,
        door_configs=("none",),
        default_door_config="none",
        supports_drawers=False, default_drawer_count=0,
        supports_shelves=False, default_shelf_count=0,
        default_toe_kick=0, appliance_hook="hood",
    ),
    # --- tall group --------------------------------------------------------
    "tall": CabinetTypeSpec(
        type="tall", group="tall", label_prefix="T",
        default_width=600, default_height=2200, default_depth=600,
        door_configs=("none", "single", "double", "split"),
        default_door_config=None,
        supports_drawers=False, default_drawer_count=0,
        supports_shelves=True, default_shelf_count=4,
        default_toe_kick=0, appliance_hook=None,
        max_height=2600,
    ),
    "oven": CabinetTypeSpec(
        type="oven", group="tall", label_prefix="T",
        default_width=600, default_height=2200, default_depth=600,
        door_configs=("single", "double"),
        default_door_config="single",
        supports_drawers=False, default_drawer_count=0,
        supports_shelves=True, default_shelf_count=2,
        default_toe_kick=0, appliance_hook="oven",
        max_height=2600,
    ),
    "fridge": CabinetTypeSpec(
        type="fridge", group="tall", label_prefix="T",
        default_width=900, default_height=2200, default_depth=700,
        door_configs=("none",),
        default_door_config="none",
        supports_drawers=False, default_drawer_count=0,
        supports_shelves=False, default_shelf_count=0,
        default_toe_kick=0, appliance_hook="fridge",
        max_width=1200, max_height=2600,
    ),
    # narrow non-structural filler strip
    "filler": CabinetTypeSpec(
        type="filler", group="base", label_prefix="F",
        default_width=100, default_height=720, default_depth=600,
        door_configs=("none",),
        default_door_config="none",
        supports_drawers=False, default_drawer_count=0,
        supports_shelves=False, default_shelf_count=0,
        default_toe_kick=0, appliance_hook=None,
        max_width=300,
    ),
}


@dataclass(frozen=True)
class Constraint:
    code: str
    level: str                      # error|warning|info
    cabinet_id: str
    param: str
    nominal: int | None
    effective: int
    message_fa: str


@dataclass(frozen=True)
class ResolvedInterior:
    door_config: str
    door_count: int
    drawer_count: int
    shelf_count: int
    toe_kick_height: int
    box_thickness: int
    back_thickness: int
    constraints: tuple[Constraint, ...]


def spec_for(cabinet_type: str) -> CabinetTypeSpec:
    return CABINET_TYPES.get(cabinet_type, CABINET_TYPES["base"])


def resolve_interior(cab) -> ResolvedInterior:
    """Resolve a cabinet's editable parameters into concrete counts.

    Deterministic and side-effect free. Explicit cabinet fields win over type
    defaults; violations produce Constraint records with the effective value.
    """
    spec = spec_for(cab.type)
    constraints: list[Constraint] = []
    cid = cab.id or ""

    def clamp(v: int, lo: int, hi: int, param: str) -> int:
        if v < lo:
            constraints.append(Constraint(
                code="cabinet.param.min", level="warning", cabinet_id=cid,
                param=param, nominal=v, effective=lo,
                message_fa=f"{param} از حداقل مجاز کمتر است ({v} → {lo})."))
            return lo
        if v > hi:
            constraints.append(Constraint(
                code="cabinet.param.max", level="warning", cabinet_id=cid,
                param=param, nominal=v, effective=hi,
                message_fa=f"{param} از حداکثر مجاز بیشتر است ({v} → {hi})."))
            return hi
        return v

    w = clamp(cab.width_mm, spec.min_width, spec.max_width, "width_mm")
    h = clamp(cab.height_mm, spec.min_height, spec.max_height, "height_mm")
    d = clamp(cab.depth_mm, spec.min_depth, spec.max_depth, "depth_mm")

    # door configuration
    dc = getattr(cab, "door_config", None)
    explicit_dc = dc is not None and dc != ""
    if not explicit_dc or dc not in spec.door_configs:
        if explicit_dc:
            # user explicitly chose a config this type does not allow
            constraints.append(Constraint(
                code="cabinet.door_config.invalid", level="error", cabinet_id=cid,
                param="door_config", nominal=None, effective=w,
                message_fa="تنظیمات درب برای این نوع کابینت معتبر نیست."))
        dc = spec.default_door_config or _auto_door(w)
    if dc not in spec.door_configs:
        dc = _auto_door(w)

    # drawer count
    drawers = getattr(cab, "drawer_count", None)
    if drawers is None or not spec.supports_drawers:
        drawers = spec.default_drawer_count

    # shelf count
    shelves = getattr(cab, "shelf_count", None)
    if shelves is None or not spec.supports_shelves:
        shelves = spec.default_shelf_count

    # toe kick
    tk = getattr(cab, "toe_kick_height", None)
    if tk is None:
        tk = spec.default_toe_kick
    tk = max(0, int(tk))

    # material thicknesses
    box_thk = getattr(cab, "box_thickness", None) or 18
    back_thk = getattr(cab, "back_thickness", None) or 16

    return ResolvedInterior(
        door_config=dc,
        door_count=DOOR_COUNT[dc],
        drawer_count=max(0, int(drawers)),
        shelf_count=max(0, int(shelves)),
        toe_kick_height=tk,
        box_thickness=box_thk,
        back_thickness=back_thk,
        constraints=tuple(constraints),
    )
