"""Art for the main menu cards, built from the project's own pixel art:
the crossroads scene and the boss (NFT) frog portraits."""
from __future__ import annotations
import json, os
from collections import deque
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16


def crossroads() -> np.ndarray:
    d = json.load(open(os.path.join(HERE, 'source', 'crossroads.json')))
    n = d['N']
    lut = {c: i for i, c in enumerate(d['alpha'])}
    pal = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in d['pal']], np.uint8)
    idx = np.array([lut[c] for c in d['data']]).reshape(n, n)
    return np.dstack([pal[idx], np.full((n, n), 255, np.uint8)])


def portraits() -> dict[str, np.ndarray]:
    d = json.load(open(os.path.join(HERE, 'source', 'desk-frogs.json')))
    out = {}
    for k, f in d.items():
        n = 99
        g = np.array([ord(c) - 65 for c in f['data']]).reshape(n, n)
        pal = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in f['pal']], np.uint8)
        out[k] = np.dstack([pal[g], np.full((n, n), 255, np.uint8)])
    return out


def cutout(img: np.ndarray, bottom: int) -> np.ndarray:
    """Remove the flat background behind a portrait (flood fill from the edges)."""
    h, w = img.shape[:2]
    lum = img[..., :3].astype(int).sum(2)
    wall = lum < 75
    bg = np.zeros((h, w), bool)
    q = deque()
    for y in range(bottom):
        for x in (0, w - 1):
            if not wall[y, x]:
                bg[y, x] = True; q.append((y, x))
    for x in range(w):
        if not wall[0, x]:
            bg[0, x] = True; q.append((0, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = y + dy, x + dx
            if 0 <= a < bottom and 0 <= b < w and not bg[a, b] and not wall[a, b]:
                bg[a, b] = True; q.append((a, b))
    out = img.copy()
    out[bg] = 0
    out[bottom:] = 0
    return out


def dissolve(img: np.ndarray, cx: float, cy: float, r0: float, r1: float) -> np.ndarray:
    """Pixel-art vignette: pixels vanish in an ordered-dither pattern past r0."""
    h, w = img.shape[:2]
    out = img.copy()
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot((xx - cx) / r1, (yy - cy) / r1) * r1
    t = np.clip((d - r0) / (r1 - r0), 0, 1)
    th = BAYER[yy % 4, xx % 4]
    out[t > th] = 0
    return out


def downsample(img: np.ndarray, k: int) -> np.ndarray:
    """Most common color in every k x k block, keeps edges crisp."""
    h, w = img.shape[0] // k, img.shape[1] // k
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            blk = img[y * k:(y + 1) * k, x * k:(x + 1) * k].reshape(-1, 4)
            vals, counts = np.unique(blk, axis=0, return_counts=True)
            out[y, x] = vals[counts.argmax()]
    return out


def paste(dst: np.ndarray, src: np.ndarray, x: int, y: int):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    for j in range(h):
        for i in range(w):
            if 0 <= y + j < H and 0 <= x + i < W and src[j, i, 3] > 0:
                dst[y + j, x + i] = src[j, i]


def outline(img: np.ndarray, color=(10, 8, 14, 255)) -> np.ndarray:
    a = img[..., 3] > 0
    edge = np.zeros_like(a)
    edge[1:] |= a[:-1]; edge[:-1] |= a[1:]; edge[:, 1:] |= a[:, :-1]; edge[:, :-1] |= a[:, 1:]
    out = img.copy()
    out[edge & ~a] = color
    return out


def canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(img).save(path)


def card_back(w=26, h=36, gold=True):
    c = canvas(w, h)
    rim = (226, 176, 64, 255) if gold else (90, 70, 130, 255)
    c[:, :] = (16, 10, 24, 255)
    c[1:-1, 1:-1] = rim
    c[2:-2, 2:-2] = (58, 26, 74, 255)
    for y in range(3, h - 3):
        for x in range(3, w - 3):
            if (x + y) % 4 == 0:
                c[y, x] = (76, 36, 96, 255)
    cy, cx = h // 2, w // 2
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(xx - cx + .5, yy - cy + .5)
    c[(r < 7.5) & (r >= 6.5)] = rim
    c[r < 6.5] = (160, 30, 46, 255)
    c[r < 4.5] = (220, 60, 66, 255)
    c[(r < 2.5)] = (255, 140, 120, 255)
    for (x, y) in ((4, 4), (w - 5, 4), (4, h - 5), (w - 5, h - 5)):
        c[y, x] = (230, 80, 80, 255)
    return c


def coin(r=5):
    s = r * 2 + 2
    c = canvas(s, s)
    yy, xx = np.mgrid[0:s, 0:s]
    d = np.hypot(xx - r - .5, yy - r - .5)
    c[d <= r + .5] = (10, 8, 14, 255)
    c[d <= r - .2] = (196, 132, 30, 255)
    c[d <= r - 1.2] = (247, 205, 90, 255)
    c[r - 1:r + 2, r] = (176, 112, 18, 255)
    c[2, 2] = (255, 246, 200, 255)
    return c


def build(out_dir):
    W = H = 125
    cr = crossroads()
    pf = portraits()

    # WORK: the three trading houses
    top = downsample(cr[0:176, 0:250], 2)          # 125 x 88
    work = canvas(W, H)
    paste(work, dissolve(top, 62, 40, 44, 64), 0, 16)
    save(work, f'{out_dir}/card-work.png')

    # FROGS: the frog in the trench coat walking up to the houses
    frog = cr[116:241, 76:182]                     # 106 x 125
    frog = dissolve(frog, 53, 66, 34, 56)
    frogs = canvas(W, H)
    paste(frogs, frog, 10, 0)
    save(frogs, f'{out_dir}/card-frogs.png')

    # SHOP: three card packs fanned out and coins
    shop = canvas(W, H)
    side = card_back(30, 42, gold=False)
    paste(shop, side, 20, 36); paste(shop, side, 75, 36)
    paste(shop, outline(card_back(38, 52)), 43, 24)
    for (x, y) in ((22, 86), (42, 92), (72, 92), (92, 86)):
        paste(shop, coin(), x, y)
    save(shop, f'{out_dir}/card-shop.png')

    # FUSION: four cards merge into one glowing card with a frog inside
    fusion = canvas(W, H)
    for i, x in enumerate((20, 41, 62, 83)):
        paste(fusion, outline(card_back(22, 30, gold=False)), x, 84)
    big = card_back(44, 58)
    big[3:-3, 3:-3] = (24, 60, 40, 255)
    big[4:-4, 4:-4] = (34, 92, 56, 255)
    face = downsample(cutout(pf['green'], 86)[6:86, 6:94], 2)   # 44 x 40
    paste(big, face, 0, 14)
    paste(fusion, outline(big), 40, 14)
    for (x, y) in ((26, 28), (100, 22), (98, 62), (24, 66)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
            fusion[y + dy, x + dx] = (255, 70, 180, 255) if abs(dx) + abs(dy) > 1 else (255, 200, 240, 255)
    save(fusion, f'{out_dir}/card-fusion.png')

    # MARKET: the mafia boss frog sitting on piles of coins
    market = canvas(W, H)
    boss = outline(cutout(pf['purple'], 86))
    paste(market, boss[8:86, :], 13, 18)
    for (x, y) in ((12, 100), (24, 104), (92, 102), (104, 98), (98, 106), (18, 108)):
        paste(market, coin(), x, y)
    save(market, f'{out_dir}/card-market.png')

    # bosses: the NFT frogs, cut out for the shop and boss pages
    for k, img in pf.items():
        save(img, f'{out_dir}/boss-{k}.png')
        save(outline(cutout(img, 86)), f'{out_dir}/boss-{k}-cut.png')



def tile(out_dir):
    """32x32 wall tile for page backgrounds: dark bricks with a rare ticker blip."""
    t = np.zeros((32, 32, 4), np.uint8)
    base, mortar, hi, lo = (24, 21, 33, 255), (14, 12, 20, 255), (32, 28, 44, 255), (19, 17, 27, 255)
    t[:, :] = mortar
    rows = [(0, 7, 0), (8, 15, 8), (16, 23, 0), (24, 31, 8)]
    for y0, y1, off in rows:
        for bx in range(-16, 32, 16):
            x0 = bx + off
            for y in range(y0 + 1, y1):
                for x in range(x0 + 1, x0 + 15):
                    if 0 <= x < 32:
                        t[y, x] = base
            for x in range(x0 + 1, x0 + 15):
                if 0 <= x < 32:
                    t[y0 + 1, x] = hi
                    t[y1 - 1, x] = lo
    # a tiny green and red candle carved into two bricks
    for (x, y, c) in ((5, 3, (40, 90, 60, 255)), (5, 4, (40, 90, 60, 255)), (5, 5, (40, 90, 60, 255)),
                      (22, 19, (100, 40, 50, 255)), (22, 20, (100, 40, 50, 255)), (22, 21, (100, 40, 50, 255))):
        t[y, x] = c
    save(t, f'{out_dir}/bg-tile.png')


if __name__ == '__main__':
    import sys
    build(sys.argv[1])
    tile(sys.argv[1])
