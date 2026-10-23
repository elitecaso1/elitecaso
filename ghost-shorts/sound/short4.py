"""Sound for Short 4 – "Garage No. 13" (35 s)."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as S  # noqa: E402

L = 35.0
tr = S.track(L)
n = int(L * S.SR)
np = S.np
S.place(tr, S.band(S.noise(L), 40, 250) * 0.2, 0)                      # room tone
S.place(tr, S.fade(S.pad(L, (34, 41, 46, 49), 0.1), 1, 3), 0, 1.0)
t = S.t_axis(n)
buzz = (np.sign(np.sin(2 * np.pi * 100 * t)) * 0.04 + np.sin(2 * np.pi * 50 * t) * 0.05).astype(np.float32)
random.seed(4)
flick = [(0, 1)]
x = 0.4
while x < 6:                                                           # flicker sputter
    flick += [(x, random.choice((0, 1))), (x + 0.05, flick[-1][1])]
    x += random.uniform(0.08, 0.3)
flick += [(6.2, 1), (35, 1)]
S.place(tr, buzz * S.curve(sorted(flick), n), 0, 1.0)
for k in range(12):
    S.place(tr, S.click(0.15), 0.4 + k * 0.45, 0.4, 0.5)
S.place(tr, S.whoosh(6.0, 3.0, 400, 3000) * 0.6, 4.0, 0.8, 0.3)        # cloth slides off
S.place(tr, S.riser(4.0), 10.0, 0.5)                                   # light sweep
S.place(tr, S.boom(2.5, 44), 14.0, 1.0)
whine = np.sin(2 * np.pi * np.cumsum(np.linspace(200, 2400, int(2.5 * S.SR))) / S.SR) * 0.15
S.place(tr, (whine * S.env(len(whine), 0.4, 1.0)).astype(np.float32), 14.5, 1.0)   # dashboard wakes
crank = S.engine(0.8, [(0, 300), (0.8, 600)]) * 0.6
S.place(tr, crank, 18.0, 1.0)
eng = S.engine(17, [(0, 1200), (0.3, 6500), (1.0, 2200), (2, 5800), (3, 2000), (8, 1300), (9, 5000), (13, 7000), (17, 7000)], 1.5)
eng *= S.curve([(0, 1.0), (4, 0.7), (9, 1.0), (12, 0.6), (13, 0.2), (17, 0.0)], len(eng))
S.place(tr, eng, 18.6, 1.1)
S.place(tr, S.boom(2.5, 38), 18.6, 1.2)
for k in range(6):
    S.place(tr, S.click(0.12), 19 + k * 0.55, 0.8, -0.2)              # flame pops
rattle = S.band(S.noise(4.0), 300, 4000) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 14 * S.t_axis(int(4 * S.SR)))))
S.place(tr, (rattle * S.env(len(rattle), 0.2, 1.5, 2.5) * 0.5).astype(np.float32), 22.5, 1.0)  # shutter
S.place(tr, S.whoosh(3.0, 1.8, 150, 4000), 27.5, 1.0)
S.place(tr, S.heartbeat(4, 60), 31.0, 0.8)
S.place(tr, S.glitch(0.6), 33.0, 0.8)
S.place(tr, S.boom(2.5, 36), 33.0, 1.1)
S.write(S.reverb(tr, 0.35, 1.6), "short4")
