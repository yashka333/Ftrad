"""Three soundtrack options for the 21.6 s teaser, produced (not chiptune):
lo-fi, phonk and cinematic. Each is cut to the teaser's beats:
  0.45 pack lands, 2.25 pack tears, 3.3 Mythic reveal, 6.6 desk, 15.6 end card, 16.0 DOCS SOON, 17.6 STAY TUNED.

  python3 music_variants.py  -> build/music-lofi.wav, music-phonk.wav, music-cinematic.wav
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import scipy.signal as sg

SR = 44100
DUR = 21.6
N = int((DUR + 0.5) * SR)
OUT = Path(__file__).parent / 'build'
LAND, TEAR, REVEAL, DESK, END, DOCS, TUNED = 0.45, 2.25, 3.3, 6.6, 15.6, 16.0, 17.6


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


class Mix:
    def __init__(self, seed=1):
        self.L = np.zeros(N)
        self.R = np.zeros(N)
        self.rng = np.random.default_rng(seed)

    def add(self, sig, t, pan=0.0, g=1.0):
        i = int(t * SR)
        if i >= N:
            return
        j = min(N, i + len(sig))
        s = sig[:j - i] * g
        self.L[i:j] += s * np.sqrt(0.5 * (1 - pan))
        self.R[i:j] += s * np.sqrt(0.5 * (1 + pan))

    def add_st(self, l, r, t, g=1.0):
        i = int(t * SR)
        j = min(N, i + len(l))
        self.L[i:j] += l[:j - i] * g
        self.R[i:j] += r[:j - i] * g


# ------------------------------------------------------------------ instruments
def tvec(d):
    return np.arange(int(d * SR)) / SR


def adsr(n, a=.005, d=.1, s=.7, r=.2, hold=None):
    t = np.arange(n) / SR
    hold = hold if hold is not None else n / SR - r
    e = np.where(t < a, t / a, np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    e = np.where(t > hold, e * np.exp(-(t - hold) / max(r / 4, 1e-3)), e)
    return e


def lowpass(x, f, order=2):
    b, a = sg.butter(order, min(f, SR / 2 - 100) / (SR / 2), 'low')
    return sg.lfilter(b, a, x)


def highpass(x, f, order=2):
    b, a = sg.butter(order, f / (SR / 2), 'high')
    return sg.lfilter(b, a, x)


def bandpass(x, lo, hi, order=2):
    b, a = sg.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band')
    return sg.lfilter(b, a, x)


def epiano(m, dur, vel=.5):
    t = tvec(dur + 1.4)
    f = midi(m)
    mod = np.sin(2 * np.pi * f * t) * 1.2 * np.exp(-t * 5)          # FM tine
    s = np.sin(2 * np.pi * f * t + mod) + .3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3)
    s *= 1 + .05 * np.sin(2 * np.pi * 4.8 * t)                     # tremolo
    e = np.exp(-t * 1.6) * (1 - np.exp(-t * 300))
    k = int(dur * SR)
    e[k:] *= np.exp(-np.arange(len(t) - k) / SR * 7)
    return s * e * vel


def bell(m, vel=.3):
    t = tvec(2.0)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t + 2.2 * np.sin(2 * np.pi * f * 3.5 * t) * np.exp(-t * 3))
    return s * np.exp(-t * 2.4) * (1 - np.exp(-t * 400)) * vel


def pad(ms, dur, vel=.2, cutoff=1800, attack=.8, detune=.12):
    t = tvec(dur + 1.5)
    s = np.zeros(len(t))
    for m in ms:
        for d in (-detune, 0, detune):
            f = midi(m + d)
            ph = (f * t + np.random.default_rng(int(m * 10 + d * 100)).random()) % 1
            s += 2 * ph - 1
    s = lowpass(s, cutoff, 2) / (len(ms) * 3)
    e = np.clip(t / attack, 0, 1)
    k = int(dur * SR)
    e[k:] *= np.exp(-np.arange(len(t) - k) / SR * 2.5)
    return s * e * vel


def strings(ms, dur, vel=.2):
    return pad(ms, dur, vel, cutoff=2600, attack=.35, detune=.08)


def sub808(m, dur, vel=.6, glide_to=None, drive=1.8):
    t = tvec(dur)
    f0 = midi(m)
    f = np.full(len(t), f0)
    if glide_to is not None:
        g = np.clip((t - dur * .55) / (dur * .3), 0, 1)
        f = f0 * (midi(glide_to) / f0) ** g
    f = f * (1 + 1.5 * np.exp(-t * 40))                              # punchy pitch drop
    ph = np.cumsum(f) / SR
    s = np.tanh(np.sin(2 * np.pi * ph) * drive) / np.tanh(drive)
    e = (1 - np.exp(-t * 300)) * np.exp(-t * .8)
    e[-int(.03 * SR):] *= np.linspace(1, 0, int(.03 * SR))
    return s * e * vel


def kick(vel=.9, tight=False):
    t = tvec(.45)
    f = 48 + 120 * np.exp(-t * (38 if tight else 26))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (11 if tight else 7))
    click = highpass(np.random.default_rng(3).standard_normal(len(t)), 3000) * np.exp(-t * 300) * .3
    return np.tanh((s + click) * 1.6) * vel


def snare(vel=.5, rng=None):
    rng = rng or np.random.default_rng(4)
    t = tvec(.35)
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 28) * .6
    nz = bandpass(rng.standard_normal(len(t)), 1500, 9000) * np.exp(-t * 16)
    return (body + nz) * vel


def clap(vel=.5, rng=None):
    rng = rng or np.random.default_rng(5)
    t = tvec(.4)
    nz = bandpass(rng.standard_normal(len(t)), 900, 6000)
    e = np.zeros(len(t))
    for k, off in enumerate((0, .011, .023)):
        i = int(off * SR)
        e[i:] += np.exp(-(t[:len(t) - i]) * (90 if k < 2 else 14))
    return nz * e * vel


def hat(vel=.15, open_=False, rng=None):
    rng = rng or np.random.default_rng(6)
    t = tvec(.3 if open_ else .06)
    nz = highpass(rng.standard_normal(len(t)), 7000, 3)
    return nz * np.exp(-t * (12 if open_ else 70)) * vel


def cowbell(m, vel=.25):
    t = tvec(.5)
    f = midi(m)
    s = np.sign(np.sin(2 * np.pi * f * t)) + np.sign(np.sin(2 * np.pi * f * 1.48 * t))
    s = bandpass(s, f * .8, f * 4)
    return s * np.exp(-t * 9) * (1 - np.exp(-t * 800)) * vel


def riser(dur, vel=.25, rng=None):
    rng = rng or np.random.default_rng(7)
    t = tvec(dur)
    nz = rng.standard_normal(len(t))
    out = np.zeros(len(t))
    blocks = 40
    for b in range(blocks):
        a, z = b * len(t) // blocks, (b + 1) * len(t) // blocks
        fc = 300 * (40 ** (b / blocks))
        out[a:z] = bandpass(nz, fc * .7, min(fc * 1.6, 18000))[a:z]
    return out * (t / dur) ** 2 * vel


def impact(vel=.9, rng=None):
    rng = rng or np.random.default_rng(8)
    t = tvec(2.5)
    boom = np.sin(2 * np.pi * np.cumsum(32 + 70 * np.exp(-t * 6)) / SR) * np.exp(-t * 1.6)
    nz = lowpass(rng.standard_normal(len(t)), 2500) * np.exp(-t * 3.5) * .5
    return np.tanh((boom + nz) * 1.4) * vel


def whoosh(dur=.6, vel=.3, rng=None):
    rng = rng or np.random.default_rng(9)
    t = tvec(dur)
    nz = rng.standard_normal(len(t))
    env = np.sin(np.pi * t / dur) ** 2
    return bandpass(nz, 400, 6000) * env * vel


def shimmer(vel=.2):
    t = tvec(2.2)
    s = np.zeros(len(t))
    for i, m in enumerate((84, 88, 91, 96, 100)):
        d = int(i * .06 * SR)
        s[d:] += np.sin(2 * np.pi * midi(m) * t[:len(t) - d]) * np.exp(-t[:len(t) - d] * 2.2)
    return s * vel / 3


def vinyl(rng, vel=.004):
    crack = lowpass(rng.standard_normal(N) * vel, 3000, 1)
    pops = (rng.random(N) < .00005) * rng.uniform(-.12, .12, N)
    return crack + pops


def reverb(L, R, wet=.25, size=1.0):
    """Small Schroeder reverb: parallel combs then allpasses, per side."""
    def side(x, seed):
        out = np.zeros_like(x)
        for d, g in ((.0297, .78), (.0371, .76), (.0411, .74), (.0437, .72)):
            k = int(d * size * SR * (1 + .03 * seed))
            b = np.zeros(k + 1); b[0] = 1
            a = np.zeros(k + 1); a[0] = 1; a[k] = -g
            out += sg.lfilter(b, a, x)
        for d, g in ((.005, .7), (.0017, .7)):
            k = int(d * SR)
            b = np.zeros(k + 1); b[0] = -g; b[k] = 1
            a = np.zeros(k + 1); a[0] = 1; a[k] = -g
            out = sg.lfilter(b, a, out)
        return lowpass(out, 6000, 1) * .25
    return L + side(L, 0) * wet, R + side(R, 1) * wet


def finish(mix: Mix, name, rev=.25, size=1.0, duck=None):
    L, R = reverb(mix.L, mix.R, rev, size)
    end = int(DUR * SR)
    fo = int(.9 * SR)
    env = np.ones(N)
    env[end - fo:end] = np.linspace(1, 0, fo)
    env[end:] = 0
    L *= env; R *= env
    st = np.stack([L, R], 1)[:end]
    st = st / np.max(np.abs(st)) * 1.25
    st = np.tanh(st) * .93                                          # gentle glue/limiter
    pcm = (st * 32767).astype('<i2')
    with wave.open(str(OUT / f'music-{name}.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('wrote', name)


def sidechain(mix: Mix, hits, depth=.6, rel=.18):
    g = np.ones(N)
    for t in hits:
        i = int(t * SR)
        k = int(rel * SR)
        j = min(N, i + k)
        g[i:j] = np.minimum(g[i:j], 1 - depth * (1 - np.linspace(0, 1, j - i)) ** 2)
    return g


# ================================================================== 1. lo-fi
def lofi():
    m = Mix(11)
    bpm = 88
    beat = 60 / bpm
    prog = [(53, [57, 60, 64, 67]), (52, [55, 59, 62, 67]), (50, [53, 57, 60, 64]), (48, [52, 55, 59, 64])]  # Fmaj7 Em7 Dm7 Cmaj7
    bar = 4 * beat
    keys = Mix(12)
    t = 0.0
    bi = 0
    while t < DUR:
        root, ch = prog[bi % 4]
        for k, n in enumerate(ch):
            keys.add(epiano(n, bar * .95, .16), t + k * .018, pan=-.2 + k * .13)
        if t >= REVEAL - .01:
            m.add(lowpass(sub808(root - 12, bar * .9, .32, drive=1.1), 400), t)
        t += bar; bi += 1
    m.L += lowpass(keys.L, 3200); m.R += lowpass(keys.R, 3200)
    # drums from the reveal to the end card, swung
    b0 = REVEAL
    n_beats = int((END - b0) / beat)
    for q in range(n_beats):
        tq = b0 + q * beat
        if q % 4 in (0,) or (q % 4 == 2 and q % 8 == 6):
            m.add(kick(.75), tq)
        if q % 4 == 2 and q % 8 != 6:
            m.add(kick(.55), tq + beat * .5)
        if q % 4 in (1, 3):
            m.add(snare(.32, m.rng), tq + .012, pan=.05)
        m.add(hat(.07, rng=m.rng), tq, pan=.3)
        m.add(hat(.05, rng=m.rng), tq + beat * .58, pan=.35)
    # bells on the reveal and the coins
    for i, n in enumerate((72, 76, 79, 84)):
        m.add(bell(n, .12), REVEAL + i * .09, pan=-.3 + i * .2)
    for k in range(int((DESK + 1.4 - 0) // 1) , 0):
        pass
    ct = DESK + 1.4
    i = 0
    while ct < END - .2:
        m.add(bell([84, 88, 91, 86][i % 4], .07), ct, pan=.35 if i % 2 else -.35)
        ct += .42 * 2; i += 1
    # end card: keys only, a soft chime on DOCS SOON and STAY TUNED
    m.add(shimmer(.1), DOCS)
    m.add(bell(79, .1), TUNED, pan=.2)
    m.add(riser(1.0, .05), REVEAL - 1.0)
    rng = np.random.default_rng(3)
    v = vinyl(rng)
    m.L += v; m.R += v
    m.L = lowpass(m.L, 9000); m.R = lowpass(m.R, 9000)
    finish(m, 'lofi', rev=.3, size=1.1)


# ================================================================== 2. phonk
def phonk():
    m = Mix(21)
    bpm = 140
    beat = 60 / bpm
    # dark intro pad and a riser into the tear
    m.add(pad([42, 49, 54], REVEAL, .22, cutoff=900, attack=1.0), 0)
    m.add(riser(TEAR, .22), 0)
    m.add(impact(.55), LAND)
    m.add(whoosh(.5, .3), TEAR - .25)
    m.add(impact(1.0), REVEAL)
    m.add(shimmer(.14), REVEAL + .05)
    # drop: from the reveal to the end card
    start = REVEAL
    steps = int((END - start) / (beat / 4))
    bass_line = [(42, 6), (42, 2), (45, 4), (40, 4)]                # F#, A, E in 16ths per beat block
    hits = []
    cow = [78, None, 78, 81, None, 78, 76, None, 78, None, 81, 83, None, 81, 78, None]
    for s in range(steps):
        t = start + s * beat / 4
        pos = s % 16
        bar = (s // 16) % 4
        if pos in (0, 10) or (pos == 7 and bar % 2):
            m.add(kick(.95, tight=True), t); hits.append(t)
        if pos in (4, 12):
            m.add(clap(.5, m.rng), t, pan=.04); m.add(snare(.25, m.rng), t)
        hv = .1 if pos % 2 == 0 else .06
        if bar == 3 and pos >= 12:
            m.add(hat(.07, rng=m.rng), t + beat / 8, pan=.25)          # hat roll
        m.add(hat(hv, rng=m.rng), t, pan=.25)
        n = cow[pos]
        if n and bar != 3:
            m.add(cowbell(n - 12 + (2 if bar == 2 else 0), .22), t, pan=-.2 if pos % 2 else .2)
        if pos == 0:
            root = [42, 42, 45, 40][bar]
            glide = [None, 37, None, 42][bar]
            m.add(sub808(root - 12, beat * 4 * .98, .7, glide_to=(glide - 12) if glide else None, drive=2.4), t)
    g = sidechain(m, hits, .25)
    m.L *= g; m.R *= g
    # end: everything stops, 808 tail and a cowbell echo
    m.add(impact(.7), END)
    m.add(sub808(30, 2.5, .6, drive=2.6), DOCS)
    for k in range(4):
        m.add(cowbell(66, .18 * (.6 ** k)), TUNED + k * beat * .75, pan=(-1) ** k * .4)
    m.add(pad([42, 49, 54, 61], 5.5, .34, cutoff=1300, attack=.4), END + .1)
    m.add(sub808(30, 2.5, .45, drive=2.2), TUNED)
    finish(m, 'phonk', rev=.18, size=.8)


# ================================================================== 3. cinematic
def cinematic():
    m = Mix(31)
    # intro: low strings swell, ticking pulse, riser to the tear
    m.add(strings([45, 52, 57], REVEAL + .2, .28), 0)
    m.add(pad([33], REVEAL, .3, cutoff=300, attack=.3), 0)
    m.add(impact(.6), LAND)
    for k in range(int(TEAR / .25)):
        m.add(hat(.05 + .03 * k / 9, rng=m.rng), .45 + k * .25, pan=.2)
    m.add(riser(TEAR + .9, .3), 0)
    m.add(whoosh(.6, .35), TEAR - .3)
    # reveal: big hit and a major lift
    m.add(impact(1.0), REVEAL)
    m.add(shimmer(.2), REVEAL)
    m.add(strings([48, 55, 60, 64, 67], DESK - REVEAL + .3, .32), REVEAL)
    for i, n in enumerate((72, 76, 79, 84)):
        m.add(bell(n, .12), REVEAL + .05 + i * .07, pan=-.3 + i * .2)
    # desk: driving arp + drums
    bpm = 120
    beat = 60 / bpm
    chords = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]   # Am F C G
    steps = int((END - DESK) / (beat / 4))
    hits = []
    for s in range(steps):
        t = DESK + s * beat / 4
        pos = s % 16
        ci = (s // 16) % 4
        root, ch = chords[ci]
        note = ch[[0, 1, 2, 1][pos % 4]] + (12 if pos >= 8 else 0)
        m.add(lowpass(pad([note], beat / 4 * .9, .16, cutoff=3500, attack=.003, detune=.06), 5000), t, pan=.25 if pos % 2 else -.25)
        if pos == 0:
            m.add(strings([root + 12] + ch, beat * 4, .2), t)
            m.add(lowpass(sub808(root - 12, beat * 4 * .95, .45, drive=1.3), 300), t)
        if pos % 4 == 0:
            m.add(kick(.8), t); hits.append(t)
        if pos in (4, 12):
            m.add(snare(.35, m.rng), t)
            m.add(clap(.2, m.rng), t)
        m.add(hat(.06 if pos % 2 else .09, rng=m.rng), t, pan=.3)
    g = sidechain(m, hits, .3)
    m.L *= g; m.R *= g
    # end: final chord and hits on DOCS SOON and STAY TUNED
    m.add(riser(.8, .2), END - .8)
    m.add(impact(1.0), DOCS)
    m.add(strings([45, 52, 57, 60, 64, 69], 5.5, .34), DOCS)
    m.add(shimmer(.16), DOCS + .05)
    m.add(impact(.5), TUNED)
    m.add(bell(81, .12), TUNED, pan=.2)
    finish(m, 'cinematic', rev=.35, size=1.3)


if __name__ == '__main__':
    lofi()
    phonk()
    cinematic()
