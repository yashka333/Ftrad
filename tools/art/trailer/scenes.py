"""Static trailer sets, built once: title wall, recruit stage, pack, cards, street, boss hall."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image

from fx import W, H, glow_layer, big_mask, stamp, BAYER1
from px2 import INK, Canvas, mix, sh
from menu_kit import (GOLD, GOLD_HI, GOLD_LO, Lights, brick_wall, enamel_plate, frame_card, lit, bloom, text_mask,
                      wood_planks, draw_text)
import menu_scenes as S
from menu2 import wall, picture_lamp

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / 'client/src/assets'

RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
RARITY_COL = {'common': (201, 205, 214), 'uncommon': (110, 224, 106), 'rare': (74, 168, 255),
              'epic': (182, 111, 255), 'legendary': (255, 180, 46), 'mythic': (255, 77, 109)}
NEON, NEON_HI = (110, 236, 90), (232, 255, 214)


def spr(name):
    return np.array(Image.open(A / name).convert('RGBA'))


def shade(img, f):
    out = img.copy()
    out[..., :3] = np.clip(out[..., :3].astype(float) * f, 0, 255).astype(np.uint8)
    return out


def composite(base: Canvas, e: Canvas):
    a = e.a[..., 3:4] / 255
    base.a[..., :3] = (base.a[..., :3] * (1 - a) + e.a[..., :3] * a).astype(np.uint8)


# ================================================================ title wall
def neon_sign(scale=3, cy=58, text='FROG TRADERS'):
    """FROG TRADERS in neon tubes. Returns (backing RGBA, lit tubes RGBA, glow RGBA)."""
    m = big_mask(text, 'title', scale)
    h, w = m.shape
    x0, y0 = W // 2 - w // 2, cy - h // 2
    full = np.zeros((H, W), bool)
    full[y0:y0 + h, x0:x0 + w] = m
    pad = np.pad(full, 1)
    inner = full & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    pad2 = np.pad(inner, 1)
    core = inner & pad2[:-2, 1:-1] & pad2[2:, 1:-1] & pad2[1:-1, :-2] & pad2[1:-1, 2:]
    heads = np.zeros((H, W), bool)
    heads_core = np.zeros((H, W), bool)
    for fx in (x0 - 40, x0 + w + 38):
        fy = cy
        for (ox, oy, r) in ((-9, -9, 6), (9, -9, 6)):
            for a in range(0, 360, 6):
                for rr in (r, r - 1):
                    X = fx + ox + round(math.cos(math.radians(a)) * rr)
                    Y = fy + oy + round(math.sin(math.radians(a)) * rr)
                    heads[Y, X] = True
            heads_core[fy + oy - 1:fy + oy + 2, fx + ox:fx + ox + 2] = True
        for a in range(200, 341, 4):
            for rr in (16, 15):
                heads[fy + 3 + round(-math.sin(math.radians(a)) * rr * .55), fx + round(math.cos(math.radians(a)) * rr)] = True
        for a in range(0, 181, 4):
            for rr in (16, 15):
                heads[fy - 1 + round(math.sin(math.radians(a)) * rr * .62), fx + round(math.cos(math.radians(a)) * rr)] = True
        heads_core[fy + 3, fx - 6:fx + 7] = True
    tubes = full | heads
    back = np.zeros((H, W, 4), np.uint8)
    sh_m = np.zeros_like(tubes)
    sh_m[4:, 4:] = tubes[:-4, :-4]
    back[sh_m & ~tubes] = (8, 6, 8, 200)
    back[tubes] = (44, 70, 40, 255)
    back[inner] = (60, 96, 54, 255)
    lit_ = np.zeros((H, W, 4), np.uint8)
    lit_[tubes] = (*NEON, 255)
    lit_[core | heads_core | (inner & ~core)] = (*mix(NEON, NEON_HI, .55), 255)
    lit_[core | heads_core] = (*NEON_HI, 255)
    glow = glow_layer(tubes.astype(float), NEON, radius=7, power=2.0, levels=(120, 70, 30))
    return back, lit_, glow


def title_set():
    lamps = [(120, 22), (520, 22)]
    bg = wall(21, lamps, logo=(W // 2, 60))
    e = Canvas(W, H)
    for (lx, ly) in lamps:
        picture_lamp(bg, e, lx, ly)
    rng = np.random.default_rng(4)
    floor_y = 318
    fl = Canvas(W, H)
    wood_planks(fl, 0, floor_y, W - 1, H - 1, rng, cols=[(70, 44, 30), (64, 40, 28), (76, 48, 32), (58, 36, 26)])
    fl.hline(0, W - 1, floor_y, INK)
    Lf = Lights(W, H, [0.35, 0.3, 0.32])
    Lf.point(W / 2, floor_y - 40, 330, [1.0, 0.8, 0.55], 0.6)
    flit = lit(fl, Lf)
    m = flit.a[..., 3] > 0
    bg.a[m] = flit.a[m]
    composite(bg, e)
    # frog line-up, common to mythic
    sprites = [spr(f'frogs/worker-{r}.png') for r in RARITIES]
    gap = 14
    total = sum(s.shape[1] for s in sprites) + gap * 5
    x = W // 2 - total // 2
    lineup = []
    for r, s in zip(RARITIES, sprites):
        lineup.append((r, s, x, floor_y + 28 - s.shape[0]))
        x += s.shape[1] + gap
    for (_, s, x, y) in lineup:
        cx = x + s.shape[1] // 2
        for yy in range(floor_y + 24, floor_y + 31):
            for xx in range(cx - 22, cx + 23):
                d = ((xx - cx) / 22) ** 2 + ((yy - floor_y - 27.5) / 3.5) ** 2
                if d < 1 and BAYER1[yy, xx] < .8 * (1 - d):
                    bg.a[yy, xx, :3] = (bg.a[yy, xx, :3] * .45).astype(np.uint8)
    return bg.a, lineup


# ================================================================ recruit stage
def recruit_set():
    rng = np.random.default_rng(9)
    c, e = Canvas(W, H), Canvas(W, H)
    desk_y = H - 52
    for x in range(W):
        fold = x % 12
        col = (90, 30, 70) if fold in (0, 1, 2) else (122, 44, 98) if fold in (3, 4, 5, 6) else (104, 36, 84)
        c.vline(x, 0, desk_y, col)
    for x in range(0, W, 12):
        c.vline(x, 0, desk_y, (60, 18, 48))
    # valance with gold fringe
    for x in range(W):
        yb = 18 + int(4 * math.sin(x / 40 * math.pi) ** 2)
        c.vline(x, 0, yb, (140, 30, 50) if (x // 6) % 2 else (128, 26, 44))
        c.px(x, yb + 1, GOLD if x % 3 else GOLD_LO)
        if x % 4 == 0:
            c.vline(x, yb + 2, yb + 4, GOLD_LO)
    c.rect(0, desk_y, W - 1, H - 1, INK)
    wood_planks(c, 0, desk_y + 1, W - 1, desk_y + 9, rng, cols=[(120, 74, 44), (112, 70, 42), (128, 80, 48)], plank=5)
    c.hline(0, W - 1, desk_y + 1, (170, 116, 72))
    c.rect(0, desk_y + 10, W - 1, H - 1, (80, 48, 30))
    for x in range(10, W, 46):
        c.box(x, desk_y + 14, x + 38, H - 5, (80, 48, 30), (104, 64, 40), (60, 34, 20))
    L = Lights(W, H, [0.26, 0.22, 0.32])
    L.spot(W / 2, -10, 0.42, 420, [1.0, 0.82, 0.62], 1.0)
    L.point(W / 2, 190, 200, [1.0, 0.5, 0.85], 0.35)
    out = lit(c, L, e)
    return out.a, desk_y


def make_pack():
    w, h = 80, 112
    c = Canvas(w, h)
    base = (120, 66, 200)
    for y in range(h):
        t = y / h
        col = mix(sh(base, 1.25), sh(base, .7), t)
        c.hline(0, w - 1, y, col)
    for y in range(h):
        for x in range(w):
            d = (x + y * .6)
            if 30 < d % 70 < 40:
                c.px(x, y, mix(c.get(x, y), (255, 255, 255), .28))
            elif 42 < d % 70 < 45:
                c.px(x, y, mix(c.get(x, y), (255, 255, 255), .16))
    # crimped seals
    for (y0, y1) in ((0, 9), (h - 10, h - 1)):
        c.rect(0, y0, w - 1, y1, sh(base, 1.45))
        for x in range(0, w, 3):
            c.vline(x, y0, y1, sh(base, 1.05))
        for x in range(0, w, 4):
            c.px(x, y0 if y0 == 0 else y1, (0, 0, 0, 0)[:3])
    c.a[0, ::4, 3] = 0
    c.a[h - 1, ::4, 3] = 0
    # emblem: frog face in a cream medallion
    cx, cy, r = w // 2, 46, 23
    c.ellipse(cx, cy, r + 1, r + 1, INK)
    c.ellipse(cx, cy, r, r, (240, 230, 206))
    c.ellipse(cx, cy, r - 3, r - 3, (40, 26, 64))
    head = spr('frogs/worker-mythic.png')[:44]
    hw = head.shape[1]
    sub = Canvas(w, h)
    sub.blit(head, cx - hw // 2, cy - 22)
    yy, xx = np.mgrid[0:h, 0:w]
    inside = (xx - cx) ** 2 + (yy - cy) ** 2 <= (r - 3) ** 2
    m = inside & (sub.a[..., 3] > 0)
    c.a[m] = sub.a[m]
    m = text_mask('FROG', 'head')
    x0 = cx - m.shape[1] // 2
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
        c.mask(m, x0 + dx, 74 + dy, INK)
    c.mask(m, x0, 74, (255, 255, 255))
    m2 = text_mask('TRADERS PACK', 'body')
    c.mask(m2, cx - m2.shape[1] // 2 + 1, 92, INK)
    c.mask(m2, cx - m2.shape[1] // 2, 91, GOLD_HI)
    # outline
    a = c.a[..., 3] > 0
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    c.a[edge, :3] = INK
    return c.a, 10   # tear line


def card_back_img():
    w, h = 96, 140
    c = Canvas(w, h)
    frame_card(c, w, h, GOLD)
    S.card_back(c, 9, 9, w - 18, h - 18, gold=True)
    cx, cy = w // 2, h // 2
    c.ellipse(cx, cy, 15, 15, INK)
    c.ellipse(cx, cy, 14, 14, GOLD)
    c.ellipse(cx, cy, 11, 11, (30, 26, 34))
    m = big_mask('?', 'title', 1)
    c.mask(m, cx - m.shape[1] // 2, cy - m.shape[0] // 2, GOLD_HI)
    return c.a


def card_front_img(rarity='mythic', label='MYTHIC KING'):
    w, h = 96, 140
    c = Canvas(w, h)
    col = RARITY_COL[rarity]
    frame_card(c, w, h, col)
    for y in range(8, h - 8):
        for x in range(8, w - 8):
            d = math.hypot((x - w / 2) / (w / 2), (y - 58) / 70)
            c.px(x, y, mix(sh(col, .55), (24, 12, 22), min(1, d * 1.1)))
    s = spr(f'frogs/worker-{rarity}.png')
    c.blit(s, w // 2 - s.shape[1] // 2 + 1, 12)
    enamel_plate(c, 10, h - 28, w - 11, h - 12, col)
    m = text_mask(label, 'body')
    c.mask(m, w // 2 - m.shape[1] // 2 + 1, h - 23, INK)
    c.mask(m, w // 2 - m.shape[1] // 2, h - 24, (255, 255, 255))
    return c.a


# ================================================================ street
def street_set():
    rng = np.random.default_rng(31)
    c, e = Canvas(W, H), Canvas(W, H)
    street = 300
    for y in range(street):
        col = mix((12, 12, 32), (58, 36, 76), y / street)
        c.hline(0, W - 1, y, col)
        e.hline(0, W - 1, y, col)
    for _ in range(70):
        sx, sy = int(rng.integers(0, W)), int(rng.integers(0, 120))
        e.px(sx, sy, (210, 210, 240) if rng.random() < .7 else (150, 150, 190))
    e.ellipse(588, 34, 11, 11, (236, 230, 206))
    e.ellipse(593, 30, 10, 10, mix((12, 12, 32), (58, 36, 76), 30 / street))
    x = 0
    while x < W:
        bw = int(rng.integers(10, 26))
        bh = int(rng.integers(60, 150))
        e.rect(x, street - bh, x + bw, street, (30, 26, 54))
        for wy in range(street - bh + 4, street - 10, 6):
            for wx in range(x + 2, x + bw - 2, 5):
                if rng.random() < .16:
                    e.px(wx, wy, (200, 170, 110))
        x += bw + 1
    specs = [
        dict(x0=14, w=192, top=78, wall=(126, 72, 52), neon=(255, 120, 50), label='MEMECOIN', style='brick'),
        dict(x0=224, w=192, top=52, wall=(70, 60, 98), neon=(255, 70, 170), label='PUMP.FUN', style='concrete'),
        dict(x0=434, w=192, top=70, wall=(132, 126, 116), neon=(60, 210, 176), label='CLASSIC', style='stone'),
    ]
    windows = []
    signs = []
    for sp in specs:
        x0, w, top, wl = sp['x0'], sp['w'], sp['top'], sp['wall']
        e.a[top:street + 1, x0:x0 + w, 3] = 0
        c.rect(x0, top, x0 + w - 1, street, INK)
        c.rect(x0 + 1, top + 1, x0 + w - 2, street, wl)
        c.rect(x0 - 3, top - 4, x0 + w + 2, top, sh(wl, .7))
        c.hline(x0 - 3, x0 + w + 2, top - 4, sh(wl, 1.3))
        if sp['style'] == 'brick':
            for y in range(top + 3, street, 4):
                off = 4 if (y // 4) % 2 else 0
                for xx in range(x0 + 2 + off, x0 + w - 2, 8):
                    c.vline(xx, y, y + 2, sh(wl, .78))
                c.hline(x0 + 1, x0 + w - 2, y + 3, sh(wl, .85))
        elif sp['style'] == 'concrete':
            for y in range(top + 8, street, 10):
                c.hline(x0 + 1, x0 + w - 2, y, sh(wl, .8))
            for xx in range(x0 + 24, x0 + w - 4, 24):
                c.vline(xx, top + 1, street, sh(wl, .86))
        else:
            for xx in range(x0 + 6, x0 + w - 4, 12):
                c.vline(xx, top + 14, street - 4, sh(wl, 1.2))
                c.vline(xx + 1, top + 14, street - 4, sh(wl, .8))
            c.rect(x0 + 1, top + 4, x0 + w - 2, top + 9, sh(wl, 1.15))
            c.hline(x0 + 1, x0 + w - 2, top + 10, sh(wl, .7))
        for wy in range(top + 16, street - 88, 15):
            for wx in range(x0 + 10, x0 + w - 12, 15):
                c.rect(wx - 1, wy - 1, wx + 8, wy + 10, INK)
                c.rect(wx, wy, wx + 7, wy + 9, (22, 22, 34))
                c.hline(wx, wx + 7, wy + 5, (16, 16, 26))
                if rng.random() < .42:
                    warm = [(255, 214, 140), (250, 190, 110), (140, 220, 230), (255, 226, 170)][int(rng.integers(0, 4))]
                    windows.append((wx, wy, warm, rng.uniform(0, 6.28), rng.random() < .15))
        # door and awning
        dx = x0 + w // 2
        c.rect(dx - 15, street - 34, dx + 14, street, INK)
        e.rect(dx - 13, street - 32, dx + 12, street - 1, mix(sp['neon'], (255, 230, 180), .55))
        e.vline(dx, street - 32, street - 1, sh(sp['neon'], .55))
        for xx in range(dx - 26, dx + 26):
            col = sp['neon'] if (xx // 6) % 2 == 0 else (236, 228, 206)
            c.vline(xx, street - 44, street - 38, sh(col, .75))
        c.hline(dx - 26, dx + 25, street - 45, INK)
        # neon sign
        m = text_mask(sp['label'], 'head')
        sx = dx - m.shape[1] // 2
        sy = street - 70
        bx0, by0, bx1, by1 = sx - 6, sy - 4, sx + m.shape[1] + 5, sy + m.shape[0] + 3
        c.rect(bx0 - 1, by0 - 1, bx1 + 1, by1 + 1, INK)
        c.rect(bx0, by0, bx1, by1, (16, 12, 20))
        c.mask(m, sx, sy, sh(sp['neon'], .35))
        rim = np.zeros((H, W), bool)
        rim[by0, bx0:bx1 + 1] = rim[by1, bx0:bx1 + 1] = True
        rim[by0:by1 + 1, bx0] = rim[by0:by1 + 1, bx1] = True
        letters = np.zeros((H, W), bool)
        letters[sy:sy + m.shape[0], sx:sx + m.shape[1]] = m
        signs.append(dict(spec=sp, rim=rim, letters=letters, cx=dx, top=top, box=(bx0, by0, bx1, by1)))
    # wet street
    for y in range(street + 1, H):
        c.hline(0, W - 1, y, (34, 32, 42) if (y - street) % 9 else (46, 44, 56))
    c.hline(0, W - 1, street, (90, 86, 100))
    c.hline(0, W - 1, street + 1, INK)
    for x in range(0, W, 40):
        c.rect(x + 6, street + 30, x + 22, street + 31, (70, 68, 80))
    L = Lights(W, H, [0.40, 0.38, 0.55])
    for s in signs:
        L.point(s['cx'], street - 60, 90, [v / 255 for v in s['spec']['neon']], 0.8)
        L.point(s['cx'], street - 10, 60, [1.0, 0.85, 0.6], 0.6)
    base = lit(c, L, e)
    bloom(base, e, .35, 2)
    for s in signs:
        g = glow_layer((s['letters'] | s['rim']).astype(float), s['spec']['neon'], radius=6, power=2.0, levels=(110, 60, 26))
        bx0, by0, bx1, by1 = s['box']
        g[by0 + 1:by1, bx0 + 1:bx1, 3] = 0          # keep the plate dark so letters read
        s['glow'] = g
    return base.a, windows, signs, street


# ================================================================ boss hall
BOSS_KEYS = ['orig', 'blue', 'purple', 'green']
BOSS_X = [W // 2 - 195, W // 2 - 65, W // 2 + 65, W // 2 + 195]
PED_TOP = 252


def boss_hall():
    """Five lit versions of the hall: 0..4 spotlights on, each with its boss placed."""
    rng = np.random.default_rng(77)
    alb = Canvas(W, H)
    wood_planks(alb, 0, 0, W - 1, 300, rng, cols=[(54, 30, 24), (48, 27, 22), (58, 33, 26), (44, 25, 20)], vertical=True, plank=10)
    for y in (60, 200):
        alb.rect(0, y, W - 1, y + 4, (80, 52, 30))
        alb.hline(0, W - 1, y, (130, 92, 52))
    alb.rect(0, 300, W - 1, H - 1, (30, 22, 30))
    for y in range(301, H):
        for x in range(W):
            if (x // 16 + y // 8) % 2:
                alb.px(x, y, (36, 26, 36))
    alb.hline(0, W - 1, 300, INK)
    busts = [np.array(Image.open(Path(__file__).parent / f'build/boss-{k}-clean.png').convert('RGBA')) for k in BOSS_KEYS]
    plates = ['#001', '#077', '#169', '#250']
    for i, x in enumerate(BOSS_X):
        # pedestal
        alb.rect(x - 52, PED_TOP, x + 51, 300, INK)
        alb.rect(x - 51, PED_TOP + 1, x + 50, 299, (60, 50, 62))
        alb.rect(x - 55, PED_TOP - 6, x + 54, PED_TOP, INK)
        alb.rect(x - 54, PED_TOP - 5, x + 53, PED_TOP - 1, (92, 80, 96))
        alb.hline(x - 54, x + 53, PED_TOP - 5, (140, 126, 146))
        alb.vline(x - 50, PED_TOP + 1, 299, (84, 72, 88))
        alb.vline(x + 49, PED_TOP + 1, 299, (40, 32, 44))
        m = text_mask(plates[i], 'body')
        alb.rect(x - 18, PED_TOP + 14, x + 17, PED_TOP + 28, INK)
        alb.rect(x - 17, PED_TOP + 15, x + 16, PED_TOP + 27, GOLD_LO)
        alb.hline(x - 17, x + 16, PED_TOP + 15, GOLD_HI)
        alb.mask(m, x - m.shape[1] // 2, PED_TOP + 18, (40, 26, 10))
    variants = []
    for k in range(5):
        a2 = Canvas(W, H)
        a2.a = alb.a.copy()
        for i in range(k):
            b = busts[i]
            a2.blit(b, BOSS_X[i] - b.shape[1] // 2, PED_TOP - 6 - b.shape[0] + 4)
        L = Lights(W, H, [0.24, 0.2, 0.27])
        for i in range(k):
            L.spot(BOSS_X[i], -30, 0.24, 560, [1.0, 0.86, 0.62], 1.9)
            L.point(BOSS_X[i], 200, 70, [1.0, 0.85, 0.6], 0.5)
        variants.append(lit(a2, L).a)
    return variants, busts
