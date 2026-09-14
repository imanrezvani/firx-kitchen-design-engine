import math, sys
import scenes
from kitchen_render import SVG, render_scene, Iso

def render_concept(key, W=1400, H=880, bg='#DFD9CC'):
    faces, pal, cam, _ = scenes.CONCEPTS[key]()
    allpts = [p for fc in faces for p in fc.pts]
    cam.fit(allpts, W, H)
    svg = SVG(W, H, bg=bg)
    render_scene(svg, faces, cam, W, H)
    return svg

if __name__ == '__main__':
    key = sys.argv[1] if len(sys.argv) > 1 else 'A'
    W = int(sys.argv[2]) if len(sys.argv) > 2 else 1400
    svg = render_concept(key, W=W)
    svg.save(f'assets/concept_{key}_perspective.svg')
    print('saved concept', key)
