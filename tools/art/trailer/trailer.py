"""Frog Traders mini trailer. Renders every frame at 640x360 and pipes them to ffmpeg at 1920x1080.

  python3 trailer.py            -> build/trailer-video.mp4 + build/events.json (sound cues)
  python3 trailer.py --still 12.3  -> one frame as PNG, for checking
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import fx
from fx import W, H, FPS, ease_out, ease_in, ease_back, clamp01
from px2 import INK, Canvas, mix, sh
from menu_kit import GOLD, GOLD_HI, GOLD_LO, text_mask
import scenes as S

HERE = Path(__file__).parent
BUILD = HERE / 'build'
FRAMES = BUILD / 'frames'
GREEN_HI, GREEN = (200, 255, 170), (110, 236, 90)
RED_HI, RED = (255, 170, 160), (255, 77, 109)
SOL_A, SOL_B = (190, 120, 255), (60, 240, 160)

EVENTS: list[tuple[float, str]] = []
REVEAL_TEXT = 'YOU PULLED THE KING!'


def crossed(t, ts):
    return t - 1 / FPS < ts <= t + 1e-9


def cue(t, name):
    EVENTS.append((round(t, 3), name))


def C(a):
    c = Canvas(W, H)
    c.a = a
    return c


def load_shot(name):
    files = sorted((FRAMES / name).glob('*.png'))
    return [np.array(Image.open(f).convert('RGBA')) for f in files]


def office_layout(room):
    return json.loads((S.A / 'office' / room / 'layout.json').read_text())


# =================================================================== sets
print('building sets...')
TITLE_BG, LINEUP = S.title_set()
NEON_BACK, NEON_LIT, NEON_GLOW = S.neon_sign()
STAGE, DESK_Y = S.recruit_set()
PACK, TEAR = S.make_pack()
CARD_BACK = S.card_back_img()
CARD_FRONT = S.card_front_img()
STREET, WINDOWS, SIGNS, STREET_Y = S.street_set()
HALL, BUSTS = S.boss_hall()
print('loading footage...')
class _Lazy(dict):
    def __missing__(self, k):
        self[k] = load_shot(k)
        return self[k]


SHOT = _Lazy()
LAY = {k: office_layout(k) for k in ('memecoin', 'pumpfun', 'classic')}
RAYS_D = np.hypot(fx.XX - 320, fx.YY - 170)
RAYS_A = np.arctan2(fx.YY - 170, fx.XX - 320)


def rays(dst, t, strength, cols=((255, 200, 90), (255, 90, 110)), cx=320, cy=170):
    if strength <= 0:
        return
    d = np.hypot(fx.XX - cx, fx.YY - cy) if (cx, cy) != (320, 170) else RAYS_D
    a = np.arctan2(fx.YY - cy, fx.XX - cx) if (cx, cy) != (320, 170) else RAYS_A
    phase = (a / (2 * math.pi) * 12 + t * 0.35) % 1
    beam = phase < 0.42
    fall = np.clip(1 - d / 260, 0, 1) * strength
    m = beam & (fx.BAYER < fall * 0.9)
    alt = (np.floor(a / (2 * math.pi) * 12 + t * 0.35) % 2) == 0
    for k, col in enumerate(cols):
        mm = m & (alt if k == 0 else ~alt)
        dst[mm, :3] = (dst[mm, :3] * 0.45 + np.array(col) * 0.55).astype(np.uint8)


def neon_on_state(t, t_on):
    """Neon sign power-up: off, a few flickers, then steady."""
    if t < t_on:
        return 0.0
    seq = [(0.06, 1), (0.08, 0), (0.05, 1), (0.14, 0), (0.07, 1), (0.05, 0)]
    x = t - t_on
    for dur, v in seq:
        if x < dur:
            return float(v)
        x -= dur
    return 1.0


# =================================================================== 1. title
def sc_title(t, f, T0, dur):
    out = TITLE_BG.copy()
    on = neon_on_state(t, 0.55)
    if t > 0.55 and on == 0:
        on = 0.0
    fx.over(out, NEON_BACK)
    if on:
        fx.over(out, NEON_GLOW)
        fx.over(out, NEON_LIT)
    shade = 0.62 + 0.3 * clamp01((t - 1.0) / 0.4)
    for (_, s, x, y) in LINEUP:
        fx.blit(out, s, x, y, shade=shade)
    c = C(out)
    if t > 1.35:
        fx.plain(c, 'AFK TRADING ON SOLANA'[:int((t - 1.35) * 34)], 320, 96, (255, 206, 130), 'title')
    if t < 0.35:
        fx.fade_black(out, 1 - t / 0.35)
    if t > dur - 0.25:
        fx.fade_black(out, (t - (dur - 0.25)) / 0.25)
    return out


# =================================================================== 2. pack
P2 = fx.Particles(5)
LADDER_Y = 316


def ladder(c, t_roll, t, final='mythic'):
    names = [r.upper() for r in S.RARITIES]
    widths = [text_mask(n, 'body').shape[1] + 12 for n in names]
    gap = 6
    total = sum(widths) + gap * 5
    x = 320 - total // 2
    if t < t_roll:
        hi = -1
    else:
        steps = int(min(17, ((t - t_roll) * 9) ** 1.25))
        hi = 5 if steps >= 17 else steps % 6
    for i, (n, w) in enumerate(zip(names, widths)):
        col = S.RARITY_COL[S.RARITIES[i]]
        on = i == hi
        fill = sh(col, .55) if on else (22, 18, 26)
        fx.chip(c, x, LADDER_Y, x + w, LADDER_Y + 15, col if on else sh(col, .5), fill)
        m = text_mask(n, 'body')
        fx.stamp(c, m, x + 6, LADDER_Y + 5, (255, 255, 255) if on else sh(col, .8))
        if on and hi == 5 and steps >= 17:
            for k in range(3):
                fx.sparkle(c.a, x + 4 + (k * 23 + int(t * 30)) % w, LADDER_Y - 3 + (k % 2) * 21, 1)
        x += w + gap
    return hi


def sc_pack(t, f, T0, dur):
    out = STAGE.copy()
    c = C(out)
    px, py = 320 - PACK.shape[1] // 2, 104
    t_land, t_shake, t_tear, t_flip, t_reveal = 0.45, 0.9, 2.25, 3.0, 3.3
    if f == 0:
        P2.p.clear()
    # light rays build up behind the pack
    if t < t_tear:
        rays(out, t, clamp01((t - t_shake) / 1.4) * .55, cols=((180, 120, 255), (255, 120, 220)))
    else:
        rays(out, t, .35 + .65 * clamp01((t - t_reveal) / .3) if t > t_flip else .5)
    # caption
    if t > 0.25:
        if t < t_reveal + 0.1:
            fx.band(out, 10, 50)
            fx.title(c, 'OPEN A PACK', 320, 16, reveal=(t - .25) / .35)
        else:
            fx.band(out, 10, 50)
            fx.title(c, REVEAL_TEXT, 320, 16, RED_HI, RED, reveal=(t - t_reveal - .1) / .4)
    # the pack
    if t < t_tear:
        if t < t_land:
            y = -130 + (py + 130) * ease_back(t / t_land)
        else:
            y = py
        dx = dy = 0
        if t > t_shake:
            amp = 1 + 3 * clamp01((t - t_shake) / (t_tear - t_shake))
            dx = round(math.sin(t * 61) * amp)
            dy = round(math.cos(t * 47) * amp * .5)
        fx.blit(out, PACK, px + dx, y + dy)
        if t > t_shake:
            gl = clamp01((t - t_shake) / 1.2)
            for k in range(int(6 * gl)):
                a = t * 3 + k * 1.05
                fx.sparkle(out, 320 + math.cos(a) * (52 + k * 3), 160 + math.sin(a) * 66, 1 + (k + f) % 2)
        if crossed(t, t_land):
            P2.burst(320, py + PACK.shape[0], 18, speed=(1, 3), cols=[(150, 120, 140), (110, 90, 110)], life=(.3, .6), grav=0.05)
    else:
        k = t - t_tear
        if k < 0.6:
            top = PACK[:TEAR + 1]
            body = PACK[TEAR + 1:]
            fx.blit(out, top, px + 30 * ease_out(k / .6), py - 90 * ease_out(k / .6), alpha=1 - k / .6)
            fx.blit(out, body, px, py + TEAR + 1 + 260 * ease_in(k / .6))
        # card rises out of the pack, then flips
        cx = 320
        rise = ease_out(clamp01(k / .5))
        cy = int(py + 40 - 44 * rise)
        if t < t_flip:
            card = CARD_BACK
            wf = 1.0
        else:
            p = clamp01((t - t_flip) / .3)
            wf = abs(math.cos(p * math.pi))
            card = CARD_BACK if p < .5 else CARD_FRONT
        if t > t_reveal:
            cy += round(math.sin((t - t_reveal) * 2.4) * 2)
        w = max(2, round(card.shape[1] * wf))
        img = np.array(Image.fromarray(card).resize((w, card.shape[0]), Image.NEAREST))
        fx.blit(out, img, cx - w // 2, cy)
        if crossed(t, t_tear):
            P2.burst(320, py + 10, 40, speed=(2, 6), cols=[(200, 160, 255), (255, 255, 255), (255, 220, 120)])
        if crossed(t, t_reveal):
            P2.burst(320, cy + 60, 70, speed=(2, 7), cols=[(255, 77, 109), (255, 226, 130), (255, 255, 255)], life=(.8, 1.6))
        if t > t_reveal:
            for k2 in range(5):
                a = t * 1.6 + k2 * 1.256
                fx.sparkle(out, 320 + math.cos(a) * 70, cy + 70 + math.sin(a) * 84, 1 + (f // 3 + k2) % 2)
    P2.step()
    P2.draw(out)
    ladder(c, 2.35, t)
    # flashes
    if t_tear <= t < t_tear + .25:
        fx.flash(out, .8 * (1 - (t - t_tear) / .25))
    if t_reveal <= t < t_reveal + .3:
        fx.flash(out, .9 * (1 - (t - t_reveal) / .3), (255, 240, 220))
    if t < 0.2:
        fx.fade_black(out, 1 - t / .2)
    if t > dur - .2:
        fx.fade_black(out, (t - (dur - .2)) / .2)
    return out


# =================================================================== 3. street
SIGN_ON = [0.45, 0.8, 1.15]
PICK = [(3.3, 0), (3.6, 1), (3.9, 2), (4.2, 0), (4.5, 1), (4.85, 2), (5.25, 0)]


def sc_street(t, f, T0, dur):
    out = STREET.copy()
    c = C(out)
    for (wx, wy, col, ph, flick) in WINDOWS:
        on = True
        if flick:
            on = math.sin(t * 2.3 + ph * 3) > -0.2
        if on:
            k = .85 + .15 * math.sin(t * 1.7 + ph)
            out[wy:wy + 10, wx:wx + 8, :3] = sh(col, k)
            out[wy + 5, wx:wx + 8, :3] = sh(col, k * .8)
    for i, s in enumerate(SIGNS):
        on = neon_on_state(t, SIGN_ON[i])
        if on:
            fx.over(out, s['glow'])
            out[s['rim'], :3] = s['spec']['neon']
            out[s['letters'], :3] = mix(s['spec']['neon'], (255, 255, 255), .6)
        if crossed(t, SIGN_ON[i]):
            cue(T0 + t, 'blip')
        # hidden crowd counter over the roof
        if t > 1.7:
            x = s['cx']
            y = s['top'] - 30
            fx.chip(c, x - 34, y, x + 33, y + 17, sh(s['spec']['neon'], .9))
            if t < 2.6:
                digits = str(int((t * 37 + i * 13) * 97) % 900 + 100)
            else:
                digits = '???'
            m = text_mask(digits + ' FROGS', 'body')
            fx.stamp(c, m, x - m.shape[1] // 2, y + 6, (255, 255, 255) if digits == '???' else (200, 200, 210))
    if crossed(t, 2.6):
        cue(T0 + t, 'hidden')
    # caption
    if t > 0.25:
        fx.band(out, 8, 44, .6)
        fx.title(c, 'PICK 1 OF 3 OFFICES', 320, 13, reveal=(t - .25) / .4)
    if t > 2.6:
        fx.band(out, 318, 344, .55)
        fx.plain(c, 'NOBODY KNOWS WHERE THE CROWD GOES', 320, 324, (255, 230, 200), 'title')
    # selector hopping between buildings, lands on MEMECOIN
    sel = None
    for (ts, i) in PICK:
        if t >= ts:
            sel = i
    if sel is not None:
        if any(crossed(t, ts) for ts, _ in PICK):
            cue(T0 + t, 'tick')
        sp = SIGNS[sel]['spec']
        x0, x1 = sp['x0'] - 6, sp['x0'] + sp['w'] + 5
        y0, y1 = sp['top'] - 38, STREET_Y + 4
        landed = t >= PICK[-1][0]
        col = GOLD_HI if (not landed or (f // 3) % 2) else (255, 255, 255)
        L = 14
        for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            for k in range(3):
                c.hline(min(cx, cx + sx * L), max(cx, cx + sx * L), cy + sy * k, INK if k == 2 else col)
                c.vline(cx + sx * k, min(cy, cy + sy * L), max(cy, cy + sy * L), INK if k == 2 else col)
        if landed:
            k = t - PICK[-1][0]
            if k < 1 / FPS:
                cue(T0 + t, 'select')
            fx.title(c, 'GO!', (x0 + x1) // 2, int(150 - 10 * ease_back(clamp01(k / .25))), GREEN_HI, GREEN, scale=3)
    if t < .2:
        fx.fade_black(out, 1 - t / .2)
    if t > dur - .35:
        fx.fade_black(out, (t - (dur - .35)) / .35)
    return out


# =================================================================== 4. work
BAL = {'v': 0}
POP_RNG = np.random.default_rng(3)
POPS: list = []


def desk_points(room):
    return [(d['frog'][0] + 30, d['screen'][1] - 4) for d in LAY[room]['desks']]


def work_overlay(out, t, T0, room, captions, pop_from, frog_pops=None, hud_from=0.0):
    c = C(out)
    pts = desk_points(room)
    # coins
    if t >= pop_from:
        n = int((t - pop_from) * 3.2)
        while sum(1 for p in POPS if p['room'] == room) < n + 1:
            i = int(POP_RNG.integers(0, 5))
            amt = int(POP_RNG.choice([8, 12, 15, 21, 34, 55]))
            POPS.append(dict(t=T0 + t, i=i, amt=amt, room=room))
            BAL['v'] += amt * 37
            cue(T0 + t, 'coin')
    for p in POPS:
        if p['room'] != room:
            continue
        x, y = pts[p['i']]
        fx.coin_pop(out, x, y, (T0 + t) - p['t'], p['amt'])
    # frogs arriving
    if frog_pops:
        for (tp, i) in frog_pops:
            k = t - tp
            d = LAY[room]['desks'][i]
            x, y = d['frog'][0], d['frog'][1] - 40
            if 0 <= k < 1 / FPS:
                P4.burst(x, y, 24, speed=(1, 3.5), cols=[(255, 255, 255), (200, 255, 170), (255, 226, 130)], life=(.3, .7), grav=.04)
                cue(T0 + t, 'pop')
            if 0 <= k < .12:
                for yy in range(max(0, y - 40), min(H, y + 50)):
                    for xx in range(x - 26, x + 27):
                        if fx.BAYER1[yy, xx] < .5 * (1 - k / .12):
                            out[yy, xx, :3] = (255, 255, 255)
    P4.step()
    P4.draw(out)
    # captions over the room sign
    for (t0, t1, text, top, bot) in captions:
        if t0 <= t < t1:
            fx.band(out, 16, 56, .7)
            fx.title(c, text, 320, 22, top, bot, reveal=(t - t0) / .35)
    if t >= hud_from:
        slide = ease_out(clamp01((t - hud_from) / .3))
        fx.balance_hud(out, BAL['v'], x=int(8 - 160 * (1 - slide)), y=64)


P4 = fx.Particles(9)
WORK_CAPS = [(0.2, 2.7, 'SEND FROGS TO WORK', GOLD_HI, GOLD), (2.7, 99, 'EARN $FROG EVERY DAY', GOLD_HI, GOLD)]
FROG_TIMES = [(0.7 + 0.32 * k, i) for k, i in enumerate([2, 0, 4, 1, 3])]


def sc_meme(t, f, T0, dur):
    out = SHOT['meme_work'][min(f, len(SHOT['meme_work']) - 1)].copy()
    work_overlay(out, t, T0, 'memecoin', WORK_CAPS, pop_from=2.3, frog_pops=FROG_TIMES, hud_from=2.3)
    if t < .2:
        fx.fade_black(out, 1 - t / .2)
    return out


def sc_room(name, room):
    def fn(t, f, T0, dur):
        out = SHOT[name][min(f + 10, len(SHOT[name]) - 1)].copy()
        work_overlay(out, t + 10, T0 - 10, room, [(0, 99, 'EARN $FROG EVERY DAY', GOLD_HI, GOLD)], pop_from=10, hud_from=0)
        if f == 0:
            cue(T0, 'whoosh')
        if name == 'classic' and t > dur - .2:
            fx.fade_black(out, (t - (dur - .2)) / .2)
        return out
    return fn


# =================================================================== 5. boss hall
DROP = [0.3, 0.62, 0.94, 1.26]
P5 = fx.Particles(21)


def sc_hall(t, f, T0, dur):
    landed = sum(1 for d in DROP if t >= d + .22)
    out = HALL[landed].copy()
    c = C(out)
    for i, d in enumerate(DROP):
        k = t - d
        b = BUSTS[i]
        fy = S.PED_TOP - 6 - b.shape[0] + 4
        if 0 <= k < .22:
            y = -110 + (fy + 110) * ease_in(k / .22)
            fx.blit(out, b, S.BOSS_X[i] - b.shape[1] // 2, y, shade=.55)
        if .22 <= k < .22 + 1 / FPS:
            P5.burst(S.BOSS_X[i], S.PED_TOP - 4, 22, speed=(1, 3), cols=[(120, 100, 110), (90, 76, 86), (255, 226, 130)], life=(.3, .7), grav=.06)
            cue(T0 + t, 'thud')
        if .22 <= k < .4:
            fx.flash(out, .25 * (1 - (k - .22) / .18), (255, 230, 180))
    P5.step()
    P5.draw(out)
    if t > 1.5:
        fx.band(out, 8, 46, .55)
        fx.title(c, 'BOSS FROGS', 320, 13, reveal=(t - 1.5) / .3, scale=2)
        if crossed(t, 1.5):
            cue(T0 + t, 'stinger')
    if t > 2.0:
        fx.plain(c, 'NFT COLLECTION', 320, 52, (255, 230, 200), 'title')
    if t > 2.5:
        k = clamp01((t - 2.5) / .9)
        n = int(250 * ease_out(k))
        fx.band(out, 306, 352, .65)
        x, w, h = fx.title(c, f'ONLY {n}', 320, 312, (255, 255, 255), (220, 220, 230), scale=2)
        if k >= 1:
            fx.title(c, f'ONLY {n}', 320, 312, GOLD_HI, GOLD, scale=2)
            if crossed(t, 3.4):
                cue(T0 + t, 'count_end')
        elif f % 2 == 0:
            cue(T0 + t, 'count')
    if t < .2:
        fx.fade_black(out, 1 - t / .2)
    if t > dur - .2:
        fx.fade_black(out, (t - (dur - .2)) / .2)
    return out


# =================================================================== 6. boss in the office
P6 = fx.Particles(33)
BOSS_AT = 1.0
BOSS_POS = (320, 150)


ZOOM_END = 3.3


def halo(out, cx, cy, r, k):
    d = np.hypot(fx.XX - cx, (fx.YY - cy) * 1.2)
    m = (d < r) & (fx.BAYER < (1 - d / r) * 1.4)
    out[m, :3] = np.clip(out[m, :3].astype(float) * (1 + .35 * k) + 18 * k, 0, 255).astype(np.uint8)


def sc_boss_office(t, f, T0, dur):
    base = SHOT['boss_office'][min(f, len(SHOT['boss_office']) - 1)]
    zoom = BOSS_AT <= t < ZOOM_END
    if zoom:
        out = np.repeat(np.repeat(base[60:240, 160:480], 2, 0), 2, 1).copy()
        bp = (320, 176)
    else:
        out = base.copy()
        bp = (320, 148)
    c = C(out)
    if f == 0:
        P6.p.clear()
    if t >= BOSS_AT:
        k = t - BOSS_AT
        halo(out, bp[0], bp[1], 120 if zoom else 60, clamp01(k / .3))
        if k < 1 / FPS:
            P6.burst(bp[0], bp[1], 70, speed=(2, 6), cols=[(200, 190, 220), (150, 140, 170), (255, 226, 130), (255, 255, 255)], life=(.4, 1.0), grav=-.03)
            cue(T0 + t, 'boss')
        if crossed(t, ZOOM_END):
            cue(T0 + t, 'whoosh')
        if k < .25:
            fx.flash(out, .8 * (1 - k / .25), (255, 240, 210))
        rad = (96, 70) if zoom else (46, 34)
        for k2 in range(5):
            a = t * 1.7 + k2 * 1.2566
            fx.sparkle(out, bp[0] + math.cos(a) * rad[0], bp[1] - 6 + math.sin(a) * rad[1], 1 + (f // 4 + k2) % 2)
    if zoom:
        P6.step()
        P6.draw(out)
    if t > .2:
        fx.band(out, 16, 56, .7)
        if t < BOSS_AT:
            fx.title(c, 'THE BOSS SEAT', 320, 22, reveal=(t - .2) / .35)
        elif zoom:
            fx.title(c, 'BOSS FROG', 320, 22, GOLD_HI, GOLD, reveal=(t - BOSS_AT - .15) / .3)
        else:
            fx.title(c, 'BOSSES RUN THE OFFICE', 320, 22, reveal=(t - ZOOM_END) / .35)
    if zoom and t > BOSS_AT + .6:
        fx.band(out, 318, 344, .6)
        fx.plain(c, 'SITS AT THE HEAD OF THE OFFICE', 320, 324, (255, 230, 200), 'title')
    if t > ZOOM_END + .3:
        fx.band(out, 212, 236, .7)
        fx.plain(c, 'MANAGES YOUR WHOLE CREW', 320, 217, (255, 230, 200), 'title')
    if t < .2:
        fx.fade_black(out, 1 - t / .2)
    if t > dur - .25:
        fx.fade_black(out, (t - (dur - .25)) / .25)
    return out


# =================================================================== 7. end card
P7 = fx.Particles(44)


def sc_end(t, f, T0, dur):
    out = TITLE_BG.copy()
    c = C(out)
    fx.over(out, NEON_BACK)
    fx.over(out, NEON_GLOW)
    fx.over(out, NEON_LIT)
    for (_, s, x, y) in LINEUP:
        fx.blit(out, s, x, y, shade=.92)
    if t > .35:
        fx.title(c, 'BUILDING ON SOLANA', 320, 104, SOL_A, SOL_B, reveal=(t - .35) / .4)
    if t > 1.2:
        k = t - 1.2
        if k < 1 / FPS:
            cue(T0 + t, 'final')
            P7.burst(320, 172, 60, speed=(2, 6), life=(.6, 1.3))
        y = int(150 - 12 * (1 - ease_back(clamp01(k / .3))))
        top, bot = (GOLD_HI, GOLD) if (f // 8) % 4 else ((255, 255, 255), GOLD_HI)
        fx.title(c, 'GAME SOON', 320, y, top, bot, scale=3)
    P7.step()
    P7.draw(out)
    if t < .25:
        fx.fade_black(out, 1 - t / .25)
    if t > dur - .7:
        fx.fade_black(out, (t - (dur - .7)) / .7)
    return out


# =================================================================== timeline
TIMELINE = [
    (3.4, sc_title, 'title'),
    (6.6, sc_pack, 'pack'),
    (6.2, sc_street, 'street'),
    (4.7, sc_meme, 'work'),
    (1.6, sc_room('pump', 'pumpfun'), 'pump'),
    (1.6, sc_room('classic', 'classic'), 'classic'),
    (5.0, sc_hall, 'hall'),
    (5.6, sc_boss_office, 'boss'),
    (5.0, sc_end, 'end'),
]


def scene_cues():
    T = 0
    for dur, _, name in TIMELINE:
        cue(T, 'scene:' + name)
        T += dur
    cue(3.4 + 0.45, 'land')
    cue(3.4 + 0.9, 'rumble')
    cue(3.4 + 2.25, 'tear')
    cue(3.4 + 2.35, 'roll')
    cue(3.4 + 3.3, 'reveal')
    return T


def frames():
    T = 0.0
    for dur, fn, name in TIMELINE:
        n = round(dur * FPS)
        for f in range(n):
            yield fn(f / FPS, f, T, dur), T + f / FPS
        T += n / FPS


def render_video(out_path):
    total = scene_cues()
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-vf', 'scale=1920:1080:flags=neighbor', '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p',
           '-tune', 'animation', str(out_path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    for img, _ in frames():
        p.stdin.write(np.ascontiguousarray(img[..., :3]).tobytes())
        n += 1
        if n % 150 == 0:
            print(n, 'frames')
    p.stdin.close()
    p.wait()
    EVENTS.sort()
    (BUILD / 'events.json').write_text(json.dumps(dict(total=total, events=EVENTS)))
    print('video', out_path, n, 'frames', total, 's')


def still(at, path):
    scene_cues()
    for img, tt in frames():
        if tt >= at - 1e-6:
            Image.fromarray(img).resize((1280, 720), Image.NEAREST).save(path)
            return


if __name__ == '__main__':
    if '--still' in sys.argv:
        ats = [float(a) for a in sys.argv[sys.argv.index('--still') + 1:]]
        out = Path('/tmp/claude-0/-home-claude/f782d41d-8771-50ed-9d54-4ef8681aae6f/scratchpad')
        imgs = []
        scene_cues()
        todo = sorted(ats)
        for img, tt in frames():
            if todo and tt >= todo[0] - 1e-6:
                imgs.append(img.copy()); todo.pop(0)
            if not todo:
                break
        sheet = Image.new('RGB', (1280, 360 * ((len(imgs) + 1) // 2)))
        for i, im in enumerate(imgs):
            sheet.paste(Image.fromarray(im).convert('RGB'), ((i % 2) * 640, (i // 2) * 360))
        sheet.save(out / 'stills.png')
    else:
        render_video(BUILD / 'trailer-video.mp4')
