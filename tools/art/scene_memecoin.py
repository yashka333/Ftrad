"""Memecoin Trading office: a full lit pixel-art room built as separate layers.

Layers (back to front), all 640x360 native:
  bg        room shell, wall objects, boss chair, floor clutter behind desks
  bossdesk  boss desk and its props (in front of the boss frog)
  chairs    worker chairs (behind worker frogs)
  desks     worker desks, props, monitors, front clutter (in front of frogs)
  emissive  self-lit pixels that ignore room lighting (window city, bulbs, signs)
  neon      lit neon letters (toggled by the flicker)
Frogs, screens, ticker, rain, clock hands, steam and smoke are drawn live in JS.
layout.json carries every anchor the runtime needs.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from font import BIG, SMALL, render
from px2 import INK, Canvas, dither, mix, rgb, sh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'client/src/assets/office/memecoin'
W, H = 640, 360
WALL_TOP, FLOOR_Y = 22, 200
rng = np.random.default_rng(42)

C = {
    'ceil': (66, 62, 72), 'ceil_lo': (50, 47, 56), 'ceil_hi': (80, 76, 86),
    'pipe': (118, 122, 130), 'pipe_hi': (160, 164, 170), 'pipe_lo': (80, 82, 92),
    'rust': (140, 78, 46),
    'mortar': (88, 80, 78), 'plaster': (152, 144, 130), 'plaster_lo': (124, 116, 104),
    'plaster_hi': (172, 164, 148), 'crack': (96, 88, 80),
    'base': (58, 40, 30), 'base_hi': (84, 60, 44),
    'wood': [(124, 86, 58), (116, 80, 54), (132, 92, 62), (110, 76, 52), (128, 88, 60)],
    'metal': (80, 82, 94), 'metal_hi': (116, 118, 132), 'metal_lo': (54, 56, 66),
    'orange': (232, 108, 46), 'orange_hi': (255, 150, 80), 'orange_lo': (170, 70, 34),
    'paper': (226, 220, 204), 'paper_lo': (190, 184, 168),
    'cork': (170, 124, 78), 'cork_lo': (140, 98, 58), 'cork_hi': (192, 146, 98),
    'green': (92, 222, 112), 'red': (232, 82, 82),
}
BRICKS = [(148, 80, 60), (138, 74, 56), (158, 90, 68), (128, 68, 52), (144, 86, 66), (120, 66, 52)]


# ---------------------------------------------------------------- room shell
def ceiling(c: Canvas):
    c.rect(0, 0, W - 1, WALL_TOP - 1, C['ceil'])
    for x in range(0, W, 80):
        c.vline(x, 0, WALL_TOP - 1, C['ceil_lo'])
        c.vline(x + 1, 0, WALL_TOP - 1, C['ceil_hi'])
    for _ in range(260):
        c.px(rng.integers(0, W), rng.integers(0, WALL_TOP), C['ceil_lo'])
    # shadow line where ceiling meets wall
    c.hline(0, W - 1, WALL_TOP - 1, INK)
    c.hline(0, W - 1, WALL_TOP - 2, C['ceil_lo'])
    # main pipe
    py = 6
    c.rect(0, py, W - 1, py + 6, INK)
    c.rect(0, py + 1, W - 1, py + 5, C['pipe'])
    c.hline(0, W - 1, py + 1, C['pipe_hi'])
    c.hline(0, W - 1, py + 2, mix(C['pipe'], C['pipe_hi'], .5))
    c.hline(0, W - 1, py + 5, C['pipe_lo'])
    for fx in range(46, W, 96):
        c.box(fx, py - 1, fx + 4, py + 7, C['pipe_lo'], C['pipe'], INK)
        c.px(fx + 2, py + 1, C['pipe_hi'])
        c.px(fx + 2, py + 5, C['pipe_hi'])
        # rust drips under joints
        for k in range(int(rng.integers(1, 4))):
            c.px(fx + 1 + k, py + 8 + k % 2, C['rust'], 150)
    # red valve wheel
    vx = 236
    c.vline(vx, py - 4, py, INK)
    c.ellipse(vx, py - 5, 4, 2, (170, 40, 40))
    c.hline(vx - 3, vx + 3, py - 5, (210, 70, 60))
    # thin conduit with sagging cables
    c.hline(0, W - 1, 17, C['metal_lo'])
    c.hline(0, W - 1, 18, C['metal'])
    for x0 in range(10, W - 60, 140):
        span = int(rng.integers(50, 90))
        sag = int(rng.integers(3, 6))
        for x in range(x0, x0 + span):
            t = (x - x0) / span
            y = 18 + int(sag * math.sin(math.pi * t))
            c.px(x, y + 1, (30, 28, 34))


def brick_wall(c: Canvas):
    top, bot = WALL_TOP, FLOOR_Y - 7
    c.rect(0, top, W - 1, bot, C['mortar'])
    bh, bw = 6, 14
    for row, y in enumerate(range(top, bot, bh)):
        off = (bw // 2) * (row % 2)
        for x in range(-off, W, bw):
            col = BRICKS[int(rng.integers(0, len(BRICKS)))]
            x0, x1 = max(0, x), min(W - 1, x + bw - 2)
            y0, y1 = y, min(bot, y + bh - 2)
            if x1 < x0:
                continue
            c.rect(x0, y0, x1, y1, col)
            c.hline(x0, x1, y0, sh(col, 1.12))
            c.hline(x0, x1, y1, sh(col, .82))
            # texture specks and chipped corners
            for _ in range(int(rng.integers(0, 4))):
                c.px(rng.integers(x0, x1 + 1), rng.integers(y0, y1 + 1), sh(col, rng.choice([.86, 1.1])))
            if rng.random() < .18:
                c.px(x1, y1, C['mortar'])
            if rng.random() < .08:
                c.rect(x0 + 2, y0 + 1, x0 + 5, y0 + 2, sh(col, .7))
    # plaster patches clinging to the brick
    # soot and damp patches darken the brick instead of floating on it
    for (cx, cy, rx, ry) in [(176, 30, 30, 8), (452, 182, 40, 9), (612, 36, 24, 10), (60, 180, 26, 8)]:
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d < 1 and top <= y <= bot and dither(x, y, .55 * (1 - d)):
                    c.px(x, y, (40, 30, 30), 120)
    # a few missing bricks showing the darker layer behind
    for (bx, by) in [(70, 160), (250, 40), (420, 186), (560, 30), (150, 176)]:
        c.rect(bx, by, bx + 12, by + 4, (66, 46, 40))
        c.hline(bx, bx + 12, by, (44, 30, 28))
        c.vline(bx, by, by + 4, (44, 30, 28))
    # water stain running down from a pipe joint
    for y in range(top, top + 70):
        w = 3 + int(2 * math.sin(y * .3))
        for x in range(526 - w, 526 + w):
            if dither(x, y, .35 * (1 - (y - top) / 70)):
                c.px(x, y, (60, 56, 50), 90)
    # baseboard
    c.rect(0, bot + 1, W - 1, FLOOR_Y - 1, C['base'])
    c.hline(0, W - 1, bot + 1, C['base_hi'])
    c.hline(0, W - 1, FLOOR_Y - 1, INK)


def plaster_patch(c: Canvas, cx, cy, rx, ry, top, bot):
    pts = []
    for k in range(28):
        a = 2 * math.pi * k / 28
        r = 1 + .28 * math.sin(3 * a + rx) + .16 * math.sin(7 * a + ry)
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    m = np.zeros((H, W), bool)
    tmp = Canvas(W, H)
    tmp.poly(pts, (255, 255, 255))
    m = tmp.a[..., 3] > 0
    m[:top] = False
    m[bot + 1:] = False
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        v = C['plaster']
        n = rng.random()
        if n < .08:
            v = C['plaster_lo']
        elif n > .94:
            v = C['plaster_hi']
        c.px(x, y, v)
    # lit top edge, shadowed bottom edge (patch sits on top of brick)
    pad = np.pad(m, 1)
    top_edge = m & ~pad[:-2, 1:-1]
    bot_edge = m & ~pad[2:, 1:-1]
    right_edge = m & ~pad[1:-1, 2:]
    for y, x in zip(*np.nonzero(top_edge)):
        c.px(x, y, C['plaster_hi'])
    for y, x in zip(*np.nonzero(bot_edge | right_edge)):
        c.px(x, y, C['plaster_lo'])
        if y + 1 <= bot:
            c.px(x, y + 1, (60, 46, 40), 140)
    # cracks
    for _ in range(2):
        x, y = cx + rng.integers(-rx // 2, rx // 2 + 1), cy + rng.integers(-ry // 2, ry // 2 + 1)
        for _ in range(int(rng.integers(8, 18))):
            if 0 <= y < H and 0 <= x < W and m[y, x]:
                c.px(x, y, C['crack'])
            x += int(rng.choice([-1, 0, 1, 1]))
            y += int(rng.choice([0, 1, 1]))


def floor(c: Canvas):
    y = FLOOR_Y
    k = 0
    while y < H:
        h = 3 + int(7 * ((y - FLOOR_Y) / (H - FLOOR_Y)) ** 1.1)
        y1 = min(H - 1, y + h - 1)
        x = -int(rng.integers(0, 60))
        while x < W:
            ln = int(rng.integers(70, 150))
            col = C['wood'][int(rng.integers(0, len(C['wood'])))]
            x0, x1 = max(0, x), min(W - 1, x + ln - 1)
            c.rect(x0, y, x1, y1, col)
            c.hline(x0, x1, y, sh(col, 1.1))
            # grain streaks
            for _ in range(max(1, ln // 18)):
                gx, gy = int(rng.integers(x0, x1 + 1)), int(rng.integers(y, y1 + 1))
                c.hline(gx, min(x1, gx + int(rng.integers(4, 14))), gy, sh(col, .9))
            # knots
            if rng.random() < .25 and h >= 5:
                kx = int(rng.integers(x0 + 3, max(x0 + 4, x1 - 3)))
                c.ellipse(kx, (y + y1) // 2, 2, 1, sh(col, .72))
            # end joint
            if x1 < W - 1:
                c.vline(x1, y, y1, (52, 36, 26))
            x += ln
        c.hline(0, W - 1, y1, (60, 42, 30))
        y = y1 + 1
        k += 1
    # dark gaps right under the baseboard (contact shadow)
    for yy in range(FLOOR_Y, FLOOR_Y + 8):
        for x in range(W):
            if dither(x, yy, .7 * (1 - (yy - FLOOR_Y) / 8)):
                c.px(x, yy, (30, 22, 18), 150)
    # scuffs and stains
    for _ in range(26):
        sx, sy = int(rng.integers(0, W)), int(rng.integers(FLOOR_Y + 6, H))
        r = int(rng.integers(3, 10))
        for yy in range(sy - r // 3, sy + r // 3 + 1):
            for xx in range(sx - r, sx + r + 1):
                if ((xx - sx) / r) ** 2 + ((yy - sy) / max(1, r / 3)) ** 2 < 1 and dither(xx, yy, .45):
                    c.px(xx, yy, (70, 48, 34), 110)


# --------------------------------------------------------------- wall pieces
def window(c: Canvas, e: Canvas):
    x0, y0, x1, y1 = 30, 48, 150, 146
    # outside scene goes to the emissive layer (not lit by the room)
    sky0, sky1 = (22, 20, 46), (64, 38, 82)
    for y in range(y0 + 3, y1 - 2):
        t = (y - y0) / (y1 - y0)
        col = mix(sky0, sky1, t)
        for x in range(x0 + 3, x1 - 2):
            e.px(x, y, col if not dither(x, y, (t * 6) % 1 * .5) else mix(col, sky1, .15))
    for _ in range(18):
        e.px(rng.integers(x0 + 4, x1 - 3), rng.integers(y0 + 4, y0 + 40), (200, 200, 230))
    # moon
    e.ellipse(x0 + 28, y0 + 18, 6, 6, (232, 226, 200))
    e.ellipse(x0 + 30, y0 + 16, 5, 5, mix(sky0, sky1, .2))
    # far skyline
    bx = x0 + 3
    while bx < x1 - 3:
        bw, bh = int(rng.integers(8, 18)), int(rng.integers(26, 60))
        top = y1 - 3 - bh
        e.rect(bx, top, min(x1 - 3, bx + bw - 1), y1 - 3, (38, 32, 64))
        for wy in range(top + 3, y1 - 5, 4):
            for wx in range(bx + 2, min(x1 - 4, bx + bw - 2), 3):
                if rng.random() < .35:
                    e.px(wx, wy, [(250, 210, 120), (255, 170, 80), (120, 230, 220)][int(rng.integers(0, 3))])
        bx += bw + int(rng.integers(0, 3))
    # near tower with a pink neon $ sign
    e.rect(x1 - 30, y0 + 30, x1 - 3, y1 - 3, (24, 20, 40))
    sym = render('$', SMALL)
    e.mask(sym, x1 - 19, y0 + 36, (255, 80, 170))
    for wy in range(y0 + 46, y1 - 6, 5):
        for wx in range(x1 - 27, x1 - 5, 4):
            if rng.random() < .3:
                e.px(wx, wy, (255, 200, 110))
    # frame and mullions in the lit layer
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 2, C['metal'])
    c.rect(x0 + 1, y1 - 2, x1 - 1, y1 - 1, C['metal_lo'])
    c.rect(x0 + 1, y0 + 1, x0 + 2, y1 - 1, C['metal'])
    c.rect(x1 - 2, y0 + 1, x1 - 1, y1 - 1, C['metal_lo'])
    c.hline(x0 + 1, x1 - 1, y0 + 1, C['metal_hi'])
    mx, my = (x0 + x1) // 2, (y0 + y1) // 2
    c.rect(mx - 1, y0, mx + 1, y1, INK)
    c.vline(mx, y0 + 1, y1 - 1, C['metal'])
    c.rect(x0, my - 1, x1, my + 1, INK)
    c.hline(x0 + 1, x1 - 1, my, C['metal'])
    # transparent hole for the outside (bg layer must not cover it)
    for y in range(y0 + 3, y1 - 2):
        for x in range(x0 + 3, x1 - 2):
            if c.a[y, x, 0] != INK[0] or c.a[y, x, 1] != INK[1]:
                if not (mx - 1 <= x <= mx + 1 or my - 1 <= y <= my + 1):
                    c.a[y, x, 3] = 0
    # sill with a dead cactus and a stack of books
    c.box(x0 - 6, y1 + 1, x1 + 6, y1 + 5, (150, 146, 138), (178, 174, 166), (112, 108, 102))
    pot_x = x0 + 8
    c.box(pot_x, y1 - 7, pot_x + 9, y1 + 1, (176, 92, 56), (204, 118, 74), (130, 64, 40))
    c.box(pot_x + 3, y1 - 17, pot_x + 6, y1 - 7, (110, 116, 64), (138, 144, 80), (80, 84, 46))
    c.box(pot_x, y1 - 14, pot_x + 3, y1 - 11, (110, 116, 64), None, (80, 84, 46))
    c.px(pot_x + 5, y1 - 18, (200, 170, 90))
    bx = x1 - 34
    for k, col in enumerate([(60, 90, 140), (150, 60, 50), (80, 120, 70)]):
        c.box(bx + k, y1 - 4 - 4 * k, bx + 26 - 2 * k, y1 - 1 - 4 * k, col, sh(col, 1.25), sh(col, .7))
        c.hline(bx + k + 2, bx + 24 - 2 * k, y1 - 3 - 4 * k, (230, 222, 200))
    return dict(rect=[x0 + 3, y0 + 3, x1 - 3, y1 - 3], light=[(x0 + x1) // 2, (y0 + y1) // 2])


def neon_sign(c: Canvas, n: Canvas):
    text = 'MEMECOIN TRADING'
    m = render(text, BIG)
    m = np.kron(m, np.ones((2, 2), bool))
    h, w = m.shape
    x0, y0 = W // 2 - w // 2, 27
    # mounting rail and brackets
    c.rect(x0 - 6, y0 + h // 2 - 1, x0 + w + 5, y0 + h // 2 + 1, C['metal_lo'])
    for bx in (x0 - 4, x0 + w // 2, x0 + w + 2):
        c.box(bx - 1, y0 + h // 2 - 3, bx + 2, y0 + h // 2 + 3, C['metal'], C['metal_hi'], C['metal_lo'])
    # tube outline: edge pixels of the stroke mask; core: inside
    pad = np.pad(m, 1)
    edge = m & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    core = m & ~edge
    c.mask(m, x0, y0, (78, 44, 36))          # dead glass when off
    c.mask(core, x0, y0, (104, 60, 46))
    # dark backplate shadow under the tubes
    sh_m = np.zeros_like(m)
    sh_m[1:, 1:] = m[:-1, :-1]
    c.mask(sh_m & ~m, x0, y0, (40, 26, 24), 160)
    n.mask(edge, x0, y0, C['orange'])
    n.mask(core, x0, y0, (255, 214, 160))
    return dict(rect=[x0, y0, x0 + w - 1, y0 + h - 1], light=[W // 2, y0 + h // 2])


def boss_tv(c: Canvas):
    x0, y0, x1, y1 = 262, 50, 378, 118
    # wall mount
    c.box((x0 + x1) // 2 - 12, y0 - 4, (x0 + x1) // 2 + 12, y0, C['metal'], C['metal_hi'], C['metal_lo'])
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, (34, 34, 40))
    c.hline(x0 + 1, x1 - 1, y0 + 1, (60, 60, 68))
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 6, INK)
    # brand strip
    c.hline((x0 + x1) // 2 - 4, (x0 + x1) // 2 + 4, y1 - 3, (90, 90, 100))
    return dict(screen=[x0 + 4, y0 + 4, x1 - 4, y1 - 7], light=[(x0 + x1) // 2, (y0 + y1) // 2])


def ticker_board(c: Canvas):
    x0, y0, x1, y1 = 430, 50, 614, 72
    for bx in (x0 + 20, x1 - 20):
        c.vline(bx, WALL_TOP, y0, (40, 38, 44))
    c.box(x0, y0, x1, y1, (40, 40, 48), (64, 64, 74), (28, 28, 34))
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, (14, 10, 10))
    for x in range(x0 + 4, x1 - 3, 2):  # dead LED grid
        for y in range(y0 + 4, y1 - 3, 2):
            c.px(x, y, (40, 24, 18))
    return dict(rect=[x0 + 4, y0 + 4, x1 - 4, y1 - 4], light=[(x0 + x1) // 2, (y0 + y1) // 2])


def poster(c: Canvas, x, y, w, h, bg, draw, label, label_col=INK):
    c.box(x, y, x + w - 1, y + h - 1, bg, sh(bg, 1.12), sh(bg, .82))
    draw(c, x, y, w, h)
    if label:
        lm = render(label, SMALL)
        c.mask(lm, x + w // 2 - lm.shape[1] // 2, y + h - 8, label_col)
    # tape corners
    for tx, ty in ((x - 1, y - 1), (x + w - 4, y - 1)):
        c.rect(tx, ty, tx + 4, ty + 2, (230, 222, 170), 200)


def dog_face(c, x, y, w, h):
    cx, cy = x + w // 2, y + 12
    fur, fur_lo, cream = (226, 156, 70), (186, 116, 46), (246, 226, 190)
    c.poly([(cx - 9, cy - 4), (cx - 7, cy - 11), (cx - 3, cy - 6)], fur_lo)
    c.poly([(cx + 9, cy - 4), (cx + 7, cy - 11), (cx + 3, cy - 6)], fur_lo)
    c.ellipse(cx, cy, 9, 7, fur)
    c.ellipse(cx, cy + 3, 5, 3, cream)
    c.px(cx - 4, cy - 2, INK); c.px(cx + 3, cy - 2, INK)
    c.rect(cx - 1, cy + 1, cx, cy + 2, INK)


def frog_face(c, x, y, w, h):
    cx, cy = x + w // 2, y + 13
    g, g_lo, belly = (110, 160, 80), (80, 120, 56), (210, 196, 150)
    c.ellipse(cx - 5, cy - 6, 4, 3, g); c.ellipse(cx + 5, cy - 6, 4, 3, g)
    c.ellipse(cx, cy, 10, 6, g)
    c.ellipse(cx, cy + 2, 7, 3, belly)
    c.ellipse(cx - 5, cy - 6, 2, 2, (240, 236, 220)); c.ellipse(cx + 5, cy - 6, 2, 2, (240, 236, 220))
    c.px(cx - 4, cy - 6, INK); c.px(cx + 6, cy - 6, INK)
    c.hline(cx - 4, cx + 4, cy, g_lo)


def cat_face(c, x, y, w, h):
    cx, cy = x + w // 2, y + 13
    fur, dark = (150, 150, 160), (100, 100, 112)
    c.poly([(cx - 9, cy - 3), (cx - 8, cy - 11), (cx - 3, cy - 6)], fur)
    c.poly([(cx + 9, cy - 3), (cx + 8, cy - 11), (cx + 3, cy - 6)], fur)
    c.ellipse(cx, cy, 9, 7, fur)
    c.rect(cx - 8, cy - 3, cx + 7, cy - 1, INK)  # shades
    c.hline(cx - 7, cx - 2, cy - 3, (80, 80, 120))
    c.hline(cx + 2, cx + 6, cy - 3, (80, 80, 120))
    c.px(cx, cy + 2, (230, 120, 140))
    c.hline(cx - 2, cx + 2, cy + 4, dark)


def rocket(c, x, y, w, h):
    cx, cy = x + w // 2, y + 12
    c.poly([(cx, cy - 10), (cx + 4, cy - 2), (cx + 4, cy + 6), (cx - 4, cy + 6), (cx - 4, cy - 2)], (220, 220, 230))
    c.ellipse(cx, cy - 1, 2, 2, (80, 160, 230))
    c.poly([(cx - 4, cy + 2), (cx - 8, cy + 8), (cx - 4, cy + 6)], (220, 70, 60))
    c.poly([(cx + 4, cy + 2), (cx + 8, cy + 8), (cx + 4, cy + 6)], (220, 70, 60))
    for k in range(4):
        c.px(cx - 1 + k % 2, cy + 7 + k, (255, 180, 60))
    c.px(cx, cy + 9, (255, 230, 120))


def chart_up(c, x, y, w, h):
    pts = [(x + 4, y + 20), (x + 9, y + 16), (x + 13, y + 18), (x + 18, y + 9), (x + 23, y + 4)]
    for (a, b), (p, q) in zip(pts, pts[1:]):
        c.line(a, b, p, q, (40, 160, 70))
        c.line(a, b + 1, p, q + 1, (40, 160, 70))
    c.poly([(x + 20, y + 3), (x + 25, y + 3), (x + 25, y + 8)], (40, 160, 70))


def corkboard(c: Canvas):
    x0, y0, x1, y1 = 432, 82, 584, 150
    c.box(x0, y0, x1, y1, (110, 72, 42), (140, 96, 60), (80, 50, 30))
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, C['cork'])
    for _ in range(420):
        c.px(rng.integers(x0 + 3, x1 - 2), rng.integers(y0 + 3, y1 - 2),
             C['cork_lo'] if rng.random() < .6 else C['cork_hi'])
    poster(c, x0 + 6, y0 + 6, 28, 34, (250, 214, 110), dog_face, '$WOOF')
    poster(c, x0 + 38, y0 + 10, 28, 34, (176, 222, 150), frog_face, '$FROG')
    poster(c, x0 + 70, y0 + 5, 28, 34, (200, 180, 230), cat_face, '$MEOW')
    poster(c, x0 + 102, y0 + 9, 26, 34, (40, 44, 70), rocket, 'MOON', (240, 230, 200))
    poster(c, x0 + 6, y0 + 43, 30, 24, (240, 240, 232), chart_up, '', INK)
    # sticky notes and pins
    for (nx, ny, col, txt) in [(x0 + 132, y0 + 8, (246, 212, 76), 'HODL'), (x0 + 42, y0 + 48, (250, 150, 190), 'WAGMI'),
                               (x0 + 78, y0 + 44, (140, 220, 240), '100X'), (x0 + 110, y0 + 46, (246, 212, 76), 'NGMI')]:
        tw = render(txt, SMALL).shape[1]
        c.box(nx, ny, nx + max(14, tw + 3), ny + 12, col, sh(col, 1.1), sh(col, .85))
        c.mask(render(txt, SMALL), nx + 2, ny + 4, (50, 40, 40))
    for (px_, py_) in [(x0 + 20, y0 + 7), (x0 + 52, y0 + 11), (x0 + 84, y0 + 6), (x0 + 115, y0 + 10)]:
        c.px(px_, py_, (220, 50, 50)); c.px(px_, py_ + 1, (120, 20, 20))


def rug_counter(c: Canvas):
    """'DAYS SINCE LAST RUG: 0' whiteboard."""
    x0, y0, x1, y1 = 166, 96, 238, 132
    c.box(x0, y0, x1, y1, (232, 232, 226), (250, 250, 246), (196, 196, 190))
    c.rect(x0 - 1, y0 - 1, x1 + 1, y0 - 1, (90, 92, 104))
    for i, line in enumerate(['DAYS SINCE', 'LAST RUG']):
        m = render(line, SMALL)
        c.mask(m, (x0 + x1) // 2 - m.shape[1] // 2, y0 + 4 + 7 * i, (60, 60, 70))
    zero = np.kron(render('0', BIG), np.ones((2, 1), bool))
    c.mask(zero, (x0 + x1) // 2 - zero.shape[1] // 2, y0 + 19, (210, 50, 50))
    # marker tray
    c.rect(x0 + 6, y1 + 1, x1 - 6, y1 + 2, (150, 150, 160))
    c.rect(x0 + 12, y1, x0 + 20, y1, (40, 90, 200))
    c.rect(x0 + 24, y1, x0 + 31, y1, (200, 40, 40))


def wall_clock(c: Canvas):
    cx, cy = 202, 70
    c.ellipse(cx, cy, 11, 11, INK)
    c.ellipse(cx, cy, 10, 10, (190, 60, 50))
    c.ellipse(cx, cy, 8, 8, (240, 236, 224))
    for k in range(12):
        a = 2 * math.pi * k / 12
        c.px(cx + round(math.sin(a) * 7), cy - round(math.cos(a) * 7), (90, 90, 96))
    return dict(center=[cx, cy])


def door(c: Canvas, e: Canvas):
    x0, y0, x1, y1 = 594, 104, 634, FLOOR_Y + 2
    c.rect(x0 - 3, y0 - 3, x1 + 3, y1, INK)
    c.rect(x0 - 2, y0 - 2, x1 + 2, y1, (72, 50, 36))
    c.hline(x0 - 2, x1 + 2, y0 - 2, (98, 70, 50))
    c.box(x0, y0, x1, y1, (84, 98, 92), (108, 124, 118), (62, 74, 70))
    # door window (hallway light, self-lit)
    c.rect(x0 + 10, y0 + 8, x1 - 10, y0 + 30, INK)
    for y in range(y0 + 9, y0 + 30):
        for x in range(x0 + 11, x1 - 10):
            e.px(x, y, mix((250, 228, 170), (200, 170, 120), (y - y0 - 9) / 21))
    c.rect(x0 + 11, y0 + 9, x1 - 11, y0 + 29, (0, 0, 0))
    c.a[y0 + 9:y0 + 30, x0 + 11:x1 - 10, 3] = 0
    # kick plate, handle, sticker
    c.rect(x0 + 2, y1 - 14, x1 - 2, y1 - 3, (120, 124, 130))
    c.hline(x0 + 2, x1 - 2, y1 - 14, (160, 164, 170))
    c.box(x0 + 3, y0 + 46, x0 + 8, y0 + 50, (190, 170, 90), (230, 210, 120), (140, 120, 60))
    m = render('STAFF', SMALL)
    c.rect(x0 + 8, y0 + 34, x0 + 9 + m.shape[1] + 1, y0 + 40, (230, 226, 210))
    c.mask(m, x0 + 9, y0 + 35, (60, 60, 70))
    # EXIT sign above
    ex0, ey0 = x0 + 4, y0 - 14
    c.box(ex0, ey0, ex0 + 32, ey0 + 9, (40, 46, 44), None, None)
    e.rect(ex0 + 2, ey0 + 2, ex0 + 30, ey0 + 7, (30, 120, 70))
    e.mask(render('EXIT', SMALL), ex0 + 9, ey0 + 2, (200, 255, 210))
    return dict(rect=[x0, y0, x1, y1], light_exit=[ex0 + 16, ey0 + 5], light_door=[(x0 + x1) // 2, y0 + 20])


def mining_rig(c: Canvas):
    """Open shelf rack in the left corner with a GPU mining rig."""
    x0, y0, x1, y1 = 2, 112, 26, FLOOR_Y + 6
    for x in (x0, x1):
        c.box(x - 1, y0, x + 1, y1, C['metal'], C['metal_hi'], C['metal_lo'])
    leds = []
    for k, sy in enumerate(range(y0 + 8, y1 - 4, 22)):
        c.rect(x0, sy, x1, sy + 1, C['metal_lo'])
        c.hline(x0, x1, sy, C['metal_hi'])
        # GPUs standing on the shelf
        for g in range(3):
            gx = x0 + 3 + g * 7
            c.box(gx, sy - 14, gx + 5, sy - 1, (44, 46, 54), (70, 72, 84), (30, 30, 36))
            c.ellipse(gx + 2.5, sy - 8, 2, 2, (24, 24, 28))
            c.px(gx + 2, sy - 8, (90, 92, 100))
            leds.append([gx + 4, sy - 12])
    # cable bundle down to the floor
    for i, col in enumerate([(30, 30, 34), (180, 40, 40), (30, 30, 34)]):
        c.vline(x1 + 3 + i, y0 + 20, y1 + 6, col)
    return dict(leds=leds)


def fridge(c: Canvas):
    x0, y0, x1, y1 = 546, 158, 584, FLOOR_Y + 8
    c.box(x0, y0, x1, y1, (210, 214, 216), (236, 238, 240), (160, 164, 168))
    c.hline(x0 + 1, x1 - 1, y0 + 14, (150, 154, 158))
    c.box(x1 - 6, y0 + 4, x1 - 4, y0 + 11, (140, 144, 150))
    c.box(x1 - 6, y0 + 18, x1 - 4, y0 + 30, (140, 144, 150))
    # stickers
    c.rect(x0 + 5, y0 + 20, x0 + 13, y0 + 26, (110, 190, 90))
    c.mask(render('GM', SMALL), x0 + 16, y0 + 21, (60, 60, 70))
    c.rect(x0 + 6, y0 + 34, x0 + 18, y0 + 38, (232, 108, 46))
    # energy drinks on top
    for k in range(4):
        cx = x0 + 4 + k * 8
        c.box(cx, y0 - 10, cx + 5, y0, (38, 38, 44), (70, 70, 80), None)
        c.rect(cx + 1, y0 - 6, cx + 4, y0 - 5, (126, 226, 84))


def trash_bin(c: Canvas, x, y):
    c.poly([(x, y - 18), (x + 16, y - 18), (x + 14, y), (x + 2, y)], INK)
    c.poly([(x + 1, y - 17), (x + 15, y - 17), (x + 13, y - 1), (x + 3, y - 1)], (90, 96, 104))
    for k in range(3):
        c.vline(x + 5 + k * 3, y - 15, y - 3, (70, 74, 82))
    for (dx, dy) in [(2, -20), (7, -22), (11, -20), (5, -24)]:
        c.ellipse(x + dx + 2, y + dy + 2, 3, 2, (236, 232, 220))
        c.px(x + dx + 1, y + dy + 2, (190, 186, 172))
    c.box(x + 12, y - 26, x + 16, y - 18, (38, 38, 44), None, None)
    c.rect(x + 13, y - 23, x + 15, y - 22, (126, 226, 84))


def pizza_stack(c: Canvas, x, y, n=3):
    for k in range(n):
        yy = y - k * 4
        c.box(x + k % 2, yy - 4, x + 26 + k % 2, yy, (206, 176, 124), (226, 198, 146), (170, 140, 96))
        c.ellipse(x + 13 + k % 2, yy - 2, 3, 1, (190, 60, 50))


def floor_cables(c: Canvas, pts, col=(26, 24, 30)):
    for (a, b), (p, q) in zip(pts, pts[1:]):
        c.line(a, b, p, q, col)
        c.line(a, b + 1, p, q + 1, sh(col, 1.6))


# ------------------------------------------------------------------ the boss
def boss_area(bg: Canvas, bd: Canvas):
    cx = W // 2
    # red rug under the boss desk
    rug = [(cx - 92, FLOOR_Y + 4), (cx + 92, FLOOR_Y + 4), (cx + 104, FLOOR_Y + 34), (cx - 104, FLOOR_Y + 34)]
    bg.poly(rug, (126, 36, 40))
    inner = [(cx - 84, FLOOR_Y + 7), (cx + 84, FLOOR_Y + 7), (cx + 94, FLOOR_Y + 31), (cx - 94, FLOOR_Y + 31)]
    bg.poly(inner, (156, 52, 50))
    for y in range(FLOOR_Y + 9, FLOOR_Y + 30, 4):
        for x in range(cx - 90, cx + 90, 6):
            if bg.get(x, y) == (156, 52, 50):
                bg.px(x, y, (190, 140, 70))
    for x in range(cx - 104, cx + 105, 2):  # fringe
        bg.px(x, FLOOR_Y + 35, (220, 200, 160))
    # empty executive chair waiting for a Boss NFT
    leather, leather_hi, leather_lo, leather_dk = (104, 46, 40), (142, 70, 58), (74, 30, 28), (52, 20, 20)
    gold = (226, 184, 86)
    X0, X1, TOP, BOT = cx - 26, cx + 26, 112, 184
    # soft shadow on the wall behind the chair
    for y in range(TOP + 4, BOT):
        for x in range(X0 + 4, X1 + 5):
            if dither(x, y, .5):
                bg.px(x, y, (30, 18, 18), 110)
    def row_span(y):
        if y == TOP: return X0 + 6, X1 - 6
        if y == TOP + 1: return X0 + 3, X1 - 3
        if y == TOP + 2: return X0 + 1, X1 - 1
        return X0, X1
    for y in range(TOP, BOT + 1):
        a0, a1 = row_span(y)
        bg.hline(a0, a1, y, INK)
    for y in range(TOP + 1, BOT + 1):
        a0, a1 = row_span(y)
        bg.hline(a0 + 1, a1 - 1, y, leather)
    # headrest cushion
    HB = TOP + 20
    for y in range(TOP + 2, HB):
        a0, a1 = row_span(y)
        bg.hline(a0 + 2, a1 - 2, y, leather_hi if y < TOP + 5 else leather)
    bg.hline(X0 + 2, X1 - 2, HB, leather_dk)
    bg.hline(X0 + 2, X1 - 2, HB + 1, leather_hi)
    for x in range(X0 + 8, X1 - 6, 9):  # headrest piping
        bg.vline(x, TOP + 6, HB - 3, leather_lo)
        bg.vline(x + 1, TOP + 6, HB - 3, leather_hi)
    # diamond tufting on the main back
    for y in range(HB + 4, BOT - 2, 8):
        off = 4 if ((y - HB) // 8) % 2 else 0
        for x in range(X0 + 6 + off, X1 - 3, 8):
            bg.px(x, y, leather_dk)
            for k in range(1, 4):  # creases running to the next buttons
                bg.px(x - k, y - k, leather_lo); bg.px(x + k, y - k, leather_lo)
                bg.px(x - k, y + k, leather_lo); bg.px(x + k, y + k, leather_lo)
            bg.px(x - 1, y - 1, leather_hi)
    # roundness: bright left edge, dark right edge
    for y in range(TOP + 3, BOT + 1):
        a0, a1 = row_span(y)
        bg.px(a0 + 1, y, leather_hi); bg.px(a0 + 2, y, leather_hi)
        bg.px(a1 - 1, y, leather_dk); bg.px(a1 - 2, y, leather_lo)
    # gold studs along the outline
    for y in range(TOP + 4, BOT, 3):
        bg.px(X0 + 1, y, gold); bg.px(X1 - 1, y, gold)
    for x in range(X0 + 7, X1 - 6, 3):
        bg.px(x, TOP + 1, gold)
    # padded armrests standing above the desk line
    for ax0 in (X0 - 13, X1 + 1):
        ax1 = ax0 + 12
        bg.rect(ax0, 158, ax1, BOT, INK)
        bg.rect(ax0 + 1, 159, ax1 - 1, BOT, leather)
        bg.rect(ax0 + 1, 159, ax1 - 1, 163, leather_hi)
        bg.hline(ax0 + 1, ax1 - 1, 164, leather_dk)
        bg.vline(ax1 - 1, 165, BOT, leather_lo)
        bg.px(ax0 + 1, 158, INK); bg.px(ax1 - 1, 158, INK)
        bg.rect(ax0 + 4, 168, ax1 - 4, BOT, (150, 150, 160))  # chrome support
        bg.vline(ax0 + 4, 168, BOT, (200, 200, 210))
    # boss desk (front layer)
    x0, x1, top = cx - 74, cx + 73, 180
    D = 8
    bd.rect(x0, top, x1, top + D + 3, INK)
    wood, wood_hi, wood_lo = (96, 50, 34), (128, 72, 48), (70, 34, 24)
    bd.rect(x0 + 1, top + 1, x1 - 1, top + D, wood)
    bd.hline(x0 + 1, x1 - 1, top + D, wood_hi)
    bd.rect(x0 + 1, top + D + 1, x1 - 1, top + D + 2, wood_lo)
    for _ in range(18):
        gx, gy = int(rng.integers(x0 + 3, x1 - 12)), int(rng.integers(top + 2, top + D))
        bd.hline(gx, gx + int(rng.integers(4, 10)), gy, sh(wood, .85))
    fy = FLOOR_Y + 22
    bd.rect(x0 + 2, top + D + 3, x1 - 2, fy, INK)
    bd.rect(x0 + 3, top + D + 3, x1 - 3, fy - 1, wood)
    for (p0, p1) in ((x0 + 5, x0 + 42), (x0 + 46, x1 - 46), (x1 - 42, x1 - 5)):
        bd.box(p0, top + D + 5, p1, fy - 3, wood, wood_hi, wood_lo)
    # gold trim + nameplate
    bd.hline(x0 + 3, x1 - 3, top + D + 3, (210, 170, 80))
    m = render('BOSS', BIG)
    pw = m.shape[1] + 8
    bd.box(cx - pw // 2, top + D + 9, cx + pw // 2, top + D + 19, (220, 180, 80), (250, 220, 130), (170, 130, 50))
    bd.mask(m, cx - m.shape[1] // 2 + 1, top + D + 11, (80, 50, 20))
    # props on the boss desk
    # money stacks
    for k in range(3):
        bx = x0 + 10 + k * 7
        for j in range(3 - k % 2):
            bd.box(bx, top - 3 - j * 3, bx + 8, top + 1 - j * 3, (110, 170, 100), (150, 210, 130), (80, 130, 70))
            bd.vline(bx + 4, top - 2 - j * 3, top - j * 3, (230, 220, 160))
    # golden frog statue
    gx = x1 - 30
    gold, gold_hi, gold_lo = (220, 176, 70), (255, 226, 130), (160, 118, 40)
    bd.rect(gx - 1, top - 2, gx + 13, top + 2, INK)
    bd.rect(gx, top - 1, gx + 12, top + 1, (60, 40, 30))
    bd.ellipse(gx + 6, top - 7, 6, 5, gold)
    bd.ellipse(gx + 3, top - 12, 2, 2, gold); bd.ellipse(gx + 9, top - 12, 2, 2, gold)
    bd.px(gx + 3, top - 12, INK); bd.px(gx + 9, top - 12, INK)
    bd.px(gx + 2, top - 9, gold_hi); bd.px(gx + 3, top - 8, gold_hi)
    bd.hline(gx + 3, gx + 9, top - 5, gold_lo)
    # ashtray with cigar
    ax = x1 - 52
    bd.ellipse(ax, top + 2, 5, 2, (130, 140, 150))
    bd.ellipse(ax, top + 2, 3, 1, (60, 60, 66))
    bd.hline(ax - 1, ax + 8, top, (110, 70, 40))
    bd.px(ax + 9, top, (150, 146, 140))
    return dict(boss_anchor=[cx, top + 4], cigar=[ax + 9, top - 1], plus=[cx, 146],
                desk_top=top, chair=[X0 - 14, TOP - 4, X1 + 14, top + 34])


# --------------------------------------------------------------- worker desks
DESK_W, DESK_TOP = 104, 282
CH = {'chair': (64, 74, 50), 'chair_hi': (86, 98, 64), 'chair_lo': (44, 52, 34), 'foam': (214, 200, 150)}
DW = {'top': (178, 128, 82), 'top_hi': (204, 156, 104), 'top_lo': (152, 106, 66),
      'front': (128, 86, 54), 'front_lo': (104, 68, 42), 'front_hi': (150, 104, 66),
      'panel': (74, 50, 36), 'panel_lo': (58, 38, 28)}


def worker_chair(c: Canvas, cx: int, top: int, bottom: int, color):
    base, hi, lo = color, sh(color, 1.32), sh(color, .7)
    x0, x1 = cx - 16, cx + 15
    for y in range(top, bottom + 1):
        inset = 3 if y == top else 1 if y == top + 1 else 0
        c.hline(x0 + inset, x1 - inset, y, INK)
    for y in range(top + 1, bottom):
        inset = 3 if y == top + 1 else 1
        c.hline(x0 + inset, x1 - inset, y, base)
    c.hline(x0 + 3, x1 - 3, top + 1, hi)
    c.vline(x0 + 1, top + 3, bottom - 1, hi)
    c.vline(x1 - 1, top + 3, bottom - 1, lo)
    for k in (-6, 5):
        c.vline(cx + k, top + 4, bottom - 3, lo)
        c.vline(cx + k + 1, top + 4, bottom - 3, hi)
    if rng.random() < .6:
        for dx, dy in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2)):
            c.px(x1 - 7 + dx, top + 5 + dy, CH['foam'])
    # armrests peeking out at the sides
    for ax in (x0 - 3, x1 + 1):
        c.box(ax, bottom - 8, ax + 2, bottom + 2, (50, 50, 58), (76, 76, 86), None)


def chair_base(c: Canvas, cx: int, y: int):
    c.rect(cx - 1, y - 9, cx, y - 1, (52, 52, 62))
    c.hline(cx - 11, cx + 10, y, INK)
    c.hline(cx - 10, cx + 9, y - 1, (78, 78, 90))
    for wx in (cx - 12, cx - 1, cx + 10):
        c.rect(wx, y + 1, wx + 2, y + 2, INK)


def worker_desk(c: Canvas, x: int, y: int, variant: int):
    W_ = DESK_W
    D = 9
    c.rect(x, y, x + W_ - 1, y + D + 3, INK)
    c.rect(x + 1, y + 1, x + W_ - 2, y + D, DW['top'])
    c.hline(x + 1, x + W_ - 2, y + 1, DW['top_lo'])
    c.hline(x + 1, x + W_ - 2, y + D, DW['top_hi'])
    c.rect(x + 1, y + D + 1, x + W_ - 2, y + D + 2, DW['front'])
    for _ in range(14):
        gx, gy = int(rng.integers(x + 3, x + W_ - 10)), int(rng.integers(y + 2, y + D))
        c.hline(gx, gx + int(rng.integers(3, 8)), gy, DW['top_lo'])
    if variant % 2:
        c.ellipse(x + 30, y + 5, 3, 1, (140, 96, 58))  # coffee ring
    top_end = y + D + 3
    floor = top_end + 29
    # Back of the desk faces us (the frog sits on the other side), so the
    # front is one closed plywood panel between two metal legs, no drawers.
    c.rect(x + 2, top_end, x + W_ - 3, floor, INK)
    c.rect(x + 3, top_end, x + W_ - 4, floor - 1, DW['panel'])
    c.hline(x + 3, x + W_ - 4, top_end, DW['panel_lo'])
    c.hline(x + 3, x + W_ - 4, top_end + 1, DW['panel_lo'])
    for sx_ in (x + 36, x + 70):  # plywood sheet seams with screws
        c.vline(sx_, top_end + 2, floor - 5, DW['panel_lo'])
        c.vline(sx_ + 1, top_end + 2, floor - 5, sh(DW['panel'], 1.15))
        for sy_ in (top_end + 4, floor - 8):
            c.px(sx_ - 2, sy_, sh(DW['panel'], 1.5)); c.px(sx_ + 3, sy_, sh(DW['panel'], 1.5))
    for _ in range(10):  # wood grain on the panel
        gx, gy = int(rng.integers(x + 6, x + W_ - 12)), int(rng.integers(top_end + 3, floor - 6))
        c.hline(gx, gx + int(rng.integers(3, 9)), gy, sh(DW['panel'], .86))
    c.rect(x + 3, floor - 4, x + W_ - 4, floor - 1, DW['panel_lo'])  # kick plate
    c.hline(x + 3, x + W_ - 4, floor - 4, sh(DW['panel'], 1.2))
    for _ in range(4):  # scuffs from feet
        kx = int(rng.integers(x + 8, x + W_ - 14))
        c.hline(kx, kx + int(rng.integers(2, 5)), floor - 2, sh(DW['panel'], 1.35))
    # cable hole with cords dropping to the floor
    hx = x + 56
    c.ellipse(hx, top_end + 4, 3, 1, (24, 18, 16))
    for k, col in enumerate([(30, 30, 34), (40, 40, 46)]):
        c.vline(hx - 1 + k * 2, top_end + 5, floor - 5, col)
    # metal legs at both ends
    for lx in (x, x + W_ - 6):
        c.box(lx, top_end - 1, lx + 5, floor, (78, 78, 90), (110, 110, 124), (52, 52, 62))
        c.hline(lx - 1, lx + 6, floor, INK)
    # desk number plate
    num = render(str(variant + 1), SMALL)
    c.box(x + 18, top_end + 4, x + 27, top_end + 12, (210, 200, 170), (232, 224, 196), (170, 160, 130))
    c.mask(num, x + 21, top_end + 6, (60, 50, 40))
    c.px(x + 19, top_end + 5, (120, 110, 90)); c.px(x + 26, top_end + 5, (120, 110, 90))
    # meme stickers slapped on the back panel
    stickers = [(110, 190, 90), (232, 108, 46), (90, 170, 230), (240, 200, 70), (200, 110, 220)]
    for k in range(1 + variant % 2):
        sx, sy = x + 78 + k * 7, floor - 14 + k * 3
        col = stickers[(variant + k) % 5]
        c.rect(sx - 1, sy - 1, sx + 5, sy + 5, INK)
        c.rect(sx, sy, sx + 4, sy + 4, col)
        c.px(sx + 1, sy + 1, INK); c.px(sx + 3, sy + 1, INK); c.hline(sx + 1, sx + 3, sy + 3, INK)
    if variant in (1, 3):  # torn price tag left from the store
        c.rect(x + 42, top_end + 8, x + 50, top_end + 12, (236, 230, 214))
        c.mask(render('99', SMALL), x + 43, top_end + 8, (190, 60, 50))
    # contact shadow on the floor
    for sx_ in range(x - 2, x + W_ + 2):
        c.px(sx_, floor + 1, (0, 0, 0), 110)
        if x + 4 <= sx_ <= x + W_ - 4:
            c.px(sx_, floor + 2, (0, 0, 0), 70)
    return top_end, floor


def monitor(c: Canvas, mx: int, base_y: int, wide=36):
    w, h = wide, 27
    x0, y0 = mx - w // 2, base_y - h - 8
    c.box(mx - 7, base_y - 1, mx + 6, base_y + 2, (78, 78, 90), (110, 110, 124), (52, 52, 62))
    c.box(mx - 2, base_y - 9, mx + 1, base_y - 1, (78, 78, 90), (110, 110, 124), (52, 52, 62))
    c.box(x0, y0, x0 + w - 1, y0 + h - 1, (66, 68, 80), (96, 98, 112), (44, 46, 56))
    sx0, sy0, sx1, sy1 = x0 + 3, y0 + 3, x0 + w - 4, y0 + h - 5
    c.rect(sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1, INK)
    c.rect(sx0, sy0, sx1, sy1, (12, 20, 24))
    c.px(x0 + w - 5, y0 + h - 3, (92, 222, 112))
    return [sx0, sy0, sx1, sy1]


def sticky(c: Canvas, x, y, col):
    c.rect(x, y, x + 5, y + 5, INK)
    c.rect(x + 1, y + 1, x + 4, y + 4, col)
    c.hline(x + 1, x + 4, y + 4, sh(col, .85))


def desk_props(c: Canvas, x: int, y: int, fx: int, variant: int, mon_x0: int, mon_y0: int):
    """Keyboard, mouse and per-desk clutter so no two desks look alike."""
    key, key_lo = (196, 196, 204), (150, 150, 162)
    c.box(fx - 13, y + 3, fx + 12, y + 7, key, None, key_lo)
    for kx in range(fx - 11, fx + 11, 2):
        c.px(kx, y + 4, key_lo); c.px(kx + 1, y + 5, key_lo)
    c.box(fx + 15, y + 4, fx + 18, y + 7, key, None, key_lo)
    steam = []
    lights = []
    if variant in (0, 3, 4):  # mug
        mx, my = x + 6, y + 6
        c.box(mx, my - 8, mx + 7, my, (232, 226, 212), None, (190, 182, 168))
        c.hline(mx + 1, mx + 6, my - 7, (86, 56, 36))
        c.rect(mx - 2, my - 6, mx, my - 3, INK)
        c.px(mx - 1, my - 5, (232, 226, 212)); c.px(mx - 1, my - 4, (232, 226, 212))
        c.rect(mx + 2, my - 4, mx + 5, my - 2, [(232, 108, 46), (90, 170, 230), (110, 190, 90), (232, 108, 46), (200, 110, 220)][variant])
        steam.append([mx + 3, my - 9])
    if variant in (0, 2):  # energy drink cans
        for k in range(1 + (variant == 2)):
            cx_, cy_ = x + 17 + k * 7, y + 5
            c.box(cx_, cy_ - 10, cx_ + 5, cy_, (38, 38, 44), (70, 70, 80), None)
            c.rect(cx_ + 1, cy_ - 6, cx_ + 4, cy_ - 5, (126, 226, 84))
            c.hline(cx_ + 1, cx_ + 4, cy_ - 9, (110, 110, 124))
    if variant == 1:  # pizza box with a slice
        px_, py_ = x + 2, y + 7
        c.box(px_, py_ - 5, px_ + 24, py_, (206, 176, 124), (226, 198, 146), (170, 140, 96))
        c.poly([(px_ + 6, py_ - 9), (px_ + 16, py_ - 9), (px_ + 11, py_ - 4)], (236, 190, 90))
        c.hline(px_ + 6, px_ + 16, py_ - 10, (190, 120, 60))
        c.px(px_ + 10, py_ - 7, (200, 60, 50)); c.px(px_ + 13, py_ - 8, (200, 60, 50))
    if variant == 2:  # desk lamp, a real light source
        lx, ly = x + 8, y + 6
        c.box(lx, ly - 2, lx + 8, ly, (60, 62, 72), (90, 92, 104), None)
        c.line(lx + 4, ly - 3, lx + 2, ly - 16, (70, 72, 82))
        c.line(lx + 2, ly - 16, lx + 10, ly - 22, (70, 72, 82))
        c.poly([(lx + 8, ly - 26), (lx + 16, ly - 22), (lx + 13, ly - 17), (lx + 6, ly - 21)], (232, 108, 46))
        c.line(lx + 8, ly - 26, lx + 16, ly - 22, INK)
        lights.append([lx + 11, ly - 18])
    if variant == 3:  # second monitor stacked on a box
        bx_ = x + 2
        c.box(bx_, y - 4, bx_ + 22, y + 6, (180, 150, 100), (200, 170, 120), (140, 110, 70))
        c.mask(render('FRAGILE', SMALL)[:, :18], bx_ + 2, y - 1, (180, 60, 50))
    if variant == 4:  # cactus and a rubber duck
        c.box(x + 18, y - 3, x + 25, y + 6, (176, 92, 56), (204, 118, 74), (130, 64, 40))
        c.box(x + 20, y - 13, x + 23, y - 3, (110, 160, 80), (140, 190, 100), (80, 120, 56))
        c.ellipse(fx + 26, y + 3, 3, 2, (250, 214, 60))
        c.ellipse(fx + 24, y, 2, 2, (250, 214, 60))
        c.px(fx + 22, y, (240, 130, 40)); c.px(fx + 24, y - 1, INK)
    # sticky notes on the monitor bezel
    for k in range(1 + variant % 3):
        sticky(c, mon_x0 - 2 + k * 6, mon_y0 + 2 + (k % 2) * 3, [(246, 212, 76), (250, 150, 190), (140, 220, 240)][k])
    return steam, lights


# ----------------------------------------------------------------------- main
def build():
    OUT.mkdir(parents=True, exist_ok=True)
    bg, e, neon = Canvas(W, H), Canvas(W, H), Canvas(W, H)
    bossdesk, chairs, desks = Canvas(W, H), Canvas(W, H), Canvas(W, H)
    layout: dict = {'size': [W, H]}

    ceiling(bg)
    brick_wall(bg)
    floor(bg)
    layout['window'] = window(bg, e)
    layout['neon'] = neon_sign(bg, neon)
    layout['tv'] = boss_tv(bg)
    layout['ticker'] = ticker_board(bg)
    corkboard(bg)
    rug_counter(bg)
    layout['clock'] = wall_clock(bg)
    layout['door'] = door(bg, e)
    layout['rig'] = mining_rig(bg)
    fridge(bg)
    trash_bin(bg, 222, FLOOR_Y + 18)
    pizza_stack(bg, 36, FLOOR_Y + 12, 4)
    # plant next to the boss desk
    px_, py_ = 404, FLOOR_Y + 14
    bg.box(px_, py_ - 12, px_ + 12, py_, (176, 92, 56), (204, 118, 74), (130, 64, 40))
    for k, (dx, dy) in enumerate([(-6, -26), (2, -34), (10, -28), (16, -20), (-2, -18)]):
        bg.line(px_ + 6, py_ - 12, px_ + 6 + dx, py_ - 12 + dy // 2, (70, 100, 50))
        bg.ellipse(px_ + 6 + dx, py_ - 12 + dy // 2, 4, 2, (100, 150, 70) if k % 2 else (120, 110, 60))
    floor_cables(bg, [(29, 204), (80, 209), (170, 213), (236, 211)])
    floor_cables(bg, [(418, 213), (480, 211), (546, 206)])

    # ceiling lamps
    lamps = []
    for lx in (104, 536):
        bg.vline(lx, 0, 27, (30, 28, 34))
        shade = [(lx - 4, 28), (lx + 4, 28), (lx + 11, 37), (lx - 11, 37)]
        bg.poly(shade, C['orange'])
        bg.line(lx - 4, 28, lx - 11, 37, INK); bg.line(lx + 4, 28, lx + 11, 37, INK)
        bg.hline(lx - 4, lx + 4, 27, INK)
        bg.line(lx - 3, 29, lx - 8, 35, C['orange_hi'])
        bg.hline(lx - 11, lx + 11, 38, INK)
        e.rect(lx - 3, 38, lx + 3, 40, (255, 236, 190))
        e.hline(lx - 2, lx + 2, 41, (255, 210, 140))
        lamps.append([lx, 40])
    layout['lamps'] = lamps

    layout['boss'] = boss_area(bg, bossdesk)

    # worker row
    desks_l = []
    gap = (W - 5 * DESK_W) // 6
    for i in range(5):
        x = gap + i * (DESK_W + gap)
        fx = x + 36
        floor_y = DESK_TOP + 12 + 29
        chair_base(chairs, fx, floor_y - 2)
        chair_col = [(64, 74, 50), (88, 52, 48), (52, 62, 84), (70, 64, 52), (60, 70, 74)][i]
        worker_chair(chairs, fx, DESK_TOP - 30, DESK_TOP + 6, chair_col)
        worker_desk(desks, x, DESK_TOP, i)
        mx = x + DESK_W - 22
        screen = monitor(desks, mx, DESK_TOP + 4, 36)
        steam, dl = desk_props(desks, x, DESK_TOP, fx, i, mx - 18, DESK_TOP + 4 - 35)
        extra_screen = None
        if i == 3:  # small second screen on the box
            extra_screen = monitor(desks, x + 13, DESK_TOP - 4, 24)
        desks_l.append(dict(x=x, frog=[fx, DESK_TOP], screen=screen, screen2=extra_screen,
                            steam=steam, lamps=dl, clip=DESK_TOP + 2))
    layout['desks'] = desks_l

    # front clutter (in front of desks)
    floor_cables(desks, [(0, 352), (90, 344), (200, 350), (330, 342), (460, 350), (640, 344)], (34, 30, 38))
    for (cx_, cy_) in [(140, 348), (402, 352), (590, 346)]:
        desks.ellipse(cx_, cy_, 4, 3, (236, 232, 220))
        desks.px(cx_ - 1, cy_ - 1, (190, 186, 172))
        desks.px(cx_ + 2, cy_ + 1, (190, 186, 172))
    desks.box(262, 340, 268, 352, (38, 38, 44), (70, 70, 80), None)  # dropped can
    desks.rect(263, 345, 267, 346, (126, 226, 84))

    L_ = layout
    layout['lights'] = (
        [dict(x=x, y=y, r=190, col=[1.0, 0.74, 0.46], i=1.05, cone=True, kind='lamp') for x, y in lamps] + [
        dict(id='neon', x=L_['neon']['light'][0], y=L_['neon']['light'][1] + 6, r=150, col=[1.0, 0.48, 0.22], i=0.78),
        dict(id='tv', x=L_['tv']['light'][0], y=L_['tv']['light'][1], r=112, col=[0.35, 1.0, 0.55], i=0.55),
        dict(id='window', x=L_['window']['light'][0], y=L_['window']['light'][1], r=124, col=[0.42, 0.46, 1.0], i=0.45),
        dict(x=L_['door']['light_exit'][0], y=L_['door']['light_exit'][1], r=40, col=[0.3, 1.0, 0.5], i=0.5),
        dict(x=L_['door']['light_door'][0], y=L_['door']['light_door'][1], r=62, col=[1.0, 0.85, 0.6], i=0.35),
        dict(id='plus', x=L_['boss']['plus'][0], y=L_['boss']['plus'][1], r=44, col=[1.0, 0.8, 0.35], i=0.55),
        dict(id='ticker', x=L_['ticker']['light'][0], y=L_['ticker']['light'][1], r=72, col=[1.0, 0.6, 0.2], i=0.38)])
    layout['clocks'] = [dict(c=L_['clock']['center'], hands=[4, 6, 7])]
    layout['theme'] = dict(
        ambient=[0.33, 0.30, 0.42], screen='meme', screenLight=[0.35, 1.0, 0.5], tv='chart', rain=True,
        cones=[255, 200, 140], deskLamp=[1.0, 0.75, 0.45], tickerStyle='coins',
        coins=['$WOOF', '$FROG', '$MEOW', '$PEPE', '$BONKR', '$MOON', '$RUGZ', '$GIGA'],
        tickerSym=[255, 176, 64], tvTitle='$FROG/SOL')
    for name, cv in [('bg', bg), ('emissive', e), ('neon', neon), ('bossdesk', bossdesk),
                     ('chairs', chairs), ('desks', desks)]:
        cv.save(OUT / f'{name}.png')
    (OUT / 'layout.json').write_text(json.dumps(layout))
    return layout


if __name__ == '__main__':
    build()
    print('ok')
