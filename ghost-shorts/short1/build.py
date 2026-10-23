"""Short 1 – "Mirror Mein Kuch Hai" (35 sec).

Baarish wali raat, highway par laal Charger. Mirror mein bina headlights wali
kaali car, overtake, tunnel mein gayab. Tunnel ke dusre end se koi nahi nikalta.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C  # noqa: E402

NAME = "short1"
opts = C.cli()
C.reset()
sc = C.setup(NAME, 35, opts["preview"])
C.world_hdri("moonless_golf_1k.hdr", 0.6, 1.2, color=(0.003, 0.004, 0.008), top=(0.010, 0.014, 0.028))
C.sun(0.06, (1.1, 0.0, 0.9), (0.6, 0.7, 1.0))           # moonlight

# --------------------------------------------------------------- world
road_path = C.Path("highway", [(0, -100, 0), (0, 300, 0), (60, 700, 0), (-40, 1100, 0),
                               (0, 1450, 0), (0, 1700, 0), (0, 1950, 0)])
T_IN, T_OUT = 1480.0, 1660.0                            # tunnel span (metres along road)
asphalt = C.surface("asphalt_wet", (0.010, 0.010, 0.011), (0.028, 0.028, 0.03), (0.03, 0.4), 0.15, 0.08, 40, puddles=True)
paint = C.mat("lane_paint", (0.8, 0.8, 0.75), 0.0, 0.5)
C.road("road", road_path, 8.0, asphalt)
C.dashes("center_line", road_path, 0.0, 12, 4, 0.15, paint)
for side in (-1, 1):
    C.dashes(f"edge_line{side}", road_path, side * 3.85, 1.0, 1.0, 0.12, paint)

ground = C.surface("ground", (0.012, 0.016, 0.010), (0.03, 0.028, 0.02), (0.6, 0.95), 0.4, 0.02, 3)
concrete = C.surface("concrete", (0.09, 0.09, 0.088), (0.16, 0.155, 0.15), (0.5, 0.9), 0.2, 0.3, 12)


C.corridor_terrain("terrain", road_path, 900, 2300, 90, 230, (0, 900), flat=16, ramp=140, hmax=55, m=ground)
# hill over the tunnel: a mound swept along the tunnel span (always above the tube)
C.loft("tunnel_hill", road_path, [(-70, -0.3), (-34, 9), (-14, 15), (0, 17), (14, 15), (34, 9), (70, -0.3)],
       T_IN, T_OUT, 6.0, ground)

# street lamps: emissive heads, a real light every 4th lamp
lamp_m = C.glow("lamp_glow", (1.0, 0.62, 0.3), 25.0)
for i, d in enumerate(C.along(road_path, 50, 0, T_IN - 30)):
    p, fwd, side = road_path.frame(d)
    base = p + side * 5.2
    C.box(f"pole{i}", (0.15, 0.15, 8), (base.x, base.y, 4), concrete)
    C.box(f"lamp{i}", (0.9, 0.35, 0.12), (base.x - side.x * 0.8, base.y - side.y * 0.8, 8), lamp_m)
    if i % 4 == 0:
        C.light(f"lamp_light{i}", "POINT", 1500, (base.x - side.x * 0.8, base.y - side.y * 0.8, 7.6),
                (1.0, 0.62, 0.3), 0.3)

# tunnel tube, portals and the ceiling strips that switch off one by one
C.loft("tunnel", road_path, [(-6.2, -0.3), (-6.2, 5.0), (-4.6, 6.6), (4.6, 6.6), (6.2, 5.0), (6.2, -0.3)],
       T_IN, T_OUT, 3.0, concrete)
for tag, d in (("in", T_IN), ("out", T_OUT)):
    p, fwd, side = road_path.frame(d)
    yaw = math.atan2(-fwd.x, fwd.y)
    for nm, lat, w, z, h in (("L", -14.5, 16, 9, 18), ("R", 14.5, 16, 9, 18), ("T", 0, 13, 12.3, 11.4)):
        c = p + side * lat
        C.box(f"portal_{tag}{nm}", (w, 1.5, h), (c.x, c.y, z), concrete, rot=(0, 0, yaw))
strips = []
for i, d in enumerate(C.along(road_path, 15, T_IN + 8, T_OUT - 5)):
    p, fwd, side = road_path.frame(d)
    m = C.glow(f"tunnel_strip{i}", (1.0, 0.78, 0.45), 14.0)
    C.box(f"strip{i}", (0.5, 3.0, 0.08), (p.x, p.y, 6.55), m, rot=(0, 0, math.atan2(-fwd.x, fwd.y)))
    lt = C.light(f"strip_light{i}", "POINT", 600, (p.x, p.y, 6.0), (1.0, 0.78, 0.45), 0.5)
    strips.append((m, lt))
# far end goes dark first, then each strip towards the camera
for k, (m, lt) in enumerate(reversed(strips)):
    t_off = C.f(27.2 + k * 0.28)
    C.key_emit(m, [(t_off - 1, 14.0), (t_off, 0.0)], "CONSTANT")
    C.key(lt.data, "energy", [(t_off - 1, 600), (t_off, 0)], "CONSTANT")

# --------------------------------------------------------------- cars
charger = C.Car("charger", "charger")
ghost = C.Car("ghost", "ghost", head_color=(1.0, 0.02, 0.02), head_on=False, spots=False)
ghost.rim_light(30)
F = C.f
charger.drive(road_path, [(F(0), 200), (F(3), 320), (F(7), 500), (F(11), 700), (F(16), 950),
                          (F(21), 1200), (F(26), 1375), (F(31), 1500), (F(35), 1600)], lane=1.9)
ghost.drive(road_path, [(F(0), 110), (F(11), 650), (F(16), 950), (F(21), 1200), (F(24), 1360),
                        (F(26.9), 1480), (F(28.5), 1570), (F(35), 1600)], lane=-1.9)
# red "eyes" wake up in the mirror, then stay as a dim glow (no headlights)
ghost.headlights([(F(0), 0), (F(1.2), 0), (F(1.8), 1.0), (F(3), 1.0), (F(3.2), 0.2)], strength=30)
C.visible(ghost.root, [(F(0), True), (F(28.5), False)])   # gone inside the tunnel

C.smoke("spray", (0, -2.4, 0.25), ghost.root, F(0), F(28.5), 4000, (0.7, 0.75, 0.8), (0, -14, 2.5),
        0.35, 14, 0.18, 1.6)
C.rain(charger.root, F(0), F(35), count=45000)
C.rain(None, F(25), F(35), (40, 60), origin=tuple(road_path.point(1450)), count=15000, name="rain_t_in")
C.rain(None, F(30), F(35), (40, 60), origin=tuple(road_path.point(1690)), count=12000, name="rain_t_out")

# speedometer set (lives far away from the highway)
DASH = (5000, 0, 0)
pivot = C.dashboard("speedo", DASH)
C.needle(pivot, [(F(7), 148), (F(8.5), 160), (F(10), 176), (F(10.6), 182), (F(11), 180)])

# --------------------------------------------------------------- shots
# 1 0:00–0:03  mirror close-up, two red lights appear
c1 = C.camera("cam1_mirror", (-1.15, 0.9, 1.0), (-1.6, -60, 1.0), 85, charger.root)
C.cut(c1, 0)
# 2 0:03–0:07  drone behind and above
C.cut(C.camera("cam2_drone", (0, -16, 7), (0, 8, 0), 28, charger.root), 3)
# 3 0:07–0:11  speedometer to 180
c3 = C.camera("cam3_dash", (DASH[0] + 0.25, -2.4, 0.1), DASH, 35)
C.shake(c3, 0.004, 2, F(7), F(11))
C.cut(c3, 7)
# 4 0:11–0:16  road level, GHOST closes in without lights
C.cut(C.camera("cam4_low", (1.0, -3.2, 0.35), ghost.root, 35, charger.root), 11)
# 5 0:16–0:21  side tracking, tinted window, nobody inside
key5 = C.light("ghost_side_key", "AREA", 0, (-3.5, 0.5, 2.2), (0.6, 0.7, 1.0), 3.0, (0, -1.0, 0), ghost.root)
C.key(key5.data, "energy", [(F(15.9), 0), (F(16), 260), (F(21), 260), (F(21.1), 0)], "CONSTANT")
C.cut(C.camera("cam5_side", (-4.5, 0.8, 1.1), (0, 0, 0.9), 35, ghost.root), 16)
# 6 0:21–0:26  front wide, GHOST pulls away, spray over the Charger
C.cut(C.camera("cam6_front", (-1.0, 18, 1.6), (0, 0, 0.6), 28, charger.root), 21)
# 7 0:26–0:31  outside the tunnel, lights die one by one
C.cut(C.camera("cam7_tunnel", tuple(road_path.point(1440, -9, 2.2)), tuple(road_path.point(1500, 0, 3)), 35), 26)
# 8 0:31–0:35  other end: empty road + title
c8 = C.camera("cam8_exit", tuple(road_path.point(1705, 1.5, 1.6)), tuple(road_path.point(1660, 0, 2.6)), 35)
C.cut(c8, 31)
title_m = C.glow("title_m", (1.0, 0.08, 0.05), 0.0)
C.text("title", "THE GHOST", (0, 0.35, -3), 0.26, title_m, rot=(0, 0, 0), parent=c8)
C.glitch_in(title_m, F(32.5), 10.0)

C.finish(NAME, opts)
