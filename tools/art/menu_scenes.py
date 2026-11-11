"""Small lit illustrations for menu cards. Each scene function returns
(albedo Canvas, Lights, emissive Canvas, meta dict) at the given size."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image

from px2 import INK, Canvas, dither, mix, sh
from menu_kit import GOLD, GOLD_HI, GOLD_LO, Lights, text_mask, draw_text

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'client/src/assets'


def sprite(name):
    return np.array(Image.open(A / name).convert('RGBA'))


def closed_eyes(spr: np.ndarray) -> np.ndarray:
    """Python twin of the runtime blink: lids over the eye whites."""
    out = spr.copy()
    h, w = spr.shape[:2]
    lim = int(h * .45)
    white = (spr[..., 3] > 0) & (spr[..., 0] > 196) & (spr[..., 1] > 190) & (spr[..., 2] > 160)
    white[lim:] = False
    from scipy import ndimage
    lab, n = ndimage.label(white)
    for i, sl in enumerate(ndimage.find_objects(lab)):
        if (lab[sl] == i + 1).sum() < 5:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop - 1, sl[1].start, sl[1].stop - 1
        lid = (116, 146, 78)
        for yy in range(y0 - 2, max(-1, y0 - 6), -1):
            px = spr[yy, (x0 + x1) // 2]
            if px[3] and int(px[0]) + int(px[1]) + int(px[2]) > 150:
                lid = tuple(int(v) for v in px[:3])
                break
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                p = spr[yy, xx]
                lum = int(p[0]) + int(p[1]) + int(p[2])
                if p[3] and (lum > 480 or lum < 110):
                    out[yy, xx, :3] = lid
        ly = min(y1, y0 + round((y1 - y0) * .65))
        for xx in range(x0, x1 + 1):
            if out[ly, xx, 3]:
                out[ly, xx, :3] = (20, 18, 22)
    return out


def _skin_near(spr, x, y):
    for dy in (-2, -3, 2, 3, -4):
        yy = min(spr.shape[0] - 1, max(0, y + dy))
        p = spr[yy, x]
        if p[3] and int(p[0]) + int(p[1]) + int(p[2]) > 200 and p[1] > p[2]:
            return tuple(int(v) for v in p[:3])
    return (120, 150, 80)


def happy_face(spr: np.ndarray, chin: int, eyes: bool = True) -> np.ndarray:
    """Turn the neutral face into a grin: eyes become ^ ^ arcs, mouth curves up."""
    out = spr.copy()
    h, w = spr.shape[:2]
    from scipy import ndimage
    white = (spr[..., 3] > 0) & (spr[..., 0] > 196) & (spr[..., 1] > 190) & (spr[..., 2] > 160)
    white[int(h * .2):] = False
    lab, n = ndimage.label(white)
    eye_bottom = 0
    for i, sl in enumerate(ndimage.find_objects(lab)):
        if (lab[sl] == i + 1).sum() < 5:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop - 1, sl[1].start, sl[1].stop - 1
        eye_bottom = max(eye_bottom, y1)
        if not eyes:
            continue
        lid = _skin_near(spr, (x0 + x1) // 2, y0)
        for yy in range(y0 - 1, y1 + 2):
            for xx in range(x0 - 1, x1 + 2):
                p = spr[yy, xx]
                lum = int(p[0]) + int(p[1]) + int(p[2])
                if p[3] and (lum > 480 or lum < 110) and 0 < xx < w - 1:
                    # keep the outer head outline
                    if spr[yy, xx - 1, 3] and spr[yy, xx + 1, 3] and spr[yy - 1, xx, 3]:
                        out[yy, xx, :3] = lid
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2 + 1
        half = max(2, (x1 - x0) // 2)
        for xx in range(cx - half, cx + half + 1):
            yy = cy - (half - abs(xx - cx)) // 1 + 1
            yy = cy + abs(xx - cx) // 2 - 1
            out[yy, xx, :3] = (20, 18, 22)
    # mouth: dark pixels between the eyes and the chin, away from the outline
    ys, xs = [], []
    for yy in range(eye_bottom + 2, chin - 3):
        for xx in range(2, w - 2):
            p = spr[yy, xx]
            if p[3] and int(p[0]) + int(p[1]) + int(p[2]) < 110 and spr[yy, xx - 2, 3] and spr[yy, xx + 2, 3] and spr[yy - 2, xx, 3] and spr[yy + 2, xx, 3]:
                ys.append(yy); xs.append(xx)
    if xs:
        mx0, mx1, my0, my1 = min(xs), max(xs), min(ys), max(ys)
        for yy, xx in zip(ys, xs):
            out[yy, xx, :3] = _skin_near(spr, xx, yy)
        mx0, mx1 = mx0 - 1, mx1 + 1
        top = my0
        for xx in range(mx0, mx1 + 1):
            t = (xx - mx0) / max(1, mx1 - mx0)
            yy = top + round(3 * math.sin(math.pi * t))
            out[yy, xx, :3] = (20, 18, 22)
            if 0.25 < t < 0.75:
                out[yy - 1, xx, :3] = (120, 30, 40)
        mid = (mx0 + mx1) // 2
        out[top + 2, mid - 1:mid + 2, :3] = (230, 110, 120)
    return out


def showgirl(dress, plume, flip=False):
    """A frog showgirl: frog head with lashes and a feather crown, fitted sequin gown, feather fan."""
    W_, H_ = 66, 84
    c = Canvas(W_, H_)
    head = happy_face(sprite('frogs/worker-common.png'), 23, eyes=False)[:24, 7:47].copy()
    cx = 38
    hx = cx - head.shape[1] // 2
    # feather fan held out to the side, behind the body
    fx, fy = 16, 36
    for k in range(8):
        a = math.radians(188 + k * 13)
        tip = (fx + math.cos(a) * 22, fy + math.sin(a) * 26)
        for t in np.linspace(0, 1, 24):
            x = fx + (tip[0] - fx) * t
            y = fy + (tip[1] - fy) * t
            r = .6 + 2.6 * math.sin(math.pi * min(1, t * 1.05))
            c.ellipse(x, y, r, r, sh(plume, .8) if k % 2 else plume)
        c.ellipse(tip[0], tip[1], 1.5, 1.5, mix(plume, (255, 255, 255), .6))
    # fitted gown flaring at the hem
    top, bot = 22, H_ - 1
    for y in range(top, bot + 1):
        t = (y - top) / (bot - top)
        half = int(10 - 3 * math.sin(min(1, t / .45) * math.pi / 2) + (max(0, t - .45) / .55) ** 1.6 * 12)
        for x in range(cx - half, cx + half + 1):
            edge = abs(x - cx) / max(1, half)
            col = sh(dress, 1.2 - .5 * edge)
            if (x * 7 + y * 5) % 17 == 0:
                col = mix(col, (255, 255, 255), .75)
            c.px(x, y, col)
        c.px(cx - half - 1, y, INK); c.px(cx + half + 1, y, INK)
        if y > top + 30 and (y % 3 == 0):
            c.px(cx + half // 3, y, sh(dress, .7))
    c.hline(cx - 20, cx + 20, bot, INK)
    c.ellipse(cx, top + 1, 7, 3, (226, 214, 170))
    for k in range(-8, 9):
        c.px(cx + k, top + 3 + abs(k) // 3, sh(dress, .65))
    # arms: one out to the fan, one on the hip
    skin, skin_lo = (126, 160, 84), (90, 120, 60)
    c.line(cx - 9, top + 4, fx + 3, fy + 2, INK)
    c.line(cx - 9, top + 5, fx + 4, fy + 3, skin)
    c.line(cx - 8, top + 6, fx + 5, fy + 4, skin_lo)
    c.ellipse(fx + 3, fy + 2, 2, 2, skin)
    c.line(cx + 10, top + 4, cx + 15, top + 13, INK)
    c.line(cx + 9, top + 5, cx + 14, top + 13, skin)
    c.line(cx + 14, top + 13, cx + 9, top + 18, skin)
    # head, lashes, blush, lips and a feather crown
    c.blit(head, hx, 0)
    for ex in (hx + 13, hx + 34):
        c.px(ex - 2, 4, INK); c.px(ex - 1, 3, INK); c.px(ex + 2, 3, INK); c.px(ex + 3, 4, INK)
    for (bx, by) in ((hx + 8, 15), (hx + 31, 14)):
        c.px(bx, by, (240, 120, 130)); c.px(bx + 1, by, (240, 140, 150)); c.px(bx + 2, by + 1, (240, 120, 130))
    for k in range(3):
        bx = hx + 16 + k * 4
        for j in range(8):
            c.px(bx + (j % 2) - k + 1, 2 - j, plume if j < 5 else (255, 255, 255))
    c.rect(hx + 13, 1, hx + 27, 2, GOLD)
    c.px(hx + 20, 1, (240, 80, 120))
    if flip:
        c.a = c.a[:, ::-1].copy()
    return c.a

def shade_sprite(spr, f):
    out = spr.copy()
    out[..., :3] = np.clip(out[..., :3].astype(float) * f, 0, 255).astype(np.uint8)
    return out


# ================================================================ FROGS
def scene_frogs(w, h, rng):
    c, e = Canvas(w, h), Canvas(w, h)
    floor_y = h - 14
    # back wall: green-grey metal lockers
    c.rect(0, 0, w - 1, floor_y, (40, 46, 44))
    lw = 21
    x = -6
    k = 0
    while x < w:
        col = (78, 98, 88) if k % 2 == 0 else (72, 92, 82)
        c.rect(x, 6, x + lw - 1, floor_y - 2, INK)
        c.rect(x + 1, 7, x + lw - 2, floor_y - 3, col)
        c.hline(x + 1, x + lw - 2, 7, sh(col, 1.3))
        c.vline(x + 1, 7, floor_y - 3, sh(col, 1.18))
        c.vline(x + lw - 2, 7, floor_y - 3, sh(col, .72))
        for vy in range(12, 26, 3):  # vents
            c.hline(x + 5, x + lw - 6, vy, sh(col, .6))
            c.hline(x + 5, x + lw - 6, vy + 1, sh(col, 1.2))
        c.rect(x + lw - 6, 46, x + lw - 4, 52, (170, 170, 176))  # handle
        c.px(x + lw - 5, 47, (220, 220, 226))
        num = text_mask(str(k + 1), 'body')
        c.rect(x + 6, 32, x + 14, 40, (230, 224, 206))
        c.mask(num, x + 10 - num.shape[1] // 2, 34, (60, 60, 66))
        if k == 2:  # a sticker on one locker
            c.rect(x + 5, 60, x + 12, 66, (232, 108, 46))
        x += lw
        k += 1
    # bench
    c.rect(0, floor_y - 10, w - 1, floor_y - 7, INK)
    c.rect(0, floor_y - 9, w - 1, floor_y - 8, (140, 96, 60))
    c.hline(0, w - 1, floor_y - 9, (176, 124, 80))
    for bx in range(10, w, 40):
        c.rect(bx, floor_y - 6, bx + 2, floor_y, (60, 60, 66))
    # floor tiles
    for y in range(floor_y, h):
        for x2 in range(w):
            c.px(x2, y, (58, 56, 64) if ((x2 // 8) + (y // 4)) % 2 else (66, 64, 72))
    c.hline(0, w - 1, floor_y, INK)
    # crew: rare and legendary behind, mythic in front
    back_l = shade_sprite(sprite('frogs/worker-rare.png'), .82)
    back_r = shade_sprite(sprite('frogs/worker-legendary.png'), .82)
    front = sprite('frogs/worker-mythic.png')
    c.blit(back_l, 2, floor_y - back_l.shape[0] + 2)
    c.blit(back_r, w - back_r.shape[1] - 2, floor_y - back_r.shape[0] + 2)
    fx = w // 2 - front.shape[1] // 2
    fy = h - front.shape[0] - 1
    # contact shadows
    for (cx_, cy_, rx) in ((w // 2, h - 3, 26), (30, floor_y + 1, 20), (w - 30, floor_y + 1, 20)):
        for yy in range(cy_ - 2, cy_ + 3):
            for xx in range(cx_ - rx, cx_ + rx + 1):
                if ((xx - cx_) / rx) ** 2 + ((yy - cy_) / 2.5) ** 2 < 1:
                    c.px(xx, yy, (0, 0, 0), 120)
    c.blit(front, fx, fy)
    # ceiling strip light (self-lit)
    e.rect(w // 2 - 22, 0, w // 2 + 22, 2, (240, 246, 230))
    L = Lights(w, h, [0.34, 0.36, 0.44])
    L.point(w / 2, 0, 150, [1.0, 0.96, 0.85], 1.1, cone=True)
    L.point(w / 2, h - 30, 50, [1.0, 0.85, 0.5], 0.35)
    return c, L, e, dict(frog=[fx, fy])


# ============================================================ GO TO WORK
def building(c, e, x0, w, top, base_y, wall, neon_col, label, rng, style):
    e.a[top:base_y + 1, x0:x0 + w, 3] = 0  # the facade hides the sky behind it
    c.rect(x0, top, x0 + w - 1, base_y, INK)
    c.rect(x0 + 1, top + 1, x0 + w - 2, base_y, wall)
    c.hline(x0 + 1, x0 + w - 2, top + 1, sh(wall, 1.3))
    if style == 'brick':
        for y in range(top + 3, base_y, 3):
            off = 3 if (y // 3) % 2 else 0
            for x in range(x0 + 2 + off, x0 + w - 2, 6):
                c.px(x, y, sh(wall, .8))
    elif style == 'concrete':
        for y in range(top + 6, base_y, 8):
            c.hline(x0 + 1, x0 + w - 2, y, sh(wall, .82))
    else:  # stone with columns
        for x in range(x0 + 4, x0 + w - 3, 8):
            c.vline(x, top + 10, base_y - 2, sh(wall, 1.2))
            c.vline(x + 1, top + 10, base_y - 2, sh(wall, .8))
        c.rect(x0 + 1, top + 4, x0 + w - 2, top + 7, sh(wall, 1.15))
    # windows
    for wy in range(top + 12, base_y - 34, 8):
        for wx in range(x0 + 4, x0 + w - 6, 7):
            c.rect(wx - 1, wy - 1, wx + 4, wy + 5, INK)
            if rng.random() < .62:
                warm = [(255, 214, 140), (250, 190, 110), (140, 220, 230)][int(rng.integers(0, 3))]
                e.rect(wx, wy, wx + 3, wy + 4, warm)
                e.hline(wx, wx + 3, wy + 4, sh(warm, .75))
            else:
                c.rect(wx, wy, wx + 3, wy + 4, (24, 24, 36))
    # door
    dx = x0 + w // 2 - 5
    c.rect(dx - 1, base_y - 15, dx + 10, base_y, INK)
    e.rect(dx, base_y - 14, dx + 9, base_y - 1, mix(neon_col, (255, 230, 180), .6))
    e.vline(dx + 5, base_y - 14, base_y - 1, sh(neon_col, .6))
    # neon sign above the door: dark plate, glowing letters, neon rim
    m = text_mask(label, 'body')
    sx = x0 + w // 2 - m.shape[1] // 2
    sy = base_y - 27
    bx0, by0, bx1, by1 = sx - 4, sy - 3, sx + m.shape[1] + 3, sy + m.shape[0] + 2
    e.a[by0 - 1:by1 + 2, bx0 - 1:bx1 + 2, 3] = 0
    c.rect(bx0 - 1, by0 - 1, bx1 + 1, by1 + 1, INK)
    c.rect(bx0, by0, bx1, by1, (16, 12, 20))
    for xx in range(bx0, bx1 + 1):
        e.px(xx, by0, sh(neon_col, .8)); e.px(xx, by1, sh(neon_col, .8))
    for yy in range(by0, by1 + 1):
        e.px(bx0, yy, sh(neon_col, .8)); e.px(bx1, yy, sh(neon_col, .8))
    e.mask(m, sx, sy, mix(neon_col, (255, 255, 255), .45))
    return (x0 + w // 2, sy + 3)


def scene_work(w, h, rng):
    c, e = Canvas(w, h), Canvas(w, h)
    street = h - 22
    for y in range(street):
        t = y / street
        for x in range(w):
            col = mix((14, 14, 34), (54, 34, 72), t)
            c.px(x, y, col)
            e.px(x, y, col)
    for _ in range(26):
        sx, sy = int(rng.integers(0, w)), int(rng.integers(0, 30))
        e.px(sx, sy, (210, 210, 240))
    e.ellipse(w - 18, 12, 5, 5, (236, 230, 206))
    e.ellipse(w - 16, 10, 4, 4, (20, 18, 40))
    # distant skyline silhouettes
    x = 0
    while x < w:
        bw = int(rng.integers(6, 14))
        bh = int(rng.integers(20, 46))
        e.rect(x, street - bh - 10, x + bw, street, (30, 26, 52))
        for wy in range(street - bh - 7, street - 12, 4):
            if rng.random() < .3:
                e.px(x + int(rng.integers(1, max(2, bw - 1))), wy, (200, 170, 110))
        x += bw + 1
    # three offices
    bw = (w - 8) // 3
    signs = []
    specs = [((126, 72, 52), (255, 120, 50), 'MEME', 'brick', 26),
             ((70, 60, 92), (255, 70, 170), 'PUMP', 'concrete', 14),
             ((132, 126, 116), (60, 210, 176), 'CLASSIC', 'stone', 22)]
    for i, (wall, neon, label, style, top) in enumerate(specs):
        x0 = 2 + i * (bw + 2)
        signs.append((building(c, e, x0, bw, top, street, wall, neon, label, rng, style), neon))
    # wet street with neon reflections
    for y in range(street + 1, h):
        for x in range(w):
            c.px(x, y, (34, 32, 42) if (y - street) % 7 else (46, 44, 56))
    c.hline(0, w - 1, street, (90, 86, 100))
    c.hline(0, w - 1, street + 1, INK)
    for (sx, sy), neon in signs:
        for y in range(street + 3, h - 1):
            for x in range(sx - 6, sx + 7):
                if (x + y) % 2 == 0 and rng.random() < .55 * (1 - (y - street) / 22):
                    e.px(x, y, neon, 110)
    # street lamp
    lx = w // 2 + 1
    c.vline(lx, street - 40, street, (40, 40, 48))
    c.hline(lx, lx + 4, street - 40, (40, 40, 48))
    e.rect(lx + 3, street - 39, lx + 5, street - 38, (255, 236, 190))
    L = Lights(w, h, [0.42, 0.40, 0.56])
    for (sx, sy), neon in signs:
        L.point(sx, sy, 34, [v / 255 for v in neon], 0.9)
    L.point(lx + 4, street - 38, 60, [1.0, 0.9, 0.7], 0.7, cone=True)
    return c, L, e, dict(signs=[[s[0][0], s[0][1]] for s in signs])


# ================================================================== SHOP
def booster(c, x, y, col, label, w=22, h=32):
    lo, hi = sh(col, .6), sh(col, 1.35)
    c.rect(x, y + 1, x + w, y + h - 1, INK)
    c.rect(x + 1, y + 2, x + w - 1, y + h - 2, col)
    for k in range(0, w + 1, 2):
        c.px(x + k, y, INK); c.px(x + k, y + h, INK)
        c.vline(x + k, y + 1, y + 3, lo)
        c.vline(x + k, y + h - 3, y + h - 1, lo)
    for k in range(8):
        c.px(x + 3 + k, y + 5 + k * 2, hi)
    c.ellipse(x + w / 2, y + 14, 6, 6, INK)
    c.ellipse(x + w / 2, y + 14, 5, 5, (240, 232, 210))
    c.ellipse(x + w / 2, y + 15, 3, 2, (110, 170, 80))
    c.px(x + w // 2 - 2, y + 12, (110, 170, 80)); c.px(x + w // 2 + 2, y + 12, (110, 170, 80))
    m = text_mask(label, 'body')
    c.rect(x + w // 2 - m.shape[1] // 2 - 1, y + 22, x + w // 2 + m.shape[1] // 2 + 1, y + 22 + m.shape[0] + 1, INK)
    c.mask(m, x + w // 2 - m.shape[1] // 2, y + 23, (255, 255, 255))


def scene_shop(w, h, rng):
    from menu_kit import brick_wall
    c, e = Canvas(w, h), Canvas(w, h)
    walk = h - 12
    brick_wall(c, 0, 0, w - 1, walk, rng, bw=12, bh=6)
    # neon SHOP sign
    m = text_mask('SHOP', 'head')
    sx, sy = w // 2 - m.shape[1] // 2, 5
    c.rect(sx - 5, sy - 3, sx + m.shape[1] + 4, sy + m.shape[0] + 3, INK)
    c.rect(sx - 4, sy - 2, sx + m.shape[1] + 3, sy + m.shape[0] + 2, (26, 22, 30))
    e.mask(m, sx, sy, (255, 214, 110))
    pad = np.pad(m, 1)
    inner = m & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    e.mask(inner, sx, sy, (255, 248, 214))
    # striped awning
    ay = sy + m.shape[0] + 6
    for x in range(4, w - 4):
        col = (60, 150, 90) if (x // 8) % 2 == 0 else (236, 228, 206)
        c.vline(x, ay, ay + 8, col)
        if (x % 8) in (3, 4):
            c.px(x, ay + 9, col)
    c.hline(4, w - 5, ay, INK)
    c.hline(4, w - 5, ay + 9, (0, 0, 0), 120)
    # display window (warm interior is self-lit)
    wx0, wy0, wx1, wy1 = 8, ay + 12, w - 30, walk - 4
    c.rect(wx0 - 2, wy0 - 2, wx1 + 2, wy1 + 2, INK)
    c.rect(wx0 - 1, wy0 - 1, wx1 + 1, wy1 + 1, (70, 44, 28))
    for y in range(wy0, wy1 + 1):
        for x in range(wx0, wx1 + 1):
            e.px(x, y, mix((120, 70, 40), (60, 30, 24), (y - wy0) / (wy1 - wy0)))
    shelf = wy1 - 12
    e.rect(wx0, shelf, wx1, shelf + 2, (150, 100, 60))
    e.hline(wx0, wx1, shelf, (190, 140, 90))
    mid = (wx0 + wx1) // 2
    tmp = Canvas(w, h)
    booster(tmp, mid - 36, shelf - 33, (90, 170, 80), 'X1')
    booster(tmp, mid + 14, shelf - 33, (150, 80, 220), 'X15')
    booster(tmp, mid - 11, shelf - 38, (230, 170, 50), 'X5')
    for (cx_, cy_) in [(mid - 8, wy1 - 4), (mid, wy1 - 3), (mid + 8, wy1 - 4), (mid - 4, wy1 - 7), (mid + 4, wy1 - 7), (mid, wy1 - 10)]:
        tmp.ellipse(cx_, cy_, 4, 2, INK)
        tmp.ellipse(cx_, cy_, 3, 1, GOLD)
        tmp.px(cx_ - 1, cy_ - 1, GOLD_HI)
    m2 = tmp.a[..., 3] > 0
    e.a[m2] = tmp.a[m2]
    # glass glare
    for k in range(10):
        e.px(wx0 + 4 + k, wy0 + 2 + k, (255, 240, 220), 90)
        e.px(wx0 + 6 + k, wy0 + 2 + k, (255, 240, 220), 60)
    # door with an OPEN sign
    dx0 = w - 24
    c.rect(dx0 - 1, wy0 - 2, w - 6, walk, INK)
    c.rect(dx0, wy0 - 1, w - 7, walk, (70, 44, 28))
    c.vline(dx0 + 1, wy0 - 1, walk, (100, 66, 44))
    e.rect(dx0 + 3, wy0 + 2, w - 10, wy0 + 20, (230, 190, 120))
    om = text_mask('OPEN', 'body')
    e.rect(dx0 + 1, wy0 + 24, dx0 + 2 + om.shape[1], wy0 + 25 + om.shape[0], (30, 120, 70))
    e.mask(om, dx0 + 2, wy0 + 25, (210, 255, 220))
    c.rect(w - 11, wy0 + 30, w - 9, wy0 + 33, GOLD)
    # sidewalk
    for y in range(walk + 1, h):
        for x in range(w):
            c.px(x, y, (84, 80, 88) if (x // 10 + y // 6) % 2 else (92, 88, 96))
    c.hline(0, w - 1, walk, INK)
    L = Lights(w, h, [0.36, 0.33, 0.40])
    L.point(mid, (wy0 + wy1) / 2, 90, [1.0, 0.75, 0.45], 0.9)
    L.point(w / 2, sy + 6, 70, [1.0, 0.85, 0.4], 0.8)
    return c, L, e, dict(sparkles=[[mid - 30, shelf - 40], [mid + 30, shelf - 36], [mid, shelf - 44], [wx0 + 6, wy1 - 6]])


# ================================================================ MARKET
def scene_market(w, h, rng):
    c, e = Canvas(w, h), Canvas(w, h)
    for y in range(h):
        for x in range(w):
            c.px(x, y, mix((22, 30, 40), (12, 14, 20), y / h))
    # back shelves with goods
    for sy in (36, 56):
        c.rect(6, sy, w - 7, sy + 2, (110, 74, 46))
        c.hline(6, w - 7, sy, (150, 104, 66))
        x = 9
        while x < w - 14:
            gw = int(rng.integers(5, 9))
            col = [(200, 60, 60), (90, 170, 230), (240, 190, 80), (120, 200, 90), (180, 110, 230)][int(rng.integers(0, 5))]
            gh = int(rng.integers(6, 12))
            c.box(x, sy - gh, x + gw, sy - 1, col, sh(col, 1.3), sh(col, .7))
            x += gw + 2
    # merchant frog
    spr = sprite('frogs/worker-epic.png')[:62]
    fx = w // 2 - spr.shape[1] // 2 + 8
    c.blit(spr, fx, 30)
    # striped awning and string lights
    for x in range(w):
        col = (60, 198, 168) if (x // 10) % 2 == 0 else (236, 228, 206)
        c.vline(x, 0, 12, col)
        c.px(x, 13 + (1 if (x % 10) in (4, 5) else 0), col)
    c.hline(0, w - 1, 0, INK)
    c.hline(0, w - 1, 15, (0, 0, 0), 110)
    bulbs = []
    for k, x in enumerate(range(4, w, 11)):
        y = 19 + int(3 * math.sin(k * 1.1))
        c.px(x, y - 1, (40, 40, 44))
        e.px(x, y, (255, 220, 140))
        e.px(x, y + 1, (255, 190, 100))
        bulbs.append([x, y])
    for x in range(0, w):
        y = 18 + int(3 * math.sin((x - 4) / 11 * 1.1))
        if c.get(x, y) != (40, 40, 44):
            c.px(x, y - 1, (40, 40, 44))
    # counter with crates and a framed card for sale
    cy0 = h - 30
    c.rect(0, cy0, w - 1, h - 1, INK)
    c.rect(0, cy0 + 1, w - 1, cy0 + 5, (160, 108, 64))
    c.hline(0, w - 1, cy0 + 1, (200, 146, 92))
    c.rect(0, cy0 + 6, w - 1, h - 1, (112, 72, 44))
    for x in range(10, w, 18):
        c.vline(x, cy0 + 7, h - 1, (88, 56, 34))
    c.box(10, cy0 - 22, 34, cy0, (40, 30, 60), (70, 56, 100), (26, 18, 40))
    c.ellipse(22, cy0 - 11, 6, 5, (180, 110, 230))
    c.px(19, cy0 - 13, (244, 240, 226)); c.px(25, cy0 - 13, (244, 240, 226))
    c.rect(38, cy0 - 12, 58, cy0 - 3, INK)
    c.rect(39, cy0 - 11, 57, cy0 - 4, (240, 232, 210))
    c.box(w - 34, cy0 - 14, w - 10, cy0, (150, 110, 66), (186, 140, 90), (110, 76, 44))
    c.line(w - 34, cy0 - 14, w - 10, cy0, (110, 76, 44))
    c.line(w - 34, cy0, w - 10, cy0 - 14, (110, 76, 44))
    L = Lights(w, h, [0.30, 0.32, 0.40])
    for bx, by in bulbs[::2]:
        L.point(bx, by, 46, [1.0, 0.82, 0.55], 0.55)
    L.point(w / 2, 20, 100, [1.0, 0.85, 0.6], 0.6, cone=True)
    return c, L, e, dict(tag=[39, cy0 - 11], bulbs=bulbs)


# =============================================================== RECRUIT
def card_back(c, x, y, w=30, h=42, gold=False):
    body, lo = (110, 30, 40), (70, 18, 26)
    c.rect(x, y, x + w - 1, y + h - 1, INK)
    c.rect(x + 1, y + 1, x + w - 2, y + h - 2, GOLD if gold else (150, 60, 50))
    c.hline(x + 1, x + w - 2, y + 1, GOLD_HI if gold else (190, 90, 76))
    c.rect(x + 3, y + 3, x + w - 4, y + h - 4, body)
    for yy in range(y + 4, y + h - 4):
        for xx in range(x + 4, x + w - 4):
            if (xx - x + yy - y) % 5 == 0 or (xx - x - (yy - y)) % 5 == 0:
                c.px(xx, yy, lo)
    cx, cy = x + w // 2, y + h // 2
    c.ellipse(cx, cy, 8, 8, INK)
    c.ellipse(cx, cy, 7, 7, GOLD if gold else (236, 226, 200))
    c.ellipse(cx, cy, 5, 5, (30, 26, 34) if gold else (236, 226, 200))
    if not gold:  # little frog emblem
        c.ellipse(cx, cy + 1, 4, 3, (100, 160, 76))
        c.ellipse(cx - 3, cy - 2, 1.5, 1.5, (100, 160, 76)); c.ellipse(cx + 3, cy - 2, 1.5, 1.5, (100, 160, 76))
        c.px(cx - 3, cy - 2, (250, 250, 240)); c.px(cx + 3, cy - 2, (250, 250, 240))
        c.hline(cx - 2, cx + 2, cy + 2, (60, 110, 50))
    return cx, cy


def scene_recruit(w, h, rng):
    from menu_kit import wood_planks
    c, e = Canvas(w, h), Canvas(w, h)
    desk_y = h - 34
    # velvet curtain backdrop
    for x in range(w):
        fold = (x % 9)
        col = (90, 30, 70) if fold in (0, 1) else (120, 44, 96) if fold in (2, 3, 4) else (104, 36, 84)
        c.vline(x, 0, desk_y, col)
    for x in range(0, w, 9):
        c.vline(x, 0, desk_y, (60, 18, 48))
    # NOW HIRING neon
    m = text_mask('NOW HIRING', 'head')
    sx, sy = w // 2 - m.shape[1] // 2, 6
    c.rect(sx - 5, sy - 3, sx + m.shape[1] + 4, sy + m.shape[0] + 3, INK)
    c.rect(sx - 4, sy - 2, sx + m.shape[1] + 3, sy + m.shape[0] + 2, (26, 16, 30))
    e.mask(m, sx, sy, (255, 90, 190))
    pad = np.pad(m, 1)
    inner = m & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    e.mask(inner, sx, sy, (255, 220, 244))
    # desk
    c.rect(0, desk_y, w - 1, h - 1, INK)
    wood_planks(c, 0, desk_y + 1, w - 1, desk_y + 7, rng, cols=[(120, 74, 44), (112, 70, 42), (128, 80, 48)], plank=4)
    c.hline(0, w - 1, desk_y + 1, (170, 116, 72))
    c.rect(0, desk_y + 8, w - 1, h - 1, (80, 48, 30))
    for x in range(14, w, 30):
        c.box(x, desk_y + 11, x + 22, h - 4, (80, 48, 30), (104, 64, 40), (60, 34, 20))
    # contracts and a stamp
    c.box(10, desk_y - 4, 34, desk_y + 2, (236, 230, 214), None, (196, 188, 172))
    c.box(12, desk_y - 7, 36, desk_y - 1, (240, 234, 220), None, (200, 192, 176))
    for k in range(3):
        c.hline(15, 31, desk_y - 5 + k * 2, (150, 146, 140))
    c.box(w - 28, desk_y - 10, w - 18, desk_y - 4, (140, 40, 40), (180, 70, 60), (100, 24, 24))
    c.rect(w - 26, desk_y - 4, w - 20, desk_y, (60, 40, 30))
    # fanned recruit cards, the middle one is the mystery hire
    card_back(c, w // 2 - 46, desk_y - 46)
    card_back(c, w // 2 + 16, desk_y - 46)
    hx, hy = card_back(c, w // 2 - 15, desk_y - 56, gold=True)
    qm = [".###.", "#...#", "...#.", "..#..", "..#..", ".....", "..#.."]
    for j, row in enumerate(qm):
        for i, ch in enumerate(row):
            if ch == '#':
                e.px(hx - 2 + i, hy - 3 + j, GOLD_HI)
    L = Lights(w, h, [0.32, 0.28, 0.40])
    L.point(w / 2, sy + 6, 90, [1.0, 0.4, 0.8], 0.8)
    L.point(w / 2, desk_y - 30, 70, [1.0, 0.85, 0.5], 0.7)
    return c, L, e, dict(halo=[hx, hy], sparkles=[[20, 40], [w - 20, 44], [w // 2 - 50, 70], [w // 2 + 50, 66], [w // 2, desk_y - 64]])


# ================================================================ CASINO
def slot(c, e, x, y, col):
    c.rect(x, y, x + 22, y + 46, INK)
    c.rect(x + 1, y + 1, x + 21, y + 45, col)
    c.vline(x + 1, y + 1, y + 45, sh(col, 1.3))
    c.vline(x + 21, y + 1, y + 45, sh(col, .65))
    c.rect(x + 3, y + 3, x + 19, y + 8, INK)
    e.rect(x + 4, y + 4, x + 18, y + 7, (255, 210, 110))
    c.rect(x + 3, y + 12, x + 19, y + 22, INK)
    e.rect(x + 4, y + 13, x + 18, y + 21, (240, 236, 224))
    for k in range(3):
        e.rect(x + 5 + k * 5, y + 15, x + 7 + k * 5, y + 19, (200, 40, 50) if k % 2 == 0 else (40, 140, 60))
    c.rect(x + 5, y + 28, x + 17, y + 31, INK)
    c.vline(x + 23, y + 10, y + 20, (180, 180, 190))
    e.px(x + 23, y + 9, (255, 60, 60))
    return [x + 4, y + 4, x + 18]


def scene_casino(w, h, rng):
    c, e = Canvas(w, h), Canvas(w, h)
    floor_y = h - 24
    for y in range(floor_y):
        for x in range(w):
            col = (70, 18, 30)
            if (x + y * 2) % 12 == 0 or (x - y * 2) % 12 == 0:
                col = (84, 26, 40)
            c.px(x, y, col)
    c.rect(0, floor_y - 6, w - 1, floor_y - 4, GOLD_LO)
    c.hline(0, w - 1, floor_y - 6, GOLD_HI)
    # JACKPOT marquee with chasing bulbs
    m = text_mask('JACKPOT', 'title')
    sx, sy = w // 2 - m.shape[1] // 2, 8
    c.rect(sx - 9, sy - 6, sx + m.shape[1] + 8, sy + m.shape[0] + 5, INK)
    c.rect(sx - 8, sy - 5, sx + m.shape[1] + 7, sy + m.shape[0] + 4, (120, 20, 30))
    c.rect(sx - 6, sy - 3, sx + m.shape[1] + 5, sy + m.shape[0] + 2, (40, 8, 14))
    e.mask(m, sx, sy, (255, 214, 110))
    pad = np.pad(m, 1)
    inner = m & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    e.mask(inner, sx, sy, (255, 248, 220))
    sign_bulbs = []
    for x in range(sx - 7, sx + m.shape[1] + 7, 3):
        sign_bulbs.append([x, sy - 5]); sign_bulbs.append([x, sy + m.shape[0] + 4])
    for bx_, by_ in sign_bulbs:
        c.px(bx_, by_, (150, 110, 50))
    # confetti hanging in the air after the win
    conf = [(255, 90, 160), (255, 214, 90), (90, 200, 255), (126, 226, 84), (255, 255, 255)]
    for _ in range(46):
        x, y = int(rng.integers(4, w - 4)), int(rng.integers(sy + 26, floor_y - 54))
        col = conf[int(rng.integers(0, len(conf)))]
        c.px(x, y, col)
        if rng.random() < .5:
            c.px(x + 1, y + (1 if rng.random() < .5 else 0), sh(col, .7))
    # slot machines along the back wall
    marquees = []
    for k, x in enumerate(range(2, w - 18, 25)):
        col = [(170, 30, 50), (40, 70, 160), (150, 40, 150), (30, 120, 90), (170, 30, 50), (40, 70, 160), (150, 40, 150)][k % 7]
        marquees.append(slot(c, e, x, floor_y - 50, col))
    # carpet
    for y in range(floor_y, h):
        for x in range(w):
            col = (120, 24, 36)
            if (x // 6 + y // 3) % 4 == 0:
                col = (150, 110, 50)
            elif (x // 6 + y // 3) % 2 == 0:
                col = (100, 18, 30)
            c.px(x, y, col)
    c.hline(0, w - 1, floor_y, INK)
    # foreground (characters and the table) on its own layer
    bgc, c = c, Canvas(w, h)
    left = showgirl((210, 40, 90), (255, 150, 200))
    right = showgirl((120, 60, 200), (190, 150, 255), flip=True)
    c.blit(left, -4, h - left.shape[0] - 1)
    c.blit(right, w - right.shape[1] + 4, h - right.shape[0] - 1)
    hero = happy_face(sprite('frogs/worker-legendary.png'), 22)[:70]
    hx = w // 2 - hero.shape[1] // 2
    hy = h - 70 - 6
    c.blit(hero, hx, hy)
    # cocktail raised in his hand
    gx, gy = hx + hero.shape[1] - 6, hy + 30
    c.poly([(gx - 4, gy - 8), (gx + 5, gy - 8), (gx, gy - 3)], (120, 220, 200))
    c.line(gx - 4, gy - 8, gx, gy - 3, INK); c.line(gx + 5, gy - 8, gx, gy - 3, INK)
    c.vline(gx, gy - 3, gy + 1, (220, 220, 230))
    c.px(gx + 3, gy - 10, (230, 60, 60))
    # table with chips and a pile of winnings in front
    ty = h - 16
    c.rect(w // 2 - 34, ty, w // 2 + 34, h - 1, INK)
    c.rect(w // 2 - 33, ty + 1, w // 2 + 33, h - 1, (30, 110, 70))
    c.hline(w // 2 - 33, w // 2 + 33, ty + 1, (60, 160, 100))
    c.rect(w // 2 - 34, ty - 2, w // 2 + 34, ty, (110, 70, 40))
    for k, (cx_, col) in enumerate([(w // 2 - 24, (230, 60, 60)), (w // 2 - 16, (60, 120, 230)), (w // 2 + 18, (40, 40, 44)), (w // 2 + 26, (230, 60, 60))]):
        for j in range(3 + k % 2):
            c.ellipse(cx_, ty - 3 - j * 2, 4, 1, INK)
            c.hline(cx_ - 3, cx_ + 3, ty - 3 - j * 2, col)
    for (cx_, cy_) in [(w // 2 - 4, ty - 3), (w // 2 + 4, ty - 3), (w // 2, ty - 5), (w // 2 - 8, ty - 2), (w // 2 + 8, ty - 2)]:
        c.ellipse(cx_, cy_, 3, 1, INK)
        c.hline(cx_ - 2, cx_ + 2, cy_, GOLD)
        c.px(cx_ - 1, cy_, GOLD_HI)
    fg = c.a[..., 3] > 0
    e.a[fg, 3] = 0
    bgc.blit(c.a, 0, 0)
    c = bgc
    L = Lights(w, h, [0.32, 0.26, 0.32])
    L.point(w / 2, sy + 6, 80, [1.0, 0.8, 0.45], 0.7)
    for mx0, my, mx1 in marquees:
        L.point((mx0 + mx1) / 2, my + 10, 40, [1.0, 0.75, 0.45], 0.55)
    L.spot(w / 2, -6, 0.5, h * 1.2, [1.0, 0.86, 0.6], 0.85)
    return c, L, e, dict(marquees=marquees, bulbs=sign_bulbs,
                         sparkles=[[w // 2 - 30, 40], [w // 2 + 30, 44], [w // 2, 30], [24, 60], [w - 24, 58]])


# ================================================================== BOSS
def scene_boss(w, h, rng):
    c, e = Canvas(w, h), Canvas(w, h)
    desk_y = h - 34
    # wood panelled wall
    from menu_kit import wood_planks
    wood_planks(c, 0, 0, w - 1, desk_y, rng, cols=[(76, 40, 28), (70, 36, 26), (82, 44, 30)], vertical=True, plank=7)
    # night window behind
    wx0, wy0, wx1, wy1 = 30, 10, w - 31, desk_y - 30
    c.rect(wx0 - 3, wy0 - 3, wx1 + 3, wy1 + 3, INK)
    c.rect(wx0 - 2, wy0 - 2, wx1 + 2, wy1 + 2, GOLD_LO)
    c.hline(wx0 - 2, wx1 + 2, wy0 - 2, GOLD_HI)
    for y in range(wy0, wy1 + 1):
        for x in range(wx0, wx1 + 1):
            e.px(x, y, mix((14, 16, 40), (50, 36, 80), (y - wy0) / (wy1 - wy0)))
    x = wx0
    while x < wx1:
        bw = int(rng.integers(6, 12))
        bh = int(rng.integers(14, wy1 - wy0 - 6))
        e.rect(x, wy1 - bh, min(wx1, x + bw), wy1, (34, 30, 58))
        for wy in range(wy1 - bh + 3, wy1 - 2, 4):
            for wxx in range(x + 1, min(wx1, x + bw) - 1, 3):
                if rng.random() < .35:
                    e.px(wxx, wy, (255, 214, 140))
        x += bw + 1
    c.a[wy0:wy1 + 1, wx0:wx1 + 1, 3] = 0
    c.rect((wx0 + wx1) // 2 - 1, wy0, (wx0 + wx1) // 2 + 1, wy1, INK)
    c.vline((wx0 + wx1) // 2, wy0, wy1, GOLD_LO)
    # boss NFT behind the desk
    spr = sprite('menu/boss-green-cut.png')
    bx = w // 2 - spr.shape[1] // 2
    by = desk_y - spr.shape[0] + 10
    c.blit(spr, bx, by)
    e.a[by:by + spr.shape[0], bx:bx + spr.shape[1], 3][spr[..., 3] > 0] = 0  # boss stands in front of the window
    # mahogany desk with gold trim
    c.rect(0, desk_y, w - 1, h - 1, INK)
    c.rect(0, desk_y + 1, w - 1, desk_y + 6, (104, 52, 34))
    c.hline(0, w - 1, desk_y + 1, (140, 76, 50))
    c.rect(0, desk_y + 7, w - 1, desk_y + 8, GOLD)
    c.rect(0, desk_y + 9, w - 1, h - 1, (90, 44, 28))
    for x0 in range(6, w - 20, 38):
        c.box(x0, desk_y + 12, x0 + 32, h - 4, (90, 44, 28), (120, 66, 44), (64, 30, 20))
    # gold lamp and money stacks
    lx = 12
    c.rect(lx, desk_y - 2, lx + 10, desk_y, GOLD_LO)
    c.vline(lx + 5, desk_y - 16, desk_y - 2, GOLD)
    c.poly([(lx - 2, desk_y - 16), (lx + 12, desk_y - 16), (lx + 9, desk_y - 22), (lx + 1, desk_y - 22)], (20, 110, 70))
    e.hline(lx, lx + 10, desk_y - 15, (255, 236, 180))
    for k in range(3):
        mx = w - 40 + k * 9
        for j in range(3 - k % 2):
            c.box(mx, desk_y - 4 - j * 3, mx + 8, desk_y - j * 3, (110, 170, 100), (150, 210, 130), (80, 130, 70))
    L = Lights(w, h, [0.30, 0.27, 0.26])
    L.point(lx + 5, desk_y - 14, 70, [0.95, 1.0, 0.65], 0.9, cone=True)
    L.spot(w / 2, -10, 0.45, h * 1.3, [1.0, 0.9, 0.65], 0.75)
    L.point(w / 2, wy0 + 10, 90, [0.5, 0.55, 1.0], 0.35)
    return c, L, e, dict(sparkles=[[w // 2 - 40, 30], [w // 2 + 38, 26], [w // 2 - 46, 70], [w // 2 + 44, 64]])
