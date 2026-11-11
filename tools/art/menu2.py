"""Home and Shop screens, rebuilt at office quality: lit wall, picture lamps,
framed cards holding small lit scenes, brass and metal UI, real pixel fonts.

Outputs client/src/assets/home/ and client/src/assets/shop/ (bg, neon, cards, tiles, layout).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from px2 import INK, Canvas, dither, mix, sh
from menu_kit import (GOLD, GOLD_HI, GOLD_LO, MUTED, TEXT, Lights, bloom, brass_inset, brick_wall, coin,
                      draw_text, enamel_plate, frame_card, gradient_text, lit, metal_plate, text_mask, text_size,
                      wood_planks)
import menu_scenes as S

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'client/src/assets'
W, H = 640, 360
PHANTOM = (171, 159, 242)


def render_scene(fn, w, h, seed, **swap):
    rng = np.random.default_rng(seed)
    alb, L, e, meta = fn(w, h, rng)
    out = lit(alb, L, e)
    bloom(out, e, .45, 2)
    return out, meta


# ------------------------------------------------------------------ header
def phantom_ghost(c, cx, cy):
    white, shade, eye = (255, 255, 255), (226, 220, 252), (60, 49, 91)
    for y in range(cy - 7, cy + 4):
        half = int(round(7 * (1 - ((cy - 2 - y) / 5.5) ** 2) ** .5)) if y < cy - 2 else 7
        c.hline(cx - half, cx + half, y, white)
        c.px(cx + half, y, shade)
    for x in range(cx - 7, cx + 8):
        k = (x - (cx - 7)) % 5
        if k in (0, 1, 2, 3):
            c.px(x, cy + 4, white)
        if k in (1, 2):
            c.px(x, cy + 5, white)
    for ex in (cx - 1, cx + 3):
        c.rect(ex, cy - 4, ex + 1, cy - 1, eye)


def button(c, x0, y0, x1, y1, col):
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, sh(col, .55))
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 3, col)
    c.hline(x0 + 2, x1 - 2, y0 + 1, sh(col, 1.35))
    c.vline(x0 + 1, y0 + 2, y1 - 3, sh(col, 1.15))
    c.vline(x1 - 1, y0 + 2, y1 - 3, sh(col, .8))


def gear(c, cx, cy, col=(206, 202, 214)):
    for k in range(8):
        a = k * math.pi / 4
        x, y = round(cx + math.cos(a) * 6), round(cy + math.sin(a) * 6)
        c.rect(x - 1, y - 1, x + 1, y + 1, col)
    c.ellipse(cx, cy, 5, 5, col)
    c.ellipse(cx, cy, 2, 2, (70, 66, 80))
    c.px(cx - 3, cy - 3, (250, 250, 255))


def wallet_glyph(c, x, y):
    c.rect(x, y + 2, x + 13, y + 11, INK)
    c.rect(x + 1, y + 3, x + 12, y + 10, (150, 120, 230))
    c.hline(x + 1, x + 12, y + 3, (190, 166, 255))
    c.rect(x + 8, y + 5, x + 13, y + 8, INK)
    c.rect(x + 9, y + 6, x + 12, y + 7, (100, 70, 180))
    c.px(x + 10, y + 6, GOLD_HI)


def header(c: Canvas, title=None, back=False):
    """Top bar. Home: balance on the left. Sub screens: back button and title on the left."""
    lay = {}
    metal_plate(c, -1, -1, W, 32, (54, 50, 62))
    for x in range(0, W, 2):
        c.px(x, 33, (0, 0, 0), 170)
        c.px(x + 1, 34, (0, 0, 0), 90)
    x = 6
    if title or back:
        button(c, 5, 4, 32, 28, (96, 92, 110))
        for k in range(5):
            c.vline(12 + k, 15 - k, 15 + k, TEXT)
        c.rect(16, 14, 25, 16, TEXT)
        lay['back'] = [5, 4, 32, 28]
        if title:
            gradient_text(c, title, 42, 8, TEXT, (200, 190, 176), 'title')
        x = 300
    brass_inset(c, x, 4, x + 132, 28)
    coin(c, x + 13, 16, 6)
    lay['coin'] = [x + 13, 16]
    lay['balance'] = [x + 24, 7, x + 100, 25]
    draw_text(c, '487,140', x + 26, 9, GOLD_HI, 'title')
    draw_text(c, '$FROG', x + 128, 13, MUTED, 'body', align='right')
    # phantom, settings, wallet
    button(c, 440, 4, 467, 28, PHANTOM)
    phantom_ghost(c, 453, 15)
    lay['phantom'] = [440, 4, 467, 28]
    button(c, 472, 4, 497, 28, (96, 92, 110))
    gear(c, 484, 15)
    lay['settings'] = [472, 4, 497, 28]
    button(c, 502, 4, 635, 28, (92, 70, 160))
    wallet_glyph(c, 509, 9)
    lay['wallet'] = [502, 4, 635, 28]
    lay['address'] = [528, 9]      # drawn live: the connected wallet
    return lay


# --------------------------------------------------------------- the wall
def wall(seed, lamps, logo=None):
    """Lit brick lobby wall with picture lamps above every card."""
    rng = np.random.default_rng(seed)
    c = Canvas(W, H)
    brick_wall(c, 0, 0, W - 1, H - 1, rng, bricks=[(104, 56, 46), (96, 52, 42), (112, 62, 50), (88, 48, 40), (100, 58, 48)],
               mortar=(46, 34, 34))
    # damp streaks
    for (cx, wd) in [(90, 16), (330, 22), (560, 14)]:
        for y in range(36, 160):
            for x in range(cx - wd, cx + wd):
                if dither(x, y, .35 * (1 - (y - 36) / 124) * (1 - abs(x - cx) / wd)):
                    c.px(x, y, (30, 22, 24), 110)
    e = Canvas(W, H)
    L = Lights(W, H, [0.20, 0.18, 0.24])
    for (lx, ly) in lamps:
        L.point(lx, ly, 160, [1.0, 0.78, 0.5], 0.95, cone=True)
    if logo:
        L.point(logo[0], logo[1], 230, [0.45, 1.0, 0.4], 0.55, squash=0.45)
    out = lit(c, L, e)
    return out


def picture_lamp(c: Canvas, e: Canvas, cx, y):
    """Brass picture light mounted on the wall above a card."""
    c.rect(cx - 2, y - 7, cx + 1, y - 2, GOLD_LO)
    c.px(cx - 1, y - 6, GOLD_HI)
    c.rect(cx - 16, y - 2, cx + 15, y + 2, INK)
    c.rect(cx - 15, y - 1, cx + 14, y + 1, GOLD)
    c.hline(cx - 15, cx + 14, y - 1, GOLD_HI)
    e.hline(cx - 13, cx + 12, y + 2, (255, 238, 196))
    e.hline(cx - 11, cx + 10, y + 3, (255, 214, 150), 160)


def neon_logo(c: Canvas, n: Canvas, cx, y):
    from PIL import ImageFont
    m = text_mask('FROGOTRADERZ', 'title')
    m = np.kron(m, np.ones((2, 2), bool))
    h, w = m.shape
    x0 = cx - w // 2
    pad = np.pad(m, 1)
    edge = m & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    core = m & ~edge
    shm = np.zeros_like(m)
    shm[3:, 3:] = m[:-3, :-3]
    c.mask(shm & ~m, x0, y, (12, 8, 10), 190)
    c.mask(m, x0, y, (44, 70, 40))
    c.mask(core, x0, y, (60, 96, 54))
    n.mask(edge, x0, y, (110, 236, 90))
    n.mask(core, x0, y, (232, 255, 214))
    # mounting rail and brackets
    for bx in (x0 + 10, x0 + w // 2, x0 + w - 10):
        c.rect(bx - 1, y + h // 2 - 3, bx + 1, y + h // 2 + 3, (70, 70, 80))
    # neon frog heads either side
    for fx in (x0 - 24, x0 + w + 22):
        fy = y + h // 2
        for (ox, oy, r) in ((-6, -6, 4), (6, -6, 4)):
            for a in range(0, 360, 12):
                n.px(fx + ox + round(math.cos(math.radians(a)) * r), fy + oy + round(math.sin(math.radians(a)) * r), (110, 236, 90))
            n.px(fx + ox + 1, fy + oy, (232, 255, 214))
        for a in range(200, 341, 8):
            n.px(fx + round(math.cos(math.radians(a)) * 11), fy + 2 + round(-math.sin(math.radians(a)) * 6), (110, 236, 90))
        for a in range(0, 181, 8):
            n.px(fx + round(math.cos(math.radians(a)) * 11), fy - 1 + round(math.sin(math.radians(a)) * 7), (110, 236, 90))
        n.hline(fx - 4, fx + 4, fy + 2, (232, 255, 214))
    return [x0, y, x0 + w - 1, y + h - 1]


# ---------------------------------------------------------------- cards
def make_card(key, title, lines, footer, scene_fn, w, h, accent, seed, art_h, blink_variant=False):
    c = Canvas(w, h)
    frame_card(c, w, h, accent)
    enamel_plate(c, 10, 10, w - 11, 28, accent)
    gradient_text(c, title, w // 2, 13, (255, 255, 255), (222, 214, 204), 'head',
                  align='center')
    ax, ay, aw = 10, 32, w - 20
    c.rect(ax - 1, ay - 1, ax + aw, ay + art_h, INK)
    art, meta = render_scene(scene_fn, aw, art_h, seed)
    # frame and text are lit by the picture lamp above the card
    L = Lights(w, h, [0.62, 0.58, 0.62])
    L.point(w / 2, -8, h * 0.95, [0.55, 0.45, 0.3], 1.0, cone=True)
    c.a = L.apply(c.a)
    c.blit(art.a, ax, ay)
    # inner shadow on the art window edges
    for x in range(ax, ax + aw):
        c.px(x, ay, (0, 0, 0), 140)
        c.px(x, ay + 1, (0, 0, 0), 70)
    ty = ay + art_h + 6
    for i, ln in enumerate(lines):
        draw_text(c, ln, w // 2, ty + i * 9, (214, 204, 190), 'body', shadow=INK, align='center')
    fy = h - 30
    brass_inset(c, 14, fy, w - 15, fy + 18)
    c.rect(17, fy + 3, 21, fy + 15, accent)
    c.vline(17, fy + 3, fy + 15, sh(accent, 1.3))
    if footer:
        draw_text(c, footer, w // 2 + 4, fy + 6, TEXT, 'body', align='center')
    out_meta = {'foot': [w // 2 + 4, fy + 6]}
    for k, v in meta.items():
        if isinstance(v, list) and v and isinstance(v[0], list):
            out_meta[k] = [[p[0] + ax, p[1] + ay] + p[2:] for p in v]
        elif isinstance(v, list):
            out_meta[k] = [v[0] + ax, v[1] + ay]
    out_meta['art'] = [ax, ay, ax + aw - 1, ay + art_h - 1]
    blink = None
    if blink_variant:
        orig = S.sprite

        def closed(name):
            spr = orig(name)
            return S.closed_eyes(spr) if 'mythic' in name else spr
        S.sprite = closed
        try:
            art2, _ = render_scene(scene_fn, aw, art_h, seed)
        finally:
            S.sprite = orig
        blink = Canvas(w, h)
        blink.a = c.a.copy()
        blink.blit(art2.a, ax, ay)
        # restore the text and window shading drawn over the art
        for x in range(ax, ax + aw):
            blink.px(x, ay, (0, 0, 0), 140)
            blink.px(x, ay + 1, (0, 0, 0), 70)
    return c, out_meta, blink


def make_action_card(key, label, scene_fn, w, h, accent, seed, art_h):
    """Shop-style card: a big lit picture and one big action button, nothing else."""
    c = Canvas(w, h)
    frame_card(c, w, h, accent)
    ax, ay, aw = 10, 10, w - 20
    L = Lights(w, h, [0.62, 0.58, 0.62])
    L.point(w / 2, -8, h * 0.95, [0.55, 0.45, 0.3], 1.0, cone=True)
    c.a = L.apply(c.a)
    c.rect(ax - 1, ay - 1, ax + aw, ay + art_h, INK)
    art, meta = render_scene(scene_fn, aw, art_h, seed)
    c.blit(art.a, ax, ay)
    for x in range(ax, ax + aw):
        c.px(x, ay, (0, 0, 0), 140)
        c.px(x, ay + 1, (0, 0, 0), 70)
    by0, by1 = ay + art_h + 6, h - 11
    button(c, 12, by0, w - 13, by1, accent)
    gradient_text(c, label, w // 2, (by0 + by1) // 2 - 7, (255, 255, 255), (232, 226, 218), 'title', align='center')
    out_meta = {}
    for k, v in meta.items():
        if isinstance(v, list) and v and isinstance(v[0], list):
            out_meta[k] = [[p[0] + ax, p[1] + ay] + p[2:] for p in v]
        elif isinstance(v, list):
            out_meta[k] = [v[0] + ax, v[1] + ay]
    out_meta['art'] = [ax, ay, ax + aw - 1, ay + art_h - 1]
    out_meta['button'] = [12, by0, w - 13, by1]
    return c, out_meta


def make_tile(key, title, sub, icon_fn, w, h, accent):
    c = Canvas(w, h)
    frame_card(c, w, h, accent)
    # icon well
    c.rect(10, 9, 10 + h - 20, h - 10, INK)
    c.rect(11, 10, 9 + h - 20, h - 11, sh(accent, .3))
    icon_fn(c, 10 + (h - 20) // 2, h // 2, accent)
    for k in range(5):
        c.vline(w - 18 + k, h // 2 - 5 + k, h // 2 + 5 - k, accent)
    L = Lights(w, h, [0.66, 0.62, 0.66])
    L.point(w / 2, -6, w * .7, [0.5, 0.42, 0.3], 1.0, cone=True)
    c.a = L.apply(c.a)
    draw_text(c, title, h + 2, 10, TEXT, 'head')
    draw_text(c, sub, h + 2, 28, MUTED, 'body')
    return c


def icon_boss(c, cx, cy, acc):
    # crown over a frog head silhouette in gold
    c.ellipse(cx - 6, cy - 2, 4, 4, INK); c.ellipse(cx + 6, cy - 2, 4, 4, INK)
    c.ellipse(cx, cy + 4, 11, 7, INK)
    c.ellipse(cx, cy + 4, 10, 6, (90, 160, 80))
    c.ellipse(cx - 6, cy - 2, 3, 3, (90, 160, 80)); c.ellipse(cx + 6, cy - 2, 3, 3, (90, 160, 80))
    c.ellipse(cx, cy + 6, 6, 3, (226, 214, 170))
    c.ellipse(cx - 6, cy - 2, 2, 2, (244, 240, 226)); c.ellipse(cx + 6, cy - 2, 2, 2, (244, 240, 226))
    c.px(cx - 5, cy - 2, INK); c.px(cx + 7, cy - 2, INK)
    c.hline(cx - 4, cx + 4, cy + 4, (60, 110, 54))
    c.poly([(cx - 8, cy - 6), (cx - 7, cy - 13), (cx - 3, cy - 9), (cx, cy - 15), (cx + 3, cy - 9), (cx + 7, cy - 13), (cx + 8, cy - 6)], GOLD)
    c.hline(cx - 8, cx + 8, cy - 6, GOLD_LO)
    c.px(cx, cy - 11, (230, 60, 60)); c.px(cx - 6, cy - 10, GOLD_HI)


def icon_casino(c, cx, cy, acc):
    # a little slot machine; the reels are animated on the home screen
    c.rect(cx - 10, cy - 12, cx + 8, cy + 12, INK)
    c.rect(cx - 9, cy - 11, cx + 7, cy + 11, (170, 30, 50))
    c.vline(cx - 9, cy - 11, cy + 11, (220, 70, 84))
    c.rect(cx - 9, cy - 11, cx + 7, cy - 8, (110, 16, 30))
    for k in range(4):
        c.px(cx - 7 + k * 4, cy - 10, GOLD_HI)
    c.rect(cx - 8, cy - 6, cx + 6, cy + 3, INK)
    c.rect(cx - 8, cy + 6, cx + 6, cy + 8, INK)
    c.hline(cx - 7, cx + 5, cy + 7, (200, 200, 212))
    c.vline(cx + 10, cy - 8, cy + 2, (200, 200, 212))
    c.ellipse(cx + 10, cy - 9, 2, 2, INK)
    c.px(cx + 10, cy - 9, (230, 50, 60))


def icon_invite(c, cx, cy, acc):
    x0, y0 = cx - 11, cy - 8
    c.rect(x0, y0, x0 + 22, y0 + 16, INK)
    c.rect(x0 + 1, y0 + 1, x0 + 21, y0 + 15, (240, 232, 214))
    c.line(x0 + 1, y0 + 1, x0 + 11, y0 + 9, (160, 150, 130))
    c.line(x0 + 21, y0 + 1, x0 + 11, y0 + 9, (160, 150, 130))
    c.rect(x0 + 15, y0 + 3, x0 + 19, y0 + 7, (200, 60, 60))  # stamp
    c.px(x0 + 17, y0 + 5, (255, 220, 200))
    c.ellipse(x0 + 18, y0 + 14, 5, 5, INK)
    c.ellipse(x0 + 18, y0 + 14, 4, 4, acc)
    c.hline(x0 + 16, x0 + 20, y0 + 14, (255, 255, 255)); c.vline(x0 + 18, y0 + 12, y0 + 16, (255, 255, 255))


# ----------------------------------------------------------------- build
def build_home():
    out = A / 'home'
    out.mkdir(parents=True, exist_ok=True)
    cw, ch, gap = 148, 220, 8
    total = 4 * cw + 3 * gap
    x0 = (W - total) // 2
    cy = 84
    lamps = [(x0 + i * (cw + gap) + cw // 2, cy - 4) for i in range(4)]
    bg = wall(1, lamps, logo=(W // 2, 52))
    e = Canvas(W, H)
    n = Canvas(W, H)
    lay = {'size': [W, H], 'hud': header(bg)}
    lay['logo'] = {'rect': neon_logo(bg, n, W // 2, 40)}
    draw_text(bg, 'AFK TRADING ON SOLANA', W // 2, 72, (255, 200, 120), 'body', align='center')
    specs = [
        ('frogs', 'FROGS', ['See your crew and what', 'they do. Rest them', 'in the casino.'], None, S.scene_frogs, (110, 200, 90), True),
        ('work', 'GO TO WORK', ['Pick an office and', 'start earning.'], '3 OFFICES', S.scene_work, (232, 108, 46), False),
        ('shop', 'SHOP', ['Recruit frogs and', 'get a boss.'], 'RECRUIT / BOSS', S.scene_shop, (240, 190, 80), False),
        ('market', 'MARKET', ['Trade Legendary and', 'Mythic frogs with', 'other players.'], None, S.scene_market, (60, 198, 168), False),
    ]
    cards = []
    for i, (key, title, lines, footer, fn, acc, blink) in enumerate(specs):
        cv, meta, bl = make_card(key, title, lines, footer, fn, cw, ch, acc, 10 + i, 118, blink)
        cv.save(out / f'card-{key}.png')
        if bl:
            bl.save(out / f'card-{key}-blink.png')
        x = x0 + i * (cw + gap)
        cards.append(dict(key=key, title=title, x=x, y=cy, w=cw, h=ch, accent=list(acc), meta=meta))
        picture_lamp(bg, e, x + cw // 2, cy - 5)
        for yy in range(cy + 3, cy + ch + 4):
            for xx in range(x + 3, x + cw + 4):
                if (xx + yy) % 2:
                    bg.px(xx, yy, (0, 0, 0), 150)
    lay['cards'] = cards
    tw, th = 198, 46
    tx0 = (W - (3 * tw + 2 * 10)) // 2
    tiles = []
    for i, (key, title, sub, icon, acc) in enumerate([
            ('casino', 'CASINO', 'Free. Tired frogs chill here', icon_casino, (230, 70, 90)),
            ('boss', 'BOSS FROGS', 'Announcement soon', icon_boss, (240, 190, 80)),
            ('invite', 'INVITE', 'Bring friends into the game', icon_invite, (90, 170, 240))]):
        tv = make_tile(key, title, sub, icon, tw, th, acc)
        tv.save(out / f'tile-{key}.png')
        x = tx0 + i * (tw + 10)
        meta = {'reels': [23 - 7, 23 - 5]} if key == 'casino' else {}
        tiles.append(dict(key=key, title=title, x=x, y=H - th - 6, w=tw, h=th, accent=list(acc), meta=meta))
    lay['tiles'] = tiles
    # self-lit bits of the wall (lamp bulbs) composited onto the background
    a = e.a[..., 3:4] / 255
    bg.a[..., :3] = (bg.a[..., :3] * (1 - a) + e.a[..., :3] * a).astype(np.uint8)
    bg.save(out / 'bg.png')
    n.save(out / 'logo-neon.png')
    (out / 'layout.json').write_text(json.dumps(lay))


def build_shop():
    out = A / 'shop'
    out.mkdir(parents=True, exist_ok=True)
    cw, ch, gap = 196, 212, 24
    total = 2 * cw + gap
    x0 = (W - total) // 2
    cy = 92
    lamps = [(x0 + i * (cw + gap) + cw // 2, cy - 4) for i in range(2)]
    bg = wall(2, lamps)
    e = Canvas(W, H)
    lay = {'size': [W, H], 'hud': header(bg, 'SHOP')}
    specs = [
        ('recruit', 'RECRUIT', S.scene_recruit, (176, 104, 255)),
        ('boss', 'PICK BOSS', S.scene_boss, (240, 190, 80)),
    ]
    cards = []
    for i, (key, label, fn, acc) in enumerate(specs):
        cv, meta = make_action_card(key, label, fn, cw, ch, acc, 30 + i, 150)
        cv.save(out / f'card-{key}.png')
        x = x0 + i * (cw + gap)
        cards.append(dict(key=key, title=label, x=x, y=cy, w=cw, h=ch, accent=list(acc), meta=meta))
        picture_lamp(bg, e, x + cw // 2, cy - 5)
        for yy in range(cy + 3, cy + ch + 4):
            for xx in range(x + 3, x + cw + 4):
                if (xx + yy) % 2:
                    bg.px(xx, yy, (0, 0, 0), 150)
    lay['cards'] = cards
    lay['tiles'] = []
    a = e.a[..., 3:4] / 255
    bg.a[..., :3] = (bg.a[..., :3] * (1 - a) + e.a[..., :3] * a).astype(np.uint8)
    bg.save(out / 'bg.png')
    (out / 'layout.json').write_text(json.dumps(lay))


if __name__ == '__main__':
    build_home()
    build_shop()
    print('ok')
