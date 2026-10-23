"""Short 5 – "75 Meter" (45 sec) — Episode 1 teaser.

Registaan, toota pul, beech mein 75 m ki canyon gap. Charger aur GHOST full speed.
Charger aakhri second par brake. GHOST ramp se udti hai — slow-mo… screen black.
Landing nahi dikhate: cliffhanger.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C  # noqa: E402

NAME = "short5"
opts = C.cli()
C.reset()
sc = C.setup(NAME, 45, opts["preview"])
C.world((0.95, 0.5, 0.25), 0.8, fog=0.0015, fog_color=(1.0, 0.7, 0.45), top=(0.12, 0.2, 0.42))
C.sun(4.5, (1.42, 0.0, 2.6), (1.0, 0.72, 0.48))          # low sunset sun
F = C.f

NEAR, FAR = 950.0, 1110.0                                 # canyon rims (y)
DECK_END, FAR_DECK = 1000.0, 1075.0                       # broken bridge: 75 m gap
DEPTH = -150.0

# --------------------------------------------------------------- desert + canyon
sand = C.mat("sand", (0.62, 0.38, 0.2), 0.0, 0.9)
rock = C.mat("canyon_rock", (0.32, 0.14, 0.07), 0.0, 0.85)


def ground(x, y):
    if NEAR < y < FAR:
        return DEPTH + 12 * C.fbm(x, y, 0.02)
    dunes = 5 + 9 * C.fbm(x, y, 0.003) + 1.5 * C.fbm(x, y, 0.03)
    return -0.3 + C.smoothstep(9, 45, abs(x)) * max(0.0, dunes)


C.grid("desert", 2000, 2400, 200, 240, ground, (0, 0, 0), sand)
for i in range(7):                                        # far mesas
    x = random.choice((-1, 1)) * random.uniform(300, 900)
    y = random.uniform(-400, 2200)
    w, d, h = random.uniform(80, 220), random.uniform(80, 220), random.uniform(40, 120)
    C.box(f"mesa{i}", (w, d, h), (x, y, h / 2 - 2), rock, bevel=6)
for y0 in (NEAR, FAR):                                     # visible rock faces at both rims
    C.box(f"rim{y0}", (2000, 6, 150), (0, y0 + (3 if y0 == NEAR else -3), DEPTH / 2), rock)

# --------------------------------------------------------------- road + broken bridge
ROAD = [(0, -600, 0), (0, 200, 0), (0, 700, 0), (0, 940, 0), (0, 990, 0), (0, 1000, 1.2)]
road_path = C.Path("desert_road", ROAD)
asphalt = C.mat("asphalt", (0.05, 0.045, 0.04), 0.0, 0.6)
paint = C.mat("paint", (0.85, 0.75, 0.4), 0.0, 0.5)
d_near = road_path.nearest((0, NEAR, 0))
C.road("road", road_path, 8.0, asphalt, 0, d_near)
C.dashes("center", road_path, 0.0, 12, 4, 0.15, paint, 0, d_near)
concrete = C.mat("bridge_concrete", (0.4, 0.36, 0.32), 0.0, 0.8)
C.loft("deck_near", road_path, [(-4.6, -0.8), (-4.6, 0.0), (4.6, 0.0), (4.6, -0.8), (-4.6, -0.8)],
       d_near - 2, road_path.length, 1.0, concrete)
C.box("deck_far", (9.2, FAR + 5 - FAR_DECK, 0.8), (0, (FAR + 5 + FAR_DECK) / 2, -0.4), concrete)
for i in range(6):                                         # snapped concrete chunks at both ends
    for y_end, s in ((DECK_END, 1), (FAR_DECK, -1)):
        C.box(f"chunk{y_end}{i}", (random.uniform(0.6, 1.6), random.uniform(0.8, 2.0), random.uniform(0.4, 0.9)),
              (random.uniform(-4, 4), y_end + s * random.uniform(-2.5, 0.5), random.uniform(-1.2, -0.3)), concrete,
              rot=(random.uniform(-0.6, 0.6), random.uniform(-0.4, 0.4), random.uniform(-0.5, 0.5)))
for y in (968.0, 1094.0):
    for sx in (-1, 1):
        C.box(f"pillar{y}{sx}", (1.6, 1.6, -DEPTH), (sx * 3.2, y, DEPTH / 2 - 0.8), concrete)
rebar = C.mat("rebar", (0.2, 0.08, 0.04), 0.8, 0.5)
for i in range(10):
    for y_end, s in ((DECK_END, 1), (FAR_DECK, -1)):
        C.box(f"rebar{y_end}{i}", (0.03, random.uniform(1, 3), 0.03), (-4 + i * 0.9, y_end + s * 0.8, -0.3), rebar,
              rot=(random.uniform(-0.7, 0.2), 0, random.uniform(-0.2, 0.2)))

# "75 m" callout over the gap (shot 1 only)
callout_m = C.glow("callout", (1.0, 0.9, 0.75), 6.0)
cam1_loc = (40, 990, 40)
label_loc = (0, (DECK_END + FAR_DECK) / 2, 13)
yaw = math.atan2(cam1_loc[0] - label_loc[0], -(cam1_loc[1] - label_loc[1]))
label = C.text("label_75m", "75 m", label_loc, 6.0, callout_m, rot=(math.pi / 2, 0, yaw), extrude=0.2)
dim = [label, C.box("dim_line", (0.25, FAR_DECK - DECK_END, 0.25), (0, (DECK_END + FAR_DECK) / 2, 8), callout_m)]
for y in (DECK_END, FAR_DECK):
    dim.append(C.box(f"dim_tick{y}", (0.25, 0.25, 4), (0, y, 8), callout_m))
C.visible(dim, [(F(0), True), (F(4), False)])

# --------------------------------------------------------------- cars
SPEED = 44.0                                               # 160 km/h
T_JUMP = 28.8
ghost_path = C.Path("ghost_line", ROAD + [(0, 1015, 4.5), (0, 1035, 6.8), (0, 1055, 6.2), (0, 1075, 3.5),
                                          (0, 1095, -2.0)])
EDGE_G = ghost_path.nearest((0, DECK_END, 1.2))
EDGE = road_path.nearest((0, DECK_END, 1.2))
charger = C.Car("charger", "charger")
ghost = C.Car("ghost", "ghost", head_color=(0.25, 0.45, 1.0), head_on=False, spots=False)
ghost.rim_light(200, (1.0, 0.75, 0.5))
start = EDGE - SPEED * T_JUMP
ghost.drive(ghost_path, [(F(0), EDGE_G - SPEED * T_JUMP), (F(T_JUMP), EDGE_G), (F(29.4), EDGE_G + 26),
                         (F(40), EDGE_G + 44)], lane=-2.0)
D = start + SPEED * 19                                    # where the Charger starts braking
charger.drive(road_path, [(F(0), start), (F(19), D), (F(20), D + 40), (F(21), D + 72), (F(22), D + 95),
                          (F(23), D + 108), (F(24), D + 114), (F(24.5), D + 115), (F(45), D + 115)], lane=2.0)

for nm, car in (("charger", charger), ("ghost", ghost)):
    for sx in (-1, 1):
        C.smoke(f"{nm}_dust{sx}", (sx * 0.9, -2.0, 0.2), car.root, F(0), F(T_JUMP), 2500, (0.75, 0.55, 0.38),
                (sx * 1.5, -6, 1.5), 1.4, 75, 0.12, 0.6)
for sx in (-1, 1):
    C.smoke(f"brake_smoke{sx}", (sx * 0.95, 1.6, 0.2), charger.root, F(19), F(23.5), 900, (0.85, 0.85, 0.85),
            (sx * 1.0, -1, 1.0), 1.0, 60, 0.15, 0.5)
C.key_emit(charger.tail, [(F(18.9), 12), (F(19), 45), (F(30), 45)], "CONSTANT")   # brake lights

DASH = (5000, 0, 0)
pivot = C.dashboard("speedo", DASH)
C.needle(pivot, [(F(10), 158), (F(11), 161), (F(12), 159), (F(13), 163), (F(14), 160)])

# black card for the ending
VOID = (0, 0, -3000)
void_m = C.glow("void", (0, 0, 0), 0.0)
C.box("void_box", (40, 40, 40), VOID, void_m)
end_m = C.glow("end_text", (1.0, 1.0, 1.0), 0.0)

# --------------------------------------------------------------- shots
c1 = C.camera("cam1_gap", cam1_loc, (0, 1037, 0), 24)                                   # 1 the gap, "75 m"
C.key(c1, "location", [(F(0), cam1_loc), (F(4), (30, 1006, 43))])
C.cut(c1, 0)
C.cut(C.camera("cam2_side", (-26, 4, 3.0), (2, 0, 0.8), 35, ghost.root), 4)              # 2 two cars, dust
C.cut(C.camera("cam3_dash", (DASH[0] + 0.1, -1.3, 0.05), DASH, 50), 10)                  # 3 160 km/h
C.cut(C.camera("cam4_pov", (0.4, 2.7, 0.95), (0.4, 80, 0.3), 50, charger.root), 14)       # 4 the bridge nears
C.cut(C.camera("cam5_brake", tuple(road_path.point(D + 132, 3.6, 0.4)),                   # 5 Charger brakes
               tuple(road_path.point(D + 112, 2.0, 0.6)), 35), 19)
C.cut(C.camera("cam6_launch", (62, 972, 9), (0, 1004, 2.5), 35), 24)                      # 6 launch, real speed
C.cut(C.camera("cam7_under", (6, 1030, -14), ghost.root, 24), 30)                         # 7 slow-mo from below
c8 = C.camera("cam8_black", VOID, (VOID[0], VOID[1] + 10, VOID[2]), 35)                   # 8 cut to black
C.cut(c8, 40)
C.text("end_title", "Episode 1 – jald aa raha hai", (0, 0, -4), 0.2, end_m, rot=(0, 0, 0), parent=c8)
C.key_emit(end_m, [(F(40.6), 0), (F(41.2), 6)])

C.finish(NAME, opts)
