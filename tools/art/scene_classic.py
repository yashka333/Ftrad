"""Classic Trading office: an old-money Wall Street room in mahogany, brass and green.

Same layer contract and desk anchors as the Memecoin office (see scene_memecoin.py).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from font import BIG, SMALL, render
from px2 import INK, Canvas, dither, mix, sh
from scene_memecoin import DESK_TOP, DESK_W, FLOOR_Y, H, W, WALL_TOP, chair_base, sticky

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'client/src/assets/office/classic'
rng = np.random.default_rng(11)

MAHOG, MAHOG_HI, MAHOG_LO, MAHOG_DK = (104, 52, 34), (136, 74, 48), (78, 36, 24), (56, 24, 16)
BRASS, BRASS_HI, BRASS_LO = (196, 156, 72), (240, 206, 120), (140, 104, 40)
GREEN, GREEN_HI, GREEN_LO = (40, 84, 64), (58, 112, 86), (26, 58, 44)
LEATHER_G, LEATHER_G_HI, LEATHER_G_LO = (44, 96, 70), (70, 132, 98), (28, 64, 46)
OXBLOOD, OXBLOOD_HI, OXBLOOD_LO = (110, 34, 36), (146, 58, 56), (74, 20, 24)
TEAL, TEAL_CORE = (60, 210, 176), (210, 255, 244)
CHAIR_RAIL = 118


# ---------------------------------------------------------------- shell
def ceiling(c: Canvas):
    c.rect(0, 0, W - 1, WALL_TOP - 1, (58, 34, 24))
    # coffers
    for x0 in range(4, W, 64):
        c.box(x0, 1, x0 + 56, 12, (70, 42, 30), (88, 56, 40), (46, 26, 18))
        c.rect(x0 + 4, 4, x0 + 52, 9, (52, 30, 22))
    # crown molding with dentils
    c.rect(0, 14, W - 1, WALL_TOP - 1, MAHOG)
    c.hline(0, W - 1, 14, MAHOG_HI)
    c.hline(0, W - 1, 15, (150, 90, 60))
    for x in range(0, W, 4):
        c.rect(x, 17, x + 1, 19, MAHOG_LO)
        c.px(x, 17, MAHOG_HI)
    c.hline(0, W - 1, WALL_TOP - 2, MAHOG_DK)
    c.hline(0, W - 1, WALL_TOP - 1, INK)


DAMASK = [
    "....#....",
    "...###...",
    "..#.#.#..",
    ".#..#..#.",
    "#..###..#",
    ".#..#..#.",
    "..#.#.#..",
    "...###...",
    "....#....",
]


def wallpaper(c: Canvas):
    top, bot = WALL_TOP, CHAIR_RAIL - 1
    c.rect(0, top, W - 1, bot, GREEN)
    motif = np.array([[ch == '#' for ch in r] for r in DAMASK])
    for row, y in enumerate(range(top + 2, bot, 14)):
        off = 9 if row % 2 else 0
        for x in range(-off, W, 18):
            c.mask(motif, x, y, GREEN_HI)
            c.px(x + 4, y + 4, (150, 130, 70))  # gold fleck
    # faint vertical stripes
    for x in range(0, W, 18):
        for y in range(top, bot):
            if y % 2:
                c.px(x + 13, y, GREEN_LO)
    # age: darker at the top, sun-faded patches
    for y in range(top, top + 10):
        for x in range(W):
            if dither(x, y, .5 * (1 - (y - top) / 10)):
                c.px(x, y, (16, 30, 24), 120)


def wainscot(c: Canvas):
    # chair rail
    c.rect(0, CHAIR_RAIL, W - 1, CHAIR_RAIL + 4, MAHOG)
    c.hline(0, W - 1, CHAIR_RAIL, INK)
    c.hline(0, W - 1, CHAIR_RAIL + 1, MAHOG_HI)
    c.hline(0, W - 1, CHAIR_RAIL + 2, (150, 90, 60))
    c.hline(0, W - 1, CHAIR_RAIL + 4, MAHOG_DK)
    top, bot = CHAIR_RAIL + 5, FLOOR_Y - 7
    c.rect(0, top, W - 1, bot, MAHOG_LO)
    # raised panels
    for x0 in range(4, W - 30, 44):
        x1 = min(W - 2, x0 + 38)
        c.rect(x0, top + 5, x1, bot - 5, MAHOG_DK)
        c.rect(x0 + 1, top + 6, x1 - 1, bot - 6, MAHOG)
        c.hline(x0 + 1, x1 - 1, top + 6, MAHOG_HI)
        c.vline(x0 + 1, top + 6, bot - 6, MAHOG_HI)
        c.rect(x0 + 5, top + 10, x1 - 5, bot - 10, (96, 48, 32))
        c.hline(x0 + 5, x1 - 5, bot - 10, MAHOG_HI)
        c.vline(x1 - 5, top + 10, bot - 10, MAHOG_HI)
        for _ in range(6):  # grain
            gy = int(rng.integers(top + 11, bot - 10))
            gx = int(rng.integers(x0 + 6, x1 - 12))
            c.hline(gx, gx + int(rng.integers(3, 9)), gy, MAHOG_LO)
    c.rect(0, bot + 1, W - 1, FLOOR_Y - 1, MAHOG_DK)
    c.hline(0, W - 1, bot + 1, MAHOG)
    c.hline(0, W - 1, FLOOR_Y - 1, INK)


def parquet(c: Canvas):
    """Chevron parquet: slanted oak planks, rows alternate their lean."""
    oak = [(156, 106, 64), (146, 98, 58), (162, 112, 68), (140, 94, 56), (150, 102, 62)]
    seam = (108, 70, 42)
    y = FLOOR_Y
    row = 0
    while y < H:
        h = 4 + int(8 * ((y - FLOOR_Y) / (H - FLOOR_Y)) ** 1.1)
        y1 = min(H - 1, y + h - 1)
        pw = h * 3
        lean = 1 if row % 2 else -1
        seed = int(rng.integers(0, 1000))
        for yy in range(y, y1 + 1):
            for x in range(W):
                u = x - (yy - y) * lean + 4000
                idx = u // pw
                col = oak[(idx * 7 + seed) % len(oak)]
                if u % pw == 0:
                    col = seam
                elif yy == y:
                    col = sh(col, 1.08)
                c.px(x, yy, col)
        c.hline(0, W - 1, y1, seam)
        y = y1 + 1
        row += 1
    for _ in range(300):  # grain flecks
        c.px(rng.integers(0, W), rng.integers(FLOOR_Y, H), (128, 84, 50))
    for yy in range(FLOOR_Y, FLOOR_Y + 8):
        for x in range(W):
            if dither(x, yy, .7 * (1 - (yy - FLOOR_Y) / 8)):
                c.px(x, yy, (40, 22, 14), 150)


def persian_rug(c: Canvas, x0, y0, x1, y1, inset_top=10):
    pts = [(x0 + inset_top, y0), (x1 - inset_top, y0), (x1, y1), (x0, y1)]
    c.poly(pts, (110, 26, 30))
    inner = [(x0 + inset_top + 6, y0 + 3), (x1 - inset_top - 6, y0 + 3), (x1 - 6, y1 - 3), (x0 + 6, y1 - 3)]
    c.poly(inner, (30, 36, 80))
    core = [(x0 + inset_top + 12, y0 + 6), (x1 - inset_top - 12, y0 + 6), (x1 - 12, y1 - 6), (x0 + 12, y1 - 6)]
    c.poly(core, (140, 34, 36))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    c.ellipse(cx, cy, 22, 6, (200, 160, 80))
    c.ellipse(cx, cy, 16, 4, (30, 36, 80))
    c.ellipse(cx, cy, 8, 2, (200, 160, 80))
    for y in range(y0 + 7, y1 - 6, 3):
        for x in range(x0 + 14, x1 - 14, 7):
            if c.get(x, y) == (140, 34, 36) and (x // 7 + y // 3) % 2:
                c.px(x, y, (200, 160, 80))
    for x in range(x0, x1 + 1, 2):
        c.px(x, y1 + 1, (226, 210, 170))


# --------------------------------------------------------------- wall pieces
def blinds_window(c: Canvas, e: Canvas):
    x0, y0, x1, y1 = 34, 40, 146, 150
    sky0, sky1 = (16, 20, 44), (40, 40, 76)
    for y in range(y0 + 3, y1 - 2):
        t = (y - y0) / (y1 - y0)
        for x in range(x0 + 3, x1 - 2):
            e.px(x, y, mix(sky0, sky1, t))
    e.ellipse(x0 + 86, y0 + 16, 6, 6, (236, 230, 206))
    bx = x0 + 3
    while bx < x1 - 3:  # skyline with an old art-deco tower
        bw, bh = int(rng.integers(8, 16)), int(rng.integers(30, 64))
        top = y1 - 3 - bh
        e.rect(bx, top, min(x1 - 3, bx + bw - 1), y1 - 3, (34, 34, 58))
        for wy in range(top + 3, y1 - 5, 4):
            for wx in range(bx + 2, min(x1 - 4, bx + bw - 2), 3):
                if rng.random() < .35:
                    e.px(wx, wy, (250, 220, 150))
        bx += bw + int(rng.integers(0, 3))
    tx = x0 + 40
    e.poly([(tx, y0 + 24), (tx + 4, y0 + 10), (tx + 8, y0 + 24)], (60, 60, 86))
    e.rect(tx - 2, y0 + 24, tx + 10, y1 - 3, (44, 44, 70))
    e.vline(tx + 4, y0 + 4, y0 + 10, (90, 90, 120))
    e.px(tx + 4, y0 + 3, (255, 80, 80))
    for wy in range(y0 + 28, y1 - 6, 4):
        for wx in (tx, tx + 4, tx + 8):
            if rng.random() < .5:
                e.px(wx, wy, (255, 230, 160))
    # venetian blinds: slats over the view (lit layer), gaps stay open
    c.rect(x0, y0, x1, y1, INK)
    c.box(x0 + 1, y0 + 1, x1 - 1, y0 + 4, (210, 196, 160), (234, 222, 190), (170, 156, 120))
    for y in range(y0 + 5, y1 - 2):
        for x in range(x0 + 3, x1 - 2):
            if (y - y0) % 5 < 2:
                c.px(x, y, (206, 192, 156) if (y - y0) % 5 == 0 else (170, 156, 122))
            else:
                c.a[y, x, 3] = 0
    for cx in (x0 + 30, x1 - 30):  # ladder strings
        for y in range(y0 + 5, y1 - 2):
            c.px(cx, y, (230, 220, 190))
    c.rect(x0, y1 - 2, x1, y1, (150, 140, 112))
    # heavy curtains with a gold tieback
    for (cx0, cx1, side) in ((x0 - 12, x0 + 6, -1), (x1 - 6, x1 + 12, 1)):
        for y in range(y0 - 8, y1 + 14):
            pinch = 0
            if y1 - 30 < y < y1 - 10:
                pinch = 3
            for x in range(cx0 + (pinch if side < 0 else 0), cx1 - (pinch if side > 0 else 0) + 1):
                fold = (x - cx0) % 5
                c.px(x, y, OXBLOOD_HI if fold == 1 else OXBLOOD_LO if fold == 4 else OXBLOOD)
            c.px(cx0 + (pinch if side < 0 else 0), y, INK)
            c.px(cx1 - (pinch if side > 0 else 0), y, INK)
        c.rect(cx0 + 2, y1 - 22, cx1 - 2, y1 - 19, BRASS)
        c.hline(cx0 + 2, cx1 - 2, y1 - 22, BRASS_HI)
    c.rect(x0 - 16, y0 - 10, x1 + 16, y0 - 8, BRASS_LO)
    c.hline(x0 - 16, x1 + 16, y0 - 10, BRASS_HI)
    for ex in (x0 - 18, x1 + 17):
        c.ellipse(ex, y0 - 9, 2, 2, BRASS)
    return dict(rect=[x0 + 3, y0 + 3, x1 - 3, y1 - 3], light=[(x0 + x1) // 2, (y0 + y1) // 2])


def neon_sign(c: Canvas, n: Canvas):
    m = render('CLASSIC TRADING', BIG)
    m = np.kron(m, np.ones((2, 2), bool))
    h, w = m.shape
    x0, y0 = W // 2 - w // 2, 27
    # walnut board with a brass frame
    c.rect(x0 - 9, y0 - 5, x0 + w + 8, y0 + h + 4, INK)
    c.rect(x0 - 8, y0 - 4, x0 + w + 7, y0 + h + 3, BRASS)
    c.hline(x0 - 8, x0 + w + 7, y0 - 4, BRASS_HI)
    c.rect(x0 - 6, y0 - 2, x0 + w + 5, y0 + h + 1, (60, 32, 22))
    for _ in range(40):
        gx, gy = int(rng.integers(x0 - 5, x0 + w)), int(rng.integers(y0 - 1, y0 + h))
        c.hline(gx, gx + 6, gy, (72, 40, 28))
    pad = np.pad(m, 1)
    edge = m & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    core = m & ~edge
    c.mask(m, x0, y0, (36, 70, 62))
    c.mask(core, x0, y0, (50, 96, 84))
    n.mask(edge, x0, y0, TEAL)
    n.mask(core, x0, y0, TEAL_CORE)
    return dict(rect=[x0, y0, x0 + w - 1, y0 + h - 1], light=[W // 2, y0 + h // 2])


def flap_board(c: Canvas):
    x0, y0, x1, y1 = 262, 50, 378, 118
    c.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, INK)
    c.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, BRASS)
    c.hline(x0 - 1, x1 + 1, y0 - 1, BRASS_HI)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, (20, 18, 16))
    for (bx, by) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        c.px(bx, by, BRASS_HI)
    return dict(screen=[x0 + 3, y0 + 3, x1 - 3, y1 - 3], rows=5, light=[(x0 + x1) // 2, (y0 + y1) // 2])


def ticker_board(c: Canvas):
    x0, y0, x1, y1 = 430, 50, 614, 72
    for bx in (x0 + 20, x1 - 20):
        c.vline(bx, WALL_TOP, y0, BRASS_LO)
    c.box(x0, y0, x1, y1, (40, 30, 24), (64, 48, 36), (26, 18, 14))
    c.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 1, BRASS)
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, (6, 12, 8))
    for x in range(x0 + 4, x1 - 3, 2):
        for y in range(y0 + 4, y1 - 3, 2):
            c.px(x, y, (16, 34, 20))
    return dict(rect=[x0 + 4, y0 + 4, x1 - 4, y1 - 4], light=[(x0 + x1) // 2, (y0 + y1) // 2])


def world_clocks(c: Canvas):
    clocks = []
    labels = [('NY', -4), ('LDN', 0), ('TKY', 9)]
    for i, (name, tz) in enumerate(labels):
        cx, cy = 178 + i * 24, 64
        c.ellipse(cx, cy, 9, 9, INK)
        c.ellipse(cx, cy, 8, 8, BRASS)
        c.ellipse(cx, cy, 6, 6, (240, 232, 210))
        c.px(cx - 6, cy - 3, BRASS_HI)
        for k in range(12):
            a = 2 * math.pi * k / 12
            c.px(cx + round(math.sin(a) * 5), cy - round(math.cos(a) * 5), (120, 110, 96))
        m = render(name, SMALL)
        c.rect(cx - m.shape[1] // 2 - 2, cy + 11, cx + m.shape[1] // 2 + 2, cy + 17, BRASS_LO)
        c.mask(m, cx - m.shape[1] // 2, cy + 12, (250, 230, 180))
        clocks.append(dict(c=[cx, cy], tz=tz, hands=[3, 5, 0]))
    return clocks


def bull_painting(c: Canvas):
    x0, y0, x1, y1 = 162, 88, 242, 132
    c.rect(x0 - 3, y0 - 3, x1 + 3, y1 + 3, INK)
    c.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, BRASS)
    c.rect(x0 - 2, y0 - 2, x1 + 2, y0 - 2, BRASS_HI)
    c.vline(x0 - 2, y0 - 2, y1 + 2, BRASS_HI)
    c.rect(x0, y0, x1, y1, INK)
    for y in range(y0 + 1, y1):
        t = (y - y0) / (y1 - y0)
        for x in range(x0 + 1, x1):
            c.px(x, y, mix((60, 70, 60), (120, 96, 60), t) if not dither(x, y, .2) else mix((70, 80, 66), (130, 104, 66), t))
    # ground
    c.rect(x0 + 1, y1 - 9, x1 - 1, y1 - 1, (70, 56, 34))
    # charging bull silhouette
    bx, by = x0 + 22, y1 - 10
    c.ellipse(bx + 18, by - 9, 16, 7, (40, 26, 20))
    c.ellipse(bx + 6, by - 12, 9, 6, (46, 30, 22))
    c.ellipse(bx - 4, by - 9, 6, 4, (40, 26, 20))
    c.line(bx - 8, by - 13, bx - 13, by - 19, (226, 210, 170))
    c.line(bx - 1, by - 14, bx + 2, by - 21, (226, 210, 170))
    for lx in (bx + 4, bx + 10, bx + 24, bx + 30):
        c.rect(lx, by - 4, lx + 2, by + 3, (36, 22, 16))
    c.line(bx + 34, by - 12, bx + 40, by - 18, (40, 26, 20))
    c.px(bx - 6, by - 10, (220, 60, 40))
    # dust clouds
    for k in range(6):
        c.ellipse(bx + 38 + k * 4, by + 1 - k % 2, 3, 2, (150, 130, 96))
    # brass picture light above
    c.rect(x0 + 24, y0 - 9, x1 - 24, y0 - 6, BRASS)
    c.hline(x0 + 24, x1 - 24, y0 - 9, BRASS_HI)
    c.vline((x0 + x1) // 2, y0 - 6, y0 - 3, BRASS_LO)
    m = render('1929', SMALL)
    c.rect((x0 + x1) // 2 - 9, y1 + 4, (x0 + x1) // 2 + 9, y1 + 10, BRASS_LO)
    c.mask(m, (x0 + x1) // 2 - m.shape[1] // 2, y1 + 5, (250, 230, 180))
    return dict(light=[(x0 + x1) // 2, y0 - 6])


def bookcase(c: Canvas):
    x0, y0, x1, y1 = 430, 82, 586, FLOOR_Y + 6
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1, MAHOG)
    c.rect(x0 - 2, y0 - 4, x1 + 2, y0, MAHOG_HI)
    c.hline(x0 - 2, x1 + 2, y0 - 4, (160, 100, 66))
    c.hline(x0 - 2, x1 + 2, y0, INK)
    shelves = [y0 + 32, y0 + 64, y0 + 96]
    inner_top = y0 + 4
    spines = [(120, 30, 30), (30, 60, 110), (40, 90, 60), (140, 110, 50), (90, 40, 90), (160, 140, 110), (60, 40, 30), (30, 30, 34)]
    for si, sy in enumerate(shelves + [y1 - 2]):
        top = inner_top if si == 0 else shelves[si - 1] + 4
        c.rect(x0 + 4, top, x1 - 4, sy - 1, MAHOG_DK)
        x = x0 + 5
        while x < x1 - 8:
            if rng.random() < .1 and si != 1:
                x += int(rng.integers(4, 10))
                continue
            bw = int(rng.integers(3, 7))
            bh = int(rng.integers(sy - top - 10, sy - top - 2))
            col = spines[int(rng.integers(0, len(spines)))]
            c.rect(x, sy - bh, x + bw - 1, sy - 1, col)
            c.vline(x, sy - bh, sy - 1, sh(col, 1.25))
            c.vline(x + bw - 1, sy - bh, sy - 1, sh(col, .7))
            c.hline(x, sy - bh + 3, x + bw - 1, BRASS_HI if rng.random() < .6 else sh(col, 1.4))
            c.hline(x, sy - 4, x + bw - 1, BRASS)
            x += bw
        c.rect(x0 + 1, sy, x1 - 1, sy + 3, MAHOG)
        c.hline(x0 + 1, x1 - 1, sy, MAHOG_HI)
        c.hline(x0 + 1, x1 - 1, sy + 3, MAHOG_DK)
    # ledgers with crash years on the middle shelf
    lx = x0 + 74
    for k, year in enumerate(['1929', '1987', '2008']):
        bx = lx + k * 18
        c.box(bx, shelves[1] - 26, bx + 15, shelves[1] - 1, (50, 36, 26), (80, 60, 40), (34, 24, 18))
        m = render(year, SMALL)
        c.mask(m, bx + 2, shelves[1] - 16, BRASS_HI)
    # golden bull bookend
    gx, gy = x0 + 132, shelves[0] - 1
    c.ellipse(gx + 6, gy - 5, 7, 4, BRASS)
    c.ellipse(gx, gy - 7, 3, 3, BRASS)
    c.px(gx - 3, gy - 11, BRASS_HI); c.px(gx + 1, gy - 11, BRASS_HI)
    c.px(gx + 4, gy - 7, BRASS_HI); c.px(gx + 5, gy - 8, BRASS_HI)
    for lx_ in (gx + 2, gx + 9):
        c.rect(lx_, gy - 2, lx_ + 1, gy, BRASS_LO)
    # brass bell on the top shelf
    bx, by = x0 + 20, shelves[0] - 1
    c.rect(bx - 6, by - 1, bx + 6, by, MAHOG_DK)
    c.poly([(bx - 5, by - 1), (bx - 3, by - 9), (bx + 3, by - 9), (bx + 5, by - 1)], BRASS)
    c.px(bx - 2, by - 7, BRASS_HI); c.px(bx - 3, by - 4, BRASS_HI)
    c.rect(bx - 1, by - 11, bx + 1, by - 10, BRASS_LO)


def tape_machine(c: Canvas):
    """Stock ticker machine under a glass dome; the paper tape spills to the floor."""
    x0 = 4
    # pedestal
    c.box(x0 + 4, 150, x0 + 20, FLOOR_Y + 8, MAHOG, MAHOG_HI, MAHOG_LO)
    c.box(x0 + 1, 146, x0 + 23, 151, MAHOG_HI, (160, 100, 66), MAHOG_LO)
    c.box(x0 + 1, FLOOR_Y + 6, x0 + 23, FLOOR_Y + 10, MAHOG, MAHOG_HI, MAHOG_LO)
    # machine
    c.box(x0 + 6, 134, x0 + 18, 145, BRASS, BRASS_HI, BRASS_LO)
    c.ellipse(x0 + 12, 132, 4, 3, BRASS_LO)
    c.ellipse(x0 + 12, 131, 2, 1, BRASS_HI)
    c.rect(x0 + 8, 138, x0 + 16, 140, (30, 30, 34))
    # glass dome (outline only, faint)
    for y in range(116, 146):
        t = (y - 116) / 30
        half = int(10 * math.sqrt(max(0, 1 - (1 - t) ** 2))) + 1
        c.px(x0 + 12 - half, y, (200, 220, 230), 150)
        c.px(x0 + 12 + half, y, (200, 220, 230), 150)
    c.hline(x0 + 9, x0 + 15, 116, (200, 220, 230), 150)
    c.line(x0 + 6, 124, x0 + 8, 120, (240, 250, 255), 180)
    # paper tape: out of the dome, over the pedestal edge and coiling on the floor
    path = []
    pts = [(x0 + 18, 141), (x0 + 24, 143), (x0 + 27, 150), (x0 + 28, 168), (x0 + 30, 186),
           (x0 + 34, FLOOR_Y + 8), (x0 + 44, FLOOR_Y + 12), (x0 + 56, FLOOR_Y + 10), (x0 + 60, FLOOR_Y + 15),
           (x0 + 50, FLOOR_Y + 18), (x0 + 40, FLOOR_Y + 16), (x0 + 46, FLOOR_Y + 21), (x0 + 64, FLOOR_Y + 22)]
    for (a, b), (p, q) in zip(pts, pts[1:]):
        n = max(abs(p - a), abs(q - b), 1)
        for k in range(n):
            x, y = round(a + (p - a) * k / n), round(b + (q - b) * k / n)
            if not path or path[-1] != [x, y]:
                path.append([x, y])
    for x, y in path:
        c.px(x, y, (236, 230, 210))
        c.px(x, y + 1, (190, 182, 160))
    return dict(path=path)


def double_door(c: Canvas, e: Canvas):
    x0, y0, x1, y1 = 594, 100, 636, FLOOR_Y + 2
    c.rect(x0 - 4, y0 - 4, x1 + 2, y1, INK)
    c.rect(x0 - 3, y0 - 3, x1 + 1, y1, MAHOG_HI)
    c.hline(x0 - 3, x1 + 1, y0 - 3, (160, 100, 66))
    mid = (x0 + x1) // 2
    for (a, b) in ((x0, mid), (mid + 1, x1)):
        c.box(a, y0, b, y1, MAHOG, MAHOG_HI, MAHOG_LO)
        # frosted glass upper pane (warm hallway light)
        gx0, gy0, gx1, gy1 = a + 4, y0 + 6, b - 4, y0 + 44
        c.rect(gx0 - 1, gy0 - 1, gx1 + 1, gy1 + 1, INK)
        for y in range(gy0, gy1 + 1):
            for x in range(gx0, gx1 + 1):
                e.px(x, y, mix((246, 226, 180), (210, 180, 130), (y - gy0) / (gy1 - gy0)), 235)
                c.a[y, x, 3] = 0
        c.box(a + 4, y0 + 52, b - 4, y1 - 8, MAHOG, MAHOG_HI, MAHOG_LO)
    m = render('PRIVATE', SMALL)
    e.mask(m, (x0 + x1) // 2 - m.shape[1] // 2, y0 + 22, (80, 60, 40))
    for hx in (mid - 4, mid + 3):
        c.box(hx, y0 + 50, hx + 2, y0 + 58, BRASS, BRASS_HI, BRASS_LO)
    ex0, ey0 = x0 + 5, y0 - 16
    c.box(ex0, ey0, ex0 + 32, ey0 + 9, (40, 46, 44), None, None)
    e.rect(ex0 + 2, ey0 + 2, ex0 + 30, ey0 + 7, (30, 120, 70))
    e.mask(render('EXIT', SMALL), ex0 + 9, ey0 + 2, (200, 255, 210))
    return dict(rect=[x0, y0, x1, y1], light_exit=[ex0 + 16, ey0 + 5], light_door=[(x0 + x1) // 2, y0 + 24])


def pendant(c: Canvas, e: Canvas, lx):
    c.vline(lx, WALL_TOP - 8, 27, BRASS_LO)
    c.box(lx - 2, 25, lx + 2, 28, BRASS, BRASS_HI, BRASS_LO)
    # brass dome shade
    for y in range(28, 38):
        half = 3 + int((y - 28) * 1.1)
        c.hline(lx - half, lx + half, y, BRASS)
        c.px(lx - half, y, INK); c.px(lx + half, y, INK)
        c.px(lx - half + 2, y, BRASS_HI)
    c.hline(lx - 13, lx + 13, 38, INK)
    e.ellipse(lx, 39, 4, 1, (255, 236, 190))
    return [lx, 40]


def banker_lamp(c: Canvas, e: Canvas, x, y):
    """Brass base, emerald glass shade. Returns the light anchor."""
    c.box(x, y - 2, x + 10, y, BRASS, BRASS_HI, BRASS_LO)
    c.vline(x + 5, y - 12, y - 2, BRASS_LO)
    c.vline(x + 6, y - 12, y - 2, BRASS_HI)
    c.poly([(x - 3, y - 12), (x + 13, y - 12), (x + 11, y - 18), (x - 1, y - 18)], (20, 110, 70))
    c.line(x - 1, y - 18, x + 11, y - 18, (110, 200, 150))
    c.line(x - 3, y - 12, x + 13, y - 12, INK)
    c.line(x - 1, y - 18, x - 3, y - 12, INK); c.line(x + 11, y - 18, x + 13, y - 12, INK)
    e.hline(x, x + 10, y - 11, (255, 236, 180))
    c.vline(x + 9, y - 11, y - 6, BRASS_HI)  # pull chain
    return [x + 5, y - 10]


# ------------------------------------------------------------------ the boss
def boss_area(bg: Canvas, bd: Canvas, e: Canvas):
    cx = W // 2
    persian_rug(bg, cx - 106, FLOOR_Y + 4, cx + 106, FLOOR_Y + 34)
    # green chesterfield wingback with brass nailheads
    TOP, BOT = 106, 184
    X0, X1 = cx - 28, cx + 28
    for y in range(TOP, BOT + 1):
        r = y - TOP
        hw = 20 + min(8, r) if r < 40 else 28 - min(6, (r - 40) // 2)
        if r < 3:
            hw = 18 + r * 2
        bg.hline(cx - hw, cx + hw, y, INK)
        bg.hline(cx - hw + 1, cx + hw - 1, y, LEATHER_G)
        bg.px(cx - hw + 1, y, LEATHER_G_HI); bg.px(cx - hw + 2, y, LEATHER_G_HI)
        bg.px(cx + hw - 1, y, LEATHER_G_LO); bg.px(cx + hw - 2, y, LEATHER_G_LO)
    for y in range(TOP + 6, BOT - 4, 7):  # deep button tufting
        off = 4 if ((y - TOP) // 7) % 2 else 0
        for x in range(cx - 20 + off, cx + 21, 8):
            bg.px(x, y, (16, 40, 28))
            for k in (1, 2):
                bg.px(x - k, y - k, LEATHER_G_LO); bg.px(x + k, y - k, LEATHER_G_LO)
                bg.px(x - k, y + k, LEATHER_G_LO); bg.px(x + k, y + k, LEATHER_G_LO)
            bg.px(x - 1, y - 1, LEATHER_G_HI)
    for y in range(TOP + 3, BOT, 3):  # nailheads along the wings
        r = y - TOP
        hw = 20 + min(8, r) if r < 40 else 28 - min(6, (r - 40) // 2)
        bg.px(cx - hw + 3, y, BRASS_HI); bg.px(cx + hw - 3, y, BRASS_HI)
    for x in range(cx - 16, cx + 17, 3):
        bg.px(x, TOP + 2, BRASS_HI)
    # rolled arms
    for ax0 in (X0 - 12, X1 + 1):
        ax1 = ax0 + 11
        bg.rect(ax0, 156, ax1, BOT, INK)
        bg.rect(ax0 + 1, 157, ax1 - 1, BOT, LEATHER_G)
        bg.ellipse((ax0 + ax1) / 2, 160, 5, 4, LEATHER_G_HI)
        bg.ellipse((ax0 + ax1) / 2, 160, 2, 2, LEATHER_G_LO)
        for y in range(166, BOT, 3):
            bg.px(ax0 + 2, y, BRASS_HI)
    # partners desk: mahogany with a green leather top
    x0, x1, top = cx - 74, cx + 73, 180
    D = 8
    bd.rect(x0, top, x1, top + D + 3, INK)
    bd.rect(x0 + 1, top + 1, x1 - 1, top + D, MAHOG)
    bd.rect(x0 + 6, top + 2, x1 - 6, top + D - 2, LEATHER_G)
    bd.hline(x0 + 6, x1 - 6, top + 2, LEATHER_G_LO)
    for x in range(x0 + 8, x1 - 7, 2):  # gold tooling border
        bd.px(x, top + 3, BRASS)
    bd.hline(x0 + 1, x1 - 1, top + D, MAHOG_HI)
    bd.rect(x0 + 1, top + D + 1, x1 - 1, top + D + 2, MAHOG_LO)
    fy = FLOOR_Y + 22
    bd.rect(x0 + 2, top + D + 3, x1 - 2, fy, INK)
    bd.rect(x0 + 3, top + D + 3, x1 - 3, fy - 1, MAHOG)
    for (p0, p1) in ((x0 + 5, x0 + 42), (x0 + 46, x1 - 46), (x1 - 42, x1 - 5)):
        bd.box(p0, top + D + 5, p1, fy - 3, MAHOG, MAHOG_HI, MAHOG_LO)
        bd.box(p0 + 4, top + D + 9, p1 - 4, fy - 7, MAHOG, MAHOG_LO, MAHOG_HI)
    m = render('BOSS', BIG)
    pw = m.shape[1] + 8
    bd.box(cx - pw // 2, top + D + 9, cx + pw // 2, top + D + 19, BRASS, BRASS_HI, BRASS_LO)
    bd.mask(m, cx - m.shape[1] // 2 + 1, top + D + 11, (70, 44, 20))
    lamp = banker_lamp(bd, e, x0 + 12, top + 2)
    # papers, fountain pen, cigar box, bell
    bd.box(cx - 30, top - 2, cx - 14, top + 2, (236, 230, 214), None, (200, 192, 176))
    bd.box(cx - 28, top - 4, cx - 12, top, (230, 224, 206), None, (196, 188, 170))
    bd.line(cx - 26, top - 1, cx - 16, top - 3, (30, 30, 40))
    bd.box(x1 - 36, top - 5, x1 - 20, top + 1, (120, 70, 40), (150, 96, 60), (80, 44, 24))
    bd.rect(x1 - 34, top - 4, x1 - 22, top - 4, (200, 60, 40))
    bx = x1 - 12
    bd.poly([(bx - 4, top + 1), (bx - 2, top - 6), (bx + 2, top - 6), (bx + 4, top + 1)], BRASS)
    bd.px(bx - 1, top - 5, BRASS_HI)
    return dict(boss_anchor=[cx, top + 4], plus=[cx, 146], desk_top=top,
                chair=[X0 - 13, TOP - 4, X1 + 13, top + 34]), lamp


# --------------------------------------------------------------- worker desks
def leather_chair(c: Canvas, cx, top, bottom):
    for y in range(top, bottom + 1):
        r = y - top
        hw = 13 + min(3, r) if r > 0 else 12
        c.hline(cx - hw, cx + hw, y, INK)
        c.hline(cx - hw + 1, cx + hw - 1, y, OXBLOOD)
        c.px(cx - hw + 1, y, OXBLOOD_HI); c.px(cx + hw - 1, y, OXBLOOD_LO)
    for y in range(top + 5, bottom - 2, 6):
        off = 3 if ((y - top) // 6) % 2 else 0
        for x in range(cx - 10 + off, cx + 11, 6):
            c.px(x, y, (50, 10, 14))
            c.px(x - 1, y - 1, OXBLOOD_LO); c.px(x + 1, y - 1, OXBLOOD_LO)
    for x in range(cx - 12, cx + 13, 3):
        c.px(x, top + 1, BRASS_HI)
    for ax in (cx - 20, cx + 17):
        c.box(ax, bottom - 8, ax + 3, bottom + 2, OXBLOOD, OXBLOOD_HI, OXBLOOD_LO)


def mahogany_desk(c: Canvas, x, y, variant):
    W_ = DESK_W
    D = 9
    c.rect(x, y, x + W_ - 1, y + D + 3, INK)
    c.rect(x + 1, y + 1, x + W_ - 2, y + D, MAHOG)
    c.rect(x + 5, y + 2, x + W_ - 6, y + D - 2, LEATHER_G)
    c.hline(x + 5, x + W_ - 6, y + 2, LEATHER_G_LO)
    for gx in range(x + 7, x + W_ - 6, 2):
        c.px(gx, y + 3, BRASS_LO)
    c.hline(x + 1, x + W_ - 2, y + D, MAHOG_HI)
    c.rect(x + 1, y + D + 1, x + W_ - 2, y + D + 2, MAHOG_LO)
    top_end = y + D + 3
    floor = top_end + 29
    # back of the desk: two raised panels
    c.rect(x + 2, top_end, x + W_ - 3, floor, INK)
    c.rect(x + 3, top_end, x + W_ - 4, floor - 1, MAHOG)
    for (p0, p1) in ((x + 6, x + W_ // 2 - 2), (x + W_ // 2 + 2, x + W_ - 7)):
        c.box(p0, top_end + 3, p1, floor - 5, MAHOG, MAHOG_HI, MAHOG_LO)
        c.box(p0 + 3, top_end + 6, p1 - 3, floor - 8, MAHOG, MAHOG_LO, MAHOG_HI)
    c.rect(x + 3, floor - 3, x + W_ - 4, floor - 1, MAHOG_DK)
    for lx in (x, x + W_ - 6):  # turned legs
        c.box(lx, top_end - 1, lx + 5, floor, MAHOG_LO, MAHOG, MAHOG_DK)
        c.hline(lx + 1, lx + 4, top_end + 4, MAHOG_HI)
        c.hline(lx + 1, lx + 4, floor - 4, MAHOG_HI)
        c.hline(lx - 1, lx + 6, floor, INK)
    # brass number plate
    num = render(str(variant + 1), SMALL)
    c.box(x + W_ // 2 - 5, top_end + 1, x + W_ // 2 + 4, top_end + 8, BRASS, BRASS_HI, BRASS_LO)
    c.mask(num, x + W_ // 2 - 1, top_end + 2, (70, 44, 20))
    for sx_ in range(x - 2, x + W_ + 2):
        c.px(sx_, floor + 1, (0, 0, 0), 110)
        if x + 4 <= sx_ <= x + W_ - 4:
            c.px(sx_, floor + 2, (0, 0, 0), 70)
    return top_end, floor


def crt(c: Canvas, mx, base_y):
    w, h = 34, 28
    x0, y0 = mx - w // 2, base_y - h
    beige, beige_hi, beige_lo = (204, 192, 162), (226, 216, 190), (160, 148, 120)
    # boxy back casing visible above
    c.box(x0 + 4, y0 - 4, x0 + w - 5, y0 + 2, beige_lo, beige, (130, 120, 96))
    c.box(x0, y0, x0 + w - 1, y0 + h - 1, beige, beige_hi, beige_lo)
    sx0, sy0, sx1, sy1 = x0 + 4, y0 + 3, x0 + w - 5, y0 + h - 7
    c.rect(sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1, INK)
    c.rect(sx0, sy0, sx1, sy1, (6, 20, 10))
    c.hline(x0 + 3, x0 + w - 4, y0 + h - 4, beige_lo)
    c.rect(x0 + w - 8, y0 + h - 5, x0 + w - 6, y0 + h - 4, (90, 200, 120))
    for vx in range(x0 + 4, x0 + 14, 2):
        c.px(vx, y0 + h - 4, (120, 110, 90))
    return [sx0, sy0, sx1, sy1]


def desk_props(c: Canvas, e: Canvas, x, y, fx, variant, mon):
    key, key_lo = (210, 200, 172), (166, 156, 128)
    c.box(fx - 13, y + 3, fx + 12, y + 7, key, None, key_lo)
    for kx in range(fx - 11, fx + 11, 2):
        c.px(kx, y + 4, key_lo); c.px(kx + 1, y + 5, key_lo)
    steam, lamps = [], []
    if variant in (0, 3):
        lamps.append(banker_lamp(c, e, x + 4, y + 6))
    if variant == 1:  # rotary phone
        px_, py_ = x + 6, y + 6
        c.box(px_, py_ - 5, px_ + 14, py_, (30, 30, 34), (60, 60, 68), None)
        c.ellipse(px_ + 7, py_ - 3, 3, 2, (230, 224, 206))
        c.px(px_ + 7, py_ - 3, (30, 30, 34))
        c.box(px_ - 1, py_ - 9, px_ + 15, py_ - 6, (30, 30, 34), (60, 60, 68), None)
    if variant == 2:  # newspaper
        nx, ny = x + 4, y + 6
        c.box(nx, ny - 6, nx + 22, ny, (232, 226, 210), None, (196, 188, 170))
        m = render('DAILY', SMALL)
        c.mask(m, nx + 2, ny - 5, (40, 40, 44))
        for k in range(3):
            c.hline(nx + 2, nx + 20, ny - 1 - k, (150, 146, 136)) if k == 0 else None
    if variant in (2, 4):  # coffee cup on a saucer
        cx_, cy_ = x + 28 if variant == 2 else x + 8, y + 6
        c.ellipse(cx_ + 3, cy_, 6, 1, (236, 232, 222))
        c.box(cx_, cy_ - 6, cx_ + 6, cy_ - 1, (240, 236, 226), None, (200, 194, 180))
        c.hline(cx_ + 1, cx_ + 5, cy_ - 5, (80, 50, 30))
        c.px(cx_ + 7, cy_ - 4, (240, 236, 226)); c.px(cx_ + 7, cy_ - 3, (240, 236, 226))
        steam.append([cx_ + 3, cy_ - 7])
    if variant == 4:  # adding machine
        ax = x + 18
        c.box(ax, y - 4, ax + 10, y + 6, (70, 70, 76), (100, 100, 108), (50, 50, 56))
        for k in range(3):
            c.hline(ax + 2, ax + 8, y - 1 + k * 2, (200, 196, 180))
        c.rect(ax + 3, y - 8, ax + 7, y - 4, (236, 230, 210))
    if variant == 3:  # cigar in an ashtray
        c.ellipse(fx + 25, y + 4, 4, 1, (90, 90, 96))
        c.hline(fx + 22, fx + 29, y + 3, (120, 70, 40))
    return steam, lamps


# ----------------------------------------------------------------------- main
def build():
    OUT.mkdir(parents=True, exist_ok=True)
    bg, e, neon = Canvas(W, H), Canvas(W, H), Canvas(W, H)
    bossdesk, chairs, desks = Canvas(W, H), Canvas(W, H), Canvas(W, H)
    layout: dict = {'size': [W, H]}

    ceiling(bg)
    wallpaper(bg)
    wainscot(bg)
    parquet(bg)
    layout['window'] = blinds_window(bg, e)
    layout['neon'] = neon_sign(bg, neon)
    layout['tv'] = flap_board(bg)
    layout['ticker'] = ticker_board(bg)
    layout['clocks'] = world_clocks(bg)
    painting = bull_painting(bg)
    bookcase(bg)
    layout['tape'] = tape_machine(bg)
    layout['door'] = double_door(bg, e)
    lamps = [pendant(bg, e, lx) for lx in (104, 536)]
    boss, boss_lamp = boss_area(bg, bossdesk, e)
    layout['boss'] = boss

    desks_l = []
    gap = (W - 5 * DESK_W) // 6
    for i in range(5):
        x = gap + i * (DESK_W + gap)
        fx = x + 36
        floor_y = DESK_TOP + 12 + 29
        chair_base(chairs, fx, floor_y - 2)
        leather_chair(chairs, fx, DESK_TOP - 30, DESK_TOP + 6)
        mahogany_desk(desks, x, DESK_TOP, i)
        mx = x + DESK_W - 22
        screen = crt(desks, mx, DESK_TOP + 6)
        steam, dl = desk_props(desks, e, x, DESK_TOP, fx, i, screen)
        desks_l.append(dict(x=x, frog=[fx, DESK_TOP], screen=screen, screen2=None,
                            steam=steam, lamps=dl, clip=DESK_TOP + 2))
    layout['desks'] = desks_l
    # rug runner in front of the desks
    persian_rug(desks, 40, 336, 600, 356, 4)

    L_ = layout
    wl = L_['window']['light']
    layout['lights'] = (
        [dict(x=x, y=y, r=180, col=[1.0, 0.8, 0.55], i=1.0, cone=True, kind='lamp') for x, y in lamps] + [
        dict(id='neon', x=L_['neon']['light'][0], y=L_['neon']['light'][1] + 6, r=150, col=[0.3, 1.0, 0.85], i=0.62),
        dict(id='tv', x=L_['tv']['light'][0], y=L_['tv']['light'][1], r=110, col=[1.0, 0.85, 0.6], i=0.42),
        dict(id='window', x=wl[0] + 20, y=wl[1] + 20, r=170, col=[0.45, 0.55, 1.0], i=0.55, stripes=[5, 3, 40]),
        dict(x=boss_lamp[0], y=boss_lamp[1] + 6, r=70, col=[0.95, 1.0, 0.65], i=0.85, cone=True),
        dict(x=painting['light'][0], y=painting['light'][1], r=46, col=[1.0, 0.85, 0.6], i=0.6, cone=True),
        dict(x=L_['door']['light_exit'][0], y=L_['door']['light_exit'][1], r=40, col=[0.3, 1.0, 0.5], i=0.45),
        dict(x=L_['door']['light_door'][0], y=L_['door']['light_door'][1], r=60, col=[1.0, 0.85, 0.6], i=0.4),
        dict(id='plus', x=L_['boss']['plus'][0], y=L_['boss']['plus'][1], r=44, col=[1.0, 0.8, 0.35], i=0.55),
        dict(id='ticker', x=L_['ticker']['light'][0], y=L_['ticker']['light'][1], r=72, col=[0.4, 1.0, 0.5], i=0.35)])
    layout['theme'] = dict(
        ambient=[0.30, 0.27, 0.26], screen='crt', screenLight=[0.4, 1.0, 0.5], tv='flap', rain=False,
        cones=[255, 214, 160], coneAlpha=0.07, deskLamp=[0.95, 1.0, 0.65], tickerStyle='stocks',
        coins=['SPX', 'NDX', 'DOW', 'GOLD', 'OIL'], tickerSym=[150, 255, 170], neonHalo=[80, 230, 196],
        stocks=[['SPX', 5812.40], ['NDX', 2039.12], ['DOW', 4286.39], ['GOLD', 2654.30], ['OIL', 71.42],
                ['BOND', 104.18], ['EUR', 1.0842], ['YEN', 149.62]])

    for name, cv in [('bg', bg), ('emissive', e), ('neon', neon), ('bossdesk', bossdesk),
                     ('chairs', chairs), ('desks', desks)]:
        cv.save(OUT / f'{name}.png')
    (OUT / 'layout.json').write_text(json.dumps(layout))
    return layout


if __name__ == '__main__':
    build()
    print('ok')
