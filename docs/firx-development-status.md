# FirX Development Status

> **Source of truth is the repository/code/tests/API**, not this document. If this
> file conflicts with the code, inspect and correct the status.

---

## Current phase
**Phase 7 (Product UX) + follow-on hardening** — costing/API/frontend/drawings/cut-list/AI phases are complete; continuing high-value gaps.

## Completed phases
- **P1–3 Costing engine + Cost API + Frontend costing** — DONE
- **P4 Technical drawings** — DONE (plan+elevations+DXF, openings/appliances, propagation tests)
- **P5 Cut list / manufacturing data hardening** — DONE (part IDs, `/cut-list` endpoint, frontend card)
- **P6 AI pipeline review** — DONE (AI emits validated spec; engine is truth; `visual_prompt` model-derived)
- **P7 Product UX (first pass)** — DONE (cabinet property editor, cut-list card, canvas numbering, edit-persistence bug fix)

## Current task
Surface deterministic costing in aggregate views + close remaining high-value gaps.

## Completed tasks in current phase
- **Cost endpoint** `GET /designs/{id}/cost` (project override merged over defaults + tenant appliance prices + tenant material prices).
- **Per-project costing config** `GET/PUT /projects/{id}/costing` (PricingConfig snapshot persisted on Project).
- **Frontend**: quote card + editable pricing settings (margin/overhead/tax/delivery) in designer.
- **Cut-list endpoint** `GET /designs/{id}/cut-list` + frontend "لیست برش" card with part IDs.
- **Drawings**: plan now includes openings + appliance positions; DXF layers OPENINGS/APPLIANCES; parameter-change→drawing tests.
- **Visualization endpoint** `GET /designs/{id}/visualization` (model-derived prompt; AI output never writes geometry).
- **Dashboard stats** now return per-design `total_retail`; **reports page** shows تخمین قیمت column.
- **DesignCanvas** shows cabinet numbers (B1/W1/T1) matching cut list/drawings.
- **Frontend render button** "پرامپت رندر AI" in designer → displays derived prompt + structured inputs.
- **Quote document** `GET /designs/{id}/quote.html` — dependency-free RTL HTML quote derived from the same cost breakdown; frontend "پیشفاکتور (PDF/چاپ)" button (auth-token blob fetch, opens for print/save-PDF).
- **Performance pass (2D canvas)**: `DesignCanvas` wrapped in `React.memo` (stable `useCallback` select/edit handlers) so unrelated state updates no longer rebuild the Konva scene; edit persistence debounced 400ms (optimistic local update + batched PUT); **`perfectDrawEnabled={false}`** on canvases' Layers and draggable Groups (disables pixel-perfect hit-canvas caching — faster render/drag on large designs).
- **Dashboard cost display**: home dashboard recent-designs list now shows "قیمت تخمینی" per design (from `/dashboard/stats` `total_retail`).
- **Project detail designs list**: new `GET /projects/{id}/designs` endpoint (designs + derived `total_retail`); project detail page now shows a designs table with چیدمان / قیمت تخمینی / تاریخ / open action.
- **AI Designer UX**: projects now load on mount (previously only on select click — save button was disabled until the user clicked the project select); after saving a design, an "باز کردن طرح ذخیرهشده" link appears (captures the generated design id).
- **Spatial editor drag**: placed objects are now draggable (reposition via `onDragEnd`, mapping Konva node position back to an along-wall offset using the same geometry as `objectRect`; island objects reposition freely). Previously click-to-place only. **Verified E2E 4/4**: placement adds offset entry + drag changes offset (۲→۳).
- **Canvas perf**: `perfectDrawEnabled={false}` on canvases' Layers and draggable Groups (disables pixel-perfect hit-canvas caching).
- **Photo upload**: ai-designer photo section now supports uploading images from the device via `POST /projects/{id}/files` (FormData + auth token), falling back to URL entry; uploaded photos listed with caption.
- **2D editor zoom/pan**: mouse-wheel zoom (0.4x–3x, cursor-centered) + drag-pan on empty room area in the DesignCanvas; zoom % shown in footer. **Verified E2E**: 100%→106% on wheel-up.
- **Responsive mobile layout**: AppShell rewritten with a responsive sidebar — desktop (`lg`) keeps the fixed sidebar; mobile gets a top bar with a hamburger drawer (no more forced horizontal overflow). Tables wrapped in `overflow-x-auto` (projects/reports/catalog); step indicator + input grids made responsive on the designer; settings/project-detail/ai-designer/designer grids now `grid-cols-1 md:grid-cols-*` with `md:`-prefixed col-spans. **Verified E2E: all 7 protected pages have zero horizontal overflow at 390px.**
- **Light/Dark mode**: `.dark` CSS-variable palette in `globals.css`; shared UI primitives (`input`/`field`/`button`/app shell/auth pages) use `bg-card`/`bg-background` tokens instead of hardcoded white; theme toggle in the sidebar footer + mobile header; persisted in `localStorage('firx_theme')` and initialised from `prefers-color-scheme`; no-flash inline script in the root layout. **Verified E2E 6/6**: toggle applies `.dark`, background changes, persists after reload, toggles back.
- **Bug fixed**: `PUT /designs/{id}` JSON snapshot in-place mutation → edit never persisted (now assigns a fresh dict).

## Partially completed tasks
- None blocking.

## Remaining tasks (candidate next gaps)
1. **PDF exports** — quote.html is print-to-PDF; native PDF (BOM/quote/shop-drawing) would need a dependency (deferred as not justified).
2. Performance: further canvas optimizations if needed.
3. Multi-language architecture (UI is Persian-only).

## Tests
- **138 backend tests passing** (costing 16, dxf 4, drawings 9, propagation 25, components 8, hardware 8, design-edit 2, AI 39, others).
- Frontend `tsc --noEmit` + `eslint` clean.
- E2E (Playwright chromium): designer **9/9**, dashboard **2/2**, project detail **3/3**, ai-designer save→open **2/2**, spatial placement+drag **4/4**, zoom **3/3**, mobile flow **4/4**, mobile overflow scan **7/7 pages clean**, dark mode **6/6**.

## Live verification
- `/cost`: retail + price-per-metre, all line items (verified with tenant prices merged).
- `/projects/{id}/costing` GET/PUT: margin 35→50 changes retail 161.4M→209.2M, restore works.
- `/cut-list`: 176 parts, 225 qty, 28 sheets, stable IDs (T1.Left Side).
- `/drawings` + `/drawings.dxf`: 3 wall runs, valid DXF with all layers.
- `/visualization`: 9-line derived Persian prompt, 27 cabinets, 5 appliances.
- `/dashboard/stats`: recent designs carry `total_retail` (161M / 122M).
- `/quote.html`: RTL HTML, `text/html` + inline disposition, derived totals embedded.
- **Edit persistence**: PUT width 800→1400 persists (GET confirms), cost rises 161.4M→164.3M.

## Known bugs
- None open (edit-persistence bug fixed).

## Next exact task
**Native PDF BOM/quote export** (if a lightweight dependency is acceptable) — quote.html already covers browser print-to-PDF. Otherwise, verify dark mode on all pages and continue with remaining UX polish (e.g. loading skeletons / optimistic UI).

Backend: uvicorn on :8000 (term_1787589449347_33). Frontend: next dev on :3000 (term_1786433647281_11). All new work uncommitted.
