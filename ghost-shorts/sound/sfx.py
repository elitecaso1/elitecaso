"""Tiny procedural sound-design kit (numpy only) for THE GHOST shorts.

Every short gets a sound/shortN.py that places these layers on its timeline
and writes renders/shortN.wav; mux.sh puts it on the video.
"""
import os
import wave

import numpy as np

SR = 44100
rng = np.random.default_rng(13)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def track(seconds):
    return np.zeros((int(seconds * SR), 2), np.float32)


def t_axis(n):
    return np.arange(n) / SR


def noise(sec):
    return rng.standard_normal(int(sec * SR)).astype(np.float32)


def band(x, lo=None, hi=None):
    """Brick-ish FFT band-pass (good enough for sound design)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x)).astype(np.float32)


def env(n, attack=0.01, release=0.3, hold=None):
    """Attack / (hold) / exponential release envelope of n samples."""
    t = t_axis(n)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    h = hold if hold is not None else 0.0
    r = np.where(t < attack + h, 1.0, np.exp(-(t - attack - h) / max(release, 1e-4)))
    return (a * r).astype(np.float32)


def fade(x, fin=0.05, fout=0.2):
    n = len(x)
    a, b = int(fin * SR), int(fout * SR)
    g = np.ones(n, np.float32)
    if a:
        g[:a] = np.linspace(0, 1, a)
    if b:
        g[-b:] = np.minimum(g[-b:], np.linspace(1, 0, b))
    return x * g


def place(tr, x, at, gain=1.0, pan=0.0):
    """Mix mono x into stereo track tr at time `at` (seconds); pan -1..1."""
    i = int(at * SR)
    if i >= len(tr):
        return
    x = x[: len(tr) - i] * gain
    tr[i:i + len(x), 0] += x * np.sqrt((1 - pan) / 2) * 1.414
    tr[i:i + len(x), 1] += x * np.sqrt((1 + pan) / 2) * 1.414


def curve(points, n):
    """Piecewise-linear automation from [(sec, value), ...] over n samples."""
    ts, vs = zip(*points)
    return np.interp(t_axis(n), ts, vs).astype(np.float32)


# ------------------------------------------------------------------ layers

def rain(sec, heavy=1.0):
    hiss = band(noise(sec), 1500, 9000) * 0.25
    drops = band(noise(sec) * (rng.random(int(sec * SR)) > 0.9995) * 8, 800, 6000) * 0.4
    return (hiss + drops) * heavy


def wind(sec, lo=200, hi=1200):
    base = band(noise(sec), lo, hi)
    wob = 0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * t_axis(len(base)) + rng.random() * 6)
    return base * wob * 0.5


def engine(sec, rpm_pts, growl=1.0):
    """V8-ish engine: firing pulses at rpm/60*4 Hz plus harmonics, band-limited."""
    n = int(sec * SR)
    rpm = curve(rpm_pts, n)
    f0 = rpm / 60 * 4
    ph = 2 * np.pi * np.cumsum(f0) / SR
    tone = sum(np.sin(k * ph) / k for k in range(1, 9))
    rough = band(noise(sec), 60, 900) * 0.6 * growl
    x = np.tanh(1.6 * (tone * 0.5 + rough * (0.5 + 0.5 * np.sin(ph * 0.5))))
    return band(x.astype(np.float32), 30, 2500) * 0.6


def boom(sec=3.0, f=42.0):
    """Cinematic sub hit."""
    n = int(sec * SR)
    t = t_axis(n)
    sweep = np.sin(2 * np.pi * np.cumsum(f * (1 + 1.5 * np.exp(-t * 8))) / SR)
    thump = band(noise(sec), 20, 300) * np.exp(-t * 12) * 0.8
    return ((sweep + thump) * env(n, 0.005, 0.9)).astype(np.float32)


def whoosh(sec=1.6, peak=0.6, lo=300, hi=5000):
    n = int(sec * SR)
    t = t_axis(n)
    shape = np.exp(-((t - peak) / (sec / 5)) ** 2)
    return band(noise(sec), lo, hi) * shape * 0.9


def riser(sec=3.0):
    n = int(sec * SR)
    t = t_axis(n)
    tone = np.sin(2 * np.pi * np.cumsum(80 + 900 * (t / sec) ** 2) / SR) * 0.25
    return ((band(noise(sec), 500, 8000) * (t / sec) ** 2 * 0.5 + tone) * (t / sec)).astype(np.float32)


def click(sec=0.35):
    """Electrical relay clunk + buzz cut."""
    n = int(sec * SR)
    t = t_axis(n)
    thud = band(noise(sec), 80, 1500) * np.exp(-t * 60)
    buzz = np.sign(np.sin(2 * np.pi * 100 * t)) * 0.15 * np.exp(-t * 25)
    return (thud + buzz).astype(np.float32)


def glitch(sec=0.6):
    n = int(sec * SR)
    x = np.zeros(n, np.float32)
    i = 0
    while i < n:
        L = int(rng.uniform(0.01, 0.06) * SR)
        if rng.random() < 0.6:
            f = rng.uniform(200, 3000)
            x[i:i + L] = np.sign(np.sin(2 * np.pi * f * t_axis(min(L, n - i)))) * 0.3
        i += L
    return band(x + noise(sec) * 0.1, 100, 9000) * env(n, 0.002, sec / 2)


def heartbeat(sec, bpm=70):
    tr = np.zeros(int(sec * SR), np.float32)
    beat = band(noise(0.25), 30, 120) * env(int(0.25 * SR), 0.005, 0.06) * 2
    t = 0.0
    while t < sec - 0.3:
        for off, g in ((0, 1.0), (0.28, 0.7)):
            i = int((t + off) * SR)
            tr[i:i + len(beat)] += beat[: len(tr) - i] * g
        t += 60 / bpm
    return tr


def thunder(sec=5.0):
    n = int(sec * SR)
    t = t_axis(n)
    crack = band(noise(sec), 200, 6000) * np.exp(-t * 6) * 0.6
    roll = band(noise(sec), 20, 400) * (np.exp(-t * 0.8) * (0.7 + 0.3 * np.sin(t * 7))) * 1.2
    return (crack + roll) * env(n, 0.02, 2.0)


def pad(sec, notes=(36, 43, 48, 51), level=0.12):
    """Dark detuned synth pad (MIDI notes), slow swell."""
    n = int(sec * SR)
    t = t_axis(n)
    x = np.zeros(n, np.float32)
    for m in notes:
        f = 440 * 2 ** ((m - 69) / 12)
        for det in (-0.12, 0.0, 0.11):
            x += np.sin(2 * np.pi * f * (1 + det / 100) * t + rng.random() * 6)
    x = band(x, 30, 1800) / (len(notes) * 3)
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.08 * t)
    return x * lfo * level


def tyre_screech(sec=1.5):
    n = int(sec * SR)
    t = t_axis(n)
    f = 1800 + 400 * np.sin(2 * np.pi * 3 * t)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    return ((tone + band(noise(sec), 1500, 6000) * 0.4) * env(n, 0.05, sec / 2)).astype(np.float32)


def reverb(tr, mix=0.25, size=2.2):
    """Cheap stereo convolution reverb with decaying noise tails."""
    out = tr.copy()
    for ch in range(2):
        ir = noise(size) * np.exp(-t_axis(int(size * SR)) * 3.0)
        ir = band(ir, 200, 6000)
        ir /= np.abs(ir).sum() ** 0.5 * 30
        n = len(tr) + len(ir)
        y = np.fft.irfft(np.fft.rfft(tr[:, ch], n) * np.fft.rfft(ir, n), n)[: len(tr)]
        out[:, ch] = tr[:, ch] * (1 - mix) + y * mix
    return out


def write(tr, name):
    rms = float(np.sqrt((tr ** 2).mean())) or 1.0
    tr = np.tanh(tr * (0.16 / rms)) * 0.95                   # loudness up + soft limiter
    path = os.path.join(ROOT, "renders", name + ".wav")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pcm = (np.clip(tr, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", path)
    return path
