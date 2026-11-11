"""Rooms, furniture and animated props for the trading floor.

Scene is 480x270 virtual pixels:
  offices   3 x (160x150) at y=0      memecoin | pumpfun | classic
  dorm      200x120 at (0,150)
  casino    280x120 at (200,150)
Positions the client needs go into layout.json.
"""
from __future__ import annotations
import math
import random
from pix import Canvas, sheet, shade, mix
import font

OUT = '#1a1410'
PATHS = {
    'memecoin': {'name': 'MEMECOIN TRADING', 'A': '#e8662f', 'wall': '#3b2430', 'floor': '#4a3328', 'poster': 'WAGMI',
                 'ticker': 'PEPE +42%  WIF -8%  BONK +13%  POPCAT +7%  '},
    'pumpfun': {'name': 'PUMP.FUN RUGS', 'A': '#9a5cf0', 'wall': '#2a2342', 'floor': '#2c2640', 'poster': 'RUG?',
                'ticker': 'NEW LAUNCH!  $DOG -99% RUG  $CAT +900%  DEV SOLD  '},
    'classic': {'name': 'CLASSIC TRADING', 'A': '#3cc6a8', 'wall': '#1f2f36', 'floor': '#26363a', 'poster': 'HODL',
                'ticker': 'BTC +2.1%  ETH +1.4%  SOL +3.0%  SPX +0.4%  '},
}
OFFICE_W, OFFICE_H = 160, 150
DESK_W, DESK_H = 40, 26
# desk positions inside an office (top-left of the desk sprite)
DESKS = [(6, 92), (60, 92), (114, 92), (33, 120), (87, 120)]
GREEN, RED = '#3ddc84', '#ff4d5e'


def light(c, f=1.25):
    return shade(c, f)


# ------------------------------------------------------------------ office

def office_bg(pid: str) -> Canvas:
    p = PATHS[pid]
    A = p['A']
    c = Canvas(OFFICE_W, OFFICE_H)
    rnd = random.Random(pid)
    wall, wall2 = p['wall'], shade(p['wall'], 1.18)
    # wall with vertical stripes
    for x in range(OFFICE_W):
        col = wall2 if (x // 6) % 2 else wall
        c.vline(x, 0, 84, col)
    # crown molding under the sign
    c.hline(0, 24, OFFICE_W, shade(wall, 0.7))
    c.hline(0, 25, OFFICE_W, shade(wall, 1.4))
    # wainscot
    c.rect(0, 66, OFFICE_W, 18, '#3a2a20')
    c.hline(0, 66, OFFICE_W, '#5a4230')
    for x in range(4, OFFICE_W, 20):
        c.frame(x, 69, 16, 12, '#2a1d15')
        c.hline(x + 1, 70, 14, '#4a3626')
    c.hline(0, 84, OFFICE_W, '#1a120c')
    # floor
    fl = p['floor']
    for y in range(85, OFFICE_H):
        for x in range(OFFICE_W):
            if pid == 'pumpfun':
                col = fl if ((x // 10) + (y // 10)) % 2 else shade(fl, 1.25)
            elif pid == 'memecoin':
                col = shade(fl, 1.1) if (x + y * 2) % 7 == 0 else fl
            else:
                col = shade(fl, 1.15) if (y // 3) % 2 and x % 5 == 0 else fl
            c.set(x, y, col)
    for x in range(OFFICE_W):
        c.set(x, 85, shade(fl, 0.6)); c.set(x, 86, shade(fl, 0.8))

    # window with the night city
    wx, wy, ww, wh = 10, 32, 34, 28
    c.rect(wx - 2, wy - 2, ww + 4, wh + 4, '#5a4230')
    c.frame(wx - 2, wy - 2, ww + 4, wh + 4, OUT)
    for y in range(wh):
        c.hline(wx, wy + y, ww, mix('#0d1530', '#25305a', y / wh))
    c.set(wx + 26, wy + 5, '#f4ead2'); c.set(wx + 27, wy + 5, '#f4ead2'); c.set(wx + 26, wy + 6, '#f4ead2')
    for bx in range(wx, wx + ww, 5):
        bh = rnd.randint(8, 20)
        c.rect(bx, wy + wh - bh, 4, bh, '#111827')
        for yy in range(wy + wh - bh + 2, wy + wh - 1, 3):
            if rnd.random() < 0.5:
                c.set(bx + 1 + rnd.randint(0, 1), yy, '#f7d774')
    c.vline(wx + ww // 2, wy, wh, '#5a4230'); c.hline(wx, wy + wh // 2, ww, '#5a4230')
    c.hline(wx - 3, wy + wh + 2, ww + 6, '#7a5a40')

    # big ticker screen frame (content is animated, see ticker_frames)
    tx, ty = 58, 30
    c.rect(tx - 3, ty - 3, 50, 34, '#2b2b33')
    c.frame(tx - 3, ty - 3, 50, 34, OUT)
    c.rect(tx, ty, 44, 28, '#05070a')
    c.hline(tx - 2, ty - 2, 48, '#4a4a55')
    c.rect(tx + 18, ty + 31, 8, 4, '#2b2b33')

    # poster on the right
    px, py = 116, 32
    c.rect(px, py, 30, 26, '#efe6d0')
    c.frame(px, py, 30, 26, OUT)
    c.rect(px + 2, py + 2, 26, 12, A)
    if pid == 'memecoin':
        # rocket
        for i in range(6):
            c.set(px + 8 + i, py + 11 - i, '#f4ead2')
        c.rect(px + 14, py + 4, 3, 3, '#f4ead2'); c.set(px + 7, py + 12, '#f2c94c')
    elif pid == 'pumpfun':
        c.ellipse(px + 15, py + 8, 7, 4, '#3ddc84'); c.rect(px + 8, py + 8, 7, 4, '#f4ead2')
    else:
        pts = [(2, 10), (6, 8), (10, 9), (14, 6), (18, 7), (22, 3), (25, 4)]
        for (a, b), (cc, d) in zip(pts, pts[1:]):
            for t in range(6):
                c.set(px + round(a + (cc - a) * t / 5), py + round(b + (d - b) * t / 5), '#f4ead2')
    tw = font.width(p['poster'], font.SMALL)
    font.draw(c, px + 15 - tw // 2, py + 17, p['poster'], OUT, font.SMALL)

    # plant in the corner
    c.rect(148, 72, 9, 10, '#a0522d'); c.frame(148, 72, 9, 10, OUT); c.hline(147, 72, 11, '#c0703d')
    for (x, y) in ((150, 70), (152, 66), (154, 68), (151, 63), (155, 64), (149, 67), (153, 61), (156, 69)):
        c.rect(x, y, 2, 4, '#3f8f3a'); c.set(x, y, '#5fbf4a')

    # bum vibe: litter on the floor
    for (x, y) in ((4, 143), (150, 140), (78, 146), (128, 112)):
        c.rect(x, y, 3, 2, '#d8d0bc'); c.set(x + 1, y, '#b0a890')
    c.rect(150, 118, 7, 5, '#c9772f'); c.frame(150, 118, 7, 5, OUT)  # pizza box
    c.set(152, 120, '#e8c060')
    return c


def office_sign(pid: str, lit: bool) -> Canvas:
    p = PATHS[pid]
    A = p['A']
    c = Canvas(148, 20)
    c.rect(0, 0, 148, 20, '#120e18')
    c.frame(0, 0, 148, 20, OUT)
    c.frame(1, 1, 146, 18, shade(A, 0.8) if lit else shade(A, 0.35))
    w = font.width(p['name'])
    x = (148 - w) // 2
    if lit:
        font.draw(c, x, 6, p['name'], light(A, 1.35), shadow=shade(A, 0.55))
    else:
        font.draw(c, x, 6, p['name'], shade(A, 0.4))
    return c


def desk() -> Canvas:
    c = Canvas(DESK_W, DESK_H)
    top, topL, front, frontD = '#b07a4a', '#c99260', '#8b5a33', '#6e4426'
    c.rect(0, 4, DESK_W, 4, top)
    c.hline(0, 4, DESK_W, topL)
    c.rect(1, 8, DESK_W - 2, 16, front)
    c.vline(1, 8, 16, shade(front, 1.12))
    for x in (13, 26):
        c.vline(x, 9, 14, frontD)
    for x in (5, 30):
        c.rect(x, 14, 4, 1, '#d8b070')
    c.rect(1, 23, 3, 3, frontD); c.rect(DESK_W - 4, 23, 3, 3, frontD)
    c.frame(0, 4, DESK_W, 20, OUT)
    c.vline(0, 23, 3, OUT); c.vline(3, 23, 3, OUT); c.vline(DESK_W - 1, 23, 3, OUT); c.vline(DESK_W - 4, 23, 3, OUT)
    # keyboard
    c.rect(19, 5, 14, 2, '#3a3a44'); c.hline(19, 5, 14, '#5a5a66')
    for x in range(20, 32, 2):
        c.set(x, 5, '#8a8a99')
    # mug and papers
    c.rect(35, 1, 3, 4, '#e8e2d0'); c.set(38, 2, '#e8e2d0'); c.set(36, 0, '#9a9a9a')
    c.rect(4, 2, 6, 2, '#f4ead2'); c.frame(4, 2, 6, 2, '#b8b0a0')
    return c


def chair() -> Canvas:
    c = Canvas(20, 22)
    c.rect(3, 0, 14, 18, '#2e2e38')
    c.rect(4, 1, 12, 16, '#3c3c48')
    c.hline(4, 1, 12, '#55556a')
    c.frame(3, 0, 14, 18, OUT)
    c.rect(9, 18, 2, 4, '#222222')
    return c


def monitor() -> Canvas:
    c = Canvas(18, 16)
    body, bodyD = '#d9d2bf', '#a9a08a'
    c.rect(0, 0, 18, 13, body)
    c.vline(17, 0, 13, bodyD); c.hline(0, 12, 18, bodyD)
    c.frame(0, 0, 18, 13, OUT)
    c.rect(3, 2, 12, 9, '#0b0f14')
    c.set(4, 3, '#2a3340'); c.set(5, 3, '#2a3340')
    c.rect(6, 13, 6, 2, bodyD); c.rect(4, 15, 10, 1, OUT)
    c.set(15, 11, '#3ddc84')
    return c


def screen_frames(pid: str, n=8) -> list[Canvas]:
    """12x9 candle chart that scrolls. Pump.fun charts are wilder."""
    rnd = random.Random('screen' + pid)
    vol = {'memecoin': 2.2, 'pumpfun': 3.5, 'classic': 1.0}[pid]
    level, bars = 4.5, []
    for _ in range(12 + n * 2):
        o = level
        level = max(1.5, min(7.5, level + rnd.uniform(-vol, vol) * 0.7))
        if pid == 'pumpfun' and rnd.random() < 0.08:
            level = 1.5
        bars.append((o, level))
    frames = []
    for f in range(n):
        c = Canvas(12, 9)
        c.rect(0, 0, 12, 9, '#06110c' if pid != 'pumpfun' else '#0d0818')
        for gy in (2, 5):
            for gx in range(0, 12, 2):
                c.set(gx, gy, '#12241b' if pid != 'pumpfun' else '#1d1430')
        for i in range(6):
            o, cl = bars[f * 2 + i]
            col = GREEN if cl >= o else RED
            lo, hi = sorted((o, cl))
            x = i * 2
            for y in range(int(8 - hi), int(9 - lo)):
                c.set(x, y, col)
        frames.append(c)
    return frames


def ticker_frames(pid: str, n=16) -> list[Canvas]:
    """44x28 wall screen: a line chart plus a scrolling ticker tape."""
    p = PATHS[pid]
    rnd = random.Random('tick' + pid)
    pts, v = [], 10.0
    for _ in range(44 + n * 3):
        v = max(2, min(17, v + rnd.uniform(-2.5, 2.6)))
        if pid == 'pumpfun' and rnd.random() < 0.05:
            v = 2
        pts.append(v)
    tape = font.render(p['ticker'] * 2, font.SMALL)
    frames = []
    for f in range(n):
        c = Canvas(44, 28)
        c.rect(0, 0, 44, 28, '#05070a')
        for gx in range(0, 44, 4):
            for gy in range(1, 20, 2):
                c.set(gx, gy, '#0f1a22')
        seg = pts[f * 3: f * 3 + 44]
        prev = None
        for x, val in enumerate(seg):
            y = int(19 - val)
            up = prev is None or val >= seg[x - 1]
            col = GREEN if up else RED
            c.set(x, y, col)
            if prev is not None:
                for yy in range(min(prev, y), max(prev, y)):
                    c.set(x, yy, col)
            for yy in range(y + 1, 20):
                if (x + yy) % 3 == 0:
                    c.set(x, yy, shade(col, 0.35))
            prev = y
        c.hline(0, 20, 44, p['A'])
        off = (f * 4) % (tape.shape[1] // 2)
        for j in range(5):
            for i in range(44):
                if tape[j, (i + off) % tape.shape[1]]:
                    c.set(i, 22 + j, '#f7d774')
        frames.append(c)
    return frames


# ------------------------------------------------------------------ dorm

DORM_W, DORM_H = 200, 120
BUNKS = [8, 56, 104, 152]          # x of each bunk frame (44 wide)
BED_ROWS = [44, 88]                 # mattress top y for upper and lower bed


def dorm_bg() -> Canvas:
    c = Canvas(DORM_W, DORM_H)
    for y in range(40):
        for x in range(DORM_W):
            c.set(x, y, '#1c2140' if (x // 8 + y // 8) % 2 else '#20264a')
    c.hline(0, 40, DORM_W, '#0f1226')
    for y in range(41, DORM_H):
        for x in range(DORM_W):
            plank = (y - 41) // 6
            col = '#4e3626' if plank % 2 else '#5a3f2e'
            if (x + plank * 13) % 37 == 0:
                col = '#3a281c'
            c.set(x, y, col)
    # window with moon
    c.rect(86, 6, 28, 22, '#0a0f24'); c.frame(85, 5, 30, 24, '#6b4a32')
    c.ellipse(105, 13, 4, 4, '#f4ead2'); c.ellipse(107, 12, 3, 3, '#0a0f24')
    for (x, y) in ((90, 9), (96, 20), (110, 23), (92, 15)):
        c.set(x, y, '#f4ead2')
    c.vline(99, 6, 22, '#6b4a32')
    w = font.width('DORM', font.SMALL)
    c.rect(6, 6, w + 8, 11, '#2c1e14'); c.frame(6, 6, w + 8, 11, '#8a6a40')
    font.draw(c, 10, 9, 'DORM', '#f7d774', font.SMALL)
    # bunk beds
    for bx in BUNKS:
        post, postD = '#7a5236', '#5a3a24'
        for px in (bx, bx + 42):
            c.rect(px, 22, 3, 92, post); c.vline(px, 22, 92, shade(post, 1.2)); c.frame(px, 22, 3, 92, OUT)
        for my in BED_ROWS:
            c.rect(bx + 3, my + 6, 39, 4, postD); c.frame(bx + 3, my + 6, 39, 4, OUT)
            c.rect(bx + 4, my, 37, 6, '#d8d0c0'); c.hline(bx + 4, my, 37, '#efe8d8'); c.frame(bx + 4, my, 37, 6, OUT)
            c.rect(bx + 6, my - 3, 10, 4, '#f4ead2'); c.frame(bx + 6, my - 3, 10, 4, OUT)  # pillow
        c.rect(bx + 38, 30, 2, 14, '#9a7050')  # ladder
        for ly in range(32, 44, 3):
            c.hline(bx + 36, ly, 4, '#9a7050')
    # lamp and socks on the floor
    c.rect(2, 108, 5, 3, '#c0392b'); c.rect(193, 110, 4, 2, '#f4ead2')
    return c


def blanket(color: str) -> Canvas:
    c = Canvas(37, 9)
    c.rect(0, 0, 37, 9, color)
    c.hline(0, 0, 37, light(color, 1.3))
    for x in range(0, 37, 6):
        c.vline(x, 1, 8, shade(color, 0.82))
    for y in (3, 6):
        c.hline(0, y, 37, shade(color, 0.88))
    c.frame(0, 0, 37, 9, OUT)
    return c


def zzz() -> Canvas:
    c = Canvas(5, 5)
    font.draw(c, 1, 0, 'Z', '#f4ead2', font.SMALL)
    return c


# ------------------------------------------------------------------ casino

CASINO_W, CASINO_H = 280, 120
SLOT_X = [6, 30, 54, 78]
TABLE = (100, 70, 104, 34)      # x, y, w, h of the roulette table (front layer)
BAR = (204, 70, 74, 30)


def casino_seats():
    seats = []
    for i in range(6):   # roulette table, frogs sit behind it
        seats.append({'x': 100 + i * 17, 'y': 47 if i % 2 == 0 else 51, 'spot': 'table'})
    for i in range(4):   # bar stools
        seats.append({'x': 204 + i * 17, 'y': 48 if i % 2 == 0 else 51, 'spot': 'bar'})
    for x in SLOT_X:     # slot machines, frogs sit in front on stools
        seats.append({'x': x - 2, 'y': 66, 'spot': 'slots'})
    # reorder so the first seats are the nicest
    order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    return [seats[i] for i in order]


def casino_bg(open_: bool) -> Canvas:
    c = Canvas(CASINO_W, CASINO_H)
    wall = '#4a1024' if open_ else '#241820'
    for y in range(48):
        for x in range(CASINO_W):
            col = wall
            if (x // 4) % 2 == 0 and open_:
                col = shade(wall, 1.12)
            c.set(x, y, col)
    c.hline(0, 20, CASINO_W, '#b8860b' if open_ else '#4a3a2a')
    c.hline(0, 47, CASINO_W, '#b8860b' if open_ else '#4a3a2a')
    for y in range(48, CASINO_H):
        for x in range(CASINO_W):
            if open_:
                d = ((x - 140) ** 2 // 60 + (y - 84) ** 2 // 12) % 9
                col = '#6a0f1e' if d < 6 else '#7a1626'
                if (x + y) % 16 == 0:
                    col = '#c8961e'
            else:
                col = '#2e2420' if (x // 12 + y // 6) % 2 else '#342a24'
            c.set(x, y, col)
    if not open_:
        # boarded up
        for i, (x, y, w) in enumerate(((60, 30, 160), (70, 60, 150), (50, 90, 170))):
            c.rect(x, y, w, 8, '#7a5a3a'); c.frame(x, y, w, 8, OUT)
            c.set(x + 4, y + 3, '#cfcfcf'); c.set(x + w - 5, y + 3, '#cfcfcf')
        return c
    # slot machines along the back-left wall
    for x in SLOT_X:
        c.rect(x, 24, 20, 40, '#8a1c2c'); c.frame(x, 24, 20, 40, OUT)
        c.rect(x + 2, 26, 16, 4, '#f2c94c')
        c.rect(x + 3, 33, 14, 9, '#f4ead2'); c.frame(x + 3, 33, 14, 9, OUT)
        for i, sym in enumerate(('#e74c3c', '#3ddc84', '#f2c94c')):
            c.rect(x + 4 + i * 4, 36, 3, 3, sym)
        c.rect(x + 3, 45, 14, 6, '#5a0f1a')
        c.vline(x + 19, 34, 10, '#cfcfcf'); c.rect(x + 18, 32, 3, 3, '#e74c3c')
    # bar shelf with bottles
    bx = 206
    c.rect(bx, 26, 70, 3, '#5a3a24'); c.rect(bx, 40, 70, 3, '#5a3a24')
    cols = ['#3ddc84', '#e8662f', '#9a5cf0', '#f2c94c', '#4aa8ff', '#e74c3c']
    for i in range(10):
        x = bx + 3 + i * 7
        col = cols[i % len(cols)]
        c.rect(x, 33, 3, 7, col); c.rect(x + 1, 30, 1, 3, col); c.set(x, 34, light(col, 1.4))
        col2 = cols[(i + 2) % len(cols)]
        c.rect(x + 1, 19, 3, 7, col2); c.set(x + 2, 17, col2)
    # chandelier glow
    for r in range(20, 0, -4):
        pass
    return c


def casino_sign(lit: bool) -> Canvas:
    c = Canvas(64, 16)
    c.rect(0, 0, 64, 16, '#1a0c12'); c.frame(0, 0, 64, 16, '#b8860b' if lit else '#4a3a2a')
    w = font.width('CASINO')
    font.draw(c, (64 - w) // 2, 4, 'CASINO', '#ffd166' if lit else '#4a3a2a', shadow='#a0482a' if lit else None)
    return c


def closed_sign() -> Canvas:
    w = font.width('FOR SALE')
    c = Canvas(w + 10, 13)
    c.rect(0, 0, w + 10, 13, '#efe6d0'); c.frame(0, 0, w + 10, 13, OUT)
    font.draw(c, 5, 3, 'FOR SALE', '#c0392b')
    return c


def casino_front() -> Canvas:
    """Everything that is drawn in front of seated frogs."""
    c = Canvas(CASINO_W, CASINO_H)
    x, y, w, h = TABLE
    # roulette table: wood rim + green felt
    c.rect(x, y, w, h, '#5a2e16')
    c.rect(x + 3, y + 3, w - 6, h - 10, '#11743a')
    c.hline(x + 3, y + 3, w - 6, '#1d9a50')
    for i in range(6):
        cx = x + 34 + i * 10
        c.rect(cx, y + 8, 8, 10, '#0d5c2d'); c.frame(cx, y + 8, 8, 10, '#e8e2d0')
        col = '#c0392b' if i % 2 else '#1a1a1a'
        c.rect(cx + 2, y + 11, 4, 4, col)
    c.rect(x + 2, y + h - 7, w - 4, 7, '#3e1e0e')
    c.frame(x, y, w, h, OUT)
    # chip stacks
    for (cx, cy, col) in ((x + 70, y + 20, '#e74c3c'), (x + 84, y + 18, '#4aa8ff'), (x + 92, y + 21, '#f2c94c')):
        for k in range(3):
            c.rect(cx, cy - k * 2, 5, 2, col); c.hline(cx, cy - k * 2, 5, light(col, 1.3))
    # bar counter
    bx, by, bw, bh = BAR
    c.rect(bx, by, bw, 4, '#c99260'); c.hline(bx, by, bw, '#e0b080')
    c.rect(bx + 1, by + 4, bw - 2, bh - 4, '#6e2a1a')
    for i in range(bx + 6, bx + bw - 4, 12):
        c.vline(i, by + 6, bh - 8, '#8a3a24')
    c.hline(bx + 1, by + bh - 3, bw - 2, '#b8860b')
    c.frame(bx, by, bw, bh, OUT)
    # stools in front of the slot machines
    for sx in SLOT_X:
        c.rect(sx + 5, 88, 10, 3, '#c0392b'); c.frame(sx + 5, 88, 10, 3, OUT)
        c.rect(sx + 9, 91, 2, 12, '#888888'); c.rect(sx + 6, 102, 8, 2, '#555555')
    return c


def roulette_frames(n=8) -> list[Canvas]:
    frames = []
    for f in range(n):
        c = Canvas(28, 16)
        c.ellipse(14, 8, 13.5, 7.5, '#3e1e0e')
        c.ellipse(14, 8, 11.5, 6, '#b8860b')
        for k in range(16):
            a0 = (k / 16) * math.tau + f * (math.tau / 32)
            col = '#c0392b' if k % 2 else '#151515'
            if k == 0:
                col = '#11743a'
            for r in (8, 9, 10):
                x = 14 + math.cos(a0) * r
                y = 8 + math.sin(a0) * r * 0.5
                c.set(int(x), int(y), col)
        c.ellipse(14, 8, 5, 2.5, '#5a2e16')
        c.set(14, 7, '#f2c94c'); c.set(14, 8, '#f2c94c')
        ba = -f * (math.tau / 8)
        c.set(int(14 + math.cos(ba) * 10), int(8 + math.sin(ba) * 5), '#ffffff')
        frames.append(c)
    return frames


def slot_lights(n=4) -> list[Canvas]:
    frames = []
    for f in range(n):
        c = Canvas(16, 4)
        for i in range(8):
            on = (i + f) % 2 == 0
            c.rect(i * 2, 0, 2, 4, '#fff3b0' if on else '#c8961e')
        frames.append(c)
    return frames
