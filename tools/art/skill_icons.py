"""Turns the painted skill icon sheet (source/skills/skills-ref.png, 7x2 tiles) into small pixel icons.

Each tile: drop the dark tile background, crop to the drawing, shrink with area averaging,
cut the palette down, snap alpha, re-ink the outline. Writes source/skills/px/<skill>.png.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).parent
SRC = HERE / 'source/skills/skills-ref.png'
OUT = HERE / 'source/skills/px'
ORDER = [['diamondHands', 'powerNap', 'fastFingers', 'caffeine', 'stopLoss', 'hotStreak', 'dipBuyer'],
         ['degenMode', 'luckyCharm', 'copyTrader', 'nightOwl', 'whaleHunter', 'rugRadar', 'insider']]
INK = np.array([20, 18, 22])


def tiles(img):
    a = np.array(img.convert('RGB')).astype(int)
    bg = a[100, 30]
    on = np.abs(a - bg).sum(2) < 22
    # tile boxes: long runs of tile background colour
    colmask = on.mean(0) > 0.25
    rowmask = on.mean(1) > 0.25
    def runs(m, minlen):
        out, start = [], None
        for i, v in enumerate(list(m) + [False]):
            if v and start is None:
                start = i
            elif not v and start is not None:
                if i - start >= minlen:
                    out.append((start, i - 1))
                start = None
        return out
    xs = runs(colmask, 3)
    ys = runs(rowmask, 3)
    return a, bg, xs, ys


def tile_boxes(a):
    """Tiles are lighter squares on the darker sheet: find them by the sheet colour."""
    sheet = a[5, 5]
    off = np.abs(a - sheet).sum(2) > 12
    lab, n = ndimage.label(ndimage.binary_opening(off, iterations=3))
    boxes = []
    for sl in ndimage.find_objects(lab):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if h > 200 and w > 200:
            boxes.append((sl[0].start, sl[1].start, sl[0].stop, sl[1].stop))
    boxes.sort(key=lambda b: (round(b[0] / 100), b[1]))
    return boxes


def pixelize(tile, bg, size):
    t = tile.astype(int)
    fg = np.abs(t - bg).sum(2) > 34
    fg = ndimage.binary_opening(fg, iterations=1)
    lab, n = ndimage.label(fg)
    if n > 1:  # drop specks far from the drawing
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        fg = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 120])
    ys, xs = np.nonzero(fg)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    side = max(y1 - y0, x1 - x0) + 1
    cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    pad = side // 2
    rgba = np.zeros(t.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = tile
    rgba[..., 3] = np.where(fg, 255, 0)
    big = np.zeros((t.shape[0] + side * 2, t.shape[1] + side * 2, 4), np.uint8)
    big[side:side + t.shape[0], side:side + t.shape[1]] = rgba
    crop = big[cy + side - pad:cy + side - pad + side, cx + side - pad:cx + side - pad + side]
    inner = size - 2  # leave room for the outline
    im = Image.fromarray(crop, 'RGBA')
    # premultiplied area average
    arr = np.array(im).astype(float)
    arr[..., :3] *= arr[..., 3:4] / 255
    small = np.array(Image.fromarray(arr.astype(np.uint8), 'RGBA').resize((inner, inner), Image.BOX)).astype(float)
    alpha = small[..., 3] / 255
    rgb = np.where(alpha[..., None] > 0, small[..., :3] / np.maximum(alpha[..., None], 1e-6), 0)
    keep = alpha > 0.42
    # palette: 10 colours per icon, chosen from the kept pixels
    pix = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB')
    q = pix.quantize(colors=10, method=Image.Quantize.MEDIANCUT)
    rgbq = np.array(q.convert('RGB'))
    # boost contrast a little: pixel art reads better slightly punchier
    rgbq = np.clip((rgbq.astype(float) - 128) * 1.08 + 132, 0, 255).astype(np.uint8)
    out = np.zeros((size, size, 4), np.uint8)
    out[1:-1, 1:-1, :3] = rgbq
    out[1:-1, 1:-1, 3] = np.where(keep, 255, 0)
    # very dark pixels become ink; then a clean outer outline
    a = out[..., 3] > 0
    dark = a & (out[..., :3].astype(int).sum(2) < 120)
    out[dark, :3] = INK
    pad_a = np.pad(a, 1)
    ring = ~a & (pad_a[:-2, 1:-1] | pad_a[2:, 1:-1] | pad_a[1:-1, :-2] | pad_a[1:-1, 2:])
    out[ring, :3] = INK
    out[ring, 3] = 255
    return out


def main(size=16):
    OUT.mkdir(parents=True, exist_ok=True)
    img = Image.open(SRC)
    a = np.array(img.convert('RGB')).astype(int)
    boxes = tile_boxes(a)
    assert len(boxes) == 14, f'found {len(boxes)} tiles'
    names = ORDER[0] + ORDER[1]
    icons = {}
    for (y0, x0, y1, x1), name in zip(boxes, names):
        tile = a[y0 + 6:y1 - 6, x0 + 6:x1 - 6]
        bg = np.median(tile[:12, :12].reshape(-1, 3), 0)
        icons[name] = pixelize(tile.astype(np.uint8), bg, size)
        Image.fromarray(icons[name], 'RGBA').save(OUT / f'{name}.png')
    return icons


if __name__ == '__main__':
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    icons = main(size)
    sheet = np.zeros((size + 4, 14 * (size + 4), 4), np.uint8)
    sheet[..., :3] = (34, 30, 40); sheet[..., 3] = 255
    for i, ic in enumerate(icons.values()):
        m = ic[..., 3] > 0
        sheet[2:2 + size, 2 + i * (size + 4):2 + i * (size + 4) + size][m] = ic[m]
    Image.fromarray(sheet).resize((sheet.shape[1] * 6, sheet.shape[0] * 6), Image.NEAREST).save(
        '/tmp/claude-0/-home-claude/f782d41d-8771-50ed-9d54-4ef8681aae6f/scratchpad/skillpx.png')
    print('ok', size)
