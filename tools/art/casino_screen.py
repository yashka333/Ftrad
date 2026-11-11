"""Casino screen: the Lucky Frog Casino room (client/src/assets/office/casino) under the game header.

Outputs client/src/assets/casino-screen/.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

from px2 import Canvas
from menu2 import header

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'client/src/assets'
OUT = A / 'casino-screen'
W, H = 640, 360


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    bg = Canvas(W, H)                      # header only: the room shows through below it
    lay = {'size': [W, H], 'hud': header(bg, 'CASINO'), 'cards': [], 'tiles': [], 'back': 'home', 'offset': 16}
    Image.fromarray(bg.a, 'RGBA').save(OUT / 'bg.png')
    for name in ('btn-work', 'btn-work-off', 'btn-stop', 'btn-stop-off'):
        shutil.copy(A / 'frogs-screen' / f'{name}.png', OUT / f'{name}.png')
    (OUT / 'layout.json').write_text(json.dumps(lay))


if __name__ == '__main__':
    build()
    print('casino screen ok')
