"""Short 3 – "Pahad Ka Mod" (40 sec).

Pahadi hairpins. Roadster drift karti hai; agle mod par GHOST pehle se khadi,
neeli headlights. Race — aakhri mod par GHOST railing ke upar se khai mein, badalon mein gayab.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C  # noqa: E402

NAME = "short3"
opts = C.cli()
C.reset()
sc = C.setup(NAME, 40, opts["preview"])
C.world_hdri("moonless_golf_1k.hdr", 0.8, 3.6, color=(0.012, 0.016, 0.03), top=(0.025, 0.035, 0.08))
C.sun(0.35, (1.0, 0.1, 2.4), (0.65, 0.75, 1.0))          # moonlight over the khai
F = C.f

# --------------------------------------------------------------- mountain road
ROAD = [(0, -20, 100), (0, 150, 100), (20, 182, 92.5), (40, 150, 85), (40, 0, 85),
        (60, -32, 77.5), (80, 0, 70), (80, 150, 70), (100, 182, 62.5), (120, 150, 55),
        (120, 80, 55), (116, 50, 55), (110, 20, 55), (110, -40, 55)]
road_path = C.Path("mountain_road", ROAD)
asphalt = C.surface("asphalt", (0.018, 0.018, 0.02), (0.04, 0.04, 0.042), (0.35, 0.75), 0.2, 0.06, 40)
paint = C.mat("paint", (0.85, 0.82, 0.7), 0.0, 0.5)
C.road("road", road_path, 8.0, asphalt)
C.dashes("center", road_path, 0.0, 9, 3, 0.14, paint)

TERRACES = [(0, 100), (40, 85), (80, 70)]          # (x, z) of the straight legs
RAIL_X = 126.5


def height(x, y):
    """Terraced mountain: flat shelves under each leg, slopes between, a sheer drop past leg 3."""
    edges = []
    for xk, zk in TERRACES:
        edges += [(xk - 7, zk - 0.3), (xk + 7, zk - 0.3)]
    edges += [(103, 54.7), (127.5, 54.7)]
    if x < edges[0][0]:
        z = 99.7 + (edges[0][0] - x) * 0.9
        amp = 6
    elif x > edges[-1][0]:
        z = max(-70.0, 54.7 - (x - edges[-1][0]) * 7) + C.smoothstep(330, 430, x) * 190
        amp = 10
    else:
        z, amp = 54.7, 0.0
        for (x0, z0), (x1, z1) in zip(edges, edges[1:]):
            if x0 <= x <= x1:
                z = z0 + (z1 - z0) * (x - x0) / (x1 - x0)
                amp = 0.0 if z0 == z1 else 2.0
                break
    return z + amp * C.fbm(x, y, 0.03)


rock = C.surface("rock", (0.035, 0.035, 0.04), (0.10, 0.095, 0.09), (0.6, 0.95), 0.6, 0.05, 4)
C.grid("mountain", 600, 520, 150, 130, height, (130, 50, 0), rock)

# railing along the khai side of the last leg
steel = C.mat("steel", (0.5, 0.5, 0.52), 1.0, 0.35)
reflector = C.glow("reflector", (1.0, 0.5, 0.1), 3.0)
for i, y in enumerate(range(-40, 151, 3)):
    C.box(f"post{i}", (0.12, 0.12, 1.0), (RAIL_X, y, 55.5), steel)
    if i % 4 == 0:
        C.box(f"refl{i}", (0.02, 0.1, 0.1), (RAIL_X - 0.08, y, 55.9), reflector)
C.box("rail", (0.08, 191, 0.28), (RAIL_X, 55.5, 55.85), steel)

# clouds filling the khai
C.fog_box("clouds", (320, 520, 90), (290, 30, -15), 0.35, (0.9, 0.92, 1.0), True, 0.025)

# --------------------------------------------------------------- cars
d_h1 = road_path.nearest(ROAD[2])
d_h2 = road_path.nearest(ROAD[5])
d_g0 = road_path.nearest(ROAD[6])
d_l3 = road_path.nearest(ROAD[10])
PARK = d_g0 + 12                                   # where the GHOST waits

roadster = C.Car("roadster", "roadster")
ghost = C.Car("ghost", "ghost", head_color=(0.25, 0.45, 1.0), head_on=False)
ghost.rim_light(140)

roadster.drive(road_path, [(F(0), d_h1 - 75), (F(3), d_h1 - 32), (F(6), d_h1), (F(9), d_h1 + 40),
                           (F(13), d_h1 + 120), (F(16.5), PARK - 32), (F(18), PARK - 9), (F(21), PARK - 9),
                           (F(24), PARK + 40), (F(30), d_l3 - 10), (F(33), d_l3 + 40), (F(35), d_l3 + 55),
                           (F(40), d_l3 + 55)], lane=2.0)
# drift: extra yaw on top of Follow Path (hairpin 1 turns right, hairpin 2 turns left)
C.key(roadster.root, "rotation_euler", [(F(3), (0, 0, 0)), (F(4.5), (0, 0, -0.45)), (F(7), (0, 0, -0.55)),
                                        (F(8.5), (0, 0, -0.1)), (F(9.2), (0, 0, 0)),
                                        (F(15), (0, 0, 0)), (F(15.8), (0, 0, 0.3)), (F(16.6), (0, 0, 0))])

ghost_path = C.Path("ghost_line", [(80, 0, 70), (80, 150, 70), (100, 182, 62.5), (120, 150, 55), (120, 80, 55),
                                   (121.5, 55, 55.2), (124.5, 38, 56.3), (128, 25, 57.0), (136, 10, 56.5),
                                   (146, -5, 52), (160, -25, 40), (175, -45, 22), (190, -65, 0), (205, -85, -25)])
g_park = PARK - d_g0
g_rail = ghost_path.nearest((124.5, 38, 56.3))
ghost.drive(ghost_path, [(F(0), g_park), (F(21), g_park), (F(24), g_park + 45), (F(30), d_l3 - 5 - d_g0),
                         (F(32.6), g_rail), (F(35), g_rail + 20), (F(37), g_rail + 100)], lane=-2.0)
ghost.headlights([(F(0), 0), (F(18.6), 0), (F(19.0), 1.0)], strength=50, spot=2500)
C.visible(ghost.root, [(F(0), True), (F(37), False)])

# tyre marks + dust from the drift
marks = C.mat("tyre_marks", (0.004, 0.004, 0.004), 0.0, 0.9, alpha=0.7)
for lat in (2.0 - 0.83, 2.0 + 0.83):
    C.dashes(f"marks{lat}", road_path, lat, 1.0, 1.0, 0.22, marks, d_h1 - 25, d_h1 + 38, 0.012)
for sx in (-1, 1):
    C.smoke(f"dust{sx}", (sx * 0.8, -1.6, 0.2), roadster.root, F(3.5), F(9), 900, (0.45, 0.42, 0.38),
            (sx * 2.0, -2, 1.0), 1.0, 70, 0.1, 0.6)

# --------------------------------------------------------------- shots
# 1 0:00–0:03  looking straight down into the khai, tilt up to the road
c1 = C.camera("cam1_khai", (165, -10, 95), (168, -15, 0), 24)
C.key(C.cam_target(c1), "location", [(F(0), (168, -15, 0)), (F(3), (118, 70, 56))])
C.cut(c1, 0)
# 2 0:03–0:09  drone above hairpin 1, drift
C.cut(C.camera("cam2_drone", (20, 140, 128), (20, 170, 93), 24), 3)
# 3 0:09–0:13  tyre marks and dust settling
C.cut(C.camera("cam3_marks", tuple(road_path.point(d_h1 + 30, 3.2, 0.4)), tuple(road_path.point(d_h1 + 8, 2, 0)), 28), 9)
# 4 0:13–0:18  Roadster POV round hairpin 2 — the GHOST is already waiting
C.cut(C.camera("cam4_pov", (0.35, 0.6, 1.15), (0.35, 30, 0.9), 24, roadster.root), 13)
# 5 0:18–0:21  GHOST front, blue headlights ignite
C.cut(C.camera("cam5_lights", (0.5, 6.5, 0.7), (0, 0, 0.6), 50, ghost.root), 18)
# 6 0:21–0:30  side by side through the bends, three angles
C.cut(C.camera("cam6a_side", (9, 2, 1.6), (2.5, 0, 0.7), 30, ghost.root), 21)
C.cut(C.camera("cam6b_front", (-0.5, 11, 1.0), (-2, 0, 0.7), 35, roadster.root), 24)
C.cut(C.camera("cam6c_drone", (2, -16, 9), (2, 10, 0), 28, ghost.root), 27)
# 7 0:30–0:35  over the railing, slow-mo flight
C.cut(C.camera("cam7_flight", (146, 66, 63), (128, 26, 56.5), 50), 30)
# 8 0:35–0:40  over the Roadster: only clouds below + title
khai = C.target("khai", (185, -45, 15))
c8 = C.camera("cam8_over", (3.5, 1.0, 2.6), khai, 30, roadster.root)
C.cut(c8, 35)
title_m = C.glow("title_m", (0.4, 0.6, 1.0), 0.0)
C.text("title", "THE GHOST", (0, 0.3, -3), 0.24, title_m, rot=(0, 0, 0), parent=c8)
C.glitch_in(title_m, F(37), 10.0)

C.finish(NAME, opts)
