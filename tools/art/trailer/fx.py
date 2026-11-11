"""Trailer helpers at native 640x360: pixel text, plates, glow, particles, dissolves."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageFilter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from px2 import INK, Canvas, mix, sh  # noqa: E402
from menu_kit import GOLD, GOLD_HI, GOLD_LO, brass_inset, coin, text_mask  # noqa: E402

W, H, FPS = 640, 360, 30
B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
YY, XX = np.mgrid[0:H, 0:W]
BAYER = B4[(YY // 2) % 4, (XX // 2) % 4]          # 2px dither cells: chunky, like the art
BAYER1 = B4[YY % 4, XX % 4]


def ease_out(t):
    t = min(max(t, 0), 1)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = min(max(t, 0), 1)
    return t ** 3


def ease_back(t):
    t = min(max(t, 0), 1)
    c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def clamp01(v):
    return min(max(v, 0.0), 1.0)


# ------------------------------------------------------------------ text
_SPACED = {}


def spaced_mask(s, style='title', track=1):
    """Pixel text drawn letter by letter with an extra gap, so letters never touch."""
    key = (s, style, track)
    if key in _SPACED:
        return _SPACED[key]
    from PIL import ImageDraw, ImageFont
    from menu_kit import _FONTS
    path, size = _FONTS[style]
    font = ImageFont.truetype(str(path), size)
    asc, desc = font.getmetrics()
    width = int(sum(font.getlength(ch) + track for ch in s)) + 8
    img = Image.new('L', (width, asc + desc + 6), 0)
    d = ImageDraw.Draw(img)
    d.fontmode = '1'
    x = 2.0
    for ch in s:
        d.text((round(x), 2), ch, font=font, fill=255)
        x += font.getlength(ch) + track
    m = np.array(img) > 127
    ys, xs = np.nonzero(m)
    if len(xs):
        m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    _SPACED[key] = m
    return m


def big_mask(s, style='title', scale=2):
    m = spaced_mask(s, style)
    return np.kron(m, np.ones((scale, scale), bool)) if scale > 1 else m


def stamp(c: Canvas, m, x, y, col, alpha=255):
    h, w = m.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(c.w, x + w), min(c.h, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = m[y0 - y:y1 - y, x0 - x:x1 - x]
    region = c.a[y0:y1, x0:x1]
    if alpha >= 255:
        region[sub, :3] = col
        region[sub, 3] = 255
    else:
        k = alpha / 255
        region[sub, :3] = (region[sub, :3] * (1 - k) + np.array(col) * k).astype(np.uint8)


def title(c: Canvas, s, cx, y, top=GOLD_HI, bottom=GOLD, scale=2, style='title', reveal=1.0, ink=INK, shadow=3):
    """Chunky two-tone title with a thick ink outline and drop shadow. Returns (x, w, h)."""
    m = big_mask(s, style, scale)
    h, w = m.shape
    x = cx - w // 2
    if reveal < 1:
        m = m.copy()
        m[:, int(w * clamp01(reveal)):] = False
    o = max(1, scale)
    stamp(c, m, x + shadow // 2, y + shadow, (0, 0, 0), 200)
    for dx in range(-o, o + 1):
        for dy in range(-o, o + 1):
            if abs(dx) + abs(dy) <= o + 1 and (dx or dy):
                stamp(c, m, x + dx, y + dy, ink)
    top_m, bot_m = m.copy(), m.copy()
    top_m[h // 2:] = False
    bot_m[:h // 2] = False
    stamp(c, top_m, x, y, top)
    stamp(c, bot_m, x, y, bottom)
    hl = np.zeros_like(m)
    hl[1:] = m[1:] & ~m[:-1]                       # top edge of every stroke
    hl[h // 2:] = False
    stamp(c, hl, x, y, mix(top, (255, 255, 255), .55))
    return x, w, h


def plain(c: Canvas, s, cx, y, col, style='head', scale=1, ink=INK, align='center', alpha=255):
    m = big_mask(s, style, scale)
    h, w = m.shape
    x = cx - w // 2 if align == 'center' else cx
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
        stamp(c, m, x + dx, y + dy, ink, alpha)
    stamp(c, m, x, y, col, alpha)
    return x, w, h


def band(c: Canvas, y0, y1, strength=0.72, x0=0, x1=W):
    """Dark see-through strip with dithered top and bottom edges, for captions."""
    a = c.a if hasattr(c, "a") else c
    for y in range(max(0, y0 - 4), min(H, y1 + 5)):
        k = strength
        if y < y0:
            k *= (y - (y0 - 4)) / 5
        elif y > y1:
            k *= ((y1 + 5) - y) / 5
        row = a[y, x0:x1, :3].astype(float) * (1 - k)
        if y < y0 or y > y1:
            keep = BAYER1[y, x0:x1] < 0.5
            row = np.where(keep[:, None], a[y, x0:x1, :3], row)
        a[y, x0:x1, :3] = row.astype(np.uint8)


def chip(c: Canvas, x0, y0, x1, y1, col, fill=(16, 13, 18)):
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, col)
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, fill)


# ------------------------------------------------------------------ glow & light
def glow_layer(mask: np.ndarray, col, radius=6, power=2.2, levels=(150, 90, 40)):
    """Stepped, dithered glow around a mask: an RGBA overlay."""
    img = Image.fromarray((mask * 255).astype(np.uint8))
    g = np.array(img.filter(ImageFilter.GaussianBlur(radius))).astype(float) / 255
    g = np.clip(g * power, 0, 1)
    a = np.select([g > .6, g > .32, g > .1], list(levels), 0).astype(np.uint8)
    a = np.where((a == levels[-1]) & (BAYER1 > .5), 0, a).astype(np.uint8)
    out = np.zeros(mask.shape + (4,), np.uint8)
    out[..., :3] = col
    out[..., 3] = a
    return out


def over(dst: np.ndarray, src: np.ndarray, k: float = 1.0):
    """Alpha-composite src onto dst (both HxWx4 uint8) in place."""
    a = src[..., 3:4].astype(float) / 255 * k
    if not a.any():
        return dst
    dst[..., :3] = (dst[..., :3] * (1 - a) + src[..., :3] * a).astype(np.uint8)
    return dst


def add_light(dst: np.ndarray, src: np.ndarray, k=1.0):
    """Additive blend of src RGB weighted by its alpha."""
    a = src[..., 3:4].astype(float) / 255 * k
    dst[..., :3] = np.clip(dst[..., :3] + src[..., :3] * a, 0, 255).astype(np.uint8)


def blit(dst: np.ndarray, spr: np.ndarray, x, y, shade=1.0, alpha=1.0):
    h, w = spr.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 0
    if alpha < 1:
        m &= BAYER[y0:y1, x0:x1] < alpha
    rgb = s[..., :3].astype(float) * shade
    reg = dst[y0:y1, x0:x1]
    reg[m, :3] = np.clip(rgb[m], 0, 255).astype(np.uint8)
    reg[m, 3] = 255


def flash(dst: np.ndarray, k, col=(255, 255, 255)):
    if k <= 0:
        return
    dst[..., :3] = (dst[..., :3] * (1 - k) + np.array(col) * k).astype(np.uint8)


def darken(dst: np.ndarray, k):
    if k <= 0:
        return
    dst[..., :3] = (dst[..., :3] * (1 - k)).astype(np.uint8)


def dissolve(a: np.ndarray, b: np.ndarray, k):
    """Ordered-dither crossfade from a to b."""
    m = BAYER < k
    out = a.copy()
    out[m] = b[m]
    return out


def fade_black(dst: np.ndarray, k):
    m = BAYER < k
    dst[m, :3] = 0


# ------------------------------------------------------------------ sparkles & particles
def sparkle(dst: np.ndarray, x, y, size, col=(255, 248, 214)):
    x, y = int(x), int(y)
    pts = [(0, 0)]
    for k in range(1, size + 1):
        pts += [(k, 0), (-k, 0), (0, k), (0, -k)]
    if size >= 2:
        pts += [(1, 1), (-1, -1), (1, -1), (-1, 1)]
    for dx, dy in pts:
        X, Y = x + dx, y + dy
        if 0 <= X < W and 0 <= Y < H:
            c = col if (abs(dx) + abs(dy)) < size else mix(col, (255, 200, 90), .5)
            dst[Y, X, :3] = c


class Particles:
    def __init__(self, seed=1):
        self.rng = np.random.default_rng(seed)
        self.p = []

    def burst(self, x, y, n, speed=(1.5, 4.5), cols=None, life=(0.6, 1.2), grav=0.12, size=(1, 2), up=0.0):
        cols = cols or [(255, 226, 130), (236, 186, 72), (255, 255, 255)]
        for _ in range(n):
            a = self.rng.uniform(0, 2 * math.pi)
            v = self.rng.uniform(*speed)
            self.p.append(dict(x=x, y=y, vx=math.cos(a) * v, vy=math.sin(a) * v - up, g=grav,
                               life=self.rng.uniform(*life), age=0.0, col=cols[int(self.rng.integers(len(cols)))],
                               s=int(self.rng.integers(size[0], size[1] + 1))))

    def step(self, dt=1 / FPS):
        for q in self.p:
            q['x'] += q['vx']; q['y'] += q['vy']; q['vy'] += q['g']; q['vx'] *= 0.97
            q['age'] += dt
        self.p = [q for q in self.p if q['age'] < q['life']]

    def draw(self, dst):
        for q in self.p:
            k = 1 - q['age'] / q['life']
            x, y = int(q['x']), int(q['y'])
            if BAYER1[y % H, x % W] > k + .15:
                continue
            for dx in range(q['s']):
                for dy in range(q['s']):
                    X, Y = x + dx, y + dy
                    if 0 <= X < W and 0 <= Y < H:
                        dst[Y, X, :3] = q['col']


# ------------------------------------------------------------------ HUD
def balance_hud(dst: np.ndarray, value: int, x=8, y=8):
    c = Canvas(W, H)
    c.a = dst
    brass_inset(c, x, y, x + 134, y + 24)
    coin(c, x + 13, y + 12, 6)
    s = f'{value:,}'
    m = text_mask(s, 'title')
    stamp(c, m, x + 26, y + 5, GOLD_HI)
    mm = text_mask('$FROG', 'body')
    stamp(c, mm, x + 130 - mm.shape[1], y + 9, (176, 164, 152))


def coin_pop(dst: np.ndarray, x, y, age, amount, life=1.1):
    """A '+N $FROG' that floats up from a desk and fades."""
    if age < 0 or age > life:
        return
    k = age / life
    yy = int(y - 34 * ease_out(k))
    c = Canvas(W, H)
    c.a = dst
    alpha = 1.0 if k < .65 else 1 - (k - .65) / .35
    s = f'+{amount}'
    m = text_mask(s, 'head')
    tw = m.shape[1] + 14
    x0 = int(x - tw // 2)
    if alpha >= 1 or BAYER1[yy % H, x0 % W] < alpha:
        coin(c, x0 + 5, yy + 6, 5)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
            stamp(c, m, x0 + 13 + dx, yy + dy, INK)
        stamp(c, m, x0 + 13, yy, GOLD_HI)
