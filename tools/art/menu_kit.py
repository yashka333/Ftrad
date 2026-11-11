"""Shared kit for menu art: crisp pixel text, baked lighting, materials and frames.

Everything is drawn at the game's native resolution (640x360) and shown at a
whole-number scale, so menus share the pixel grid and lighting of the offices.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from px2 import INK, Canvas, dither, mix, sh

FONT_DIR = Path(__file__).parent / 'fonts'
_FONTS = {
    'title': (FONT_DIR / 'jersey-10-latin-400-normal.woff', 20),
    'head': (FONT_DIR / 'jersey-15-latin-400-normal.woff', 15),
    'body': (FONT_DIR / 'tiny5-latin-400-normal.woff', 8),
}
_cache: dict = {}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

GOLD, GOLD_HI, GOLD_LO = (236, 186, 72), (255, 226, 130), (170, 120, 40)
TEXT, MUTED = (244, 234, 216), (176, 164, 152)


# ---------------------------------------------------------------- text
def text_mask(s: str, style: str = 'body') -> np.ndarray:
    key = (s, style)
    if key in _cache:
        return _cache[key]
    if style == 'head' and 'K' in s:
        # Jersey 15 draws K like H at this size: compose from the glyph strips with a hand-drawn K
        from glyphs import export
        if 'head-glyphs' not in _cache:
            _cache['head-glyphs'] = export('head')
        gl = _cache['head-glyphs']
        cols = []
        for i, ch in enumerate(s):
            rows = (gl['g'].get(ch) or gl['g']['?']).split('|')
            arr = np.array([[c == '#' for c in r] for r in rows], bool)
            cols.append(arr)
            if i < len(s) - 1:
                cols.append(np.zeros((arr.shape[0], 1), bool))
        m = np.concatenate(cols, 1)
        ys = np.nonzero(m.any(1))[0]
        m = m[ys.min():ys.max() + 1]
        _cache[key] = m
        return m
    path, size = _FONTS[style]
    font = ImageFont.truetype(str(path), size)
    l, t, r, b = font.getbbox(s)
    img = Image.new('L', (r - l + 4, b - t + 4), 0)
    d = ImageDraw.Draw(img)
    d.fontmode = '1'
    d.text((2 - l, 2 - t), s, font=font, fill=255)
    m = np.array(img) > 127
    ys, xs = np.nonzero(m)
    if len(xs):
        m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    _cache[key] = m
    return m


def text_size(s, style='body'):
    m = text_mask(s, style)
    return m.shape[1], m.shape[0]


def draw_text(c: Canvas, s, x, y, col, style='body', shadow=INK, outline=None, align='left'):
    m = text_mask(s, style)
    if align == 'center':
        x -= m.shape[1] // 2
    elif align == 'right':
        x -= m.shape[1]
    if outline:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            c.mask(m, x + dx, y + dy, outline)
    if shadow:
        c.mask(m, x + 1, y + 1, shadow)
    c.mask(m, x, y, col)
    return m.shape[1], m.shape[0]


def gradient_text(c: Canvas, s, x, y, top, bottom, style='title', shadow=INK, outline=INK, align='left'):
    """Two-tone title: lighter top half, darker bottom half, inked outline."""
    m = text_mask(s, style)
    if align == 'center':
        x -= m.shape[1] // 2
    if outline:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            c.mask(m, x + dx, y + dy, outline)
    if shadow:
        c.mask(m, x + 1, y + 2, shadow)
    h = m.shape[0]
    for j in range(h):
        row = np.zeros_like(m)
        row[j] = m[j]
        c.mask(row, x, y, top if j < h * .5 else bottom)
    return m.shape[1], h


# ------------------------------------------------------------- lighting
class Lights:
    """Baked light map: ambient plus point, cone and box lights, applied with
    dithered banding so it matches the runtime office lighting."""

    def __init__(self, w, h, ambient):
        self.w, self.h = w, h
        self.L = np.zeros((h, w, 3))
        self.L[:] = ambient
        self.yy, self.xx = np.mgrid[0:h, 0:w]

    def point(self, x, y, r, col, i=1.0, cone=False, squash=1.0):
        d = np.sqrt((self.xx - x) ** 2 + ((self.yy - y) / squash) ** 2)
        f = np.clip(1 - d / r, 0, 1) ** 2 * i
        if cone:
            c = np.clip((self.yy - y) / (d + 1e-6), 0, 1)
            f *= 0.18 + 0.82 * c ** 0.8
        self.L += f[..., None] * np.array(col)

    def spot(self, x, y, half_angle, length, col, i=1.0):
        """Downward spotlight: bright inside a cone, soft at the edges."""
        dy = self.yy - y
        dx = self.xx - x
        ang = np.abs(np.arctan2(dx, np.maximum(dy, 1e-3)))
        inside = np.clip(1 - ang / half_angle, 0, 1) ** 0.7
        fall = np.clip(1 - np.sqrt(dx ** 2 + dy ** 2) / length, 0, 1) ** 1.2
        f = np.where(dy > 0, inside * fall * i, 0)
        self.L += f[..., None] * np.array(col)

    def apply(self, albedo: np.ndarray, levels=9) -> np.ndarray:
        th = 0.5 + (BAYER[self.yy % 4, self.xx % 4] - 0.5) * 0.45
        q = np.floor(np.clip(self.L, 0, 1.35) * levels + th[..., None]) / levels
        out = albedo.copy()
        out[..., :3] = np.clip(albedo[..., :3].astype(float) * q, 0, 255).astype(np.uint8)
        return out


def lit(c: Canvas, lights: Lights, emissive: Canvas | None = None) -> Canvas:
    out = Canvas(c.w, c.h)
    out.a = lights.apply(c.a)
    if emissive is not None:
        a = emissive.a[..., 3:4] / 255.0
        out.a[..., :3] = (out.a[..., :3] * (1 - a) + emissive.a[..., :3] * a).astype(np.uint8)
        out.a[..., 3] = np.maximum(out.a[..., 3], emissive.a[..., 3])
    return out


def bloom(c: Canvas, emissive: Canvas, col_scale=0.5, radius=3):
    """Cheap dithered glow around self-lit pixels."""
    a = emissive.a[..., 3] > 0
    if not a.any():
        return
    ys, xs = np.nonzero(a)
    rgb = emissive.a[..., :3].astype(float)
    acc = np.zeros((c.h, c.w, 3))
    wsum = np.zeros((c.h, c.w))
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                continue
            wgt = max(0, 1 - math.hypot(dx, dy) / (radius + .5))
            sh_a = np.roll(np.roll(a, dy, 0), dx, 1)
            sh_c = np.roll(np.roll(rgb, dy, 0), dx, 1)
            acc += sh_c * (sh_a * wgt)[..., None]
            wsum += sh_a * wgt
    m = (wsum > 0) & ~a
    yy, xx = np.mgrid[0:c.h, 0:c.w]
    m &= ((xx + yy) % 2 == 0)
    glow = acc[m] / np.maximum(wsum[m], 1e-6)[:, None]
    k = np.clip(wsum[m] / 6, 0, 1)[:, None] * col_scale
    base = c.a[m][:, :3].astype(float)
    c.a[m, :3] = np.clip(base * (1 - k) + glow * k, 0, 255).astype(np.uint8)


# ------------------------------------------------------------ materials
def brick_wall(c: Canvas, x0, y0, x1, y1, rng, bricks=None, mortar=(52, 38, 38), bw=16, bh=7):
    bricks = bricks or [(120, 66, 52), (110, 60, 48), (128, 74, 58), (100, 56, 46), (118, 70, 56)]
    c.rect(x0, y0, x1, y1, mortar)
    for row, y in enumerate(range(y0, y1 + 1, bh)):
        off = (bw // 2) * (row % 2)
        for x in range(x0 - off, x1 + 1, bw):
            col = bricks[int(rng.integers(0, len(bricks)))]
            a, b = max(x0, x), min(x1, x + bw - 2)
            yb = min(y1, y + bh - 2)
            if b < a:
                continue
            c.rect(a, y, b, yb, col)
            c.hline(a, b, y, sh(col, 1.12))
            c.hline(a, b, yb, sh(col, .8))
            for _ in range(int(rng.integers(1, 5))):
                c.px(rng.integers(a, b + 1), rng.integers(y, yb + 1), sh(col, rng.choice([.85, 1.1])))
            if rng.random() < .15:
                c.px(b, yb, mortar)


def wood_planks(c: Canvas, x0, y0, x1, y1, rng, cols=None, vertical=False, plank=6):
    cols = cols or [(104, 64, 40), (96, 58, 36), (112, 70, 44), (90, 54, 34)]
    if vertical:
        for x in range(x0, x1 + 1, plank):
            col = cols[int(rng.integers(0, len(cols)))]
            c.rect(x, y0, min(x1, x + plank - 2), y1, col)
            c.vline(min(x1, x + plank - 1), y0, y1, sh(col, .6))
            c.vline(x, y0, y1, sh(col, 1.12))
            for _ in range((y1 - y0) // 6):
                gy = int(rng.integers(y0, y1 + 1))
                c.vline(int(rng.integers(x, min(x1, x + plank - 2) + 1)), gy, min(y1, gy + int(rng.integers(2, 6))), sh(col, .85))
    else:
        for y in range(y0, y1 + 1, plank):
            col = cols[int(rng.integers(0, len(cols)))]
            c.rect(x0, y, x1, min(y1, y + plank - 2), col)
            c.hline(x0, x1, min(y1, y + plank - 1), sh(col, .6))
            c.hline(x0, x1, y, sh(col, 1.12))
            for _ in range((x1 - x0) // 8):
                gx = int(rng.integers(x0, x1 + 1))
                c.hline(gx, min(x1, gx + int(rng.integers(3, 9))), int(rng.integers(y, min(y1, y + plank - 2) + 1)), sh(col, .85))


def metal_plate(c: Canvas, x0, y0, x1, y1, base=(58, 54, 66), rivets=True):
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, base)
    c.hline(x0 + 1, x1 - 1, y0 + 1, sh(base, 1.45))
    c.hline(x0 + 1, x1 - 1, y0 + 2, sh(base, 1.2))
    c.vline(x0 + 1, y0 + 1, y1 - 1, sh(base, 1.25))
    c.hline(x0 + 1, x1 - 1, y1 - 1, sh(base, .6))
    c.vline(x1 - 1, y0 + 2, y1 - 1, sh(base, .7))
    # brushed streaks
    for y in range(y0 + 3, y1 - 1, 2):
        for x in range(x0 + 3, x1 - 2, 7):
            c.px(x + (y * 3) % 5, y, sh(base, 1.08))
    if rivets:
        for (rx, ry) in ((x0 + 3, y0 + 3), (x1 - 3, y0 + 3), (x0 + 3, y1 - 3), (x1 - 3, y1 - 3)):
            c.px(rx, ry, sh(base, 1.7)); c.px(rx + 1, ry + 1, sh(base, .5))


def brass_inset(c: Canvas, x0, y0, x1, y1, fill=(16, 13, 18)):
    """Dark readout window with a brass rim (for balances and counters)."""
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, GOLD_LO)
    c.hline(x0 + 1, x1 - 1, y0 + 1, GOLD_HI)
    c.vline(x0 + 1, y0 + 1, y1 - 1, GOLD)
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, INK)
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, fill)
    c.hline(x0 + 3, x1 - 3, y0 + 3, sh(fill, .6))


def frame_card(c: Canvas, w, h, accent, wood=(70, 42, 28)):
    """Framed board: dark wood moulding, brass fillet, accent enamel strip, dark panel."""
    c.rect(0, 0, w - 1, h - 1, INK)
    # wood moulding with bevel
    c.rect(1, 1, w - 2, h - 2, wood)
    for k in range(1, 5):
        c.hline(k, w - 1 - k, k, sh(wood, 1.45 - k * .08))
        c.vline(k, k, h - 1 - k, sh(wood, 1.3 - k * .06))
        c.hline(k, w - 1 - k, h - 1 - k, sh(wood, .55 + k * .05))
        c.vline(w - 1 - k, k, h - 1 - k, sh(wood, .62 + k * .05))
    # brass fillet
    c.rect(5, 5, w - 6, h - 6, INK)
    c.rect(6, 6, w - 7, h - 7, GOLD_LO)
    c.hline(6, w - 7, 6, GOLD_HI)
    c.vline(6, 6, h - 7, GOLD)
    # panel
    c.rect(7, 7, w - 8, h - 8, INK)
    c.rect(8, 8, w - 9, h - 9, (26, 22, 30))
    # corner caps
    for (x, y) in ((2, 2), (w - 6, 2), (2, h - 6), (w - 6, h - 6)):
        c.rect(x, y, x + 3, y + 3, GOLD_LO)
        c.px(x + 1, y + 1, GOLD_HI)


def enamel_plate(c: Canvas, x0, y0, x1, y1, col):
    """Title plate: enamel colour, glossy top line, dark bottom, inked outline."""
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, sh(col, .55))
    c.rect(x0 + 1, y0 + 1, x1 - 1, (y0 + y1) // 2, sh(col, .68))
    c.hline(x0 + 2, x1 - 2, y0 + 1, sh(col, 1.0))
    c.hline(x0 + 1, x1 - 1, y1 - 1, sh(col, .4))
    for (rx, ry) in ((x0 + 2, (y0 + y1) // 2), (x1 - 2, (y0 + y1) // 2)):
        c.px(rx, ry, GOLD_HI)


def coin(c: Canvas, x, y, r=6):
    c.ellipse(x, y, r, r, INK)
    c.ellipse(x, y, r - 1, r - 1, GOLD_LO)
    c.ellipse(x - .5, y - .5, r - 2, r - 2, GOLD)
    m = text_mask('F', 'body')
    c.mask(m, x - m.shape[1] // 2, y - m.shape[0] // 2, GOLD_LO)
    c.px(x - r + 2, y - 2, GOLD_HI); c.px(x - r + 3, y - 3, GOLD_HI)
