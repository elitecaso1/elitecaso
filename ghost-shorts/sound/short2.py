"""Sound for Short 2 – "Signal Laal Hai" (30 s)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as S  # noqa: E402

L = 30.0
tr = S.track(L)
n = int(L * S.SR)
S.place(tr, S.band(S.noise(L), 40, 400) * 0.25, 0)                    # distant city hum
S.place(tr, S.fade(S.pad(L, (37, 44, 49, 52)), 1, 3), 0, 1.0)


def beep(f):
    t = S.t_axis(int(0.35 * S.SR))
    return (S.np.sin(2 * S.np.pi * f * t) * S.env(len(t), 0.005, 0.12)).astype(S.np.float32)


for t, f in ((0.2, 660), (7.0, 740), (14.0, 880)):                    # 3 .. 2 .. 1
    S.place(tr, beep(f), t, 0.6)
    S.place(tr, S.boom(2.0, 40), t, 0.6)
idle = S.engine(L, [(0, 950), (17, 1000), (17.3, 5200), (22, 7000), (26, 7200), (30, 7200)])
idle *= S.curve([(0, 0.35), (16.8, 0.4), (17, 1.0), (25.8, 0.8), (26, 0.0)], n)
S.place(tr, idle, 0, 1.0, -0.2)
S.place(tr, S.engine(L, [(0, 800), (17, 820), (17.4, 4800), (26, 6600), (30, 6600)], 1.4)
        * S.curve([(0, 0.25), (17, 0.3), (17.2, 0.8), (25.8, 0.6), (26, 0)], n), 0, 0.8, 0.3)
for k in range(5):                                                    # exhaust pops on "2"
    S.place(tr, S.click(0.2), 7.3 + k * 0.4, 0.7, -0.3 + k * 0.15)
S.place(tr, S.riser(3.5), 10.0, 0.6)                                  # GHOST out of the fog
S.place(tr, S.whoosh(2.5, 1.6, 150, 3000), 11.0, 0.8)
S.place(tr, S.boom(3, 36), 13.6, 1.1)
S.place(tr, S.heartbeat(3, 96), 14.0, 1.0)
S.place(tr, S.riser(2.8), 14.2, 0.8)
S.place(tr, S.boom(3, 44), 17.0, 1.3)                                 # GREEN
S.place(tr, S.tyre_screech(2.5), 17.0, 0.9, -0.4)
S.place(tr, S.tyre_screech(2.0), 17.1, 0.7, 0.4)
S.place(tr, S.whoosh(1.8, 0.8, 200, 6000), 19.6, 1.0)
S.place(tr, S.whoosh(1.8, 0.8, 200, 6000), 22.5, 0.8, 0.3)
S.place(tr, beep(520), 26.0, 0.5)                                     # red again, empty
S.place(tr, S.glitch(0.5), 27.5, 0.5)
S.place(tr, S.wind(4, 150, 800), 26, 0.5)
S.write(S.reverb(tr, 0.25, 2.8), "short2")
