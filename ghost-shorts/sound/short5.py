"""Sound for Short 5 – "75 Meter" (45 s)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as S  # noqa: E402

L = 45.0
tr = S.track(L)
n = int(L * S.SR)
S.place(tr, S.wind(L, 100, 2000) * S.curve([(0, 1.0), (29, 0.6), (29.4, 0.3), (40, 0.3), (40.05, 0.0)], n), 0, 1.0)
S.place(tr, S.fade(S.pad(40, (36, 43, 48, 51)), 1, 0.05), 0, 1.0)
S.place(tr, S.riser(0.6), 0.0, 0.5)
S.place(tr, S.boom(3, 40), 0.5, 1.1)                                    # "75 m"
c = S.engine(L, [(0, 6800), (19, 7000), (19.3, 3000), (24, 900), (45, 900)])
c *= S.curve([(0, 0.0), (4, 0.6), (10, 0.9), (14, 0.7), (19, 0.6), (24, 0.3), (29.4, 0.0)], n)
g = S.engine(L, [(0, 7200), (29, 7600)], 0.6) * S.curve([(0, 0.0), (4, 0.4), (19, 0.4), (24, 0.6), (28.8, 0.9), (29.4, 0.0)], n)
S.place(tr, c, 0, 1.0, 0.3)
S.place(tr, g, 0, 1.0, -0.3)
S.place(tr, S.tyre_screech(4.5), 19.0, 1.0, 0.3)                        # Charger brakes
S.place(tr, S.whoosh(1.6, 0.6, 200, 6000), 19.6, 1.0, -0.3)             # GHOST blows past
S.place(tr, S.riser(4.0), 24.8, 0.9)
S.place(tr, S.boom(4, 34), 28.8, 1.4)                                   # launch
slow = S.boom(11, 22)
S.place(tr, slow, 29.4, 1.2)
S.place(tr, S.heartbeat(10.5, 44), 29.5, 1.0)
S.place(tr, S.whoosh(10, 5.0, 60, 900) * 0.8, 29.4, 1.0)
# 0:40 hard cut to black: silence, then the title hit
S.place(tr, S.boom(4.5, 30), 40.6, 1.3)
S.place(tr, S.fade(S.pad(4.4, (36, 43, 48), 0.18), 0.5, 1.5), 40.6, 1.0)
S.write(S.reverb(tr, 0.25, 3.0), "short5")
