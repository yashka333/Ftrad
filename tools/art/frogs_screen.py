"""Frogs screen: your crew in a locker room. A grid of portraits on the left,
the picked frog's card, status and actions on the right.

Outputs client/src/assets/frogs-screen/.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from px2 import INK, Canvas, mix, sh, dither
from menu_kit import (GOLD, GOLD_HI, GOLD_LO, TEXT, MUTED, Lights, brass_inset, draw_text, frame_card, gradient_text,
                      lit, text_mask, text_size, metal_plate)
from menu2 import button, header
import menu_scenes as S

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'client/src/assets'
OUT = A / 'frogs-screen'
W, H = 640, 360
RARITY = [(201, 205, 214), (110, 224, 106), (74, 168, 255), (182, 111, 255), (255, 180, 46), (255, 77, 109)]
KEYS = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
TILE_W, TILE_H = 50, 64
LEFT = (6, 58, 408, 354)
RIGHT = (414, 58, 634, 354)


def save(c, name):
    Image.fromarray(c.a if isinstance(c, Canvas) else c, 'RGBA').save(OUT / name)


def panel(c, box, accent):
    x0, y0, x1, y1 = box
    p = Canvas(x1 - x0 + 1, y1 - y0 + 1)
    frame_card(p, p.w, p.h, accent)
    c.blit(p.a, x0, y0)


def lockers(c):
    """The locker room wall behind the panels."""
    floor = 330
    c.rect(0, 34, W - 1, floor, (34, 40, 38))
    lw, x, k = 26, -4, 0
    while x < W:
        col = (70, 88, 80) if k % 2 == 0 else (64, 82, 74)
        c.rect(x, 40, x + lw - 1, floor - 2, INK)
        c.rect(x + 1, 41, x + lw - 2, floor - 3, col)
        c.hline(x + 1, x + lw - 2, 41, sh(col, 1.3))
        c.vline(x + 1, 41, floor - 3, sh(col, 1.18))
        c.vline(x + lw - 2, 41, floor - 3, sh(col, .72))
        for vy in range(48, 66, 3):
            c.hline(x + 6, x + lw - 7, vy, sh(col, .6))
            c.hline(x + 6, x + lw - 7, vy + 1, sh(col, 1.2))
        c.rect(x + lw - 7, 120, x + lw - 5, 128, (160, 160, 168))
        x += lw
        k += 1
    for y in range(floor, H):
        for x2 in range(W):
            c.px(x2, y, (54, 52, 60) if ((x2 // 10) + (y // 5)) % 2 else (62, 60, 68))
    c.hline(0, W - 1, floor, INK)


def portrait_frame(rid):
    """Small rarity frame with a dark window for the frog's head."""
    col = RARITY[rid]
    c = Canvas(TILE_W, TILE_H)
    c.rect(0, 0, TILE_W - 1, TILE_H - 1, INK)
    c.rect(1, 1, TILE_W - 2, TILE_H - 2, sh(col, .55))
    c.hline(1, TILE_W - 2, 1, sh(col, 1.0))
    c.vline(1, 1, TILE_H - 2, sh(col, .85))
    c.rect(3, 3, TILE_W - 4, 47, INK)
    for y in range(4, 47):
        for x in range(4, TILE_W - 4):
            d = math.hypot((x - TILE_W / 2) / 26, (y - 22) / 26)
            base = mix(sh(col, .5), (16, 12, 20), min(1, d))
            if dither(x, y, max(0, .45 - d) * .5):
                base = mix(base, sh(col, .85), .3)
            c.px(x, y, base)
    # info strip under the window
    c.rect(3, 49, TILE_W - 4, TILE_H - 4, (20, 16, 24))
    if rid >= 4:
        c.px(2, 2, (255, 255, 255)); c.px(TILE_W - 3, 2, (255, 255, 255))
    return c


def plate(w, h, col, active):
    c = Canvas(w, h)
    button(c, 0, 0, w - 1, h - 1, col if active else (62, 56, 72))
    return c


def action_button(label, col, w=86, h=18, dark=False):
    c = Canvas(w, h)
    button(c, 0, 0, w - 1, h - 1, col)
    draw_text(c, label, w // 2, (h - 8) // 2, (40, 24, 6) if dark else (255, 255, 255), 'head', shadow=None if dark else INK, align='center')
    return c


def desk_slot(w=24, h=20):
    """An empty desk in the picker: a dark well with a little desk and monitor."""
    c = Canvas(w, h)
    c.rect(0, 0, w - 1, h - 1, INK)
    c.rect(1, 1, w - 2, h - 2, (30, 26, 36))
    c.hline(1, w - 2, h - 2, (52, 46, 60))
    c.rect(7, 5, 16, 11, (58, 54, 68))
    c.rect(8, 6, 15, 10, (36, 44, 52))
    c.vline(11, 12, 13, (58, 54, 68)); c.vline(12, 12, 13, (58, 54, 68))
    c.rect(4, 14, 19, 15, (74, 60, 50))
    return c



def build():
    OUT.mkdir(parents=True, exist_ok=True)
    bg = Canvas(W, H)
    lockers(bg)
    L = Lights(W, H, [0.42, 0.44, 0.52])
    for lx in (120, 320, 520):
        L.point(lx, 30, 200, [1.0, 0.95, 0.85], 0.55, cone=True)
    bg = lit(bg, L)
    lay = {'size': [W, H], 'hud': header(bg, 'FROGS'), 'cards': [], 'tiles': [], 'back': 'home'}
    panel(bg, LEFT, (110, 200, 90))
    panel(bg, RIGHT, (110, 200, 90))
    # drop shadows
    for (x0, y0, x1, y1) in (LEFT, RIGHT):
        for y in range(y0 + 3, y1 + 3):
            if y < H:
                for x in (x1 + 1, x1 + 2):
                    if x < W and (x + y) % 2:
                        bg.px(x, y, (0, 0, 0), 140)
    # locker cubbies behind every grid cell: empty slots read as empty lockers
    gx0, gy0 = LEFT[0] + 10, LEFT[1] + 10
    for r in range(4):
        for col in range(7):
            x, y = gx0 + col * (TILE_W + 4), gy0 + r * (TILE_H + 4)
            bg.rect(x, y, x + TILE_W - 1, y + TILE_H - 1, INK)
            bg.rect(x + 1, y + 1, x + TILE_W - 2, y + TILE_H - 2, (40, 48, 46))
            bg.hline(x + 1, x + TILE_W - 2, y + 1, (60, 72, 68))
            bg.rect(x + 3, y + 3, x + TILE_W - 4, y + TILE_H - 4, (24, 28, 30))
            for vy in range(y + 6, y + 16, 3):
                bg.hline(x + 10, x + TILE_W - 11, vy, (34, 40, 40))
                bg.hline(x + 10, x + TILE_W - 11, vy + 1, (48, 56, 54))
            bg.rect(x + TILE_W - 9, y + 30, x + TILE_W - 8, y + 36, (70, 76, 80))
    # card niche: a soft spotlight where the picked frog's card stands
    rx0, ry0 = RIGHT[0] + 8, RIGHT[1] + 8
    for y in range(ry0, ry0 + 184):
        for x in range(rx0, rx0 + 112):
            d = math.hypot((x - rx0 - 56) / 70, (y - ry0 - 70) / 110)
            base = mix((44, 36, 52), (16, 12, 20), min(1, d))
            if dither(x, y, max(0, .4 - d) * .4):
                base = mix(base, (60, 52, 70), .5)
            bg.px(x, y, base)
    bg.rect(rx0 - 1, ry0 - 1, rx0 + 112, ry0 - 1, INK)
    draw_text(bg, 'PICK A FROG', rx0 + 56, ry0 + 84, (120, 110, 130), 'body', align='center')
    # info labels
    ix = rx0 + 118
    for y, label in ((ry0, 'STATUS'), (ry0 + 34, 'DESK'), (ry0 + 54, 'STAMINA')):
        draw_text(bg, label, ix, y, (130, 120, 136), 'body', shadow=None)
    brass_inset(bg, ix, ry0 + 62, ix + 85, ry0 + 70)
    bg.hline(ix, ix + 85, ry0 + 78, (44, 38, 50))
    # skills shelf under the card
    draw_text(bg, 'SKILLS', rx0, ry0 + 190, (130, 120, 136), 'body', shadow=None)
    bg.hline(rx0 + 30, rx0 + 204, ry0 + 193, (44, 38, 50))
    # scrollbar track
    sx = LEFT[2] - 16
    bg.rect(sx, LEFT[1] + 9, sx + 5, LEFT[3] - 9, INK)
    bg.rect(sx + 1, LEFT[1] + 10, sx + 4, LEFT[3] - 10, (34, 28, 40))
    save(bg, 'bg.png')
    for rid in range(6):
        save(portrait_frame(rid), f'tile-{KEYS[rid]}.png')
    save(desk_slot(), 'slot.png')
    save(action_button('ALL TO WORK', GOLD, 108, 16, dark=True), 'btn-allwork.png')
    save(action_button('ALL TO CASINO', (230, 70, 90), 108, 16), 'btn-allrest.png')
    save(plate(76, 16, (110, 200, 90), False), 'tab.png')
    save(plate(76, 16, (110, 200, 90), True), 'tab-on.png')
    for key, label, col, dark in (('assign', 'ASSIGN DESK', (110, 200, 90), False), ('work', 'WORK', GOLD, True),
                                  ('rest', 'REST', (230, 70, 90), False), ('stop', 'UNASSIGN', (96, 92, 110), False),
                                  ('view', 'VIEW OFFICE', (60, 170, 150), False)):
        save(action_button(label, col, dark=dark), f'btn-{key}.png')
        save(action_button(label, (70, 66, 80)), f'btn-{key}-off.png')
    lay['grid'] = {'x': gx0, 'y': gy0, 'cols': 7, 'rows': 4, 'w': TILE_W, 'h': TILE_H, 'gap': 4,
                   'scroll': [sx + 1, LEFT[1] + 10, sx + 4, LEFT[3] - 10]}
    lay['tabs'] = [{'key': k, 'label': l, 'x': 8 + i * 80, 'y': 40, 'w': 76, 'h': 16}
                   for i, (k, l) in enumerate((('all', 'ALL'), ('working', 'WORKING'), ('casino', 'CASINO'),
                                                ('ready', 'READY'), ('idle', 'IDLE')))]
    lay['card'] = [rx0, ry0]
    ix = rx0 + 118
    lay['info'] = {'x': ix, 'y': ry0, 'w': 86}
    lay['buttons'] = {k: {'x': ix, 'y': ry0 + 84 + i * 20, 'w': 86, 'h': 18}
                      for i, k in enumerate(('assign', 'work', 'rest', 'stop', 'view'))}
    lay['global'] = {'allwork': {'x': RIGHT[0], 'y': 40, 'w': 108, 'h': 16},
                     'allrest': {'x': RIGHT[0] + 112, 'y': 40, 'w': 108, 'h': 16}}
    lay['picker'] = {'x': rx0, 'y': ry0 + 202, 'label': 62, 'row': 26, 'w': 24, 'h': 20, 'gap': 4,
                     'paths': ['memecoin', 'pumpfun', 'classic']}
    lay['footer'] = {'y': LEFT[3] - 12, 'x0': gx0, 'x1': gx0 + 7 * (TILE_W + 4) - 4}
    lay['skills'] = {'x': rx0, 'y': ry0 + 202, 'w': 204}
    lay['rows'] = {'status': ry0 + 8, 'rate': ry0 + 22, 'desk': ry0 + 42, 'bar': [ix + 3, ry0 + 65, ix + 82, ry0 + 67], 'time': ry0 + 73}
    (OUT / 'layout.json').write_text(json.dumps(lay))


if __name__ == '__main__':
    build()
    print('frogs screen ok')
