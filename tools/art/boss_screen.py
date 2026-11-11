"""Boss Frogs screen placeholder: a black room with the title and an announcement teaser.

Outputs client/src/assets/boss-screen/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from px2 import INK, Canvas, mix, dither
from menu_kit import GOLD, GOLD_HI, GOLD_LO, text_mask
from menu2 import header

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'client/src/assets/boss-screen'
W, H = 640, 360


def big(c, s, cy, scale, top, bottom):
    """Title text at a whole-number scale with an ink outline and a two-tone fill."""
    m = np.kron(text_mask(s, 'title'), np.ones((scale, scale), bool))
    x, y = W // 2 - m.shape[1] // 2, cy - m.shape[0] // 2
    for dx, dy in ((-scale, 0), (scale, 0), (0, -scale), (0, scale)):
        c.mask(m, x + dx, y + dy, INK)
    c.mask(m, x + scale, y + scale * 2, (0, 0, 0))
    h = m.shape[0]
    for j in range(h):
        row = np.zeros_like(m)
        row[j] = m[j]
        c.mask(row, x, y, top if j < h * .5 else bottom)
    return x, y, m.shape[1], h


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    c = Canvas(W, H)
    c.rect(0, 0, W - 1, H - 1, (6, 5, 8))
    # a faint warm glow behind the title, dithered so it stays pixel art
    steps = [(6, 5, 8), (12, 9, 9), (18, 13, 9), (25, 18, 10)]
    for y in range(36, H):
        for x in range(W):
            k = max(0.0, 1 - (((x - W / 2) / 250) ** 2 + ((y - 172) / 110) ** 2))
            lv = k * k * (len(steps) - 1)
            i = int(lv)
            if i >= len(steps) - 1:
                c.px(x, y, steps[-1])
            elif lv > 0:
                c.px(x, y, steps[i + 1] if dither(x, y, lv - i) else steps[i])
    lay = {'size': [W, H], 'hud': header(c, 'BOSS FROGS'), 'cards': [], 'tiles': [], 'back': 'home'}
    _, ty, _, th = big(c, 'BOSS FROGS', 160, 3, GOLD_HI, GOLD)
    # thin gold rules under the title
    y = ty + th + 12
    for x in range(W // 2 - 90, W // 2 + 91):
        a = 1 - abs(x - W // 2) / 91
        if a > 0.15:
            c.px(x, y, mix((6, 5, 8), GOLD_LO, a))
    lay['soon'] = [W // 2, y + 12]
    Image.fromarray(c.a, 'RGBA').save(OUT / 'bg.png')
    (OUT / 'layout.json').write_text(json.dumps(lay))


if __name__ == '__main__':
    build()
    print('boss screen ok')
