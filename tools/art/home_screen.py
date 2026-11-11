"""Home screen (the hub you land on after logging in), drawn as native pixel art.

Outputs client/src/assets/home/:
  bg.png          wall, HUD bar, logo glass (neon off), ticker housing
  logo-neon.png   lit neon tubes of the logo
  card-<k>.png    five big section cards (Frogs, Go to work, Fusion, Shop, Market)
  tile-<k>.png    four small tiles (Casino, Boss Frogs, Invite, Withdraw)
  layout.json     positions and animation anchors for home_engine.js
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from font import BIG, SMALL, render
from px2 import INK, Canvas, dither, mix, sh

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'client/src/assets'
OUT = A / 'home'
LIT = Path(__file__).parent / 'source/lit'
W, H = 640, 360
rng = np.random.default_rng(5)

GOLD, GOLD_HI, GOLD_LO = (236, 186, 72), (255, 226, 130), (170, 120, 40)
PANEL, PANEL_HI, PANEL_LO = (30, 26, 36), (58, 52, 66), (18, 16, 22)
INSET = (14, 12, 18)
TEXT, MUTED = (242, 231, 212), (168, 156, 146)
ACCENTS = {
    'frogs': (110, 200, 90), 'work': (232, 108, 46), 'fusion': (176, 104, 255),
    'shop': (240, 190, 80), 'market': (60, 198, 168),
    'casino': (230, 70, 90), 'boss': (240, 190, 80), 'invite': (90, 170, 240), 'withdraw': (126, 226, 84),
}


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def text(c: Canvas, s, x, y, col, font=SMALL, shadow=INK, scale=1):
    m = render(s, font)
    if scale > 1:
        m = np.kron(m, np.ones((scale, scale), bool))
    if shadow:
        c.mask(m, x + 1, y + 1, shadow)
    c.mask(m, x, y, col)
    return m.shape[1]


def text_w(s, font=SMALL, scale=1):
    return render(s, font).shape[1] * scale


def center_text(c, s, cx, y, col, font=SMALL, shadow=INK, scale=1):
    text(c, s, cx - text_w(s, font, scale) // 2, y, col, font, shadow, scale)


def bevel_frame(c: Canvas, x0, y0, x1, y1, accent, fill=PANEL):
    """Chunky game frame: ink, 2px bevelled accent rim, ink, panel."""
    c.rect(x0, y0, x1, y1, INK)
    hi, lo = sh(accent, 1.25), sh(accent, .62)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, accent)
    c.hline(x0 + 1, x1 - 1, y0 + 1, hi)
    c.vline(x0 + 1, y0 + 1, y1 - 1, hi)
    c.hline(x0 + 1, x1 - 1, y1 - 1, lo)
    c.vline(x1 - 1, y0 + 2, y1 - 1, lo)
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, INK)
    c.rect(x0 + 4, y0 + 4, x1 - 4, y1 - 4, fill)
    for (rx, ry) in ((x0 + 2, y0 + 2), (x1 - 2, y0 + 2), (x0 + 2, y1 - 2), (x1 - 2, y1 - 2)):
        c.px(rx, ry, GOLD_HI)


def inset(c: Canvas, x0, y0, x1, y1, fill=INSET):
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)
    c.hline(x0 + 1, x1 - 1, y1, (70, 62, 80))


# ------------------------------------------------------------------ icons
def coin_icon(c, x, y, r=6):
    c.ellipse(x, y, r, r, INK)
    c.ellipse(x, y, r - 1, r - 1, GOLD_LO)
    c.ellipse(x - .5, y - .5, r - 2, r - 2, GOLD)
    c.mask(render('F', SMALL), x - 1, y - 2, GOLD_LO)
    c.px(x - r + 2, y - 2, GOLD_HI); c.px(x - r + 3, y - 3, GOLD_HI)


def frog_face(c, x, y, s=1.0, skin=(110, 170, 80)):
    """Little frog head icon centred on x, y (about 20 px wide at s=1)."""
    lo, belly = sh(skin, .7), (226, 214, 170)
    c.ellipse(x - 6 * s, y - 5 * s, 4 * s, 4 * s, INK)
    c.ellipse(x + 6 * s, y - 5 * s, 4 * s, 4 * s, INK)
    c.ellipse(x, y + 1 * s, 10 * s, 7 * s, INK)
    c.ellipse(x, y + 1 * s, 9 * s, 6 * s, skin)
    c.ellipse(x - 6 * s, y - 5 * s, 3 * s, 3 * s, skin)
    c.ellipse(x + 6 * s, y - 5 * s, 3 * s, 3 * s, skin)
    c.ellipse(x, y + 3 * s, 6 * s, 3 * s, belly)
    c.ellipse(x - 6 * s, y - 5 * s, 2 * s, 2 * s, (244, 240, 226))
    c.ellipse(x + 6 * s, y - 5 * s, 2 * s, 2 * s, (244, 240, 226))
    c.px(x - 5 * s, y - 5 * s, INK); c.px(x + 7 * s, y - 5 * s, INK)
    c.hline(x - 4 * s, x + 4 * s, y + 1 * s, lo)
    for k in range(3):
        c.px(x - 8 * s + k * 2, y - 1 * s, lo)


def chest_icon(c, x, y):
    c.rect(x, y + 5, x + 17, y + 14, INK)
    c.rect(x + 1, y + 6, x + 16, y + 13, (140, 84, 44))
    c.hline(x + 1, x + 16, y + 6, (180, 116, 64))
    c.rect(x + 1, y, x + 16, y + 5, INK)
    c.rect(x + 2, y + 1, x + 15, y + 4, (160, 98, 52))
    c.hline(x + 2, x + 15, y + 1, (196, 132, 76))
    for bx in (x + 4, x + 13):
        c.vline(bx, y + 1, y + 13, GOLD_LO)
    c.rect(x + 7, y + 4, x + 10, y + 8, GOLD)
    c.px(x + 8, y + 6, INK)


PHANTOM = (171, 159, 242)


def phantom_icon(c, cx, cy):
    """Phantom wallet ghost: white body with a wavy hem and two eyes."""
    white, shade, eye = (255, 255, 255), (226, 220, 252), (60, 49, 91)
    for y in range(cy - 7, cy + 4):
        if y < cy - 2:
            half = int(round(7 * (1 - ((cy - 2 - y) / 5.5) ** 2) ** .5))
        else:
            half = 7
        c.hline(cx - half, cx + half, y, white)
        c.px(cx + half, y, shade)
    for x in range(cx - 7, cx + 8):  # wavy hem
        k = (x - (cx - 7)) % 5
        if k in (0, 1, 2, 3):
            c.px(x, cy + 4, white)
        if k in (1, 2):
            c.px(x, cy + 5, white)
    for ex in (cx - 1, cx + 3):
        c.rect(ex, cy - 4, ex + 1, cy - 1, eye)


def gear_icon(c, x, y):
    cx, cy = x + 7, y + 7
    for k in range(8):
        a = k * math.pi / 4
        c.rect(round(cx + math.cos(a) * 6) - 1, round(cy + math.sin(a) * 6) - 1,
               round(cx + math.cos(a) * 6) + 1, round(cy + math.sin(a) * 6) + 1, (150, 146, 160))
    c.ellipse(cx, cy, 5, 5, (150, 146, 160))
    c.ellipse(cx, cy, 2, 2, PANEL)
    c.px(cx - 3, cy - 3, (200, 196, 210))


def wallet_icon(c, x, y):
    c.rect(x, y + 2, x + 13, y + 11, INK)
    c.rect(x + 1, y + 3, x + 12, y + 10, (120, 90, 200))
    c.hline(x + 1, x + 12, y + 3, (160, 130, 240))
    c.rect(x + 8, y + 5, x + 13, y + 8, INK)
    c.rect(x + 9, y + 6, x + 12, y + 7, (90, 60, 160))
    c.px(x + 10, y + 6, GOLD_HI)


def vault_icon(c, x, y):
    c.rect(x, y, x + 13, y + 13, INK)
    c.rect(x + 1, y + 1, x + 12, y + 12, (110, 116, 130))
    c.hline(x + 1, x + 12, y + 1, (150, 156, 170))
    c.ellipse(x + 6.5, y + 6.5, 4, 4, INK)
    c.ellipse(x + 6.5, y + 6.5, 3, 3, (80, 86, 100))
    c.line(x + 6, y + 4, x + 8, y + 9, GOLD)
    c.px(x + 2, y + 4, INK); c.px(x + 2, y + 9, INK)


def clock_icon(c, x, y):
    c.ellipse(x + 6, y + 6, 6, 6, INK)
    c.ellipse(x + 6, y + 6, 5, 5, (230, 226, 214))
    c.vline(x + 6, y + 3, y + 6, INK)
    c.hline(x + 6, x + 8, y + 6, INK)


# --------------------------------------------------------------- background
def background(c: Canvas):
    # deep night brick wall
    bricks = [(78, 44, 40), (70, 40, 36), (84, 50, 44), (64, 36, 34)]
    mortar = (40, 30, 32)
    c.rect(0, 0, W - 1, H - 1, mortar)
    for row, y in enumerate(range(0, H, 7)):
        off = 8 * (row % 2)
        for x in range(-off, W, 16):
            col = bricks[int(rng.integers(0, len(bricks)))]
            c.rect(max(0, x), y, min(W - 1, x + 14), min(H - 1, y + 5), col)
            c.hline(max(0, x), min(W - 1, x + 14), y, sh(col, 1.1))
            c.hline(max(0, x), min(W - 1, x + 14), min(H - 1, y + 5), sh(col, .8))
    # darken with a vignette and pull a green glow behind the logo
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H * .4) / (H * .75)) ** 2)
    shade = np.clip(0.30 + 0.38 * (1 - d), 0.16, 0.62)
    glow = np.clip(1 - np.sqrt(((xx - W / 2) / 190) ** 2 + ((yy - 58) / 46) ** 2), 0, 1)
    B = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16
    th = B[yy % 4, xx % 4]
    q = np.floor(shade * 8 + th) / 8
    rgb = c.a[..., :3].astype(float) * q[..., None]
    g = np.floor(glow * 4 + th) / 4
    rgb += g[..., None] * np.array([18, 40, 16])
    c.a[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    c.a[..., 3] = 255


def hud(c: Canvas):
    layout = {}
    c.rect(0, 0, W - 1, 31, INK)
    c.rect(0, 0, W - 1, 30, PANEL)
    c.hline(0, W - 1, 0, PANEL_HI)
    c.hline(0, W - 1, 29, PANEL_LO)
    for x in range(0, W, 2):  # shadow under the bar
        c.px(x, 32, (0, 0, 0), 160)
        c.px(x + 1, 33, (0, 0, 0), 90)
    for x in range(8, W, 40):
        c.px(x, 3, PANEL_HI); c.px(x, 27, PANEL_HI)
    # balance: the $FROG the player holds
    x = 6
    inset(c, x, 4, x + 128, 26)
    layout['coin'] = [x + 11, 15]
    text(c, '487,140', x + 24, 8, GOLD_HI, BIG, INK, 1)
    text(c, '$FROG', x + 86, 12, MUTED)
    # chest, settings, wallet
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


def logo(c: Canvas, n: Canvas):
    m = render('FROG TRADERS', BIG)
    m = np.kron(m, np.ones((3, 3), bool))
    h, w = m.shape
    x0, y0 = W // 2 - w // 2, 40
    pad = np.pad(m, 1)
    edge = m & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    core = m & ~edge
    # dead glass tubes and their shadow on the brick
    shm = np.zeros_like(m)
    shm[2:, 2:] = m[:-2, :-2]
    c.mask(shm & ~m, x0, y0, (10, 8, 10), 170)
    c.mask(m, x0, y0, (40, 70, 36))
    c.mask(core, x0, y0, (56, 96, 50))
    n.mask(edge, x0, y0, (110, 230, 90))
    n.mask(core, x0, y0, (226, 255, 206))
    # frog heads flanking the sign
    frog_face(c, x0 - 18, y0 + 11, 1.0)
    frog_face(c, x0 + w + 16, y0 + 11, 1.0)
    center_text(c, 'AFK TRADING ON SOLANA', W // 2, y0 + h + 6, (255, 196, 110))
    return dict(rect=[x0, y0, x0 + w - 1, y0 + h - 1])


def ticker_housing(c: Canvas):
    x0, y0, x1, y1 = 12, 342, 627, 357
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, (30, 26, 34))
    c.rect(x0 + 3, y0 + 2, x1 - 3, y1 - 2, (10, 6, 6))
    for x in range(x0 + 4, x1 - 3, 2):
        for y in range(y0 + 3, y1 - 2, 2):
            c.px(x, y, (36, 20, 16))
    return dict(rect=[x0 + 4, y0 + 2, x1 - 4, y1 - 2])


# --------------------------------------------------------------- card art
ART_W, ART_H = 134, 118


def art_frogs():
    c = Canvas(ART_W, ART_H)
    yy, xx = np.mgrid[0:ART_H, 0:ART_W]
    for y in range(ART_H):
        for x in range(ART_W):
            d = math.hypot((x - ART_W / 2) / 60, (y - 40) / 80)
            col = mix((60, 110, 54), (16, 22, 18), min(1, d))
            if dither(x, y, (d * 6) % 1 * .5):
                col = mix(col, (16, 22, 18), .12)
            c.px(x, y, col)
    # golden rays behind the mythic frog
    for k in range(10):
        a = k * math.pi / 5 + .2
        for r in range(14, 70):
            x, y = ART_W / 2 + math.cos(a) * r, 46 + math.sin(a) * r * .9
            if dither(int(x), int(y), .45 * (1 - r / 70)):
                c.px(x, y, (255, 214, 110), 150)
    c.ellipse(ART_W / 2, ART_H - 6, 30, 5, (10, 14, 10))
    c.ellipse(ART_W / 2, ART_H - 6, 24, 3, (30, 46, 26))
    spr = load(A / 'frogs/worker-mythic.png')
    fx, fy = ART_W // 2 - spr.shape[1] // 2, ART_H - spr.shape[0] - 4
    c.blit(spr, fx, fy)
    for (sx, sy) in ((12, 20), (88, 30), (18, 74), (84, 82)):
        c.px(sx, sy, (255, 240, 180)); c.px(sx - 1, sy, (255, 214, 110), 160); c.px(sx + 1, sy, (255, 214, 110), 160)
        c.px(sx, sy - 1, (255, 214, 110), 160); c.px(sx, sy + 1, (255, 214, 110), 160)
    return c, dict(frog=[fx, fy], sprite='mythic')


def art_work():
    c = Canvas(ART_W, ART_H)
    c.rect(0, 0, ART_W - 1, ART_H - 1, INK)
    crops = [('memecoin', 4, 234, ACCENTS['work'], 'MEME'), ('pumpfun', 252, 234, (255, 70, 170), 'PUMP'),
             ('classic', 4, 234, ACCENTS['market'], 'CLASSIC')]
    sh_ = (ART_H - 4) // 3
    for i, (room, cx, cy, col, label) in enumerate(crops):
        im = load(LIT / f'lit-{room}.png')
        y0 = 1 + i * (sh_ + 1)
        part = im[cy:cy + sh_, cx:cx + ART_W]
        c.blit(part, 0, y0)
        c.hline(0, ART_W - 1, y0 + sh_, col)
        w_ = text_w(label)
        c.rect(1, y0 + 1, w_ + 4, y0 + 8, INK)
        c.rect(2, y0 + 2, w_ + 3, y0 + 7, sh(col, .55))
        text(c, label, 3, y0 + 2, (255, 255, 255), SMALL, None)
    return c, {}


def art_fusion():
    c = Canvas(ART_W, ART_H)
    for y in range(ART_H):
        for x in range(ART_W):
            d = math.hypot((x - ART_W / 2) / 55, (y - 56) / 60)
            c.px(x, y, mix((70, 30, 120), (14, 8, 24), min(1, d)))
    # rune circle on the floor
    cx, cy = ART_W // 2, ART_H - 18
    for k in range(64):
        a = k / 64 * math.pi * 2
        x, y = cx + math.cos(a) * 40, cy + math.sin(a) * 9
        c.px(x, y, (200, 150, 255))
        if k % 8 == 0:
            c.px(x, y - 1, (255, 230, 255))
    for k in range(32):
        a = k / 32 * math.pi * 2
        c.px(cx + math.cos(a) * 26, cy + math.sin(a) * 6, (150, 100, 230))
    # two frog heads leaning in
    left = load(A / 'frogs/worker-common.png')[:44]
    right = load(A / 'frogs/worker-rare.png')[:44, ::-1]
    c.blit(left, -14, 30)
    c.blit(right, ART_W - right.shape[1] + 14, 30)
    # the orb (the engine pulses it)
    c.ellipse(ART_W / 2, 50, 9, 9, (120, 60, 200))
    c.ellipse(ART_W / 2, 50, 6, 6, (210, 170, 255))
    c.ellipse(ART_W / 2, 50, 3, 3, (255, 255, 255))
    for k, (dx, dy) in enumerate([(-22, 14), (22, 14)]):  # plus signs
        x, y = ART_W // 2 + dx, 50 + dy
        c.hline(x - 2, x + 2, y, (255, 230, 255)); c.vline(x, y - 2, y + 2, (255, 230, 255))
    return c, dict(orb=[ART_W // 2, 50])


def booster(c: Canvas, x, y, col, label):
    w, h = 30, 44
    lo, hi = sh(col, .6), sh(col, 1.35)
    c.rect(x, y + 2, x + w, y + h - 2, INK)
    c.rect(x + 1, y + 3, x + w - 1, y + h - 3, col)
    for k in range(0, w + 1, 2):  # crimped ends
        c.px(x + k, y + 1, INK); c.px(x + k, y + h - 1, INK)
        c.vline(x + k, y + 2, y + 4, lo)
        c.vline(x + k, y + h - 4, y + h - 2, lo)
    for k in range(10):  # foil sheen
        c.px(x + 4 + k, y + 6 + k * 2, hi)
        c.px(x + 5 + k, y + 6 + k * 2, hi)
    c.ellipse(x + w / 2, y + 20, 8, 8, INK)
    c.ellipse(x + w / 2, y + 20, 7, 7, (240, 232, 210))
    frog_face(c, x + w / 2, y + 21, .55)
    lw = text_w(label)
    c.rect(x + w // 2 - lw // 2 - 2, y + 31, x + w // 2 + lw // 2 + 1, y + 37, INK)
    text(c, label, x + w // 2 - lw // 2, y + 32, (255, 255, 255), SMALL, None)


def art_shop():
    c = Canvas(ART_W, ART_H)
    for y in range(ART_H):
        for x in range(ART_W):
            d = math.hypot((x - ART_W / 2) / 60, (y - 46) / 70)
            c.px(x, y, mix((96, 70, 26), (20, 14, 10), min(1, d)))
    mid = ART_W // 2
    booster(c, mid - 49, 28, (90, 170, 80), 'X1')
    booster(c, mid + 19, 28, (150, 80, 220), 'X15')
    booster(c, mid - 15, 14, (230, 170, 50), 'X5')
    # coin pile
    for k, (cx, cy) in enumerate([(mid - 18, 102), (mid - 6, 104), (mid + 6, 102), (mid + 18, 104), (mid - 12, 97),
                                  (mid, 98), (mid + 12, 97), (mid, 92), (mid - 26, 106), (mid + 28, 106)]):
        c.ellipse(cx, cy, 6, 3, INK)
        c.ellipse(cx, cy, 5, 2, GOLD)
        c.hline(cx - 3, cx + 1, cy - 1, GOLD_HI)
        c.hline(cx - 5, cx + 5, cy + 2, GOLD_LO)
    return c, dict(sparkles=[[mid - 46, 16], [mid + 40, 20], [mid + 2, 6], [mid - 54, 72], [mid + 52, 70]])


def art_market():
    c = Canvas(ART_W, ART_H)
    for y in range(ART_H):
        for x in range(ART_W):
            c.px(x, y, mix((24, 44, 50), (12, 18, 22), y / ART_H))
    # shelves in the back
    for sy in (42, 62):
        c.rect(6, sy, ART_W - 7, sy + 2, (90, 60, 40))
        for k in range(10, ART_W - 12, 9):
            col = [(200, 60, 60), (90, 170, 230), (240, 190, 80), (120, 200, 90)][(k // 9 + sy) % 4]
            c.box(k, sy - 9, k + 6, sy - 1, col, sh(col, 1.3), sh(col, .7))
    # merchant frog behind the counter
    spr = load(A / 'frogs/worker-epic.png')[:60]
    fx = ART_W // 2 - spr.shape[1] // 2
    c.blit(spr, fx, 30)
    # awning
    for x in range(ART_W):
        col = (60, 198, 168) if (x // 10) % 2 == 0 else (236, 228, 206)
        c.vline(x, 0, 14, col)
        c.px(x, 15 + (1 if (x % 10) in (4, 5) else 0), col)
    c.hline(0, ART_W - 1, 0, INK)
    for x in range(0, ART_W, 10):
        c.ellipse(x + 5, 15, 5, 2, (60, 198, 168) if (x // 10) % 2 == 0 else (236, 228, 206))
    c.hline(0, ART_W - 1, 18, (0, 0, 0), 120)
    # counter
    c.rect(0, 84, ART_W - 1, ART_H - 1, INK)
    c.rect(0, 85, ART_W - 1, 89, (150, 100, 60))
    c.hline(0, ART_W - 1, 85, (190, 134, 84))
    c.rect(0, 90, ART_W - 1, ART_H - 1, (110, 70, 42))
    for x in range(8, ART_W, 16):
        c.vline(x, 91, ART_H - 1, (86, 54, 32))
    # framed frog card for sale and its price tag
    c.box(12, 64, 34, 86, (40, 30, 60), (70, 56, 100), (26, 18, 40))
    frog_face(c, 23, 74, .6, (180, 110, 230))
    c.rect(40, 74, 62, 84, INK)
    c.rect(41, 75, 61, 83, (240, 232, 210))
    c.px(40, 79, (240, 232, 210))
    return c, dict(tag=[42, 77])


# --------------------------------------------------------------------- cards
CARD_W, CARD_H = 146, 212
CARDS = [
    ('frogs', 'FROGS', ['SEE YOUR CREW AND WHAT', 'THEY DO, REST THEM', 'IN THE CASINO'], '6 FROGS', art_frogs),
    ('work', 'GO TO WORK', ['PICK AN OFFICE AND', 'START EARNING'], '3 OFFICES', art_work),
    ('shop', 'SHOP', ['SUMMON NEW FROGS', 'IN PACKS OF 1 TO 15'], '25,000 / FROG', art_shop),
    ('market', 'MARKET', ['TRADE FROGS WITH', 'OTHER PLAYERS'], '24 LISTINGS', art_market),
]


def card(key, title, lines, footer, art_fn):
    acc = ACCENTS[key]
    c = Canvas(CARD_W, CARD_H)
    bevel_frame(c, 0, 0, CARD_W - 1, CARD_H - 1, acc)
    # title plate
    c.rect(4, 4, CARD_W - 5, 19, sh(acc, .42))
    c.hline(4, CARD_W - 5, 4, sh(acc, .6))
    c.hline(4, CARD_W - 5, 19, INK)
    center_text(c, title, CARD_W // 2, 8, (255, 255, 255), BIG)
    # art window
    ax, ay = 6, 22
    c.rect(ax - 1, ay - 1, ax + ART_W, ay + ART_H, INK)
    art, meta = art_fn()
    c.blit(art.a, ax, ay)
    # description
    for i, ln in enumerate(lines):
        center_text(c, ln, CARD_W // 2, ay + ART_H + 6 + i * 8, MUTED, SMALL, None)
    # footer pill
    fy = CARD_H - 26
    c.rect(8, fy, CARD_W - 9, fy + 16, INK)
    c.rect(9, fy + 1, CARD_W - 10, fy + 15, sh(acc, .3))
    c.hline(9, CARD_W - 10, fy + 1, sh(acc, .5))
    c.rect(9, fy + 1, 14, fy + 15, acc)
    center_text(c, footer, CARD_W // 2 + 3, fy + 5, TEXT, SMALL, INK)
    meta = {k: ([v[0] + ax, v[1] + ay] if isinstance(v, list) and len(v) == 2 and all(isinstance(t, int) for t in v) else v)
            for k, v in meta.items()}
    if 'sparkles' in meta:
        meta['sparkles'] = [[x + ax, y + ay] for x, y in meta['sparkles']]
    meta['art'] = [ax, ay, ax + ART_W - 1, ay + ART_H - 1]
    return c, meta


# --------------------------------------------------------------------- tiles
TILE_W, TILE_H = 301, 36


def slot_icon(c, x, y):
    c.rect(x, y, x + 21, y + 21, INK)
    c.rect(x + 1, y + 1, x + 20, y + 20, (190, 50, 70))
    c.hline(x + 1, x + 20, y + 1, (230, 90, 110))
    c.rect(x + 3, y + 6, x + 18, y + 15, INK)
    for k in range(3):
        c.rect(x + 4 + k * 5, y + 7, x + 7 + k * 5, y + 14, (240, 236, 224))
    c.vline(x + 22, y + 4, y + 12, (150, 150, 160))
    c.ellipse(x + 22, y + 3, 2, 2, (230, 60, 60))
    return [x + 4, y + 7]


def crown_icon(c, x, y):
    frog_face(c, x + 11, y + 14, .85, (110, 170, 80))
    c.poly([(x + 3, y + 7), (x + 5, y), (x + 8, y + 4), (x + 11, y - 1), (x + 14, y + 4), (x + 17, y), (x + 19, y + 7)], GOLD)
    c.hline(x + 3, x + 19, y + 7, GOLD_LO)
    c.px(x + 11, y + 3, (220, 60, 60))


def mail_icon(c, x, y):
    c.rect(x, y + 3, x + 21, y + 18, INK)
    c.rect(x + 1, y + 4, x + 20, y + 17, (236, 228, 206))
    c.line(x + 1, y + 4, x + 10, y + 11, (150, 140, 120))
    c.line(x + 20, y + 4, x + 11, y + 11, (150, 140, 120))
    c.ellipse(x + 16, y + 15, 4, 4, INK)
    c.ellipse(x + 16, y + 15, 3, 3, (90, 170, 240))
    c.hline(x + 14, x + 18, y + 15, (255, 255, 255)); c.vline(x + 16, y + 13, y + 17, (255, 255, 255))


def bag_icon(c, x, y):
    c.ellipse(x + 10, y + 13, 9, 8, INK)
    c.ellipse(x + 10, y + 13, 8, 7, (170, 130, 70))
    c.rect(x + 6, y + 2, x + 14, y + 6, INK)
    c.rect(x + 7, y + 3, x + 13, y + 5, (190, 150, 90))
    c.mask(render('$', SMALL), x + 9, y + 11, GOLD_HI)
    c.vline(x + 19, y + 2, y + 9, (126, 226, 84))
    c.line(x + 17, y + 4, x + 19, y + 2, (126, 226, 84)); c.line(x + 21, y + 4, x + 19, y + 2, (126, 226, 84))


TILES = [
    ('boss', 'BOSS FROGS', 'NFT MANAGERS FOR YOUR OFFICES', crown_icon),
    ('invite', 'INVITE', 'BRING FRIENDS INTO THE GAME', mail_icon),
]


def tile(key, title, sub, icon):
    acc = ACCENTS[key]
    c = Canvas(TILE_W, TILE_H)
    bevel_frame(c, 0, 0, TILE_W - 1, TILE_H - 1, acc)
    inset(c, 6, 5, 31, 28, sh(acc, .28))
    meta = {}
    r = icon(c, 8, 7)
    if r:
        meta['reels'] = r
    text(c, title, 38, 8, TEXT, BIG)
    text(c, sub, 38, 20, MUTED, SMALL, None)
    # arrow
    ax = TILE_W - 14
    for k in range(4):
        c.vline(ax + k, 13 + k, 21 - k, acc)
    return c, meta


# ---------------------------------------------------------------------- main
def build():
    OUT.mkdir(parents=True, exist_ok=True)
    bg, neon = Canvas(W, H), Canvas(W, H)
    background(bg)
    layout = {'size': [W, H]}
    layout['hud'] = hud(bg)
    layout['logo'] = logo(bg, neon)

    cards = []
    gap = 10
    total = 4 * CARD_W + 3 * gap
    x0 = (W - total) // 2
    for i, (key, title, lines, footer, fn) in enumerate(CARDS):
        cv, meta = card(key, title, lines, footer, fn)
        cv.save(OUT / f'card-{key}.png')
        x = x0 + i * (CARD_W + gap)
        cards.append(dict(key=key, title=title, x=x, y=84, w=CARD_W, h=CARD_H, accent=ACCENTS[key], meta=meta))
        # shadow on the wall
        for yy in range(88, 84 + CARD_H + 4):
            for xx in range(x + 4, x + CARD_W + 4):
                if (xx + yy) % 2:
                    bg.px(xx, yy, (0, 0, 0), 140)
    layout['cards'] = cards

    tiles = []
    tgap = 10
    ttotal = 2 * TILE_W + tgap
    tx0 = (W - ttotal) // 2
    for i, (key, title, sub, icon) in enumerate(TILES):
        cv, meta = tile(key, title, sub, icon)
        cv.save(OUT / f'tile-{key}.png')
        x = tx0 + i * (TILE_W + tgap)
        tiles.append(dict(key=key, title=title, x=x, y=308, w=TILE_W, h=TILE_H, accent=ACCENTS[key], meta=meta))
    layout['tiles'] = tiles

    bg.save(OUT / 'bg.png')
    neon.save(OUT / 'logo-neon.png')
    (OUT / 'layout.json').write_text(json.dumps(layout))
    return layout


if __name__ == '__main__':
    build()
    print('ok')
