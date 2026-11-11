"""Recruit screen: velvet stage, a pack on a plinth, pack size chips and a big OPEN button.
Also the frog card parts (frames per rarity, card back, stat and skill icons) that the
Recruit reveal and the Frogs screen share.

Outputs client/src/assets/recruit/ and client/src/assets/cards/.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent / 'trailer'))

from px2 import INK, Canvas, mix, sh, dither  # noqa: E402
from menu_kit import (GOLD, GOLD_HI, GOLD_LO, TEXT, MUTED, Lights, bloom, brass_inset, coin, draw_text,  # noqa: E402
                      enamel_plate, frame_card, gradient_text, lit, text_mask, text_size, wood_planks)
from menu2 import button, header, picture_lamp  # noqa: E402
import menu_scenes as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'client/src/assets'
OUT = A / 'recruit'
CARDS = A / 'cards'
W, H = 640, 360
RARITY = [('common', 'COMMON', (201, 205, 214)), ('uncommon', 'UNCOMMON', (110, 224, 106)),
          ('rare', 'RARE', (74, 168, 255)), ('epic', 'EPIC', (182, 111, 255)),
          ('legendary', 'LEGENDARY', (255, 180, 46)), ('mythic', 'MYTHIC', (255, 77, 109))]
VIOLET = (176, 104, 255)
CARD_W, CARD_H = 112, 184
ART = (8, 26, 103, 125)            # art window inside a card (x0, y0, x1, y1)


def save(a, path):
    Image.fromarray(a.a if isinstance(a, Canvas) else a, 'RGBA').save(path)


# ================================================================== icons
PAL = {'k': INK, 'w': (246, 242, 232), 'y': GOLD, 'Y': GOLD_HI, 'o': (240, 120, 40), 'r': (226, 60, 60),
       'g': (96, 200, 80), 'G': (40, 110, 44), 'b': (60, 120, 220), 'B': (150, 200, 255), 'c': (90, 220, 230),
       'p': (170, 100, 240), 's': (150, 146, 160), 'n': (130, 80, 46), 'N': (90, 54, 30)}

SKILL_ART = {
    'diamondHands': ["...........", "..kkkkkkk..", ".kBwBBcBBk.", "kBwBBcBBcBk", "kkkkkkkkkkk", ".kcBBcBBck.",
                     "..kcBcBck..", "...kcBck...", "....kck....", ".....k.....", "..........."],
    'powerNap': ["......kk...", "....kkYk...", "...kYYk....", "..kYYk.....", "..kYYk..kkk", "..kYYk...k.",
                 "..kYYYk.kkk", "...kYYYkk..", "....kkkk...", "...........", "..........."],
    'fastFingers': ["......kkk..", ".....kYYk..", "....kYYk...", "...kYYk....", "..kYYYYYk..", "...kkYYk...",
                    "....kYYk...", "...kYYk....", "..kYYk.....", "..kkk......", "..........."],
    'caffeine': ["...w..w....", "....w..w...", "...........", ".kkkkkkk...", ".kwwwwwkkk.", ".knnnnnk.k.",
                 ".knnnnnkkk.", ".knNnnnk...", "..kkkkk....", "kkkkkkkkk..", "..........."],
    'stopLoss': [".kkkkkkkkk.", ".kbbbbbbbk.", ".kbbbbbbwk.", ".kbbbbbwbk.", ".kbwbbwbbk.", ".kbbwwbbbk.",
                 "..kbbbbbk..", "...kbbbk...", "....kbk....", ".....k.....", "..........."],
    'hotStreak': ["....k......", "....kk.....", "...kok.....", "...kook....", "..kooYok...", "..koYYok.k.",
                  ".koYYYYokok", ".koYwwYoook", ".koYwwYook.", "..kooooook.", "...kkkkkk.."],
    'dipBuyer': ["...........", "rr.......gg", "rrr.....ggg", ".rrr...ggg.", "..rrr.ggg..", "...rrggg...",
                 "....rgg....", ".....g.....", "...........", "kkkkkkkkkkk", "..........."],
    'degenMode': ["..kkkkkkk..", ".kwwwwwwwk.", "kwwwwwwwwwk", "kwkkwwwkkwk", "kwkkwwwkkwk", "kwwwwkwwwwk",
                  ".kwwwwwwwk.", "..kwkwkwk..", "..kkkkkkk..", "...........", "..........."],
    'luckyCharm': [".kkk.kkk...", "kgggkgggk..", "kgGgkgGgk..", "kgggggggk..", ".kgggggk...", "kgggggggk..",
                   "kgGgkgGgk..", "kgggkgggk.k", ".kkk.kkkGk.", "......kGk..", "......k...."],
    'copyTrader': ["kkkkkkk....", "kwwwwwk....", "kwssskkkkkk", "kwwwwkwwwwk", "kwssskssssk", "kwwwwkwwwwk",
                   "kkkkkkssssk", ".....kwwwwk", ".....kssssk", ".....kwwwwk", ".....kkkkkk"],
    'nightOwl': ["......kkk..", "....kkBBk..", "...kBBk....", "..kBBk...y.", "..kBBk..yYy", "..kBBk...y.",
                 "..kBBBk....", "...kBBBkkk.", "....kkBBBk.", "......kkk..", "..........."],
    'whaleHunter': ["...........", ".......w.w.", "........w..", ".........kk", "..kkkkk.kbk", ".kbbbbbkbk.",
                    "kbwbbbbbbk.", "kbbbbbbbk..", "kBBBBBBk...", ".kkkkkk....", "..........."],
    'rugRadar': ["...kkkkk...", "..kGgggGk..", ".kGgGGGgGk.", "kGgGgggGgGk", "kGgGgwgGgGk", "kGgGgggGgGk",
                 ".kGgGGGgGk.", "..kGgggGk..", "...kkkkk...", "...........", "..........."],
    'insider': ["...........", "...kkkkk...", ".kkwwwwwkk.", "kwwwbbbwwwk", "kwwbkkkbwwk", "kwwbkwkbwwk",
                "kwwbkkkbwwk", "kwwwbbbwwwk", ".kkwwwwwkk.", "...kkkkk...", "..........."],
}
STAT_ART = {
    'patience': [".kkkkkkk.", ".kYYYYYk.", "..kwwwk..", "...kwk...", "....k....", "...kyk...", "..kyyyk..",
                 ".kYYYYYk.", ".kkkkkkk."],
    'profit': ["..kkkkk..", ".kYYYYYk.", "kYYyyyYYk", "kYyYYYyYk", "kYyYYYyYk", "kYyYYYyYk", "kYYyyyYYk",
               ".kyyyyyk.", "..kkkkk.."],
    'risk': ["kkkkkkkkk", "kwwwwwwwk", "kwkwwwkwk", "kwwwwwwwk", "kwwwkwwwk", "kwwwwwwwk", "kwkwwwkwk",
             "kwwwwwwwk", "kkkkkkkkk"],
}


def icon_img(rows):
    h, w = len(rows), max(len(r) for r in rows)
    a = np.zeros((h, w, 4), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in PAL:
                a[y, x, :3] = PAL[ch]
                a[y, x, 3] = 255
    return a


def build_icons():
    """One atlas with every icon, plus a JSON map of their boxes."""
    px16 = Path(__file__).parent / 'source/skills/px16'
    tiles = [('skill-' + k, np.array(Image.open(px16 / f'{k}.png').convert('RGBA'))) for k in SKILL_ART] + [('stat-' + k, icon_img(v)) for k, v in STAT_ART.items()]
    w = sum(t.shape[1] + 1 for _, t in tiles)
    h = max(t.shape[0] for _, t in tiles)
    atlas = np.zeros((h, w, 4), np.uint8)
    boxes, x = {}, 0
    for name, t in tiles:
        atlas[:t.shape[0], x:x + t.shape[1]] = t
        boxes[name] = [x, 0, t.shape[1], t.shape[0]]
        x += t.shape[1] + 1
    Image.fromarray(atlas, 'RGBA').save(CARDS / 'icons.png')
    return boxes


# ================================================================== cards
def card_frame(rid):
    key, name, col = RARITY[rid]
    c = Canvas(CARD_W, CARD_H)
    frame_card(c, CARD_W, CARD_H, col)
    # rarity enamel plate
    enamel_plate(c, 8, 8, CARD_W - 9, 23, col)
    m = text_mask(name, 'head')
    x0 = CARD_W // 2 - m.shape[1] // 2
    for dx, dy in ((0, 1), (1, 1)):
        c.mask(m, x0 + dx, 10 + dy, INK)
    c.mask(m, x0, 10, (255, 255, 255))
    # art window: deep radial glow in the rarity colour
    x0, y0, x1, y1 = ART
    c.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, INK)
    cx, cy = (x0 + x1) / 2, y0 + 44
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = math.hypot((x - cx) / 52, (y - cy) / 62)
            base = mix(sh(col, .62), (18, 12, 22), min(1, d * .95))
            if dither(x, y, max(0, .5 - d) * .5):
                base = mix(base, sh(col, .9), .35)
            c.px(x, y, base)
    # floor shadow and rays for the higher tiers
    for x in range(x0, x1 + 1):
        c.px(x, y1, sh(col, .25)); c.px(x, y1 - 1, sh(col, .32))
    if rid >= 3:
        for k in range(10):
            a = -math.pi / 2 + (k - 4.5) * 0.28
            for r in range(16, 64):
                X, Y = int(cx + math.cos(a) * r), int(cy + math.sin(a) * r * .9)
                if x0 < X < x1 and y0 < Y < y1 and (X + Y + r) % 3 == 0:
                    c.px(X, Y, mix(c.get(X, Y), sh(col, 1.2), .35))
    # text panel
    c.rect(8, 128, CARD_W - 9, CARD_H - 9, (22, 18, 26))
    c.hline(8, CARD_W - 9, 128, (40, 34, 46))
    # stat wells: three brass-rimmed slots
    for i in range(3):
        sx = 10 + i * 31
        brass_inset(c, sx, 140, sx + 29, 153)
    if rid >= 4:   # gold corner gems for the top tiers
        for (gx, gy) in ((3, 3), (CARD_W - 6, 3), (3, CARD_H - 6), (CARD_W - 6, CARD_H - 6)):
            c.rect(gx - 1, gy - 1, gx + 3, gy + 3, INK)
            c.rect(gx, gy, gx + 2, gy + 2, col)
            c.px(gx, gy, (255, 255, 255))
    return c


def card_back():
    c = Canvas(CARD_W, CARD_H)
    frame_card(c, CARD_W, CARD_H, GOLD)
    S.card_back(c, 8, 8, CARD_W - 16, CARD_H - 16, gold=True)
    cx, cy = CARD_W // 2, CARD_H // 2
    c.ellipse(cx, cy, 17, 17, INK)
    c.ellipse(cx, cy, 16, 16, GOLD)
    c.ellipse(cx, cy, 13, 13, (30, 26, 34))
    m = text_mask('?', 'title')
    m = np.kron(m, np.ones((2, 2), bool))
    c.mask(m, cx - m.shape[1] // 2, cy - m.shape[0] // 2, GOLD_HI)
    return c


def big_pack():
    """The frog pack, 80x112, foil stripes and a mythic frog medallion."""
    from scenes import make_pack
    p, tear = make_pack()
    return p, tear


# ================================================================== stage
def stage():
    rng = np.random.default_rng(12)
    c, e = Canvas(W, H), Canvas(W, H)
    floor = 300
    for x in range(W):
        fold = x % 12
        col = (90, 30, 70) if fold in (0, 1, 2) else (122, 44, 98) if fold in (3, 4, 5, 6) else (104, 36, 84)
        c.vline(x, 34, floor, col)
    for x in range(0, W, 12):
        c.vline(x, 34, floor, (60, 18, 48))
    for x in range(W):            # valance with a gold fringe under the header
        yb = 44 + int(5 * math.sin(x / 53 * math.pi) ** 2)
        c.vline(x, 34, yb, (140, 30, 50) if (x // 6) % 2 else (128, 26, 44))
        c.px(x, yb + 1, GOLD if x % 3 else GOLD_LO)
        if x % 4 == 0:
            c.vline(x, yb + 2, yb + 4, GOLD_LO)
    # stage floor
    c.rect(0, floor, W - 1, H - 1, INK)
    wood_planks(c, 0, floor + 1, W - 1, H - 1, rng, cols=[(110, 66, 40), (102, 62, 38), (118, 72, 44), (96, 58, 36)])
    c.hline(0, W - 1, floor + 1, (170, 116, 72))
    c.hline(0, W - 1, floor + 2, (140, 92, 58))
    # plinth for the pack
    px0, px1, py = 274, 365, 222
    c.rect(px0 - 4, py, px1 + 4, py + 6, INK)
    c.rect(px0 - 3, py + 1, px1 + 3, py + 5, (150, 40, 60))
    c.hline(px0 - 3, px1 + 3, py + 1, (200, 70, 90))
    c.rect(px0, py + 7, px1, floor, INK)
    c.rect(px0 + 1, py + 7, px1 - 1, floor, (60, 44, 56))
    c.vline(px0 + 1, py + 7, floor, (90, 70, 84))
    c.vline(px1 - 1, py + 7, floor, (40, 30, 38))
    for x in range(px0 + 6, px1 - 4, 10):
        c.vline(x, py + 10, floor - 3, (70, 54, 66))
    c.rect(px0 - 3, py + 7, px1 + 3, py + 9, GOLD_LO)
    c.hline(px0 - 3, px1 + 3, py + 7, GOLD_HI)
    # NOW HIRING neon sign
    m = text_mask('NOW HIRING', 'title')
    sx, sy = W // 2 - m.shape[1] // 2, 60
    c.rect(sx - 8, sy - 5, sx + m.shape[1] + 7, sy + m.shape[0] + 4, INK)
    c.rect(sx - 7, sy - 4, sx + m.shape[1] + 6, sy + m.shape[0] + 3, (26, 14, 30))
    for bx in (sx - 4, sx + m.shape[1] + 3):
        c.vline(bx, 47, sy - 6, (70, 70, 80))
    e.mask(m, sx, sy, (255, 90, 190))
    pad = np.pad(m, 1)
    inner = m & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    e.mask(inner, sx, sy, (255, 220, 244))
    # silhouettes of the six frogs you can pull, rim-lit in their rarity colour
    spots = [(50, 0), (106, 1), (162, 2), (478, 3), (534, 4), (590, 5)]
    for cx_, rid in spots:
        spr = S.sprite(f'frogs/worker-{RARITY[rid][0]}.png')
        h, w = spr.shape[:2]
        x0, y0 = cx_ - w // 2, floor + 4 - h
        alpha = spr[..., 3] > 0
        col = RARITY[rid][2]
        toward = 1 if cx_ < W // 2 else -1
        for y in range(h):
            for x in range(w):
                if not alpha[y, x]:
                    continue
                lum = spr[y, x, :3].astype(float).mean() / 255
                base = mix((14, 8, 18), (34, 20, 40), lum)
                nx = x + toward
                edge = not (0 <= nx < w) or not alpha[y, nx]
                c.px(x0 + x, y0 + y, base)
                if edge:
                    e.px(x0 + x, y0 + y, sh(col, .9), 220)
                elif (0 <= x + 2 * toward < w) and not alpha[y, x + 2 * toward] and (x + y) % 2:
                    e.px(x0 + x, y0 + y, sh(col, .55), 140)
        # soft floor glow in the rarity colour
        for yy in range(floor + 2, floor + 9):
            for xx in range(cx_ - 26, cx_ + 27):
                d = ((xx - cx_) / 26) ** 2 + ((yy - floor - 5) / 4) ** 2
                if d < 1 and (xx + yy) % 2:
                    e.px(xx, yy, sh(col, .7), int(90 * (1 - d)))
        # a question mark above each silhouette
        q = text_mask('?', 'head')
        e.mask(q, cx_ - q.shape[1] // 2, y0 - 14, sh(col, .95))
    L = Lights(W, H, [0.24, 0.2, 0.3])
    L.spot(W / 2, 34, 0.32, 300, [1.0, 0.82, 0.62], 1.25)
    L.point(W / 2, 70, 120, [1.0, 0.4, 0.8], 0.5)
    for cx_, rid in spots:
        L.point(cx_, floor - 20, 60, [v / 255 for v in RARITY[rid][2]], 0.35)
    out = lit(c, L, e)
    bloom(out, e, .45, 2)
    return out


def size_chip(n, on):
    w, h = 54, 22
    c = Canvas(w, h)
    col = VIOLET if on else (86, 78, 98)
    button(c, 0, 0, w - 1, h - 1, col)
    label = f'x{n}'
    tw_, th_ = text_size(label, 'head')
    draw_text(c, label, w // 2, 4, (255, 255, 255) if on else (210, 204, 220), 'head', align='center')
    if on:
        c.px(3, 3, (255, 255, 255)); c.px(w - 4, 3, (255, 255, 255))
    return c


def open_button(n, price):
    w, h = 236, 40
    c = Canvas(w, h)
    button(c, 0, 0, w - 1, h - 1, GOLD)
    label = 'OPEN PACK' if n == 1 else f'OPEN {n} PACKS'
    gradient_text(c, label, w // 2, 4, (60, 34, 8), (40, 22, 6), 'title', shadow=None, outline=None, align='center')
    price_s = f'{price:,} $FROG'
    tw_, _ = text_size(price_s, 'body')
    cx = w // 2 - (tw_ + 12) // 2
    coin(c, cx + 4, 29, 4)
    draw_text(c, price_s, cx + 12, 26, (70, 40, 10), 'body', shadow=None)
    return c


def action_button(label, col, dark_text):
    w, h = 180, 36
    c = Canvas(w, h)
    button(c, 0, 0, w - 1, h - 1, col)
    if dark_text:
        gradient_text(c, label, w // 2, 9, (60, 34, 8), (40, 22, 6), 'title', shadow=None, outline=None, align='center')
    else:
        gradient_text(c, label, w // 2, 9, (255, 255, 255), (232, 226, 218), 'title', align='center')
    return c


def arrow(d):
    w, h = 18, 34
    c = Canvas(w, h)
    button(c, 0, 0, w - 1, h - 1, (86, 78, 98))
    cx = w // 2
    for k in range(6):
        x = cx - 2 * d + k * d
        c.vline(x, 16 - (5 - k), 16 + (5 - k), (240, 234, 226))
    return c


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    CARDS.mkdir(parents=True, exist_ok=True)
    bg = stage()
    lay = {'size': [W, H], 'hud': header(bg, 'RECRUIT')}
    save(bg, OUT / 'bg.png')
    pack, tear = big_pack()
    save(pack, OUT / 'pack.png')
    sizes = [1, 5, 10, 15]
    chips = []
    total = len(sizes) * 54 + (len(sizes) - 1) * 8
    for i, n in enumerate(sizes):
        save(size_chip(n, False), OUT / f'size-{n}.png')
        save(size_chip(n, True), OUT / f'size-{n}-on.png')
        chips.append({'n': n, 'x': W // 2 - total // 2 + i * 62, 'y': 262, 'w': 54, 'h': 22})
        save(open_button(n, n * 10_000), OUT / f'open-{n}.png')
    lay['pack'] = {'x': W // 2 - pack.shape[1] // 2, 'y': 108, 'tear': tear}
    lay['chips'] = chips
    lay['open'] = {'x': W // 2 - 118, 'y': 292, 'w': 236, 'h': 40}
    lay['back'] = 'shop'
    lay['cards'] = []
    lay['tiles'] = []
    for key, label, col in (('work', 'SEND TO WORK', GOLD), ('more', 'OPEN MORE', VIOLET)):
        save(action_button(label, col, key == 'work'), OUT / f'btn-{key}.png')
    save(arrow(-1), OUT / 'arrow-left.png')
    save(arrow(1), OUT / 'arrow-right.png')
    lay['result'] = {'work': {'x': 132, 'y': 304, 'w': 180, 'h': 36}, 'more': {'x': 328, 'y': 304, 'w': 180, 'h': 36},
                     'left': {'x': 4, 'y': 150, 'w': 18, 'h': 34}, 'right': {'x': 618, 'y': 150, 'w': 18, 'h': 34},
                     'slots': [[20 + i * 122, 82] for i in range(5)], 'single': [264, 82]}
    (OUT / 'layout.json').write_text(json.dumps(lay))
    for rid in range(6):
        save(card_frame(rid), CARDS / f'frame-{RARITY[rid][0]}.png')
    save(card_back(), CARDS / 'back.png')
    boxes = build_icons()
    (CARDS / 'layout.json').write_text(json.dumps({'size': [CARD_W, CARD_H], 'art': ART, 'icons': boxes,
                                                   'stats': [[10 + i * 31, 140] for i in range(3)]}))


if __name__ == '__main__':
    build()
    print('recruit ok')
