# Cabora → FirX Capability Mapping

> **Status**: Compiled from Cabora's public help center / product pages (www.cabora.ai). Authenticated app inspection was NOT possible — the secure credential mechanism returned no credentials for any Cabora host (verified via git credential helper, netrc, git-credentials, env). Anything that requires a live login is marked **[UNKNOWN]**.
> **Evidence source**: `docs/cabora-reverse-engineering.md`. FirX basis: current backend (`app/design/`, `app/bom/`, `app/catalog/`, `app/validation/`) and frontend designer.

---

## 1. Cabinet Types & Parametric Structure

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| 21 parametric cabinet types grouped Base/Wall/Tall, each with small *unique* settings (blind-corner blind side + extension; trash pull-out bin count → min width; microwave opening height; hood opening width = chimney) | Library → drag → Properties shows type-specific controls; Build tab for interior | 8 coarse `type` strings (`base\|wall\|tall\|corner\|sink\|drawer\|oven\|fridge`) placed by engine; catalog rows have a `cabinet_type` enum | Add the full type taxonomy as an enum + a **TypeParams schema** per type (blind side/extension, bin count, opening heights, door config, drawer heights, shelf thickness). Persist type-specific params in the JSON snapshot |
| Common settings on every type (name, W/H/D, material, door style, finish, manufacturing method, molding, left/right filler) | Properties tab | `Cabinet{name,w,h,d,material,position}`; material on box | Add `box{door_style,manufacturing_method,finish_color}`, `molding{}`, `scribe{left,right}` to Cabinet; treat **manufacturing method (Paint Grade vs Prefinished)** as a first-class field since it drives materials/edge banding/costing |
| Properties panel 3 tabs: Properties / Build / **Info** (hardware list, edge banding spec, dimension summary for cut list) | Click cabinet → right panel | No Info tab; BOM is a separate endpoint | Add a derived `info` block per cabinet (hardware list, edge banding, cut-list dims) — computed, not stored |
| Presets: right-click → Save as Preset (captures type, dims, interior, hardware, finish); reuse across projects | Presets tab in library | None | Add a cabinet-preset entity (JSON fragment) reusable across projects |

## 2. Parameter System

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Editable W/H/D with per-type constraints (bin size → required width; oven opening height) | Type a number, engine adjusts/validates | Engine picks widths from catalog; no constraint records | Add **constraint layer** (`Constraint{code,level,param,nominal,effective}`) — user intent preserved, effective value derived, both in snapshot |
| Drawer-base: set each drawer height, remaining fills proportionally | Build tab → Interior Layout | Drawers not modeled | Add `interior.drawers[]` with per-drawer heights + proportional-fill derivation rule |
| Reveals (1/16") + door gap (1/8") as shop-wide construction standards, per-cabinet overridable | Shop Defaults → Construction Standards | None | Add `box.reveals{}` + `box.assembly` (dowel/confirmat) |
| Units inches throughout (configurable to metric) | Settings | FirX is mm-only | Keep mm; add display/export unit conversion (not internal) |

## 3. Relationships & Dependencies

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Fridge enclosure auto-creates linked Panel Fridge; moves/resizes together; top box width stays in sync; delete asks cascade | Drag enclosure → linked appliance appears; Appliance section in Properties | Appliance placed beside a `tall` fridge cabinet, positions copied once (one-way, fragile) | Add **generalized `links`** (`enclosure_cabinet_id`, `top_box_cabinet_id`, `clearance`) on Appliance so tracking is bidirectional and deletion is a cascade decision |
| Autoscribe: dragging flush to wall auto-adds scribe strip from active Shop Defaults profile; per-cabinet left/right filler override | Drag → toast "wall scribe auto-added" | None | Add `scribe{left_mm,right_mm}` auto-populated by a wall-adjacency rule; configurable default profile |
| End panels per cabinet per side; Advisor flags end panel against a wall | Build → End Panels | None | Add `end_panels{left,right}` + validation warning when exposed side faces wall/adjacent cabinet |
| Openings (doors/windows) affect run length; included in elevations | Openings tab → drag onto wall | Door swings shrink base-run span; windows kept under sink | Doors already modeled; add **wall usable-run** as an explicit derived field; include openings in elevation output |
| Appliances = placeholders, reserve space, no cut parts | Drag appliance → dims/position | Correct — appliances in design but BOM lists them as line items (they are "bought", not "built") | Keep; make the no-cut-parts rule explicit in BOM |
| Molding catalog (crown/light rail/sub-rail/toe kick/scribe) applied per project/run | Shop Defaults → Moldings; Properties → Molding | None | Add molding profile entity (name,type,height,projection,material,cost/ft) + per-cabinet assignment |

## 4. Layout Workflow

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Drag-drop snaps to wall; click-to-place; R rotate 90°; Shift multi-select align/distribute | Canvas | Engine auto-places runs (no free placement) | Add manual placement + snap; align/distribute only meaningful with free placement |
| Room setup: width/depth/ceiling editable anytime | Properties when nothing selected | `RoomParam` fixed at project level | Allow room resize to re-run engine |
| Brief-to-Layout (AI): plain language → full layout | AI panel → Generate Layout → describe | MockAIProvider → 14-section spec → DesignSpecification → DesignCanvas | Real intent: AI emits a **proposed Kitchen JSON** that passes engine validation before applying |

## 5. BOM / Materials

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Materials breakdown from **cut list sheet counts** × cost × waste factor | Costing tab | `_sheet_estimate()` = rough front-face area / sheet | Replace with component-derived sheet counts (see cut list) |
| Sheet goods with use tags (Carcass/Back/Drawer/Shelf) drive material quantities | Shop Defaults → Sheet Goods | `Material` table (type, thickness, price/sqm) | Add `use_tags` + cost-per-sheet; compute consumption per tag |
| Bill of Materials PDF: sheet goods, hardware, labor hours, grand cost vs retail | Export → BOM PDF | BOM endpoint returns rows+totals (no PDF) | Add labor-hours-per-operation and margin display; PDF export |
| BOM rows carry code/name/qty/dims/unit+total price | — | Already implemented (`bom_items` semantics in service) | Extend with edge banding + finish rows |

## 6. Costing

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Bottom-up: materials + hardware + labor(×rates) + finishing + install + overhead% + contingency% + margin% + tax + delivery | Costing tab | BOM totals only (cabinet price + appliance price + countertop price) | Implement the full **cost chain** as a pure function over the design; store `costing` config per project |
| Labor rates: blended shop rate or per-operation (machining/assembly/finishing/install); default $75/hr | Shop Defaults | None | Add labor config + per-cabinet labor-hours derivation |
| Markup: overhead 15%, margin 35%, waste 12%, tax, delivery; per-project overrides | Costing tab | None | Add markup config + per-project override (inheritance) |
| Price per linear foot sanity check; 3-tier label (Entry/Mid/High-End) from door style + finish | Costing summary | None | Add price-per-linear-meter + tier label |
| **Scenarios**: multiple pricing snapshots of same design (e.g. 3 finish tiers) | Costing → Scenarios | None | Add scenario snapshots of costing config |

## 7. Hardware

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Hardware derivation: hinges per door, slides per drawer, pulls per door+drawer, pins per adjustable shelf | Info tab / Costing → Hardware Breakdown | `app/bom/hardware.py` (just added): hinges=2×doors, slides=per drawer, pins=4×shelf, pulls=doors+drawers, width heuristic + explicit overrides | Already aligned; add edge-band spec and per-cabinet Info wiring; surface hardware in frontend |
| Hardware library with real per-unit costs; custom ordered parts; defaults Blum 110° + Tandem | Shop Defaults → Hardware | Hard-coded unit costs in `hardware.py` | Add hardware library entity (key,name,unit_cost) so costs come from tenant config |
| Fasteners (price/box, units/box); ordered parts (thickness, cost each) | Shop Defaults | None | Add fastener/ordered-part cost lines |

## 8. Cut List

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Cut list = per-cabinet **parts** (e.g. "B1.Left Side") with material, W×L×T, qty, grain, sheet ref | Cut Planner → review | None (BOM lists whole cabinets, not parts) | Add **component derivation** per cabinet (case sides, top/bottom, back, shelves, drawer boxes, doors, toe kick) → part rows with grain + edge banding |
| Optimizer nests parts on sheets (sheet size, waste factor/kerf, grain-locked orientation); re-run after any change | Cut Planner → Optimize | None | Add sheet-goods size config + a nesting/sheet-count function (guillotine bin-pack acceptable first pass) |
| Sheet reference carries into cut list + labels | Optimize → Sheet column | None | Add sheet ref to parts |
| Shop Mode: work order by station (Panel/Track/Table/Miter/Manual) with checkboxes, auto-saved progress | Cut Planner → Shop Mode | None | Add station routing rule (equipment profile) + part-status tracking |
| Cut list CSV export | Export → Cut List CSV | None | Add CSV export of part rows |
| Part labels (Avery 5163/5160) with dims, edge banding, sheet ref, QR; grouping by sheet or cabinet | Cut Planner → Export Labels | None | Add label data generation (QR payload = part JSON) |

## 9. Technical Drawings

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Shop Drawing PDF: axonometric, dimensioned plan, per-wall-run front elevations with per-cabinet labels, title block | Drawings tab | Frontend renders a canvas plan view only (no elevations, no export) | Add **wall-run elevation derivation** (project cabinets onto wall plane with dims + labels) |
| DXF R12 export (layers: outlines, dimensions, text, ref lines, fill regions) | Drawings → Export DXF | None | Add DXF R12 writer for plan + elevations |

## 10. Validation / Constraints

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Advisor surfaces constraints: corner efficiency, symmetry, dead zones, work triangle, clearances, vertical space, end-panel-against-wall | AI panel → Analyze Design | `ValidationResult` (ok/warning/error) + warnings (aisle <900, window overlap, dim limits) | Add: work-triangle check, dead-zone detection, end-panel waste, corner efficiency; produce **prioritized 3–8 suggestions with cabinet refs** |
| Type constraints: bin size → width, oven opening height | Properties enforcement | Partial (sink/dishwasher widths) | Move type rules into the constraint layer (§2) |
| Dimension limits flagged per cabinet | — | Already in warnings | — |

## 11. Project / Version Workflow

| Cabora capability | Observed workflow | FirX equivalent | FirX improve/add |
|---|---|---|---|
| Auto-save to cloud; unsaved-changes indicator; version history (named snapshots) | Save button; version history on Studio/Shop | `Design` + `DesignVersion{version_no, snapshot, change_desc}`; explicit save | Add auto-save debounce + dirty flag; add **named snapshots** with change description (partially present via `change_desc`) |
| Multi-room **Jobs** grouping projects; aggregated quote (total cost, price/ft, cabinet count, room count) | Job view | Project → single design only | Add Job entity + room grid + aggregated derived totals |
| Client CRM, share links, proposal send, status lifecycle (In Design → Client Review → Approved → In Shop → Install → Complete); client feedback pinned to cabinets | Share panel; status badge | None | Add status lifecycle + share/feedback model (feedback anchored to cabinet_id) |
| Per-project override of shop defaults (project-level takes precedence) | Costing tab | None | Add `materials.overrides` / `costing` project override layer |

## 12. Important UI Interactions (transferable UX patterns)

| Cabora interaction | Observed behavior | FirX relevance |
|---|---|---|
| Undo/redo at any time | ⌘Z/⇧⌘Z | All edits go through the JSON kernel → implement undo as snapshot diff |
| Unsaved-changes dot | Amber dot clears on save | Mirrors auto-save model |
| Multi-select align/distribute | Shift+click / box-select | Only after free placement (§4) |
| Keyboard shortcuts (R/C/F/?) | Rotate, center, fit, help | Easy wins for the canvas |
| Click-to-annotate elevations for client feedback | Client clicks cabinet in drawing | Requires elevation rendering (§9) |

---

## Top 5 Justified Next Actions for FirX

1. **Cabinet component derivation** → part rows (case/back/shelves/drawers/doors/toe kick) with grain + exposure-derived edge banding; feeds cut list, sheet counts, BOM, labels. **(DONE — `backend/app/bom/components.py`: `derive_components`/`aggregate_parts`/`sheet_count` with shelf-based bin packing; BOM endpoint returns `parts` + real sheet counts; frontend renders parts table. Grain-locked nesting + labels still to come.)**
2. **Costing engine** as a pure function: materials (from components) + hardware + labor + overhead + margin + tax; price-per-meter + tier label; scenario snapshots.
3. **Type taxonomy + constraint layer**: full enum + TypeParams + `Constraint{nominal,effective}` records persisted in the JSON snapshot.
4. **Elevation drawings + DXF R12 export** from the existing geometry (no 3D engine needed).
5. **Generalized appliance links** (enclosure/top-box coupling) + end panels + scribe fillers as first-class Cabinet fields.

## UNKNOWN (requires authenticated Cabora access)
Exact JSON snapshot schema; live derived-count refresh behavior; optimizer/nesting algorithm internals; actual render pipeline; label-export plan discrepancy; cost-tier exact rules.
