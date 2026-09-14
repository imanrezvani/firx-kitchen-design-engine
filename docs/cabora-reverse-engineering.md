# Cabora Reverse Engineering — Product Model Analysis

> **Purpose**: Extract the observable conceptual model of Cabora (an AI cabinet design tool at https://www.cabora.ai) from its public help center and marketing pages. This document feeds the original FirX parametric domain model in `firx-parametric-model.md`. Nothing here copies Cabora source code, branding, or proprietary assets — only publicly documented product concepts, workflows, and data shapes are recorded.

## 0. Methodology & Source Base

- Sources: public pages at `www.cabora.ai` — homepage, `/cabinet-design-software`, and help-center articles: `/help/getting-started`, `/help/designing`, `/help/canvas-layout`, `/help/cabinet-types`, `/help/costing`, `/help/cut-list-shop-mode`, `/help/shop-defaults`, `/help/equipment`, `/help/clients-jobs`, `/help/ai`, `/help/exports`, `/help/sharing`, `/help/faq`.
- Fetch method: `webfetch` (markdown) of each URL. All facts below are quoted from or paraphrased from those pages.
- **Limitation**: No authenticated access was available (no app subdomain exposed; no credentials provisioned via the credential helper). Everything observed is the *documented* product surface. Anything requiring a live logged-in session (e.g., actual optimizer internals, exact JSON snapshot shape, real render behavior) is marked **[UNKNOWN]**.

---

## 1. Product Overview

Cabora is a browser-based, AI-assisted cabinet design and quoting tool aimed at hobbyists, DIYers, solo makers, and small cabinet shops. Key value proposition: **design a room → generate a cut list and cost estimate → share a polished proposal** — all in one place, from any device.

Three plan tiers shape the feature surface:

| Capability | Trial (14d) | Maker | Studio | Shop |
|---|---|---|---|---|
| Price | Free | $15/mo | $49/mo | $149/mo |
| Seats | 1 | 1 | 1 | 2+ |
| Projects | 1 | Unlimited | Unlimited | Unlimited |
| Cut list CSV | — | ✓ | ✓ | ✓ |
| Part stickers / cut sheet PDF | — | — | ✓ | ✓ |
| Shop drawing PDF / Quote / BOM PDF | Watermarked | — | ✓ | ✓ |
| DXF CAD export | — | — | ✓ | ✓ |
| Full 3-tier costing | ✓ | — | ✓ | ✓ |
| Multi-room jobs | ✓ | — | ✓ | ✓ |
| AI Advisor | 5 total | 10/mo | 25/mo | 150/mo |
| AI Copilot chat | 10 total | — | 50/mo | 300/mo |
| AI Optimizer + Brief-to-Layout | ✓ | — | ✓ | ✓ |
| AI Renders | 3 total | — | 25/mo | 100/mo |
| Client share links + CRM | — | — | ✓ | ✓ |
| Project version history | — | — | ✓ | ✓ |
| Custom branding on exports | — | — | — | ✓ |
| Client feedback portal / templates / custom send | — | — | — | ✓ |

Units: **inches everywhere** (room, cabinet, part dimensions). Working units Imperial/Metric are configurable in Shop Defaults (Working units, Room units, PDF units).

---

## 2. Project / Room / Job Hierarchy

- **Project** = a single room design (kitchen, bath, laundry, or custom). Created via New Project → choose room type → enter width, depth, ceiling height (inches).
- **Job** = a container grouping multiple room projects under one client (Studio/Shop). A Job wraps one or more Projects; a proposal from a Job shows all rooms in one link and one PDF. Job view shows aggregated quote (total cost, price/ft, total cabinet count, total room count).
- **Client** = CRM entity with name/company/email/phone/address/notes; completeness indicator.
- **Status lifecycle**: In Design → Client Review → Specs Approved → In Shop → Installation → Complete (project-level). Status auto-advances to Client Review when a proposal link is sent. ("Active/Review/Approved/Production/Install/Completed" naming used in the sharing article.)

---

## 3. The Editor (view model)

Top tabs: **Design** (plan view), **3D**, **Drawings**, **Methods** (per-cabinet manufacturing method), **Costing**, **Cut Planner**. Additional AI panel (bottom-right), notes/activity panel, feedback panel.

- Left panel: **Library** with three tabs — Cabinets (grouped Base/Wall/Tall), Appliances, Openings (doors/windows). A **Presets** tab holds saved cabinet configurations.
- Center: 2D canvas, top-down plan view. Drag-drop snaps to nearest wall; click-to-place; Shift multi-select (move/align/distribute); R rotate 90°; C center view; F fit; ⌘Z/⇧⌘Z undo/redo; ? shortcuts.
- Right panel: **Properties** panel. When a cabinet is selected it has three tabs: **Properties** (dimensions, position, door style, finish, material, molding, scribe fillers), **Build** (interior layout, back panel, end panels, island options), **Info** (hardware list, edge banding spec, dimension summary for cut list). Appliances show a single Properties view. When nothing selected, room settings (width/depth/ceiling) appear.
- Undo/redo at any time; **version history (named snapshots)** on Studio/Shop; auto-save to cloud with unsaved-changes indicator.

---

## 4. Cabinet Taxonomy

### 4.1 Common settings (every type, Properties tab)

- **Name** — label in drawings, cut list, BOM
- **Width / Height / Depth** — inches
- **Material** — box material from the sheet goods library
- **Door Style** — Shaker, slab, or none
- **Manufacturing Method** — Paint Grade or Prefinished Standard
- **Finish / Color** — paint color or prefinished species (per-cabinet overrides for two-tone layouts; brand paint codes accepted)
- **Molding** — crown, light rail, sub-rail, toe kick profile assignments
- **Left / Right Filler** — scribe strip width on each side

### 4.2 Base cabinets

| Type | Purpose | Unique settings |
|---|---|---|
| Base Cabinet | Standard floor-mounted, doors or drawers | Door configuration (single / double / drawers on top + door below); #drawers (Build tab); shelf count |
| Drawer Base | All-drawer, no doors | #drawers (typically 3–4); each drawer height individually set, remaining fills proportionally |
| Sink Base | Open interior for plumbing, no shelf/drawer | False drawer fronts toggle; door configuration (single/double) |
| Blind Corner | Fills inside corner run, access from one side | Blind side (L/R); blind extension (how far into corner) |
| Lazy Susan | Corner rotating shelves | Corner type (pie-cut / full-round); #shelves (typ. 2) |
| Trash Pull-out | Narrow base with bin hardware | #bins (1 or 2); bin size (affects required cabinet width) |
| Island | Free-standing base, not wall-attached | Double-sided toggle (affects back construction/finish); countertop overhang per side |
| Vanity | Bathroom base, shallower depth (18–21") | none beyond standard (set depth) |
| Desk Base | Kneespace cutout | Kneespace width; kneespace height (floor-to-underside) |
| Appliance Garage | Compact countertop upper, tambour or lift-up door | Door type (tambour / lift-up) |
| Filler | Narrow strip to close a gap; not structural | none (set width to gap) |

### 4.3 Wall cabinets

| Type | Purpose | Unique settings |
|---|---|---|
| Wall Cabinet | Standard upper | Height from floor (default 54" for kitchens); door configuration (single / double / lift-up) |
| Corner Wall | Upper for inside corner | Corner type (square L-interior / diagonal angled front); blind side (for square) |
| Microwave Cabinet | Wall cabinet with microwave cutout | Microwave height (clear opening); upper shelf toggle |
| Open Shelves | Wall-mounted open unit, frame + shelves only | #shelves; shelf thickness (¾" or 1½") |

### 4.4 Tall cabinets

| Type | Purpose | Unique settings |
|---|---|---|
| Tall Pantry | Floor-to-ceiling doors | Door configuration (single full-height / double / upper-lower split with fixed shelf); shelf count |
| Fridge Enclosure | Wraps fridge with finished gables + optional top box | Appliance type (fridge/freezer/wine/paired columns); clearance gap; top box toggle (linked wall cabinet) |
| Wardrobe | Full-height wardrobe/linen | Interior layout (hanging rod / shelf stack / combination) |
| Oven Tower | Houses wall oven | Oven opening height; oven position; storage above / below toggles |
| Linen Tower | Narrow tall (bath/laundry) | none beyond standard |
| Hood Cabinet | Frames a range hood, cutout at bottom | Hood opening width (matches chimney); hood opening height |

### 4.5 Build tab (interior, all types)

Sections: **Interior Layout** (add/remove/resize shelves & drawers; shelf pin type), **Back Panel** (toggle full-height back; material), **End Panels** (left/right exposed-side finish), **Island Options** (finished back; double-sided access — island only), **Assembly** (dowel vs confirmat fasteners; biscuit/spline joinery).

---

## 5. Parameters — Editable vs Derived

**Clearly editable (Properties):** name, W/H/D, material, door style, manufacturing method, finish/color, molding assignments, left/right filler widths; per-type unique settings (door config, drawer count/heights, shelf count, blind side, etc.).

**Derived (computed, shown in Info tab):** hardware list (hinges per door, slides per drawer, pulls per door+drawer, shelf pins per adjustable shelf), edge banding spec (e.g., "Front + Left + Right"), dimension summary for the cut list. **[UNKNOWN]** the exact formulas and whether Info numbers update live on every property change (docs strongly imply they do: "Change a door from single to double and the hinge count updates" is implied by the Info-tab description and the cut-list part naming "B1.Left Side" — but live in-app verification was not possible).

---

## 6. Cabinet Relationships & Coupling

Observable coupling facts (from the 2D Canvas guide):

1. **Wall-snap + Autoscribe**: dragging a cabinet flush to a wall auto-adds a scribe strip (filler) to that side, toast "wall scribe auto-added". Default scribe width comes from the **active Scribe Strip profile** in Shop Defaults → Moldings. Per-cabinet override via Left/Right Filler.
2. **Fridge enclosure → linked Panel Fridge appliance**: dragging a Fridge Enclosure auto-creates a Panel Fridge inside and links them. The appliance moves and resizes with the enclosure. Appliance type (fridge/freezer/wine/paired column), dimensions, and clearance gap are adjustable from the enclosure's Properties → Appliance section.
3. **Top box = linked wall cabinet**: added from the enclosure; width stays in sync with the enclosure automatically; height set independently. Moving the enclosure moves appliance + top box. Deleting the enclosure prompts whether to delete linked objects or leave them standalone.
4. **End panels are per-cabinet, per-side** (not exposed / standard / stained / furniture). Advisor flags end panels set on a side against a wall (suggests removal to save material cost).
5. **Openings (doors/windows)** affect available run length for cabinets on that wall and appear in elevation drawings. Door swings shrink usable run span; windows are kept (sink placed under window is the implied default — matching FirX behavior).
6. **Molding** is a shop-level catalog (name, type, height, projection, material, cost/ft) applied per project or per run; crown returns at corners.
7. **Appliances are layout placeholders**: they reserve space, affect visuals/renders, but **no cut list parts are generated for them**.

---

## 7. Materials, Manufacturing, Hardware

- **Two default manufacturing methods**:
  - **Paint Grade**: ¾" paint-grade ply carcass; ½" paint-grade ply back in a dado joint; painted on site; paint-grade iron-on edge banding.
  - **Prefinished Standard**: ¾" prefinished birch carcass; ½" prefinished birch back in dado; factory prefinished; color-matched 0.5mm PVC edge banding.
- **Construction standard**: frameless European-style (euro) with ¾" sheet goods and Blum hardware. Face-frame construction not supported.
- **Default hardware**: Blum 110° soft-close hinges, Blum Tandem Plus Blumotion drawer slides; overridable at shop level.
- **Materials library** (Shop Defaults): Sheet Goods (name, thickness, sheet size w×h, core type Plywood/MDF/Particleboard/Melamine, cost/sheet, **use tags**: Carcass/Back/Drawer Box/Shelf — tags used for material quantity calc), Solid Stock (species, thickness, board width, board length, cost/board-foot — for face frames, molding, fillers), Edgebanding (name, thickness mm, width mm, cost/linear-ft).
- **Hardware library**: hinges, drawer slides, pulls, shelf pins, fasteners (price/box, units/box), ordered parts (name, thickness, cost each). Custom hardware prices flow into the Hardware Breakdown.
- **Finishing**: paint/stain/sealer/topcoat with cost/unit and coverage rate (used for finishing labor + material cost on paint-grade jobs).
- **Construction Standards** (shop defaults, per-cabinet overridable): Reveal Top/Bottom/Left/Right (1/16"), Door Gap (1/8" between double doors), Toe Kick Height (4").
- **Appearance settings** (3D/render only, no construction impact): cabinet finish, countertop, hardware finish, wall color, floor, appliance style, backsplash, lighting, style preset; per-cabinet color overrides.
- **291 Sherwin-Williams / Benjamin Moore paint colors with LRV** (homepage claim).

---

## 8. Costing (3-tier job costing)

Costing tab = full retail quote: materials, hardware, labor, overhead, margin — broken down by line item. Quote summary shows total retail price, **price per linear foot**, and a **tier label** (Entry Custom / Mid Custom / High-End Custom based on door style + finish complexity).

**Line items** (bottom-up build):

| Line item | Covers |
|---|---|
| Material cost | Sheet goods at configured prices + waste factor |
| Hardware cost | Hinges, slides, pulls, pins — per cabinet |
| Labor | Hours × labor rate (blended shop rate or broken out) |
| Finishing | Paint/finish hours × finishing rate |
| Installation | Install hours × install rate |
| Overhead | % applied to total cost (default 15%) |
| Contingency | Buffer % for scope changes |
| Target margin | Gross margin goal on top (default 35%) |
| Material tax | Tax on materials/hardware |
| Delivery fee | Flat per-project freight charge |

- **Labor rates**: Shop rate $75/hr default (blended); optional Machining / Assembly / Finishing / Install rates. If only blended set, used for all labor.
- **Markup & margin**: Overhead % (15), Target margin % (35), Waste factor % (12), Material tax rate, Delivery fee.
- **Materials breakdown**: per-material table — sheets required, cost/sheet, waste, total. **Sheet count comes directly from the cut list** (exact parts + waste factor).
- **Hardware breakdown**: hinges (per door), slides (per drawer), pulls (per door+drawer), shelf pins (per adjustable shelf), custom ordered parts.
- **Scenarios tab**: save multiple pricing versions of the same design (e.g., three finish tiers) — each a snapshot of current costing settings.
- Shop Defaults pre-populate every project; **per-project overrides** allowed without touching defaults.

---

## 9. Cut List & Shop Mode

Cut Planner tab → four-step flow:

1. **Review cut list**: table of every part from every cabinet — Part Name (e.g., "B1.Left Side" = cabinet label + part name), Cabinet, Material, Width/Length/Thickness (inches), Qty, Grain (Vertical/Horizontal/Any), Sheet (populated after optimize). Sortable/filterable by material.
2. **Run optimizer**: nests parts onto full sheets (maximize yield/minimize waste) per material type. Sheet column fills; sheet overview shows each sheet with nested parts. Affected by: sheet size (Shop Defaults), waste factor (kerf buffer), grain direction (orientation-locked parts), equipment profile (cut sequencing). **Re-run after any design change.**
3. **Review sheet assignments**: zoom per sheet, see positions/orientations/waste; sheet reference ("Sheet 3") carries into cut list and labels.
4. **Shop Mode**: reorganizes cut list into a shop-floor work order sorted by cutting **station**: Panel Saw (full-sheet breakdown), Track Saw (sheet breakdown), Table Saw (rips + sled crosscuts within fence/sled limits), Miter Saw (short crosscuts within max crosscut), Manual (hand saw/jigsaw). Stations only appear for enabled tools; disabled-tool cuts reassign to next station. Checkbox per part marks it cut; stations collapse when done; progress auto-saved. **Station color-coding.**

**Cut list CSV export** (Maker+): one row per part with all on-screen columns.

**Labels PDF** (Studio+): Avery 5163 (2×4", 10/page) or Avery 5160 (1×2.625", 30/page); grouping By sheet (cut sequence) or By cabinet (assembly/packing). Each label: part name + parent cabinet, dimensions, material + edge banding spec, sheet reference, **QR code** encoding part details.

### 9.1 Equipment profiles

Multiple profiles (main shop / satellite). Tools:

- **Table Saw**: Fence (max rip width 12–60"), Sled width (0–48"), Max area (% of optimization load).
- **Miter Saw**: Max crosscut (4–24").
- **Track Saw**: enable only.
- **Panel Saw**: enable only.

Workflow prefs: **Cut order** (Rip first default / Crosscut first), **Preferred breakdown method** (Auto-detect / Track saw / Panel saw — only when both enabled). Example two-man shop: table saw fence 52"/sled 24"/max area 70%, miter max 16", track saw on, panel off, rip first.

---

## 10. Exports

| Export | Contents | Plan |
|---|---|---|
| Shop Drawing PDF | Axonometric 3D overview; dimensioned plan; front elevations per wall run with per-cabinet labels; floor/ceiling reference lines; cabinet labels matching cut list; title block (project/shop/date) | Studio+ |
| Quote PDF | Total retail, price/ft, itemized (materials/hardware/labor/overhead/margin), branding | Studio+ |
| Bill of Materials PDF | Every sheet good (qty/unit cost/total), every hardware item, labor hours by operation, grand cost vs retail (margin) | Studio+ |
| Client Proposal PDF | Logo/contact, project+client+date, renders or elevations, pricing summary, specs | Studio+ |
| Cut List CSV | One row per part: Cabinet, Part Name, W×L×T, Qty, Material, Grain, Sheet | Maker+ |
| Label PDF | Avery part stickers with QR | Maker+ (Studio+ per FAQ: "Part stickers PDF — Studio ✓" — FAQ table differs from Exports article table; **UNKNOWN** which is authoritative) |
| DXF CAD Export | ASCII DXF R12 of plan + elevations; layers: Cabinet outlines, Dimensions, Text labels, Reference lines, Fill regions | Studio+ |
| Shop Package ZIP | All shop docs bundled | Studio+ |

Branding (logo, company name/address/phone) on Shop plan via Settings → Shop Branding; applies to quote, proposal, drawing cover page, share page.

---

## 11. AI Features

- **AI Advisor** (Maker 10/mo, Studio 25/mo, Shop 150/mo): reviews current layout, returns **3–8 prioritized suggestions** (high/medium/low) with references to specific cabinets. Evaluates: corner cabinet efficiency, symmetry/visual balance, storage capacity & dead zones, workflow ergonomics (work triangle, clearances), vertical space usage, cabinet type choices. Trigger: AI panel → Analyze Design.
- **AI Copilot chat** (Studio 50/mo, Shop 300/mo): conversational assistant **with full access to project data** (dimensions, materials, costs, cut results). Can answer ("what's my total hinge count?") and **make changes** (resize, reposition, change types) from natural language.
- **AI Optimizer** (Studio+): analyzes build efficiency — sheet yield/waste %, material consolidation (fewer sheet types), part standardization (repeated sizes cut together), grain optimization, stock sheet size selection. Returns 3–8 insights with estimated savings in $ or sheets.
- **AI Brief-to-Layout** (Studio+): plain-language room description → complete cabinet layout (base + wall cabinets, appliances positioned). Editable afterward.
- **AI Renders** (Studio 25/mo, Shop 100/mo; trial 3 lifetime): photorealistic renders, 10–20s (FAQ says 30–60s; **UNKNOWN** discrepancy). Uses current 3D view angle; render prefs from Appearance panel; per-cabinet paint colors included. Saved to project; can be included in client exports. Render packs (25/100/500 credits).
- **AI reads project data**: Advisor/Optimizer/Copilot have access to project dimensions, materials, costs, cut results.

---

## 12. Collaboration & Sharing

- **Client share links** (Studio+): secure link, no client account needed. Client sees: AI render gallery, elevation drawings (click to annotate, pin feedback to specific cabinets), project name + note, proposal PDF download, Approve / Request Changes buttons, comment box.
- **Client responses**: Approve → status Approved; Request Changes → status returns to Active + comments appear in project. Email notifications.
- **Feedback panel**: comments; Resolve marks done (hidden but not deleted). On Shop, client annotations pinned to cabinets; clicking cabinet in editor highlights feedback.
- **Job share management**: Job view shows active links, viewed status, response, last-sent; resend; new link after revisions.
- **Activity panel**: Status quick buttons; private Notes; Message client (direct email).
- **Team**: Shop plan seats; roles editor/viewer; real-time simultaneous editing on Shop; other plans owner-edits-only. Onboarding call + custom send address on Shop.

---

## 13. Change Propagation & Derived-Output Chain

Public docs do not give a formal data model, but the following derivation chain is consistent with every article:

```
Shop Defaults (materials, hardware prices, labor rates, moldings,
  construction standards, equipment profile)
        │  inherited into each project (per-project override allowed)
        ▼
Project (room dims, openings, obstacles)  +  Library placements (cabinets,
  appliances, presets)  +  Properties edits (W/H/D, door style, drawers,
  shelves, end panels, molding, fillers)
        │  parametric kernel (single source of truth, in-browser + cloud
        │  autosave, version snapshots)
        ▼
Rendered views (plan / 3D)  ─────────────►  AI Render (uses view angle + prefs)
        │
        ├─► Cut list parts (per cabinet component, grain, edge banding spec)
        │        └─► Optimizer (sheets, waste, stations) → cut list CSV, labels
        ├─► Hardware list (hinges/slides/pulls/pins per cabinet) ──► BOM PDF
        ├─► Sheet count + waste ──► Materials breakdown ──► Costing
        │        (labor × rates, overhead %, margin) ──► Quote PDF, proposal
        ├─► Elevation drawings per wall run ──► Shop Drawing PDF, DXF
        └─► AI Advisor/Optimizer/Copilot inputs (dimensions, materials,
             costs, cut results)
```

**Change propagation**: every downstream artifact (drawings, cut list, BOM, quote) is derived, not hand-maintained. Docs imply edits flow through automatically ("re-run the optimizer to update the nesting" after design changes; version history on named snapshots).

---

## 14. Source-of-Truth Assessment

- The **parametric design model** is the source of truth; the canvas/3D/render are derived views. This is evidenced by: Properties edits driving all outputs, undo/redo + version snapshots, autoscribe auto-adding fillers, fridge-enclosure link sync, top-box width sync, "info tab = hardware list/edge banding/dimension summary" (derived), cut list parts named from cabinet labels.
- **AI is not the source of truth**: AI renders use view angle + appearance prefs but do not alter construction; AI features read the design, and AI-generated layouts are "editable afterward" — i.e., they emit parametric objects, not pixels.
- JSON snapshot existence: version history stores snapshots; "Export My Data" yields a ZIP of raw project data. **[UNKNOWN]** exact JSON schema.

---

## 15. Gaps / UNKNOWN Items (need authenticated access)

- Exact JSON snapshot schema for a project/design/version.
- Live behavior of derived counts (hinges/slides/pins) on property change (inferred, not observed).
- Optimizer algorithm internals (nesting/guillotine details beyond the "grain-locked" marketing claim).
- Render timing discrepancy (10–20s vs 30–60s).
- Label-export plan availability discrepancy (Exports article vs FAQ table).
- Face of the costing tier labels (Entry/Mid/High-End Custom) exact rules.
- Whether sheet-size/grain/kerf math uses imperial or metric internally beyond the inches UI.
