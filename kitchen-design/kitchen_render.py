import math, json

SIN30 = math.sin(math.radians(30))
COS30 = math.cos(math.radians(30))

# ----------------------------------------------------------------------------
# Color utilities
# ----------------------------------------------------------------------------
def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb2hex(c):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(v)))) for v in c)

def shade(hexc, f):
    r, g, b = hex2rgb(hexc)
    return rgb2hex((r*f, g*f, b*f))

def light_dir():
    return norm((0.35, 0.25, 0.95))

def norm(v):
    m = math.sqrt(sum(a*a for a in v))
    return tuple(a/m for a in v)

def dot(a, b):
    return sum(x*y for x, y in zip(a, b))

# ----------------------------------------------------------------------------
# SVG document
# ----------------------------------------------------------------------------
class SVG:
    def __init__(self, w, h, bg='#ffffff'):
        self.w, self.h = w, h
        self.bg = bg
        self.elems = []
        self.defs = []

    def _poly(self, pts, fill, stroke=None, sw=0, op=1.0):
        if len(pts) < 3:
            return ''
        pstr = ' '.join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts)
        s = f'<polygon points="{pstr}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"'
        if op < 1.0:
            s += f' opacity="{op}"'
        return s + '/>'

    def poly(self, pts, fill, stroke=None, sw=0, op=1.0):
        self.elems.append(self._poly(pts, fill, stroke, sw, op))

    def line(self, x1, y1, x2, y2, stroke, sw=1, dash=None, op=1.0):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.elems.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}" opacity="{op}"{d}/>')

    def rect(self, x, y, w, h, fill, stroke=None, sw=0, op=1.0):
        s = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw}"'
        if op < 1.0:
            s += f' opacity="{op}"'
        self.elems.append(s + '/>')

    def circle(self, cx, cy, r, fill, stroke=None, sw=0, op=1.0):
        s = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw}"'
        if op < 1.0:
            s += f' opacity="{op}"'
        self.elems.append(s + '/>')

    def ellipse(self, cx, cy, rx, ry, fill, stroke=None, sw=0, op=1.0):
        s = f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw}"'
        if op < 1.0:
            s += f' opacity="{op}"'
        self.elems.append(s + '/>')

    def path(self, d, stroke, sw=1, fill='none', op=1.0, dash=None, cap='butt'):
        dd = f' stroke-dasharray="{dash}"' if dash else ''
        self.elems.append(f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" '
                          f'fill="{fill}" stroke-linecap="{cap}" opacity="{op}"{dd}/>')

    def text(self, x, y, s, size=12, fill='#111', anchor='start', weight='normal', transform=None, font='Arial, sans-serif'):
        tf = f' transform="{transform}"' if transform else ''
        self.elems.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" '
                          f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{tf}>{s}</text>')

    def grad_def(self, gid, stops, kind='linear', x1=0, y1=0, x2=1, y2=1):
        body = ''
        for off, col, op in stops:
            body += f'<stop offset="{off}" stop-color="{col}" stop-opacity="{op}"/>'
        self.defs.append(f'<{kind}Gradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{body}</{kind}Gradient>')

    def to_string(self):
        defs = f'<defs>{"".join(self.defs)}</defs>' if self.defs else ''
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">{defs}'
                f'<rect width="100%" height="100%" fill="{self.bg}"/>'
                + ''.join(self.elems) + '</svg>')

    def save(self, path):
        with open(path, 'w') as f:
            f.write(self.to_string())

# ----------------------------------------------------------------------------
# Projectors
# ----------------------------------------------------------------------------
class Iso:
    def __init__(self, scale=0.5):
        self.s = scale

    def project(self, p):
        x, y, z = p
        u = (x - y) * COS30 * self.s
        v = (x + y) * SIN30 * self.s - z * self.s
        return (u, v)

    def fit(self, pts, W, H, pad=60):
        xs = [self.project(p)[0] for p in pts]
        ys = [self.project(p)[1] for p in pts]
        mnx, mxx = min(xs), max(xs)
        mny, mxy = min(ys), max(ys)
        self.s = min((W - 2*pad) / (mxx - mnx), (H - 2*pad) / (mxy - mny))
        self.ox = (W - (mxx + mnx)) / 2
        self.oy = (H - (mxy + mny)) / 2

    def project_xy(self, p):
        u, v = self.project(p)
        return (u + self.ox, v + self.oy)


class Cam:
    def __init__(self, pos, target, fov=50, up=(0, 0, 1)):
        self.pos = pos
        self.fwd = norm(tuple(a-b for a, b in zip(target, pos)))
        self.right = norm(cross(self.fwd, up))
        self.upv = cross(self.right, self.fwd)
        self.fov = fov
        self.f = None

    def _f(self, H):
        if self.f is None:
            return (H / 2) / math.tan(math.radians(self.fov) / 2)
        return self.f

    def project(self, p, W, H):
        d = tuple(a-b for a, b in zip(p, self.pos))
        w = dot(d, self.fwd)
        if w < 150:
            return None
        u = dot(d, self.right)
        v = dot(d, self.upv)
        f = self._f(H)
        return (W/2 + (u/w)*f, H/2 - (v/w)*f)

    def fit(self, points, W, H, pad=40, near=200, pct=0.985):
        """Set focal length so ~98.5% of in-front points fit in the frame."""
        uu, vv = [], []
        for p in points:
            d = tuple(a-b for a, b in zip(p, self.pos))
            w = dot(d, self.fwd)
            if w < near:
                continue
            uu.append(abs(dot(d, self.right) / w))
            vv.append(abs(dot(d, self.upv) / w))
        if not uu:
            return
        uu.sort(); vv.sort()
        mu = max(uu[min(len(uu)-1, int(pct*len(uu)))], 1e-6)
        mv = max(vv[min(len(vv)-1, int(pct*len(vv)))], 1e-6)
        fu = (W/2 - pad) / mu
        fv = (H/2 - pad) / mv
        self.f = min(fu, fv)
        self.fov = 2 * math.degrees(math.atan((H/2) / self.f))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

# ----------------------------------------------------------------------------
# Scene model
# ----------------------------------------------------------------------------
class Face:
    __slots__ = ('pts', 'fill', 'normal', 'stroke', 'sw', 'order', 'depth')
    def __init__(self, pts, fill, normal=None, stroke=None, sw=0, order=0):
        self.pts = pts          # list of (x,y,z)
        self.fill = fill
        self.normal = normal    # tuple or None
        self.stroke = stroke
        self.sw = sw
        self.order = order      # manual draw priority (higher = drawn later/on top)
        self.depth = 0.0

def box(x0, y0, z0, x1, y1, z1, color, order=0, light=None, stroke=None, sw=0, top_face=True):
    """Return faces for an axis-aligned box. color may be a dict of per-face colors."""
    if light is None:
        light = light_dir()
    faces = []
    def mk(poly, n):
        nonlocal faces
        if isinstance(color, dict):
            c = color.get(n, color.get('all', '#808080'))
        else:
            c = color
        f = max(0.66, min(1.0, 0.66 + 0.32*dot(n, light)))
        faces.append(Face(poly, shade(c, f), n, stroke, sw, order))
    # top z1
    if top_face:
        mk([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1))
    # +x face (east)
    mk([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0))
    # -x face
    mk([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], (-1, 0, 0))
    # +y face
    mk([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (0, 1, 0))
    # -y face
    mk([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0))
    return faces

def plane_faces(corners, normal, color, order=0, light=None):
    """corners: 4 (x,y,z) pts; polygon normal for shading."""
    if light is None:
        light = light_dir()
    f = max(0.66, min(1.0, 0.66 + 0.32*dot(normal, light)))
    return [Face(list(corners), shade(color, f), normal, None, 0, order)]

# ----------------------------------------------------------------------------
# Renderer
# ----------------------------------------------------------------------------
def render_scene(svg, faces, proj, W, H, cull=True, sort=True):
    out = []
    for fc in faces:
        pts2 = []
        ok = True
        ctr = [0.0, 0.0, 0.0]
        for p in fc.pts:
            for i in range(3):
                ctr[i] += p[i] / len(fc.pts)
        if cull and fc.normal is not None:
            # backface cull
            view = None
            if isinstance(proj, Cam):
                view = norm(tuple(a-b for a, b in zip(proj.pos, ctr)))
            else:
                view = (1.0, 1.0, 0.6)
            if dot(fc.normal, view) <= 0:
                continue
        for p in fc.pts:
            pp = proj.project(p, W, H) if isinstance(proj, Cam) else proj.project_xy(p)
            if pp is None:
                ok = False
                break
            pts2.append(pp)
        if not ok:
            continue
        if isinstance(proj, Cam):
            d = tuple(a-b for a, b in zip(proj.pos, ctr))
            depth = dot(d, proj.fwd)
        else:
            depth = ctr[0] + ctr[1] + ctr[2]
        out.append((fc.order, -depth, fc, pts2))
    out.sort(key=lambda t: (t[0], t[1]))
    for _, _, fc, pts2 in out:
        svg.poly(pts2, fc.fill, fc.stroke, fc.sw)
