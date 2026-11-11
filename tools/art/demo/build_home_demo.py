"""Bundle the game into one self-contained HTML page.

  python3 build_home_demo.py OUT.html          browser demo (local crew, 60x time)
  python3 build_home_demo.py OUT.html --live   the real game client, served by the server
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/art'))
from font import BIG, SMALL  # noqa: E402

A = ROOT / 'client/src/assets'
HOME = A / 'home'
HERE = Path(__file__).parent


def uri(p: Path) -> str:
    return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()


def screen(folder):
    lay = json.loads((folder / 'layout.json').read_text())
    imgs = {p.stem: uri(p) for p in sorted(folder.glob('*.png'))}
    imgs['bg'] = uri(folder / 'bg.png')
    if (folder / 'logo-neon.png').exists():
        imgs['neon'] = uri(folder / 'logo-neon.png')
    for c in lay['cards']:
        imgs['card-' + c['key']] = uri(folder / f"card-{c['key']}.png")
        if (folder / f"card-{c['key']}-blink.png").exists():
            imgs['card-' + c['key'] + '-blink'] = uri(folder / f"card-{c['key']}-blink.png")
    for t in lay.get('tiles', []):
        imgs['tile-' + t['key']] = uri(folder / f"tile-{t['key']}.png")
    return {'layout': lay, 'images': imgs}


from glyphs import all_fonts  # noqa: E402

LIVE = '--live' in sys.argv
# rules the browser needs, straight from the shared package
(HERE / 'rules.json').write_text(subprocess.run(['npx', 'tsx', str(HERE / 'export_rules.ts')], cwd=ROOT, check=True,
                                                capture_output=True, text=True).stdout)

KEYS = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
CARDS = A / 'cards'
cards = {'layout': json.loads((CARDS / 'layout.json').read_text()),
         'frames': {k: uri(CARDS / f'frame-{k}.png') for k in KEYS},
         'sprites': {k: uri(A / f'frogs/worker-{k}.png') for k in KEYS},
         'back': uri(CARDS / 'back.png'), 'icons': uri(CARDS / 'icons.png'),
         'rules': json.loads((HERE / 'rules.json').read_text())}
data = {'screens': {'home': screen(HOME), 'shop': screen(A / 'shop'), 'recruit': screen(A / 'recruit'), 'frogs': screen(A / 'frogs-screen'), 'boss': screen(A / 'boss-screen'), 'work': screen(A / 'work-screen'), 'casino': screen(A / 'casino-screen')},
        'shared': {'frogSprite': uri(A / 'frogs/worker-mythic.png')},
        'fonts': {'big': BIG, 'small': SMALL}, 'glyphs': all_fonts(), 'cards': cards, 'wallet': 0 if LIVE else 487140}
if LIVE:
    for name in ('login', 'wallet', 'invite', 'market'):
        data['screens'][name] = screen(A / f'{name}-screen')

LAYERS = ('bg', 'emissive', 'neon', 'bossdesk', 'chairs', 'desks')
offices = {k: {'layout': json.loads((A / 'office' / k / 'layout.json').read_text()),
               'images': {n: uri(A / 'office' / k / f'{n}.png') for n in LAYERS}} for k in ('memecoin', 'pumpfun', 'classic')}
casino = {'layout': json.loads((A / 'office/casino/layout.json').read_text()),
          'images': {n: uri(A / 'office/casino' / f'{n}.png') for n in LAYERS}}
ENGINES = ['office_engine.js', 'live_engine.js' if LIVE else 'crew_engine.js', 'cards_engine.js', 'recruit_engine.js',
           'frogs_engine.js', 'boss_engine.js', 'work_engine.js', 'casino_engine.js']
if LIVE:
    ENGINES += ['login_engine.js', 'wallet_engine.js', 'invite_engine.js', 'market_engine.js']
engine = '\n'.join((HERE / f).read_text() for f in ENGINES + ['home_engine.js'])

HEAD = ('<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="theme-color" content="#0b090d">\n'
        '<meta name="description" content="Frogotraderz: open packs, pull frogs, send them to trade. AFK on Solana.">\n'
        '<title>Frogotraderz</title>\n') if LIVE else '<title>Frogotraderz Game</title>\n<meta name="claude:viewport-fit-sides" content="cover">'
html = f'''{HEAD}
<style>
/* Layout: a single pixel-art game screen, scaled by whole numbers and centred. */
:root {{ --bg: #0b090d; color-scheme: dark; }}
html, body {{ height: 100%; background: var(--bg); }}
body {{ margin: 0; display: grid; place-items: center; padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 16px; box-sizing: border-box; }}
@media (max-width: 699px) {{ body {{ padding: 0; }} canvas {{ box-shadow: none; }} }}
canvas {{ touch-action: manipulation; -webkit-tap-highlight-color: transparent; }}
canvas {{ display: block; image-rendering: pixelated; image-rendering: crisp-edges; max-width: 100%; height: auto;
  box-shadow: 0 0 0 3px #000, 0 0 0 5px #2c2531; }}
</style>
<canvas id="home" aria-label="Frogotraderz game screens: home, shop and recruit"></canvas>
<script>window.FT_OFFICES = {json.dumps(offices)}; window.FT_CASINO = {json.dumps(casino)};</script>
<script>{engine}</script>
<script>
(function () {{
  const cv = document.getElementById('home');
  HomeScene.create({json.dumps(data)}, cv);
  function fit() {{
    const pad = window.innerWidth < 700 ? 0 : 32;
    const avail = Math.min(window.innerWidth - pad, (window.innerHeight - pad) * 640 / 360);
    const s = Math.max(1, Math.floor(avail / 640));
    cv.style.width = (avail >= 640 ? 640 * s : avail) + 'px';
  }}
  window.addEventListener('resize', fit); fit();
}})();
</script>
'''
out = Path(sys.argv[1])
out.write_text(html)
print(out, len(html) // 1024, 'KB')
