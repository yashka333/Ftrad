"""Clean cut-outs of the boss frogs from their framed portraits (boss-*.png -> build/boss-*-clean.png).

The frogs are inked with a near-black outline, so the background is flood-filled
from the edges and stops at that outline. The desk strip at the bottom is dropped.
"""
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'client/src/assets/menu'
OUT = Path(__file__).parent / 'build'
OUT.mkdir(exist_ok=True)
DESK = {'orig': 88, 'blue': 88, 'purple': 87, 'green': 89}
INK = {'orig': 34, 'blue': 62, 'purple': 34, 'green': 34}
SIDE_SEED = {'orig': 99, 'blue': 99, 'purple': 99, 'green': 40}   # seed the side edges only above this row


def cut(key):
    ink = INK[key]
    a = np.array(Image.open(SRC / f'boss-{key}.png').convert('RGBA'))
    y_desk = DESK[key]
    a = a[:y_desk].copy()
    h, w = a.shape[:2]
    rgb = a[..., :3].astype(int)
    barrier = rgb.max(2) < ink
    bg = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        q.append((0, x))
    for y in range(min(h, SIDE_SEED[key])):
        q.append((y, 0)); q.append((y, w - 1))
    while q:
        y, x = q.popleft()
        if not (0 <= y < h and 0 <= x < w) or bg[y, x] or barrier[y, x]:
            continue
        bg[y, x] = True
        q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    fg = ~bg
    lab, n = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    keep = lab == (int(np.argmax(sizes)) + 1)
    a[~keep, 3] = 0
    if key == 'blue':
        a[:, :11, 3] = 0          # the monitor behind his shoulder
    # the outline on the cut bottom edge: ink the last row so the bust sits cleanly
    return a


if __name__ == '__main__':
    tiles = []
    for k in DESK:
        a = cut(k)
        Image.fromarray(a).save(OUT / f'boss-{k}-clean.png')
        tiles.append(a)
    sheet = Image.new('RGBA', (len(tiles) * 105, 100), (255, 0, 255, 255))
    for i, t in enumerate(tiles):
        im = Image.fromarray(t)
        sheet.paste(im, (i * 105, 0), im)
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save('/tmp/claude-0/-home-claude/f782d41d-8771-50ed-9d54-4ef8681aae6f/scratchpad/clean.png')
