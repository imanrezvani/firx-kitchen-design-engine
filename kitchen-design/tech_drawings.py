# Technical drawings — 2D dimensioned architectural drawings (black & white)
import math
from kitchen_render import SVG

ROOM_X, ROOM_Y, ROOM_Z = 4200, 3600, 2700
TOE = 100
CH = 900          # counter height
CT = 950
UB = 1350         # upper bottom
UT = 2700

INK = '#111111'

def dim(svg, x1, y1, x2, y2, text, off=18, text_size=12, flip=False):
    """Horizontal or vertical dimension line."""
    svg.line(x1, y1, x2, y2, INK, 0.7)
    if y1 == y2:
        svg.line(x1, y1 - 4, x1, y1 + 4, INK, 0.7)
        svg.line(x2, y2 - 4, x2, y2 + 4, INK, 0.7)
        svg.line(x1, y1, x1 - 7, y1 - 5, INK, 0.7)
        svg.line(x2, y2, x2 + 7, y2 - 5, INK, 0.7)
        svg.text((x1 + x2)/2, y1 - 6, text, text_size, INK, 'middle')
    else:
        svg.line(x1 - 4, y1, x1 + 4, y1, INK, 0.7)
        svg.line(x2 - 4, y2, x2 + 4, y2, INK, 0.7)
        svg.line(x1, y1, x1 - 5, y1 - 7, INK, 0.7)
        svg.line(x2, y2, x2 + 5, y2 + 7, INK, 0.7)
        svg.text(x1 - 6, (y1 + y2)/2 + 4, text, text_size, INK, 'middle')

def title_block(svg, W, H, title, subtitle, scale, sheet):
    svg.rect(W - 290, H - 60, 260, 34, 'white', INK, 1)
    svg.text(W - 275, H - 40, title, 14, INK, 'start', 'bold')
    svg.text(W - 275, H - 26, subtitle, 10, INK, 'start')
    svg.text(W - 60, H - 40, f'SCALE 1:{scale}', 10, INK, 'end')
    svg.text(W - 60, H - 26, f'SHEET {sheet}', 10, INK, 'end')

# ----------------------------------------------------------------------------
# FLOOR PLAN — Concept A
# ----------------------------------------------------------------------------
def floor_plan():
    s = 0.155   # px/mm
    W, H = 1150, 950
    svg = SVG(W, H, bg='white')
    ox, oy = 210, 660      # plan origin on canvas (room corner)
    def P(x, y):
        return (ox + x * s, oy - (ROOM_Y - y) * s)
    def PX(x): return ox + x * s
    def PY(y): return oy - (ROOM_Y - y) * s

    def wall(p0, p1, t=9):
        x0, y0 = p0; x1, y1 = p1
        svg.line(x0, y0, x1, y1, INK, 2.4)

    # room walls (thick) with a window gap on the west, door gap on south
    # north wall
    wall(P(0, 0), P(ROOM_X, 0))
    # south wall with door opening x 3300..4200
    wall(P(0, ROOM_Y), P(3300, ROOM_Y))
    wall(P(4200, ROOM_Y), P(4200, ROOM_Y))
    # west wall with window opening y 900..2400
    wall(P(0, 0), P(0, 900))
    wall(P(0, 2400), P(0, ROOM_Y))
    # east wall
    wall(P(ROOM_X, 0), P(ROOM_X, ROOM_Y))
    # window symbol on west wall
    x0, x1, y0, y1 = PX(0), PX(0), PY(900), PY(2400)
    svg.rect(x0 - 6, min(y0, y1), 12, abs(y1 - y0), 'white', INK, 0.8)
    svg.line(x0, y0, x0, y1, INK, 0.8)
    svg.line(x0 - 4, (y0+y1)/2, x0 + 4, (y0+y1)/2, INK, 0.8)
    svg.text(x0 - 26, (y0+y1)/2 + 4, 'WIN-1', 10, INK, 'middle')
    # door symbol on south wall
    dx0, dy0 = PX(3300), PY(3600)
    dx1, dy1 = PX(4200), PY(3600)
    svg.line(dx0, dy0, dx1, dy1, INK, 2.0)
    # swing arc
    r = 900 * s
    svg.path(f'M {dx1} {dy0} A {r} {r} 0 0 1 {dx1 - r} {dy0 - r}', INK, 0.6)
    svg.line(dx1, dy0, dx1 - r, dy0 - r, INK, 0.6)
    svg.text((dx0+dx1)/2, dy0 + 16, 'ENTRANCE 900', 10, INK, 'middle')

    def cab(x0, y0, x1, y1, code, hatch=False):
        ax, ay = PX(x0), PY(y0)
        bx, by = PX(x1), PY(y1)
        svg.rect(ax, min(ay, by), bx - ax, abs(by - ay), 'white', INK, 1.1)
        svg.text((ax+bx)/2, (ay+by)/2 + 4, code, 11, INK, 'middle', 'bold')
        if hatch:
            import random
            random.seed(7)
            for i in range(int(abs(by-ay)/9)):
                yy = min(ay, by) + 5 + i * 9
                svg.line(ax + 3, yy, bx - 3, yy, INK, 0.4)

    # WEST run (window wall) — y 600..3600
    wmods = [('B1', 600, 600, 1200, False), ('B2', 600, 1200, 2100, False),
             ('B3', 600, 2100, 2700, False), ('B4', 600, 2700, 3300, False),
             ('B5', 300, 3300, 3600, False)]
    for code, w, y0, y1, h in wmods:
        cab(0, y0, w, y1, code, h)
    # NORTH run — x 600..3300
    nmods = [('A1', 300, 600, 900), ('A2', 600, 900, 1500), ('A3', 600, 1500, 2100),
             ('A4', 600, 2100, 2700), ('A5', 600, 2700, 3300)]
    for code, w, x0, x1 in nmods:
        cab(x0, 0, x1, 600, code, hatch=(code in ('A4', 'A5')))
    # countertop outline (620 deep) — dashed
    def counter(x0, y0, x1, y1):
        ax, ay = PX(x0), PY(y0)
        bx, by = PX(x1), PY(y1)
        svg.rect(ax, min(ay, by), bx - ax, abs(by - ay), 'none', INK, 0.5, )
        svg.rect(ax, min(ay, by), bx - ax, abs(by - ay), 'none', INK, 0.5, )
    # west counter depth 0..620
    svg.rect(PX(0), PY(3600), PX(620)-PX(0), PY(600)-PY(3600), 'none', INK, 0.5)
    # north counter depth 0..620
    svg.rect(PX(600), PY(0), PX(3300)-PX(600), PY(620)-PY(0), 'none', INK, 0.5)

    # appliance symbols
    # sink on B2 (west run, y 1200..2100)
    sx, sy = PX(300), PY(1650)
    svg.circle(sx, sy, 150*s, 'white', INK, 1.0)
    svg.circle(sx, sy, 60*s, 'white', INK, 0.6)
    # hob on A2 (north run, x 900..1500)
    hxc, hyc = PX(1200), PY(300)
    svg.rect(hxc-240, hyc-210, 480, 420, 'white', INK, 1.0)
    for dx in (-120, 120):
        for dy in (-90, 90):
            svg.circle(hxc+dx, hyc+dy, 55*s, 'white', INK, 0.7)
    # fridge door swing on A4
    svg.text(PX(2400), PY(300), 'FRIDGE', 9, INK, 'middle')
    # DW on B3
    svg.text(PX(300), PY(2400), 'DW', 9, INK, 'middle')
    # oven on A2
    svg.text(PX(1200), PY(520), 'OVEN', 9, INK, 'middle')
    # hood on upper run (x900..1500) shown dashed
    svg.rect(PX(900), PY(100), PX(1500)-PX(900), PY(0)-PY(100), 'none', INK, 0.5, )

    # work triangle
    tri = [(PX(300), PY(1650)), (PX(1200), PY(300)), (PX(2400), PY(300))]
    for i in range(3):
        a, b = tri[i], tri[(i+1) % 3]
        svg.line(a[0], a[1], b[0], b[1], '#333333', 1.2, dash='6 4')
    svg.circle(*tri[0], 3.5, INK, None, 0)
    svg.circle(*tri[1], 3.5, INK, None, 0)
    svg.circle(*tri[2], 3.5, INK, None, 0)
    svg.text(tri[0][0] - 10, tri[0][1] - 10, 'S', 11, INK, 'end', 'bold')
    svg.text(tri[1][0] - 8, tri[1][1] + 20, 'H', 11, INK, 'end', 'bold')
    svg.text(tri[2][0] + 8, tri[2][1] + 20, 'F', 11, INK, 'start', 'bold')

    # dimension lines
    dim(svg, PX(0), PY(ROOM_Y) - 130, PX(ROOM_X), PY(ROOM_Y) - 130, '4200')
    dim(svg, PX(0), PY(ROOM_Y) + 40, PX(600), PY(ROOM_Y) + 40, '600')
    dim(svg, PX(ROOM_X) + 40, PY(0), PX(ROOM_X) + 40, PY(ROOM_Y), '3600')
    dim(svg, PX(3300) + 40, PY(ROOM_Y), PX(4200) + 40, PY(ROOM_Y), '900')
    dim(svg, PX(600), PY(ROOM_Y) + 40, PX(2100), PY(ROOM_Y) + 40, '1500')
    dim(svg, PX(2100), PY(ROOM_Y) + 40, PX(3300), PY(ROOM_Y) + 40, '1200')

    # north arrow
    nx, ny = PX(4300), PY(ROOM_Y - 200)
    svg.text(nx, ny + 20, 'N', 14, INK, 'middle', 'bold')
    svg.path(f'M {nx} {ny} l -8 -20 l 8 8 l 8 -8 Z', INK, 1, 'none')
    svg.path(f'M {nx} {ny} l -8 -20 l 8 8 l 8 -8 Z', INK, 0, INK)

    # legend
    lx, ly = 30, 40
    svg.text(lx, ly, 'CABINET LEGEND', 12, INK, 'start', 'bold')
    legend = [
        ('A1', 'Corner blind base 300'), ('A2', 'Oven base 600 + drawer'),
        ('A3', 'Drawer base 600'), ('A4', 'Tall fridge column 600'),
        ('A5', 'Tall pantry column 600'), ('B1/B4', 'Drawer base 600'),
        ('B2', 'Sink base 900'), ('B3', 'Dishwasher base 600'),
        ('B5', 'Filler 300'), ('S1/S3', 'Wall cabinet 600 (to ceiling)'),
        ('W1', 'Wall cabinet 600 (to ceiling)'),
    ]
    for i, (c, d) in enumerate(legend):
        svg.text(lx, ly + 20 + i * 17, c, 10, INK, 'start', 'bold')
        svg.text(lx + 70, ly + 20 + i * 17, d, 10, INK, 'start')

    title_block(svg, W, H, 'CONCEPT A - FLOOR PLAN', 'L-Shaped Kitchen 4200 x 3600 mm', 50, 'T-01')
    return svg

# ----------------------------------------------------------------------------
# FRONT ELEVATION — North run (cooking wall), view from south
# ----------------------------------------------------------------------------
def elev_north():
    s = 0.34
    W, H = 1150, 980
    svg = SVG(W, H, bg='white')
    ox, oy = 180, 850   # baseline origin
    def X(x): return ox + x * s
    def Y(y): return oy - y * s
    # ground line
    svg.line(ox - 30, oy, X(3600), oy, INK, 1.6)

    # backsplash band
    svg.rect(X(600), Y(UB), X(3300)-X(600), UB - CH, 'none', INK, 0.6, )

    # lower run 600..3300
    svg.rect(X(600), Y(CH), X(3300)-X(600), CH - TOE, 'white', INK, 1.1)
    # toe kick
    svg.rect(X(600), Y(TOE), X(3300)-X(600), TOE, 'white', INK, 0.8)
    # A1 corner 300
    svg.text(X(750), Y(500), 'A1', 10, INK, 'middle')
    svg.line(X(900), Y(TOE), X(900), Y(CH), INK, 0.6)
    # A2 oven 600 with oven + drawer
    svg.rect(X(920), Y(490), X(1480)-X(920), 360, 'white', INK, 0.8)   # oven
    svg.line(X(920), Y(500), X(1480), Y(500), INK, 1.4)
    svg.text(X(1200), Y(400), 'OVEN', 9, INK, 'middle')
    svg.line(X(900), Y(600), X(1500), Y(600), INK, 0.5)  # drawer seam
    svg.text(X(1200), Y(750), 'DRAWER', 8, INK, 'middle')
    svg.line(X(1500), Y(TOE), X(1500), Y(CH), INK, 0.6)
    # A3 drawer 600 with drawer seams + handles
    svg.text(X(1800), Y(500), 'A3', 10, INK, 'middle')
    for yy in (430, 620, 810):
        svg.line(X(1500), Y(yy), X(2100), Y(yy), INK, 0.5)
    for hy in (265, 520, 715):
        svg.line(X(1600), Y(hy), X(2000), Y(hy), INK, 1.0)
    svg.line(X(2100), Y(TOE), X(2100), Y(CH), INK, 0.6)
    # A4 fridge tall
    svg.rect(X(2100), Y(UT), X(2700)-X(2100), UT - TOE, 'white', INK, 1.1)
    svg.line(X(2400), Y(1870), X(2400), Y(UT), INK, 0.6)
    svg.line(X(2100), Y(1870), X(2700), Y(1870), INK, 0.6)
    svg.line(X(2250), Y(1400), X(2250), Y(1400), INK, 1.0)
    svg.line(X(2220), Y(300), X(2280), Y(300), INK, 0.8)
    svg.line(X(2220), Y(1600), X(2280), Y(1600), INK, 0.8)
    svg.text(X(2400), Y(1200), 'FRIDGE', 9, INK, 'middle')
    svg.text(X(2400), Y(2300), 'STORAGE', 8, INK, 'middle')
    svg.line(X(2700), Y(TOE), X(2700), Y(UT), INK, 0.6)
    # A5 pantry tall
    svg.rect(X(2700), Y(UT), X(3300)-X(2700), UT - TOE, 'white', INK, 1.1)
    svg.text(X(3000), Y(1600), 'A5', 10, INK, 'middle')
    svg.line(X(3000), Y(300), X(3000), Y(2400), INK, 0.8)
    svg.line(X(3300), Y(TOE), X(3300), Y(CH), INK, 0.6)
    # uppers S1, hood, S3
    svg.rect(X(600), Y(UB), X(900)-X(600), UT - UB, 'white', INK, 1.0)
    svg.text(X(750), Y(2100), 'S1', 9, INK, 'middle')
    svg.line(X(750), Y(1500), X(750), Y(2500), INK, 0.5)
    # hood 600
    svg.path(f'M {X(920)} {Y(UB)} l 0 140 l 560 0 l 0 -140 Z', INK, 1.0, 'none')
    svg.line(X(1000), Y(UB+140), X(1400), Y(UB+140), INK, 0.6)
    svg.text(X(1200), Y(UB+90), 'HOOD', 8, INK, 'middle')
    # S3
    svg.rect(X(1500), Y(UB), X(2100)-X(1500), UT - UB, 'white', INK, 1.0)
    svg.text(X(1800), Y(2100), 'S3', 9, INK, 'middle')
    svg.line(X(1800), Y(1500), X(1800), Y(2500), INK, 0.5)

    # heights
    svg.line(X(600) - 20, Y(0), X(600) - 20, Y(UT), INK, 0.4)
    dim(svg, X(600)-20, Y(TOE), X(600)-20, Y(CH), '900', off=18, flip=True)
    dim(svg, X(600)-20, Y(UB), X(600)-20, Y(UT), '1350', off=18, flip=True)
    dim(svg, X(600)-20, Y(CH), X(600)-20, Y(UB), '450', off=18, flip=True)
    # widths
    dim(svg, X(600), Y(TOE) - 30, X(900), Y(TOE) - 30, '300')
    dim(svg, X(900), Y(TOE) - 30, X(1500), Y(TOE) - 30, '600')
    dim(svg, X(1500), Y(TOE) - 30, X(2100), Y(TOE) - 30, '600')
    dim(svg, X(2100), Y(TOE) - 30, X(2700), Y(TOE) - 30, '600')
    dim(svg, X(2700), Y(TOE) - 30, X(3300), Y(TOE) - 30, '600')
    dim(svg, X(600), Y(TOE) - 60, X(3300), Y(TOE) - 60, '2700 TOTAL FRONTAGE')

    title_block(svg, W, H, 'CONCEPT A - FRONT ELEVATION (NORTH RUN)', 'Cooking wall: corner + oven + drawer + tall fridge + tall pantry', 50, 'T-02')
    return svg

# ----------------------------------------------------------------------------
# FRONT ELEVATION — West run (window/sink wall), view from east
# ----------------------------------------------------------------------------
def elev_west():
    s = 0.30
    W, H = 1250, 900
    svg = SVG(W, H, bg='white')
    ox, oy = 150, 800
    def X(x): return ox + x * s
    def Y(y): return oy - y * s
    svg.line(ox - 30, oy, X(3700), oy, INK, 1.6)
    # wall
    svg.rect(X(600), Y(UB), X(3600)-X(600), UT - UB, 'white', INK, 0.5)

    # lower run 600..3600
    svg.rect(X(600), Y(CH), X(3600)-X(600), CH - TOE, 'white', INK, 1.1)
    svg.rect(X(600), Y(TOE), X(3600)-X(600), TOE, 'white', INK, 0.8)
    # B1 drawer
    svg.text(X(900), Y(500), 'B1', 10, INK, 'middle')
    for yy in (430, 620, 810):
        svg.line(X(600), Y(yy), X(1200), Y(yy), INK, 0.5)
    for hy in (265, 520, 715):
        svg.line(X(700), Y(hy), X(1100), Y(hy), INK, 1.0)
    # B2 sink 900
    svg.rect(X(1200), Y(CH), X(2100)-X(1200), CH - TOE, 'white', INK, 1.0)
    svg.line(X(1650), Y(CH), X(1650), Y(TOE), INK, 0.6)
    svg.rect(X(1400), Y(300), X(1900)-X(1400), 260, 'white', INK, 0.8)  # sink bowl
    svg.path(f'M {X(1850)} {Y(700)} l 0 60 l -40 0 l 0 -60 Z', INK, 0.8, 'none')  # faucet
    svg.line(X(1750), Y(760), X(1900), Y(760), INK, 0.8)
    svg.text(X(1650), Y(500), 'SINK', 9, INK, 'middle')
    # B3 DW
    svg.text(X(2400), Y(500), 'B3 DW', 10, INK, 'middle')
    svg.line(X(2100), Y(TOE), X(2700), Y(TOE), INK, 0.6)
    svg.line(X(2400), Y(300), X(2400), Y(700), INK, 0.6)
    svg.line(X(2400), Y(200), X(2400), Y(200), INK, 1.0)
    # B4 drawer
    svg.text(X(3000), Y(500), 'B4', 10, INK, 'middle')
    for yy in (430, 620, 810):
        svg.line(X(2700), Y(yy), X(3300), Y(yy), INK, 0.5)
    for hy in (265, 520, 715):
        svg.line(X(2800), Y(hy), X(3200), Y(hy), INK, 1.0)
    # B5 filler
    svg.text(X(3450), Y(500), 'B5', 10, INK, 'middle')
    svg.line(X(3300), Y(TOE), X(3300), Y(CH), INK, 0.6)

    # window on wall y900..2400
    wx0, wx1 = X(900), X(2400)
    svg.rect(wx0, Y(2400), wx1-wx0, 1500, 'white', INK, 1.0)
    svg.line(wx0, Y(1650), wx1, Y(1650), INK, 0.6)
    svg.line((wx0+wx1)/2, Y(2400), (wx0+wx1)/2, Y(900), INK, 0.6)
    svg.text((wx0+wx1)/2, Y(2000), 'WINDOW 1500 x 1500', 9, INK, 'middle')
    # over-window cabinet
    svg.rect(wx0, Y(UT), wx1-wx0, UT-2400, 'white', INK, 1.0)
    svg.line((wx0+wx1)/2, Y(2400), (wx0+wx1)/2, Y(UT), INK, 0.6)
    svg.text((wx0+wx1)/2, Y(2620), 'OVER-WINDOW CABINET', 8, INK, 'middle')
    # W1 wall cabinet
    svg.rect(X(2700), Y(UB), X(3300)-X(2700), UT-UB, 'white', INK, 1.0)
    svg.text(X(3000), Y(2100), 'W1', 9, INK, 'middle')
    svg.line(X(3000), Y(1500), X(3000), Y(2500), INK, 0.5)

    dim(svg, X(600), Y(TOE) - 26, X(1200), Y(TOE) - 26, '600')
    dim(svg, X(1200), Y(TOE) - 26, X(2100), Y(TOE) - 26, '900')
    dim(svg, X(2100), Y(TOE) - 26, X(2700), Y(TOE) - 26, '600')
    dim(svg, X(2700), Y(TOE) - 26, X(3300), Y(TOE) - 26, '600')
    dim(svg, X(3300), Y(TOE) - 26, X(3600), Y(TOE) - 26, '300')
    dim(svg, X(600), Y(TOE) - 54, X(3600), Y(TOE) - 54, '3000 TOTAL FRONTAGE')
    svg.line(X(3600)-20, Y(0), X(3600)-20, Y(UT), INK, 0.4)
    dim(svg, X(3600)-20, Y(TOE), X(3600)-20, Y(CH), '900', flip=True)
    dim(svg, X(3600)-20, Y(CH), X(3600)-20, Y(UB), '450', flip=True)

    title_block(svg, W, H, 'CONCEPT A - FRONT ELEVATION (WEST RUN)', 'Window and sink wall: drawer + sink + dishwasher + drawer + filler', 50, 'T-03')
    return svg

# ----------------------------------------------------------------------------
# CROSS SECTION — through north run (view toward east)
# ----------------------------------------------------------------------------
def section():
    s = 0.30
    W, H = 1150, 820
    svg = SVG(W, H, bg='white')
    ox, oy = 260, 660
    def X(x): return ox + x * s
    def Y(y): return oy - y * s
    # wall (at back, depth 0)
    svg.rect(X(-40), Y(UT), X(40), UT, 'white', INK, 1.4)
    svg.text(X(0), Y(2650), 'WALL', 8, INK, 'middle')
    # toe kick
    svg.rect(X(60), Y(TOE), X(600)-X(60), TOE, 'white', INK, 1.0)
    svg.text(X(300), Y(50), 'TOE KICK 100', 8, INK, 'middle')
    # lower carcass
    svg.rect(X(0), Y(CH), X(600)-X(0), CH - TOE, 'white', INK, 1.0)
    # countertop
    svg.rect(X(-30), Y(CT), X(620)-X(-30), CT - CH, 'none', INK, 1.2)
    svg.line(X(-30), Y(CT), X(620), Y(CT), INK, 1.2)
    svg.text(X(700), Y(925), 'COUNTERTOP 620 (40 THICK)', 8, INK, 'middle')
    # backsplash
    svg.line(X(0), Y(UB), X(0), Y(CH), INK, 0.6)
    svg.text(X(0), Y(1150), 'BACKSPLASH 450', 8, INK, 'middle', )
    # upper cabinet
    svg.rect(X(0), Y(UB), X(350)-X(0), UT - UB, 'white', INK, 1.0)
    svg.line(X(20), Y(1500), X(20), Y(2600), INK, 0.5)
    svg.text(X(175), Y(2100), 'UPPER CABINET 350 DEEP', 8, INK, 'middle')
    # tall column (fridge) full depth
    svg.rect(X(600), Y(UT), X(700)-X(600), UT - TOE, 'white', INK, 0.8)
    svg.text(X(650), Y(1400), 'TALL', 8, INK, 'middle')
    # ceiling
    svg.line(X(-60), Y(UT), X(800), Y(UT), INK, 1.0)
    svg.text(X(780), Y(2650), 'CEILING 2700', 8, INK, 'end')
    # dims
    dim(svg, X(-60), Y(0), X(620), Y(0), '620', flip=False)
    dim(svg, X(0), Y(0), X(600), Y(0) - 26, '600')
    dim(svg, X(620), Y(0), X(620) + 60, Y(0), '50', flip=True)
    svg.line(X(620), Y(CT), X(700), Y(CT), INK, 0.4)
    dim(svg, X(700), Y(CT), X(700), Y(0), '950', flip=True)
    dim(svg, X(60), Y(TOE), X(60), Y(CH), '800', flip=True)

    title_block(svg, W, H, 'CONCEPT A - CROSS SECTION', 'Through cooking run, view toward east', 20, 'T-04')
    return svg
