"""Sound for Short 3 – "Pahad Ka Mod" (40 s)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as S  # noqa: E402

L = 40.0
tr = S.track(L)
n = int(L * S.SR)
S.place(tr, S.wind(L, 120, 1500) * S.curve([(0, 0.9), (13, 0.5), (35, 0.6), (40, 1.0)], n), 0, 1.0)
S.place(tr, S.fade(S.pad(L, (35, 42, 47, 50)), 2, 3), 0, 1.0)
S.place(tr, S.boom(3, 32), 0.1, 0.9)                                   # the khai
eng = S.engine(L, [(0, 5200), (3, 4300), (6, 3800), (9, 5500), (13, 6000), (16.5, 4000), (18, 1100),
                   (21, 1300), (21.4, 6200), (30, 7000), (33, 4500), (35, 900), (40, 900)])
eng *= S.curve([(0, 0.4), (3, 0.6), (9, 0.3), (13, 0.8), (18, 0.4), (21, 0.5), (30, 0.8), (35, 0.2), (40, 0.15)], n)
S.place(tr, eng, 0, 1.0, 0.2)
S.place(tr, S.tyre_screech(5.0), 3.6, 0.9)                             # drift
S.place(tr, S.tyre_screech(1.5), 15.0, 0.6, -0.3)
S.place(tr, S.heartbeat(5, 80), 13.5, 0.8)
S.place(tr, S.riser(2.0), 16.8, 0.6)
hum = S.np.sin(2 * S.np.pi * 110 * S.t_axis(int(2.5 * S.SR))) * S.env(int(2.5 * S.SR), 0.3, 1.0) * 0.3
S.place(tr, hum.astype(S.np.float32), 18.6, 1.0)                       # blue headlights ignite
S.place(tr, S.boom(3, 40), 18.7, 1.3)
for t in (21.0, 24.0, 27.0):
    S.place(tr, S.whoosh(1.4, 0.4, 250, 6000), t - 0.4, 0.9)
S.place(tr, S.tyre_screech(1.8), 30.5, 0.7, 0.3)
S.place(tr, S.riser(2.6), 30.0, 0.8)
slow = S.boom(6, 26)                                                   # slow-mo over the railing
S.place(tr, slow, 32.6, 1.3)
S.place(tr, S.whoosh(3.5, 2.0, 80, 1500), 32.6, 0.9, 0.5)
S.place(tr, S.heartbeat(5, 50), 33.0, 0.9)
S.place(tr, S.glitch(0.6), 37.0, 0.7)
S.place(tr, S.boom(3, 38), 37.0, 1.0)
S.write(S.reverb(tr, 0.3, 3.5), "short3")
