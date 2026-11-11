"""Builds capture.html: the office engine with every room, frog and boss image,
driven by a fake clock so footage can be grabbed frame by frame."""
import base64
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / 'client/src/assets'
HERE = Path(__file__).parent
OUT = HERE / 'build'
OUT.mkdir(exist_ok=True)


def uri(p) -> str:
    if isinstance(p, Image.Image):
        import io
        b = io.BytesIO(); p.save(b, 'PNG'); data = b.getvalue()
    else:
        data = Path(p).read_bytes()
    return 'data:image/png;base64,' + base64.b64encode(data).decode()


def pixel_scale(img: Image.Image, f: float) -> Image.Image:
    """Shrink pixel art: average colours, then snap alpha so edges stay hard."""
    w, h = round(img.width * f), round(img.height * f)
    a = np.array(img.convert('RGBA').resize((w, h), Image.BOX)).astype(float)
    alpha = a[..., 3:4] / 255
    rgb = np.where(alpha > 0, a[..., :3] / np.maximum(alpha, 1e-6), 0)
    out = np.zeros((h, w, 4), np.uint8)
    keep = a[..., 3] > 110
    out[..., :3] = np.clip(rgb, 0, 255)
    out[..., 3] = np.where(keep, 255, 0)
    return Image.fromarray(out)


LAYERS = ('bg', 'emissive', 'neon', 'bossdesk', 'chairs', 'desks')
rooms = {}
for key in ('memecoin', 'pumpfun', 'classic'):
    d = A / 'office' / key
    rooms[key] = dict(layout=json.loads((d / 'layout.json').read_text()), images={n: uri(d / f'{n}.png') for n in LAYERS})
# ---- 'desk': one memecoin desk cut out of the office, on a plain dark backdrop
def desk_room():
    d = A / 'office' / 'memecoin'
    lay = json.loads((d / 'layout.json').read_text())
    W, H = 640, 360
    x0, x1, y0, y1 = 266, 374, 240, 327
    def only_desk(name):
        a = np.array(Image.open(d / f'{name}.png').convert('RGBA'))
        keep = np.zeros(a.shape[:2], bool)
        keep[y0:y1 + 1, x0:x1 + 1] = True
        a[~keep, 3] = 0
        return Image.fromarray(a)
    yy = np.arange(H)[:, None].repeat(W, 1)
    bg = np.zeros((H, W, 4), np.uint8)
    t = yy / H
    bg[..., 0] = (40 - 18 * t).astype(np.uint8)
    bg[..., 1] = (34 - 16 * t).astype(np.uint8)
    bg[..., 2] = (52 - 22 * t).astype(np.uint8)
    bg[..., 3] = 255
    floor = 326
    rng = np.random.default_rng(2)
    for y in range(floor, H):
        row = (y - floor) // 5
        for xs in range(-(row * 23) % 40, W, 40):
            col = [(70, 46, 34), (64, 42, 30), (76, 50, 36)][int(rng.integers(0, 3))]
            bg[y, max(0, xs):xs + 39, :3] = col
            if (y - floor) % 5 == 4:
                bg[y, max(0, xs):xs + 39, :3] = (40, 26, 20)
    bg[floor, :, :3] = (24, 18, 18)
    empty = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lamp = [lp for lp in lay['desks'][2]['lamps']]
    lay['desks'] = [lay['desks'][2]]
    lay['lights'] = [
        dict(x=320, y=150, r=230, col=[1.0, 0.86, 0.66], i=1.25, cone=True, kind='lamp'),
        dict(x=320, y=300, r=170, col=[0.55, 0.45, 0.9], i=0.35),
    ]
    lay['theme'] = dict(lay['theme'], ambient=[0.16, 0.15, 0.22], cones=False, rain=False)
    imgs = dict(bg=uri(Image.fromarray(bg)), emissive=uri(empty), neon=uri(empty), bossdesk=uri(empty),
                chairs=uri(only_desk('chairs')), desks=uri(only_desk('desks')))
    return dict(layout=lay, images=imgs)


rooms['desk'] = desk_room()
frogs = {f'frog-{r}': uri(A / f'frogs/worker-{r}.png') for r in ('common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic')}
bosses = {}
for k in ('orig', 'blue', 'purple', 'green'):
    im = Image.open(HERE / f'build/boss-{k}-clean.png').convert('RGBA')
    for f in (1.0, 0.8, 0.7, 0.6):
        bosses[f'{k}@{f}'] = uri(im if f == 1.0 else pixel_scale(im, f))

engine = (ROOT / 'tools/art/demo/office_engine.js').read_text()
clock = """
(function(){
  let s = 1234567;
  Math.random = function(){ s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  window.__seed = (v) => { s = v; };
  window.__cbs = []; window.__now = 1000;
  window.requestAnimationFrame = (cb) => { window.__cbs.push(cb); return window.__cbs.length; };
  window.cancelAnimationFrame = () => {};
  performance.now = () => window.__now;
  window.__step = (ms) => { window.__now += ms; const c = window.__cbs; window.__cbs = []; c.forEach((f) => f(window.__now)); };
})();
"""
html = f"""<!doctype html><html><body style="margin:0;background:#000">
<canvas id="c"></canvas><div id="tip" hidden></div>
<script>{clock}</script>
<script>window.ROOMS = {json.dumps(rooms)}; window.FROGS = {json.dumps(frogs)}; window.BOSSES = {json.dumps(bosses)};</script>
<script>{engine}</script>
<script>
window.makeScene = function (room, opts) {{
  const r = ROOMS[room];
  const images = Object.assign({{}}, r.images, FROGS);
  if (opts.boss) images.boss = BOSSES[opts.boss];
  const D = {{ layout: JSON.parse(JSON.stringify(r.layout)), images, frogs: opts.frogs, showBoss: !!opts.boss, bossSink: opts.bossSink }};
  if (window.scene) window.scene.stop();
  window.scene = OfficeScene.create(D, document.getElementById('c'), document.getElementById('tip'));
}};
</script></body></html>"""
(OUT / 'capture.html').write_text(html)
print('ok', OUT / 'capture.html')
