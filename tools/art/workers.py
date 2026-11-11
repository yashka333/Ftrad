"""Digitize the AI-generated worker frog sheet into clean native pixel art.

The reference image is "fake" pixel art: blocks of roughly 6 px with drift,
blurred edges and hundreds of near-duplicate colors. This script:
  1. cuts each frog out of the sheet,
  2. finds the real pixel grid per frog with dynamic programming
     (cut lines follow strong color edges, gaps stay near the block size),
  3. samples one color per cell (median of the cell core),
  4. maps everything onto one shared palette,
  5. cleans stray pixels and unifies the outline.

Output: client/src/assets/frogs/worker-<rarity>.png (native size, transparent).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'tools/art/source/workers/workers-ref.png'
OUT = ROOT / 'client/src/assets/frogs'
RARITY_ORDER = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
BG = np.array([37, 37, 39])


def find_frogs(img: np.ndarray):
    fg = np.abs(img - BG).sum(2) > 30
    fg = ndimage.binary_closing(fg, iterations=3)
    lab, n = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    objs = ndimage.find_objects(lab)
    boxes = [objs[i] for i in range(n) if sizes[i] > 5000]
    # reading order: top row then bottom row, left to right
    boxes.sort(key=lambda s: ((s[0].start + s[0].stop) // 2 > img.shape[0] // 2, s[1].start))
    return boxes


def grid_cuts(profile: np.ndarray, block: float) -> list[int]:
    """Choose cut positions maximizing edge strength with gaps near `block`."""
    n = len(profile)
    lo, hi = int(np.floor(block - 1.6)), int(np.ceil(block + 1.6))
    norm = profile / (profile.max() + 1e-9)
    best = np.full(n + 1, -1e18)
    prev = np.full(n + 1, -1, dtype=int)
    for s in range(0, hi):
        best[s] = norm[s] if s < n else 0
    for i in range(hi, n + 1):
        gain = norm[i] if i < n else 0
        for g in range(lo, hi + 1):
            j = i - g
            if j < 0:
                continue
            v = best[j] + gain - 0.12 * abs(g - block)
            if v > best[i]:
                best[i], prev[i] = v, j
    end = int(np.argmax(best[n - hi:])) + n - hi
    cuts = [end]
    while prev[cuts[-1]] >= 0:
        cuts.append(prev[cuts[-1]])
    return sorted(cuts)


def sample(crop: np.ndarray, block: float):
    gx = np.abs(np.diff(crop, axis=1)).sum(2)
    gy = np.abs(np.diff(crop, axis=0)).sum(2)
    px = np.concatenate([[0], gx.sum(0)])
    py = np.concatenate([[0], gy.sum(1)])
    xs, ys = grid_cuts(px, block), grid_cuts(py, block)
    h, w = len(ys) - 1, len(xs) - 1
    out = np.zeros((h, w, 4), dtype=np.uint8)
    for r in range(h):
        for c in range(w):
            y0, y1, x0, x1 = ys[r], ys[r + 1], xs[c], xs[c + 1]
            core = crop[y0 + 1:max(y1 - 1, y0 + 2), x0 + 1:max(x1 - 1, x0 + 2)]
            pix = core.reshape(-1, 3)
            out[r, c, :3] = np.median(pix, axis=0)
            out[r, c, 3] = 255
    # Background = bg-colored cells connected to the border. Dark suits inside
    # the silhouette share the background's brightness, so a plain color test
    # would punch holes in them; the outline stops the flood fill instead.
    near = np.abs(out[..., :3].astype(int) - BG).sum(2) <= 16
    lab, _ = ndimage.label(near)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    out[np.isin(lab, list(border)), 3] = 0
    # Enclosed gaps (arm on hip, hand on head) are background too when they are
    # big and match the backdrop exactly; small dark patches are suit shading.
    exact = (np.abs(out[..., :3].astype(int) - BG).sum(2) <= 10) & (out[..., 3] > 0)
    lab, k = ndimage.label(exact)
    for i in range(1, k + 1):
        if (lab == i).sum() >= 12:
            out[lab == i, 3] = 0
    return out


def build_palette(sprites, k=48):
    from sklearn.cluster import KMeans
    cols = np.concatenate([s[s[..., 3] > 0][:, :3] for s in sprites]).astype(float)
    km = KMeans(n_clusters=k, n_init=8, random_state=3).fit(cols)
    pal = km.cluster_centers_
    # merge clusters that are visually identical
    merged: list[np.ndarray] = []
    for c in pal[np.argsort(pal.sum(1))]:
        if all(np.abs(c - m).sum() > 14 for m in merged):
            merged.append(c)
    return np.round(np.array(merged)).astype(np.uint8)


def quantize(s, pal):
    out = s.copy()
    m = s[..., 3] > 0
    px = s[m][:, :3].astype(int)
    d = ((px[:, None, :] - pal[None, :, :].astype(int)) ** 2).sum(2)
    out[m, :3] = pal[d.argmin(1)]
    return out


def cleanup(s):
    a = s[..., 3] > 0
    rgb = s[..., :3].astype(int)
    lum = rgb.mean(2)
    out = s.copy()
    # unify the outline: every very dark pixel becomes one ink color
    ink = (lum < 20) & a
    out[ink, :3] = (20, 18, 22)
    # drop single orphan pixels sitting outside the silhouette
    nb = ndimage.convolve(a.astype(int), np.ones((3, 3)), mode='constant') - a
    out[(a) & (nb <= 1), 3] = 0
    # fill single-pixel holes inside the silhouette
    hole = (~a) & (ndimage.convolve(a.astype(int), np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]]), mode='constant') == 4)
    for y, x in zip(*np.nonzero(hole)):
        nbrs = [out[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        out[y, x] = nbrs[0]
    # every edge pixel touching transparency gets the ink color (clean 1px outline)
    a2 = out[..., 3] > 0
    edge = a2 & ~ndimage.binary_erosion(a2, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    out[edge, :3] = (20, 18, 22)
    return out


def trim(s):
    ys, xs = np.nonzero(s[..., 3])
    return s[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def main(block: float = 6.2):
    img = np.array(Image.open(SRC).convert('RGB')).astype(int)
    boxes = find_frogs(img)
    assert len(boxes) == 6, len(boxes)
    sprites = []
    for sy, sx in boxes:
        crop = img[max(sy.start - 4, 0):sy.stop + 4, max(sx.start - 4, 0):sx.stop + 4]
        sprites.append(sample(crop, block))
    pal = build_palette(sprites)
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}
    for name, s in zip(RARITY_ORDER, sprites):
        s = trim(cleanup(quantize(s, pal)))
        Image.fromarray(s, 'RGBA').save(OUT / f'worker-{name}.png')
        meta[name] = {'w': int(s.shape[1]), 'h': int(s.shape[0])}
    (OUT / 'workers.json').write_text(json.dumps({'palette': len(pal), 'sprites': meta}, indent=2))
    print(json.dumps(meta), 'palette', len(pal))


if __name__ == '__main__':
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 6.2)
