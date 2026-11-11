"""Screens for the live game: Login (connect Phantom), Wallet, Invite and Market.

Outputs client/src/assets/{login,wallet,invite,market}-screen/.
"""
from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from px2 import INK, Canvas, dither, mix, sh
from menu_kit import GOLD, GOLD_HI, TEXT, MUTED, brass_inset, draw_text, gradient_text
from menu2 import PHANTOM, button, header, neon_logo, phantom_ghost, wall
from frogs_screen import KEYS, LEFT, RIGHT, TILE_H, TILE_W, action_button, panel, plate, portrait_frame

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'client/src/assets'
W, H = 640, 360
PINK, TEAL, BLUE, GREEN = (230, 70, 90), (60, 198, 168), (90, 170, 240), (110, 200, 90)


def out(name):
    d = A / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def save(c, d, name):
    Image.fromarray(c.a, 'RGBA').save(d / name)


def shadow(bg, box):
    x0, y0, x1, y1 = box
    for y in range(y0 + 3, min(H, y1 + 4)):
        for x in (x1 + 1, x1 + 2, x1 + 3):
            if x < W and (x + y) % 2:
                bg.px(x, y, (0, 0, 0), 150)
    for x in range(x0 + 3, min(W, x1 + 4)):
        for y in (y1 + 1, y1 + 2):
            if y < H and (x + y) % 2:
                bg.px(x, y, (0, 0, 0), 150)


def well(c, x0, y0, x1, y1):
    brass_inset(c, x0, y0, x1, y1)


def frog_sprite(rarity):
    im = Image.open(A / f'frogs/worker-{rarity}.png').convert('RGBA')
    return np.array(im)


# ---------------------------------------------------------------- login
def build_login():
    d = out('login-screen')
    bg = wall(5, [(150, 100), (490, 100)], logo=(W // 2, 52))
    n = Canvas(W, H)
    lay = {'size': [W, H], 'hud': {}, 'cards': [], 'tiles': [], 'back': None}
    lay['logo'] = {'rect': neon_logo(bg, n, W // 2, 40)}
    draw_text(bg, 'AFK TRADING ON SOLANA', W // 2, 80, GOLD, 'body', align='center')
    box = (180, 112, 460, 318)
    shadow(bg, box)
    panel(bg, box, PHANTOM)
    x0, y0, x1, y1 = box
    gradient_text(bg, 'CONNECT TO PLAY', W // 2, y0 + 18, (255, 255, 255), (214, 206, 196), 'title', align='center')
    for i, ln in enumerate(['Sign in with your Phantom wallet.', 'It is free and sends no transaction.']):
        draw_text(bg, ln, W // 2, y0 + 40 + i * 10, (214, 204, 190), 'body', align='center')
    # the connect button is drawn live (hover, busy state); its plate is baked here
    btn = Canvas(200, 30)
    button(btn, 0, 0, 199, 29, PHANTOM)
    phantom_ghost(btn, 22, 15)
    draw_text(btn, 'CONNECT PHANTOM', 112, 10, (40, 24, 60), 'head', shadow=None, align='center')
    save(btn, d, 'btn-connect.png')
    btn2 = Canvas(200, 30)
    button(btn2, 0, 0, 199, 29, (120, 112, 140))
    draw_text(btn2, 'CONNECTING...', 100, 10, (40, 24, 60), 'head', shadow=None, align='center')
    save(btn2, d, 'btn-connect-busy.png')
    lay['connect'] = {'x': W // 2 - 100, 'y': y0 + 70, 'w': 200, 'h': 30}
    well(bg, x0 + 18, y0 + 114, x1 - 18, y0 + 160)
    lay['status'] = [W // 2, y0 + 122]
    for i, ln in enumerate(['TEST MODE', 'Balances are test $FROG, not real tokens.']):
        draw_text(bg, ln, W // 2, y0 + 172 + i * 10, GOLD if i == 0 else MUTED, 'body', align='center')
    # two frogs keeping the door
    for rk, fx in (('legendary', 60), ('mythic', 520)):
        sp = frog_sprite(rk)
        h, w = sp.shape[:2]
        c = Canvas(w, h)
        c.a[:] = sp
        bg.blit(c.a, fx, 330 - h)
    # floor shadow under the frogs
    for fx in (60, 520):
        for x in range(fx + 4, fx + 56):
            if x % 2:
                bg.px(x, 331, (0, 0, 0), 120)
    save(bg, d, 'bg.png')
    Image.fromarray(n.a, 'RGBA').save(d / 'logo-neon.png')
    (d / 'layout.json').write_text(json.dumps(lay))


# ---------------------------------------------------------------- wallet
def build_wallet():
    d = out('wallet-screen')
    bg = wall(6, [(320, 40)])
    lay = {'size': [W, H], 'hud': header(bg, 'WALLET'), 'cards': [], 'tiles': [], 'back': 'home'}
    box = (110, 46, 530, 350)
    shadow(bg, box)
    panel(bg, box, PHANTOM)
    x0, y0, x1, y1 = box
    rows = {}
    # two balance wells
    for i, (key, label) in enumerate((('balance', 'BALANCE'), ('chest', 'EARNED BY YOUR FROGS'))):
        wy = y0 + 16 + i * 50
        draw_text(bg, label, x0 + 22, wy, MUTED, 'body')
        well(bg, x0 + 20, wy + 9, x1 - 20, wy + 33)
        rows[key] = [x0 + 30, wy + 15]
    lay['rows'] = rows
    for key, label, col, dark in (('withdraw', 'WITHDRAW', GOLD, True), ('deposit', 'TEST DEPOSIT', GREEN, False),
                                  ('signout', 'SIGN OUT', (96, 92, 110), False)):
        save(action_button(label, col, 120, 20, dark), d, f'btn-{key}.png')
        save(action_button(label, (70, 66, 80), 120, 20), d, f'btn-{key}-off.png')
    lay['buttons'] = {'withdraw': {'x': x0 + 22, 'y': y0 + 122, 'w': 120, 'h': 20},
                      'deposit': {'x': x0 + 150, 'y': y0 + 122, 'w': 120, 'h': 20},
                      'signout': {'x': x1 - 142, 'y': y0 + 122, 'w': 120, 'h': 20}}
    well(bg, x0 + 20, y0 + 152, x1 - 20, y1 - 16)
    lay['info'] = [x0 + 30, y0 + 160, x1 - 30]
    save(bg, d, 'bg.png')
    (d / 'layout.json').write_text(json.dumps(lay))


# ---------------------------------------------------------------- invite
def build_invite():
    d = out('invite-screen')
    bg = wall(7, [(200, 40), (520, 40)])
    lay = {'size': [W, H], 'hud': header(bg, 'INVITE'), 'cards': [], 'tiles': [], 'back': 'home'}
    L, R = (6, 46, 330, 354), (336, 46, 634, 354)
    for b in (L, R):
        shadow(bg, b)
        panel(bg, b, BLUE)
    x0, y0, x1, _ = L
    gradient_text(bg, 'BRING FRIENDS', x0 + 18, y0 + 16, (255, 255, 255), (214, 206, 196), 'title')
    rules = [('A FRIEND BUYS 10 FROGS', 'YOU GET 1 FREE PACK'), ('EVERY NEXT 10 FROGS', 'YOU GET 2 MORE PACKS')]
    for i, (a, b) in enumerate(rules):
        ry = y0 + 40 + i * 30
        well(bg, x0 + 16, ry, x1 - 16, ry + 24)
        draw_text(bg, a, x0 + 26, ry + 6, TEXT, 'body')
        draw_text(bg, b, x1 - 26, ry + 14, GOLD_HI, 'body', align='right')
    draw_text(bg, 'Free packs roll like any pack: any rarity can drop.', x0 + 18, y0 + 104, MUTED, 'body')
    draw_text(bg, 'YOUR LINK', x0 + 18, y0 + 122, MUTED, 'body')
    well(bg, x0 + 16, y0 + 131, x1 - 16, y0 + 151)
    lay['link'] = [x0 + 24, y0 + 137, x1 - 24]
    save(action_button('COPY LINK', BLUE, 136, 20), d, 'btn-copy.png')
    save(action_button('OPEN FREE PACK', GOLD, 136, 20, dark=True), d, 'btn-open.png')
    save(action_button('OPEN FREE PACK', (70, 66, 80), 136, 20), d, 'btn-open-off.png')
    lay['buttons'] = {'copy': {'x': x0 + 16, 'y': y0 + 158, 'w': 136, 'h': 20}}
    # stats wells
    for i, (key, label) in enumerate((('friends', 'FRIENDS'), ('earned', 'PACKS EARNED'), ('free', 'FREE PACKS'))):
        sx = x0 + 16 + i * 102
        well(bg, sx, y0 + 196, sx + 94, y0 + 236)
        draw_text(bg, label, sx + 47, y0 + 202, MUTED, 'body', align='center')
        lay.setdefault('stats', {})[key] = [sx + 47, y0 + 214]
    lay['buttons']['open'] = {'x': x0 + 16, 'y': y0 + 248, 'w': 136, 'h': 20}
    draw_text(bg, 'Rewards come in as your friends buy packs.', x0 + 18, y0 + 280, MUTED, 'body')
    # friends list
    rx0, ry0, rx1, ry1 = R
    gradient_text(bg, 'YOUR FRIENDS', rx0 + 16, ry0 + 16, (255, 255, 255), (214, 206, 196), 'title')
    draw_text(bg, 'BOUGHT', rx1 - 100, ry0 + 22, MUTED, 'body', align='right')
    draw_text(bg, 'PACKS', rx1 - 24, ry0 + 22, MUTED, 'body', align='right')
    well(bg, rx0 + 14, ry0 + 34, rx1 - 14, ry1 - 14)
    lay['list'] = {'x': rx0 + 18, 'y': ry0 + 38, 'w': rx1 - rx0 - 36, 'row': 24, 'rows': 10}
    save(bg, d, 'bg.png')
    (d / 'layout.json').write_text(json.dumps(lay))


# ---------------------------------------------------------------- market
def stall_wall(c):
    """Market hall behind the panels: dark wood stalls under a striped awning."""
    c.rect(0, 34, W - 1, H - 1, (40, 30, 26))
    for x in range(0, W, 12):
        col = (52, 38, 30) if (x // 12) % 2 else (46, 34, 28)
        c.rect(x, 34, x + 11, H - 1, col)
        c.vline(x, 34, H - 1, (34, 24, 20))
    # striped awning
    for x in range(W):
        stripe = (x // 16) % 2
        col = (60, 170, 150) if stripe else (236, 226, 200)
        for y in range(34, 46):
            c.px(x, y, sh(col, 1 - (y - 34) / 40))
        yy = 46 + int(3 * abs(math.sin((x % 16) / 16 * math.pi)))
        for y in range(46, yy + 1):
            c.px(x, y, sh(col, .8))
    c.hline(0, W - 1, 34, INK)
    # string lights under the awning
    for x in range(8, W, 20):
        c.px(x, 52, (255, 214, 120))
        c.px(x, 51, (120, 90, 40))


def build_market():
    d = out('market-screen')
    bg = Canvas(W, H)
    stall_wall(bg)
    lay = {'size': [W, H], 'hud': header(bg, 'MARKET'), 'cards': [], 'tiles': [], 'back': 'home'}
    LB, RB = (6, 58, 408, 354), (414, 58, 634, 354)
    for b in (LB, RB):
        shadow(bg, b)
        panel(bg, b, TEAL)
    gx0, gy0 = LB[0] + 10, LB[1] + 10
    cols, rows, pitch = 7, 3, 78
    for r in range(rows):
        for col in range(cols):
            x, y = gx0 + col * (TILE_W + 4), gy0 + r * pitch
            bg.rect(x, y, x + TILE_W - 1, y + TILE_H + 11, INK)
            bg.rect(x + 1, y + 1, x + TILE_W - 2, y + TILE_H + 10, (34, 30, 30))
            bg.hline(x + 1, x + TILE_W - 2, y + 1, (52, 46, 44))
    lay['grid'] = {'x': gx0, 'y': gy0, 'cols': cols, 'rows': rows, 'w': TILE_W, 'h': TILE_H, 'gap': 4, 'pitch': pitch}
    for rid, k in enumerate(KEYS):
        Image.fromarray(portrait_frame(rid).a, 'RGBA').save(d / f'tile-{k}.png')
    Image.fromarray(plate(96, 16, TEAL, True).a, 'RGBA').save(d / 'tab-on.png')
    Image.fromarray(plate(96, 16, TEAL, False).a, 'RGBA').save(d / 'tab.png')
    lay['tabs'] = [{'key': k, 'x': 8 + i * 100, 'y': 40, 'w': 96, 'h': 16} for i, k in enumerate(('buy', 'sell', 'mine'))]
    # card niche
    rx0, ry0 = RB[0] + 8, RB[1] + 8
    for y in range(ry0, ry0 + 184):
        for x in range(rx0, rx0 + 112):
            dd = math.hypot((x - rx0 - 56) / 70, (y - ry0 - 70) / 110)
            base = mix((30, 50, 50), (12, 16, 18), min(1, dd))
            bg.px(x, y, base)
    lay['card'] = [rx0, ry0]
    ix = rx0 + 118
    lay['info'] = {'x': ix, 'y': ry0 + 6, 'w': 86}
    for key, label, col, dark in (('buy', 'BUY', GOLD, True), ('list', 'LIST FOR SALE', GREEN, False),
                                  ('cancel', 'TAKE BACK', (96, 92, 110), False)):
        save(action_button(label, col, 86, 18, dark), d, f'btn-{key}.png')
        save(action_button(label, (70, 66, 80), 86, 18), d, f'btn-{key}-off.png')
    lay['button'] = {'x': ix, 'y': ry0 + 166, 'w': 86, 'h': 18}
    lay['price'] = {'x': ix, 'y': ry0 + 120, 'w': 86, 'h': 18}
    well(bg, rx0, ry0 + 192, RB[2] - 8, RB[3] - 10)
    lay['notes'] = [rx0 + 8, ry0 + 200]
    save(bg, d, 'bg.png')
    (d / 'layout.json').write_text(json.dumps(lay))


if __name__ == '__main__':
    build_login()
    build_wallet()
    build_invite()
    build_market()
    print('ui screens ok')
