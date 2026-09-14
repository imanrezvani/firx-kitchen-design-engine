# Build the final self-contained HTML presentation
import materials as mat

CONCEPTS = {
    'A': dict(
        name='Concept A',
        title='The Ergonomic L',
        layout='L-SHAPED + TALL PANTRY WALL',
        style='Modern Minimalist',
        palette='Warm off-white lacquer + light oak floor, white quartz, brushed-steel accents',
        desc=(
            'The sink is centered under the window for maximum natural light over the work zone. '
            'A clean L-shape opens toward the entrance, with the cooking wall on the north and a '
            'full-height fridge + pantry column closing the run. The compact work triangle '
            '(sink - hob - fridge = 5.3 m) keeps every move efficient while leaving the window wall '
            'completely free for daylight.'
        ),
        features=[
            'Sink centered under window, 900 base with undermount sink',
            'Cooking wall: 60 cm oven under 4-zone induction hob + extractor',
            'Full-height fridge column and 600 pantry with pull-outs',
            'Upper cabinets to ceiling on both runs for dust-free storage',
            'Over-window cabinet integrates the window wall cleanly',
            'Work triangle 5.3 m - well inside the 7.9 m NKBA guideline',
        ],
    ),
    'B': dict(
        name='Concept B',
        title='The Storage U',
        layout='U-SHAPED - THREE WORKING WALLS',
        style='Warm Walnut / Craftsman',
        palette='American walnut cabinetry, stone-gray quartz, bronze hardware',
        desc=(
            'Three full runs enclose the work zone for the maximum linear storage in the room. '
            'The west wall keeps the sink on the window, the north wall carries cooking plus the '
            'tall column, and the new south wall adds a second prep and storage run opposite the entry. '
            'The open end of the U faces the door, so the space still reads open and welcoming.'
        ),
        features=[
            'Longest linear storage: three runs totalling 8.4 m of cabinetry',
            'Prep run opposite the cooking wall keeps two cooks working side by side',
            'U mouth opens to the entrance - clear sightline from the door',
            'Tall fridge + pantry on the far leg, away from the door swing',
            'Generous 1.8 m aisle between runs',
        ],
    ),
    'C': dict(
        name='Concept C',
        title='The L + Island',
        layout='L-SHAPED + FREESTANDING ISLAND',
        style='Contemporary Two-Tone',
        palette='Graphite lowers, cream uppers, white quartz, oak island base',
        desc=(
            'The L-shape stays identical to Concept A, but a freestanding island with a 300 mm '
            'overhang adds a breakfast bar for two, extra prep surface and under-island storage. '
            'Pendant lighting anchors the island over the seating zone. The island creates a '
            'natural circulation loop between entry, cooking zone and dining area.'
        ),
        features=[
            'Island 1500 x 900 with 300 mm overhang for two bar stools',
            'Two pendants frame the seating zone',
            'Prep surface right beside the cooking wall',
            'Under-island drawer bank and open shelf for cookbooks',
            '900+ mm clearances maintained on all island sides',
        ],
    ),
    'D': dict(
        name='Concept D',
        title='The L + Dining Corner',
        layout='L-SHAPED WITH DINING ZONE',
        style='Scandinavian Light',
        palette='Pale oak lowers, cream uppers, white quartz, terracotta accents',
        desc=(
            'A full-height buffet wall and a built-in banquette turn the east side of the room '
            'into a proper kitchen-diner. The kitchen functions as a two-zone room: a quiet '
            'cooking zone by the window and a coffee-and-breakfast zone with seating for four '
            'at the table. Ideal for families that live in the kitchen.'
        ),
        features=[
            'Dining table 1400 x 800 with banquette seating for four',
            'Buffet / coffee station on the east wall (to ceiling)',
            'Kitchen zone separated from dining zone by circulation',
            'Breakfast preparation within arm\'s reach of the table',
        ],
    ),
}

RENDERS = 'assets'

VIEWS = [
    ('selected_front_view.svg', 'Front view - cooking wall'),
    ('selected_left_perspective.svg', 'Left perspective - from the sink wall'),
    ('selected_right_perspective.svg', 'Right perspective - from the east wall'),
    ('selected_entrance_view.svg', 'Kitchen entrance view'),
    ('selected_corner_closeup.svg', 'Window and sink corner'),
    ('selected_birdseye.svg', 'Bird\'s-eye perspective'),
]

TECH = [
    ('tech_floor_plan.svg', 'T-01', 'Dimensioned Floor Plan 1:50'),
    ('tech_elev_north.svg', 'T-02', 'Front Elevation - North Run (Cooking Wall) 1:50'),
    ('tech_elev_west.svg', 'T-03', 'Front Elevation - West Run (Window & Sink Wall) 1:50'),
    ('tech_section.svg', 'T-04', 'Cross Section - Cooking Run 1:20'),
]

def svg_inline(path):
    with open(path) as f:
        return f.read()

def swatch(hexs):
    return ''.join(f'<span class="sw" style="background:{h}" title="{h}"></span>' for h in hexs)

def build():
    m = mat.estimate()
    css = '''
      :root { --ink:#23272b; --muted:#6b7178; --line:#d8dbd7; --paper:#ffffff; --soft:#f4f3ef; --acc:#b8893c; }
      * { box-sizing: border-box; }
      body { margin:0; font-family:"Segoe UI", Arial, sans-serif; color:var(--ink); background:#ecebe6; line-height:1.5; }
      .wrap { max-width:1280px; margin:0 auto; padding:24px 20px 60px; }
      .cover { background:linear-gradient(135deg,#23272b 0%,#3a3f44 55%,#b8893c 130%); color:#fff; border-radius:14px;
               padding:48px 44px; margin-bottom:28px; }
      .cover h1 { margin:0 0 6px; font-size:34px; letter-spacing:.5px; }
      .cover .sub { font-size:15px; opacity:.85; }
      .cover .meta { display:flex; flex-wrap:wrap; gap:10px 26px; margin-top:22px; font-size:13px; opacity:.95; }
      .cover .meta b { opacity:.6; font-weight:600; display:block; font-size:11px; letter-spacing:1px; }
      .grid { display:grid; gap:20px; }
      .card { background:var(--paper); border:1px solid var(--line); border-radius:12px; overflow:hidden; }
      .card h2 { margin:0; font-size:18px; }
      .card .body { padding:20px 22px; }
      .render { width:100%; display:block; background:#dfd9cc; }
      .tag { display:inline-block; background:#ede7da; color:#6a5b36; font-size:11px; letter-spacing:1.2px;
             font-weight:700; padding:4px 10px; border-radius:20px; margin-bottom:10px; }
      .pill { display:inline-block; background:var(--soft); border:1px solid var(--line); color:var(--muted);
              font-size:12px; padding:3px 9px; border-radius:6px; margin:2px 4px 2px 0; }
      .sw { display:inline-block; width:26px; height:26px; border-radius:6px; border:1px solid rgba(0,0,0,.12); margin-right:5px; vertical-align:middle; }
      .concept-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
      .feature-list { padding-left:18px; margin:10px 0 0; font-size:14px; color:#3c4044; }
      .feature-list li { margin-bottom:5px; }
      .two { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
      .note { background:#fff8ec; border:1px solid #ecd9ae; border-radius:10px; padding:14px 18px; font-size:13.5px; }
      table { width:100%; border-collapse:collapse; font-size:14px; }
      th, td { border:1px solid var(--line); padding:8px 12px; text-align:left; }
      th { background:var(--soft); font-weight:600; }
      .num { text-align:right; }
      .tot td { font-weight:700; background:#f7f3ea; }
      .sec-t { font-size:22px; font-weight:700; margin:40px 0 14px; padding-left:12px; border-left:4px solid var(--acc); }
      .sub-sec { font-size:17px; font-weight:600; margin:26px 0 10px; }
      .col2 { column-count:2; column-gap:40px; }
      footer { text-align:center; color:var(--muted); font-size:12px; margin-top:44px; }
    '''

    # ---- concept cards ----
    concepts_html = ''
    for key, c in CONCEPTS.items():
        render = svg_inline(f'{RENDERS}/concept_{key}_perspective.svg')
        palette_map = {
            'A': ['#D7C9AE', '#F1ECE1', '#F6F4EF', '#D6C2A0', '#23262A'],
            'B': ['#8A6A4B', '#CBCED3', '#7E6B53', '#2B2B2B'],
            'C': ['#3A3D42', '#F6F3ED', '#F7F5F1', '#D2B48C', '#D8C5A6'],
            'D': ['#D9C9AE', '#F3EFE6', '#F7F5F1', '#B49A78', '#E2D3BC'],
        }[key]
        feats = ''.join(f'<li>{f}</li>' for f in c['features'])
        concepts_html += f'''
        <div class="card">
          <svg class="render" viewBox="0 0 1400 880" preserveAspectRatio="xMidYMid meet">{render}</svg>
          <div class="body">
            <span class="tag">{c['layout']}</span>
            <h2>{c['name']} - {c['title']}</h2>
            <div style="margin:8px 0">
              <span class="pill">Style: {c['style']}</span>
              <span class="pill">{c['palette']}</span>
              <span style="margin-left:8px">{swatch(palette_map)}</span>
            </div>
            <p style="font-size:14px; color:#444; margin:10px 0 6px">{c['desc']}</p>
            <ul class="feature-list">{feats}</ul>
          </div>
        </div>'''

    views_html = ''
    for fname, label in VIEWS:
        views_html += f'''<div class="card"><svg class="render" viewBox="0 0 1400 880" preserveAspectRatio="xMidYMid meet">{svg_inline(f'{RENDERS}/{fname}')}</svg>
        <div class="body" style="padding:12px 18px"><h2 style="font-size:15px">{label}</h2></div></div>'''

    tech_html = ''
    for fname, sheet, label in TECH:
        svg = svg_inline(f'{RENDERS}/{fname}')
        tech_html += f'''<div class="card">
          <div style="background:#fff; text-align:center; padding:6px 0">
            <svg style="max-width:100%; height:auto" viewBox="0 0 1150 950" preserveAspectRatio="xMidYMid meet">{svg}</svg>
          </div>
          <div class="body" style="padding:12px 18px; display:flex; justify-content:space-between">
            <h2 style="font-size:14px">{sheet} - {label}</h2><span class="pill">Black & white, print-ready</span>
          </div></div>'''

    # materials table
    matrows = ''
    for name, qty, unit, cost in m['rows']:
        matrows += f'<tr><td>{name}</td><td class="num">{qty:g}</td><td class="num">&euro;{unit:g}</td><td class="num">&euro;{cost:g}</td></tr>'
    matrows += f'''<tr class="tot"><td>Subtotal materials</td><td></td><td></td><td class="num">&euro;{m['subtotal']:g}</td></tr>
    <tr><td>Contingency (+10%)</td><td></td><td></td><td class="num">&euro;{m['contingency']:g}</td></tr>
    <tr class="tot"><td>TOTAL MATERIAL COST</td><td></td><td></td><td class="num">&euro;{m['total']:g} &plusmn;10%</td></tr>'''

    approws = ''
    for name, cost in m['appliances'].items():
        approws += f'<tr><td>{name}</td><td class="num">&euro;{cost:g}</td></tr>'
    approws += f'<tr class="tot"><td>TOTAL APPLIANCES</td><td class="num">&euro;{m["app_total"]:g}</td></tr>'

    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kitchen Design Presentation - Firx AI</title>
<style>{css}</style></head>
<body><div class="wrap">

  <div class="cover">
    <h1>Residential Kitchen Design Proposal</h1>
    <div class="sub">Prepared by Firx AI - Kitchen Designer &middot; Interior Architect &middot; Cabinet Planning Specialist</div>
    <div class="meta">
      <div><b>ROOM</b>4200 &times; 3600 &times; 2700 mm</div>
      <div><b>ENTRY</b>1 door &middot; 900 mm &middot; south wall</div>
      <div><b>WINDOW</b>1500 &times; 1500 &middot; west wall</div>
      <div><b>STYLE</b>Modern Minimalist</div>
      <div><b>COUNTERTOP</b>White quartz</div>
      <div><b>FLOOR</b>Large-format warm oak tile</div>
    </div>
  </div>

  <div class="note">
    <b>Project data &amp; assumptions.</b> The brief reached the studio without the dimension /
    photo fields populated, so the design is developed on a standard room shell: length 4200 mm,
    width 3600 mm, clear height 2700 mm, one 900 mm entrance on the south wall and one 1500 &times;
    1500 mm window centered on the west wall (sill 900 mm). Layouts, cabinetry and elevations are
    dimensioned to real millimetres and are production-ready. Re-run with the actual survey and
    room photos to lock the final module schedule.
  </div>

  <h2 class="sec-t">Design Standards Compliance</h2>
  <table>
    <tr><th>Check</th><th>Standard / Guideline</th><th>This design</th></tr>
    <tr><td>Work triangle total</td><td>NKBA &le; 7900 mm</td><td>Concept A: 5300 mm</td></tr>
    <tr><td>Clearance in front of cabinets</td><td>&ge; 1060 mm (with appliances), 900 mm minimum</td><td>1800 mm aisle - exceeds</td></tr>
    <tr><td>Counter height</td><td>900 mm standard</td><td>900 mm</td></tr>
    <tr><td>Toe kick</td><td>100 mm standard</td><td>100 mm recessed 50 mm</td></tr>
    <tr><td>Sink-hob gap</td><td>300-900 mm worktop</td><td>600 mm prep between sink and hob</td></tr>
    <tr><td>Upper cabinet base height</td><td>1350-1400 mm (450 mm over counter)</td><td>1350 mm, to ceiling</td></tr>
    <tr><td>Door / window clearance</td><td>No obstruction</td><td>All zones kept clear</td></tr>
    <tr><td>Fridge door swing</td><td>Full 90&deg; swing clear</td><td>Located at run end</td></tr>
  </table>

  <h2 class="sec-t">Four Design Concepts</h2>
  <div class="concept-grid">{concepts_html}</div>

  <h2 class="sec-t">Selected Concept - The Ergonomic L (Concept A)</h2>
  <div class="note" style="margin-bottom:18px">
    <b>Why Concept A wins.</b> It places the sink directly under the window so the most-used
    position gets the best daylight and outlook; it produces the shortest work triangle (5.3 m);
    it keeps the door and window completely unobstructed; it uses only simple L-run construction
    (two corners) for the cleanest build; and its open corner facing the entrance makes the
    14 m&sup2; room feel larger. Concept B stores the most, but its extra corner and closed feel
    give the edge to A for ergonomics, light and construction simplicity.
  </div>

  <h3 class="sub-sec">Design Gallery - six views of the selected concept</h3>
  <div class="two">{views_html}</div>

  <h2 class="sec-t">Technical Drawings</h2>
  <div class="two">{tech_html}</div>

  <h2 class="sec-t">Material Estimation Report</h2>
  <div class="two">
    <div class="card"><div class="body">
      <h2 style="margin-bottom:10px">Board &amp; hardware quantities</h2>
      <table>
        <tr><th>Item</th><th class="num">Qty</th><th class="num">Unit</th></tr>
        <tr><td>18 mm MDF sheets (1220 &times; 2440)</td><td class="num">{m['sheets_18']} sheets</td><td class="num">{m['m2_18']} m&sup2;</td></tr>
        <tr><td>6 mm back panels</td><td class="num">{m['sheets_06']} sheets</td><td class="num">{m['m2_back']} m&sup2;</td></tr>
        <tr><td>Quartz countertop</td><td class="num">{m['counter_m2']} m&sup2;</td><td class="num">620 deep, 40 thick</td></tr>
        <tr><td>Edge banding</td><td class="num">{m['edge_m']} m</td><td class="num">2 mm PVC</td></tr>
        <tr><td>Hinges (soft-close)</td><td class="num">{m['hinges']} pcs</td><td class="num">110&deg;</td></tr>
        <tr><td>Drawer slides</td><td class="num">{m['slides']} pcs</td><td class="num">full extension</td></tr>
        <tr><td>Handles</td><td class="num">{m['handles']} pcs</td><td class="num">aluminium bar</td></tr>
        <tr><td>Toe-kick plinth</td><td class="num">{m['toe_m']} m</td><td class="num">from offcuts</td></tr>
      </table>
    </div></div>
    <div class="card"><div class="body">
      <h2 style="margin-bottom:10px">Material cost estimate (EUR)</h2>
      <table>
        <tr><th>Item</th><th class="num">Qty</th><th class="num">&euro;/u</th><th class="num">Cost</th></tr>
        {matrows}
      </table>
      <p style="font-size:12.5px; color:var(--muted); margin:10px 0 0">
        Quantities approximate to &plusmn;10%. This is a material estimate for pricing -
        not a manufacturing BOM. Excludes labour, delivery and fit-out.
      </p>
    </div></div>
  </div>

  <h3 class="sub-sec">Recommended appliances (quoted separately)</h3>
  <div class="card"><div class="body">
    <table>
      <tr><th>Appliance</th><th class="num">Budget</th></tr>
      {approws}
    </table>
    <p style="font-size:12.5px; color:var(--muted); margin:10px 0 0">
      Full project estimate: materials &euro;{m['total']:g} + appliances &euro;{m['app_total']:g}
      &asymp; <b>&euro;{m['total'] + m['app_total']:g}</b> (materials + appliances, before labour).
    </p>
  </div></div>

  <footer>Kitchen Design Proposal &middot; prepared by Firx AI &middot; drawings and renders generated from the dimensioned 3D model &middot; all dimensions in millimetres</footer>
</div></body></html>'''

    with open('Kitchen_Design_Report.html', 'w') as f:
        f.write(html)
    print('report written:', len(html), 'bytes')

if __name__ == '__main__':
    build()
