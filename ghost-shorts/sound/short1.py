"""Sound for Short 1 – "Mirror Mein Kuch Hai" (35 s). Timings follow short1/build.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as S  # noqa: E402

L = 35.0
tr = S.track(L)

# bed: rain + dark pad
rain = S.rain(L) * S.curve([(0, 0.7), (6.8, 0.7), (7, 0.3), (11, 0.3), (11.2, 0.7), (31, 0.6), (35, 0.25)], int(L * S.SR))
S.place(tr, rain, 0, 0.9)
S.place(tr, S.fade(S.pad(L, (38, 45, 50, 53)), 2, 3), 0, 1.0)

# Charger engine (the GHOST is silent — that is the point)
eng = S.engine(L, [(0, 4000), (3, 4300), (7, 4600), (11, 6900), (16, 6100), (21, 6000), (26, 4600), (31, 3600), (35, 3000)])
eng *= S.curve([(0, 0.45), (3, 0.35), (7, 0.9), (11, 0.7), (11.5, 0.6), (16, 0.2), (21, 0.5), (26, 0.25), (30.8, 0.15), (31, 0.0)],
               len(eng))
S.place(tr, eng, 0, 1.0)

# 0:00–0:03 two red eyes in the mirror
S.place(tr, S.riser(1.5), 0.0, 0.5)
S.place(tr, S.boom(3.5, 38), 1.5, 1.2)
S.place(tr, S.thunder(6), 4.0, 0.9, -0.3)
# 0:07–0:11 needle to 180: rev climbs (engine curve) + gear whine
S.place(tr, S.whoosh(1.2, 0.9, 1000, 6000), 9.8, 0.3)
# 0:11–0:21 something without headlights closes in
S.place(tr, S.heartbeat(10, 72), 11, 0.9)
S.place(tr, S.riser(4.5), 11.5, 0.6)
S.place(tr, S.boom(3, 45), 16.0, 1.0)
S.place(tr, S.wind(5.0, 300, 2500), 16, 0.6, -0.5)
# 0:21–0:26 the GHOST passes, spray over the Charger
S.place(tr, S.whoosh(2.2, 1.2, 200, 7000), 21.4, 1.3, 0.4)
S.place(tr, S.band(S.noise(3), 2000, 9000) * S.env(int(3 * S.SR), 0.1, 1.0), 22.5, 0.5, -0.2)
# 0:26–0:31 tunnel strips die one by one (far -> near)
for k in range(12):
    S.place(tr, S.click(), 27.2 + k * 0.28, 0.9 - k * 0.03, 0.6 - k * 0.1)
S.place(tr, S.boom(3, 34), 30.6, 0.7)
# 0:31–0:35 empty exit + title glitch
S.place(tr, S.wind(4.0, 150, 900), 31, 0.5)
S.place(tr, S.glitch(0.7), 32.5, 0.8)
S.place(tr, S.boom(2.5, 40), 32.5, 1.2)

S.write(S.reverb(tr, 0.22, 2.4), "short1")
