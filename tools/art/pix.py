"""Tiny pixel-art toolkit: palette grids, outlines, sprite sheets."""
from __future__ import annotations
from PIL import Image

RGBA = tuple[int, int, int, int]


def hex2rgba(h: str, a: int = 255) -> RGBA:
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def shade(h: str, f: float) -> str:
    r, g, b, _ = hex2rgba(h)
    c = lambda v: max(0, min(255, round(v * f)))
    return '#%02x%02x%02x' % (c(r), c(g), c(b))


def mix(h1: str, h2: str, t: float) -> str:
    a, b = hex2rgba(h1), hex2rgba(h2)
    return '#%02x%02x%02x' % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Canvas:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.px = self.img.load()

    def set(self, x: int, y: int, color: str | None, a: int = 255):
        if color is None or not (0 <= x < self.w and 0 <= y < self.h):
            return
        self.px[x, y] = hex2rgba(color, a)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return (0, 0, 0, 0)

    def rect(self, x, y, w, h, color, a=255):
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.set(i, j, color, a)

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def frame(self, x, y, w, h, color):
        self.hline(x, y, w, color); self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color); self.vline(x + w - 1, y, h, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for j in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for i in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((i + .5 - cx) / rx) ** 2 + ((j + .5 - cy) / ry) ** 2 <= 1:
                    self.set(i, j, color)

    def grid(self, x0, y0, rows: list[str], pal: dict[str, str | None]):
        """Paint ASCII art. Unknown chars and '.' are skipped."""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                c = pal.get(ch)
                if c:
                    self.set(x0 + i, y0 + j, c)

    def paste(self, other: 'Canvas', x, y):
        self.img.alpha_composite(other.img, (x, y))
        self.px = self.img.load()

    def outline(self, color: str):
        """Add a 1px outline around every opaque pixel (4-neighbour)."""
        src = self.img.copy().load()
        for y in range(self.h):
            for x in range(self.w):
                if src[x, y][3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < self.w and 0 <= yy < self.h and src[xx, yy][3] > 0:
                            self.set(x, y, color)
                            break

    def save(self, path, scale=1):
        im = self.img if scale == 1 else self.img.resize((self.w * scale, self.h * scale), Image.NEAREST)
        im.save(path)


def mirror_rows(half: list[str]) -> list[str]:
    """Build symmetric rows from their left halves."""
    return [r + r[::-1] for r in half]


def sheet(frames: list[Canvas]) -> Canvas:
    w, h = frames[0].w, frames[0].h
    out = Canvas(w * len(frames), h)
    for i, f in enumerate(frames):
        out.paste(f, i * w, 0)
    return out
