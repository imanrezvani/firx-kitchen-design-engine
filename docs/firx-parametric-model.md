# FirX Parametric Domain Model — Kitchen JSON as Source of Truth

> **Goal**: Define an original, parametric domain model for FirX, a parametric kitchen-design engine. The **Kitchen JSON** (a structured snapshot of the room, cabinets, appliances, walls, openings, materials, hardware, and derived outputs) is the single source of truth. Images, renders, and browser state are derived views — never authoritative. This model is inspired by the *observable concepts* of the Cabora product (see `cabora-reverse-engineering.md`) but is an original design: naming, schema, derivation rules, and behavior are FirX's own.

---

## 1. Design Principles

1. **Kitchen JSON is canonical.** Every render, drawing, cut list, BOM, cost estimate, and AI suggestion is *derived* from it. Persist it per design and per version.
2. **Editable vs derived, explicitly separated.** The JSON separates user-editable intent (`cabinets[].params`) from engine-derived results (`cabinets[].components`, `hardware`, `bom`, `cost`). Derived fields are recomputed on every change and tagged `derived: true`; they are never written by hand.
3. **Componentization.** A cabinet is a recipe of components (case, back, shelves, drawers, doors, toe kick, fillers, panels, molding). Hardware is attached to components (hinges → doors, slides → drawers, pins → adjustable shelves). This is what makes change propagation mechanical.
4. **Deterministic kernel.** All geometry, part generation, counts, and costs come from pure functions over the JSON. No AI randomness, no view-derived numbers.
5. **AI is advisory only.** AI emits structured *intent* (a proposed Kitchen JSON, a suggestion list, a layout brief) which is validated against the kernel before it becomes truth. AI never produces geometry directly.
6. **Units: millimetres internally** (FirX is metric-first, matching its Persian-language UI), inches only in display and export conversion. (Cabora is inches-first; this is a deliberate FirX divergence.)

---

## 2. Top-Level Document

```jsonc
{
  "schema_version": "1.0",
  "kitchen": {
    "id": "uuid",
    "name": "آشپزخانه اصلی",
    "project_id": "uuid",
    "created_at": "...", "updated_at": "...",
    "meta": { "author": "uuid", "source": "form|photo|ai-brief|manual", "plan": "studio" }
  },
  "room":      { ...Room, see §3 },
  "walls":     [ ...Wall ],           // derived from room + openings
  "openings":  [ ...Opening ],
  "obstacles": [ ...Obstacle ],
  "cabinets":  [ ...Cabinet, see §4 ],
  "appliances":[ ...Appliance, see §5 ],
  "countertops":[ ...Countertop, see §6 ],
  "materials": { ...MaterialLibrary, see §7 },   // shop defaults + overrides
  "hardware_library": { ... },                    // see §8
  "costing":    { ...CostingConfig, see §9 },
  "derived":    { ...DerivedOutputs, see §10 }
}
```

---

## 3. Room, Walls, Openings, Obstacles

```jsonc
Room {
  id, name,
  width_mm: 4200, length_mm: 3600, ceiling_height_mm: 2700,
  floor_z: 0,
  units: "mm"
}

Wall {
  id, side: "north|south|east|west",
  length_mm, thickness_mm: 150,
  // derived: usable run length on the interior face (deducts openings)
  usable_from_mm, usable_to_mm,       // derived
  has_door_swing: bool, door_swing_mm  // derived (shrinks base-run span)
}

Opening {            // door or window cut into a wall
  id, kind: "door|window",
  wall: "north", position_mm, width_mm, height_mm,
  sill_height_mm, swing: "left|right|double|none",
  // derived influence: openings reduce usable run length; windows are kept
  // (sink may sit under a window), doors shrink the run at their swing side.
}

Obstacle {           // column, radiator, water, drain, electrical, gas, other
  id, kind, wall, position_mm, width_mm, depth_mm, height_mm, notes
}
```

---

## 4. Cabinet

### 4.1 Core identity & editable params

```jsonc
Cabinet {
  id, name,                       // editable label → drawings/cut list/BOM
  type: CabinetType,              // see §4.3
  catalog_item_id,                // optional link to catalog row
  position: { x_mm, y_mm, z_mm, rotation_deg },  // z = bottom (toe kick below)
  box: {
    material_key,                 // -> materials.sheet_goods[key]
    manufacturing_method: "paint_grade|prefinished",
    finish_color_key,             // paint brand code or prefinished species
    door_style: "shaker|slab|none",
    door_config: "single|double|drawers_top|lift_up|split|none",
    reveals: { top_mm: 1.6, bottom_mm: 1.6, left_mm: 1.6, right_mm: 1.6,
               center_gap_mm: 3.2 },
    toe_kick_height_mm: 100,
    assembly: "dowel|confirmat|biscuit|spline"
  },
  interior: {
    back_panel: { enabled: true, material_key },
    end_panels: { left: "not_exposed|standard|stained|furniture",
                  right: "not_exposed|standard|stained|furniture" },
    shelves:  [ { id, y_mm, type: "fixed|adjustable", material_key, thickness_mm,
                  pin_type: "5mm|7mm" } ],
    drawers:  [ { id, y_mm, height_mm, width_mm, slides_type, interior_mm } ],
    island:   { double_sided: false, finished_back: false, overhang_mm } // island only
  },
  scribe: { left_mm: 0, right_mm: 0 },   // fillers; autoscribe sets these
  molding: { crown_key, light_rail_key, sub_rail_key, toe_kick_cap_key }, // -> moldings library
  type_specific: TypeParams,             // see §4.4
  // DERIVED (engine-filled):
  size:            { width_mm, height_mm, depth_mm },     // derived after constraints
  front:           { doors: [...], facade_total: ... },   // derived
  components:      [ ...CabinetComponent ],               // derived, §4.5
  hardware:        { hinges: n, slides: n, pulls: n, shelf_pins: n },  // derived
  constraints:     [ ...Constraint ],                     // derived, §12
  bom_refs:        [ ... ],                               // derived
}
```

**Editable vs derived (per type)** — full matrix in Appendix A; summary:

- **Editable**: name, box (material/method/finish/door style/config/reveals/assembly), interior (shelves, drawers, back, end panels), scribe fillers, molding, position, and each type's unique params.
- **Derived**: overall `size` (constrained by type rules — e.g., sink base min width from bin size, trash pull-out width from bin size), door/drawer fronts count + geometry from `door_config`, component part list, hardware counts, edge banding spec, material consumption, and constraint results.

### 4.2 Width/height/depth handling

Cabora treats W/H/D as directly editable fields. FirX adds a **constraint layer**: for each type a set of `WidthRule`/`HeightRule`/`DepthRule` (min/max/step/relation). The engine:
1. Takes the user-edited nominal size.
2. Applies the type's rules; emits a `Constraint` record for every adjustment or violation.
3. Stores both `nominal` (user intent) and `size` (effective, after rules) — so the UI can show "you asked 890, sink base minimum is 900 → 900" without losing intent.

This is a **justified divergence**: it makes corner/type coupling (blind corner extension, trash-bin width, oven opening height) explicit and auditable, which Cabora only hints at ("bin size affects the required cabinet width").

### 4.3 CabinetType taxonomy

```
base:     base | drawer_base | sink_base | blind_corner | lazy_susan
          | trash_pullout | island | vanity | desk_base | appliance_garage
          | filler
wall:     wall | corner_wall | microwave | open_shelves
tall:     tall_pantry | fridge_enclosure | wardrobe | oven_tower
          | linen_tower | hood
```

Each type registers: default size, min/max/step rules, door config options, interior defaults, and a `build_components()` recipe.

### 4.4 TypeParams (unique per type)

| Type | Unique editable params |
|---|---|
| base | door_config, drawer_count, drawer_heights[], shelf_count |
| drawer_base | drawer_heights[] (remaining height fills proportionally) |
| sink_base | false_drawer_fronts: bool, door_config |
| blind_corner | blind_side: L/R, blind_extension_mm |
| lazy_susan | corner_type: pie|full_round, shelf_count |
| trash_pullout | bin_count: 1|2, bin_size_key → min cabinet width (derived) |
| island | double_sided, overhang_lr_mm |
| desk_base | kneespace_width_mm, kneespace_height_mm |
| appliance_garage | door_type: tambour|lift_up |
| filler | (width only) |
| wall | height_from_floor_mm (default 1370 ≈ 54"), door_config |
| corner_wall | corner_type: square|diagonal, blind_side |
| microwave | opening_height_mm, upper_shelf: bool |
| open_shelves | shelf_count, shelf_thickness: 19|38mm |
| tall_pantry | door_config: single|double|split, shelf_count |
| fridge_enclosure | appliance_type: fridge|freezer|wine|paired, clearance_mm, top_box: bool |
| wardrobe | interior_layout: rod|shelf|combo |
| oven_tower | opening_height_mm, position_mm, storage_above/below: bool |
| linen_tower | shelf_count |
| hood | opening_width_mm (matches chimney), opening_height_mm |

### 4.5 CabinetComponent (derived parts)

```jsonc
CabinetComponent {
  id, parent_cabinet_id,
  kind: "left_side|right_side|top|bottom|back|shelf|drawer_box"
        "|drawer_front|door|toe_kick|filler|end_panel|crown|light_rail"
        "|sub_rail|fixed_shelf|vertical_stiffener",
  material_key, thickness_mm,
  width_mm, length_mm, depth_mm,   // in-material dimensions
  grain: "vertical|horizontal|any",
  edge_banding: ["front","left","right"],   // derived from exposure
  qty,
  hardware_refs: ["door_hinge","drawer_slide"],
  label: "B1.Left Side"            // cabinet index + part name (cut list)
}
```

Edge banding spec ("front + left + right") and grain are **derived from exposure** (which faces are visible given end panels, adjacency, wall contact, scribe). This matches Cabora's label/edge-band evidence and gives FirX a real cut-list foundation.

---

## 5. Appliance

```jsonc
Appliance {
  id, name, appliance_type: "fridge|cooktop|oven|hood|dishwasher|sink|faucet"
        |"fridge_drawer|wine_fridge|column_fridge|column_freezer|microwave"
        |"microwave_over_range|washer|dryer|wall_oven",
  catalog_item_id,
  size: { width_mm, height_mm, depth_mm },
  position: { x_mm, y_mm, z_mm, rotation_deg },
  panel_config: { panel_ready: bool, panel_material_key },   // panel-ready only
  links: {           // fridge-enclosure style coupling (FirX generalization)
    enclosure_cabinet_id: "uuid | null",
    top_box_cabinet_id:   "uuid | null",
    clearance_mm
  },
  manufactured: false     // layout placeholder: space + visuals only, no cut parts
}
```

**Coupling rule (generalized from Cabora's fridge enclosure):** any appliance may be *linked* to a cabinet. When the cabinet moves/resizes, the linked appliance tracks it; the top-box width stays in sync with the enclosure; deleting a cabinet with links prompts a cascade decision. FirX generalizes this into a first-class `links` mechanism rather than a fridge-only special case.

---

## 6. Countertop

```jsonc
Countertop {
  id, name,
  parent_run: "north|south|east|west|island|peninsula",
  width_mm, depth_mm, thickness_mm: 40,
  z_mm: 860, overhang_front_mm: 20,
  material_key,
  sink_cutout: { x_mm, y_mm, width_mm, depth_mm } | null,   // derived from sink appliance
  cooktop_cutout: { ... } | null                            // derived
}
```

Countertops are derived per run from the cabinets' back-edge alignment (same logic already in FirX engine, promoted to a documented rule). Cutouts are derived from the sink/cooktop appliance positions.

---

## 7. Materials Library

```jsonc
MaterialLibrary {
  sheet_goods: [ { key, name, thickness_mm, width_mm, length_mm,
                   core: "plywood|mdf|particleboard|melamine",
                   cost_per_sheet, use_tags: ["carcass","back","drawer","shelf"] } ],
  solid_stock: [ { key, name, species, thickness_mm, board_width_mm,
                   board_length_mm, cost_per_board_foot } ],
  edgebanding: [ { key, name, thickness_mm, width_mm, cost_per_m } ],
  moldings:    [ { key, name, type: "crown|light_rail|sub_rail|toe_kick|scribe",
                   height_mm, projection_mm, material_key, cost_per_m } ],
  finishing:   [ { key, name, kind: "paint|stain|sealer|topcoat",
                   cost_per_unit, coverage_m2_per_unit } ]
}
```

Shop defaults are inherited per project; a project may override any entry (overrides stored in `materials.overrides`). Fallback default estimates when a material key is missing.

---

## 8. Hardware Library

```jsonc
HardwareLibrary {
  hinges:   [ { key, name, brand, cost_each, style: "full_overlay|half_overlay|inset|push_to_open" } ],
  slides:   [ { key, name, cost_per_pair, kind: "undermount|side_mount|soft_close" } ],
  pulls:    [ { key, name, cost_each } ],
  shelf_pins:[ { key, name, diameter_mm: 5|7, cost_each } ],
  fasteners:[ { key, name, price_per_box, units_per_box } ],
  ordered:  [ { key, name, thickness_mm, cost_each } ]
}
```

Default hinge = soft-close 110°, default slide = undermount soft-close (FirX's own defaults, not Blum-specific).

---

## 9. Costing Config

```jsonc
CostingConfig {
  labor: { blended_rate_per_hr: 75,
           machining_rate, assembly_rate, finishing_rate, install_rate },
  markup: { overhead_pct: 15, target_margin_pct: 35, waste_pct: 12 },
  tax: { material_tax_pct: 0, delivery_fee: 0 },
  scenarios: [ { id, name, config_snapshot, total } ]   // multiple pricing snapshots
}
```

**Derived cost model** (matches the bottom-up chain, FirX formulas):
```
material_cost   = Σ sheets(per material) × cost/sheet × (1 + waste)   // sheets from cut list
hardware_cost   = Σ hardware counts × unit cost
labor_cost      = Σ labor_hours(op) × rate(op)        // hours derived per cabinet type
finishing_cost  = finishing_hours × finishing_rate + finishing_material
install_cost    = install_hours × install_rate
subtotal        = material + hardware + labor + finishing + install
overhead        = subtotal × overhead_pct
contingency     = subtotal × contingency_pct
cost_before_margin = subtotal + overhead + contingency
price           = cost_before_margin / (1 - margin_pct)   // margin-on-top
tax             = (material + hardware) × material_tax_pct
delivery        = delivery_fee
total_retail    = price + tax + delivery
price_per_linear_m = total_retail / total_run_length_m
tier            = tier_from(door_style, finish_complexity)  // entry|mid|high-end custom
```

---

## 10. Derived Outputs (top-level)

```jsonc
DerivedOutputs {
  cut_list:      [ ...CutPart ],     // from cabinets[].components, flattened + grain
  sheet_plan:    { nesting: [...], waste_pct, sheets_per_material },   // from optimizer
  hardware_bom:  { hinges, slides, pulls, shelf_pins, fasteners },     // aggregated
  materials_bom: [ { material_key, sheets, cost, waste } ],
  cost:          { ...computed from §9 },
  drawings:      { plan_bbox, elevations: [ ...WallElevation ], axo: {...} },
  validation:    { score, issues: [ ...Constraint ] },
  warnings:      [ ... ],
  labels:        [ ...LabelData ]      // part stickers w/ QR payloads
}
```

All fields are recomputed from the Kitchen JSON; nothing in `derived` is stored as authoritative input.

---

## 11. Change Propagation

1. A single edit mutates the Kitchen JSON (e.g., `cabinet.size.nominal`).
2. The **kernel** recomputes in dependency order:
   - `size` (constraints) → component recipe → cut parts & edge banding/grain
   - hardware counts (doors→hinges, drawers→slides, shelves→pins)
   - material consumption → sheets → materials BOM
   - cost chain (§9) → quote/proposal
   - elevations/plan (geometry from positions)
3. Views subscribe to the JSON and redraw from it (no view-owned state).
4. Every recompute produces a **diff**; the UI shows derived changes (e.g., "hinges 4 → 6") and, on save, creates a **DesignVersion** snapshot.

---

## 12. Constraint / Validation

```jsonc
Constraint {
  code: "cabinets.width.min",
  level: "error|warning|info",
  cabinet_id, param: "width_mm", nominal, effective,
  message: { fa, en },
  source: "type_rule|adjacency|opening|clearance|aisle"
}
```

Built-in rule families: type size rules (min/max/step), sink-vs-dishwasher adjacency, door swing clearance, window-column conflict (upper cabinets), aisle width (walkway min 900mm), end-panel-on-wall waste flag, work-triangle length, blind-corner opening interference, trash-bin width coupling, appliance clearances (fridge door swing, hood over cooktop).

---

## 13. AI Integration Points (structured intent only)

| AI feature | Emits (structured) | Consumed by |
|---|---|---|
| Brief-to-Layout | proposed `Kitchen.json` (rooms, cabinets, appliances) | kernel validation → applied only if constraints pass |
| Advisor | `Suggestion[] { priority, cabinet_refs, problem, action, expected_effect }` | UI + optional auto-apply as intent edits |
| Optimizer | `OptimizationInsight[] { kind, estimated_savings, suggested_param }` | UI (never silently mutates) |
| Copilot | tool-call intents (resize/replace/reposition) → applied as JSON edits through kernel | change propagation |

AI providers produce **proposals against the JSON schema**, never geometry or pixel output.

---

## Appendix A — Editable vs Derived Matrix (phase-2 detail)

| Type | Editable params | Derived from editable | UNKNOWN |
|---|---|---|---|
| base | door_config, #drawers, drawer heights, shelves, reveals | door/drawer front count; hinges=doors×config; slides=drawers; pins=adjustable shelves | hinge spacing rule; door overlap factor |
| drawer_base | #drawers, heights | remaining height fills proportionally; slides=#drawers | drawer front reveal math |
| sink_base | false fronts, door_config | hinges=fronts; opening width vs sink clearance | plumbing clearance min |
| blind_corner | blind_side, extension | usable opening width; door hardware for blind door | corner cabinet hardware spec |
| lazy_susan | corner_type, #shelves | shelf circle diameter vs box | rotating hardware part counts |
| trash_pullout | #bins, bin size | min cabinet width; bin slides | bin frame construction |
| island | double_sided, overhang | end panels both sides; finished back; countertop | overhang max before support |
| vanity | (standard) | depth class 18–21" influence on sinks/faucets | faucet clearance rules |
| desk_base | kneespace w/h | toe kick split; support panels | knee panel hardware |
| appliance_garage | door_type | tambour parts vs lift-up hinge parts | tambour track cost |
| filler | width | no components (non-structural) | max filler width rule |
| wall | height_from_floor, door_config | upper run z; hinges/lift mechanism | lift-up piston count |
| corner_wall | corner_type, blind_side | diagonal/squared front geometry | corner miter part count |
| microwave | opening height, upper shelf | cutout box; shelf above | microwave vent clearance |
| open_shelves | #shelves, thickness | shelf boards, brackets | bracket hardware per shelf |
| tall_pantry | door_config, shelf count | split doors + fixed shelf; hinges | split shelf thickness |
| fridge_enclosure | appliance_type, clearance, top_box | linked appliance; top-box sync width | gable panel material |
| wardrobe | interior layout | rod vs shelf parts | rod length limits |
| oven_tower | opening height/position, storage toggles | cutout box; storage sections | oven clearance codes |
| linen_tower | shelf count | (standard tall) | — |
| hood | opening width/height | cutout matching chimney | hood-to-cabinet spacing |

## Appendix B — Justified Adoptions vs Deliberate Divergences

**Adopt (concept, re-implemented originally):**
- Kitchen JSON as canonical source of truth; version snapshots.
- Componentized cabinet → hardware/cut-list/BOM/cost derivation chain.
- Shop-defaults inheritance with per-project override.
- Per-cabinet end panels, scribe/filler, molding profiles, type-specific params.
- Appliances as non-manufactured placeholders with linked enclosure coupling.
- Bottom-up 3-tier costing (materials/hardware/labor/overhead/margin), scenarios.
- 3–8 prioritized AI advisor output with cabinet references; optimizer insights with estimated savings.
- Version history named snapshots; multi-room jobs; status lifecycle; cut-list CSV; labels; DXF.

**Divergence (FirX-specific, justified):**
- **Metric-first** (mm) with inch display conversion (Cabora is inches-only).
- **Explicit constraint layer** with `Constraint` records (nominal vs effective) instead of silently clamping dimensions.
- **Generalized `links`** coupling for any appliance↔cabinet, not fridge-enclosure-only.
- **AI emits schema-valid intent** that passes kernel validation (Cabora's "AI reads project data" is vaguer).
- **Edge banding & grain derived from exposure** as first-class computed fields (Cabora shows them in Info/labels but does not document the derivation).
- Deterministic pure-function kernel designed to be unit-tested (FirX has 65 backend tests; this model is testable end-to-end).

## Appendix C — JSON lifecycle in FirX today vs target

| Aspect | Current FirX | Target |
|---|---|---|
| Source of truth | `DesignModel` (parametric.py) persisted as `snapshot` JSON on `Design` | Same persistence, schema extended with cabinets components/hardware/bom/cost |
| Cabinet | `Cabinet{type,w,h,d,x,y,z,rotation,material}` | Add box/interior/scribe/molding/type_specific/components/hardware |
| Derived outputs | `generate_bom()` rough estimate | Full derivation chain (§10) behind deterministic kernel |
| Versions | `DesignVersion{version_no, snapshot}` | Unchanged (already correct) |
| AI | MockAIProvider → `DesignSpecification` text sections | Keep; extend to optionally propose Kitchen JSON intents |

## Appendix D — Parametric model hardening status (implemented)

The parametric model is now the deterministic single source of truth; all
derived outputs are pure functions of it:

| Layer | Module | Status |
|---|---|---|
| Type registry | `app/design/cabinet_types.py` | 13 cabinet types, explicit defaults, `resolve_interior()` → counts + `Constraint` records (min/max clamp, invalid door_config) |
| Cabinet params | `app/design/parametric.py` `Cabinet` | Explicit editable fields: width/height/depth, type, `door_config` (none/single/double/lift_up/split/drawers_top), `drawer_count`, `shelf_count`, `toe_kick_height`, `end_panel_left/right`, `box_thickness`/`back_thickness`, `appliance_hook`, material |
| Components / cut parts | `app/bom/components.py` | `derive_components()` → parts with grain + exposure-derived edge banding; filler non-structural; `sheet_count()` shelf bin-packing |
| Hardware | `app/bom/hardware.py` | hinges=2×doors, slides=1/drawer, pins=4/shelf, pulls; uses the same resolver (no duplicate heuristics) |
| BOM | `app/bom/services.py` | Rows + totals + `parts` (numbered) + `material_estimate` + `sheets` |
| Numbering | `app/design/derive.py` `number_cabinets()` | Stable labels per group prefix (B/W/T/V/I/F) in design order |
| Material estimation | `app/design/derive.py` `material_estimate()` | Per (material, thickness) area + part counts from cut parts |
| AI visualization prompt | `app/design/derive.py` `build_visual_prompt()` + `DesignModel.visual_prompt` | Derived from the model at generation time; renderer consumes it, never a source of truth |
| Technical drawings | `app/design/drawings.py` `plan_geometry()` / `run_elevations()` + `GET /designs/{id}/drawings` | Plan view + per-wall-run elevations (along offset, dims, z, door/drawer/shelf counts, labels) derived as pure functions; no 3D engine |
| Costing engine | `app/bom/costing.py` `derive_cost()` + `GET /designs/{id}/cost` | Deterministic quote derived from the verified chain (material_estimate + hardware + edge banding + accessories + labor + appliances + countertops → overhead/contingency/margin/tax/delivery → retail + price-per-metre). Pricing in configurable `PricingConfig`, never hard-coded in the design engine |
| DXF export | `app/design/dxf_export.py` `design_to_dxf()` + `GET /designs/{id}/drawings.dxf` | ASCII DXF R12 serialized from the *same* plan/elevation geometry (no separate geometry source), with named layers (CABINETS/DIMENSIONS/TEXT/REFLINE/ROOM) |
| Propagation tests | `tests/test_param_propagation.py` | 25 tests: width→doors→hinges, drawer/shelf/end-panel/toe-kick/thickness chains, constraints, numbering, material aggregation, downstream readiness, partial-edit regression |
| Drawings tests | `tests/test_drawings.py` | 6 tests: plan geometry, rotation footprint swap, wall grouping + sorting, elevation entries, numbering match with cut list, determinism |
| Costing tests | `tests/test_costing.py` | 13 tests: determinism, structure, material/dimension/type/door/drawer/cabinet-count propagation, appliance/countertop prices, config overrides, price-per-metre, material-consistency |
| DXF tests | `tests/test_dxf_export.py` | 4 tests: valid R12 structure + layers, plan/elevation labels for every cabinet, determinism, derived-only-from-drawing-geometry |
| Suite | — | 129 backend tests passing; frontend tsc + eslint clean |

Change propagation guarantee (verified by tests): editing one editable parameter
(e.g. `drawer_count`) deterministically regenerates dependent components,
hardware, material consumption, numbering and BOM rows — with unaffected
derivations left untouched.
