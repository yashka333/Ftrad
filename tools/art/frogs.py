"""Frog sprites: 4 skins x 6 rarity outfits, layered so the game can combine them.

Every frog frame is 24x24. The frog sits behind a desk, so only the head,
torso and arms are drawn. Layers:
  frog-skin-<k>.png     body + face, frames for each animation
  frog-outfit-<r>.png   clothes and accessories for rarity r, same frames
"""
from __future__ import annotations
from pix import Canvas, mirror_rows, sheet, shade

W = H = 24
OUT = '#1a1410'
EYE = '#f4ead2'
PUPIL = '#1a1410'
MOUTH = '#3a2418'
BELLY = '#d8c79e'

SKINS = [
    {'name': 'olive', 'S': '#8f8f52', 's': '#6b6b3b', 'L': '#b3b071'},
    {'name': 'teal', 'S': '#5b9c98', 's': '#3e7471', 'L': '#86c3bd'},
    {'name': 'lavender', 'S': '#8f84a6', 's': '#686081', 'L': '#b5abc8'},
    {'name': 'green', 'S': '#4f9a45', 's': '#357032', 'L': '#7ac26b'},
]

# Left halves (12 chars), mirrored to 24. Head starts at row 3 to leave
# room for the crown.
HEAD = mirror_rows([
    '....OOOO....',
    '...OWWWWO...',
    '...OWWWWO...',
    '..OSWWWWOOOO',
    '.OSSSOOSSSSS',
    'OSSLSSSSSsSS',
    'OSSSSSSSSSSS',
    'OSsSSSSSSSSS',
    'OSsMMMMMMMMM',
    '.OSSSSSBBBBB',
    '..OOSSSSBBBB',
    '....OOOSSSSS',
])
TORSO = mirror_rows([
    '.......OCCCC',
    '......OCCCCC',
    '.....OAOCCCC',
    '.....OAOCCCC',
    '....OAAOCCCC',
    '....OAAOCCCC',
    '....OHHOCCCC',
    '.....OO.CCCC',
])
HEAD_Y = 3
TORSO_Y = HEAD_Y + len(HEAD)   # 15


def _pal(skin):
    return {'O': OUT, 'W': EYE, 'S': skin['S'], 's': skin['s'], 'L': skin['L'],
            'M': MOUTH, 'B': BELLY, 'A': skin['S'], 'H': skin['L']}


# Animation frames. Each entry tweaks pose: pupils, blink, hands.
# pupil: (dx, dy) offset inside the 4x3 eye white, None = closed eyes.
WORK = [
    {'pupil': (1, 1), 'hands': (0, 0)},
    {'pupil': (1, 1), 'hands': (-1, 0)},
    {'pupil': (1, 1), 'hands': (0, -1)},
    {'pupil': (2, 1), 'hands': (-1, 0)},
    {'pupil': None, 'hands': (0, 0)},          # blink
    {'pupil': (0, 1), 'hands': (0, -1)},
]
SLEEP = [
    {'pupil': None, 'bob': 0},
    {'pupil': None, 'bob': 1},
]
CASINO = [
    {'pupil': (1, 0), 'arms': 'down'},
    {'pupil': (1, 0), 'arms': 'up'},
    {'pupil': (2, 0), 'arms': 'up'},
    {'pupil': (1, 0), 'arms': 'down'},
]
IDLE = [
    {'pupil': (1, 1)},
    {'pupil': None},
]


def _eyes(c: Canvas, pupil, y0=HEAD_Y, skin=None):
    # eye whites are at cols 4..7 and 16..19, rows y0+1..y0+3
    for ex in (4, 16):
        if pupil is None:
            for j in range(3):
                for i in range(4):
                    c.set(ex + i, y0 + 1 + j, skin['S'])
            for i in range(4):
                c.set(ex + i, y0 + 2, OUT)
        else:
            dx, dy = pupil
            dx = max(0, min(2, dx))
            dy = max(0, min(1, dy))
            for j in range(2):
                for i in range(2):
                    c.set(ex + dx + i, y0 + 1 + dy + j, PUPIL)
            c.set(ex + dx, y0 + 1 + dy, '#ffffff')


def _spots(c: Canvas, skin, y0=HEAD_Y):
    for (x, y) in ((6, 7), (9, 6), (14, 6), (17, 7), (11, 9), (3, 9), (20, 9)):
        c.set(x, y0 + y - 3, skin['s'])


def body_frame(skin, pose, kind='work') -> Canvas:
    c = Canvas(W, H)
    bob = pose.get('bob', 0)
    pal = _pal(skin)
    c.grid(0, HEAD_Y + bob, HEAD, pal)
    torso = [list(r) for r in TORSO]
    c.grid(0, TORSO_Y + bob, [''.join(r) for r in torso], {**pal, 'C': skin['S'], 'H': skin['L']})
    _spots(c, skin, HEAD_Y + bob)
    _eyes(c, pose.get('pupil'), HEAD_Y + bob, skin)
    if kind == 'work':
        dx, dy = pose['hands']
        # hands rest on the keyboard at rows 21..22; lift one of them
        for side, (hx, sdx) in enumerate(((4, dx), (18, -dx))):
            lift = dy if side == 0 else (-1 - dy if dy else 0)
            lift = max(-1, min(0, lift))
            c.rect(hx + (sdx if side == 0 else 0), TORSO_Y + 5 + lift, 2, 1, skin['L'])
    if kind == 'casino' and pose.get('arms') == 'up':
        # right arm raised with a cocktail
        for x in (18, 19):
            for y in range(TORSO_Y + 2, TORSO_Y + 8):
                c.px[x, y] = (0, 0, 0, 0)
        arm = [(18, TORSO_Y + 2), (19, TORSO_Y + 1), (20, TORSO_Y), (20, TORSO_Y - 1), (21, TORSO_Y - 2)]
        for (x, y) in arm:
            c.set(x, y, skin['S'])
        for (x, y) in arm:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if c.get(x + dx, y + dy)[3] == 0:
                    c.set(x + dx, y + dy, OUT)
        c.set(21, TORSO_Y - 3, skin['L'])
        # cocktail glass
        for (x, y, col) in ((20, TORSO_Y - 6, '#cfe9f2'), (21, TORSO_Y - 6, '#cfe9f2'), (22, TORSO_Y - 6, '#cfe9f2'),
                            (20, TORSO_Y - 5, '#e74c3c'), (21, TORSO_Y - 5, '#e74c3c'), (22, TORSO_Y - 5, '#cfe9f2'),
                            (21, TORSO_Y - 4, '#cfe9f2'), (23, TORSO_Y - 7, '#f2c94c')):
            c.set(x, y, col)
    return c


# ---------------------------------------------------------------- outfits

OUTFITS = [
    # 0 Common: stained grey tank top, bare arms, band-aid on the head
    {'C': '#8a8a80', 'c': '#66665e', 'blanket': '#7a5a3a', 'holes': True, 'bandaid': True, 'sleeves': False},
    # 1 Uncommon: green hoodie with the hood behind the neck
    {'C': '#4f8f3a', 'c': '#3a6d2b', 'hood': True, 'sleeves': True},
    # 2 Rare: white shirt and red tie
    {'C': '#eae4d6', 'c': '#c6bfae', 'tie': '#c0392b', 'sleeves': True, 'sleeve': '#eae4d6'},
    # 3 Epic: purple suit
    {'C': '#6b3fa0', 'c': '#4e2c78', 'shirt': True, 'tie': '#2b1a44', 'sleeves': True},
    # 4 Legendary: black suit, shades and a gold chain
    {'C': '#26232b', 'c': '#16141a', 'shirt': True, 'tie': '#c0392b', 'sleeves': True,
     'shades': True, 'chain': True},
    # 5 Mythic: gold suit and a crown
    {'C': '#d9a520', 'c': '#a87a12', 'shirt': True, 'tie': '#b0182f', 'sleeves': True,
     'crown': True, 'chain': True},
]


def outfit_frame(r: int, pose, kind='work') -> Canvas:
    o = OUTFITS[r]
    c = Canvas(W, H)
    bob = pose.get('bob', 0)
    ty = TORSO_Y + bob
    C, cs = o['C'], o['c']
    # torso cloth: cols 8..15, rows ty..ty+7 (body is cols 7..16 with outline)
    for j in range(8):
        for i in range(8, 16):
            if j == 0 and i in (8, 15):
                continue
            c.set(i, ty + j, cs if i >= 13 else C)
    if o.get('holes'):
        for (x, y) in ((10, 3), (13, 5), (9, 6)):
            c.set(x, ty + y, '#4a4a44')
        c.set(12, ty + 2, '#a3743a')  # stain
    if o.get('sleeves') and not (kind == 'casino' and pose.get('arms') == 'up'):
        sl = o.get('sleeve', C)
        for (x, y) in ((6, 2), (6, 3), (5, 4), (6, 4), (5, 5), (6, 5)):
            c.set(x, ty + y, sl)
            c.set(23 - x, ty + y, shade(sl, 0.85))
    if o.get('hood'):
        c.hline(7, ty - 1, 10, shade(C, 0.8))
        c.set(11, ty + 1, '#e8e2d0'); c.set(12, ty + 1, '#e8e2d0')  # strings
        c.set(11, ty + 2, '#e8e2d0'); c.set(12, ty + 3, '#e8e2d0')
        c.rect(10, ty + 5, 4, 2, shade(C, 0.75))  # pocket
    if o.get('shirt'):
        for j in range(0, 6):
            c.set(11, ty + j, '#eae4d6'); c.set(12, ty + j, '#eae4d6')
        c.set(10, ty, '#eae4d6'); c.set(13, ty, '#eae4d6')
    if o.get('tie'):
        t = o['tie']
        c.set(11, ty, t); c.set(12, ty, t)
        for j in range(1, 6):
            c.set(11, ty + j, t); c.set(12, ty + j, shade(t, 0.8))
        c.set(11, ty + 6, shade(t, 0.8))
    if o.get('chain'):
        for (x, y) in ((9, 1), (10, 2), (11, 3), (12, 3), (13, 2), (14, 1)):
            c.set(x, ty + y, '#f2c94c')
        c.set(12, ty + 4, '#f2c94c')
    hy = HEAD_Y + bob
    if o.get('bandaid'):
        c.rect(9, hy + 4, 3, 1, '#e7b98a'); c.set(10, hy + 4, '#c98f5e')
    if o.get('shades'):
        for ex in (4, 16):
            c.rect(ex, hy + 1, 4, 3, '#1d2a3a')
            c.set(ex, hy + 1, '#7f9cc0'); c.set(ex + 1, hy + 2, '#4d6787')
        c.hline(8, hy + 2, 8, '#1a1410')
    if o.get('drink') and kind == 'casino' and pose.get('arms') == 'up':
        pass
    if o.get('crown'):
        g, gs = '#f2c94c', '#b8860b'
        cy = hy + 2
        c.hline(9, cy, 6, gs)
        c.hline(9, cy - 1, 6, g)
        for x in (9, 11, 12, 14):
            c.set(x, cy - 2, g)
        c.set(9, cy - 3, g); c.set(14, cy - 3, g)
        c.set(11, cy - 1, '#e74c3c'); c.set(12, cy - 1, '#e74c3c')
        for (x, y) in ((8, cy), (8, cy - 1), (8, cy - 2), (8, cy - 3), (9, cy - 4), (10, cy - 3), (10, cy - 2),
                       (11, cy - 3), (12, cy - 3), (13, cy - 3), (13, cy - 2), (14, cy - 4), (15, cy - 3),
                       (15, cy - 2), (15, cy - 1), (15, cy)):
            if c.get(x, y)[3] == 0:
                c.set(x, y, '#5a3a06')
    return c


def build(out_dir, preview_dir=None):
    import os
    os.makedirs(out_dir, exist_ok=True)
    anims = {'work': WORK, 'sleep': SLEEP, 'casino': CASINO, 'idle': IDLE}
    layout = []
    for name, frames in anims.items():
        layout.append((name, len(frames)))
    for k, skin in enumerate(SKINS):
        frames = []
        for name, poses in anims.items():
            kind = name if name in ('work', 'casino') else 'idle'
            frames += [body_frame(skin, p, kind) for p in poses]
        sheet(frames).save(f'{out_dir}/frog-skin-{k}.png')
    for r in range(len(OUTFITS)):
        frames = []
        for name, poses in anims.items():
            kind = name if name in ('work', 'casino', 'sleep') else 'idle'
            frames += [outfit_frame(r, p, kind) for p in poses]
        sheet(frames).save(f'{out_dir}/frog-outfit-{r}.png')
    return layout


if __name__ == '__main__':
    import sys
    from PIL import Image
    out = sys.argv[1]
    layout = build(out)
    # preview: every skin x outfit, first work frame, 6x
    prev = Image.new('RGBA', (W * 6 * 6, H * 6 * 4), (40, 36, 48, 255))
    for k in range(4):
        for r in range(6):
            a = Image.open(f'{out}/frog-skin-{k}.png').crop((0, 0, W, H))
            b = Image.open(f'{out}/frog-outfit-{r}.png').crop((0, 0, W, H))
            a.alpha_composite(b)
            prev.alpha_composite(a.resize((W * 6, H * 6), Image.NEAREST), (r * W * 6, k * H * 6))
    prev.save(f'{out}/_preview.png')
    print(layout)
