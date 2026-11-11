"""Office pieces drawn as native pixel art: the worker desk unit.

Layer order for one desk (back to front):
  floor shadow, chair base, chair back, frog (clipped at the desk line),
  desk, desk props, monitor.
The frog layer is separate so the game can swap frogs and animate them.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FROGS = ROOT / 'client/src/assets/frogs'

INK = (20, 18, 22)

# Memecoin Trading: cheap plywood desk, worn olive chair, budget monitor.
P = {
    'top': (178, 128, 82), 'top_hi': (204, 156, 104), 'top_lo': (152, 106, 66),
    'front': (128, 86, 54), 'front_lo': (104, 68, 42), 'front_hi': (150, 104, 66),
    'panel': (74, 50, 36), 'panel_lo': (58, 38, 28),
    'metal': (78, 78, 90), 'metal_lo': (52, 52, 62), 'metal_hi': (110, 110, 124),
    'bezel': (66, 68, 80), 'bezel_hi': (96, 98, 112), 'bezel_lo': (44, 46, 56),
    'screen': (12, 20, 24), 'grid': (22, 36, 40), 'up': (92, 222, 112), 'down': (232, 82, 82),
    'chair': (64, 74, 50), 'chair_hi': (86, 98, 64), 'chair_lo': (44, 52, 34), 'foam': (214, 200, 150),
    'mug': (232, 226, 212), 'mug_lo': (190, 182, 168), 'coffee': (86, 56, 36),
    'can': (38, 38, 44), 'can_hi': (70, 70, 80), 'can_band': (126, 226, 84),
    'note': (246, 212, 76), 'note_lo': (214, 176, 50),
    'key': (196, 196, 204), 'key_lo': (150, 150, 162),
}


class Canvas:
    def __init__(self, w: int, h: int):
        self.a = np.zeros((h, w, 4), dtype=np.uint8)
        self.w, self.h = w, h

    def px(self, x, y, c, alpha=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            if alpha >= 255:
                self.a[y, x] = (*c, 255)
            else:
                old = self.a[y, x].astype(float)
                k = alpha / 255
                self.a[y, x, :3] = (old[:3] * (1 - k) + np.array(c) * k).astype(np.uint8)
                self.a[y, x, 3] = max(old[3], alpha)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x, y1, c)

    def box(self, x0, y0, x1, y1, fill, hi=None, lo=None):
        """Filled rectangle with ink outline and optional bevel."""
        self.rect(x0, y0, x1, y1, INK)
        self.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)
        if hi:
            self.hline(x0 + 1, x1 - 1, y0 + 1, hi)
            self.vline(x0 + 1, y0 + 1, y1 - 1, hi)
        if lo:
            self.hline(x0 + 1, x1 - 1, y1 - 1, lo)
            self.vline(x1 - 1, y0 + 2, y1 - 1, lo)

    def paste(self, img: np.ndarray, x, y, clip_y=None):
        h, w = img.shape[:2]
        for j in range(h):
            if clip_y is not None and y + j > clip_y:
                break
            for i in range(w):
                if img[j, i, 3]:
                    self.px(x + i, y + j, tuple(int(v) for v in img[j, i, :3]))

    def image(self):
        return Image.fromarray(self.a, 'RGBA')


def chair(c: Canvas, cx: int, top: int, bottom: int):
    """Worn office chair back with rounded top and tufted channels."""
    x0, x1 = cx - 16, cx + 15
    for y in range(top, bottom + 1):
        inset = 3 if y == top else 1 if y == top + 1 else 0
        c.hline(x0 + inset, x1 - inset, y, INK)
    for y in range(top + 1, bottom):
        inset = 3 if y == top + 1 else 1 if y == top + 2 else 1
        c.hline(x0 + inset, x1 - inset, y, P['chair'])
    c.hline(x0 + 3, x1 - 3, top + 1, P['chair_hi'])
    c.vline(x0 + 1, top + 3, bottom - 1, P['chair_hi'])
    c.vline(x1 - 1, top + 3, bottom - 1, P['chair_lo'])
    # three tufted channels
    for k in (-6, 5):
        c.vline(cx + k, top + 4, bottom - 3, P['chair_lo'])
        c.vline(cx + k + 1, top + 4, bottom - 3, P['chair_hi'])
    for y in range(top + 6, bottom - 3, 6):
        for k in (-11, -1, 10):
            c.px(cx + k, y, P['chair_lo'])
    # torn patch with foam
    for dx, dy in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2)):
        c.px(x1 - 7 + dx, top + 5 + dy, P['foam'])
    c.px(x1 - 4, top + 5, P['chair_lo'])


def chair_base(c: Canvas, cx: int, y: int):
    c.rect(cx - 1, y - 9, cx, y - 1, P['metal_lo'])
    c.px(cx - 1, y - 9, P['metal'])
    c.hline(cx - 11, cx + 10, y, INK)
    c.hline(cx - 10, cx + 9, y - 1, P['metal'])
    c.hline(cx - 10, cx + 9, y, P['metal_lo'])
    for wx in (cx - 12, cx - 1, cx + 10):
        c.rect(wx, y + 1, wx + 2, y + 2, INK)


def monitor(c: Canvas, mx: int, base_y: int, seed: int):
    """Budget flat monitor facing the viewer with a live-looking candle chart."""
    w, h = 36, 27
    x0, y0 = mx - w // 2, base_y - h - 8
    # stand
    c.box(mx - 7, base_y - 1, mx + 6, base_y + 2, P['metal'], P['metal_hi'], P['metal_lo'])
    c.box(mx - 2, base_y - 9, mx + 1, base_y - 1, P['metal'], P['metal_hi'], P['metal_lo'])
    # bezel and screen
    c.box(x0, y0, x0 + w - 1, y0 + h - 1, P['bezel'], P['bezel_hi'], P['bezel_lo'])
    sx0, sy0, sx1, sy1 = x0 + 3, y0 + 3, x0 + w - 4, y0 + h - 5
    c.rect(sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1, INK)
    c.rect(sx0, sy0, sx1, sy1, P['screen'])
    for gy in range(sy0 + 4, sy1, 5):
        for gx in range(sx0, sx1 + 1, 2):
            c.px(gx, gy, P['grid'])
    # candles: a rough uptrend with a red dip
    rng = np.random.default_rng(seed)
    level = sy1 - 4
    x = sx0 + 1
    while x + 2 <= sx1 - 1:
        move = int(rng.integers(-4, 6))
        up = move >= 0
        o, cl = level, max(sy0 + 2, min(sy1 - 1, level - move))
        hi_y, lo_y = min(o, cl) - int(rng.integers(1, 3)), max(o, cl) + int(rng.integers(0, 2))
        col = P['up'] if up else P['down']
        c.vline(x + 1, max(sy0, hi_y), min(sy1, lo_y), col)
        c.rect(x, min(o, cl), x + 2, max(o, cl), col)
        level = cl
        x += 4
    # power led and a sticky note on the bezel
    c.px(x0 + w - 5, y0 + h - 3, P['up'])
    c.rect(x0 - 2, y0 + 2, x0 + 3, y0 + 7, INK)
    c.rect(x0 - 1, y0 + 3, x0 + 2, y0 + 6, P['note'])
    c.hline(x0 - 1, x0 + 2, y0 + 6, P['note_lo'])
    return (sx0 + sx1) // 2, (sy0 + sy1) // 2


def desk(c: Canvas, x: int, y: int, W: int):
    """Cheap plywood desk. y = back edge of the desk top."""
    D = 9  # depth of the top seen from above
    # top surface
    c.rect(x, y, x + W - 1, y + D + 3, INK)
    c.rect(x + 1, y + 1, x + W - 2, y + D, P['top'])
    c.hline(x + 1, x + W - 2, y + 1, P['top_lo'])
    c.hline(x + 1, x + W - 2, y + D, P['top_hi'])
    # front edge thickness
    c.rect(x + 1, y + D + 1, x + W - 2, y + D + 2, P['front'])
    rng = np.random.default_rng(7)
    for _ in range(14):  # plywood grain
        gx, gy = int(rng.integers(x + 3, x + W - 10)), int(rng.integers(y + 2, y + D))
        c.hline(gx, gx + int(rng.integers(3, 8)), gy, P['top_lo'])
    # chipped corner
    c.px(x + W - 2, y + D + 1, P['front_lo'])
    c.px(x + W - 3, y + D + 2, P['front_lo'])
    top_end = y + D + 3
    floor = top_end + 29
    # modesty panel
    c.rect(x + 4, top_end, x + W - 5, top_end + 13, INK)
    c.rect(x + 5, top_end, x + W - 6, top_end + 12, P['panel'])
    c.hline(x + 5, x + W - 6, top_end, P['panel_lo'])
    # right leg
    c.box(x + W - 8, top_end - 1, x + W - 3, floor, P['metal'], P['metal_hi'], P['metal_lo'])
    # drawer pedestal on the left
    px0, px1 = x + 2, x + 28
    c.rect(px0, top_end - 1, px1, floor, INK)
    c.rect(px0 + 1, top_end, px1 - 1, floor - 1, P['front'])
    for d0, d1 in ((top_end + 1, top_end + 13), (top_end + 15, floor - 2)):
        c.box(px0 + 2, d0, px1 - 2, d1, P['front'], P['front_hi'], P['front_lo'])
        hy = (d0 + d1) // 2
        c.rect((px0 + px1) // 2 - 3, hy, (px0 + px1) // 2 + 3, hy + 1, INK)
        c.hline((px0 + px1) // 2 - 2, (px0 + px1) // 2 + 2, hy, P['metal_hi'])
    # meme sticker on the lower drawer
    sx, sy = px0 + 5, floor - 10
    c.rect(sx, sy, sx + 4, sy + 4, (110, 190, 90))
    c.px(sx + 1, sy + 1, INK)
    c.px(sx + 3, sy + 1, INK)
    c.hline(sx + 1, sx + 3, sy + 3, INK)
    return top_end, floor


def props(c: Canvas, x: int, y: int, fx: int):
    """Keyboard, mug and an energy drink on the desk top."""
    # keyboard in front of the frog
    c.box(fx - 13, y + 3, fx + 12, y + 7, P['key'], None, P['key_lo'])
    for kx in range(fx - 11, fx + 11, 2):
        c.px(kx, y + 4, P['key_lo'])
        c.px(kx + 1, y + 5, P['key_lo'])
    # mouse
    c.box(fx + 15, y + 4, fx + 18, y + 7, P['key'], None, P['key_lo'])
    # mug with coffee
    mx, my = x + 6, y + 6
    c.box(mx, my - 8, mx + 7, my, P['mug'], None, P['mug_lo'])
    c.hline(mx + 1, mx + 6, my - 7, P['coffee'])
    c.rect(mx - 2, my - 6, mx, my - 3, INK)
    c.px(mx - 1, my - 5, P['mug'])
    c.px(mx - 1, my - 4, P['mug'])
    # steam
    c.px(mx + 3, my - 10, (200, 196, 190), 120)
    c.px(mx + 4, my - 11, (200, 196, 190), 90)
    # energy drink
    cx, cy = x + 17, y + 5
    c.box(cx, cy - 10, cx + 5, cy, P['can'], P['can_hi'], None)
    c.rect(cx + 1, cy - 6, cx + 4, cy - 5, P['can_band'])
    c.hline(cx + 1, cx + 4, cy - 9, P['metal_hi'])


def glow(c: Canvas, gx: int, gy: int, color, radius: int, x_min: int):
    """Screen light falling on the frog and desk: two dithered rings."""
    for y in range(c.h):
        for x in range(x_min, c.w):
            if c.a[y, x, 3] == 0:
                continue
            d = ((x - gx) ** 2 + (y - gy) ** 2) ** 0.5
            if d < radius * 0.55:
                c.px(x, y, color, 30)
            elif d < radius and (x + y) % 2 == 0:
                c.px(x, y, color, 22)


def desk_unit(frog: str | None, seed: int = 1) -> Image.Image:
    W = 96
    c = Canvas(112, 100)
    x, y = 8, 56
    fx = x + 38
    floor = y + 9 + 3 + 29
    # floor shadow
    for sx in range(x - 2, x + W + 2):
        c.px(sx, floor + 1, (0, 0, 0), 90)
        if x + 4 <= sx <= x + W - 4:
            c.px(sx, floor + 2, (0, 0, 0), 60)
    chair_base(c, fx, floor - 2)
    chair(c, fx, y - 30, y + 6)
    mx = x + W - 22
    if frog:
        spr = np.array(Image.open(FROGS / f'worker-{frog}.png').convert('RGBA'))
        layer = Canvas(c.w, c.h)
        layer.paste(spr, fx - spr.shape[1] // 2, y - 50, clip_y=y + 2)
        # screen light on the frog's side facing the monitor
        glow(layer, mx - 18, y - 22, P['up'], 24, fx)
        c.paste(layer.a, 0, 0)
    desk(c, x, y, W)
    props(c, x, y, fx)
    monitor(c, mx, y + 4, seed)
    return c.image()


if __name__ == '__main__':
    out = ROOT / 'client/src/assets/office'
    out.mkdir(parents=True, exist_ok=True)
    desk_unit(None).save(out / 'desk-memecoin-empty.png')
    for f in ('common', 'rare', 'legendary'):
        desk_unit(f).save(out / f'desk-memecoin-{f}.png')
    print('ok')
