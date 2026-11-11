"""Short teaser: open a pack, pull a Mythic, the Mythic farms $FROG at its desk, docs soon.

  python3 short.py               -> build/frog-traders-teaser.mp4 (no audio)
  python3 short.py --still 3 9 18  -> contact sheet of stills
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import fx
from fx import W, H, FPS, ease_out, ease_back, clamp01
from px2 import Canvas, sh
from menu_kit import GOLD, GOLD_HI, text_mask
import scenes as S
import trailer as T

OUT_W, OUT_H = 1920, 1080
T.REVEAL_TEXT = 'YOU PULLED A MYTHIC!'
T.CARD_FRONT = S.card_front_img(label='MYTHIC')
T.NEON_BACK, T.NEON_LIT, T.NEON_GLOW = S.neon_sign(text='FROGOTRADERZ')
DESK = T.load_shot('desk')
CROP = (200, 210, 440, 345)              # 240x135 -> 8x = 1920x1080
GREEN_HI, GREEN = (200, 255, 170), (110, 236, 90)


def up(a, k):
    return np.repeat(np.repeat(a, k, 0), k, 1)


def C(a):
    c = Canvas(W, H)
    c.a = a
    return c


# ------------------------------------------------------------------ desk close-up
SCREEN = ((335 + 364) / 2, 254)          # monitor top centre, office coords
SX = (SCREEN[0] - CROP[0]) * W / (CROP[2] - CROP[0])
SY = (SCREEN[1] - CROP[1]) * H / (CROP[3] - CROP[1])
POPS = []
POP_RNG = np.random.default_rng(8)
FARM = {'v': 0.0}
PD = fx.Particles(12)


def sc_desk(t, f, T0, dur):
    base = DESK[min(f + 15, len(DESK) - 1)][CROP[1]:CROP[3], CROP[0]:CROP[2]]
    big = up(base[..., :3], 8)
    ov = np.zeros((H, W, 4), np.uint8)
    c = C(ov)
    # coins fly out of the monitor
    if t > 1.4:
        while len(POPS) < int((t - 1.4) / .42) + 1:
            amt = int(POP_RNG.choice([34, 55, 89, 144]))
            POPS.append((t, amt, [-58, 34, -26, 62][len(POPS) % 4]))
            FARM['target'] = FARM.get('target', 0) + amt * 11
            PD.burst(SX, SY + 10, 8, speed=(1, 2.5), life=(.3, .6), grav=.05)
    for (tp, amt, dx) in POPS:
        age = t - tp
        if 0 <= age < 1.3:
            k = age / 1.3
            x = SX + dx * ease_out(k)
            y = SY - 6 - 70 * ease_out(k)
            alpha = 1 if k < .7 else 1 - (k - .7) / .3
            m = fx.big_mask(f'+{amt}', 'title', 2)
            cx = int(x)
            from menu_kit import coin
            if alpha >= 1 or (f + int(dx)) % 3:
                coin(c, cx - m.shape[1] // 2 - 12, int(y) + 11, 9)
                fx.title(c, f'+{amt}', cx + 8, int(y), GOLD_HI, GOLD, scale=2, shadow=2)
    PD.step()
    PD.draw(ov)
    FARM['v'] += (FARM.get('target', 0) - FARM['v']) * .18
    # captions
    if t > .3:
        fx.band(ov, 10, 50, .65)
        if t < 4.2:
            fx.title(c, 'YOUR FROG GOES TO WORK', 320, 16, reveal=(t - .3) / .45)
        else:
            fx.title(c, 'FARMING $FROG', 320, 16, GREEN_HI, GREEN, reveal=(t - 4.2) / .35)
    if t > 1.6:
        slide = ease_out(clamp01((t - 1.6) / .35))
        y0 = int(306 + 60 * (1 - slide))
        fx.chip(c, 200, y0, 439, y0 + 38, GOLD, (18, 14, 20))
        from menu_kit import coin
        coin(c, 222, y0 + 19, 9)
        m = text_mask('$FROG FARMED', 'body')
        fx.stamp(c, m, 238, y0 + 16, (176, 164, 152))
        fx.title(c, f'{int(FARM["v"]):,}', 360, y0 + 6, GOLD_HI, GOLD, scale=2, shadow=2)
    out = big.copy()
    ovb = up(ov, 3)
    m = ovb[..., 3] > 0
    out[m] = ovb[m, :3]
    if t < .25:
        k = 1 - t / .25
        out[:] = (out * (1 - k) + 255 * k).astype(np.uint8)        # flash in from the card reveal
    if t > dur - .3:
        _fade(out, (t - (dur - .3)) / .3)
    return out


# ------------------------------------------------------------------ end card
PE = fx.Particles(31)


def sc_end(t, f, T0, dur):
    out = T.TITLE_BG.copy()
    out[300:] = (out[300:] * .35).astype(np.uint8)
    c = C(out)
    fx.over(out, np.roll(T.NEON_BACK, 34, 0))
    fx.over(out, np.roll(T.NEON_GLOW, 34, 0))
    fx.over(out, np.roll(T.NEON_LIT, 34, 0))
    if t > .4:
        k = t - .4
        if k < 1 / FPS:
            PE.burst(320, 168, 60, speed=(2, 6), life=(.6, 1.3))
        y = int(146 - 12 * (1 - ease_back(clamp01(k / .3))))
        fx.title(c, 'DOCS SOON', 320, y, scale=3)
    if t > 1.2:
        fx.plain(c, 'THE FULL DOCUMENT WITH ALL THE DETAILS', 320, 206, (255, 230, 200), 'title')
        fx.plain(c, 'IS BEING PREPARED', 320, 222, (255, 230, 200), 'title')
    if t > 2.0:
        on = (f // 12) % 2 == 0 or t < 2.6
        if on:
            fx.title(c, 'STAY TUNED', 320, 254, GREEN_HI, GREEN, scale=2, reveal=(t - 2.0) / .3)
    PE.step()
    PE.draw(out)
    if t < .25:
        fx.fade_black(out, 1 - t / .25)
    if t > dur - .6:
        fx.fade_black(out, (t - (dur - .6)) / .6)
    return up(out[..., :3], 3)


def _fade(big, k):
    m = up(fx.BAYER < k, 3)
    big[m] = 0


def sc_pack(t, f, T0, dur):
    return up(T.sc_pack(t, f, T0, dur)[..., :3], 3)


TIMELINE = [(6.6, sc_pack), (9.0, sc_desk), (6.0, sc_end)]


def frames():
    T0 = 0.0
    for dur, fn in TIMELINE:
        n = round(dur * FPS)
        for f in range(n):
            yield fn(f / FPS, f, T0, dur), T0 + f / FPS
        T0 += n / FPS


if __name__ == '__main__':
    if '--still' in sys.argv:
        ats = sorted(float(a) for a in sys.argv[sys.argv.index('--still') + 1:])
        imgs = []
        for img, tt in frames():
            if ats and tt >= ats[0] - 1e-6:
                imgs.append(Image.fromarray(img).resize((960, 540), Image.NEAREST)); ats.pop(0)
            if not ats:
                break
        sheet = Image.new('RGB', (1920, 540 * ((len(imgs) + 1) // 2)))
        for i, im in enumerate(imgs):
            sheet.paste(im, ((i % 2) * 960, (i // 2) * 540))
        sheet.save('/tmp/claude-0/-home-claude/f782d41d-8771-50ed-9d54-4ef8681aae6f/scratchpad/teaser.png')
    else:
        out = T.BUILD / 'frog-traders-teaser.mp4'
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OUT_W}x{OUT_H}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-tune', 'animation', '-movflags', '+faststart', str(out)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for img, _ in frames():
            p.stdin.write(np.ascontiguousarray(img).tobytes())
        p.stdin.close(); p.wait()
        print('teaser', out)
