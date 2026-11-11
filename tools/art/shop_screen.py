"""Shop hub: three big cards (Recruit, Casino, Boss) under a sub-screen header.

Outputs client/src/assets/shop/: bg.png, card-<k>.png, layout.json.
The header helper is shared by every sub-screen (back button + title + wallet bar).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from font import BIG, SMALL, render
from px2 import INK, Canvas, dither, mix, sh
from home_screen import (A, GOLD, GOLD_HI, GOLD_LO, H, MUTED, PANEL, PANEL_HI, PANEL_LO, PHANTOM, TEXT, W,
                         background, bevel_frame, center_text, frog_face, gear_icon, inset, load, phantom_icon,
                         text, text_w, wallet_icon)

OUT = A / 'shop'
rng = np.random.default_rng(21)


def sub_header(c: Canvas, title: str):
    """Back button and title on the left, balance and wallet controls on the right."""
    layout = {}
    c.rect(0, 0, W - 1, 31, INK)
    c.rect(0, 0, W - 1, 30, PANEL)
    c.hline(0, W - 1, 0, PANEL_HI)
    c.hline(0, W - 1, 29, PANEL_LO)
    for x in range(0, W, 2):
        c.px(x, 32, (0, 0, 0), 160)
        c.px(x + 1, 33, (0, 0, 0), 90)
    # back
    bevel_frame(c, 4, 2, 31, 28, (110, 104, 124))
    ax, ay = 11, 15
    for k in range(5):
        c.vline(ax + k, ay - k, ay + k, TEXT)
    c.rect(ax + 4, ay - 1, ax + 12, ay + 1, TEXT)
    layout['back'] = [4, 2, 31, 28]
    text(c, title, 40, 9, TEXT, BIG, INK, 2)
    # balance
    x = 300
    inset(c, x, 4, x + 128, 26)
    layout['coin'] = [x + 11, 15]
    text(c, '487,140', x + 24, 8, GOLD_HI, BIG, INK, 1)
    text(c, '$FROG', x + 86, 12, MUTED)
    x = 434
    bevel_frame(c, x, 2, x + 27, 28, (171, 159, 242), PHANTOM)
    phantom_icon(c, x + 14, 15)
    layout['phantom'] = [x, 2, x + 27, 28]
    x = 466
    bevel_frame(c, x, 2, x + 25, 28, (110, 104, 124))
    gear_icon(c, x + 6, 8)
    x = 496
    bevel_frame(c, x, 2, x + 139, 28, (120, 90, 200), (30, 24, 44))
    wallet_icon(c, x + 7, 8)
    text(c, '2FTB...3OT3', x + 26, 11, TEXT, BIG)
    c.ellipse(x + 129, 15, 2, 2, (110, 230, 110))
    return layout


ART_W, ART_H = 158, 146


def radial(c: Canvas, cx, cy, inner, outer, rx, ry):
    for y in range(ART_H):
        for x in range(ART_W):
            d = min(1, math.hypot((x - cx) / rx, (y - cy) / ry))
            col = mix(inner, outer, d)
            if dither(x, y, (d * 7) % 1 * .45):
                col = mix(col, outer, .15)
            c.px(x, y, col)


# ------------------------------------------------------------------- recruit
def card_back(c: Canvas, x, y, w=46, h=64, rim=(150, 60, 50), gold=False):
    body, hi, lo = (110, 30, 40), (150, 50, 60), (70, 18, 26)
    c.rect(x, y, x + w - 1, y + h - 1, INK)
    rim_c = GOLD if gold else rim
    c.rect(x + 1, y + 1, x + w - 2, y + h - 2, rim_c)
    c.hline(x + 1, x + w - 2, y + 1, GOLD_HI if gold else sh(rim, 1.3))
    c.rect(x + 3, y + 3, x + w - 4, y + h - 4, body)
    for yy in range(y + 4, y + h - 4):  # diamond lattice
        for xx in range(x + 4, x + w - 4):
            if (xx - x + yy - y) % 6 == 0 or (xx - x - (yy - y)) % 6 == 0:
                c.px(xx, yy, lo)
    c.hline(x + 3, x + w - 4, y + 3, hi)
    cx, cy = x + w // 2, y + h // 2
    c.ellipse(cx, cy, 13, 13, INK)
    c.ellipse(cx, cy, 12, 12, GOLD if gold else (60, 14, 22))
    c.ellipse(cx, cy, 10, 10, (30, 26, 34) if gold else (236, 226, 200))
    if not gold:
        frog_face(c, cx, cy + 1, .6)
    return cx, cy


def art_recruit():
    c = Canvas(ART_W, ART_H)
    radial(c, ART_W // 2, 62, (80, 40, 120), (14, 10, 22), 90, 90)
    # rays behind the hero card
    for k in range(14):
        a = k * math.pi / 7
        for r in range(30, 80):
            x, y = ART_W / 2 + math.cos(a) * r, 64 + math.sin(a) * r
            if dither(int(x), int(y), .35 * (1 - r / 80)):
                c.px(x, y, (255, 214, 120), 140)
    card_back(c, 22, 50)
    card_back(c, 90, 50)
    cx, cy = card_back(c, 56, 30, gold=True)
    # mystery frog silhouette with a question mark
    frog_face(c, cx, cy + 1, .8, (40, 36, 50))
    # pixel question mark
    qm = [".###.", "#...#", "...#.", "..#..", "..#..", ".....", "..#.."]
    for j, row in enumerate(qm):
        for i, ch in enumerate(row):
            if ch == '#':
                c.px(cx - 2 + i, cy - 4 + j, GOLD_HI)
    # rarity gems floating below
    gems = [(201, 205, 214), (110, 224, 106), (74, 168, 255), (182, 111, 255), (255, 180, 46), (255, 77, 109)]
    for k, col in enumerate(gems):
        gx, gy = 22 + k * 23, 126 + (k % 2) * 3
        c.poly([(gx, gy - 4), (gx + 4, gy), (gx, gy + 4), (gx - 4, gy)], INK)
        c.poly([(gx, gy - 3), (gx + 3, gy), (gx, gy + 3), (gx - 3, gy)], col)
        c.px(gx - 1, gy - 1, (255, 255, 255))
    return c, dict(halo=[cx, cy], sparkles=[[16, 22], [140, 30], [30, 104], [128, 100], [80, 12]])


# -------------------------------------------------------------------- casino
def art_casino():
    c = Canvas(ART_W, ART_H)
    radial(c, ART_W // 2, 50, (110, 30, 50), (16, 8, 14), 90, 100)
    # floor
    c.rect(0, 122, ART_W - 1, ART_H - 1, (40, 14, 22))
    for x in range(0, ART_W, 8):
        for y in range(124, ART_H, 4):
            c.px(x + (y // 4 % 2) * 4, y, (60, 22, 32))
    # slot machine
    x0, y0, x1, y1 = 44, 28, 114, 128
    c.rect(x0 - 1, y0 + 14, x1 + 1, y1, INK)
    c.rect(x0, y0 + 15, x1, y1 - 1, (190, 40, 56))
    c.vline(x0 + 1, y0 + 15, y1 - 1, (230, 80, 90))
    c.vline(x1 - 1, y0 + 15, y1 - 1, (130, 24, 36))
    # marquee with bulbs
    c.rect(x0 - 4, y0, x1 + 4, y0 + 16, INK)
    c.rect(x0 - 3, y0 + 1, x1 + 3, y0 + 15, (60, 16, 30))
    bulbs = []
    for x in range(x0 - 1, x1 + 3, 4):
        bulbs.append([x, y0 + 2]); bulbs.append([x, y0 + 13])
    for y in range(y0 + 5, y0 + 12, 4):
        bulbs.append([x0 - 2, y]); bulbs.append([x1 + 2, y])
    for bx, by in bulbs:
        c.px(bx, by, (120, 90, 40))
    m = render('CASINO', BIG)
    c.mask(m, (x0 + x1) // 2 - m.shape[1] // 2 + 1, y0 + 5, INK)
    c.mask(m, (x0 + x1) // 2 - m.shape[1] // 2, y0 + 4, GOLD_HI)
    # reels window
    rx0, ry0 = x0 + 8, y0 + 26
    c.rect(rx0 - 2, ry0 - 2, rx0 + 51, ry0 + 21, INK)
    c.rect(rx0 - 1, ry0 - 1, rx0 + 50, ry0 + 20, GOLD)
    reels = []
    for k in range(3):
        c.rect(rx0 + k * 17, ry0, rx0 + k * 17 + 15, ry0 + 19, (240, 236, 224))
        c.hline(rx0 + k * 17, rx0 + k * 17 + 15, ry0, (200, 196, 186))
        c.hline(rx0 + k * 17, rx0 + k * 17 + 15, ry0 + 19, (200, 196, 186))
        reels.append([rx0 + k * 17, ry0])
    # pay line and buttons
    c.hline(rx0 - 1, rx0 + 50, ry0 + 9, (230, 60, 60), 120)
    for k, col in enumerate([(240, 200, 70), (90, 200, 120), (90, 160, 240)]):
        c.box(x0 + 10 + k * 18, y0 + 56, x0 + 22 + k * 18, y0 + 62, col, sh(col, 1.3), sh(col, .7))
    # coin tray with coins
    c.rect(x0 + 10, y1 - 22, x1 - 10, y1 - 10, INK)
    c.rect(x0 + 11, y1 - 21, x1 - 11, y1 - 11, (60, 16, 26))
    for k in range(6):
        cx_ = x0 + 16 + k * 7
        c.ellipse(cx_, y1 - 13, 3, 2, GOLD)
        c.px(cx_ - 1, y1 - 14, GOLD_HI)
    # lever
    c.rect(x1 + 2, y0 + 40, x1 + 5, y0 + 46, (150, 150, 160))
    c.vline(x1 + 6, y0 + 22, y0 + 44, (190, 190, 200))
    c.ellipse(x1 + 6, y0 + 20, 3, 3, INK)
    c.ellipse(x1 + 6, y0 + 20, 2, 2, (230, 50, 50))
    # chip stacks on the floor
    for (sx, sy, col) in [(18, 130, (230, 60, 60)), (26, 134, (60, 120, 230)), (132, 132, (40, 40, 44)), (140, 136, (90, 200, 120))]:
        for k in range(4):
            c.ellipse(sx, sy - k * 2, 5, 2, INK)
            c.ellipse(sx, sy - k * 2, 4, 1, col)
            c.px(sx - 2, sy - k * 2, (255, 255, 255))
    return c, dict(bulbs=bulbs, reels=reels, rest=[ART_W // 2, 110])


# ---------------------------------------------------------------------- boss
def art_boss():
    c = Canvas(ART_W, ART_H)
    radial(c, ART_W // 2, 80, (60, 50, 20), (12, 10, 8), 100, 100)
    # spotlight cone from above
    for y in range(ART_H):
        half = 12 + y * .45
        for x in range(int(ART_W / 2 - half), int(ART_W / 2 + half) + 1):
            if dither(x, y, .22 * (1 - abs(x - ART_W / 2) / half)):
                c.px(x, y, (255, 230, 160), 120)
    # pedestal
    px0, px1, py = 30, 128, 116
    c.rect(px0, py, px1, ART_H - 1, INK)
    c.rect(px0 + 1, py + 1, px1 - 1, ART_H - 1, (200, 196, 186))
    c.hline(px0 + 1, px1 - 1, py + 1, (240, 236, 226))
    c.rect(px0 + 1, py + 6, px1 - 1, py + 8, GOLD)
    c.hline(px0 + 1, px1 - 1, py + 6, GOLD_HI)
    for x in range(px0 + 6, px1 - 4, 9):  # marble veins
        c.line(x, py + 10, x + 4, ART_H - 2, (170, 166, 156))
    # the boss NFT
    spr = load(A / 'menu/boss-green-cut.png')
    bx, by = ART_W // 2 - spr.shape[1] // 2, py - spr.shape[0] + 8
    c.blit(spr, bx, by)
    # NFT tag
    c.rect(ART_W - 30, 6, ART_W - 6, 16, INK)
    c.rect(ART_W - 29, 7, ART_W - 7, 15, GOLD)
    m = render('NFT', SMALL)
    c.mask(m, ART_W - 18 - m.shape[1] // 2, 9, (60, 40, 10))
    return c, dict(sparkles=[[40, 30], [118, 38], [30, 80], [128, 86], [78, 10]])


# --------------------------------------------------------------------- cards
CARD_W, CARD_H = 168, 214
CARDS = [
    ('recruit', 'RECRUIT', 'HIRE NEW FROGS', (176, 104, 255), art_recruit),
    ('casino', 'CASINO', 'FROGS RECOVER FASTER', (230, 70, 90), art_casino),
    ('boss', 'BOSS', '1 SOL OR $FROG', (240, 190, 80), art_boss),
]


def card(key, title, sub, acc, fn):
    c = Canvas(CARD_W, CARD_H)
    bevel_frame(c, 0, 0, CARD_W - 1, CARD_H - 1, acc)
    ax, ay = 5, 5
    c.rect(ax - 1, ay - 1, ax + ART_W, ay + ART_H, INK)
    art, meta = fn()
    c.blit(art.a, ax, ay)
    # name plate
    py = ay + ART_H + 4
    c.rect(6, py, CARD_W - 7, py + 26, INK)
    c.rect(7, py + 1, CARD_W - 8, py + 25, (34, 30, 42))
    c.hline(7, CARD_W - 8, py + 1, (60, 54, 70))
    c.rect(7, py + 23, CARD_W - 8, py + 25, acc)
    center_text(c, title, CARD_W // 2, py + 6, TEXT, BIG, INK, 2)
    center_text(c, sub, CARD_W // 2, py + 34, MUTED, SMALL, None)

    def shift(v):
        return [v[0] + ax, v[1] + ay]
    out = {}
    for k, v in meta.items():
        if isinstance(v, list) and v and isinstance(v[0], list):
            out[k] = [shift(p) for p in v]
        elif isinstance(v, list):
            out[k] = shift(v)
    return c, out


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    bg = Canvas(W, H)
    background(bg)
    layout = {'size': [W, H], 'hud': sub_header(bg, 'SHOP')}
    gap = 22
    total = 3 * CARD_W + 2 * gap
    x0 = (W - total) // 2
    cards = []
    for i, (key, title, sub, acc, fn) in enumerate(CARDS):
        cv, meta = card(key, title, sub, acc, fn)
        cv.save(OUT / f'card-{key}.png')
        x, y = x0 + i * (CARD_W + gap), 76
        cards.append(dict(key=key, title=title, x=x, y=y, w=CARD_W, h=CARD_H, accent=list(acc), meta=meta))
        for yy in range(y + 4, y + CARD_H + 4):
            for xx in range(x + 4, x + CARD_W + 4):
                if (xx + yy) % 2:
                    bg.px(xx, yy, (0, 0, 0), 140)
    layout['cards'] = cards
    layout['tiles'] = []
    bg.save(OUT / 'bg.png')
    (OUT / 'layout.json').write_text(json.dumps(layout))
    return layout


if __name__ == '__main__':
    build()
    print('ok')
