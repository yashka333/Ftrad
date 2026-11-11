"""Pixel drawing kit for scene art (numpy RGBA canvas, ink outlines, dithering)."""
from __future__ import annotations

import numpy as np
from PIL import Image

INK = (20, 18, 22)
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def rgb(h: str):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def sh(c, f):
    """Scale a color's brightness."""
    return tuple(int(max(0, min(255, v * f))) for v in c)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Canvas:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), dtype=np.uint8)

    # --- primitives -----------------------------------------------------
    def px(self, x, y, c, alpha=255):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            if alpha >= 255:
                self.a[y, x, :3] = c[:3]
                self.a[y, x, 3] = 255
            elif alpha > 0:
                k = alpha / 255
                o = self.a[y, x, :3].astype(float)
                self.a[y, x, :3] = (o * (1 - k) + np.array(c[:3]) * k).astype(np.uint8)
                self.a[y, x, 3] = max(int(self.a[y, x, 3]), alpha)

    def get(self, x, y):
        return tuple(int(v) for v in self.a[y, x, :3])

    def rect(self, x0, y0, x1, y1, c, alpha=255):
        x0, x1 = max(0, int(x0)), min(self.w - 1, int(x1))
        y0, y1 = max(0, int(y0)), min(self.h - 1, int(y1))
        if x0 > x1 or y0 > y1:
            return
        if alpha >= 255:
            self.a[y0:y1 + 1, x0:x1 + 1, :3] = c[:3]
            self.a[y0:y1 + 1, x0:x1 + 1, 3] = 255
        else:
            k = alpha / 255
            reg = self.a[y0:y1 + 1, x0:x1 + 1]
            reg[..., :3] = (reg[..., :3] * (1 - k) + np.array(c[:3]) * k).astype(np.uint8)
            reg[..., 3] = np.maximum(reg[..., 3], alpha)

    def hline(self, x0, x1, y, c, alpha=255):
        self.rect(min(x0, x1), y, max(x0, x1), y, c, alpha)

    def vline(self, x, y0, y1, c, alpha=255):
        self.rect(x, min(y0, y1), x, max(y0, y1), c, alpha)

    def line(self, x0, y0, x1, y1, c, alpha=255):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, c, alpha)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def box(self, x0, y0, x1, y1, fill, hi=None, lo=None, ink=INK):
        self.rect(x0, y0, x1, y1, ink)
        self.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)
        if hi:
            self.hline(x0 + 1, x1 - 1, y0 + 1, hi)
            self.vline(x0 + 1, y0 + 1, y1 - 1, hi)
        if lo:
            self.hline(x0 + 1, x1 - 1, y1 - 1, lo)
            self.vline(x1 - 1, y0 + 2, y1 - 1, lo)

    def ellipse(self, cx, cy, rx, ry, c, alpha=255):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if ((x - cx) / max(rx, .5)) ** 2 + ((y - cy) / max(ry, .5)) ** 2 <= 1:
                    self.px(x, y, c, alpha)

    def poly(self, pts, c, alpha=255):
        """Scanline fill of a polygon given as [(x, y), ...]."""
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
                if y0 == y1:
                    continue
                if min(y0, y1) <= y + .5 < max(y0, y1):
                    xs.append(x0 + (y + .5 - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(round(xs[i])), int(round(xs[i + 1])) - 1, y, c, alpha)

    def mask(self, m: np.ndarray, x, y, c, alpha=255):
        for j, i in zip(*np.nonzero(m)):
            self.px(x + i, y + j, c, alpha)

    def blit(self, img: np.ndarray, x, y, clip=None):
        h, w = img.shape[:2]
        for j in range(h):
            for i in range(w):
                if img[j, i, 3]:
                    X, Y = x + i, y + j
                    if clip and not clip(X, Y):
                        continue
                    self.px(X, Y, tuple(int(v) for v in img[j, i, :3]), int(img[j, i, 3]))

    def outline(self, color=INK):
        """1px outline around everything opaque."""
        a = self.a[..., 3] > 0
        pad = np.pad(a, 1)
        ring = (~a) & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
        self.a[ring, :3] = color
        self.a[ring, 3] = 255

    def save(self, path):
        Image.fromarray(self.a, 'RGBA').save(path)

    def image(self):
        return Image.fromarray(self.a, 'RGBA')


def dither(x, y, t):
    """True on a Bayer pattern for coverage t in [0, 1]."""
    return BAYER4[y % 4, x % 4] < t
