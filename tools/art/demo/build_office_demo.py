"""Bundle the office scenes into one self-contained HTML page with a room switcher."""
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / 'client/src/assets'
HERE = Path(__file__).parent


def uri(p: Path) -> str:
    return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()


LAYERS = ('bg', 'emissive', 'neon', 'bossdesk', 'chairs', 'desks')
frog_imgs = {f'frog-{r}': uri(A / f'frogs/worker-{r}.png') for r in ('common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic')}
bosses = [uri(A / f'menu/boss-{k}-cut.png') for k in ('orig', 'blue', 'purple', 'green')]


def frog(name, rarity, stamina, power, skill, state='work'):
    return dict(name=name, rarity=rarity, stamina=stamina, power=power, skill=skill, state=state)


ROOMS = [
    dict(key='memecoin', name='Memecoin Trading', head=['MEMECOIN', 'TRADING'], accent='#e8662f', office='01',
         frogs=[frog('Dusty', 'common', 83, 2, 'No skills yet'), frog('Mochi', 'uncommon', 0, 5, 'Pattern Hunter', 'sleep'), None,
                frog('Ledger', 'rare', 72, 8, 'Chart Wizard'), frog('Big Wick', 'legendary', 64, 14, 'Diamond Hands, Hot Streak')]),
    dict(key='pumpfun', name='Pump.fun Rugs', head=['PUMP.FUN', 'RUGS'], accent='#ff46aa', office='02',
         frogs=[frog('Rugpull Ray', 'epic', 77, 11, 'Rug Radar, Degen Ape'), frog('Gas Fee', 'common', 40, 1, 'No skills yet'),
                frog('Sniper', 'mythic', 91, 17, 'Fast Fingers, Hot Streak, Rug Radar'), None,
                frog('Paper', 'uncommon', 0, 4, 'Degen Ape', 'sleep')]),
    dict(key='classic', name='Classic Trading', head=['CLASSIC', 'TRADING'], accent='#3cc6a8', office='03',
         frogs=[frog('Old Bond', 'epic', 88, 10, 'Diamond Hands, Chart Wizard'), frog('Dividend', 'rare', 70, 7, 'Pattern Hunter'),
                None, frog('Blue Chip', 'legendary', 55, 13, 'Insomniac, Chart Wizard'), frog('Coupon', 'common', 0, 2, 'No skills yet', 'sleep')]),
]
rooms = []
for r in ROOMS:
    d = A / 'office' / r['key']
    if not (d / 'layout.json').exists():
        continue
    imgs = {n: uri(d / f'{n}.png') for n in LAYERS}
    rooms.append(dict(key=r['key'], name=r['name'], head=r['head'], accent=r['accent'], office=r['office'],
                      layout=json.loads((d / 'layout.json').read_text()), images=imgs, frogs=r['frogs']))
engine = (HERE / 'office_engine.js').read_text()
tabs = ''.join(f'<button class="tab" role="tab" data-i="{i}" style="--c:{r["accent"]}"><i></i>{r["name"]}</button>' for i, r in enumerate(rooms))

html = f'''<title>Frog Traders Offices</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Silkscreen&display=swap">
<style>
/* Layout: one framed scene with a slim stat strip above it, like a game HUD. */
:root {{
  --bg: #0d0b11; --panel: #17131b; --line: #2c2531; --ink: #f2e7d4; --muted: #9b8f86;
  --accent: #e8662f; --gold: #f0be52; --good: #6ee06a; --bad: #ff5a50; --sleep: #8aa8ff;
  --display: "Jersey 10", "Courier New", monospace; --label: "Silkscreen", "Courier New", monospace;
  color-scheme: dark;
}}
html, body {{ background: var(--bg); color: var(--ink); }}
body {{ font-family: var(--label); padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 18px 28px; }}
.wrap {{ max-width: 1280px; margin: 0 auto; display: grid; gap: 12px; }}
header {{ display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: 12px; }}
.crumb {{ font-size: 11px; letter-spacing: .12em; color: var(--muted); text-transform: uppercase; }}
h1 {{ font-family: var(--display); font-weight: 400; font-size: clamp(34px, 5vw, 52px); line-height: .9; margin: 4px 0 0;
  letter-spacing: .02em; text-wrap: balance; }}
h1 em {{ font-style: normal; color: var(--room, var(--accent)); }}
.tabs {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.tab {{ font-family: var(--label); font-size: 11px; letter-spacing: .06em; color: var(--muted); background: var(--panel); border: 2px solid var(--line);
  padding: 7px 12px 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; }}
.tab i {{ width: 8px; height: 8px; background: var(--c); display: inline-block; }}
.tab[aria-selected="true"] {{ color: var(--ink); border-color: var(--c); box-shadow: inset 0 -3px 0 var(--c); }}
.tab:focus-visible {{ outline: 2px solid var(--c); outline-offset: 2px; }}
.stats {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.stat {{ background: var(--panel); border: 2px solid var(--line); padding: 6px 10px 5px; min-width: 92px; }}
.stat small {{ display: block; font-size: 9px; letter-spacing: .14em; color: var(--muted); text-transform: uppercase; }}
.stat b {{ font-family: var(--display); font-weight: 400; font-size: 24px; line-height: 1; font-variant-numeric: tabular-nums; }}
.stat b.good {{ color: var(--good); }} .stat b.sleep {{ color: var(--sleep); }}
.stage {{ position: relative; border: 3px solid #000; outline: 2px solid var(--line); background: #000; line-height: 0; }}
canvas {{ width: 100%; height: auto; image-rendering: pixelated; image-rendering: crisp-edges; display: block; }}
#tip {{ position: absolute; z-index: 2; pointer-events: none; min-width: 170px; max-width: 230px; line-height: 1.35;
  background: var(--panel); border: 2px solid var(--room, var(--accent)); padding: 8px 10px; font-size: 10px; color: var(--ink);
  box-shadow: 4px 4px 0 #000; }}
#tip b {{ font-family: var(--display); font-weight: 400; font-size: 22px; display: block; line-height: 1; }}
#tip .r {{ display: inline-block; margin-top: 3px; font-size: 9px; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }}
#tip .r.common {{ color: #c9cdd6; }} #tip .r.uncommon {{ color: #6ee06a; }} #tip .r.rare {{ color: #4aa8ff; }}
#tip .r.epic {{ color: #b66fff; }} #tip .r.legendary {{ color: #ffb42e; }} #tip .r.mythic {{ color: #ff4d6d; }}
#tip p {{ margin: 6px 0 0; color: var(--muted); }}
#tip .bar {{ height: 6px; background: #000; margin-top: 7px; border: 1px solid var(--line); }}
#tip .bar i {{ display: block; height: 100%; background: var(--good); }}
.hint {{ font-size: 10px; color: var(--muted); letter-spacing: .08em; }}
.modal[hidden] {{ display: none; }}
.modal {{ position: fixed; inset: 0; z-index: 20; display: grid; place-items: center; background: rgba(6, 4, 8, .72);
  padding: max(16px, env(safe-area-inset-top, 0px)) max(16px, env(safe-area-inset-right, 0px)) max(16px, env(safe-area-inset-bottom, 0px)) max(16px, env(safe-area-inset-left, 0px)); }}
.sheet {{ position: relative; width: min(520px, 100%); max-height: 100%; overflow: auto; background: var(--panel);
  border: 3px solid #000; outline: 2px solid var(--gold); box-shadow: 8px 8px 0 #000; padding: 20px 20px 18px; display: grid; gap: 14px; }}
.sheet .eyebrow {{ font-size: 10px; letter-spacing: .16em; color: var(--gold); text-transform: uppercase; }}
.sheet h2 {{ font-family: var(--display); font-weight: 400; font-size: 44px; line-height: .9; margin: 2px 0 0; }}
.sheet p {{ margin: 0; font-size: 11px; line-height: 1.6; color: var(--ink); }}
.sheet .x {{ position: absolute; top: 10px; right: 10px; width: 32px; height: 32px; background: #000; color: var(--ink);
  border: 2px solid var(--line); font-family: var(--display); font-size: 24px; line-height: 1; cursor: pointer; }}
.sheet .x:hover, .sheet .x:focus-visible {{ border-color: var(--gold); color: var(--gold); outline: none; }}
.bosses {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }}
.bosses img {{ width: 100%; aspect-ratio: 1; image-rendering: pixelated; background: #0a080d; border: 2px solid var(--line); display: block; }}
.ways {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.way {{ background: #0a080d; border: 2px solid var(--line); padding: 10px 12px; display: grid; gap: 2px; }}
.way small {{ font-size: 9px; letter-spacing: .14em; color: var(--muted); text-transform: uppercase; }}
.way b {{ font-family: var(--display); font-weight: 400; font-size: 34px; line-height: 1; color: var(--gold); }}
.way span {{ font-size: 10px; color: var(--muted); }}
.soon {{ font-size: 10px; color: var(--muted); letter-spacing: .08em; border-top: 2px dashed var(--line); padding-top: 10px; }}
@media (max-width: 460px) {{ .ways {{ grid-template-columns: 1fr; }} .sheet h2 {{ font-size: 36px; }} }}
</style>
<div class="wrap">
  <div class="tabs" role="tablist" aria-label="Offices">{tabs}</div>
  <header>
    <div>
      <div class="crumb" id="crumb">Croak St. / Go to work</div>
      <h1 id="title"></h1>
    </div>
    <div class="stats">
      <div class="stat"><small>Desks</small><b id="sDesks"></b></div>
      <div class="stat"><small>Trading</small><b class="good" id="sTrading"></b></div>
      <div class="stat"><small>Asleep</small><b class="sleep" id="sAsleep"></b></div>
      <div class="stat"><small>Est. per hour</small><b id="sRate"></b></div>
    </div>
  </header>
  <div class="stage">
    <canvas id="scene" aria-label="Office with an empty boss seat and five worker desks"></canvas>
    <div id="tip" hidden></div>
  </div>
  <div class="hint">Hover a desk to inspect a frog. Click the boss seat to learn about Boss Frogs.</div>
</div>
<div class="modal" id="bossModal" hidden role="dialog" aria-modal="true" aria-labelledby="bossTitle">
  <div class="sheet">
    <button class="x" id="bossClose" aria-label="Close">×</button>
    <div class="eyebrow">Boss seat · empty</div>
    <h2 id="bossTitle">Boss Frogs</h2>
    <div class="bosses">{''.join(f'<img src="{b}" alt="Boss Frog NFT">' for b in bosses)}</div>
    <p>Boss Frogs are an NFT collection. Seat a boss in this chair and it runs the office for you: rested frogs go back to their desks automatically.</p>
    <div class="ways">
      <div class="way"><small>Mint</small><b>$100</b><span>Buy a Boss Frog</span></div>
      <div class="way"><small>Whitelist</small><b>Free</b><span>WL holders mint for free</span></div>
    </div>
    <div class="soon">Full details and mint date coming soon.</div>
  </div>
</div>
<script>window.ROOMS = {json.dumps(rooms)}; window.FROG_IMGS = {json.dumps(frog_imgs)};</script>
<script>{engine}</script>
<script>
(function () {{
  const canvas = document.getElementById('scene'), tip = document.getElementById('tip');
  const tabsEl = [...document.querySelectorAll('.tab')];
  let scene = null;
  function show(i) {{
    const r = ROOMS[i];
    if (scene) scene.stop();
    scene = OfficeScene.create(Object.assign({{}}, r, {{ images: Object.assign({{}}, r.images, FROG_IMGS) }}), canvas, tip);
    document.documentElement.style.setProperty('--room', r.accent);
    document.getElementById('title').innerHTML = '<em>' + r.head[0] + '</em> ' + r.head[1];
    document.getElementById('crumb').textContent = 'Croak St. / Go to work / Office ' + r.office;
    const seated = r.frogs.filter(Boolean), working = seated.filter((f) => f.state !== 'sleep');
    document.getElementById('sDesks').textContent = seated.length + '/5';
    document.getElementById('sTrading').textContent = working.length;
    document.getElementById('sAsleep').textContent = seated.length - working.length;
    const rate = working.reduce((a, f) => a + f.power, 0) * 52;
    document.getElementById('sRate').textContent = '+' + rate.toLocaleString('en-US') + ' $FROG';
    tabsEl.forEach((t, k) => {{ t.setAttribute('aria-selected', k === i ? 'true' : 'false'); t.tabIndex = k === i ? 0 : -1; }});
    try {{ localStorage.setItem('ft-room', String(i)); }} catch (e) {{}}
  }}
  tabsEl.forEach((t, k) => t.addEventListener('click', () => show(k)));
  let start = 0;
  try {{ start = Math.min(ROOMS.length - 1, Math.max(0, +localStorage.getItem('ft-room') || 0)); }} catch (e) {{}}
  const hash = location.hash.slice(1), hi = ROOMS.findIndex((r) => r.key === hash);
  show(hi >= 0 ? hi : start);
}})();
(function () {{
  const m = document.getElementById('bossModal'), close = document.getElementById('bossClose');
  let back = null;
  function open() {{ back = document.activeElement; m.hidden = false; close.focus(); }}
  function shut() {{ m.hidden = true; if (back && back.focus) back.focus(); }}
  window.addEventListener('office:boss-seat', open);
  close.addEventListener('click', shut);
  m.addEventListener('click', (e) => {{ if (e.target === m) shut(); }});
  document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape' && !m.hidden) shut(); }});
}})();
</script>
'''
out = Path(sys.argv[1])
out.write_text(html)
print(out, len(html) // 1024, 'KB')
