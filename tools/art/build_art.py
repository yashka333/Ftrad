"""Builds every sprite the client uses.

    python3 tools/art/build_art.py

Outputs go to client/src/assets. Replace any PNG with hand-made or generated
art of the same size and the game picks it up; layout.json holds positions.
"""
from __future__ import annotations
import json
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import frogs  # noqa: E402
import icons  # noqa: E402
import rooms  # noqa: E402
import font  # noqa: E402
from pix import Canvas, sheet, hex2rgba  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
ASSETS = os.path.join(ROOT, 'client', 'src', 'assets')
SPR = os.path.join(ASSETS, 'sprites')
SCN = os.path.join(ASSETS, 'scenes')
UI = os.path.join(ASSETS, 'ui')

SCENE_W, SCENE_H = 480, 270
OFFICE_ORDER = ['memecoin', 'pumpfun', 'classic']
DORM_POS = (0, 150)
CASINO_POS = (200, 150)

# frog sprite placement relative to a desk sprite
DESK_FROG = (15, -16)
DESK_MONITOR = (1, -12)
DESK_SCREEN = (4, -10)
DESK_CHAIR = (17, -12)


def save(c: Canvas, *parts):
    path = os.path.join(*parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    c.save(path)


def build_frogs():
    frogs.build(SPR)
    for r, o in enumerate(frogs.OUTFITS):
        save(rooms.blanket(o.get('blanket', o['C'])), SPR, f'blanket-{r}.png')
    frames = {'work': len(frogs.WORK), 'sleep': len(frogs.SLEEP), 'casino': len(frogs.CASINO), 'idle': len(frogs.IDLE)}
    out, start = {}, 0
    for k, n in frames.items():
        out[k] = {'start': start, 'count': n}
        start += n
    return out


def build_rooms():
    for pid in OFFICE_ORDER:
        save(rooms.office_bg(pid), SCN, f'office-{pid}.png')
        save(rooms.office_sign(pid, True), SCN, f'sign-{pid}-on.png')
        save(rooms.office_sign(pid, False), SCN, f'sign-{pid}-off.png')
        save(sheet(rooms.screen_frames(pid)), SPR, f'screen-{pid}.png')
        save(sheet(rooms.ticker_frames(pid)), SPR, f'ticker-{pid}.png')
    save(rooms.desk(), SPR, 'desk.png')
    save(rooms.chair(), SPR, 'chair.png')
    save(rooms.monitor(), SPR, 'monitor.png')
    save(rooms.dorm_bg(), SCN, 'dorm.png')
    save(rooms.zzz(), SPR, 'zzz.png')
    save(rooms.casino_bg(True), SCN, 'casino.png')
    save(rooms.casino_bg(False), SCN, 'casino-closed.png')
    save(rooms.casino_front(), SCN, 'casino-front.png')
    save(rooms.casino_sign(True), SCN, 'casino-sign-on.png')
    save(rooms.casino_sign(False), SCN, 'casino-sign-off.png')
    save(rooms.closed_sign(), SCN, 'casino-for-sale.png')
    save(sheet(rooms.roulette_frames()), SPR, 'roulette.png')
    save(sheet(rooms.slot_lights()), SPR, 'slot-lights.png')


def build_icons():
    for name, fn in icons.UI.items():
        save(fn(), UI, f'icon-{name}.png')
    for name, fn in icons.SKILLS.items():
        save(fn(), UI, f'skill-{name}.png')


def build_card_back():
    c = Canvas(48, 64)
    c.rect(0, 0, 48, 64, '#2a1d44')
    c.frame(0, 0, 48, 64, '#1a1410')
    c.frame(2, 2, 44, 60, '#f2c94c')
    for y in range(4, 60, 4):
        for x in range(4 + (y // 4) % 2 * 2, 44, 4):
            c.set(x, y, '#3a2a5c')
    c.ellipse(24, 32, 13, 13, '#1a1410')
    c.ellipse(24, 32, 12, 12, '#4f9a45')
    c.ellipse(18, 24, 4, 4, '#4f9a45'); c.ellipse(30, 24, 4, 4, '#4f9a45')
    c.rect(16, 22, 4, 3, '#f4ead2'); c.rect(28, 22, 4, 3, '#f4ead2')
    c.rect(17, 23, 2, 2, '#1a1410'); c.rect(29, 23, 2, 2, '#1a1410')
    c.hline(16, 35, 16, '#2a1a10')
    c.ellipse(24, 40, 4, 2, '#d8c79e')
    font.draw(c, 24 - font.width('FROG', font.SMALL) // 2, 52, 'FROG', '#f2c94c', font.SMALL)
    save(c, UI, 'card-back.png')


def build_logo():
    text = 'FROG TRADERS'
    w = font.width(text)
    c = Canvas(w + 4, 11)
    font.draw(c, 1, 1, text, '#3ddc84', shadow='#0d3a20')
    c.outline('#1a1410')
    save(c, UI, 'logo.png')


def build_hub():
    """The crossroads scene from the teaser art, with sign overlays that flicker."""
    data = json.load(open(os.path.join(HERE, 'source', 'crossroads.json')))
    n = data['N']
    lut = {ch: i for i, ch in enumerate(data['alpha'])}
    pal = [hex2rgba(h) for h in data['pal']]
    base = Image.new('RGBA', (n, n))
    px = base.load()
    for i, ch in enumerate(data['data']):
        px[i % n, i // n] = pal[lut[ch]]
    os.makedirs(SCN, exist_ok=True)
    base.save(os.path.join(SCN, 'hub.png'))
    for b in data['boards']:
        ov = Image.new('RGBA', (n, n), (0, 0, 0, 0))
        op = ov.load()
        for idx, col in b['ov']:
            op[idx % n, idx // n] = pal[col]
        ov.save(os.path.join(SCN, f"hub-sign-{b['key']}-off.png"))


def layout(frog_anims):
    offices = []
    for i, pid in enumerate(OFFICE_ORDER):
        ox = i * rooms.OFFICE_W
        offices.append({
            'path': pid, 'x': ox, 'y': 0, 'w': rooms.OFFICE_W, 'h': rooms.OFFICE_H,
            'sign': {'x': ox + 6, 'y': 3},
            'ticker': {'x': ox + 58, 'y': 30},
            'desks': [{'x': ox + dx, 'y': dy} for dx, dy in rooms.DESKS],
        })
    dx, dy = DORM_POS
    beds = []
    for row in rooms.BED_ROWS:
        for bx in rooms.BUNKS:
            beds.append({'frog': {'x': dx + bx + 10, 'y': dy + row - 17},
                         'blanket': {'x': dx + bx + 4, 'y': dy + row - 3}})
    cx, cy = CASINO_POS
    seats = [{'x': cx + s['x'], 'y': cy + s['y'], 'spot': s['spot']} for s in rooms.casino_seats()]
    return {
        'scene': {'w': SCENE_W, 'h': SCENE_H},
        'frog': {'w': frogs.W, 'h': frogs.H, 'anims': frog_anims, 'skins': len(frogs.SKINS),
                 'outfits': len(frogs.OUTFITS)},
        'desk': {'w': rooms.DESK_W, 'h': rooms.DESK_H, 'frog': DESK_FROG, 'monitor': DESK_MONITOR,
                 'screen': DESK_SCREEN, 'chair': DESK_CHAIR},
        'offices': offices,
        'dorm': {'x': dx, 'y': dy, 'w': rooms.DORM_W, 'h': rooms.DORM_H, 'beds': beds},
        'casino': {
            'x': cx, 'y': cy, 'w': rooms.CASINO_W, 'h': rooms.CASINO_H,
            'sign': {'x': cx + 108, 'y': cy + 2},
            'forSale': {'x': cx + 140 - (font.width('FOR SALE') + 10) // 2, 'y': cy + 52},
            'roulette': {'x': cx + rooms.TABLE[0] + 4, 'y': cy + rooms.TABLE[1] + 6},
            'slotLights': [{'x': cx + x + 2, 'y': cy + 26} for x in rooms.SLOT_X],
            'seats': seats,
        },
        'sheets': {
            'screen': {'w': 12, 'h': 9, 'frames': 8},
            'ticker': {'w': 44, 'h': 28, 'frames': 16},
            'roulette': {'w': 28, 'h': 16, 'frames': 8},
            'slotLights': {'w': 16, 'h': 4, 'frames': 4},
        },
    }


def main():
    anims = build_frogs()
    build_rooms()
    build_icons()
    build_card_back()
    build_logo()
    build_hub()
    lay = layout(anims)
    with open(os.path.join(ASSETS, 'layout.json'), 'w') as f:
        json.dump(lay, f, indent=2)
    print('art written to', ASSETS)


if __name__ == '__main__':
    main()
