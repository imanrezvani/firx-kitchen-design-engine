# Extra renders for the selected concept A
import scenes
from kitchen_render import SVG, render_scene, Cam, Iso

W, H = 1400, 880
BG = '#DFD9CC'

def sceneA():
    return scenes.concept_A()

def render(cam, fname, W=W, H=H):
    faces, pal, _, _ = sceneA()
    allpts = [p for fc in faces for p in fc.pts]
    cam.fit(allpts, W, H)
    svg = SVG(W, H, bg=BG)
    render_scene(svg, faces, cam, W, H)
    svg.save(f'assets/{fname}')
    print('saved', fname)

def main():
    # front view of the cooking wall (north run)
    render(Cam((1950, 2650, 1550), (1950, 300, 1350), fov=50), 'selected_front_view.svg')
    # left perspective (from the window/sink side, looking east)
    render(Cam((250, 1800, 1500), (3000, 1800, 1100), fov=56), 'selected_left_perspective.svg')
    # right perspective (from the east wall, looking west)
    render(Cam((4100, 1800, 1550), (600, 1800, 1100), fov=56), 'selected_right_perspective.svg')
    # kitchen entrance view (from the doorway)
    render(Cam((3550, 3550, 1650), (1600, 1400, 1100), fov=55), 'selected_entrance_view.svg')
    # sink corner close-up
    render(Cam((1200, 1200, 1500), (300, 1650, 1200), fov=48), 'selected_corner_closeup.svg')
    # bird's-eye isometric
    faces, pal, _, _ = sceneA()
    allpts = [p for fc in faces for p in fc.pts]
    proj = Iso(scale=0.4)
    proj.fit(allpts, W, H)
    svg = SVG(W, H, bg=BG)
    render_scene(svg, faces, proj, W, H)
    svg.save('assets/selected_birdseye.svg')
    print('saved selected_birdseye.svg')

if __name__ == '__main__':
    main()
