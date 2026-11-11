"""Pump.fun Rugs office: an underground launch bunker in pink and purple neon.

Same layer contract and desk anchors as the Memecoin office (see scene_memecoin.py),
so frogs, seats and the runtime engine work unchanged.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from font import BIG, SMALL, render
from px2 import INK, Canvas, dither, mix, sh
import scene_memecoin as base
from scene_memecoin import DESK_TOP, DESK_W, FLOOR_Y, H, W, WALL_TOP, chair_base, floor_cables, sticky

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'client/src/assets/office/pumpfun'
rng = np.random.default_rng(7)

PINK, PINK_HI, PINK_LO = (255, 70, 170), (255, 170, 220), (170, 30, 110)
PURP, PURP_HI, PURP_LO = (150, 80, 230), (196, 140, 255), (90, 40, 150)
STEEL, STEEL_HI, STEEL_LO = (70, 70, 84), (104, 104, 120), (46, 46, 56)
BLOCKS = [(84, 76, 96), (78, 70, 90), (90, 82, 102), (74, 66, 86), (86, 80, 94)]
MORTAR = (56, 50, 66)
HAZ_Y, HAZ_B = (240, 196, 40), (30, 28, 30)


# ---------------------------------------------------------------- shell
def ceiling(c: Canvas):
    c.rect(0, 0, W - 1, WALL_TOP - 1, (38, 34, 46))
    for _ in range(300):
        c.px(rng.integers(0, W), rng.integers(0, WALL_TOP), (30, 27, 36))
    # steel I-beams running across with rivets
    for y0 in (3, 13):
        c.rect(0, y0, W - 1, y0 + 4, INK)
        c.rect(0, y0 + 1, W - 1, y0 + 3, STEEL)
        c.hline(0, W - 1, y0 + 1, STEEL_HI)
        c.hline(0, W - 1, y0 + 3, STEEL_LO)
        for x in range(6, W, 12):
            c.px(x, y0 + 2, STEEL_HI)
            c.px(x + 1, y0 + 2, STEEL_LO)
    # vertical beam ends
    for x in range(0, W, 160):
        c.box(x, 0, x + 5, WALL_TOP - 1, STEEL, STEEL_HI, STEEL_LO)
    # bundled cables sagging between beams (pink and black)
    for x0 in range(20, W - 80, 110):
        span = int(rng.integers(60, 100))
        for k, col in enumerate([(30, 26, 36), PINK_LO, (30, 26, 36)]):
            sag = 4 + k
            for x in range(x0, x0 + span):
                t = (x - x0) / span
                c.px(x, 18 + k + int(sag * math.sin(math.pi * t)), col)
    c.hline(0, W - 1, WALL_TOP - 1, INK)


def block_wall(c: Canvas):
    top, bot = WALL_TOP, FLOOR_Y - 7
    c.rect(0, top, W - 1, bot, MORTAR)
    bh, bw = 10, 22
    for row, y in enumerate(range(top, bot, bh)):
        off = (bw // 2) * (row % 2)
        for x in range(-off, W, bw):
            col = BLOCKS[int(rng.integers(0, len(BLOCKS)))]
            x0, x1 = max(0, x), min(W - 1, x + bw - 2)
            y0, y1 = y, min(bot, y + bh - 2)
            if x1 < x0:
                continue
            c.rect(x0, y0, x1, y1, col)
            c.hline(x0, x1, y0, sh(col, 1.12))
            c.vline(x0, y0, y1, sh(col, 1.06))
            c.hline(x0, x1, y1, sh(col, .8))
            for _ in range(int(rng.integers(3, 8))):  # concrete pores
                c.px(rng.integers(x0, x1 + 1), rng.integers(y0, y1 + 1), sh(col, rng.choice([.82, 1.12])))
            if rng.random() < .1:
                c.rect(x1 - 3, y0, x1, y0 + 2, MORTAR)
    # damp stains seeping down
    for (cx, w_) in [(180, 18), (418, 26), (560, 14)]:
        for y in range(top, top + 80):
            ww = w_ * (1 - (y - top) / 90)
            for x in range(int(cx - ww), int(cx + ww)):
                if dither(x, y, .4 * (1 - (y - top) / 80)):
                    c.px(x, y, (40, 34, 48), 110)
    # hazard stripe band above the baseboard
    hy0, hy1 = bot - 8, bot - 2
    c.rect(0, hy0 - 1, W - 1, hy1 + 1, INK)
    for y in range(hy0, hy1 + 1):
        for x in range(W):
            c.px(x, y, HAZ_Y if ((x + y) // 5) % 2 else HAZ_B)
    for x in range(0, W, 3):  # scuffed paint
        if rng.random() < .25:
            c.px(x, hy0 + int(rng.integers(0, 6)), sh(HAZ_Y, .7))
    c.rect(0, bot + 1, W - 1, FLOOR_Y - 1, (34, 30, 40))
    c.hline(0, W - 1, bot + 1, (56, 52, 64))
    c.hline(0, W - 1, FLOOR_Y - 1, INK)


def concrete_floor(c: Canvas):
    y = FLOOR_Y
    while y < H:
        h = 4 + int(10 * ((y - FLOOR_Y) / (H - FLOOR_Y)) ** 1.1)
        y1 = min(H - 1, y + h - 1)
        tile_w = 40 + int(20 * (y - FLOOR_Y) / (H - FLOOR_Y))
        x = -int(rng.integers(0, tile_w))
        while x < W:
            col = mix((70, 64, 80), (80, 74, 90), rng.random())
            x0, x1 = max(0, x), min(W - 1, x + tile_w - 2)
            c.rect(x0, y, x1, y1, col)
            c.hline(x0, x1, y, sh(col, 1.1))
            for _ in range(tile_w // 6):
                c.px(rng.integers(x0, x1 + 1), rng.integers(y, y1 + 1), sh(col, rng.choice([.85, 1.1])))
            if x1 < W - 1:
                c.vline(x1 + 1, y, y1, (44, 40, 52))
            x += tile_w
        c.hline(0, W - 1, y1, (44, 40, 52))
        y = y1 + 1
    for yy in range(FLOOR_Y, FLOOR_Y + 8):
        for x in range(W):
            if dither(x, yy, .7 * (1 - (yy - FLOOR_Y) / 8)):
                c.px(x, yy, (20, 16, 26), 150)
    # yellow floor tape marking the walkway
    for x in range(0, W, 1):
        if (x // 10) % 2 == 0:
            c.px(x, FLOOR_Y + 40, HAZ_Y)
            c.px(x, FLOOR_Y + 41, sh(HAZ_Y, .75))
    # oil stains
    for _ in range(14):
        sx, sy = int(rng.integers(0, W)), int(rng.integers(FLOOR_Y + 10, H))
        r = int(rng.integers(4, 12))
        for yy in range(sy - r // 3, sy + r // 3 + 1):
            for xx in range(sx - r, sx + r + 1):
                if ((xx - sx) / r) ** 2 + ((yy - sy) / max(1, r / 3)) ** 2 < 1 and dither(xx, yy, .5):
                    c.px(xx, yy, (40, 34, 48), 120)


def puddle(c: Canvas, e: Canvas, cx, cy, rx, ry):
    """Water puddle reflecting the pink neon (reflection is self-lit)."""
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 1:
                c.px(x, y, (40, 36, 54))
                if dither(x, y, .35 * (1 - d)) and abs(x - cx) < rx * .7:
                    e.px(x, y, PINK, 140)
    c.hline(cx - rx + 3, cx + rx - 3, cy - ry, (96, 90, 110))


# --------------------------------------------------------------- wall pieces
def launchpad_board(c: Canvas):
    x0, y0, x1, y1 = 28, 44, 152, 150
    c.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, INK)
    c.box(x0 - 1, y0 - 1, x1 + 1, y1 + 1, STEEL, STEEL_HI, STEEL_LO)
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, INK)
    # corner bolts
    for (bx, by) in ((x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x0 + 1, y1 - 1), (x1 - 1, y1 - 1)):
        c.px(bx, by, STEEL_HI)
    # mounting chains
    for bx in (x0 + 16, x1 - 16):
        for y in range(WALL_TOP, y0 - 1):
            c.px(bx, y, STEEL_HI if y % 2 else STEEL_LO)
    return dict(rect=[x0 + 4, y0 + 4, x1 - 4, y1 - 4], rows=6, light=[(x0 + x1) // 2, (y0 + y1) // 2])


def neon_sign(c: Canvas, n: Canvas):
    m = render('PUMP.FUN RUGS', BIG)
    m = np.kron(m, np.ones((2, 2), bool))
    h, w = m.shape
    x0, y0 = W // 2 - w // 2, 27
    # backing: black metal plate with pink rim
    c.rect(x0 - 8, y0 - 4, x0 + w + 7, y0 + h + 3, INK)
    c.rect(x0 - 7, y0 - 3, x0 + w + 6, y0 + h + 2, (28, 22, 36))
    for x in range(x0 - 6, x0 + w + 6, 2):
        c.px(x, y0 - 3, (60, 40, 70))
    pad = np.pad(m, 1)
    edge = m & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    core = m & ~edge
    c.mask(m, x0, y0, (80, 34, 64))
    c.mask(core, x0, y0, (110, 50, 86))
    n.mask(edge, x0, y0, PINK)
    n.mask(core, x0, y0, (255, 214, 240))
    return dict(rect=[x0, y0, x0 + w - 1, y0 + h - 1], light=[W // 2, y0 + h // 2])


def big_screen(c: Canvas):
    x0, y0, x1, y1 = 262, 50, 378, 118
    c.box((x0 + x1) // 2 - 12, y0 - 4, (x0 + x1) // 2 + 12, y0, STEEL, STEEL_HI, STEEL_LO)
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, (24, 20, 30))
    c.hline(x0 + 1, x1 - 1, y0 + 1, (54, 44, 64))
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 6, INK)
    c.hline((x0 + x1) // 2 - 4, (x0 + x1) // 2 + 4, y1 - 3, PURP_LO)
    return dict(screen=[x0 + 4, y0 + 4, x1 - 4, y1 - 7], light=[(x0 + x1) // 2, (y0 + y1) // 2])


def ticker_board(c: Canvas):
    x0, y0, x1, y1 = 430, 50, 614, 72
    for bx in (x0 + 20, x1 - 20):
        for y in range(WALL_TOP, y0):
            c.px(bx, y, STEEL_HI if y % 2 else STEEL_LO)
    c.box(x0, y0, x1, y1, (36, 30, 44), (60, 50, 70), (24, 20, 30))
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, (12, 6, 14))
    for x in range(x0 + 4, x1 - 3, 2):
        for y in range(y0 + 4, y1 - 3, 2):
            c.px(x, y, (40, 18, 36))
    return dict(rect=[x0 + 4, y0 + 4, x1 - 4, y1 - 4], light=[(x0 + x1) // 2, (y0 + y1) // 2])


def rug_roll(c: Canvas, x, y, length, d, cols):
    """A rolled carpet lying sideways: body plus a spiral end facing us."""
    base_, hi, lo = cols
    r = d // 2
    c.rect(x, y - r, x + length, y + r, INK)
    c.rect(x + 1, y - r + 1, x + length - 1, y + r - 1, base_)
    c.hline(x + 1, x + length - 1, y - r + 1, hi)
    c.hline(x + 1, x + length - 1, y + r - 1, lo)
    for k in range(x + 4, x + length - 2, 6):  # woven pattern bands
        c.vline(k, y - r + 2, y + r - 2, lo)
        c.px(k + 2, y, hi)
    # fringe
    for yy in range(y - r + 1, y + r):
        c.px(x - 1, yy, (230, 214, 170))
    # spiral end
    ex = x + length
    c.ellipse(ex, y, max(2, r - 1), r, INK)
    c.ellipse(ex, y, max(1, r - 2), r - 1, hi)
    for k in range(r - 1, 0, -2):
        c.ellipse(ex, y, max(1, k * .6), k, lo if k % 4 else base_)
    c.px(ex, y, INK)


def rug_shelf(c: Canvas):
    x0, y0, x1, y1 = 432, 82, 584, 160
    for x in (x0, x1 - 3):
        c.box(x, y0, x + 3, y1 + 40, STEEL, STEEL_HI, STEEL_LO)
    shelves = [y0 + 24, y0 + 52]
    for sy in shelves + [y1 + 38]:
        c.rect(x0, sy, x1, sy + 3, INK)
        c.rect(x0 + 1, sy + 1, x1 - 1, sy + 2, STEEL)
        c.hline(x0 + 1, x1 - 1, sy + 1, STEEL_HI)
    palettes = [((170, 50, 60), (210, 90, 90), (120, 30, 40)), ((70, 60, 150), (110, 100, 200), (40, 34, 100)),
                ((180, 130, 60), (220, 170, 90), (130, 90, 40)), ((60, 120, 110), (100, 170, 150), (34, 80, 70)),
                ((150, 60, 160), (200, 110, 210), (100, 30, 110))]
    k = 0
    for sy in shelves:
        x = x0 + 6
        while x < x1 - 50:
            ln = int(rng.integers(38, 58))
            d = int(rng.integers(8, 12))
            rug_roll(c, x, sy - d // 2 - 1, ln, d, palettes[k % len(palettes)])
            k += 1
            x += ln + d // 2 + 6
    # stacked rolls on top
    rug_roll(c, x0 + 10, y0 - 6, 60, 10, palettes[2])
    rug_roll(c, x0 + 80, y0 - 6, 52, 10, palettes[4])
    # cardboard sign
    sx, sy = x0 + 40, y1 + 6
    c.box(sx, sy, sx + 64, sy + 20, (200, 160, 110), (220, 184, 136), (160, 124, 80))
    for i, line in enumerate(['RUGS', '4 PULLING']):
        mm = render(line, SMALL)
        c.mask(mm, sx + 32 - mm.shape[1] // 2, sy + 4 + i * 7, (40, 30, 30))
    c.line(sx + 2, sy + 2, sx + 6, sy + 6, (230, 222, 170))
    # rolled rug leaning on the shelf, standing upright
    lx = x1 + 4
    c.rect(lx, y0 - 10, lx + 9, y1 + 40, INK)
    c.rect(lx + 1, y0 - 9, lx + 8, y1 + 39, (150, 60, 160))
    c.vline(lx + 2, y0 - 9, y1 + 39, (200, 110, 210))
    for y in range(y0 - 6, y1 + 38, 7):
        c.hline(lx + 1, lx + 8, y, (100, 30, 110))
    c.ellipse(lx + 4, y0 - 10, 4, 2, (200, 110, 210))
    c.ellipse(lx + 4, y0 - 10, 2, 1, (100, 30, 110))


def rug_counter(c: Canvas):
    x0, y0, x1, y1 = 164, 96, 240, 138
    c.box(x0, y0, x1, y1, (34, 28, 40), (60, 50, 70), (22, 18, 26))
    c.rect(x0 + 3, y0 + 12, x1 - 3, y1 - 3, (16, 6, 8))
    for x in range(x0 + 4, x1 - 3, 2):
        for y in range(y0 + 13, y1 - 3, 2):
            c.px(x, y, (36, 12, 14))
    m = render('RUGS TODAY', SMALL)
    c.mask(m, (x0 + x1) // 2 - m.shape[1] // 2, y0 + 4, (230, 200, 210))
    return dict(digits=[x0 + 4, y0 + 15, x1 - x0 - 8], light=[(x0 + x1) // 2, y0 + 24])


def countdown_box(c: Canvas):
    x0, y0, x1, y1 = 172, 52, 232, 84
    c.box(x0, y0, x1, y1, (34, 28, 40), (60, 50, 70), (22, 18, 26))
    c.rect(x0 + 3, y0 + 11, x1 - 3, y1 - 3, (6, 14, 14))
    m = render('NEXT LAUNCH', SMALL)
    c.mask(m, (x0 + x1) // 2 - m.shape[1] // 2, y0 + 3, (200, 230, 220))
    return dict(pos=[x0 + 13, y0 + 15])


def graffiti(c: Canvas, text, x, y, col, scale=2):
    m = render(text, SMALL)
    m = np.kron(m, np.ones((scale, scale), bool))
    # spray overspray halo
    for j, i in zip(*np.nonzero(m)):
        for dx, dy in ((1, 1), (-1, 0), (0, -1)):
            if rng.random() < .3:
                c.px(x + i + dx, y + j + dy, col, 90)
    c.mask(m, x, y, col)
    # drips
    for i in range(0, m.shape[1], 3):
        col_has = np.nonzero(m[:, i])[0]
        if len(col_has) and rng.random() < .5:
            yy = y + col_has.max()
            for k in range(int(rng.integers(2, 7))):
                c.px(x + i, yy + k, col, 220 - k * 25)


def siren(c: Canvas):
    sx, sy = 200, 40
    c.vline(sx, WALL_TOP - 4, sy - 6, STEEL_LO)
    c.box(sx - 5, sy, sx + 5, sy + 3, STEEL, STEEL_HI, STEEL_LO)
    c.rect(sx - 3, sy - 5, sx + 3, sy, (90, 20, 24))
    c.rect(sx - 2, sy - 6, sx + 2, sy - 6, (90, 20, 24))
    c.px(sx - 2, sy - 4, (150, 60, 60))
    return dict(pos=[sx, sy - 2])


def server_rack(c: Canvas):
    x0, y0, x1, y1 = 2, 104, 28, FLOOR_Y + 8
    c.box(x0, y0, x1, y1, (30, 28, 36), (52, 50, 60), (20, 18, 24))
    leds = []
    for k, y in enumerate(range(y0 + 4, y1 - 6, 8)):
        c.box(x0 + 3, y, x1 - 3, y + 6, (44, 42, 52), (64, 62, 74), (30, 28, 36))
        for vx in range(x0 + 5, x1 - 10, 2):
            c.px(vx, y + 3, (24, 22, 28))
        leds.append([x1 - 7, y + 2])
        leds.append([x1 - 5, y + 4])
    for i, col in enumerate([(30, 28, 34), PINK_LO, (30, 28, 34), PURP_LO]):
        c.vline(x1 + 2 + i, y0 + 10, y1 + 4, col)
    return dict(leds=leds)


def vending(c: Canvas, e: Canvas):
    x0, y0, x1, y1 = 542, 146, 586, FLOOR_Y + 8
    c.box(x0, y0, x1, y1, (54, 30, 80), (80, 50, 110), (34, 18, 54))
    # glowing front window with cans (self-lit)
    gx0, gy0, gx1, gy1 = x0 + 4, y0 + 12, x1 - 12, y1 - 16
    c.rect(gx0 - 1, gy0 - 1, gx1 + 1, gy1 + 1, INK)
    cans = [(126, 226, 84), PINK, (90, 200, 255), (255, 200, 60)]
    for y in range(gy0, gy1 + 1):
        for x in range(gx0, gx1 + 1):
            e.px(x, y, (60, 190, 210) if (y - gy0) % 10 else (30, 100, 120))
    for r, yy in enumerate(range(gy0 + 2, gy1 - 3, 10)):
        for k, xx in enumerate(range(gx0 + 2, gx1 - 2, 6)):
            col = cans[(r + k) % 4]
            e.rect(xx, yy, xx + 3, yy + 6, col)
            e.hline(xx, xx + 3, yy, (240, 240, 240))
            e.vline(xx, yy + 1, yy + 6, sh(col, 1.25))
    c.a[gy0:gy1 + 1, gx0:gx1 + 1, 3] = 0
    # header sign
    e.rect(x0 + 3, y0 + 3, x1 - 3, y0 + 9, (40, 12, 40))
    m = render('ENERGY', SMALL)
    e.mask(m, (x0 + x1) // 2 - m.shape[1] // 2, y0 + 4, PINK_HI)
    c.a[y0 + 3:y0 + 10, x0 + 3:x1 - 2, 3] = 0
    # coin slot panel
    c.box(x1 - 10, gy0, x1 - 3, gy0 + 20, (34, 18, 54), (60, 40, 80), None)
    c.rect(x1 - 7, gy0 + 4, x1 - 6, gy0 + 8, INK)
    c.rect(x0 + 4, y1 - 12, x1 - 12, y1 - 6, INK)
    return dict(light=[(gx0 + gx1) // 2, (gy0 + gy1) // 2])


def bunker_door(c: Canvas, e: Canvas):
    x0, y0, x1, y1 = 594, 104, 636, FLOOR_Y + 2
    c.rect(x0 - 3, y0 - 3, x1 + 2, y1, INK)
    c.rect(x0 - 2, y0 - 2, x1 + 1, y1, STEEL_LO)
    c.box(x0, y0, x1, y1, (86, 90, 100), (116, 120, 130), (62, 64, 74))
    for y in (y0 + 6, y1 - 8):  # hinges and rivets
        for x in range(x0 + 3, x1 - 2, 4):
            c.px(x, y, (130, 134, 144))
    # hazard bottom
    for y in range(y1 - 16, y1 - 3):
        for x in range(x0 + 2, x1 - 1):
            c.px(x, y, HAZ_Y if ((x + y) // 4) % 2 else HAZ_B)
    # porthole
    cx, cy = (x0 + x1) // 2, y0 + 22
    c.ellipse(cx, cy, 9, 9, INK)
    c.ellipse(cx, cy, 8, 8, (130, 134, 144))
    c.ellipse(cx, cy, 6, 6, INK)
    for y in range(cy - 5, cy + 6):
        for x in range(cx - 5, cx + 6):
            if (x - cx) ** 2 + (y - cy) ** 2 <= 25:
                e.px(x, y, mix((120, 60, 180), (60, 30, 100), (y - cy + 5) / 10))
                c.a[y, x, 3] = 0
    e.px(cx - 2, cy - 3, (220, 190, 255))
    # wheel handle
    hx, hy = cx, y0 + 50
    c.ellipse(hx, hy, 7, 7, INK)
    c.ellipse(hx, hy, 6, 6, (180, 40, 40))
    c.ellipse(hx, hy, 4, 4, (86, 90, 100))
    c.hline(hx - 6, hx + 6, hy, (180, 40, 40))
    c.vline(hx, hy - 6, hy + 6, (180, 40, 40))
    c.ellipse(hx, hy, 1, 1, (210, 210, 220))
    # EXIT sign
    ex0, ey0 = x0 + 5, y0 - 14
    c.box(ex0, ey0, ex0 + 32, ey0 + 9, (40, 46, 44), None, None)
    e.rect(ex0 + 2, ey0 + 2, ex0 + 30, ey0 + 7, (30, 120, 70))
    e.mask(render('EXIT', SMALL), ex0 + 9, ey0 + 2, (200, 255, 210))
    return dict(rect=[x0, y0, x1, y1], light_exit=[ex0 + 16, ey0 + 5], light_door=[cx, cy])


def caged_lamp(c: Canvas, e: Canvas, lx):
    c.vline(lx, 0, 28, (30, 26, 36))
    c.box(lx - 3, 27, lx + 3, 30, STEEL, STEEL_HI, STEEL_LO)
    # wire cage around the bulb
    for y in range(31, 41):
        w_ = 5 if y < 39 else 4
        c.px(lx - w_, y, (60, 60, 70)); c.px(lx + w_, y, (60, 60, 70))
    for x in range(lx - 4, lx + 5, 2):
        c.px(x, 40, (60, 60, 70))
    c.hline(lx - 5, lx + 5, 34, (60, 60, 70))
    e.ellipse(lx, 35, 3, 4, (236, 220, 255))
    e.px(lx - 1, 33, (255, 255, 255))
    return [lx, 36]


# ------------------------------------------------------------------ the boss
def boss_area(bg: Canvas, bd: Canvas, e: Canvas):
    cx = W // 2
    # crooked purple rug, one corner flipped up (somebody pulled it)
    rug = [(cx - 96, FLOOR_Y + 6), (cx + 86, FLOOR_Y + 2), (cx + 104, FLOOR_Y + 32), (cx - 88, FLOOR_Y + 38)]
    bg.poly(rug, (96, 40, 120))
    inner = [(cx - 88, FLOOR_Y + 9), (cx + 80, FLOOR_Y + 5), (cx + 96, FLOOR_Y + 29), (cx - 82, FLOOR_Y + 35)]
    bg.poly(inner, (130, 60, 160))
    for y in range(FLOOR_Y + 10, FLOOR_Y + 34, 4):
        for x in range(cx - 84, cx + 92, 6):
            if bg.get(x, y) == (130, 60, 160):
                bg.px(x, y, PINK_LO)
    flip = [(cx + 104, FLOOR_Y + 32), (cx + 86, FLOOR_Y + 34), (cx + 98, FLOOR_Y + 22)]
    bg.poly(flip, (70, 26, 90))
    bg.line(cx + 86, FLOOR_Y + 34, cx + 98, FLOOR_Y + 22, (150, 90, 180))
    # throne gaming chair in purple velvet with pink stripes
    gold = (240, 180, 90)
    X0, X1, TOP, BOT = cx - 24, cx + 24, 108, 184
    velvet, v_hi, v_lo, v_dk = (92, 40, 130), (130, 70, 170), (64, 24, 96), (44, 14, 66)
    def half_at(r):
        if r < 4:
            return 16 + r * 2           # rounded top
        if r < 30:
            return 27                   # wide winged shoulders
        if r < 36:
            return 27 - (r - 30)        # wings taper in
        return 21                       # seat back
    for y in range(TOP, BOT + 1):
        hw = half_at(y - TOP)
        bg.hline(cx - hw, cx + hw, y, INK)
        bg.hline(cx - hw + 1, cx + hw - 1, y, velvet)
        bg.px(cx - hw + 1, y, v_hi); bg.px(cx - hw + 2, y, v_hi)
        bg.px(cx + hw - 1, y, v_dk); bg.px(cx + hw - 2, y, v_lo)
    # wing panels are darker so the shape reads as a racing seat
    for y in range(TOP + 4, TOP + 36):
        hw = half_at(y - TOP)
        for x in range(cx - hw + 3, cx - 15):
            bg.px(x, y, v_lo)
        for x in range(cx + 15, cx + hw - 2):
            bg.px(x, y, v_lo)
        bg.px(cx - 15, y, INK); bg.px(cx + 15, y, INK)
    # pink racing stripes down the middle panel
    for y in range(TOP + 3, BOT):
        bg.px(cx - 9, y, PINK_LO); bg.px(cx - 8, y, PINK)
        bg.px(cx + 8, y, PINK); bg.px(cx + 9, y, PINK_LO)
    # harness slots and head pillow
    for hx in (cx - 12, cx + 10):
        bg.rect(hx, TOP + 8, hx + 2, TOP + 13, v_dk)
    bg.box(cx - 7, TOP + 4, cx + 7, TOP + 14, (40, 36, 48), (64, 60, 76), (28, 24, 34))
    mm = render('$', SMALL)
    bg.mask(mm, cx - 1, TOP + 7, gold)
    for y in range(TOP + 40, BOT - 4, 6):  # stitched panels
        bg.hline(cx - 19, cx - 11, y, v_lo)
        bg.hline(cx + 11, cx + 19, y, v_lo)
    X0, X1 = cx - 27, cx + 27
    # armrests
    for ax0 in (X0 - 12, X1 + 1):
        ax1 = ax0 + 11
        bg.rect(ax0, 158, ax1, BOT, INK)
        bg.rect(ax0 + 1, 159, ax1 - 1, BOT, (40, 36, 48))
        bg.rect(ax0 + 1, 159, ax1 - 1, 162, (70, 64, 80))
        bg.rect(ax0 + 4, 166, ax1 - 4, BOT, STEEL)
    # boss desk: black steel with a pink LED strip
    x0, x1, top = cx - 74, cx + 73, 180
    D = 8
    bd.rect(x0, top, x1, top + D + 3, INK)
    bd.rect(x0 + 1, top + 1, x1 - 1, top + D, (40, 38, 48))
    bd.hline(x0 + 1, x1 - 1, top + D, (70, 68, 82))
    bd.rect(x0 + 1, top + D + 1, x1 - 1, top + D + 2, (24, 22, 30))
    for _ in range(20):  # brushed metal
        gx, gy = int(rng.integers(x0 + 3, x1 - 12)), int(rng.integers(top + 2, top + D))
        bd.hline(gx, gx + int(rng.integers(4, 10)), gy, (50, 48, 60))
    fy = FLOOR_Y + 22
    bd.rect(x0 + 2, top + D + 3, x1 - 2, fy, INK)
    bd.rect(x0 + 3, top + D + 3, x1 - 3, fy - 1, (30, 28, 36))
    for x in range(x0 + 6, x1 - 5, 3):  # vented front
        for y in range(top + D + 8, fy - 6, 3):
            bd.px(x, y, (18, 16, 22))
    for (p0, p1) in ((x0 + 4, x0 + 10), (x1 - 10, x1 - 4)):
        bd.box(p0, top + D + 3, p1, fy, STEEL, STEEL_HI, STEEL_LO)
    strips = [[x0 + 2, top + D + 4, x1 - 2]]
    # BOSS plate in pink
    m = render('BOSS', BIG)
    pw = m.shape[1] + 8
    bd.box(cx - pw // 2, top + D + 10, cx + pw // 2, top + D + 20, (60, 20, 50), (90, 40, 80), (40, 10, 34))
    bd.mask(m, cx - m.shape[1] // 2 + 1, top + D + 12, PINK_HI)
    # red button under a glass case
    bx = cx - 50
    bd.rect(bx - 1, top - 1, bx + 17, top + 2, INK)
    bd.rect(bx, top, bx + 16, top + 1, (60, 60, 70))
    bd.ellipse(bx + 8, top - 3, 6, 3, (180, 20, 20))
    bd.ellipse(bx + 8, top - 4, 5, 2, (230, 50, 40))
    bd.px(bx + 6, top - 5, (255, 160, 150))
    for y in range(top - 14, top):  # glass box outline
        bd.px(bx, y, (170, 200, 220), 160); bd.px(bx + 16, y, (170, 200, 220), 160)
    bd.hline(bx, bx + 16, top - 14, (170, 200, 220), 160)
    bd.line(bx + 3, top - 12, bx + 7, top - 8, (230, 240, 255), 140)
    # rolled rug on the desk
    rug_roll(bd, cx + 22, top - 5, 34, 8, ((170, 50, 60), (210, 90, 90), (120, 30, 40)))
    # energy cans
    for k in range(2):
        ccx = cx - 26 + k * 7
        bd.box(ccx, top - 10, ccx + 5, top, (38, 38, 44), (70, 70, 80), None)
        bd.rect(ccx + 1, top - 6, ccx + 4, top - 5, PINK)
    return dict(boss_anchor=[cx, top + 4], plus=[cx, 146], desk_top=top,
                chair=[X0 - 13, TOP - 4, X1 + 13, top + 34]), strips


# --------------------------------------------------------------- worker desks
def gaming_chair(c: Canvas, cx, top, bottom, accent):
    body, hi, lo = (34, 32, 40), (60, 58, 70), (22, 20, 26)
    for y in range(top, bottom + 1):
        r = y - top
        half = 15 if r > 8 else 17 if r > 3 else 12 + r
        c.hline(cx - half, cx + half, y, INK)
        c.hline(cx - half + 1, cx + half - 1, y, body)
        c.px(cx - half + 1, y, hi); c.px(cx + half - 1, y, lo)
    for y in range(top + 2, bottom):  # racing stripes
        c.px(cx - 6, y, accent); c.px(cx - 5, y, sh(accent, .7))
        c.px(cx + 5, y, accent); c.px(cx + 6, y, sh(accent, .7))
    c.rect(cx - 3, top + 4, cx + 3, top + 7, lo)  # harness slot
    c.rect(cx - 3, top + 4, cx + 3, top + 4, INK)
    for ax in (cx - 19, cx + 17):
        c.box(ax, bottom - 8, ax + 2, bottom + 2, (50, 50, 58), (76, 76, 86), None)


def gaming_desk(c: Canvas, x, y, variant):
    W_ = DESK_W
    D = 9
    c.rect(x, y, x + W_ - 1, y + D + 3, INK)
    c.rect(x + 1, y + 1, x + W_ - 2, y + D, (36, 34, 44))
    c.hline(x + 1, x + W_ - 2, y + 1, (28, 26, 34))
    c.hline(x + 1, x + W_ - 2, y + D, (64, 60, 76))
    c.rect(x + 1, y + D + 1, x + W_ - 2, y + D + 2, (24, 22, 30))
    # carbon-fibre texture on top
    for gy in range(y + 2, y + D):
        for gx in range(x + 2, x + W_ - 2, 4):
            c.px(gx + (gy % 2) * 2, gy, (44, 42, 54))
    top_end = y + D + 3
    floor = top_end + 29
    # back panel: black steel mesh, closed to the floor
    c.rect(x + 2, top_end, x + W_ - 3, floor, INK)
    c.rect(x + 3, top_end, x + W_ - 4, floor - 1, (30, 28, 36))
    for yy in range(top_end + 4, floor - 4, 2):
        for xx in range(x + 6 + (yy % 4), x + W_ - 7, 4):
            c.px(xx, yy, (18, 16, 22))
    c.rect(x + 3, floor - 4, x + W_ - 4, floor - 1, (22, 20, 26))
    for lx in (x, x + W_ - 6):  # legs
        c.box(lx, top_end - 1, lx + 5, floor, (50, 48, 58), (80, 78, 92), (32, 30, 38))
        c.hline(lx - 1, lx + 6, floor, INK)
    # desk number in a pink badge
    num = render(str(variant + 1), SMALL)
    c.box(x + 16, top_end + 6, x + 25, top_end + 14, (60, 20, 50), (90, 40, 80), (40, 10, 34))
    c.mask(num, x + 19, top_end + 8, PINK_HI)
    # stickers
    for k in range(1 + variant % 2):
        sx, sy = x + 74 + k * 8, floor - 15 + k * 3
        col = [(126, 226, 84), PINK, (90, 200, 255), (255, 214, 60)][(variant + k) % 4]
        c.rect(sx - 1, sy - 1, sx + 5, sy + 5, INK)
        c.rect(sx, sy, sx + 4, sy + 4, col)
        c.px(sx + 1, sy + 1, INK); c.px(sx + 3, sy + 1, INK); c.hline(sx + 1, sx + 3, sy + 3, INK)
    for sx_ in range(x - 2, x + W_ + 2):
        c.px(sx_, floor + 1, (0, 0, 0), 110)
        if x + 4 <= sx_ <= x + W_ - 4:
            c.px(sx_, floor + 2, (0, 0, 0), 70)
    return top_end, floor, [x + 3, top_end + 1, x + W_ - 4]


def slim_monitor(c: Canvas, mx, base_y, wide=36):
    w, h = wide, 26
    x0, y0 = mx - w // 2, base_y - h - 7
    c.box(mx - 8, base_y - 1, mx + 7, base_y + 1, (40, 38, 48), (64, 62, 76), (28, 26, 32))
    c.box(mx - 1, base_y - 8, mx + 1, base_y - 1, (40, 38, 48), (64, 62, 76), None)
    c.rect(x0, y0, x0 + w - 1, y0 + h - 1, INK)
    c.rect(x0 + 1, y0 + 1, x0 + w - 2, y0 + h - 2, (24, 22, 30))
    sx0, sy0, sx1, sy1 = x0 + 2, y0 + 2, x0 + w - 3, y0 + h - 4
    c.rect(sx0, sy0, sx1, sy1, (14, 8, 22))
    c.hline(x0 + 6, x0 + w - 7, y0 + h - 2, PURP_LO)
    return [sx0, sy0, sx1, sy1]


def desk_props(c: Canvas, e: Canvas, x, y, fx, variant, mon):
    key = (40, 38, 48)
    c.box(fx - 13, y + 3, fx + 12, y + 7, key, (60, 58, 70), None)
    for kx in range(fx - 11, fx + 11, 2):  # RGB keyboard glow is self-lit
        e.px(kx, y + 5, [PINK, PURP, (90, 200, 255)][(kx // 4) % 3], 200)
    c.box(fx + 15, y + 4, fx + 19, y + 7, key, (60, 58, 70), None)
    e.px(fx + 17, y + 5, PINK)
    steam, lamps = [], []
    if variant in (0, 2, 4):  # energy can towers
        for k in range(2 + variant % 2):
            cx_, cy_ = x + 6 + k * 7, y + 5
            col = [(126, 226, 84), PINK, (90, 200, 255)][(k + variant) % 3]
            c.box(cx_, cy_ - 10, cx_ + 5, cy_, (38, 38, 44), (70, 70, 80), None)
            c.rect(cx_ + 1, cy_ - 6, cx_ + 4, cy_ - 5, col)
    if variant == 1:  # headphones and chips
        c.ellipse(x + 10, y + 1, 6, 4, INK)
        c.ellipse(x + 10, y + 1, 5, 3, (36, 34, 44))
        c.rect(x + 4, y - 1, x + 6, y + 4, PINK)
        c.rect(x + 14, y - 1, x + 16, y + 4, PINK)
        c.box(x + 20, y - 4, x + 29, y + 6, (230, 60, 60), (255, 120, 100), (170, 30, 30))
        c.mask(render('CHIP', SMALL)[:, :8], x + 21, y - 1, (255, 230, 120))
    if variant == 3:  # pink neon tube lamp, a light source
        lx = x + 8
        c.box(lx, y + 2, lx + 8, y + 6, (40, 38, 48), (64, 62, 76), None)
        c.vline(lx + 4, y - 18, y + 2, (60, 58, 70))
        e.rect(lx + 2, y - 22, lx + 6, y - 19, PINK)
        e.hline(lx + 3, lx + 5, y - 21, (255, 220, 240))
        lamps.append([lx + 4, y - 20])
        c.ellipse(fx + 25, y + 2, 4, 3, (110, 160, 80))  # frog plush
        c.ellipse(fx + 23, y - 1, 1, 1, (240, 236, 220)); c.ellipse(fx + 27, y - 1, 1, 1, (240, 236, 220))
    if variant == 4:  # mug
        mx, my = x + 22, y + 6
        c.box(mx, my - 8, mx + 7, my, (40, 30, 50), None, (30, 20, 40))
        c.rect(mx + 2, my - 5, mx + 5, my - 3, PINK)
        c.rect(mx - 2, my - 6, mx, my - 3, INK)
        steam.append([mx + 3, my - 9])
    if variant == 0:
        steam = []
    for k in range(variant % 3):
        sticky(c, mon[0] - 3 + k * 6, mon[1] + 1 + (k % 2) * 3, [PINK_HI, (140, 220, 240), (246, 212, 76)][k])
    return steam, lamps


# ----------------------------------------------------------------------- main
def build():
    OUT.mkdir(parents=True, exist_ok=True)
    bg, e, neon = Canvas(W, H), Canvas(W, H), Canvas(W, H)
    bossdesk, chairs, desks = Canvas(W, H), Canvas(W, H), Canvas(W, H)
    layout: dict = {'size': [W, H]}

    ceiling(bg)
    block_wall(bg)
    concrete_floor(bg)
    puddle(bg, e, 120, FLOOR_Y + 26, 22, 4)
    puddle(bg, e, 520, FLOOR_Y + 30, 16, 3)
    layout['launchpad'] = launchpad_board(bg)
    layout['neon'] = neon_sign(bg, neon)
    layout['tv'] = big_screen(bg)
    layout['ticker'] = ticker_board(bg)
    rug_shelf(bg)
    layout['counter'] = rug_counter(bg)
    layout['countdown'] = countdown_box(bg)
    graffiti(bg, 'SEND IT', 166, 148, PINK)
    graffiti(bg, 'LFG', 392, 140, (126, 226, 84))
    graffiti(bg, 'NGMI', 40, 162, (90, 200, 255), 1)
    layout['siren'] = siren(bg)
    layout['rig'] = server_rack(bg)
    vend = vending(bg, e)
    layout['door'] = bunker_door(bg, e)
    lamps = [caged_lamp(bg, e, lx) for lx in (104, 536)]
    floor_cables(bg, [(31, 206), (90, 210), (180, 213), (236, 211)], (40, 20, 50))
    floor_cables(bg, [(418, 213), (480, 210), (540, 206)], (40, 20, 50))
    boss, strips = boss_area(bg, bossdesk, e)
    layout['boss'] = boss

    desks_l = []
    gap = (W - 5 * DESK_W) // 6
    accents = [PINK, (90, 200, 255), PURP_HI, (126, 226, 84), (255, 200, 60)]
    for i in range(5):
        x = gap + i * (DESK_W + gap)
        fx = x + 36
        floor_y = DESK_TOP + 12 + 29
        chair_base(chairs, fx, floor_y - 2)
        gaming_chair(chairs, fx, DESK_TOP - 32, DESK_TOP + 6, accents[i])
        _, _, strip = gaming_desk(desks, x, DESK_TOP, i)
        strips.append(strip)
        mx = x + DESK_W - 22
        screen = slim_monitor(desks, mx, DESK_TOP + 4, 36)
        steam, dl = desk_props(desks, e, x, DESK_TOP, fx, i, screen)
        desks_l.append(dict(x=x, frog=[fx, DESK_TOP], screen=screen, screen2=None,
                            steam=steam, lamps=dl, clip=DESK_TOP + 2))
    layout['desks'] = desks_l
    layout['strips'] = strips

    floor_cables(desks, [(0, 352), (90, 344), (200, 350), (330, 342), (460, 350), (640, 344)], (40, 20, 50))
    for (cx_, cy_) in [(150, 349), (410, 352)]:
        desks.box(cx_, cy_ - 4, cx_ + 6, cy_ + 2, (38, 38, 44), (70, 70, 80), None)
        desks.rect(cx_ + 1, cy_ - 2, cx_ + 5, cy_ - 1, PINK)

    L_ = layout
    layout['lights'] = (
        [dict(x=x, y=y, r=170, col=[0.85, 0.75, 1.0], i=0.85, cone=True, kind='lamp') for x, y in lamps] + [
        dict(id='neon', x=L_['neon']['light'][0], y=L_['neon']['light'][1] + 6, r=165, col=[1.0, 0.32, 0.72], i=0.95),
        dict(id='tv', x=L_['tv']['light'][0], y=L_['tv']['light'][1], r=112, col=[0.8, 0.4, 1.0], i=0.6),
        dict(x=L_['launchpad']['light'][0], y=L_['launchpad']['light'][1], r=112, col=[0.8, 0.45, 1.0], i=0.55),
        dict(x=vend['light'][0], y=vend['light'][1], r=74, col=[0.4, 0.9, 1.0], i=0.6),
        dict(x=L_['door']['light_exit'][0], y=L_['door']['light_exit'][1], r=40, col=[0.3, 1.0, 0.5], i=0.5),
        dict(x=L_['door']['light_door'][0], y=L_['door']['light_door'][1], r=40, col=[0.6, 0.3, 1.0], i=0.35),
        dict(id='plus', x=L_['boss']['plus'][0], y=L_['boss']['plus'][1], r=44, col=[1.0, 0.8, 0.35], i=0.55),
        dict(id='ticker', x=L_['ticker']['light'][0], y=L_['ticker']['light'][1], r=72, col=[1.0, 0.35, 0.7], i=0.42),
        dict(x=L_['counter']['light'][0], y=L_['counter']['light'][1], r=46, col=[1.0, 0.2, 0.2], i=0.45),
        dict(id='siren', x=L_['siren']['pos'][0], y=L_['siren']['pos'][1], r=260, col=[1.0, 0.12, 0.12], i=1.0)])
    layout['theme'] = dict(
        ambient=[0.28, 0.22, 0.40], screen='pump', screenLight=[0.75, 0.4, 1.0], tv='pump', tvLight=[0.8, 0.4, 1.0],
        rain=False, cones=[210, 180, 255], coneAlpha=0.1, deskLamp=[1.0, 0.4, 0.8], tickerStyle='launch',
        coins=['$GIGA', '$CHAD', '$FROGE', '$RUGME', '$SEND', '$KEK', '$HOPPY', '$WAGMI'],
        tickerSym=[255, 110, 200], neonHalo=[255, 90, 190], ledColors=[[200, 90, 255], [90, 220, 255]], rugStart=17)

    for name, cv in [('bg', bg), ('emissive', e), ('neon', neon), ('bossdesk', bossdesk),
                     ('chairs', chairs), ('desks', desks)]:
        cv.save(OUT / f'{name}.png')
    (OUT / 'layout.json').write_text(json.dumps(layout))
    return layout


if __name__ == '__main__':
    build()
    print('ok')
