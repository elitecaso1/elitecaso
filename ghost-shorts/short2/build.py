"""Short 2 – "Signal Laal Hai" (30 sec).

Raat 3 baje khaali chauraha. Charger, Roadster aur pickup signal par. Countdown
3…2…1, beech ki lane mein fog se GHOST aakar rukti hai. Green — sabse aage GHOST.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C  # noqa: E402

NAME = "short2"
opts = C.cli()
C.reset()
sc = C.setup(NAME, 30, opts["preview"])
C.world((0.004, 0.005, 0.009), 1.0, fog=0.004, fog_color=(0.55, 0.6, 0.7), top=(0.01, 0.012, 0.025))
F = C.f

# --------------------------------------------------------------- city block
main = C.Path("main_road", [(0, -320, 0), (0, 0, 0), (0, 400, 0), (0, 900, 0)])
STOP = main.nearest((0, 0, 0))                      # stop line at y = 0
asphalt = C.mat("asphalt", (0.018, 0.018, 0.02), 0.0, 0.35)
paint = C.mat("paint", (0.85, 0.85, 0.8), 0.0, 0.5)
C.road("main", main, 14.0, asphalt)
for lat in (-3.5, 3.5):
    C.dashes(f"lane{lat}", main, lat, 10, 3, 0.14, paint)
C.box("double_yellow", (0.3, 1200, 0.02), (0, 290, 0.02), C.mat("yellow", (0.8, 0.55, 0.05), 0, 0.5))
C.box("cross_road", (600, 14, 0.04), (0, 20, -0.01), asphalt)
C.box("stop_line", (14, 0.5, 0.03), (0, 0.4, 0.03), paint)
for i in range(10):                                  # zebra crossing
    C.box(f"zebra{i}", (0.8, 4.0, 0.03), (-6.3 + i * 1.4, 4.0, 0.03), paint)
C.box("ground", (1200, 1600, 0.2), (0, 300, -0.35), C.mat("pavement", (0.03, 0.03, 0.032), 0, 0.8))

# buildings with lit windows on all four corners
wall = C.mat("building", (0.02, 0.022, 0.026), 0.1, 0.7)
window_on = C.glow("window_on", (1.0, 0.75, 0.45), 4.0)
window_blue = C.glow("window_blue", (0.4, 0.6, 1.0), 3.0)
for bx in (-1, 1):
    for by, y0 in ((-1, -260), (1, 40)):
        y = y0
        while y < y0 + 220:
            w, d, h = random.uniform(14, 24), random.uniform(16, 28), random.uniform(12, 55)
            x = bx * (14 + w / 2 + random.uniform(0, 4))
            C.box(f"bld{bx}{by}{int(y)}", (w, d, h), (x, y + d / 2, h / 2), wall)
            for k in range(int(h // 4)):
                for j in range(int(d // 4)):
                    if random.random() < 0.22:
                        C.box(f"win{bx}{int(y)}{k}{j}", (0.05, 1.4, 1.6),
                              (x - bx * (w / 2 + 0.01), y + 2 + j * 4, 3 + k * 4),
                              window_on if random.random() < 0.8 else window_blue)
            y += d + random.uniform(2, 8)
lamp_m = C.glow("lamp_m", (1.0, 0.6, 0.28), 20)
for i, (x, y) in enumerate(((-8.5, -30), (8.5, -30), (-8.5, 30), (8.5, 30), (-8.5, -90), (8.5, -90))):
    C.box(f"pole{i}", (0.18, 0.18, 9), (x, y, 4.5), wall)
    C.box(f"lamp{i}", (1.2, 0.4, 0.15), (x * 0.85, y, 9), lamp_m)
    C.light(f"lamp_light{i}", "SPOT", 6000, (x * 0.85, y, 8.8), (1.0, 0.6, 0.28), 0.4, spot=1.6)

# fog bank the GHOST drives out of
C.fog_box("fog_bank", (30, 160, 8), (0, -110, 4), 0.25, (0.6, 0.65, 0.72), True, 0.08)

# --------------------------------------------------------------- traffic signal
house_m = C.mat("signal_house", (0.02, 0.02, 0.02), 0.4, 0.5)
C.box("signal_pole", (0.25, 0.25, 6.5), (8.2, 6.5, 3.25), house_m)
C.box("signal_arm", (8.5, 0.2, 0.2), (4.0, 6.5, 6.4), house_m)
C.box("signal_house", (0.7, 0.6, 2.1), (0.6, 6.5, 5.6), house_m, bevel=0.05)
red = C.glow("sig_red", (1.0, 0.03, 0.02), 0.0)
amber = C.glow("sig_amber", (1.0, 0.45, 0.02), 0.0)
green = C.glow("sig_green", (0.1, 1.0, 0.3), 0.0)
for z, m, nm in ((6.25, red, "red"), (5.6, amber, "amber"), (4.95, green, "green")):
    C.cylinder("lamp_" + nm, 0.24, 0.05, (0.6, 6.18, z), m, axis="Y")
C.key_emit(red, [(F(0), 25), (F(17), 25), (F(17) + 1, 0), (F(25), 0), (F(26), 25)], "CONSTANT")
C.key_emit(green, [(F(0), 0), (F(17), 0), (F(17) + 1, 30), (F(25), 30), (F(25) + 1, 0)], "CONSTANT")
C.key_emit(amber, [(F(0), 0), (F(25), 0), (F(25) + 1, 25), (F(26), 0)], "CONSTANT")
red_spill = C.light("red_spill", "POINT", 300, (0.6, 5.6, 5.8), (1.0, 0.05, 0.03), 0.4)
C.key(red_spill.data, "color", [(F(0), (1.0, 0.05, 0.03)), (F(17) + 1, (0.1, 1.0, 0.3)),
                                (F(25) + 1, (1.0, 0.45, 0.02)), (F(26), (1.0, 0.05, 0.03))], "CONSTANT")

# countdown display under the signal
C.box("count_box", (0.9, 0.3, 0.9), (0.6, 6.5, 3.9), house_m, bevel=0.04)
digit_m = C.glow("digit_m", (1.0, 0.1, 0.05), 18.0)
digits = []
for n, (t0, t1) in zip("321", ((0, 7), (7, 14), (14, 17))):
    d = C.text(f"digit{n}", n, (0.6, 6.33, 3.88), 0.7, digit_m, extrude=0.01)
    C.visible(d, [(F(0), False), (F(t0), True), (F(t1), False)])
    digits.append(d)

# --------------------------------------------------------------- cars
lanes = {"charger": -5.25, "ghost": -1.75, "roadster": 1.75, "pickup": 5.25}
cars = {"charger": C.Car("charger", "charger"), "roadster": C.Car("roadster", "roadster"),
        "pickup": C.Car("pickup", "pickup"),
        "ghost": C.Car("ghost", "ghost", head_color=(0.3, 0.5, 1.0), head_on=False, spots=False)}
cars["ghost"].rim_light(150)
WAIT = STOP - 3.0                                   # car centre just behind the stop line
accel = {"ghost": 9.0, "charger": 7.2, "roadster": 7.6, "pickup": 5.5}


def race(a, t0=17.0):
    keys = [(F(0), WAIT), (F(t0), WAIT)]
    for i in range(1, 10):
        keys.append((F(t0 + i), WAIT + 0.5 * a * i * i))
    return keys


for nm in ("charger", "roadster", "pickup"):
    car = cars[nm]
    car.drive(main, race(accel[nm]), lanes[nm])
    car.vibrate(F(0), F(17))
    C.visible(car.root, [(F(0), True), (F(26), False)])
g = cars["ghost"]
g.drive(main, [(F(0), WAIT - 160), (F(10), WAIT - 160), (F(11.5), WAIT - 60), (F(12.8), WAIT - 12),
               (F(13.5), WAIT - 2), (F(14), WAIT), (F(17), WAIT)] + race(accel["ghost"])[2:], lanes["ghost"])
g.vibrate(F(14), F(17))
C.visible(g.root, [(F(0), False), (F(10), True), (F(26), False)])

# exhaust breath on "2", burnout smoke on green
for nm, car in cars.items():
    for i, ex in enumerate(car.exhausts):
        C.smoke(f"{nm}_exhaust{i}", tuple(ex), car.root, F(7), F(17), 300, (0.5, 0.5, 0.55), (0, -1.5, 0.6),
                0.25, 40, 0.08)
    for sx in (-1, 1):
        C.smoke(f"{nm}_burnout{sx}", (sx * 0.95, -1.6, 0.2), car.root, F(17), F(21), 900,
                (0.75, 0.75, 0.78), (sx * 1.5, -3, 1.2), 0.9, 60, 0.12, 0.5)

# --------------------------------------------------------------- shots
c1 = C.camera("cam1_signal", (0.6, 3.0, 4.6), (0.6, 6.5, 4.8), 50)
C.cut(c1, 0)                                                       # 1 "3" close-up
C.cut(C.camera("cam2_front", (0, 13, 0.6), (0, -3, 0.9), 24), 3)   # 2 line-up, idling
ch = cars["charger"].root
C.cut(C.camera("cam3_rear", (0.6, -4.6, 0.45), (0.5, -2.5, 0.35), 28, ch), 7)     # 3 "2", exhaust
C.cut(C.camera("cam4_top", (-1.75, -45, 70), (-1.75, -35, 0), 30), 10)              # 4 GHOST out of fog
YW = main.point(WAIT).y
c5 = C.camera("cam5_push", (16, YW, 1.3), (0, YW, 1.1), 35)                            # 5 "1", push-in
C.key(c5, "location", [(F(14), (16, YW, 1.3)), (F(17), (8.5, YW, 1.2))])
C.cut(c5, 14)
C.cut(C.camera("cam6_wheel", (-2.2, -2.6, 0.45), (-0.95, -1.55, 0.36), 24, ch), 17)  # 6 green, wheels
C.cut(C.camera("cam7_drone", (1.75, -26, 9), (1.75, 12, 0), 30, g.root), 20)          # 7 race, GHOST ahead
C.cut(c1, 26)                                                                         # 8 red again, loop
c8_fill = C.camera("cam8_wide", (14, -24, 6), (0, 6, 3), 28)                          # wider alt angle
C.cut(c8_fill, 27.5)

C.finish(NAME, opts)
