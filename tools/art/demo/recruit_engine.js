/* Recruit screen: pick a pack size, open packs, watch the cards flip, send the frogs to work.
 * Registers window.FTScreens.recruit for HomeScene. Rolls use the shared rules (demo only: the real game rolls on the server).
 */
(function () {
  'use strict';
  const KEYS = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic'];
  const COL = ['#c9cdd6', '#6ee06a', '#4aa8ff', '#b66fff', '#ffb42e', '#ff4d6d'];
  const RGB = [[201, 205, 214], [110, 224, 106], [74, 168, 255], [182, 111, 255], [255, 180, 46], [255, 77, 109]];
  let R = null;                       // rules
  let packMask = null, rays = {};
  let nextId = 18788;
  const st = { mode: 'idle', n: 1, frogs: [], t0: 0, page: 0, now: 0, flipAt: {}, tip: null, shake: 0 };
  const parts = [];

  // ------------------------------------------------------------ rolls (same tables as shared/src)
  const randInt = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));
  function rollRarity() {
    const total = R.rarities.reduce((s, r) => s + r.odds, 0);
    let roll = Math.random() * total;
    for (const r of R.rarities) { roll -= r.odds; if (roll < 0) return r.id; }
    return 0;
  }
  function rollSkills(count) {
    const pool = Object.keys(R.skills), out = [];
    while (out.length < count && pool.length) {
      const total = pool.reduce((s, id) => s + R.skillWeight[R.skills[id].tier], 0);
      let roll = Math.random() * total, pick = pool.length - 1;
      for (let i = 0; i < pool.length; i++) { roll -= R.skillWeight[R.skills[pool[i]].tier]; if (roll < 0) { pick = i; break; } }
      out.push(pool[pick]); pool.splice(pick, 1);
    }
    return out;
  }
  function makeFrog() {
    const rarity = rollRarity(), r = R.rarities[rarity];
    return {
      id: nextId++, rarity,
      name: R.names[Math.floor(Math.random() * R.names.length)],
      stats: { patience: randInt(...r.patience), profit: randInt(...r.profit), risk: randInt(...r.risk) },
      skills: rollSkills(randInt(...r.skills)),
    };
  }

  // ------------------------------------------------------------ precomputed effects
  function makeRays(W, H, cx, cy) {
    // 16 rotation frames of dithered light beams, as alpha masks
    const frames = [];
    for (let f = 0; f < 16; f++) {
      const c = document.createElement('canvas'); c.width = W; c.height = H;
      const g = c.getContext('2d'), d = g.createImageData(W, H), a = d.data;
      const B = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        const dx = x - cx, dy = y - cy, dist = Math.hypot(dx, dy);
        const ang = Math.atan2(dy, dx) / (Math.PI * 2) * 10 + f / 16;
        const ph = ang - Math.floor(ang);
        if (ph > 0.3) continue;
        const fall = Math.max(0, 1 - dist / 230) * 0.9 * Math.min(1, dist / 40);
        if (B[(y >> 1) & 3][(x >> 1) & 3] / 16 < fall) { const i = (y * W + x) * 4; a[i] = a[i + 1] = a[i + 2] = 255; a[i + 3] = 255; }
      }
      g.putImageData(d, 0, 0);
      frames.push(c);
    }
    return frames;
  }
  function tinted(frames, color) {
    if (rays[color]) return rays[color];
    rays[color] = frames.map((f) => {
      const c = document.createElement('canvas'); c.width = f.width; c.height = f.height;
      const g = c.getContext('2d'); g.drawImage(f, 0, 0); g.globalCompositeOperation = 'source-in';
      g.fillStyle = color; g.fillRect(0, 0, c.width, c.height); return c;
    });
    return rays[color];
  }
  let rayFrames = null;
  function drawRays(ctx, t, color, alpha) {
    if (alpha <= 0) return;
    const fr = tinted(rayFrames, color);
    ctx.g.globalAlpha = alpha;
    ctx.g.drawImage(fr[Math.floor(t * 6) % fr.length], 0, 0);
    ctx.g.globalAlpha = 1;
  }

  function sparkle(ctx, x, y, size, c1 = '#fff6d2', c2 = '#ffd66e') {
    ctx.px(x, y, c1);
    for (let k = 1; k <= size; k++) { ctx.px(x - k, y, c2, 0.8 / k); ctx.px(x + k, y, c2, 0.8 / k); ctx.px(x, y - k, c2, 0.8 / k); ctx.px(x, y + k, c2, 0.8 / k); }
  }
  function burst(x, y, n, cols, speed = [1.5, 4.5], life = [0.5, 1.1]) {
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2, v = speed[0] + Math.random() * (speed[1] - speed[0]);
      parts.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 1, life: life[0] + Math.random() * (life[1] - life[0]), age: 0, c: cols[i % cols.length], s: 1 + (i % 3 === 0) });
    }
  }
  function stepParts(ctx, dt) {
    for (const p of parts) { p.x += p.vx; p.y += p.vy; p.vy += 0.12; p.vx *= 0.97; p.age += dt; }
    for (let i = parts.length - 1; i >= 0; i--) if (parts[i].age > parts[i].life) parts.splice(i, 1);
    for (const p of parts) { const k = 1 - p.age / p.life; ctx.rect(p.x, p.y, p.x + p.s - 1, p.y + p.s - 1, p.c, Math.min(1, k * 1.5)); }
  }

  // ------------------------------------------------------------ layout helpers
  const lay = (ctx) => ctx.L;
  const FREE_BTN = { x: 470, y: 42, w: 160, h: 20 };
  const freeCount = () => (window.FTLive && FTLive.player ? FTLive.player.freePacks || 0 : 0);
  let busy = false;
  function start(frogs) {
    st.frogs = frogs;
    st.mode = 'open'; st.t0 = st.now; st.page = 0; st.flipAt = {};
    parts.length = 0;
  }
  /** Live game: the server rolls the frogs; the cards open when they arrive. */
  function openLive(ctx, count, free) {
    if (busy) return;
    busy = true;
    FTLive.openPacks(count, free).then(start).catch(() => {}).finally(() => { busy = false; });
  }
  const inBox = (b, x, y) => x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h;
  function pageFrogs() { return st.frogs.slice(st.page * 5, st.page * 5 + 5); }
  function slotOf(ctx, i, count) {
    const r = lay(ctx).result;
    if (count === 1) return r.single;
    const w = 112, gap = 10, total = count * w + (count - 1) * gap, x0 = Math.round(320 - total / 2);
    return [x0 + i * (w + gap), r.slots[0][1]];
  }

  // ------------------------------------------------------------ module
  const mod = {
    async init(ctx, load) {
      const d = ctx.D.cards;
      R = d.rules;
      FTCrew.init(R);
      await FTCards.init(d, load, ctx.blinkOf);
      const im = await load(ctx.D.screens.recruit.images.pack);
      const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
      const g = c.getContext('2d'); g.drawImage(im, 0, 0);
      packMask = g.getImageData(0, 0, im.width, im.height).data;
      rayFrames = makeRays(ctx.W, ctx.H, 320, 162);
    },
    enter() { if (st.mode !== 'idle') { st.mode = 'idle'; st.frogs = []; } },

    hit(ctx, x, y) {
      const L = lay(ctx);
      if (st.mode === 'idle' && freeCount() && inBox(FREE_BTN, x, y)) return { key: 'free' };
      if (st.mode === 'idle') {
        for (const c of L.chips) if (inBox(c, x, y)) return { key: 'chip', n: c.n };
        if (inBox(L.open, x, y)) return { key: 'open' };
        const p = L.pack, b = { x: p.x, y: p.y, w: 80, h: 112 };
        if (inBox(b, x, y)) return { key: 'open' };
        return null;
      }
      if (st.mode === 'result') {
        const r = L.result;
        if (inBox(r.work, x, y)) return { key: 'work' };
        if (inBox(r.more, x, y)) return { key: 'more' };
        const pages = Math.ceil(st.frogs.length / 5);
        if (pages > 1 && st.page > 0 && inBox(r.left, x, y)) return { key: 'left' };
        if (pages > 1 && st.page < pages - 1 && inBox(r.right, x, y)) return { key: 'right' };
      }
      return null;
    },
    click(ctx, it) {
      if (it.key === 'chip') { st.n = it.n; return; }
      if (it.key === 'free') { openLive(ctx, Math.min(15, freeCount()), true); return; }
      if (it.key === 'open' && window.FTLive) {
        if (FTLive.wallet < st.n * R.packPrice) { ctx.toast('NOT ENOUGH $FROG', [230, 70, 90]); return; }
        openLive(ctx, st.n, false); return;
      }
      if (it.key === 'open') {
        const price = st.n * R.packPrice;
        if (ctx.wallet.value < price) { ctx.toast('NOT ENOUGH $FROG', [230, 70, 90]); return; }
        ctx.wallet.value -= price;
        st.frogs = Array.from({ length: st.n }, () => FTCrew.makeFrog());
        st.mode = 'open'; st.t0 = st.now; st.page = 0; st.flipAt = {};
        parts.length = 0;
        return;
      }
      if (it.key === 'work' && window.FTLive) {
        const total = st.frogs.length;
        FTCrew.autoSeat().then((seated) => {
          const left = total - seated;
          ctx.toast(seated === 0 ? 'ALL 15 DESKS ARE TAKEN: FROGS WAIT IN THE LOCKER ROOM'
            : left <= 0 ? (seated === 1 ? 'YOUR FROG IS HEADING TO ITS DESK' : `${seated} FROGS ARE HEADING TO THEIR DESKS`)
            : `${seated} SEATED, ${left} WAIT IN THE LOCKER ROOM`, [240, 190, 80]);
        });
        st.mode = 'idle'; st.frogs = []; return;
      }
      if (it.key === 'work') {
        FTCrew.add(st.frogs);
        const seated = FTCrew.autoSeat(st.frogs), left = st.frogs.length - seated;
        ctx.toast(left === 0 ? (seated === 1 ? 'YOUR FROG IS HEADING TO ITS DESK' : `${seated} FROGS ARE HEADING TO THEIR DESKS`)
          : seated === 0 ? 'ALL 15 DESKS ARE TAKEN: FROGS WAIT IN THE LOCKER ROOM' : `${seated} SEATED, ${left} WAIT IN THE LOCKER ROOM`, [240, 190, 80]);
        st.mode = 'idle'; st.frogs = []; return;
      }
      if (it.key === 'more') { FTCrew.add(st.frogs); st.mode = 'idle'; st.frogs = []; return; }
      if (it.key === 'left' || it.key === 'right') {
        st.page += it.key === 'left' ? -1 : 1;
        st.mode = 'flip'; st.t0 = st.now; st.flipAt = {};
      }
    },

    frame(ctx, t, dt) {
      st.now = t;
      const L = lay(ctx), img = ctx.img, g = ctx.g;
      const hov = ctx.hover && ctx.hover.kind === 'mod' ? ctx.hover.item : null;
      const down = ctx.press && ctx.press.kind === 'mod' ? ctx.press.item : null;
      const k = t - st.t0;

      if (st.mode === 'idle') {
        drawRays(ctx, t * 0.4, '#b88cff', 0.12);
        drawPack(ctx, t, L.pack.x, L.pack.y + (Math.sin(t * 2) > 0.3 ? -1 : 0), 0, hov && hov.key === 'open');
        // pack count: stacked packs behind for 5/10/15
        L.chips.forEach((c) => {
          const on = st.n === c.n, h = hov && hov.key === 'chip' && hov.n === c.n;
          const y = c.y + (down && down.key === 'chip' && down.n === c.n ? 1 : h && !on ? -1 : 0);
          g.drawImage(img['size-' + c.n + (on ? '-on' : '')], c.x, y);
        });
        const o = L.open, oh = hov && hov.key === 'open', od = down && down.key === 'open';
        const oy = o.y + (od ? 1 : oh ? -2 : 0);
        if (oh) for (let i = 1; i <= 3; i++) for (let xx = o.x - i; xx <= o.x + o.w - 1 + i; xx++) if ((xx + i) % 2) { ctx.px(xx, oy - i, '#ffe282', 0.5 / i); ctx.px(xx, oy + o.h - 1 + i, '#ffe282', 0.5 / i); }
        g.drawImage(img['open-' + st.n], o.x, oy);
        if (busy) ctx.gtext('ROLLING...', 320, o.y - 10, '#ffe282', 'body', { align: 'center' });
        const fc = freeCount();
        if (fc) {
          const b = FREE_BTN, fh = hov && hov.key === 'free', by = b.y + (fh ? -1 : 0);
          ctx.rect(b.x, by, b.x + b.w - 1, by + b.h - 1, '#141216');
          ctx.rect(b.x + 1, by + 1, b.x + b.w - 2, by + b.h - 2, Math.floor(t * 3) % 2 ? '#ffd66e' : '#ecba48');
          ctx.rect(b.x + 1, by + b.h - 3, b.x + b.w - 2, by + b.h - 2, '#aa7828');
          ctx.gtext(`OPEN ${Math.min(15, fc)} FREE ${fc === 1 ? 'PACK' : 'PACKS'}`, b.x + b.w / 2, by + 6, '#3a2408', 'head', { align: 'center', shadow: null });
        }
        // twinkling question marks over the silhouettes
        [50, 106, 162, 478, 534, 590].forEach((x, i) => {
          const s = (Math.sin(t * 2.2 + i * 1.3) + 1) / 2;
          if (s > 0.8) sparkle(ctx, x + 6, 196 + (i % 2) * 6, 1, '#fff', COL[i]);
        });
        return;
      }

      // dim the stage while the pack opens and the cards show
      const dim = st.mode === 'open' ? Math.min(0.66, k * 2) : 0.66;
      ctx.rect(0, 35, ctx.W - 1, ctx.H - 1, '#08050b', dim);

      if (st.mode === 'open') {
        const best = Math.max(...st.frogs.map((f) => f.rarity));
        const tTear = 1.45;
        if (k < tTear) {
          const lift = Math.min(1, k / 0.35);
          const amp = k > 0.35 ? 1 + 3 * Math.min(1, (k - 0.35) / 1.1) : 0;
          const sx = Math.round(Math.sin(k * 61) * amp), sy = Math.round(Math.cos(k * 47) * amp * 0.5);
          drawRays(ctx, t, '#b88cff', Math.min(0.35, Math.max(0, k - 0.3)));
          drawPack(ctx, t, L.pack.x + sx, L.pack.y - 12 * lift + sy, 0, false);
          for (let i = 0; i < Math.floor(6 * Math.min(1, k / 1.2)); i++) {
            const a = t * 3 + i * 1.05;
            sparkle(ctx, 320 + Math.cos(a) * (56 + i * 3), 162 + Math.sin(a) * 70, 1 + ((i + Math.floor(t * 8)) % 2));
          }
        } else {
          const kk = k - tTear;
          if (kk < 1 / 30 + 0.001 && !st.burst) { burst(320, 110, 46, ['#d8c0ff', '#ffffff', '#ffe282']); st.burst = true; }
          drawRays(ctx, t, COL[Math.max(2, best)], 0.32);
          if (kk < 0.6) {
            const e = 1 - Math.pow(1 - kk / 0.6, 3);
            drawPack(ctx, t, L.pack.x, L.pack.y - 12 + 280 * Math.pow(kk / 0.6, 2), L.pack.tear + 1, false);
            const tp = L.pack.tear + 1;
            ctx.g.globalAlpha = Math.max(0, 1 - kk / 0.6);
            ctx.g.drawImage(img.pack, 0, 0, 80, tp, L.pack.x + 36 * e, L.pack.y - 12 - 96 * e, 80, tp);
            ctx.g.globalAlpha = 1;
          }
          // card backs fly out to their slots
          const list = pageFrogs();
          list.forEach((f, i) => {
            const [tx, ty] = slotOf(ctx, i, list.length);
            const d = Math.min(1, Math.max(0, (kk - i * 0.06) / 0.45));
            const e2 = 1 - Math.pow(1 - d, 3);
            const x = 264 + (tx - 264) * e2, y = 100 + (ty - 100) * e2 - Math.sin(d * Math.PI) * 20;
            FTCards.draw(ctx, f, x, y, { flip: 0 });
          });
          if (kk < 0.25) ctx.rect(0, 0, ctx.W - 1, ctx.H - 1, '#ffffff', 0.85 * (1 - kk / 0.25));
          if (kk > 0.55) { st.mode = 'flip'; st.t0 = t; st.burst = false; }
          if (st.frogs.length === 1) ladder(ctx, t, -1);
        }
        stepParts(ctx, dt);
        return;
      }

      // flip and result
      const list = pageFrogs();
      const order = list.map((f, i) => i).sort((a, b) => list[a].rarity - list[b].rarity || a - b);
      const bestHere = Math.max(...list.map((f) => f.rarity));
      drawRays(ctx, t, COL[Math.max(1, bestHere)], 0.26);
      let allDone = true;
      order.forEach((i, n) => {
        const f = list[i];
        const start = 0.15 + n * (list.length === 1 ? 0 : 0.32) + (list.length === 1 ? 0.9 : 0);
        const p = Math.min(1, Math.max(0, (k - start) / 0.28));
        if (p < 1) allDone = false;
        if (p >= 0.5 && !st.flipAt[f.id]) {
          st.flipAt[f.id] = t;
          const [x, y] = slotOf(ctx, i, list.length);
          if (f.rarity >= 3) { burst(x + 56, y + 76, 60, [COL[f.rarity], '#ffffff', '#ffe282'], [2, 6], [0.7, 1.4]); st.flash = { t, c: COL[f.rarity] }; }
          else burst(x + 56, y + 76, 14, [COL[f.rarity], '#ffffff'], [1, 3], [0.3, 0.7]);
        }
        const [x, y] = slotOf(ctx, i, list.length);
        const lift = st.mode === 'result' && hov && hov.card === f.id ? -2 : 0;
        if (p >= 0.5 && f.rarity >= 2) {
          // rarity aura around revealed rare+ cards
          const c = RGB[f.rarity], r = Math.sin(t * 4 + i) * 0.5 + 0.5;
          for (let q = 1; q <= 3; q++) for (let xx = x - q; xx <= x + 111 + q; xx++) if ((xx + q + Math.floor(t * 8)) % 3 === 0) {
            ctx.px(xx, y - q + lift, `rgb(${c})`, (0.55 - q * 0.12) * (0.6 + r * 0.4));
            ctx.px(xx, y + 183 + q + lift, `rgb(${c})`, (0.55 - q * 0.12) * (0.6 + r * 0.4));
          }
          for (let q = 1; q <= 3; q++) for (let yy = y - q; yy <= y + 183 + q; yy++) if ((yy + q + Math.floor(t * 8)) % 3 === 0) {
            ctx.px(x - q, yy + lift, `rgb(${c})`, (0.55 - q * 0.12) * (0.6 + r * 0.4));
            ctx.px(x + 111 + q, yy + lift, `rgb(${c})`, (0.55 - q * 0.12) * (0.6 + r * 0.4));
          }
        }
        const blink = p >= 1 && ((t * 1000 + f.id * 397) % 3700) < 140;
        FTCards.draw(ctx, f, x, y + lift, { flip: p, blink });
        if (p >= 1 && f.rarity >= 4) for (let s = 0; s < 4; s++) {
          const a = t * 1.8 + s * 1.57 + i;
          const sv = (Math.sin(t * 5 + s * 2) + 1) / 2;
          if (sv > 0.4) sparkle(ctx, x + 56 + Math.cos(a) * 62, y + 88 + Math.sin(a) * 96, 1 + (sv > 0.8));
        }
      });
      if (st.flash) {
        const fk = t - st.flash.t;
        if (fk < 0.3) ctx.rect(0, 0, ctx.W - 1, ctx.H - 1, '#fff6e0', 0.7 * (1 - fk / 0.3)); else st.flash = null;
      }
      stepParts(ctx, dt);

      if (list.length === 1) ladder(ctx, t, st.mode === 'result' || k > 1.05 ? list[0].rarity : -1);
      if (allDone && st.mode === 'flip' && k > 0) { if (k > (list.length === 1 ? 1.5 : 0.4 + list.length * 0.32)) st.mode = 'result'; }

      // headline
      const f0 = st.frogs, best = Math.max(...f0.map((f) => f.rarity));
      if (st.mode === 'result' || (list.length === 1 && k > 1.2)) {
        // dark band behind the headline hides the NOW HIRING sign
        for (let yy = 36; yy <= 80; yy++) {
          const edge = yy > 74 ? (80 - yy) / 6 : 1;
          ctx.rect(0, yy, ctx.W - 1, yy, '#08050b', 0.85 * edge);
        }
        const title = f0.length === 1 ? 'YOU PULLED ' + (best === 0 || best === 1 || best === 2 ? 'A ' : best === 3 ? 'AN ' : 'A ') + KEYS[best].toUpperCase() + '!' : f0.length + ' NEW FROGS';
        ctx.gtext(title.replace('A EPIC', 'AN EPIC').replace('A UNCOMMON', 'AN UNCOMMON'), 320, 44, COL[best], 'title', { align: 'center', outline: '#141216' });
        if (f0.length > 1) ctx.gtext('BEST PULL: ' + KEYS[best].toUpperCase(), 320, 63, '#f2e7d4', 'body', { align: 'center' });
      }
      if (st.mode !== 'result') return;

      // buttons
      const r = L.result;
      for (const key of ['work', 'more']) {
        const b = r[key], h = hov && hov.key === key, d2 = down && down.key === key;
        const by = b.y + (d2 ? 1 : h ? -2 : 0);
        g.drawImage(img['btn-' + key], b.x, by);
      }
      const pages = Math.ceil(st.frogs.length / 5);
      if (pages > 1) {
        if (st.page > 0) g.drawImage(img['arrow-left'], r.left.x, r.left.y + (hov && hov.key === 'left' ? -1 : 0));
        if (st.page < pages - 1) g.drawImage(img['arrow-right'], r.right.x, r.right.y + (hov && hov.key === 'right' ? -1 : 0));
        ctx.gtext(`${st.page + 1} / ${pages}`, 320, 290, '#b0a498', 'body', { align: 'center' });
      }
      // skill tooltip
      if (st.tip) {
        const s = R.skills[st.tip];
        const line = s.name.toUpperCase() + ': ' + s.description;
        const w = ctx.gwidth(line, 'body') + 14, x0 = Math.round(320 - w / 2), y0 = st.frogs.length === 1 ? 289 : 272;
        ctx.rect(x0, y0, x0 + w, y0 + 14, '#141216');
        ctx.rect(x0 + 1, y0 + 1, x0 + w - 1, y0 + 13, '#ecba48');
        ctx.rect(x0 + 2, y0 + 2, x0 + w - 2, y0 + 12, '#1e1a24');
        ctx.gtext(line, x0 + 7, y0 + 4, '#f2e7d4', 'body', { shadow: null });
      }
    },
  };

  /** Rarity ladder under a single card: rolls, then stops on the pulled rarity. */
  function ladder(ctx, t, stopAt) {
    const names = KEYS.map((k) => k.toUpperCase());
    const ws = names.map((n) => ctx.gwidth(n, 'body') + 12), gap = 4;
    const total = ws.reduce((a, b) => a + b, 0) + gap * 5;
    let x = Math.round(320 - total / 2);
    const y = 272;
    const hi = stopAt >= 0 ? stopAt : Math.floor(t * 14) % 6;
    names.forEach((n, i) => {
      const on = i === hi, c = RGB[i];
      ctx.rect(x, y, x + ws[i], y + 14, '#141216');
      ctx.rect(x + 1, y + 1, x + ws[i] - 1, y + 13, on ? `rgb(${c})` : `rgb(${c.map((v) => v * 0.45 | 0)})`);
      ctx.rect(x + 2, y + 2, x + ws[i] - 2, y + 12, on ? `rgb(${c.map((v) => v * 0.55 | 0)})` : '#16121a');
      ctx.gtext(n, x + 6, y + 4, on ? '#ffffff' : `rgb(${c.map((v) => v * 0.8 | 0)})`, 'body', { shadow: null });
      x += ws[i] + gap;
    });
  }

  /** The pack with a moving foil glint. Rows above `fromRow` are skipped (the torn top). */
  function drawPack(ctx, t, x, y, fromRow, hot) {
    const img = ctx.img.pack;
    x = Math.round(x); y = Math.round(y);
    ctx.g.drawImage(img, 0, fromRow, 80, 112 - fromRow, x, y + fromRow, 80, 112 - fromRow);
    const band = ((t * 0.7) % 1.6) * 200 - 60;
    for (let yy = fromRow; yy < 112; yy++) for (let xx = 0; xx < 80; xx++) {
      const d = xx + yy * 0.6 - band;
      if (d < 0 || d > 7) continue;
      if (!packMask[(yy * 80 + xx) * 4 + 3]) continue;
      ctx.px(x + xx, y + yy, '#ffffff', d < 3 ? 0.35 : 0.18);
    }
    if (hot) for (let q = 1; q <= 3; q++) for (let xx = x - q; xx <= x + 79 + q; xx++) if ((xx + q) % 2) { ctx.px(xx, y - q, '#d2aaff', 0.5 / q); ctx.px(xx, y + 111 + q, '#d2aaff', 0.5 / q); }
  }

  /** Hover over a skill icon of a revealed card shows its text. */
  mod.hover = function (ctx, x, y) {
    st.tip = null;
    if (st.mode !== 'result') return;
    const list = pageFrogs();
    list.forEach((f, i) => {
      const [cx, cy] = slotOf(ctx, i, list.length);
      const s = FTCards.skillAt(f, cx, cy, x, y);
      if (s) st.tip = s;
    });
  };

  window.FTScreens = window.FTScreens || {};
  window.FTScreens.recruit = mod;
})();
