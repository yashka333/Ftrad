"""8-bit soundtrack and sound effects for the trailer, synthesized with numpy.

Reads build/events.json (scene starts and cues from trailer.py), writes build/music.wav.
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

SR = 44100
HERE = Path(__file__).parent
EV = json.loads((HERE / 'build/events.json').read_text())
TOTAL = EV['total'] + 0.6
N = int(TOTAL * SR)
mix = np.zeros(N)
rng = np.random.default_rng(1)

scene = {e[1][6:]: e[0] for e in EV['events'] if e[1].startswith('scene:')}
cues = [(t, n) for t, n in EV['events'] if not n.startswith('scene:')]
cues += [(scene['hall'] + 1.5, 'stinger'), (scene['hall'] + 3.4, 'count_end'), (scene['end'] + 1.2, 'final')]

BPM = 120
STEP = 60 / BPM / 4            # one 16th note
A4 = 440.0


def hz(note: str) -> float:
    names = {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4, 'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2}
    n, o = note[:-1], int(note[-1])
    return A4 * 2 ** ((names[n] + (o - 4) * 12) / 12)


def env(n, a=0.004, d=0.0, s=1.0, r=0.03):
    e = np.ones(n) * s
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if d:
        nd = int(d * SR)
        e[na:na + nd] = np.linspace(1, s, len(e[na:na + nd]))
    if nr and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def square(f, dur, duty=0.5, vol=0.2, decay=0.0, slide=0.0, vib=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = f * (1 + slide * t / max(dur, 1e-6))
    if vib:
        freq = freq * (1 + vib * np.sin(2 * np.pi * 6 * t) * np.clip(t * 4, 0, 1))
    ph = np.cumsum(freq) / SR
    w = np.where((ph % 1) < duty, 1.0, -1.0)
    e = env(n)
    if decay:
        e *= np.exp(-t * decay)
    return w * e * vol


def tri(f, dur, vol=0.3, decay=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ph = (f * t) % 1
    w = 4 * np.abs(ph - 0.5) - 1
    w = np.round(w * 8) / 8                     # 4-bit staircase like the NES
    e = env(n, r=0.02)
    if decay:
        e *= np.exp(-t * decay)
    return w * e * vol


def noise(dur, vol=0.2, decay=30, hp=False, lp=False):
    n = int(dur * SR)
    t = np.arange(n) / SR
    w = rng.uniform(-1, 1, n)
    hold = 2 if hp else 6                        # sample-and-hold for a crunchy 8-bit noise
    w = np.repeat(w[::hold], hold)[:n]
    if hp:
        w = np.diff(np.concatenate([[0], w]))
    if lp:
        w = np.convolve(w, np.ones(8) / 8, 'same')
    return w * np.exp(-t * decay) * vol


def kick(vol=0.55):
    dur = 0.16
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 150 * np.exp(-t * 28) + 42
    ph = np.cumsum(f) / SR
    return np.sin(2 * np.pi * ph) * np.exp(-t * 18) * vol


def snare(vol=0.3):
    out = noise(0.16, vol, 22)
    tone = tri(190, 0.08, vol * .5, 40)
    out[:len(tone)] += tone
    return out


def hat(vol=0.08, open_=False):
    return noise(0.12 if open_ else 0.035, vol, 18 if open_ else 90, hp=True)


def put(sig, t):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0:
        return
    j = min(N, i + len(sig))
    mix[max(0, i):j] += sig[max(0, -i):j - i]


def section(t):
    order = ['title', 'pack', 'street', 'work', 'pump', 'classic', 'hall', 'boss', 'end']
    cur = 'title'
    for k in order:
        if t >= scene[k] - 1e-6:
            cur = k
    return cur


# chords per bar (2 s): A minor, F, C, G
PROG = [('A2', ['A4', 'C5', 'E5', 'B4']), ('F2', ['F4', 'A4', 'C5', 'E5']),
        ('C3', ['C5', 'E5', 'G5', 'D5']), ('G2', ['G4', 'B4', 'D5', 'F#5'])]
LEAD = ['E5', None, 'A5', None, 'G5', 'E5', None, 'D5', 'E5', None, None, 'C5', 'D5', None, 'E5', None,
        'C5', None, 'F5', None, 'E5', 'C5', None, 'A4', 'C5', None, None, 'D5', 'E5', None, 'G5', None,
        'G5', None, 'E5', None, 'G5', 'A5', None, 'G5', 'E5', None, None, 'D5', 'C5', None, 'D5', None,
        'B4', None, 'D5', None, 'G5', None, 'F#5', 'G5', 'A5', None, 'G5', None, 'E5', None, 'D5', None]

tear = scene['pack'] + 2.25
reveal = scene['pack'] + 3.3
steps = int(TOTAL / STEP)
for s in range(steps):
    t = s * STEP
    sec = section(t)
    bar = int(t / 2) % 4
    pos = s % 16
    root, chord = PROG[bar]
    if sec == 'end' and t > scene['end'] + 1.2:
        continue
    if sec == 'title':
        if pos % 2 == 0:
            put(square(hz(chord[(pos // 2) % 4]), STEP * 1.6, 0.25, 0.06, decay=6), t)
        if pos == 0:
            put(tri(hz(root), 2.0, 0.18, decay=0.8), t)
    elif sec == 'pack':
        k = t - scene['pack']
        if t < tear:
            build = min(1, k / 2.2)
            if pos % 2 == 0:
                put(tri(hz('A2'), STEP * 1.8, 0.28, decay=4), t)
            put(hat(0.03 + 0.05 * build), t)
            if k > 0.9:
                rate = 4 if k < 1.6 else 2 if k < 2.0 else 1
                if pos % rate == 0:
                    put(snare(0.08 + 0.18 * build), t)
            if pos % 4 == 0:
                put(square(hz('A4') * (1 + build), STEP * 2, 0.125, 0.04 + 0.04 * build, decay=8), t)
        elif t < reveal:
            pass                                   # held breath before the reveal
        else:
            if pos % 4 == 0:
                put(kick(0.4), t)
            if pos % 2 == 0:
                put(square(hz(chord[(pos // 2) % 4]), STEP * 1.6, 0.25, 0.06, decay=6), t)
            if pos == 0:
                put(tri(hz(root), 2.0, 0.22, decay=0.6), t)
    elif sec in ('street', 'work', 'pump', 'classic', 'boss'):
        full = sec != 'street'
        if pos % 4 == 0:
            put(kick(0.5), t)
        if pos in (4, 12):
            put(snare(0.26), t)
        if pos % 2 == 1 or full:
            put(hat(0.06 if pos % 2 else 0.035), t)
        bass_pat = [0, None, 0, 12, None, 0, 7, None, 0, None, 0, 12, None, 7, 10, 12]
        b = bass_pat[pos]
        if b is not None:
            put(tri(hz(root) * 2 ** (b / 12), STEP * 0.95, 0.3), t)
        put(square(hz(chord[pos % 4]) * (2 if full and pos % 8 >= 4 else 1), STEP * 0.9, 0.25, 0.045, decay=10), t)
        if full:
            li = (s - int(scene['work'] / STEP)) % len(LEAD)
            note = LEAD[li]
            if note:
                put(square(hz(note), STEP * 1.9, 0.5, 0.075, decay=2.5, vib=0.006), t)
                put(square(hz(note) * 1.003, STEP * 1.9, 0.125, 0.03, decay=2.5), t + 0.06)   # soft echo
    elif sec == 'hall':
        k = t - scene['hall']
        if pos == 0:
            put(tri(hz('A1'), 2.0, 0.3, decay=0.9), t)
            put(square(hz('A2'), 2.0, 0.5, 0.05, decay=1.2), t)
        if k > 1.5 and pos % 4 == 0:
            put(kick(0.45), t)
        if k > 1.5 and pos in (4, 12):
            put(snare(0.2), t)
        if k > 1.5:
            put(hat(0.04), t)

# ------------------------------------------------------------------ sound effects
for t, n in cues:
    if n == 'blip':
        put(square(hz('E6'), 0.05, 0.5, 0.07) , t); put(square(hz('B6'), 0.06, 0.5, 0.06), t + 0.05)
        put(noise(0.12, 0.05, 30, hp=True), t)
    elif n == 'tick':
        put(square(hz('A5'), 0.04, 0.25, 0.08), t)
    elif n == 'select':
        for i, nt in enumerate(['C6', 'E6', 'G6', 'C7']):
            put(square(hz(nt), 0.09, 0.5, 0.08, decay=8), t + i * 0.05)
    elif n == 'hidden':
        put(square(hz('D5'), 0.25, 0.5, 0.06, slide=-0.3, vib=0.02), t)
    elif n == 'coin':
        put(square(hz('B5'), 0.07, 0.5, 0.06), t); put(square(hz('E6'), 0.25, 0.5, 0.06, decay=10), t + 0.07)
    elif n == 'pop':
        put(square(hz('C5'), 0.12, 0.5, 0.08, slide=1.2, decay=10), t)
        put(noise(0.08, 0.06, 40, hp=True), t)
    elif n == 'land':
        put(kick(0.6), t); put(noise(0.2, 0.15, 25, lp=True), t)
    elif n == 'rumble':
        pass
    elif n == 'tear':
        put(noise(0.5, 0.35, 7), t)                      # rip + crash
        put(square(hz('A3'), 0.4, 0.5, 0.06, slide=3, decay=4), t)
    elif n == 'roll':
        for i in range(17):
            put(square(hz('E6') if i % 2 else hz('B5'), 0.03, 0.25, 0.05), t + (i + 1) ** 0.8 / 9)
    elif n == 'reveal':
        put(noise(0.9, 0.18, 4, hp=True), t)
        for i, nt in enumerate(['C5', 'E5', 'G5', 'C6', 'E6']):
            put(square(hz(nt), 0.7 - i * 0.08, 0.5, 0.07, decay=2.5), t + i * 0.07)
        for nt in ('C4', 'G4', 'C5'):
            put(square(hz(nt), 1.2, 0.25, 0.05, decay=1.6, vib=0.01), t + 0.35)
        put(tri(hz('C3'), 1.2, 0.35, decay=1.5), t + 0.35)
    elif n == 'whoosh':
        put(noise(0.3, 0.12, 6, hp=True) * np.linspace(0, 1, int(0.3 * SR)) ** 2, t - 0.25)
    elif n == 'thud':
        put(kick(0.7), t); put(tri(hz('A1'), 0.4, 0.35, decay=6), t); put(noise(0.25, 0.12, 18, lp=True), t)
    elif n == 'stinger':
        for nt in ('A3', 'C4', 'E4', 'A4'):
            put(square(hz(nt), 0.9, 0.5, 0.05, decay=2, vib=0.01), t)
        put(noise(0.6, 0.15, 6, hp=True), t)
    elif n == 'count':
        put(square(hz('A6'), 0.025, 0.5, 0.035), t)
    elif n == 'count_end':
        put(square(hz('E6'), 0.08, 0.5, 0.07), t); put(square(hz('A6'), 0.4, 0.5, 0.07, decay=5), t + 0.08)
    elif n == 'boss':
        put(noise(0.6, 0.25, 6), t)
        for nt in ('A2', 'E3', 'A3'):
            put(square(hz(nt), 1.0, 0.5, 0.07, decay=2), t)
        put(kick(0.8), t)
        for i, nt in enumerate(['A5', 'C6', 'E6', 'A6']):
            put(square(hz(nt), 0.12, 0.5, 0.05, decay=8), t + 0.2 + i * 0.06)
    elif n == 'final':
        put(noise(1.2, 0.2, 3, hp=True), t)
        put(kick(0.8), t)
        for nt in ('A3', 'E4', 'A4', 'C5', 'E5'):
            put(square(hz(nt), 3.2, 0.5 if nt[-1] in '34' else 0.25, 0.045, decay=0.9, vib=0.008), t)
        put(tri(hz('A2'), 3.2, 0.4, decay=0.8), t)
        for i, nt in enumerate(['E5', 'A5', 'C6', 'E6', 'A6']):
            put(square(hz(nt), 0.15, 0.5, 0.05, decay=6), t + 0.05 + i * 0.07)

# neon hum under the title
hum_n = int(scene['pack'] * SR)
tt = np.arange(hum_n) / SR
mix[:hum_n] += 0.015 * np.sign(np.sin(2 * np.pi * 60 * tt)) * np.clip(tt - 0.5, 0, 1)

# fade out at the very end
fade = int(1.2 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)
mix = np.tanh(mix * 1.6) / np.tanh(1.6)
mix = mix / max(1e-6, np.abs(mix).max()) * 0.89
pcm = (mix * 32767).astype(np.int16)
stereo = np.repeat(pcm[:, None], 2, 1)
with wave.open(str(HERE / 'build/music.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(stereo.tobytes())
print('music', TOTAL, 's')
