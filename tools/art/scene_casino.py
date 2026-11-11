"""Lucky Frog Casino: the free lounge where tired frogs chill until they are rested.

Same layer contract as the offices (see scene_memecoin.py), so office_engine.js lights and animates it:
  bg        room shell, slot machines, back bar, seat backs behind frogs
  chairs    seat backs (behind frogs)
  bossdesk  bar counter (in front of the bar frogs)
  desks     sofa, card table and armchairs fronts, floor clutter (in front of the front-row frogs)
  emissive  self-lit pixels (chandelier bulbs, slot glass, bar backlight, jackpot frame)
  neon      lit neon letters (toggled by the flicker)
Seats are listed in layout['desks'] in the order frogs fill them.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from font import BIG, SMALL, render
from px2 import INK, Canvas, dither, mix, sh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'client/src/assets/office/casino'
W, H = 640, 360
WALL_TOP, FLOOR_Y, RAIL = 22, 200, 150
FRONT = 282                     # front row seat line (same as office desks)
BAR_TOP = 196                   # bar counter line
rng = np.random.default_rng(77)

WINE, WINE_HI, WINE_LO, WINE_DK = (92, 22, 40), (118, 36, 56), (70, 14, 30), (46, 8, 20)
GOLD, GOLD_HI, GOLD_LO = (206, 160, 64), (250, 214, 120), (140, 98, 36)
WOOD, WOOD_HI, WOOD_LO, WOOD_DK = (88, 44, 30), (118, 64, 42), (64, 30, 20), (42, 18, 12)
FELT, FELT_HI, FELT_LO = (26, 112, 70), (44, 146, 92), (16, 78, 48)
TEAL, TEAL_HI, TEAL_LO = (40, 128, 140), (72, 172, 180), (24, 84, 96)
EMER, EMER_HI, EMER_LO = (30, 98, 66), (52, 132, 92), (18, 64, 42)
PINK, PINK_CORE = (255, 64, 150), (255, 210, 236)
LEATHER, LEATHER_HI, LEATHER_LO = (140, 40, 44), (182, 70, 66), (96, 24, 30)

DAMASK = [
    "....#....",
    "...#.#...",
    "..#.#.#..",
    ".#.###.#.",
    "#.##.##.#",
    ".#.###.#.",
    "..#.#.#..",
    "...#.#...",
    "....#....",
]


# ---------------------------------------------------------------- shell
def ceiling(c: Canvas):
    c.rect(0, 0, W - 1, WALL_TOP - 1, (36, 18, 30))
    for x0 in range(2, W, 52):
        c.box(x0, 1, x0 + 46, 11, (48, 24, 38), (62, 32, 48), (28, 12, 22))
        c.rect(x0 + 4, 4, x0 + 42, 8, (40, 20, 32))
        c.px(x0 + 23, 6, GOLD_LO)
    c.rect(0, 13, W - 1, WALL_TOP - 1, GOLD_LO)
    c.hline(0, W - 1, 13, GOLD_HI)
    c.hline(0, W - 1, 14, GOLD)
    for x in range(0, W, 4):
        c.rect(x, 16, x + 1, 18, (110, 76, 28))
        c.px(x, 16, GOLD)
    c.hline(0, W - 1, WALL_TOP - 2, (90, 60, 24))
    c.hline(0, W - 1, WALL_TOP - 1, INK)


def wallpaper(c: Canvas):
    top, bot = WALL_TOP, RAIL - 1
    c.rect(0, top, W - 1, bot, WINE)
    motif = np.array([[ch == '#' for ch in r] for r in DAMASK])
    for row, y in enumerate(range(top + 3, bot - 4, 15)):
        off = 10 if row % 2 else 0
        for x in range(-off, W, 20):
            c.mask(motif, x, y, WINE_HI)
            c.px(x + 4, y + 4, (150, 96, 54))
    for x in range(0, W, 20):
        for y in range(top, bot):
            if y % 2 == 0:
                c.px(x + 15, y, WINE_LO)
    for y in range(top, top + 12):
        for x in range(W):
            if dither(x, y, .55 * (1 - (y - top) / 12)):
                c.px(x, y, (24, 4, 12), 130)


def wainscot(c: Canvas):
    c.rect(0, RAIL, W - 1, RAIL + 4, GOLD_LO)
    c.hline(0, W - 1, RAIL, INK)
    c.hline(0, W - 1, RAIL + 1, GOLD_HI)
    c.hline(0, W - 1, RAIL + 2, GOLD)
    c.hline(0, W - 1, RAIL + 4, (90, 60, 24))
    top, bot = RAIL + 5, FLOOR_Y - 7
    c.rect(0, top, W - 1, bot, WOOD_LO)
    for x0 in range(4, W - 20, 40):
        x1 = min(W - 2, x0 + 34)
        c.rect(x0, top + 4, x1, bot - 4, WOOD_DK)
        c.rect(x0 + 1, top + 5, x1 - 1, bot - 5, WOOD)
        c.hline(x0 + 1, x1 - 1, top + 5, WOOD_HI)
        c.vline(x0 + 1, top + 5, bot - 5, WOOD_HI)
        c.rect(x0 + 5, top + 9, x1 - 5, bot - 9, (76, 36, 24))
        c.hline(x0 + 5, x1 - 5, bot - 9, WOOD_HI)
        c.vline(x1 - 5, top + 9, bot - 9, WOOD_HI)
        c.px(x0 + 5, top + 9, GOLD_LO); c.px(x1 - 5, top + 9, GOLD_LO)
    c.rect(0, bot + 1, W - 1, FLOOR_Y - 1, WOOD_DK)
    c.hline(0, W - 1, bot + 1, GOLD_LO)
    c.hline(0, W - 1, FLOOR_Y - 1, INK)


def pilaster(c: Canvas, x):
    """Gold-trimmed column that frames the center of the room."""
    c.rect(x - 5, WALL_TOP, x + 5, FLOOR_Y - 1, INK)
    c.rect(x - 4, WALL_TOP, x + 4, FLOOR_Y - 1, (120, 40, 52))
    c.vline(x - 3, WALL_TOP, FLOOR_Y - 1, (150, 60, 70))
    c.vline(x + 3, WALL_TOP, FLOOR_Y - 1, (84, 22, 34))
    for fx in (x - 1, x + 1):
        c.vline(fx, WALL_TOP + 10, FLOOR_Y - 12, (96, 28, 40))
    for y0 in (WALL_TOP, FLOOR_Y - 10):
        c.rect(x - 7, y0, x + 7, y0 + 7, INK)
        c.rect(x - 6, y0 + 1, x + 6, y0 + 6, GOLD)
        c.hline(x - 6, x + 6, y0 + 1, GOLD_HI)
        c.hline(x - 6, x + 6, y0 + 6, GOLD_LO)


def carpet(c: Canvas):
    """Classic casino carpet: wine red with gold rings and teal diamonds."""
    base, dark = (112, 20, 36), (92, 14, 30)
    for y in range(FLOOR_Y, H):
        for x in range(W):
            u, v = x % 32, (y - FLOOR_Y) % 20
            col = base if ((x // 32) + ((y - FLOOR_Y) // 20)) % 2 == 0 else dark
            d = math.hypot(u - 16, (v - 10) * 1.6)
            if 6.5 <= d < 8.2:
                col = (176, 128, 52)
            elif d < 2.4:
                col = (40, 120, 120)
            elif abs(u - 0) + abs(v - 10) * 1.6 < 4 or abs(u - 32) + abs(v - 10) * 1.6 < 4:
                col = (48, 136, 132)
            elif (u + v) % 8 == 0 and d > 9:
                col = mix(col, (150, 60, 50), .5)
            c.px(x, y, col)
    # depth: darker towards the wall
    for y in range(FLOOR_Y, FLOOR_Y + 40):
        k = 1 - (y - FLOOR_Y) / 40
        for x in range(W):
            if dither(x, y, .6 * k):
                c.px(x, y, (30, 4, 10), 150)
    c.hline(0, W - 1, FLOOR_Y, INK)


# ---------------------------------------------------------------- wall pieces
def neon_sign(c: Canvas, n: Canvas, e: Canvas):
    text = 'LUCKY FROG CASINO'
    m = np.kron(render(text, BIG), np.ones((2, 2), bool))
    h, w = m.shape
    x0, y0 = W // 2 - w // 2, 29
    # bulb frame behind the tubes
    bx0, by0, bx1, by1 = x0 - 10, y0 - 6, x0 + w + 9, y0 + h + 5
    c.rect(bx0, by0, bx1, by1, INK)
    c.rect(bx0 + 1, by0 + 1, bx1 - 1, by1 - 1, (50, 12, 30))
    c.rect(bx0 + 3, by0 + 3, bx1 - 3, by1 - 3, (30, 6, 18))
    c.hline(bx0 + 1, bx1 - 1, by0 + 1, (80, 24, 46))
    bulbs = []
    for x in range(bx0 + 2, bx1 - 1, 4):
        bulbs += [[x, by0 + 1], [x, by1 - 1]]
    for y in range(by0 + 5, by1 - 3, 4):
        bulbs += [[bx0 + 1, y], [bx1 - 1, y]]
    for bx, by in bulbs:
        c.px(bx, by, (120, 90, 50))
    pad = np.pad(m, 1)
    edge = m & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    core = m & ~edge
    c.mask(m, x0, y0, (90, 30, 58))
    c.mask(core, x0, y0, (120, 44, 76))
    n.mask(edge, x0, y0, PINK)
    n.mask(core, x0, y0, PINK_CORE)
    # brass hangers to the ceiling
    for hx in (bx0 + 14, bx1 - 14):
        c.vline(hx, WALL_TOP, by0 - 1, (110, 80, 36))
    return dict(rect=[x0, y0, x0 + w - 1, y0 + h - 1], light=[W // 2, y0 + h // 2]), bulbs


def jackpot_board(c: Canvas, e: Canvas):
    x0, y0, x1, y1 = 252, 60, 388, 116
    c.rect(x0 - 3, y0 - 3, x1 + 3, y1 + 3, INK)
    c.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, GOLD)
    c.hline(x0 - 2, x1 + 2, y0 - 2, GOLD_HI)
    c.hline(x0 - 2, x1 + 2, y1 + 2, GOLD_LO)
    c.vline(x1 + 2, y0 - 2, y1 + 2, GOLD_LO)
    c.rect(x0, y0, x1, y1, (10, 6, 10))
    for y in range(y0, y1 + 1, 2):
        for x in range(x0, x1 + 1, 2):
            c.px(x, y, (22, 14, 18))
    m = np.kron(render('JACKPOT', BIG), np.ones((1, 1), bool))
    tx = (x0 + x1) // 2 - m.shape[1] // 2
    e.mask(m, tx, y0 + 5, (255, 200, 80))
    for k in range(4):
        e.px(x0 + 4 + k * 3, y0 + 7, (255, 90, 60) if k % 2 else (255, 200, 80))
        e.px(x1 - 4 - k * 3, y0 + 7, (255, 90, 60) if k % 2 else (255, 200, 80))
    # coin pile painted under the board
    for (cx, cy) in [(x0 + 10, y1 + 8), (x1 - 10, y1 + 8)]:
        for j in range(4):
            c.ellipse(cx, cy - j * 2, 5, 2, INK)
            c.ellipse(cx, cy - j * 2, 4, 1, GOLD)
            c.px(cx - 2, cy - j * 2, GOLD_HI)
    return dict(rect=[x0, y0, x1, y1], digits=[x0 + 6, y0 + 22, x1 - x0 - 12], light=[(x0 + x1) // 2, (y0 + y1) // 2])


def sconce(c: Canvas, e: Canvas, x, y):
    c.rect(x - 2, y, x + 2, y + 10, GOLD_LO)
    c.vline(x - 2, y, y + 10, GOLD)
    c.poly([(x - 6, y - 6), (x + 6, y - 6), (x + 3, y + 1), (x - 3, y + 1)], (230, 200, 150))
    c.line(x - 6, y - 6, x - 3, y + 1, INK); c.line(x + 6, y - 6, x + 3, y + 1, INK)
    c.hline(x - 6, x + 6, y - 7, INK)
    e.rect(x - 3, y - 5, x + 3, y - 1, (255, 232, 190))
    e.hline(x - 1, x + 1, y - 6, (255, 250, 230))


def chandelier(c: Canvas, e: Canvas, cx):
    """Crystal chandelier with candle bulbs; returns the light anchor."""
    c.vline(cx, 0, 18, (110, 80, 36))
    c.vline(cx + 1, 0, 18, (70, 50, 22))
    c.ellipse(cx, 22, 4, 3, INK)
    c.ellipse(cx, 22, 3, 2, GOLD)
    # two tiers of curved arms
    for tier, (ry, rx, n) in enumerate(((30, 20, 5), (38, 30, 7))):
        c.ellipse(cx, ry, rx, 3, INK)
        c.ellipse(cx, ry, rx - 1, 2, GOLD_LO)
        c.hline(cx - rx + 2, cx + rx - 2, ry - 1, GOLD)
        for k in range(n):
            bx = cx - rx + 2 + round(k * (2 * rx - 4) / (n - 1))
            c.vline(bx, ry - 6, ry - 2, (236, 228, 210))
            c.px(bx, ry - 7, (180, 170, 150))
            e.px(bx, ry - 8, (255, 236, 180))
            e.px(bx, ry - 9, (255, 250, 230))
            # crystal drops
            for d in range(1, 4 + tier):
                c.px(bx, ry + 2 + d, (170, 210, 236) if d % 2 else (120, 160, 196))
    c.vline(cx, 22, 44, GOLD_LO)
    for d in range(4):
        c.px(cx, 45 + d, (190, 226, 250) if d % 2 else (130, 170, 210))
    e.px(cx, 46, (230, 246, 255))
    return [cx, 34]


def slot_machine(c: Canvas, e: Canvas, x, col, label):
    """A tall cabinet against the wall. Reels and marquee bulbs are animated at runtime."""
    top, base = 118, FLOOR_Y + 8
    hi, lo = sh(col, 1.35), sh(col, .62)
    w = 38
    c.rect(x, top, x + w, base, INK)
    # rounded marquee head
    c.rect(x + 1, top + 1, x + w - 1, top + 18, lo)
    c.rect(x + 3, top + 3, x + w - 3, top + 16, (26, 10, 18))
    c.hline(x + 2, x + w - 2, top + 1, hi)
    m = render(label, SMALL)
    e.mask(m, x + w // 2 - m.shape[1] // 2, top + 7, (255, 226, 140))
    marquee = [x + 3, top + 3, x + w - 3]
    # body
    c.rect(x + 1, top + 19, x + w - 1, base - 1, col)
    c.vline(x + 1, top + 19, base - 1, hi)
    c.vline(x + 2, top + 19, base - 1, sh(col, 1.15))
    c.vline(x + w - 1, top + 19, base - 1, lo)
    c.hline(x + 1, x + w - 1, top + 19, INK)
    # reel window with chrome bezel
    rx0, ry0, rx1, ry1 = x + 5, top + 24, x + w - 5, top + 44
    c.rect(rx0 - 2, ry0 - 2, rx1 + 2, ry1 + 2, (200, 200, 212))
    c.hline(rx0 - 2, rx1 + 2, ry0 - 2, (240, 240, 248))
    c.hline(rx0 - 2, rx1 + 2, ry1 + 2, (120, 120, 132))
    c.rect(rx0 - 1, ry0 - 1, rx1 + 1, ry1 + 1, INK)
    e.rect(rx0, ry0, rx1, ry1, (236, 232, 220))
    # pay table plate and buttons
    c.rect(x + 5, top + 50, x + w - 5, top + 60, (30, 12, 20))
    for k in range(3):
        c.rect(x + 7 + k * 9, top + 53, x + 11 + k * 9, top + 57, [(230, 60, 60), (60, 160, 230), (250, 200, 70)][k])
    c.rect(x + 4, top + 64, x + w - 4, top + 66, INK)
    c.hline(x + 5, x + w - 5, top + 65, (200, 200, 212))
    # coin tray
    c.rect(x + 8, top + 72, x + w - 8, top + 78, INK)
    c.rect(x + 9, top + 73, x + w - 9, top + 77, (150, 150, 162))
    c.hline(x + 9, x + w - 9, top + 73, (60, 60, 70))
    for k in range(3):
        c.px(x + 12 + k * 4, top + 76, GOLD_HI)
    # base plinth
    c.rect(x - 1, base - 6, x + w + 1, base, INK)
    c.rect(x, base - 5, x + w, base - 1, (44, 20, 26))
    c.hline(x, x + w, base - 5, GOLD_LO)
    # lever
    lx = x + w + 2
    c.rect(lx, top + 30, lx + 2, top + 38, (160, 160, 172))
    c.vline(lx + 1, top + 14, top + 30, (200, 200, 212))
    c.vline(lx + 2, top + 14, top + 30, (130, 130, 140))
    c.ellipse(lx + 1, top + 12, 3, 3, INK)
    c.ellipse(lx + 1, top + 12, 2, 2, (220, 40, 50))
    c.px(lx, top + 11, (255, 140, 140))
    return dict(reels=[rx0, ry0, rx1, ry1], marquee=marquee, light=[x + w // 2, top + 34], col=[v / 255 for v in hi])


def back_bar(c: Canvas, e: Canvas):
    """Mirror shelves with backlit bottles behind the bar."""
    x0, y0, x1, y1 = 448, 62, 632, FLOOR_Y - 8
    c.rect(x0 - 3, y0 - 3, x1 + 3, y1, INK)
    c.rect(x0 - 2, y0 - 2, x1 + 2, y1, WOOD)
    c.hline(x0 - 2, x1 + 2, y0 - 2, WOOD_HI)
    c.rect(x0, y0, x1, y1 - 2, (36, 30, 44))
    # mirror streaks
    for k in range(0, x1 - x0, 22):
        c.line(x0 + k, y1 - 3, x0 + k + 26, y0, (52, 46, 62))
    # BAR sign
    m = np.kron(render('BAR', BIG), np.ones((2, 2), bool))
    pad = np.pad(m, 1)
    edge = m & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    sx, sy = (x0 + x1) // 2 - m.shape[1] // 2, y0 + 5
    c.mask(m, sx, sy, (40, 70, 90))
    e.mask(edge, sx, sy, (80, 220, 255))
    e.mask(m & ~edge, sx, sy, (220, 250, 255))
    shelves = []
    palette = [(60, 150, 70), (170, 90, 40), (200, 190, 150), (120, 40, 60), (50, 90, 160), (200, 140, 40), (90, 160, 150)]
    for sy_ in (y0 + 44, y0 + 76, y0 + 108):
        c.rect(x0, sy_, x1, sy_ + 2, (200, 210, 224))
        c.hline(x0, x1, sy_, (240, 246, 255))
        c.hline(x0, x1, sy_ + 3, INK)
        e.hline(x0 + 1, x1 - 1, sy_ + 4, (110, 90, 255))
        shelves.append([x0, sy_ + 4, x1])
        bx = x0 + 3
        while bx < x1 - 8:
            col = palette[int(rng.integers(0, len(palette)))]
            kind = int(rng.integers(0, 3))
            bh = [22, 18, 14][kind]
            bw = [6, 7, 9][kind]
            bt = sy_ - bh
            c.rect(bx, bt + 6, bx + bw - 1, sy_ - 1, INK)
            c.rect(bx + 1, bt + 7, bx + bw - 2, sy_ - 1, col)
            c.vline(bx + 1, bt + 7, sy_ - 2, sh(col, 1.5))
            c.rect(bx + (bw // 2) - 1, bt, bx + (bw // 2), bt + 6, INK)
            c.px(bx + bw // 2 - 1, bt + 1, sh(col, 1.2))
            if kind < 2:
                c.rect(bx + 1, bt + 12, bx + bw - 2, bt + 15, (236, 226, 200))
            e.px(bx + 1, bt + 8, (255, 255, 255), 160)
            bx += bw + int(rng.integers(1, 4))
    return dict(rect=[x0, y0, x1, y1], shelves=shelves, light=[(x0 + x1) // 2, y0 + 70])


def bar_counter(c: Canvas, glow):
    x0, x1 = 440, W - 1
    top = BAR_TOP
    c.rect(x0, top - 3, x1, top + 3, INK)
    c.rect(x0 + 1, top - 2, x1, top + 2, WOOD_HI)
    c.hline(x0 + 1, x1, top - 2, (160, 96, 62))
    c.hline(x0 + 1, x1, top + 2, WOOD_LO)
    # tufted leather front
    c.rect(x0 + 2, top + 4, x1, top + 34, INK)
    glow.append([x0 + 3, top + 4, x1])
    c.rect(x0 + 3, top + 5, x1, top + 33, LEATHER)
    for y in range(top + 9, top + 32, 8):
        for x in range(x0 + 8 + ((y // 8) % 2) * 6, x1, 12):
            c.px(x, y, LEATHER_LO)
            c.px(x - 1, y - 1, LEATHER_HI)
            c.line(x, y, x + 6, y + 4, LEATHER_LO)
            c.px(x, y, GOLD_LO)
    c.hline(x0 + 3, x1, top + 5, LEATHER_HI)
    # brass foot rail
    c.hline(x0 + 2, x1, top + 30, GOLD)
    c.hline(x0 + 2, x1, top + 31, GOLD_LO)
    for x in range(x0 + 10, x1, 40):
        c.rect(x, top + 30, x + 1, top + 35, GOLD_LO)
    c.rect(x0 + 2, top + 34, x1, top + 36, INK)
    # drinks on the counter, one per seat
    glasses = []
    for gx, kind in ((502, 0), (562, 1), (622, 2)):
        if kind == 0:   # martini
            c.poly([(gx - 4, top - 10), (gx + 5, top - 10), (gx, top - 5)], (160, 230, 220))
            c.line(gx - 4, top - 10, gx, top - 5, INK); c.line(gx + 5, top - 10, gx, top - 5, INK)
            c.vline(gx, top - 5, top - 3, (220, 220, 232))
            c.hline(gx - 2, gx + 2, top - 3, (220, 220, 232))
            c.px(gx + 2, top - 12, (60, 140, 50)); c.px(gx + 2, top - 11, (200, 40, 40))
        elif kind == 1:  # whisky tumbler
            c.rect(gx - 3, top - 9, gx + 3, top - 3, INK)
            c.rect(gx - 2, top - 8, gx + 2, top - 4, (214, 150, 60))
            c.hline(gx - 2, gx + 2, top - 8, (240, 240, 248))
            c.px(gx - 1, top - 7, (250, 220, 160))
        else:            # pink cocktail with umbrella
            c.rect(gx - 2, top - 11, gx + 2, top - 3, INK)
            c.rect(gx - 1, top - 10, gx + 1, top - 4, (255, 120, 170))
            c.line(gx + 1, top - 11, gx + 4, top - 16, (230, 230, 230))
            c.poly([(gx + 1, top - 16), (gx + 8, top - 16), (gx + 4, top - 19)], (90, 200, 240))
        glasses.append([gx, top - 6])
    return glasses


# ---------------------------------------------------------------- seats
def sofa_back(c: Canvas, x0, x1):
    top, bot = 236, FRONT + 4
    c.rect(x0 + 6, top, x1 - 6, bot, INK)
    c.rect(x0 + 7, top + 1, x1 - 7, bot, TEAL)
    # rolled top edge
    c.rect(x0 + 5, top - 2, x1 - 5, top + 4, INK)
    c.rect(x0 + 6, top - 1, x1 - 6, top + 3, TEAL_HI)
    c.hline(x0 + 7, x1 - 7, top - 1, (90, 170, 176))
    # diamond tufting
    for row, y in enumerate(range(top + 9, bot - 2, 9)):
        for x in range(x0 + 14 + (row % 2) * 8, x1 - 10, 16):
            c.px(x, y, TEAL_LO)
            c.px(x, y - 1, (12, 44, 52))
            c.line(x, y, x - 8, y + 9, TEAL_LO)
            c.line(x, y, x + 8, y + 9, TEAL_LO)
            c.px(x - 1, y - 2, TEAL_HI)
    for y in range(top + 1, bot):
        for x in range(x0 + 7, x1 - 6):
            if dither(x, y, .25 * (y - top) / (bot - top)):
                c.px(x, y, TEAL_LO)


def sofa_front(c: Canvas, x0, x1):
    seat = FRONT + 2
    # cushion fronts
    n = 3
    cw = (x1 - x0 - 28) // n
    for k in range(n):
        cx0 = x0 + 14 + k * cw
        c.rect(cx0, seat, cx0 + cw, seat + 14, INK)
        c.rect(cx0 + 1, seat + 1, cx0 + cw - 1, seat + 13, TEAL)
        c.hline(cx0 + 1, cx0 + cw - 1, seat + 1, (90, 170, 176))
        c.hline(cx0 + 2, cx0 + cw - 2, seat + 2, TEAL_HI)
        c.hline(cx0 + 1, cx0 + cw - 1, seat + 13, TEAL_LO)
        c.vline(cx0 + cw - 1, seat + 2, seat + 12, TEAL_LO)
    # skirt with gold piping
    c.rect(x0 + 8, seat + 15, x1 - 8, seat + 26, INK)
    c.rect(x0 + 9, seat + 15, x1 - 9, seat + 25, TEAL_LO)
    c.hline(x0 + 9, x1 - 9, seat + 15, GOLD)
    for x in range(x0 + 12, x1 - 10, 4):
        c.vline(x, seat + 17, seat + 24, (16, 52, 60))
    # rolled arms
    for ax in (x0, x1 - 16):
        c.rect(ax, seat - 26, ax + 16, seat + 25, INK)
        c.rect(ax + 1, seat - 25, ax + 15, seat + 24, TEAL)
        c.ellipse(ax + 8, seat - 24, 8, 5, INK)
        c.ellipse(ax + 8, seat - 24, 7, 4, TEAL_HI)
        c.ellipse(ax + 8, seat - 24, 3, 2, TEAL)
        c.px(ax + 8, seat - 24, GOLD)
        c.vline(ax + 1, seat - 22, seat + 24, TEAL_HI)
        c.vline(ax + 15, seat - 22, seat + 24, TEAL_LO)
    # gold legs
    for lx in (x0 + 4, x1 - 6):
        c.rect(lx, seat + 26, lx + 2, seat + 31, INK)
        c.vline(lx + 1, seat + 26, seat + 30, GOLD)
    # a drink on the left arm
    gx, gy = x0 + 8, seat - 31
    c.rect(gx - 2, gy - 6, gx + 2, gy, INK)
    c.rect(gx - 1, gy - 5, gx + 1, gy - 1, (255, 170, 60))
    c.px(gx - 1, gy - 5, (255, 236, 200))


def table_chair_back(c: Canvas, cx):
    top, bot = 228, FRONT + 4
    c.rect(cx - 15, top + 4, cx + 15, bot, INK)
    c.ellipse(cx, top + 6, 15, 7, INK)
    c.ellipse(cx, top + 6, 14, 6, LEATHER)
    c.rect(cx - 14, top + 6, cx + 14, bot, LEATHER)
    c.ellipse(cx, top + 6, 10, 3, LEATHER_HI)
    c.vline(cx - 14, top + 6, bot, GOLD_LO)
    c.vline(cx + 14, top + 6, bot, GOLD_LO)
    for y in range(top + 12, bot - 2, 7):
        for x in (cx - 7, cx, cx + 7):
            c.px(x, y, LEATHER_LO)
            c.px(x, y - 1, GOLD_LO)


def card_table(c: Canvas, e: Canvas, x0, x1):
    rail = FRONT
    # padded rail
    c.rect(x0, rail, x1, rail + 7, INK)
    c.rect(x0 + 1, rail + 1, x1 - 1, rail + 6, (64, 34, 26))
    c.hline(x0 + 2, x1 - 2, rail + 1, (110, 64, 46))
    c.hline(x0 + 2, x1 - 2, rail + 2, (86, 48, 34))
    for x in range(x0 + 6, x1 - 4, 10):
        c.px(x, rail + 4, GOLD_LO)
    # felt
    c.rect(x0 + 1, rail + 7, x1 - 1, rail + 20, FELT)
    c.hline(x0 + 1, x1 - 1, rail + 7, FELT_LO)
    c.hline(x0 + 4, x1 - 4, rail + 19, FELT_HI)
    # betting layout lines in gold
    c.rect(x0 + 60, rail + 10, x1 - 60, rail + 18, GOLD_LO)
    c.rect(x0 + 61, rail + 11, x1 - 61, rail + 17, FELT)
    for x in range(x0 + 61, x1 - 60, 12):
        c.vline(x, rail + 11, rail + 17, GOLD_LO)
    for k, x in enumerate(range(x0 + 63, x1 - 62, 12)):
        c.rect(x, rail + 12, x + 8, rail + 16, (180, 30, 40) if k % 2 == 0 else (20, 20, 24))
    # chip stacks and cards
    for (cx, col, n) in [(x0 + 20, (230, 60, 60), 4), (x0 + 30, (60, 120, 230), 3), (x0 + 42, (40, 40, 44), 5),
                         (x1 - 22, GOLD, 5), (x1 - 34, (230, 60, 60), 3), (x1 - 44, (126, 226, 84), 2)]:
        for j in range(n):
            y = rail + 14 - j * 2
            c.ellipse(cx, y, 4, 1, INK)
            c.hline(cx - 3, cx + 3, y, col)
            c.px(cx - 2, y, (255, 255, 255))
    for k in range(2):
        c.rect(x0 + 52 + k * 5, rail + 9 + k, x0 + 57 + k * 5, rail + 15 + k, INK)
        c.rect(x0 + 53 + k * 5, rail + 10 + k, x0 + 56 + k * 5, rail + 14 + k, (240, 236, 226))
        c.px(x0 + 54 + k * 5, rail + 11 + k, (200, 40, 50))
    # apron and legs
    c.rect(x0 + 2, rail + 21, x1 - 2, rail + 34, INK)
    c.rect(x0 + 3, rail + 21, x1 - 3, rail + 33, WOOD)
    c.hline(x0 + 3, x1 - 3, rail + 21, GOLD)
    c.hline(x0 + 3, x1 - 3, rail + 22, GOLD_LO)
    for x in range(x0 + 10, x1 - 8, 28):
        c.rect(x, rail + 25, x + 18, rail + 31, WOOD_LO)
        c.hline(x, x + 18, rail + 31, WOOD_HI)
    c.hline(x0 + 3, x1 - 3, rail + 33, WOOD_DK)
    for lx in (x0 + 14, x1 - 18):
        c.rect(lx, rail + 34, lx + 4, rail + 44, INK)
        c.rect(lx + 1, rail + 34, lx + 3, rail + 43, WOOD_LO)
        c.rect(lx - 2, rail + 42, lx + 6, rail + 45, INK)
        c.hline(lx - 1, lx + 5, rail + 43, GOLD_LO)
    # roulette wheel bowl (the spinning wheel is drawn live)
    rc = [(x0 + x1) // 2, rail + 14]
    c.ellipse(rc[0], rc[1], 22, 8, INK)
    c.ellipse(rc[0], rc[1], 21, 7, WOOD_LO)
    c.ellipse(rc[0], rc[1] - 1, 20, 6, WOOD_HI)
    return dict(c=rc, rx=18, ry=5)


def wing_chair_back(c: Canvas, cx):
    top, bot = 226, FRONT + 4
    c.rect(cx - 18, top + 6, cx + 18, bot, INK)
    c.ellipse(cx, top + 8, 18, 9, INK)
    c.ellipse(cx, top + 8, 17, 8, EMER)
    c.rect(cx - 17, top + 8, cx + 17, bot, EMER)
    c.ellipse(cx, top + 6, 12, 4, EMER_HI)
    for y in range(top + 14, bot - 2, 8):
        for x in (cx - 9, cx, cx + 9):
            c.px(x, y, EMER_LO)
            c.px(x, y - 1, (110, 170, 120))
    # wings
    for wx, d in ((cx - 18, -1), (cx + 18, 1)):
        c.rect(min(wx, wx + d * 5), top + 16, max(wx, wx + d * 5), bot - 12, INK)
        c.rect(min(wx, wx + d * 4), top + 17, max(wx, wx + d * 4), bot - 13, EMER_LO)


def wing_chair_front(c: Canvas, cx):
    seat = FRONT + 2
    c.rect(cx - 16, seat, cx + 16, seat + 12, INK)
    c.rect(cx - 15, seat + 1, cx + 15, seat + 11, EMER)
    c.hline(cx - 15, cx + 15, seat + 1, EMER_HI)
    c.rect(cx - 18, seat + 12, cx + 18, seat + 24, INK)
    c.rect(cx - 17, seat + 12, cx + 17, seat + 23, EMER_LO)
    c.hline(cx - 17, cx + 17, seat + 12, GOLD_LO)
    for ax in (cx - 24, cx + 15):
        c.rect(ax, seat - 18, ax + 9, seat + 23, INK)
        c.rect(ax + 1, seat - 17, ax + 8, seat + 22, EMER)
        c.ellipse(ax + 4, seat - 17, 5, 3, INK)
        c.ellipse(ax + 4, seat - 17, 4, 2, EMER_HI)
        c.vline(ax + 1, seat - 15, seat + 22, EMER_HI)
    for lx in (cx - 22, cx + 19):
        c.rect(lx, seat + 24, lx + 2, seat + 29, INK)
        c.vline(lx + 1, seat + 24, seat + 28, WOOD_HI)


def side_table(c: Canvas, e: Canvas, cx):
    top = FRONT + 6
    c.ellipse(cx, top, 10, 3, INK)
    c.ellipse(cx, top, 9, 2, WOOD_HI)
    c.rect(cx - 1, top + 2, cx + 1, top + 26, WOOD_LO)
    c.rect(cx - 6, top + 25, cx + 6, top + 27, INK)
    # small table lamp
    c.rect(cx - 1, top - 10, cx, top - 2, GOLD_LO)
    c.poly([(cx - 6, top - 18), (cx + 6, top - 18), (cx + 4, top - 10), (cx - 4, top - 10)], (230, 196, 140))
    c.line(cx - 6, top - 18, cx - 4, top - 10, INK); c.line(cx + 6, top - 18, cx + 4, top - 10, INK)
    c.hline(cx - 6, cx + 6, top - 19, INK)
    e.hline(cx - 3, cx + 3, top - 9, (255, 226, 170))
    return [cx, top - 12]


def front_clutter(c: Canvas):
    for (x, y, col) in [(200, 340, (230, 60, 60)), (206, 343, GOLD), (452, 338, (60, 120, 230)), (618, 346, (40, 40, 44)),
                        (34, 348, GOLD), (300, 352, (126, 226, 84))]:
        c.ellipse(x, y, 3, 1, INK)
        c.hline(x - 2, x + 2, y, col)
        c.px(x - 1, y, (255, 255, 255))
    # a dropped ace
    c.rect(470, 344, 476, 352, INK)
    c.rect(471, 345, 475, 351, (240, 236, 226))
    c.px(473, 348, (200, 40, 50))
    # confetti
    conf = [(255, 90, 160), (255, 214, 90), (90, 200, 255), (126, 226, 84)]
    for _ in range(40):
        x, y = int(rng.integers(4, W - 4)), int(rng.integers(326, 356))
        c.px(x, y, conf[int(rng.integers(0, 4))])


# ---------------------------------------------------------------- build
def build():
    OUT.mkdir(parents=True, exist_ok=True)
    bg, e, neon = Canvas(W, H), Canvas(W, H), Canvas(W, H)
    bar, chairs, front = Canvas(W, H), Canvas(W, H), Canvas(W, H)
    lay: dict = {'size': [W, H]}

    ceiling(bg)
    wallpaper(bg)
    wainscot(bg)
    carpet(bg)
    for x in (226, 414):
        pilaster(bg, x)
    lay['neon'], lay['bulbs'] = neon_sign(bg, neon, e)
    lay['jackpot'] = jackpot_board(bg, e)
    for sx in (240, 400):
        sconce(bg, e, sx, 138)
    slots = []
    for k, (x, col, label) in enumerate([(10, (170, 30, 50), '777'), (58, (40, 70, 170), 'BAR'),
                                         (106, (140, 40, 150), 'WIN'), (154, (30, 120, 96), '$$$')]):
        slots.append(slot_machine(bg, e, x, col, label))
    lay['slots'] = slots
    lay['backbar'] = back_bar(bg, e)
    lamps = [chandelier(bg, e, 120), chandelier(bg, e, 520)]
    lay['lamps'] = lamps

    # seats, in the order frogs fill them
    seats = []
    tx0, tx1 = 214, 426
    for cx in (262, 320, 378):
        table_chair_back(chairs, cx)
        seats.append(dict(kind='table', x=cx - 36, frog=[cx, FRONT], clip=FRONT + 2))
    lay['roulette'] = card_table(front, e, tx0, tx1)
    glow = []
    glasses = bar_counter(bar, glow)
    lay['strips'] = [[g[0], g[1] - 1, g[2]] for g in glow]
    for cx in (500, 560, 620):
        seats.append(dict(kind='bar', x=cx - 36, frog=[cx, BAR_TOP], clip=BAR_TOP - 1))
    sofa_back(chairs, 14, 192)
    for cx in (56, 103, 150):
        seats.append(dict(kind='sofa', x=cx - 36, frog=[cx, FRONT + 4], clip=FRONT + 3))
    sofa_front(front, 14, 192)
    lamp2 = side_table(front, e, 568)
    for cx in (532, 604):
        wing_chair_back(chairs, cx)
        wing_chair_front(front, cx)
        seats.append(dict(kind='armchair', x=cx - 36, frog=[cx, FRONT + 4], clip=FRONT + 3))
    front_clutter(front)
    for s in seats:
        s.update(screen=None, screen2=None, steam=[], lamps=[])
    lay['desks'] = seats

    L_ = lay
    lights = [dict(x=x, y=y, r=210, col=[1.0, 0.8, 0.55], i=1.0, cone=True, kind='lamp') for x, y in lamps]
    lights += [
        dict(id='neon', x=L_['neon']['light'][0], y=L_['neon']['light'][1] + 8, r=170, col=[1.0, 0.3, 0.65], i=0.8),
        dict(x=L_['jackpot']['light'][0], y=L_['jackpot']['light'][1], r=96, col=[1.0, 0.75, 0.3], i=0.5),
        dict(x=L_['backbar']['light'][0], y=L_['backbar']['light'][1], r=130, col=[0.45, 0.5, 1.0], i=0.6),
        dict(x=320, y=150, r=170, col=[1.0, 0.9, 0.7], i=0.75, cone=True),
        dict(x=lamp2[0], y=lamp2[1], r=70, col=[1.0, 0.8, 0.5], i=0.8),
        dict(x=540, y=176, r=130, col=[1.0, 0.72, 0.5], i=0.7),
        dict(x=104, y=236, r=120, col=[0.8, 0.7, 1.0], i=0.45),
        dict(x=320, y=300, r=110, col=[0.9, 1.0, 0.8], i=0.35),
        dict(x=240, y=134, r=46, col=[1.0, 0.85, 0.6], i=0.5),
        dict(x=400, y=134, r=46, col=[1.0, 0.85, 0.6], i=0.5),
    ]
    for s in slots:
        lights.append(dict(x=s['light'][0], y=s['light'][1], r=52, col=s['col'], i=0.6))
    lay['lights'] = lights
    lay['theme'] = dict(ambient=[0.36, 0.28, 0.38], screen='none', screenLight=[1, 1, 1], tv='none', rain=False,
                        cones=[255, 210, 160], coneEnd=300, coneAlpha=0.08, coins=['$FROG'], neonHalo=[255, 90, 170])
    for name, cv in [('bg', bg), ('emissive', e), ('neon', neon), ('bossdesk', bar), ('chairs', chairs), ('desks', front)]:
        cv.save(OUT / f'{name}.png')
    (OUT / 'layout.json').write_text(json.dumps(lay))
    return lay


if __name__ == '__main__':
    build()
    print('casino ok')
