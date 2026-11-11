"""Exports the three pixel fonts (Jersey 10, Jersey 15, Tiny5) as 1-bit glyph strips,
so the browser engines draw runtime text (names, numbers) in the same fonts as the baked art.

Format per style: {"h": rows, "base": baseline row, "g": {char: "rows joined by |"}} with '#' for ink.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from menu_kit import _FONTS

CHARS = ''.join(chr(c) for c in range(32, 127)) + '…·×'


def export(style: str) -> dict:
    path, size = _FONTS[style]
    font = ImageFont.truetype(str(path), size)
    asc, desc = font.getmetrics()
    h = asc + desc
    out = {}
    for ch in CHARS:
        adv = max(1, round(font.getlength(ch)))
        img = Image.new('L', (adv + 8, h + 4), 0)
        d = ImageDraw.Draw(img)
        d.fontmode = '1'
        d.text((2, 2), ch, font=font, fill=255)
        m = np.array(img) > 127
        m = m[2:2 + h]
        cols = np.nonzero(m.any(0))[0]
        if ch == ' ' or not len(cols):
            out[ch] = '|'.join('.' * max(2, adv // 2) for _ in range(h))
            continue
        m = m[:, cols.min():cols.max() + 1]
        out[ch] = '|'.join(''.join('#' if v else '.' for v in row) for row in m)
    if style == 'head':  # Jersey 15 draws K like H at this size: hand-drawn K
        rows = out['H'].split('|')
        ink = [i for i, r in enumerate(rows) if '#' in r]
        shape = ['##.##', '##.##', '##.#.', '####.', '####.', '##.#.', '##.##', '##.##']
        k = ['.' * 5] * len(rows)
        for j, i in enumerate(range(ink[0], ink[-1] + 1)):
            k[i] = shape[min(len(shape) - 1, round(j * (len(shape) - 1) / max(1, ink[-1] - ink[0])))]
        out['K'] = '|'.join(k)
    # trim empty rows shared by every glyph (top and bottom)
    rows = [g.split('|') for g in out.values()]
    used = [any('#' in r[i] for r in rows) for i in range(h)]
    top = used.index(True)
    bot = h - 1 - used[::-1].index(True)
    out = {k: '|'.join(v.split('|')[top:bot + 1]) for k, v in out.items()}
    return {'h': bot - top + 1, 'base': asc - top, 'g': out}


def all_fonts() -> dict:
    return {s: export(s) for s in ('title', 'head', 'body')}


if __name__ == '__main__':
    f = all_fonts()
    for k, v in f.items():
        print(k, v['h'], v['g']['K'].replace('|', '\n'), sep='\n')
    Path('/tmp/claude-0/-home-claude/f782d41d-8771-50ed-9d54-4ef8681aae6f/scratchpad/glyphs.json').write_text(json.dumps(f))
