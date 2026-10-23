"""Short 4 – "Garage No. 13" (35 sec).

Purana garage, jhapakti tube light, kapde se dhaki car. Kapda hat'ta hai — GHOST.
Dashboard apne aap jalta hai, shutter khulta hai, car bina driver ke bahar.
Diwar par 13 photos — har ek mein ek haari hui car.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C  # noqa: E402

NAME = "short4"
opts = C.cli()
C.reset()
sc = C.setup(NAME, 35, opts["preview"])
C.world((0.003, 0.004, 0.007), 1.0)
F = C.f

# --------------------------------------------------------------- garage
concrete = C.surface("garage_concrete", (0.07, 0.066, 0.06), (0.14, 0.13, 0.12), (0.6, 0.95), 0.3, 0.4, 10)
floor_m = C.surface("garage_floor", (0.035, 0.035, 0.035), (0.08, 0.075, 0.07), (0.08, 0.6), 0.15, 0.35, 20, puddles=True)  # oily patches
C.box("floor", (14, 18, 0.2), (0, 0, -0.1), floor_m)
C.box("ceiling", (14, 18, 0.2), (0, 0, 5.1), concrete)
C.box("back_wall", (14, 0.3, 5), (0, -9, 2.5), concrete)
for sx in (-1, 1):
    C.box(f"side_wall{sx}", (0.3, 18, 5), (sx * 7, 0, 2.5), concrete)
    C.box(f"front_wall{sx}", (4, 0.3, 5), (sx * 5, 9, 2.5), concrete)
C.box("front_lintel", (6, 0.3, 1.2), (0, 9, 4.4), concrete)
shutter = C.box("shutter", (6, 0.08, 3.8), (0, 8.75, 1.9), C.mat("shutter_m", (0.18, 0.18, 0.19), 0.8, 0.45))
for i in range(19):                                  # corrugation ribs
    C.box(f"rib{i}", (6, 0.12, 0.04), (0, -0.02, -1.8 + i * 0.2), shutter.data.materials[0], parent=shutter)
C.key(shutter, "location", [(F(22.5), (0, 8.75, 1.9)), (F(26.5), (0, 8.75, 5.6))])

# junk: shelves, tyres, barrels
junk = C.mat("junk", (0.06, 0.05, 0.04), 0.3, 0.6)
for i in range(4):
    C.box(f"shelf{i}", (0.6, 3.0, 0.06), (-6.4, -4 + (i % 2) * 3.5, 0.8 + (i // 2) * 1.0), junk)
for i in range(5):
    C.cylinder(f"tyre{i}", 0.36, 0.26, (6.2, -7 + i * 0.05, 0.13 + i * 0.27), C.mat(f"tyre_m{i}", (0.015,) * 3, 0, 0.8))
for i in range(3):
    C.cylinder(f"barrel{i}", 0.3, 0.9, (-6.1 + i * 0.65, 7.6, 0.45), C.mat(f"barrel_m{i}", (0.25, 0.04, 0.02), 0.5, 0.5))

# flickering tube light
tube_m = C.glow("tube_m", (0.85, 0.95, 1.0), 25.0)
C.cylinder("tube", 0.04, 1.6, (0, -1, 4.85), tube_m, axis="X", segments=12)
tube = C.light("tube_light", "AREA", 220, (0, -1, 4.75), (0.85, 0.95, 1.0), 1.6)
tube.data.shape = "RECTANGLE"
tube.data.size, tube.data.size_y = 1.6, 0.15
pairs = []
t = 0.0
while t < 35:
    on = random.random() < (0.45 if t < 4 else 0.93)
    pairs.append((F(t), 1.0 if on else 0.0))
    t += random.uniform(0.06, 0.25) if t < 4 else random.uniform(0.4, 2.0)
C.key(tube.data, "energy", [(fr, 220 * v) for fr, v in pairs], "CONSTANT")
C.key_emit(tube_m, [(fr, 25 * v) for fr, v in pairs], "CONSTANT")
C.light("bounce", "POINT", 25, (0, 5, 2.5), (0.5, 0.55, 0.7), 1.0)

# street outside the shutter
C.box("street", (200, 40, 0.2), (0, 30, -0.12), C.mat("street_m", (0.02, 0.02, 0.022), 0, 0.3))
window_on = C.glow("window_on", (1.0, 0.72, 0.4), 4.0)
wall = C.mat("facade", (0.02, 0.02, 0.025), 0.1, 0.7)
for i in range(9):
    w, h = random.uniform(10, 18), random.uniform(10, 40)
    x = -55 + i * 13
    C.box(f"facade{i}", (w, 10, h), (x, 52, h / 2), wall)
    for k in range(int(h // 4)):
        for j in range(int(w // 3)):
            if random.random() < 0.25:
                C.box(f"fw{i}_{k}_{j}", (1.4, 0.05, 1.6), (x - w / 2 + 1.5 + j * 3, 46.95, 3 + k * 4), window_on)
C.light("street_lamp", "SPOT", 5000, (6, 30, 8), (1.0, 0.6, 0.3), 0.4, spot=1.7)

# --------------------------------------------------------------- the car and its cover
exit_path = C.Path("exit", [(0, -1, 0), (0, 10, 0), (0, 22, 0), (15, 35, 0), (45, 40, 0)])
ghost = C.Car("ghost", "ghost", head_color=(0.25, 0.45, 1.0), head_on=False)
ghost.drive(exit_path, [(F(0), 0), (F(27), 0), (F(28), 3), (F(29), 10), (F(30), 22), (F(31), 42),
                        (F(35), 120)], interp="LINEAR")
ghost.headlights([(F(0), 0), (F(14.4), 0), (F(14.8), 1.0)], strength=45, spot=2200)
C.key_emit(ghost.tail, [(F(0), 0), (F(14.4), 0), (F(14.8), 12)])

cloth_m = C.mat("cloth", (0.16, 0.15, 0.13), 0.0, 0.95)
cloth = C.box("cloth", (2.35, 5.3, 1.5), (0, -1, 0.78), cloth_m)
cloth.modifiers.new("sub", "SUBSURF").levels = 3
tex = C.bpy.data.textures.new("cloth_wrinkles", "CLOUDS")
tex.noise_scale = 0.35
disp = cloth.modifiers.new("wrinkles", "DISPLACE")
disp.texture, disp.strength = tex, 0.12
C.key(cloth, "location", [(F(4), (0, -1, 0.78)), (F(7), (0, -2.6, 0.7)), (F(10), (0, -6.3, 0.25))])
C.key(cloth, "rotation_euler", [(F(4), (0, 0, 0)), (F(10), (-0.25, 0, 0.08))])
C.key(cloth, "scale", [(F(4), (1, 1, 1)), (F(10), (1.05, 0.6, 0.25))])

# light line sweeping along the body
sweep = C.light("sweep", "AREA", 400, (2.6, -4.5, 1.0), (0.8, 0.9, 1.0), 0.1, rot=(0, math.pi / 2, 0))
sweep.data.shape = "RECTANGLE"
sweep.data.size, sweep.data.size_y = 0.08, 1.4
C.key(sweep, "location", [(F(10), (2.6, -4.5, 1.0)), (F(14), (2.6, 2.6, 1.0))], "LINEAR")
C.key(sweep.data, "energy", [(F(9.9), 0), (F(10), 400), (F(14), 400), (F(14.1), 0)], "CONSTANT")

# exhaust flames + garage shake
flame_m = C.glow("flame", (0.25, 0.5, 1.0), 0.0)
for i, ex in enumerate(ghost.exhausts):
    fl = C.cylinder(f"flame{i}", 0.09, 0.6, (ex.x, ex.y - 0.3, ex.z), flame_m, axis="Y", r2=0.0, parent=ghost.root)
    C.key(fl, "scale", [(F(18) + k * 2, (1, random.uniform(0.6, 1.6), 1)) for k in range(60)])
pulse = [(F(18) - 1, 0)] + [(F(18) + k * 2, random.uniform(8, 30)) for k in range(60)] + [(F(22.5), 0)]
C.key_emit(flame_m, pulse)
blue = C.light("flame_light", "POINT", 0, (0, -3.2, 0.4), (0.25, 0.5, 1.0), 0.2, parent=ghost.root)
C.key(blue.data, "energy", [(fr, v * 12) for fr, v in pulse])
for ex in ghost.exhausts:
    C.smoke(f"exhaust_smoke{ex.x}", tuple(ex), ghost.root, F(18), F(31), 700, (0.45, 0.45, 0.5), (0, -2.5, 0.5),
            0.5, 60, 0.1)

# speedometer set (the GHOST's dashboard wakes up)
DASH = (5000, 0, 0)
pivot = C.dashboard("dash", DASH, color=(0.3, 0.55, 1.0))
for nm in ("dash_ring", "dash_tick", "dash_font", "dash_needle_m"):
    m = C.bpy.data.materials[nm]
    full = C.emission(m).default_value
    C.key_emit(m, [(F(14), 0), (F(14.6), full)])
C.needle(pivot, [(F(14.8), 0), (F(16), 240), (F(17.2), 0)])

# --------------------------------------------------------------- the wall of 13 photos
names = ["CHARGER", "PICKUP", "ROADSTER"] + [f"#{n}" for n in range(4, 14)]
tints = [(0.42, 0.01, 0.01), (0.06, 0.16, 0.32), (0.75, 0.72, 0.66)]
frame_m = C.mat("photo_frame", (0.85, 0.83, 0.78), 0, 0.6)
cross_m = C.mat("red_x", (0.6, 0.01, 0.01), 0, 0.5)
font_m = C.mat("label", (0.05, 0.05, 0.05), 0, 0.6)
FACE_ROOM = (math.pi / 2, 0, math.pi)              # faces +Y, reads left-to-right from inside
slots = [(r, c) for r, n in enumerate((5, 4, 4)) for c in range(n)]
for i, (r, c) in enumerate(slots):
    n_in_row = (5, 4, 4)[r]
    x = (c - (n_in_row - 1) / 2) * 1.25
    z = 3.3 - r * 0.95
    y = -8.83
    C.plane(f"photo_frame{i}", 0.95, 0.75, (x, y, z), frame_m, rot=FACE_ROOM)
    img = os.path.join(C.ASSETS, "photos", f"photo{i + 1}.png")
    pm = C.image_mat(f"photo_m{i}", img, 0.3) if os.path.exists(img) else \
        C.mat(f"photo_m{i}", tints[i] if i < 3 else (0.1, 0.1, 0.1), 0.2, 0.5)
    C.plane(f"photo{i}", 0.85, 0.55, (x, y + 0.005, z + 0.04), pm, rot=FACE_ROOM)
    for s in (-1, 1):
        C.box(f"x{i}{s}", (0.95, 0.01, 0.04), (x, y + 0.01, z + 0.04), cross_m, rot=(0, s * 0.55, 0))
    C.text(f"label{i}", names[i], (x, y + 0.01, z - 0.3), 0.08, font_m, rot=FACE_ROOM, extrude=0.0)

# --------------------------------------------------------------- shots
C.cut(C.camera("cam1_corner", (6.3, 8.3, 4.2), (0, -1, 0.8), 18), 0)                  # 1 tube light flicker
c2 = C.camera("cam2_push", (0, 6, 1.6), (0, -1, 0.9), 35)                               # 2 cover slides off
C.key(c2, "location", [(F(4), (0, 6, 1.6)), (F(10), (0, 3.6, 1.35))])
C.cut(c2, 4)
C.cut(C.camera("cam3_side", (3.4, -0.2, 0.9), (0.9, -1.2, 0.75), 35), 10)               # 3 light line
C.cut(C.camera("cam4_dash", (DASH[0] + 0.2, -2.4, 0.05), DASH, 35), 14)                       # 4 dashboard wakes
c5 = C.camera("cam5_rear", (0.7, -7.2, 0.35), (0.5, -3.6, 0.38), 24)                    # 5 blue flames
C.shake(c5, 0.03, 1.5, F(18), F(22))
C.cut(c5, 18)
C.cut(C.camera("cam6_out", (-1.6, -6.8, 1.6), (0, 9, 1.7), 24), 22)                     # 6+7 shutter, exit
c8 = C.camera("cam8_wall", (-2.6, -5.6, 2.35), (-2.6, -8.8, 2.35), 35)                 # 8 the 13 photos
tgt = C.cam_target(c8)
C.key(c8, "location", [(F(31), (-2.6, -5.6, 2.35)), (F(35), (2.6, -5.6, 2.35))], "LINEAR")
C.key(tgt, "location", [(F(31), (-2.6, -8.8, 2.35)), (F(35), (2.6, -8.8, 2.35))], "LINEAR")
C.cut(c8, 31)
title_m = C.glow("title_m", (1.0, 0.08, 0.05), 0.0)
C.text("title", "Next?", (0, -0.5, -2.2), 0.28, title_m, rot=(0, 0, 0), parent=c8)
C.glitch_in(title_m, F(33), 10.0)

C.finish(NAME, opts)
