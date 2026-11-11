"""Go to work screen: the three lit offices under the game header, with office tabs in the header
and the crew buttons on the floor. The office rooms themselves come from client/src/assets/office/.

Outputs client/src/assets/work-screen/.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

from px2 import Canvas
from menu2 import button, header

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'client/src/assets'
OUT = A / 'work-screen'
W, H = 640, 360
OFFSET = 16          # the office is drawn this many pixels down, under the header
PATHS = (('memecoin', (232, 108, 46)), ('pumpfun', (200, 70, 200)), ('classic', (60, 198, 168)))
TAB_W, TAB_H = 82, 24


def save(c, name):
    Image.fromarray(c.a, 'RGBA').save(OUT / name)


def tab(col):
    c = Canvas(TAB_W, TAB_H)
    button(c, 0, 0, TAB_W - 1, TAB_H - 1, col)
    return c


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    bg = Canvas(W, H)                      # header only: the office shows through below it
    lay = {'size': [W, H], 'hud': header(bg, back=True), 'cards': [], 'tiles': [], 'back': 'home', 'offset': OFFSET}
    save(bg, 'bg.png')
    save(tab((62, 56, 72)), 'tab.png')
    for key, col in PATHS:
        save(tab(col), f'tab-{key}.png')
    lay['tabs'] = [{'key': k, 'x': 40 + i * (TAB_W + 4), 'y': 4, 'w': TAB_W, 'h': TAB_H} for i, (k, _) in enumerate(PATHS)]
    for name in ('btn-allwork', 'btn-allrest', 'btn-work', 'btn-work-off', 'btn-rest', 'btn-rest-off',
                 'btn-stop', 'btn-stop-off', 'btn-assign'):
        shutil.copy(A / 'frogs-screen' / f'{name}.png', OUT / f'{name}.png')
    lay['bottom'] = {'allwork': {'x': 8, 'y': 340, 'w': 108, 'h': 16}, 'allrest': {'x': 120, 'y': 340, 'w': 108, 'h': 16}}
    (OUT / 'layout.json').write_text(json.dumps(lay))


if __name__ == '__main__':
    build()
    print('work screen ok')
