/* Frog cards: composes a card (frame, frog, name, stats, skills) once, caches it, and draws it with a flip.
 * FTCards.init(data, load, blinkOf) then FTCards.draw(ctx, frog, x, y, { flip: 0..1, back: bool }).
 * frog = { id, name, rarity, stats: { patience, profit, risk }, skills: [ids] }
 */
(function () {
  'use strict';
  const KEYS = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic'];
  let L = null, frames = {}, back = null, icons = null, sprites = {}, blinks = {}, rules = null;
  const cache = new Map();

  async function init(data, load, blinkOf) {
    L = data.layout; rules = data.rules;
    for (const k of KEYS) {
      frames[k] = await load(data.frames[k]);
      sprites[k] = await load(data.sprites[k]);
      blinks[k] = blinkOf(sprites[k]);
    }
    back = await load(data.back);
    icons = await load(data.icons);
  }

  const compact = (v) => (v >= 1000 ? (v / 1000).toFixed(v >= 10000 ? 0 : 1).replace('.0', '') + 'K' : String(v));

  function icon(g, name, x, y) {
    const b = L.icons[name]; if (!b) return;
    g.drawImage(icons, b[0], b[1], b[2], b[3], x, y, b[2], b[3]);
  }

  /** Builds the card face into an offscreen canvas. */
  function face(ctx, frog, blink) {
    const key = (frog.uid || frog.id) + ':' + (blink ? 1 : 0);
    if (cache.has(key)) return cache.get(key);
    const [W, H] = L.size;
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d'); g.imageSmoothingEnabled = false;
    const rk = KEYS[frog.rarity];
    g.drawImage(frames[rk], 0, 0);
    const [ax0, ay0, ax1, ay1] = L.art;
    const sp = blink ? blinks[rk] : sprites[rk];
    g.drawImage(sp, Math.round((ax0 + ax1) / 2 - sp.width / 2), ay1 - 2 - sp.height);
    // draw text into this canvas with the shared glyph renderer
    const id = '#' + frog.id;
    withG(ctx, g, () => {
      ctx.gtext(id, ax1 - 2, ay0 + 3, '#f2e7d4', 'body', { align: 'right', shadow: '#141216' });
      ctx.gtext(frog.name.toUpperCase(), W / 2, 131, '#f2e7d4', 'body', { align: 'center' });
      const vals = [String(frog.stats.patience), compact(frog.stats.profit), frog.stats.risk + '%'];
      ['patience', 'profit', 'risk'].forEach((s, i) => {
        const [wx, wy] = L.stats[i];
        icon(g, 'stat-' + s, wx + 3, wy + 3);
        ctx.gtext(vals[i], wx + 14, wy + 4, '#ffe9b0', 'body', { shadow: null });
      });
      const sk = frog.skills;
      const total = sk.length * 18 - 2, sx = Math.round(W / 2 - total / 2);
      if (!sk.length) ctx.gtext('NO SKILLS', W / 2, 162, '#6d6475', 'body', { align: 'center', shadow: null });
      sk.forEach((s, i) => icon(g, 'skill-' + s, sx + i * 18, 157));
    });
    cache.set(key, c);
    return c;
  }

  // gtext in the engine draws on its own context; swap it for the card canvas
  function withG(ctx, g, fn) {
    const real = ctx.g;
    ctx.__swap && ctx.__swap(g);
    try { fn(); } finally { ctx.__swap && ctx.__swap(real); }
  }

  /** Skill under a point of a card drawn at (x, y), or null. */
  function skillAt(frog, x, y, px, py) {
    const [W] = L.size, sk = frog.skills, total = sk.length * 18 - 2, sx = Math.round(W / 2 - total / 2);
    for (let i = 0; i < sk.length; i++) {
      const X = x + sx + i * 18, Y = y + 157;
      if (px >= X && px < X + 16 && py >= Y && py < Y + 16) return sk[i];
    }
    return null;
  }

  function draw(ctx, frog, x, y, o = {}) {
    const [W, H] = L.size;
    const flip = o.flip == null ? 1 : o.flip;          // 0 = back, 1 = face
    const showFace = flip >= 0.5;
    const k = Math.abs(Math.cos(flip * Math.PI));        // width factor
    const w = Math.max(2, Math.round(W * k));
    const img = showFace ? face(ctx, frog, o.blink) : back;
    ctx.g.drawImage(img, 0, 0, W, H, Math.round(x + (W - w) / 2), Math.round(y), w, H);
  }

  const sprite = (rarity, blink) => (blink ? blinks : sprites)[KEYS[rarity]];
  const drawIcon = (ctx, name, x, y) => icon(ctx.g, name, x, y);
  window.FTCards = { init, draw, skillAt, sprite, icon: drawIcon, size: () => L.size, compact };
})();
