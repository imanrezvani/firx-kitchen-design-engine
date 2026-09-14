# Kitchen concept scenes — builds face lists in real mm coordinates.
import math
from kitchen_render import (Face, box, plane_faces, light_dir, Cam)

ROOM_X, ROOM_Y, ROOM_Z = 4200, 3600, 2700
TOE_H = 100
COUNTER_H = 900
COUNTER_T = 950          # top of counter
DEPTH = 600              # lower/tall cabinet depth
UPPER_BOTTOM = 1350
UPPER_TOP = 2700
WINDOW = (900, 2400, 900, 2400)     # y0,y1,z0,z1 on west wall
DOOR = (3300, 4200)                 # x0,x1 on south wall

LIGHT = light_dir()

# ----------------------------------------------------------------------------
# coordinate helpers per wall
# ----------------------------------------------------------------------------
def map3(wall, a, d, z):
    if wall == 'W':
        return (d, a, z)
    if wall == 'N':
        return (a, d, z)
    if wall == 'S':
        return (a, ROOM_Y - d, z)
    if wall == 'E':
        return (ROOM_X - d, a, z)

FRONT_NORMAL = {'W': (1, 0, 0), 'N': (0, 1, 0), 'S': (0, -1, 0), 'E': (-1, 0, 0)}

def front_face(faces, wall, a0, a1, z0, z1, color, order=5, depth=DEPTH):
    pts = [map3(wall, a0, depth, z0), map3(wall, a0, depth, z1), map3(wall, a1, depth, z1), map3(wall, a1, depth, z0)]
    faces.append(Face(pts, color, FRONT_NORMAL[wall], None, 0, order))

def seam(faces, wall, a0, a1, z, color, order=6, thick=1.2, depth=DEPTH):
    d = depth + 2
    pts = [map3(wall, a0, d, z - thick), map3(wall, a0, d, z + thick),
           map3(wall, a1, d, z + thick), map3(wall, a1, d, z - thick)]
    faces.append(Face(pts, color, FRONT_NORMAL[wall], None, 0, order))

def seam_v(faces, wall, a, z0, z1, color, order=6, thick=1.2, depth=DEPTH):
    d = depth + 2
    pts = [map3(wall, a - thick, d, z0), map3(wall, a - thick, d, z1),
           map3(wall, a + thick, d, z1), map3(wall, a + thick, d, z0)]
    faces.append(Face(pts, color, FRONT_NORMAL[wall], None, 0, order))

def handle_h(faces, wall, a_center, z_center, length=300, color='#2E2E2E', order=7, depth=DEPTH):
    a0, a1 = a_center - length/2, a_center + length/2
    faces.extend(handle_box(wall, (a0, a1, z_center - 6, z_center + 6), color, order, depth))

def handle_v(faces, wall, a_center, z0, z1, color='#2E2E2E', order=7, depth=DEPTH):
    faces.extend(handle_box(wall, (a_center - 6, a_center + 6, z0, z1), color, order, depth))

def handle_box(wall, a0a1z0z1, color, order, depth=DEPTH):
    # protrude ~14 mm from front plane toward the room
    a0, a1, z0, z1 = a0a1z0z1
    if wall == 'W':
        return box(depth, a0, z0, depth + 14, a1, z1, color, order)
    if wall == 'N':
        return box(a0, depth, z0, a1, depth + 14, z1, color, order)
    if wall == 'S':
        return box(a0, ROOM_Y - depth - 14, z0, a1, ROOM_Y - depth, z1, color, order)
    return box(ROOM_X - depth - 14, a0, z0, ROOM_X - depth, a1, z1, color, order)

# ----------------------------------------------------------------------------
# run builders
# ----------------------------------------------------------------------------
def add_lower_run(faces, wall, a0, a1, mods, pal):
    """mods: list of (type, width) laid out from a0."""
    a = a0
    # toe-kick plinth band
    if wall == 'W':
        faces.extend(box(110, a0, 0, DEPTH, a1, TOE_H, pal['toe'], 0))
    elif wall == 'N':
        faces.extend(box(a0, 110, 0, a1, DEPTH, TOE_H, pal['toe'], 0))
    elif wall == 'S':
        faces.extend(box(a0, ROOM_Y - DEPTH, 0, a1, ROOM_Y - 110, TOE_H, pal['toe'], 0))
    else:
        faces.extend(box(ROOM_X - DEPTH, a0, 0, ROOM_X - 110, a1, TOE_H, pal['toe'], 0))
    # carcass body
    if wall == 'W':
        faces.extend(box(0, a0, TOE_H, DEPTH, a1, COUNTER_H, pal['carcass'], 0))
    elif wall == 'N':
        faces.extend(box(a0, 0, TOE_H, a1, DEPTH, COUNTER_H, pal['carcass'], 0))
    elif wall == 'S':
        faces.extend(box(a0, ROOM_Y - DEPTH, TOE_H, a1, ROOM_Y, COUNTER_H, pal['carcass'], 0))
    else:
        faces.extend(box(ROOM_X - DEPTH, a0, TOE_H, ROOM_X, a1, COUNTER_H, pal['carcass'], 0))
    # countertop slab
    if wall == 'W':
        faces.extend(box(0, a0, COUNTER_H, DEPTH + 20, a1, COUNTER_T, pal['counter'], 2))
    elif wall == 'N':
        faces.extend(box(a0, 0, COUNTER_H, a1, DEPTH + 20, COUNTER_T, pal['counter'], 2))
    elif wall == 'S':
        faces.extend(box(a0, ROOM_Y - DEPTH - 20, COUNTER_H, a1, ROOM_Y, COUNTER_T, pal['counter'], 2))
    else:
        faces.extend(box(ROOM_X - DEPTH - 20, a0, COUNTER_H, ROOM_X, a1, COUNTER_T, pal['counter'], 2))
    # front panels per module
    for typ, w in mods:
        if typ == 'filler':
            front_face(faces, wall, a, a + w, TOE_H, COUNTER_H, pal['filler'], 5)
        elif typ == 'drawer':
            front_face(faces, wall, a, a + w, TOE_H, COUNTER_H, pal['lower'], 5)
            for sz in (430, 620, 810):
                seam(faces, wall, a, a + w, sz, pal['seam'])
            for hz in (265, 520, 715):
                handle_h(faces, wall, a + w/2, hz, length=w - 100, color=pal['handle'])
        elif typ == 'sink':
            front_face(faces, wall, a, a + w, TOE_H, COUNTER_H, pal['lower'], 5)
            # split door seam vertical
            seam_v(faces, wall, a + w/2, TOE_H, COUNTER_H, pal['seam'])
            handle_h(faces, wall, a + w/4, COUNTER_H - 90, length=180, color=pal['handle'])
            handle_h(faces, wall, a + 3*w/4, COUNTER_H - 90, length=180, color=pal['handle'])
        elif typ == 'dw':
            front_face(faces, wall, a, a + w, TOE_H, COUNTER_H, pal['lower'], 5)
            seam(faces, wall, a, a + w, COUNTER_H - 130, pal['seam'])
            handle_h(faces, wall, a + w/2, COUNTER_H - 200, length=w - 120, color=pal['handle'])
        elif typ == 'oven':
            front_face(faces, wall, a, a + w, TOE_H, COUNTER_H, pal['lower'], 5)
            seam(faces, wall, a, a + w, 500, pal['seam'])
            front_face(faces, wall, a + 30, a + w - 30, 130, 490, pal['oven_glass'], 6)
            handle_h(faces, wall, a + w/2, 470, length=w - 160, color=pal['handle'])
            handle_h(faces, wall, a + w/2, 700, length=w - 100, color=pal['handle'])
        elif typ == 'corner':
            front_face(faces, wall, a, a + w, TOE_H, COUNTER_H, pal['lower'], 5)
            handle_v(faces, wall, a + w - 40, COUNTER_H/2 - 60, COUNTER_H/2 + 60, color=pal['handle'])
        elif typ == 'cab':
            front_face(faces, wall, a, a + w, TOE_H, COUNTER_H, pal['lower'], 5)
            seam_v(faces, wall, a + w/2, TOE_H, COUNTER_H, pal['seam'])
            handle_h(faces, wall, a + w/4, COUNTER_H - 80, length=150, color=pal['handle'])
            handle_h(faces, wall, a + 3*w/4, COUNTER_H - 80, length=150, color=pal['handle'])
        a += w

def add_upper_run(faces, wall, a0, a1, mods, pal):
    a = a0
    if wall == 'W':
        faces.extend(box(0, a0, UPPER_BOTTOM, 350, a1, UPPER_TOP, pal['upper_body'], 3))
    elif wall == 'N':
        faces.extend(box(a0, 0, UPPER_BOTTOM, a1, 350, UPPER_TOP, pal['upper_body'], 3))
    elif wall == 'S':
        faces.extend(box(a0, ROOM_Y - 350, UPPER_BOTTOM, a1, ROOM_Y, UPPER_TOP, pal['upper_body'], 3))
    else:
        faces.extend(box(ROOM_X - 350, a0, UPPER_BOTTOM, ROOM_X, a1, UPPER_TOP, pal['upper_body'], 3))
    for typ, w in mods:
        if typ == 'cab':
            front_face(faces, wall, a, a + w, UPPER_BOTTOM, UPPER_TOP, pal['upper'], 5, depth=350)
            seam_v(faces, wall, a + w/2, UPPER_BOTTOM + 40, UPPER_TOP - 40, pal['seam'], depth=350)
            handle_h(faces, wall, a + w/4, UPPER_BOTTOM + 90, length=140, color=pal['handle'], depth=350)
            handle_h(faces, wall, a + 3*w/4, UPPER_BOTTOM + 90, length=140, color=pal['handle'], depth=350)
        elif typ == 'hood':
            # extractor canopy
            h0 = 1560
            if wall == 'N':
                faces.extend(box(a + 20, 80, 1420, a + w - 20, 560, h0, pal['hood'], 4))
            elif wall == 'W':
                faces.extend(box(80, a + 20, 1420, 560, a + w - 20, h0, pal['hood'], 4))
            elif wall == 'S':
                faces.extend(box(a + 20, ROOM_Y - 560, 1420, a + w - 20, ROOM_Y - 80, h0, pal['hood'], 4))
        a += w

def add_tall_run(faces, wall, a0, a1, typ, pal):
    if wall == 'N':
        faces.extend(box(a0, 0, TOE_H, a1, DEPTH, UPPER_TOP, pal['tall_body'], 3))
    elif wall == 'W':
        faces.extend(box(0, a0, TOE_H, DEPTH, a1, UPPER_TOP, pal['tall_body'], 3))
    elif wall == 'S':
        faces.extend(box(a0, ROOM_Y - DEPTH, TOE_H, a1, ROOM_Y, UPPER_TOP, pal['tall_body'], 3))
    w = a1 - a0
    if typ == 'fridge':
        front_face(faces, wall, a0, a1, TOE_H, UPPER_TOP, pal['lower'], 5)
        seam(faces, wall, a0, a1, 1870, pal['seam'])
        seam_v(faces, wall, a0 + w/2, 130, 1870, pal['seam'])
        front_face(faces, wall, a0 + 6, a1 - 6, 130, 1870, pal['appliance'], 6)
        front_face(faces, wall, a0 + 6, a1 - 6, 1880, UPPER_TOP - 30, pal['upper'], 6)
        handle_v(faces, wall, a0 + w/2, 300, 1700, color=pal['handle'])
    elif typ == 'pantry':
        front_face(faces, wall, a0, a1, TOE_H, UPPER_TOP, pal['lower'], 5)
        handle_v(faces, wall, a0 + w - 40, 400, UPPER_TOP - 300, color=pal['handle'])

def add_backsplash(faces, wall, a0, a1, pal, z0=COUNTER_H, z1=UPPER_BOTTOM):
    d = 0
    pts = [map3(wall, a0, d, z0), map3(wall, a0, d, z1), map3(wall, a1, d, z1), map3(wall, a1, d, z0)]
    faces.append(Face(pts, pal['backsplash'], FRONT_NORMAL[wall], None, 0, 1))

# ----------------------------------------------------------------------------
# room shell: floor, walls, ceiling, window, door
# ----------------------------------------------------------------------------
def add_shell(faces, pal):
    # floor
    faces.append(Face([(0, 0, 0), (ROOM_X, 0, 0), (ROOM_X, ROOM_Y, 0), (0, ROOM_Y, 0)],
                      pal['floor'], (0, 0, 1), None, 0, -10))
    # floor plank lines
    for i in range(0, ROOM_X + 1, 600):
        faces.append(Face([(i, 0, 0.5), (i, ROOM_Y, 0.5)], pal['floor_line'], (0, 0, 1), None, 0, -9))
    for j in range(0, ROOM_Y + 1, 900):
        faces.append(Face([(0, j, 0.5), (ROOM_X, j, 0.5)], pal['floor_line'], (0, 0, 1), None, 0, -9))
    # walls
    faces.append(Face([(0, 0, 0), (0, ROOM_Y, 0), (0, ROOM_Y, ROOM_Z), (0, 0, ROOM_Z)], pal['wall'], (1, 0, 0), None, 0, -8))
    faces.append(Face([(0, 0, 0), (ROOM_X, 0, 0), (ROOM_X, 0, ROOM_Z), (0, 0, ROOM_Z)], pal['wall'], (0, 1, 0), None, 0, -8))
    faces.append(Face([(ROOM_X, 0, 0), (ROOM_X, ROOM_Y, 0), (ROOM_X, ROOM_Y, ROOM_Z), (ROOM_X, 0, ROOM_Z)], pal['wall'], (-1, 0, 0), None, 0, -8))
    faces.append(Face([(0, ROOM_Y, 0), (ROOM_X, ROOM_Y, 0), (ROOM_X, ROOM_Y, ROOM_Z), (0, ROOM_Y, ROOM_Z)], pal['wall'], (0, -1, 0), None, 0, -8))
    # ceiling
    faces.append(Face([(0, 0, ROOM_Z), (ROOM_X, 0, ROOM_Z), (ROOM_X, ROOM_Y, ROOM_Z), (0, ROOM_Y, ROOM_Z)],
                      pal['ceiling'], (0, 0, -1), None, 0, -8))
    # window on west wall
    y0, y1, z0, z1 = WINDOW
    fr = pal['frame']
    # frame strips as thin boxes offset into room
    faces.extend(box(0, y0 - 40, z0 - 40, 60, y0 + 20, z1 + 40, fr, 1))
    faces.extend(box(0, y1 - 20, z0 - 40, 60, y1 + 40, z1 + 40, fr, 1))
    faces.extend(box(0, y0, z0 - 40, 60, y1, z0 + 20, fr, 1))
    faces.extend(box(0, y0, z1 - 20, 60, y1, z1 + 40, fr, 1))
    faces.extend(box(0, y0, (z0+z1)/2 - 20, 60, y1, (z0+z1)/2 + 20, fr, 1))
    # glass
    faces.append(Face([(6, y0, z0), (6, y0, z1), (6, y1, z1), (6, y1, z0)], pal['glass'], (1, 0, 0), None, 0, 3))
    # door on south wall
    x0, x1 = DOOR
    faces.append(Face([(x0, ROOM_Y, 0), (x1, ROOM_Y, 0), (x1, ROOM_Y, ROOM_Z), (x0, ROOM_Y, ROOM_Z)],
                      pal['door'], (0, -1, 0), None, 0, -7))
    faces.append(Face([(x0, ROOM_Y - 40, 0), (x0, ROOM_Y - 40, 2100), (x1, ROOM_Y - 40, 2100), (x1, ROOM_Y - 40, 0)],
                      pal['door_leaf'], (0, -1, 0), None, 0, 0))
    faces.append(Face([(x0, ROOM_Y - 40, 0), (x0, ROOM_Y - 40, 2100), (x0 + 20, ROOM_Y - 40, 2100), (x0 + 20, ROOM_Y - 40, 0)],
                      pal['door_leaf2'], (0, -1, 0), None, 0, 0))

def add_sun_patch(faces, pal):
    # warm light patch on floor near window
    pts = [(300, 700, 2), (2600, 300, 2), (2900, 2600, 2), (900, 2900, 2)]
    faces.append(Face(pts, '#FFF3D8', (0, 0, 1), None, 0, 8, ))

# ----------------------------------------------------------------------------
# decor: sink, hob, faucet, items
# ----------------------------------------------------------------------------
def add_sink_decor(faces, wall, a_center, pal):
    # sink bowl on countertop top face
    if wall == 'W':
        cx, cy, cz = 300, a_center, COUNTER_T + 2
        faces.append(Face([(cx - 340, cy - 215, cz), (cx - 340, cy + 215, cz), (cx + 340, cy + 215, cz), (cx + 340, cy - 215, cz)],
                          pal['sink'], (0, 0, 1), None, 0, 8))
        faces.append(Face([(cx - 280, cy - 160, cz + 2), (cx - 280, cy + 160, cz + 2), (cx + 280, cy + 160, cz + 2), (cx + 280, cy - 160, cz + 2)],
                          pal['sink_in'], (0, 0, 1), None, 0, 9))
        # faucet
        faces.extend(box(500, cy - 40, COUNTER_T, 512, cy + 40, COUNTER_T + 280, pal['faucet'], 9))
        faces.extend(box(452, cy - 15, COUNTER_T + 250, 512, cy + 15, COUNTER_T + 265, pal['faucet'], 9))

def add_hob_decor(faces, wall, a0, a1, pal):
    if wall == 'N':
        faces.extend(box(a0 + 25, 70, COUNTER_T, a1 - 25, 530, COUNTER_T + 12, pal['appliance'], 8))
        for (hx, hy) in ((a0 + 180, 220), (a0 + 420, 220), (a0 + 180, 400), (a0 + 420, 400)):
            faces.append(Face([(hx - 55, hy - 55, COUNTER_T + 13), (hx + 55, hy - 55, COUNTER_T + 13),
                               (hx + 55, hy + 55, COUNTER_T + 13), (hx - 55, hy + 55, COUNTER_T + 13)],
                              pal['hob_ring'], (0, 0, 1), None, 0, 9))

def add_items(faces, a_center, pal, wall='W'):
    # cutting board + fruit bowl on a counter (west run by default)
    if wall == 'W':
        faces.extend(box(150, a_center + 90, COUNTER_T, 360, a_center + 330, COUNTER_T + 18, pal['board'], 9))
        faces.append(Face([(180, a_center - 60, COUNTER_T + 19), (180, a_center + 60, COUNTER_T + 19),
                           (320, a_center + 60, COUNTER_T + 19), (320, a_center - 60, COUNTER_T + 19)],
                          pal['bowl'], (0, 0, 1), None, 0, 10))

def add_pendants(faces, pal, x_center, y_center):
    for dx in (-330, 330):
        faces.extend(box(x_center + dx - 12, y_center - 12, 2500, x_center + dx + 12, y_center + 12, 2620, pal['pendant_rod'], 9))
        faces.extend(box(x_center + dx - 70, y_center - 70, 2340, x_center + dx + 70, y_center + 70, 2500, pal['pendant'], 9))

# ----------------------------------------------------------------------------
# Concept A — Ergonomic L  (west = sink/window, north = cooking + tall wall)
# ----------------------------------------------------------------------------
def concept_A():
    pal = dict(
        wall='#E9E3D7', ceiling='#F4F1EA', floor='#D6C2A0', floor_line='#C9B38F',
        lower='#D7C9AE', upper='#F1ECE1', tall='#D7C9AE',
        carcass='#C3B393', upper_body='#E3DCCB', tall_body='#C0B090',
        counter='#F6F4EF', backsplash='#EAE4D6', toe='#8E8673', filler='#C3B393',
        seam='#B8A585', handle='#2E2E2E',
        glass='#C9DCF0', frame='#45484C', hood='#4A4D52',
        appliance='#23262A', oven_glass='#1B1E21', door='#C3B393', door_leaf='#A89F8E', door_leaf2='#8F8675',
        sink='#B9BEC4', sink_in='#CFD4D9', faucet='#8E9499',
        board='#C29A6B', bowl='#D96B4A', hob_ring='#33363A',
        pendant='#E8E3D6', pendant_rod='#333333',
    )
    faces = []
    add_shell(faces, pal)
    add_sun_patch(faces, pal)
    # wall art on the east wall
    faces.append(Face([(4100, 1500, 1500), (4100, 1500, 1950), (4100, 2100, 1950), (4100, 2100, 1500)], '#B7A58A', (-1, 0, 0), None, 0, 4))
    faces.append(Face([(4100, 1580, 1580), (4100, 1580, 1870), (4100, 2020, 1870), (4100, 2020, 1580)], '#7E8FA3', (-1, 0, 0), None, 0, 5))
    # WEST run (window wall) lower: y 600..3600
    add_lower_run(faces, 'W', 600, 3600, [
        ('drawer', 600), ('sink', 900), ('dw', 600), ('drawer', 600), ('filler', 300)], pal)
    add_backsplash(faces, 'W', 600, 900, pal)
    add_backsplash(faces, 'W', 2400, 3600, pal)
    add_upper_run(faces, 'W', 2700, 3300, [('cab', 600)], pal)
    # over-window cabinet 1500 wide x 300 high
    faces.extend(box(0, 900, 2400, 350, 2400, 2700, pal['upper_body'], 3))
    front_face(faces, 'W', 900, 2400, 2400, 2700, pal['upper'], 5, depth=350)
    seam_v(faces, 'W', 1650, 2410, 2690, pal['seam'], depth=350)
    # NORTH run (cooking) lower: x 600..3300
    add_lower_run(faces, 'N', 600, 3300, [
        ('corner', 300), ('oven', 600), ('drawer', 600)], pal)
    add_tall_run(faces, 'N', 2100, 2700, 'fridge', pal)
    add_tall_run(faces, 'N', 2700, 3300, 'pantry', pal)
    add_backsplash(faces, 'N', 600, 2100, pal)
    add_upper_run(faces, 'N', 600, 2100, [('cab', 600), ('hood', 600), ('cab', 600)], pal)
    # decor
    add_sink_decor(faces, 'W', 1650, pal)
    add_hob_decor(faces, 'N', 900, 1500, pal)
    add_items(faces, 950, pal)
    cam = Cam((3400, 2100, 1550), (1900, 500, 1000), fov=48)
    return faces, pal, cam, 'A'

# ----------------------------------------------------------------------------
# Concept B — U-shaped  (west sink, north cooking+tall, south prep/storage)
# ----------------------------------------------------------------------------
def concept_B():
    pal = dict(
        wall='#EAE2D3', ceiling='#F1EBDF', floor='#7E6B53', floor_line='#75624B',
        lower='#8A6A4B', upper='#8A6A4B', tall='#8A6A4B',
        carcass='#7A5C40', upper_body='#7A5C40', tall_body='#75583D',
        counter='#CBCED3', backsplash='#E5E1D6', toe='#5C4936', filler='#7A5C40',
        seam='#6D5138', handle='#2B2B2B',
        glass='#C9DCF0', frame='#3F423F', hood='#3A3D3A',
        appliance='#1E2123', oven_glass='#191C1E', door='#7A5C40', door_leaf='#68503A', door_leaf2='#5A452F',
        sink='#AEB4BA', sink_in='#C8CDD3', faucet='#7A8086',
        board='#B98F5F', bowl='#C9573B', hob_ring='#2E3133',
        pendant='#8A6A4B', pendant_rod='#2B2B2B',
    )
    faces = []
    add_shell(faces, pal)
    add_sun_patch(faces, pal)
    add_lower_run(faces, 'W', 600, 3600, [
        ('drawer', 600), ('sink', 900), ('dw', 600), ('drawer', 600), ('filler', 300)], pal)
    add_backsplash(faces, 'W', 600, 900, pal)
    add_backsplash(faces, 'W', 2400, 3600, pal)
    add_upper_run(faces, 'W', 2700, 3300, [('cab', 600)], pal)
    faces.extend(box(0, 900, 2400, 350, 2400, 2700, pal['upper_body'], 3))
    front_face(faces, 'W', 900, 2400, 2400, 2700, pal['upper'], 5, depth=350)
    seam_v(faces, 'W', 1650, 2410, 2690, pal['seam'], depth=350)
    add_lower_run(faces, 'N', 600, 3300, [
        ('corner', 300), ('oven', 600), ('drawer', 600)], pal)
    add_tall_run(faces, 'N', 2100, 2700, 'fridge', pal)
    add_tall_run(faces, 'N', 2700, 3300, 'pantry', pal)
    add_backsplash(faces, 'N', 600, 2100, pal)
    add_upper_run(faces, 'N', 600, 2100, [('cab', 600), ('hood', 600), ('cab', 600)], pal)
    # SOUTH run (prep/storage) x 600..3300
    add_lower_run(faces, 'S', 600, 3300, [
        ('corner', 300), ('drawer', 600), ('drawer', 600), ('drawer', 600), ('drawer', 600)], pal)
    add_backsplash(faces, 'S', 600, 3300, pal)
    add_upper_run(faces, 'S', 600, 3000, [('cab', 600), ('cab', 600), ('cab', 600), ('cab', 600)], pal)
    add_sink_decor(faces, 'W', 1650, pal)
    add_hob_decor(faces, 'N', 900, 1500, pal)
    add_items(faces, 950, pal)
    cam = Cam((3350, 2300, 1550), (1600, 1400, 1050), fov=56)
    return faces, pal, cam, 'B'

# ----------------------------------------------------------------------------
# Concept C — L + island
# ----------------------------------------------------------------------------
def concept_C():
    pal = dict(
        wall='#F0EBE2', ceiling='#F5F1EA', floor='#D8C5A6', floor_line='#CDB896',
        lower='#3A3D42', upper='#F6F3ED', tall='#3A3D42',
        carcass='#31343A', upper_body='#DDD7CA', tall_body='#2E3136',
        counter='#F7F5F1', backsplash='#EFE9DE', toe='#23252A', filler='#31343A',
        seam='#23252A', handle='#C9C4B8',
        glass='#C9DCF0', frame='#45484C', hood='#4A4D52',
        appliance='#1E2124', oven_glass='#191C1E', door='#31343A', door_leaf='#A89F8E', door_leaf2='#8F8675',
        sink='#B9BEC4', sink_in='#CFD4D9', faucet='#8E9499',
        board='#C29A6B', bowl='#D96B4A', hob_ring='#33363A',
        pendant='#E8E3D6', pendant_rod='#333333', island='#D2B48C', island_shelf='#B89A6E',
    )
    faces = []
    add_shell(faces, pal)
    add_sun_patch(faces, pal)
    add_lower_run(faces, 'W', 600, 3600, [
        ('drawer', 600), ('sink', 900), ('dw', 600), ('drawer', 600), ('filler', 300)], pal)
    add_backsplash(faces, 'W', 600, 900, pal)
    add_backsplash(faces, 'W', 2400, 3600, pal)
    add_upper_run(faces, 'W', 2700, 3300, [('cab', 600)], pal)
    faces.extend(box(0, 900, 2400, 350, 2400, 2700, pal['upper_body'], 3))
    front_face(faces, 'W', 900, 2400, 2400, 2700, pal['upper'], 5, depth=350)
    seam_v(faces, 'W', 1650, 2410, 2690, pal['seam'], depth=350)
    add_lower_run(faces, 'N', 600, 3300, [
        ('corner', 300), ('oven', 600), ('drawer', 600)], pal)
    add_tall_run(faces, 'N', 2100, 2700, 'fridge', pal)
    add_tall_run(faces, 'N', 2700, 3300, 'pantry', pal)
    add_backsplash(faces, 'N', 600, 2100, pal)
    add_upper_run(faces, 'N', 600, 2100, [('cab', 600), ('hood', 600), ('cab', 600)], pal)
    # ISLAND 1500x900 at X 1800..3300, Y 1500..2400
    ix0, ix1, iy0, iy1 = 1800, 3300, 1500, 2400
    faces.extend(box(ix0, iy0, TOE_H, ix1, iy1, COUNTER_H, pal['island'], 3))
    faces.extend(box(ix0, iy0, COUNTER_H, ix1 + 300, iy1, COUNTER_T, pal['counter'], 4))
    # island drawer front faces (north + south)
    faces.append(Face([(ix0, iy0, TOE_H), (ix0, iy0, COUNTER_H), (ix1, iy0, COUNTER_H), (ix1, iy0, TOE_H)],
                      pal['island'], (0, 1, 0), None, 0, 5))
    faces.append(Face([(ix0, iy1, TOE_H), (ix0, iy1, COUNTER_H), (ix1, iy1, COUNTER_H), (ix1, iy1, TOE_H)],
                      pal['island'], (0, -1, 0), None, 0, 5))
    # handles on island north drawer fronts
    for hx in (ix0 + 250, ix0 + 750, ix0 + 1250):
        faces.extend(box(hx - 190, iy0 - 14, 494, hx + 190, iy0, 506, pal['handle'], 7))
    # open shelf on east end (seating side)
    faces.append(Face([(ix1, iy0, TOE_H), (ix1, iy0, COUNTER_H), (ix1, iy1, COUNTER_H), (ix1, iy1, TOE_H)],
                      pal['island'], (-1, 0, 0), None, 0, 5))
    faces.extend(box(ix1 - 10, iy0, COUNTER_H - 300, ix1 + 10, iy1, COUNTER_H, pal['island_shelf'], 6))
    # two stools at the east seating side
    for sy in (1750, 2100):
        faces.extend(box(3400, sy - 180, 0, 3760, sy + 180, 470, pal['island_shelf'], 6))
        faces.extend(box(3520, sy - 30, 470, 3640, sy + 30, 730, pal['island_shelf'], 6))
    add_pendants(faces, pal, (ix0 + ix1) / 2, iy0 + 300)
    add_sink_decor(faces, 'W', 1650, pal)
    add_hob_decor(faces, 'N', 900, 1500, pal)
    add_items(faces, 950, pal)
    cam = Cam((4050, 2950, 2150), (2000, 2000, 1000), fov=57)
    return faces, pal, cam, 'C'

# ----------------------------------------------------------------------------
# Concept D — L + dining nook
# ----------------------------------------------------------------------------
def concept_D():
    pal = dict(
        wall='#F0EBE0', ceiling='#F5F1E9', floor='#E2D3BC', floor_line='#D6C5AA',
        lower='#D9C9AE', upper='#F3EFE6', tall='#B49A78',
        carcass='#C9B795', upper_body='#E6E0D2', tall_body='#A8906F',
        counter='#F7F5F1', backsplash='#EDE7DA', toe='#8C7A5C', filler='#C9B795',
        seam='#BEAC8B', handle='#3A3A3A',
        glass='#C9DCF0', frame='#45484C', hood='#4A4D52',
        appliance='#1E2124', oven_glass='#191C1E', door='#C9B795', door_leaf='#A89F8E', door_leaf2='#8F8675',
        sink='#B9BEC4', sink_in='#CFD4D9', faucet='#8E9499',
        board='#C29A6B', bowl='#D96B4A', hob_ring='#33363A',
        pendant='#E8E3D6', pendant_rod='#333333', island='#D2B48C', island_shelf='#B89A6E',
    )
    faces = []
    add_shell(faces, pal)
    add_sun_patch(faces, pal)
    add_lower_run(faces, 'W', 600, 3600, [
        ('drawer', 600), ('sink', 900), ('dw', 600), ('drawer', 600), ('filler', 300)], pal)
    add_backsplash(faces, 'W', 600, 900, pal)
    add_backsplash(faces, 'W', 2400, 3600, pal)
    add_upper_run(faces, 'W', 2700, 3300, [('cab', 600)], pal)
    faces.extend(box(0, 900, 2400, 350, 2400, 2700, pal['upper_body'], 3))
    front_face(faces, 'W', 900, 2400, 2400, 2700, pal['upper'], 5, depth=350)
    seam_v(faces, 'W', 1650, 2410, 2690, pal['seam'], depth=350)
    add_lower_run(faces, 'N', 600, 3300, [
        ('corner', 300), ('oven', 600), ('drawer', 600)], pal)
    add_tall_run(faces, 'N', 2100, 2700, 'fridge', pal)
    add_tall_run(faces, 'N', 2700, 3300, 'pantry', pal)
    add_backsplash(faces, 'N', 600, 2100, pal)
    add_upper_run(faces, 'N', 600, 2100, [('cab', 600), ('hood', 600), ('cab', 600)], pal)
    # DINING ZONE on east wall
    # banquette bench along east wall y 300..1400
    faces.extend(box(3600, 300, 0, 4100, 1400, 460, pal['lower'], 3))
    faces.extend(box(3600, 300, 460, 4100, 1400, 900, pal['upper'], 4))
    # buffet / coffee tall unit on east wall y 1800..2600
    faces.extend(box(3600, 1800, 0, 4200, 2600, UPPER_TOP, pal['tall_body'], 3))
    front_face(faces, 'E', 1800, 2600, TOE_H, UPPER_TOP, pal['tall'], 5)
    handle_v(faces, 'E', 2510, 400, 2400, color=pal['handle'])
    # table
    faces.extend(box(2400, 1500, 720, 3800, 2300, 750, pal['counter'], 4))
    # chairs (simplified blocks)
    faces.extend(box(2350, 2300, 0, 2450, 2500, 460, pal['island_shelf'], 4))
    faces.extend(box(3750, 2300, 0, 3850, 2500, 460, pal['island_shelf'], 4))
    add_sink_decor(faces, 'W', 1650, pal)
    add_hob_decor(faces, 'N', 900, 1500, pal)
    add_items(faces, 950, pal)
    add_pendants(faces, pal, 3000, 2200)
    cam = Cam((3450, 3380, 1550), (1900, 950, 1150), fov=56)
    return faces, pal, cam, 'D'

CONCEPTS = {'A': concept_A, 'B': concept_B, 'C': concept_C, 'D': concept_D}
