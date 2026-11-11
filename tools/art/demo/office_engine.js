/* Frog Traders office renderer (shared by all three offices).
 * Composes albedo layers, lights them per pixel with dithered banding,
 * then draws self-lit screens, signs and particles on top.
 * Usage: const scene = OfficeScene.create(data, canvas, tipElement); scene.stop();
 * Embedded: OfficeScene.create(data, offscreenCanvas, null, { embed: true }) returns step(dt, t), setHover(i), ready.
 * frog.state: 'work' trades, 'ready' sits with the screen asleep, 'sleep' dozes.
 * data = { layout, images: {name: dataURI}, frogs: [...] }. layout.theme picks the
 * room flavour; optional layout keys switch room features on.
 */
(function () {
  'use strict';
  const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map((v) => v / 16);
  const LEVELS = 9;

  // ------------------------------------------------------------ 3x5 font
  const F = {
    A: '.#.|#.#|###|#.#|#.#', B: '##.|#.#|##.|#.#|##.', C: '.##|#..|#..|#..|.##', D: '##.|#.#|#.#|#.#|##.',
    E: '###|#..|##.|#..|###', F: '###|#..|##.|#..|#..', G: '.##|#..|#.#|#.#|.##', H: '#.#|#.#|###|#.#|#.#',
    I: '###|.#.|.#.|.#.|###', J: '..#|..#|..#|#.#|.#.', K: '#.#|#.#|##.|#.#|#.#', L: '#..|#..|#..|#..|###',
    M: '#.#|###|###|#.#|#.#', N: '##.|#.#|#.#|#.#|#.#', O: '.#.|#.#|#.#|#.#|.#.', P: '##.|#.#|##.|#..|#..',
    Q: '.#.|#.#|#.#|##.|.##', R: '##.|#.#|##.|#.#|#.#', S: '.##|#..|.#.|..#|##.', T: '###|.#.|.#.|.#.|.#.',
    U: '#.#|#.#|#.#|#.#|###', V: '#.#|#.#|#.#|#.#|.#.', W: '#.#|#.#|###|###|#.#', X: '#.#|#.#|.#.|#.#|#.#',
    Y: '#.#|#.#|.#.|.#.|.#.', Z: '###|..#|.#.|#..|###', 0: '###|#.#|#.#|#.#|###', 1: '.#.|##.|.#.|.#.|###',
    2: '##.|..#|.#.|#..|###', 3: '##.|..#|.#.|..#|##.', 4: '#.#|#.#|###|..#|..#', 5: '###|#..|##.|..#|##.',
    6: '.##|#..|###|#.#|###', 7: '###|..#|.#.|.#.|.#.', 8: '###|#.#|###|#.#|###', 9: '###|#.#|###|..#|##.',
    $: '.#.|###|##.|.##|###', '%': '#.#|..#|.#.|#..|#.#', '+': '...|.#.|###|.#.|...', '-': '...|...|###|...|...',
    '.': '...|...|...|...|.#.', ',': '...|...|...|.#.|#..', '!': '.#.|.#.|.#.|...|.#.', ' ': '..|..|..|..|..',
    '/': '..#|..#|.#.|#..|#..', ':': '...|.#.|...|.#.|...', '^': '.#.|###|...|...|...', 'v': '...|...|...|###|.#.',
    '&': '.#.|#.#|.#.|#.#|.##',
  };
  const glyphs = {};
  for (const k in F) glyphs[k] = F[k].split('|').map((r) => [...r].map((c) => c === '#'));
  const BLANK = [false, false, false, false, false];
  function textCols(s) {
    const cols = [];
    [...s].forEach((ch, i) => {
      const g = glyphs[ch] || glyphs[ch.toUpperCase()] || glyphs[' '];
      for (let x = 0; x < g[0].length; x++) cols.push(g.map((r) => r[x]));
      if (i < s.length - 1) cols.push(BLANK);
    });
    return cols;
  }
  const textWidth = (s) => textCols(s).length;
  const rnd = (a, b) => a + Math.random() * (b - a);
  const pick = (a) => a[(Math.random() * a.length) | 0];

  function loadImage(src) {
    return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
  }
  function toData(img) {
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const g = c.getContext('2d');
    g.drawImage(img, 0, 0);
    return g.getImageData(0, 0, img.width, img.height);
  }

  // blink frame: close the eye whites with a lid and a lash line
  function makeBlink(sp) {
    const { width: w, height: h, data } = sp;
    const out = new ImageData(new Uint8ClampedArray(data), w, h);
    const isWhite = (i) => data[i * 4 + 3] && data[i * 4] > 196 && data[i * 4 + 1] > 190 && data[i * 4 + 2] > 160;
    const seen = new Uint8Array(w * h);
    const limit = Math.floor(h * 0.45);
    for (let y = 0; y < limit; y++) for (let x = 0; x < w; x++) {
      const s = y * w + x;
      if (seen[s] || !isWhite(s)) continue;
      const stack = [s], comp = [];
      seen[s] = 1;
      while (stack.length) {
        const p = stack.pop(); comp.push(p);
        const px = p % w, py = (p / w) | 0;
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const nx = px + dx, ny = py + dy;
          if (nx < 0 || ny < 0 || nx >= w || ny >= limit) continue;
          const q = ny * w + nx;
          if (!seen[q] && isWhite(q)) { seen[q] = 1; stack.push(q); }
        }
      }
      if (comp.length < 5) continue;
      let x0 = w, x1 = 0, y0 = h, y1 = 0;
      for (const p of comp) { const px = p % w, py = (p / w) | 0; x0 = Math.min(x0, px); x1 = Math.max(x1, px); y0 = Math.min(y0, py); y1 = Math.max(y1, py); }
      let lid = [116, 146, 78];
      for (let yy = y0 - 2; yy >= Math.max(0, y0 - 5); yy--) {
        const q = (yy * w + ((x0 + x1) >> 1)) * 4;
        if (data[q + 3] && data[q] + data[q + 1] + data[q + 2] > 150) { lid = [data[q], data[q + 1], data[q + 2]]; break; }
      }
      for (let yy = y0; yy <= y1; yy++) for (let xx = x0; xx <= x1; xx++) {
        const q = (yy * w + xx) * 4;
        if (!data[q + 3]) continue;
        const lum = data[q] + data[q + 1] + data[q + 2];
        if (lum > 480 || lum < 110) { out.data[q] = lid[0]; out.data[q + 1] = lid[1]; out.data[q + 2] = lid[2]; }
      }
      const ly = Math.min(y1, y0 + Math.round((y1 - y0) * 0.65));
      for (let xx = x0; xx <= x1; xx++) {
        const q = (ly * w + xx) * 4;
        if (data[q + 3]) { out.data[q] = 20; out.data[q + 1] = 18; out.data[q + 2] = 22; }
      }
    }
    return out;
  }

  function newChart(n, start, drift = 0.5) {
    const c = []; let p = start;
    for (let i = 0; i < n; i++) { const o = p; p = Math.max(5, p + rnd(-3, 3 + drift)); c.push({ o, c: p, h: Math.max(o, p) + rnd(0, 2), l: Math.min(o, p) - rnd(0, 2) }); }
    return c;
  }

  // ============================================================ scene
  function create(D, canvas, tip, opts = {}) {
    const embed = !!opts.embed;
    const L = D.layout, T = L.theme;
    const W = L.size[0], H = L.size[1], N = W * H;
    const ctx = canvas.getContext('2d');
    canvas.width = W; canvas.height = H;
    const out = ctx.createImageData(W, H);
    const alb = new Uint8ClampedArray(N * 4);
    const light = new Float32Array(N * 3);
    let back, front, frontIdx, emissive, neonImg, bgAlpha;
    const frogSprites = {};
    let bossSprite = null, showBoss = !!D.showBoss;
    const lights = [], byId = {};
    let running = true, raf = 0, loaded = false, embAcc = 0;

    function addLight(o) {
      const r = o.r;
      const x0 = Math.max(0, Math.floor(o.x - r)), x1 = Math.min(W - 1, Math.ceil(o.x + r));
      const y0 = Math.max(0, Math.floor(o.y - (o.cone ? r * 0.25 : r))), y1 = Math.min(H - 1, Math.ceil(o.y + r));
      const bw = x1 - x0 + 1, bh = y1 - y0 + 1;
      const m = new Float32Array(bw * bh);
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
        const dx = x - o.x, dy = y - o.y, d = Math.sqrt(dx * dx + dy * dy);
        let f = Math.max(0, 1 - d / r); f = f * f * o.i;
        if (o.cone) { const c = Math.max(0, Math.min(1, dy / (d + 1e-6))); f *= 0.22 + 0.78 * Math.pow(c, 0.7); }
        if (o.stripes) { const [per, duty, sy] = o.stripes; if (((y - sy) % per + per) % per >= duty) f *= 0.25; }
        if (o.box) { const b = o.box; if (x < b[0] || x > b[2] || y < b[1] || y > b[3]) f *= 0.15; }
        m[(y - y0) * bw + (x - x0)] = f;
      }
      const l = Object.assign({ x0, y0, bw, bh, m, k: 1 }, o, { col: o.col.slice(), base: o.col.slice() });
      lights.push(l);
      if (o.id) byId[o.id] = l;
      return l;
    }

    // ---------------------------------------------------------- state
    const coins = T.coins || ['$FROG'];
    const desks = L.desks.map((d, i) => Object.assign({}, d, {
      frog: D.frogs[i] || null, pos: d.frog, idx: i,
      chart: newChart(9, 30 + i * 4), coin: coins[i % coins.length],
      nextCandle: rnd(0.6, 1.4), event: null, eventT: 0,
      blinkT: rnd(1, 5), blinking: 0, breathPhase: rnd(0, 6.28),
      saver: { x: 4, y: 4, vx: 0.35, vy: 0.22 },
      book: Array.from({ length: 5 }, () => rnd(3, 10)),
      bond: rnd(10, 70),
    }));
    const tv = { chart: newChart(20, 60), nextCandle: 1, mc: rnd(20, 60), bond: rnd(20, 60), state: null, stateT: 0, coin: pick(coins) };
    let neonOn = true, neonTimer = rnd(3, 7), neonSeq = [];
    let flash = 0, flashTimer = rnd(10, 22), lightning = 0;
    const rain = [], steam = [], zs = [], dust = [];
    let hover = -2;
    let tickerOffset = 0, tickerCols = [], tickerColors = [];
    let alarm = 0, rugCount = T.rugStart || 17, countdown = 42;
    const launches = [];
    const flap = [];
    let tapeOffset = 0;

    function rugEvent() {
      rugCount++;
      alarm = 3.2;
    }

    function buildTicker() {
      const parts = [];
      const push = (t, col) => parts.push({ t, col });
      for (let i = 0; i < 10; i++) {
        if (T.tickerStyle === 'stocks') {
          const s = pick(T.stocks);
          const ch = rnd(-1.8, 2.2);
          push(s[0] + ' ', T.tickerSym);
          push(s[1].toFixed(2) + ' ', [220, 230, 220]);
          push((ch >= 0 ? '^' : 'v') + Math.abs(ch).toFixed(2) + '%', ch >= 0 ? [110, 240, 130] : [255, 96, 86]);
        } else if (T.tickerStyle === 'launch') {
          const c = pick(coins);
          const r = Math.random();
          push('NEW ' + c + ' ', T.tickerSym);
          if (r < 0.25) push('RUGGED', [255, 70, 70]);
          else if (r < 0.45) push('BONDED', [255, 214, 90]);
          else push('MC ' + rnd(4, 90).toFixed(1) + 'K', [190, 150, 255]);
        } else {
          const c = coins[i % coins.length];
          const ch = rnd(-30, 140);
          push(c + ' ', T.tickerSym);
          push((ch >= 0 ? '+' : '') + ch.toFixed(1) + '%', ch >= 0 ? [110, 240, 120] : [255, 90, 80]);
        }
        push('   ', [0, 0, 0]);
      }
      parts.forEach((p) => {
        textCols(p.t).forEach((c) => { tickerCols.push(c); tickerColors.push(p.col); });
        tickerCols.push(BLANK); tickerColors.push(p.col);
      });
    }

    function newLaunch(row) {
      return { row, coin: pick(coins), p: rnd(2, 25), v: rnd(4, 14), state: null, t: 0 };
    }

    function blend(dst, src) {
      for (let i = 0; i < src.length; i += 4) {
        const a = src[i + 3];
        if (!a) continue;
        const k = a / 255;
        dst[i] = dst[i] * (1 - k) + src[i] * k; dst[i + 1] = dst[i + 1] * (1 - k) + src[i + 1] * k;
        dst[i + 2] = dst[i + 2] * (1 - k) + src[i + 2] * k; dst[i + 3] = Math.max(dst[i + 3], a);
      }
    }
    function blitSprite(img, x, y, clipY) {
      const { width: w, height: h, data } = img;
      for (let j = 0; j < h; j++) {
        const Y = y + j; if (Y < 0 || Y >= H || (clipY !== undefined && Y > clipY)) continue;
        for (let i = 0; i < w; i++) {
          const X = x + i; if (X < 0 || X >= W) continue;
          const s = (j * w + i) * 4; if (!data[s + 3]) continue;
          const d = (Y * W + X) * 4;
          alb[d] = data[s]; alb[d + 1] = data[s + 1]; alb[d + 2] = data[s + 2]; alb[d + 3] = 255;
        }
      }
    }
    function apx(x, y, c) { // albedo pixel (gets lit)
      x |= 0; y |= 0; if (x < 0 || y < 0 || x >= W || y >= H) return;
      const p = (y * W + x) * 4; alb[p] = c[0]; alb[p + 1] = c[1]; alb[p + 2] = c[2];
    }
    function epx(x, y, r, g, b, a) { // emissive pixel (after lighting)
      x |= 0; y |= 0; if (x < 0 || y < 0 || x >= W || y >= H) return;
      const d = (y * W + x) * 4, o = out.data;
      if (a === undefined || a >= 1) { o[d] = r; o[d + 1] = g; o[d + 2] = b; return; }
      o[d] = o[d] + (r - o[d]) * a; o[d + 1] = o[d + 1] + (g - o[d + 1]) * a; o[d + 2] = o[d + 2] + (b - o[d + 2]) * a;
    }
    function erect(x0, y0, x1, y1, r, g, b, a) { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) epx(x, y, r, g, b, a); }
    function etext(s, x, y, col, a, scale = 1) {
      textCols(s).forEach((c, i) => c.forEach((on, j) => {
        if (!on) return;
        for (let u = 0; u < scale; u++) for (let v = 0; v < scale; v++) epx(x + i * scale + u, y + j * scale + v, col[0], col[1], col[2], a);
      }));
    }

    // ---------------------------------------------------------- init
    async function init() {
      const imgs = {};
      await Promise.all(Object.entries(D.images).map(async ([k, v]) => { imgs[k] = toData(await loadImage(v)); }));
      back = new Uint8ClampedArray(imgs.bg.data);
      blend(back, imgs.chairs.data);
      front = new Uint8ClampedArray(imgs.bossdesk.data);
      blend(front, imgs.desks.data);
      const idx = [];
      for (let i = 0; i < N; i++) if (front[i * 4 + 3]) idx.push(i);
      frontIdx = new Uint32Array(idx);
      emissive = imgs.emissive.data; neonImg = imgs.neon.data; bgAlpha = imgs.bg.data;
      if (imgs.boss) bossSprite = imgs.boss;
      for (const k of Object.keys(imgs)) if (k.startsWith('frog-')) frogSprites[k.slice(5)] = { open: imgs[k], blink: makeBlink(imgs[k]) };

      L.lights.forEach(addLight);
      desks.forEach((d) => {
        const s = d.screen;
        if (!s) return;
        d.light = addLight({ x: (s[0] + s[2]) / 2, y: (s[1] + s[3]) / 2, r: 54, col: T.screenLight, i: 0.72 });
        if (d.screen2) { const t = d.screen2; d.light2 = addLight({ x: (t[0] + t[2]) / 2, y: (t[1] + t[3]) / 2, r: 34, col: [0.5, 0.8, 1.0], i: 0.4 }); }
        d.lamps.forEach(([x, y]) => addLight({ x, y: y + 8, r: 62, col: T.deskLamp, i: 0.9, cone: true, kind: 'desklamp' }));
      });
      if (L.window && T.rain) {
        const w = L.window.rect;
        for (let i = 0; i < 70; i++) rain.push({ x: rnd(w[0], w[2]), y: rnd(w[1], w[3]), v: rnd(2.2, 3.6) });
      }
      const lampLights = lights.filter((l) => l.kind === 'lamp');
      if (T.cones) for (let i = 0; i < 26; i++) dust.push({ lamp: i % Math.max(1, lampLights.length), t: Math.random(), s: rnd(-1, 1), v: rnd(0.002, 0.006) });
      if (L.launchpad) for (let r = 0; r < L.launchpad.rows; r++) launches.push(newLaunch(r));
      if (T.tv === 'flap') T.stocks.slice(0, L.tv.rows || 5).forEach((s) => flap.push({ sym: s[0], val: s[1], ch: rnd(-1.5, 1.5), shown: '', target: '', flipT: 0 }));
      buildTicker();
      loaded = true;
      if (embed) return;
      canvas.addEventListener('mousemove', onMove);
      canvas.addEventListener('pointerdown', onMove);
      canvas.addEventListener('click', onClick);
      canvas.addEventListener('mouseleave', onLeave);
      raf = requestAnimationFrame(loop);
    }
    function onClick(e) { onMove(e); if (hover === -1) { tip.hidden = true; window.dispatchEvent(new CustomEvent('office:boss-seat')); } }
    function onLeave() { hover = -2; tip.hidden = true; }

    // ---------------------------------------------------------- update
    function update(dt, t) {
      neonTimer -= dt;
      if (neonTimer <= 0 && !neonSeq.length) {
        neonSeq = Math.random() < 0.4 ? [[0.09, false]] : [[0.07, false], [0.05, true], [0.12, false], [0.04, true], [0.05, false]];
        neonTimer = rnd(4, 9);
      }
      if (neonSeq.length) {
        neonSeq[0][0] -= dt; neonOn = neonSeq[0][1];
        if (neonSeq[0][0] <= 0) { neonSeq.shift(); if (!neonSeq.length) neonOn = true; }
      }
      if (byId.neon) byId.neon.k = neonOn ? 0.95 + 0.05 * Math.sin(t * 50) : 0.08;
      if (T.rain) {
        flashTimer -= dt;
        if (flashTimer <= 0) { flash = 0.5; flashTimer = rnd(14, 30); }
        lightning = flash > 0 ? (flash > 0.38 || (flash < 0.24 && flash > 0.14) ? 1 : 0) : 0;
        flash = Math.max(0, flash - dt);
        if (byId.window) byId.window.k = 1 + lightning * 2.4;
      }
      lights.forEach((l) => { if (l.kind === 'lamp') l.k = 0.97 + 0.03 * Math.sin(t * 7 + l.x); });
      if (byId.plus) byId.plus.k = 0.75 + 0.35 * Math.sin(t * 3);
      // desks
      desks.forEach((d) => {
        d.nextCandle -= dt;
        const last = d.chart[d.chart.length - 1];
        const working = d.frog && d.frog.state === 'work';
        if (working) {
          last.c = Math.max(4, last.c + rnd(-0.6, 0.7));
          last.h = Math.max(last.h, last.c); last.l = Math.min(last.l, last.c);
          d.bond = Math.min(100, d.bond + dt * rnd(0, 3));
          if (d.nextCandle <= 0) {
            d.chart.push({ o: last.c, c: last.c, h: last.c, l: last.c });
            if (d.chart.length > 9) d.chart.shift();
            d.nextCandle = rnd(0.7, 1.5);
            if (!d.event && Math.random() < (T.screen === 'pump' ? 0.07 : T.screen === 'crt' ? 0.03 : 0.05)) {
              const r = Math.random();
              if (T.screen === 'pump') d.event = r < 0.55 ? 'RUG' : 'KING';
              else if (T.screen === 'crt') d.event = r < 0.5 ? 'BUY' : 'SELL';
              else d.event = r < 0.6 ? 'PUMP' : 'RUG';
              d.eventT = 1.4;
              if (d.event === 'RUG' && L.counter) rugEvent();
              if (d.event === 'RUG' || d.event === 'KING') d.bond = rnd(5, 30);
            }
          }
          if (d.bond >= 100) d.bond = rnd(5, 20);
        }
        if (d.event) { d.eventT -= dt; if (d.eventT <= 0) d.event = null; }
        if (!d.screen) {
          d.blinkT -= dt;
          if (d.blinkT <= 0) { d.blinking = 0.14; d.blinkT = rnd(2.5, 6); }
          d.blinking = Math.max(0, d.blinking - dt);
          if (d.frog && d.frog.state === 'sleep' && Math.random() < 0.012) zs.push({ x: d.pos[0] + 14, y: d.pos[1] - 44, a: 1 });
          return;
        }
        const s = d.saver;
        s.x += s.vx; s.y += s.vy;
        const sw = d.screen[2] - d.screen[0] - 3, sh = d.screen[3] - d.screen[1] - 3;
        if (s.x < 0 || s.x > sw) s.vx *= -1;
        if (s.y < 0 || s.y > sh) s.vy *= -1;
        d.book = d.book.map((v) => Math.max(1, Math.min(10, v + rnd(-1, 1))));
        if (!working) { d.light.col = [0.3, 0.5, 0.9]; d.light.k = 0.35; }
        else if (d.event === 'RUG' || d.event === 'SELL') { d.light.col = [1.0, 0.25, 0.2]; d.light.k = 1.25; }
        else if (d.event === 'PUMP' || d.event === 'BUY') { d.light.col = [0.4, 1.0, 0.45]; d.light.k = 1.3; }
        else if (d.event === 'KING') { d.light.col = [1.0, 0.85, 0.3]; d.light.k = 1.3; }
        else { d.light.col = T.screenLight; d.light.k = 0.92 + 0.08 * Math.sin(t * 3 + d.idx); }
        d.blinkT -= dt;
        if (d.blinkT <= 0) { d.blinking = 0.14; d.blinkT = rnd(2.5, 6); }
        d.blinking = Math.max(0, d.blinking - dt);
        d.steam.forEach(([x, y]) => { if (Math.random() < 0.08) steam.push({ x: x + rnd(-1, 1), y, a: 0.55, ph: rnd(0, 6) }); });
        if (d.frog && d.frog.state === 'sleep' && Math.random() < 0.012) zs.push({ x: d.pos[0] + 14, y: d.pos[1] - 44, a: 1 });
      });
      updateCasino(dt, t);
      // big screen
      if (T.tv === 'none') return finishUpdate(dt, t);
      tv.nextCandle -= dt;
      const tl = tv.chart[tv.chart.length - 1];
      if (T.tv === 'pump') {
        if (tv.state) { tv.stateT -= dt; if (tv.stateT <= 0) { tv.state = null; tv.chart = newChart(20, 20, 1.5); tv.mc = rnd(4, 12); tv.bond = rnd(2, 10); tv.coin = pick(coins); } }
        else {
          tl.c = Math.max(4, tl.c + rnd(-0.5, 1.3)); tl.h = Math.max(tl.h, tl.c); tl.l = Math.min(tl.l, tl.c);
          tv.mc += dt * rnd(0.2, 2.4); tv.bond = Math.min(100, tv.bond + dt * rnd(0.5, 3));
          if (tv.nextCandle <= 0) { tv.chart.push({ o: tl.c, c: tl.c, h: tl.c, l: tl.c }); if (tv.chart.length > 20) tv.chart.shift(); tv.nextCandle = rnd(0.6, 1.2); }
          if (tv.bond >= 100) { tv.state = 'BONDED'; tv.stateT = 2.2; }
          else if (Math.random() < 0.0025) {
            tv.state = 'RUGGED'; tv.stateT = 2.4;
            for (let k = 0; k < 3; k++) { const c = tv.chart[tv.chart.length - 1].c; tv.chart.push({ o: c, c: c * 0.35, h: c, l: c * 0.3 }); tv.chart.shift(); }
            if (L.counter) rugEvent();
          }
        }
        if (byId.tv) byId.tv.col = tv.state === 'RUGGED' ? [1, 0.25, 0.25] : tv.state === 'BONDED' ? [1, 0.85, 0.3] : T.tvLight || [0.8, 0.4, 1.0];
      } else if (T.tv === 'flap') {
        flap.forEach((f) => {
          if (f.flipT > 0) { f.flipT -= dt; if (f.flipT <= 0) f.shown = f.target; }
          else if (Math.random() < 0.006) {
            f.ch += rnd(-0.4, 0.4); f.val *= 1 + f.ch / 1000; f.flipT = 0.45;
          }
          f.target = f.val.toFixed(2);
          if (!f.shown) f.shown = f.target;
        });
      } else {
        tl.c = Math.max(8, tl.c + rnd(-0.9, 1.0)); tl.h = Math.max(tl.h, tl.c); tl.l = Math.min(tl.l, tl.c);
        if (tv.nextCandle <= 0) { tv.chart.push({ o: tl.c, c: tl.c, h: tl.c, l: tl.c }); if (tv.chart.length > 20) tv.chart.shift(); tv.nextCandle = rnd(0.9, 1.6); }
        if (byId.tv) byId.tv.col = tl.c >= tl.o ? [0.35, 1.0, 0.55] : [1.0, 0.35, 0.3];
      }
      finishUpdate(dt, t);
    }
    function finishUpdate(dt, t) {
      // launchpad board
      launches.forEach((l, i) => {
        if (l.state) { l.t -= dt; if (l.t <= 0) launches[i] = newLaunch(l.row); return; }
        l.p += dt * l.v * rnd(0.2, 1.4);
        if (l.p >= 100) { l.p = 100; l.state = 'BONDED'; l.t = 1.6; }
        else if (Math.random() < 0.0018) { l.state = 'RUGGED'; l.t = 1.6; rugEvent(); }
      });
      if (L.countdown) { countdown -= dt; if (countdown <= 0) countdown = 60 + rnd(0, 30); }
      // siren
      alarm = Math.max(0, alarm - dt);
      if (byId.siren) byId.siren.k = alarm > 0 ? 0.6 + 0.6 * Math.abs(Math.sin(t * 9)) : 0;
      // particles
      for (const p of steam) { p.y -= 0.22; p.x += Math.sin(p.ph + p.y * 0.4) * 0.12; p.a -= 0.006; }
      for (const p of zs) { p.y -= 0.12; p.x += 0.05; p.a -= 0.004; }
      prune(steam); prune(zs);
      if (L.window && T.rain) for (const r of rain) { r.y += r.v; r.x -= r.v * 0.25; const w = L.window.rect; if (r.y > w[3]) { r.y = w[1]; r.x = rnd(w[0], w[2] + 10); } }
      for (const p of dust) { p.t += p.v; if (p.t > 1) p.t = 0; }
      tickerOffset += dt * 14;
      tapeOffset += dt * 6;
    }
    function prune(a) { for (let i = a.length - 1; i >= 0; i--) if (a[i].a <= 0) a.splice(i, 1); }

    // ---------------------------------------------------------- render
    function render(t) {
      alb.set(back);
      drawClocks();
      drawTape();
      if (bossSprite && showBoss && L.boss) {
        // the boss sits in the big chair, behind the boss desk
        const [bx] = L.boss.boss_anchor;
        const by = L.boss.desk_top + (D.bossSink || 6) - bossSprite.height + (Math.sin(t * 1.3) > 0.7 ? -1 : 0);
        blitSprite(bossSprite, bx - (bossSprite.width >> 1), by);
      }
      desks.forEach((d) => {
        if (!d.frog) return;
        const sp = frogSprites[d.frog.rarity];
        const sleeping = d.frog.state === 'sleep';
        const img = sleeping || d.blinking > 0 ? sp.blink : sp.open;
        const bob = sleeping ? 3 : (Math.sin(t * 2.1 + d.breathPhase) > 0.55 ? -1 : 0);
        blitSprite(img, d.pos[0] - (img.width >> 1), d.pos[1] - 50 + bob, d.clip);
      });
      for (let n = 0; n < frontIdx.length; n++) {
        const i = frontIdx[n] * 4;
        const a = front[i + 3];
        if (a === 255) { alb[i] = front[i]; alb[i + 1] = front[i + 1]; alb[i + 2] = front[i + 2]; alb[i + 3] = 255; }
        else { const k = a / 255; alb[i] += (front[i] - alb[i]) * k; alb[i + 1] += (front[i + 1] - alb[i + 1]) * k; alb[i + 2] += (front[i + 2] - alb[i + 2]) * k; }
      }
      drawRoulette();
      const amb = T.ambient;
      for (let i = 0; i < N; i++) { light[i * 3] = amb[0]; light[i * 3 + 1] = amb[1]; light[i * 3 + 2] = amb[2]; }
      for (const l of lights) {
        const k = l.k; if (k <= 0) continue;
        const cr = l.col[0] * k, cg = l.col[1] * k, cb = l.col[2] * k;
        for (let y = 0; y < l.bh; y++) {
          let li = ((l.y0 + y) * W + l.x0) * 3, mi = y * l.bw;
          for (let x = 0; x < l.bw; x++, li += 3, mi++) {
            const f = l.m[mi]; if (f <= 0.0005) continue;
            light[li] += cr * f; light[li + 1] += cg * f; light[li + 2] += cb * f;
          }
        }
      }
      const o = out.data;
      for (let y = 0; y < H; y++) {
        const brow = (y & 3) * 4;
        for (let x = 0; x < W; x++) {
          const i = y * W + x, p = i * 4, li = i * 3;
          const th = 0.5 + (BAYER[brow + (x & 3)] - 0.5) * 0.45;
          o[p] = alb[p] * (Math.floor(Math.min(light[li], 1.3) * LEVELS + th) / LEVELS);
          o[p + 1] = alb[p + 1] * (Math.floor(Math.min(light[li + 1], 1.3) * LEVELS + th) / LEVELS);
          o[p + 2] = alb[p + 2] * (Math.floor(Math.min(light[li + 2], 1.3) * LEVELS + th) / LEVELS);
          o[p + 3] = 255;
        }
      }
      if (T.cones) drawCones(t);
      for (let i = 0; i < N; i++) {
        const p = i * 4; if (!emissive[p + 3]) continue;
        if (lightning && insideWindow(i)) { o[p] = Math.min(255, emissive[p] + 150); o[p + 1] = Math.min(255, emissive[p + 1] + 150); o[p + 2] = Math.min(255, emissive[p + 2] + 170); continue; }
        const a = emissive[p + 3] / 255;
        o[p] += (emissive[p] - o[p]) * a; o[p + 1] += (emissive[p + 1] - o[p + 1]) * a; o[p + 2] += (emissive[p + 2] - o[p + 2]) * a;
      }
      if (T.rain) drawRain();
      if (neonOn) drawNeon();
      desks.forEach((d) => { if (d.screen) drawScreen(d); });
      if (T.tv === 'pump') drawPumpTV(t); else if (T.tv === 'flap') drawFlap(t); else if (T.tv !== 'none') drawChartTV(t);
      drawCasino(t);
      drawTicker();
      drawLeds(t);
      drawStrips(t);
      drawLaunchpad(t);
      drawCounter(t);
      drawCountdown(t);
      drawSiren(t);
      drawPlus(t);
      for (const p of steam) epx(p.x, p.y, 230, 228, 222, p.a * 0.6);
      for (const p of zs) etext('Z', p.x, p.y, [210, 220, 255], Math.max(0, p.a));
      if (hover >= -1) drawHover();
      ctx.putImageData(out, 0, 0);
    }

    // ---------------------------------------------------------- casino
    const SYMS = [[220, 40, 50], [250, 196, 60], [60, 150, 230], [80, 190, 90], [160, 70, 200]];
    const slotState = (L.slots || []).map(() => ({ spin: 0, wait: rnd(1, 6), reels: [0, 1, 2].map(() => (Math.random() * SYMS.length) | 0), off: 0, win: 0 }));
    const jack = { v: 1284000 + Math.floor(Math.random() * 90000) };
    const wheel = { a: 0, v: 1.6, ball: 0, bv: -3.2 };
    function updateCasino(dt, t) {
      slotState.forEach((s) => {
        if (s.spin > 0) {
          s.spin -= dt; s.off += dt * 40;
          if (s.spin <= 0) {
            s.reels = s.reels.map(() => (Math.random() * SYMS.length) | 0);
            if (Math.random() < 0.22) { s.reels = [s.reels[0], s.reels[0], s.reels[0]]; s.win = 1.6; }
            s.wait = rnd(2, 7);
          }
        } else { s.wait -= dt; if (s.wait <= 0) s.spin = rnd(0.9, 1.6); }
        s.win = Math.max(0, s.win - dt);
      });
      jack.v += dt * rnd(40, 160);
      wheel.a += wheel.v * dt; wheel.ball += wheel.bv * dt;
    }
    function drawRoulette() {
      const R = L.roulette; if (!R) return;
      const [cx, cy] = R.c, rx = R.rx, ry = R.ry;
      for (let y = cy - ry; y <= cy + ry; y++) for (let x = cx - rx; x <= cx + rx; x++) {
        const nx = (x - cx) / rx, ny = (y - cy) / ry, d = nx * nx + ny * ny;
        if (d > 1) continue;
        const ang = Math.atan2(ny, nx) + wheel.a;
        const k = (((Math.floor((ang / (Math.PI * 2)) * 37) % 37) + 37) % 37);
        if (d > 0.55) apx(x, y, k === 0 ? [30, 140, 70] : k % 2 ? [180, 28, 36] : [24, 20, 24]);
        else if (d > 0.2) apx(x, y, (k % 4 === 0) ? [190, 150, 70] : [120, 70, 40]);
        else apx(x, y, d < 0.06 ? [250, 214, 120] : [190, 150, 70]);
      }
      const bx = Math.round(cx + Math.cos(wheel.ball) * rx * 0.86), by = Math.round(cy + Math.sin(wheel.ball) * ry * 0.86);
      apx(bx, by, [255, 255, 255]);
    }
    function drawCasino(t) {
      if (L.bulbs) {
        const n = L.bulbs.length, step = Math.floor(t * 10);
        L.bulbs.forEach(([x, y], i) => {
          const on = (i + step) % 4 === 0 || (i + step) % 4 === 1;
          if (on) epx(x, y, 255, 240, 190); else epx(x, y, 150, 100, 50, 0.6);
        });
      }
      (L.slots || []).forEach((sl, si) => {
        const s = slotState[si], [x0, y0, x1, y1] = sl.reels, rw = Math.floor((x1 - x0 + 1) / 3);
        erect(x0, y0, x1, y1, 236, 232, 220);
        for (let r = 0; r < 3; r++) {
          const rx0 = x0 + r * rw, cx = rx0 + (rw >> 1);
          if (r) erect(rx0, y0, rx0, y1, 170, 164, 156);
          const spinning = s.spin > 0 && (r === 0 || s.spin > 0.25 * r);
          const sym = spinning ? (Math.floor(s.off + r * 3) % SYMS.length) : s.reels[r];
          const c = SYMS[sym], dy = spinning ? Math.floor((s.off * 3 + r) % 6) - 3 : 0;
          const top = ((y0 + y1) >> 1) - 3 + dy;
          for (let yy = Math.max(y0 + 1, top); yy <= Math.min(y1 - 1, top + 6); yy++) for (let xx = cx - 2; xx <= cx + 2; xx++) {
            if ((yy === top || yy === top + 6) && (xx === cx - 2 || xx === cx + 2)) continue;
            epx(xx, yy, c[0], c[1], c[2]);
          }
          if (!spinning) epx(cx - 1, top + 1, 255, 255, 255, 0.7);
          if (spinning) for (let xx = rx0 + 1; xx < rx0 + rw; xx++) { epx(xx, y0 + 2, 200, 196, 190); epx(xx, y1 - 2, 200, 196, 190); }
        }
        const [mx0, my, mx1] = sl.marquee;
        const hot = s.win > 0 && Math.floor(t * 8) % 2;
        for (let x = mx0; x <= mx1; x += 2) {
          const on = hot || ((x >> 1) + Math.floor(t * 6)) % 3 === 0;
          epx(x, my, on ? 255 : 120, on ? 236 : 80, on ? 160 : 40);
          epx(x, my + 13, on ? 255 : 120, on ? 236 : 80, on ? 160 : 40);
        }
        if (hot) { erect(x0, y0, x1, y0 + 1, 255, 220, 90); erect(x0, y1 - 1, x1, y1, 255, 220, 90); }
      });
      if (L.jackpot) {
        const [x, y, w] = L.jackpot.digits;
        const s = String(Math.floor(jack.v)).padStart(7, '0');
        const tw = textWidth(s) * 3;
        etext(s, x + ((w - tw) >> 1), y, [255, 120, 70], 1, 3);
        if (Math.floor(t * 2) % 2) etext('$FROG', x + ((w - textWidth('$FROG')) >> 1), y + 18, [255, 210, 120]);
      }
    }

    function insideWindow(i) { if (!L.window) return false; const w = L.window.rect, x = i % W, y = (i / W) | 0; return x >= w[0] && x <= w[2] && y >= w[1] && y <= w[3]; }

    function drawRain() {
      for (const r of rain) for (let k = 0; k < 3; k++) {
        const x = Math.round(r.x + k * 0.25), y = Math.round(r.y - k);
        const p = (y * W + x) * 4;
        if (x < 0 || y < 0 || x >= W || y >= H || bgAlpha[p + 3] || !insideWindow(y * W + x)) continue;
        epx(x, y, 150, 170, 230, 0.55 - k * 0.15);
      }
    }

    function drawNeon() {
      const r = L.neon.rect, halo = T.neonHalo || [255, 140, 70];
      for (let y = r[1]; y <= r[3]; y++) for (let x = r[0]; x <= r[2]; x++) {
        const p = (y * W + x) * 4; if (!neonImg[p + 3]) continue;
        out.data[p] = neonImg[p]; out.data[p + 1] = neonImg[p + 1]; out.data[p + 2] = neonImg[p + 2];
      }
      for (let y = Math.max(0, r[1] - 2); y <= r[3] + 2; y++) for (let x = r[0] - 2; x <= r[2] + 2; x++) {
        if ((x + y) & 1) continue;
        const p = (y * W + x) * 4;
        if (neonImg[p + 3]) continue;
        let near = false;
        for (let dy = -2; dy <= 2 && !near; dy++) for (let dx = -2; dx <= 2; dx++) { const q = ((y + dy) * W + x + dx) * 4; if (neonImg[q + 3]) { near = true; break; } }
        if (near) epx(x, y, halo[0], halo[1], halo[2], 0.35);
      }
    }

    function drawCones(t) {
      const c = T.cones;
      const lamps = lights.filter((l) => l.kind === 'lamp');
      lamps.forEach((l, li) => {
        const lx = l.x, ly = l.y, end = T.coneEnd || 250;
        for (let y = ly + 2; y < end; y++) {
          const k = (y - ly) / (end - ly);
          const half = 6 + k * 62;
          const a = (T.coneAlpha || 0.12) * (1 - k);
          for (let x = Math.round(lx - half); x <= lx + half; x++) {
            if (((x + y) & 1) === 0) continue;
            const edge = 1 - Math.abs(x - lx) / half;
            epx(x, y, c[0], c[1], c[2], a * Math.min(1, edge * 2.5));
          }
        }
        dust.filter((d) => d.lamp === li).forEach((d) => {
          const y = ly + 10 + d.t * (end - ly - 20), half = 6 + ((y - ly) / (end - ly)) * 62;
          const x = lx + d.s * half * 0.8 + Math.sin(t + d.s * 9) * 2;
          epx(x, y, 255, 230, 190, 0.5 * (1 - d.t));
        });
      });
    }

    function drawClocks() {
      if (!L.clocks) return;
      const now = new Date();
      L.clocks.forEach((ck) => {
        const [cx, cy] = ck.c;
        let h = now.getHours(), m = now.getMinutes();
        if (ck.tz !== undefined) {
          const utc = now.getUTCHours() + now.getUTCMinutes() / 60 + ck.tz;
          h = Math.floor(((utc % 24) + 24) % 24); m = now.getUTCMinutes();
        }
        const len = ck.hands || [3, 5, 5];
        const hands = [
          [((h % 12) + m / 60) / 12, len[0], [30, 28, 34]],
          [(m + now.getSeconds() / 60) / 60, len[1], [30, 28, 34]],
        ];
        if (len[2]) hands.push([now.getSeconds() / 60, len[2], [200, 40, 40]]);
        hands.forEach(([f, n, col]) => {
          const a = f * Math.PI * 2;
          for (let s = 0; s <= n; s++) apx(Math.round(cx + Math.sin(a) * s), Math.round(cy - Math.cos(a) * s), col);
        });
      });
    }

    function drawTape() {
      if (!L.tape) return;
      const path = L.tape.path;
      const off = Math.floor(tapeOffset);
      for (let i = 0; i < path.length; i++) {
        const k = (i + off) % 7;
        if (k === 0 || k === 2) apx(path[i][0], path[i][1], [70, 70, 80]);
      }
    }

    function drawChart(chart, s, opts) {
      const [x0, y0, x1, y1] = s;
      let lo = Infinity, hi = -Infinity;
      chart.forEach((c) => { lo = Math.min(lo, c.l); hi = Math.max(hi, c.h); });
      const span = Math.max(1, hi - lo);
      const Y = (v) => Math.round(y1 - ((v - lo) / span) * (y1 - y0));
      chart.forEach((c, i) => {
        const x = x0 + i * opts.pitch;
        if (x + opts.body > x1 + 1) return;
        const up = c.c >= c.o;
        const col = opts.mono ? (up ? opts.mono : opts.monoDim) : up ? [92, 230, 112] : [240, 84, 84];
        const wx = x + (opts.body >> 1);
        for (let y = Y(c.h); y <= Y(c.l); y++) epx(wx, y, col[0] * 0.75, col[1] * 0.75, col[2] * 0.75);
        const a = Y(Math.max(c.o, c.c)), b = Math.max(a, Y(Math.min(c.o, c.c)));
        erect(x, a, x + opts.body - 1, b, col[0], col[1], col[2]);
      });
      return Y;
    }

    function drawScreen(d) {
      const [x0, y0, x1, y1] = d.screen;
      const asleep = !d.frog || d.frog.state !== 'work';
      const st = T.screen;
      if (asleep) {
        const bg = st === 'crt' ? [4, 14, 8] : st === 'pump' ? [14, 6, 22] : [8, 12, 22];
        erect(x0, y0, x1, y1, bg[0], bg[1], bg[2]);
        const sx = x0 + 1 + Math.round(d.saver.x), sy = y0 + 1 + Math.round(d.saver.y);
        const c = st === 'crt' ? [60, 200, 90] : st === 'pump' ? [200, 90, 255] : [90, 140, 240];
        erect(sx, sy, sx + 1, sy + 1, c[0], c[1], c[2]);
      } else if (d.event) {
        const bad = d.event === 'RUG' || d.event === 'SELL';
        const gold = d.event === 'KING';
        const blink = Math.floor(d.eventT * 6) % 2;
        if (st === 'crt') {
          erect(x0, y0, x1, y1, 4, blink ? 40 : 22, 12);
        } else if (gold) erect(x0, y0, x1, y1, blink ? 150 : 90, blink ? 110 : 70, 10);
        else erect(x0, y0, x1, y1, bad ? (blink ? 150 : 90) : 20, bad ? 20 : (blink ? 120 : 70), bad ? 24 : 40);
        const tw = textWidth(d.event);
        const tc = st === 'crt' ? [120, 255, 150] : bad ? [255, 220, 210] : gold ? [255, 244, 200] : [220, 255, 220];
        etext(d.event, ((x0 + x1) >> 1) - (tw >> 1), ((y0 + y1) >> 1) - 2, tc);
      } else if (st === 'pump') {
        erect(x0, y0, x1, y1, 16, 8, 26);
        for (let y = y0 + 8; y <= y1 - 4; y += 4) for (let x = x0; x <= x1; x += 2) epx(x, y, 34, 18, 50);
        etext(d.coin, x0 + 1, y0 + 1, [255, 110, 200]);
        drawChart(d.chart, [x0 + 1, y0 + 8, x1 - 1, y1 - 5], { pitch: 3, body: 2 });
        // bonding progress bar
        erect(x0 + 1, y1 - 2, x1 - 1, y1 - 1, 40, 20, 60);
        erect(x0 + 1, y1 - 2, x0 + 1 + Math.round((x1 - x0 - 2) * d.bond / 100), y1 - 1, 200, 90, 255);
      } else if (st === 'crt') {
        erect(x0, y0, x1, y1, 4, 18, 8);
        const g = [90, 255, 130], gd = [40, 120, 60];
        etext(d.coin, x0 + 1, y0 + 1, g);
        const Y = drawChart(d.chart, [x0 + 1, y0 + 8, x1 - 1, y1 - 1], { pitch: 3, body: 2, mono: g, monoDim: gd });
        const py = Y(d.chart[d.chart.length - 1].c);
        for (let x = x0; x <= x1; x += 2) epx(x, py, 140, 255, 170, 0.35);
        for (let y = y0 + 1; y <= y1; y += 2) for (let x = x0; x <= x1; x++) epx(x, y, 0, 0, 0, 0.28);
        // curved CRT glass corners
        epx(x0, y0, 30, 30, 30); epx(x1, y0, 30, 30, 30); epx(x0, y1, 30, 30, 30); epx(x1, y1, 30, 30, 30);
      } else {
        erect(x0, y0, x1, y1, 10, 18, 22);
        for (let y = y0 + 8; y <= y1; y += 4) for (let x = x0; x <= x1; x += 2) epx(x, y, 22, 40, 44);
        etext(d.coin, x0 + 1, y0 + 1, [255, 190, 90]);
        const last = d.chart[d.chart.length - 1];
        const Y = drawChart(d.chart, [x0 + 1, y0 + 8, x1 - 1, y1 - 1], { pitch: 3, body: 2 });
        const py = Y(last.c);
        for (let x = x0; x <= x1; x += 2) epx(x, py, 255, 255, 255, 0.35);
      }
      for (let x = x0; x <= x1; x++) epx(x, y0, 255, 255, 255, 0.08);
      if (d.screen2) {
        const [a0, b0, a1, b1] = d.screen2;
        erect(a0, b0, a1, b1, 10, 14, 24);
        if (!asleep) d.book.forEach((v, i) => {
          const y = b0 + 1 + i * 3; if (y > b1 - 1) return;
          const half = (a1 - a0) >> 1;
          erect(a0 + half - Math.round(v * half / 10), y, a0 + half - 1, y + 1, 220, 80, 80);
          erect(a0 + half, y, a0 + half + Math.round((11 - v) * half / 11), y + 1, 90, 220, 110);
        });
      }
    }

    function drawChartTV(t) {
      const [x0, y0, x1, y1] = L.tv.screen;
      erect(x0, y0, x1, y1, 8, 16, 20);
      for (let y = y0 + 12; y <= y1 - 10; y += 6) for (let x = x0; x <= x1; x += 3) epx(x, y, 24, 44, 46);
      const last = tv.chart[tv.chart.length - 1], first = tv.chart[0];
      const ch = ((last.c - first.o) / first.o) * 100;
      etext(T.tvTitle || '$FROG/SOL', x0 + 3, y0 + 3, [255, 190, 90]);
      const pct = (ch >= 0 ? '+' : '') + ch.toFixed(1) + '%';
      etext(pct, x1 - 2 - textWidth(pct), y0 + 3, ch >= 0 ? [110, 240, 120] : [255, 90, 80]);
      if (Math.floor(t * 2) % 2) erect(x0 + 44, y0 + 4, x0 + 45, y0 + 5, 255, 60, 60);
      etext('LIVE', x0 + 48, y0 + 3, [255, 120, 110]);
      const Y = drawChart(tv.chart, [x0 + 3, y0 + 11, x1 - 3, y1 - 10], { pitch: 5, body: 3 });
      const py = Y(last.c);
      for (let x = x0; x <= x1; x += 2) epx(x, py, 255, 255, 255, 0.4);
      tv.chart.forEach((c, i) => {
        const x = x0 + 3 + i * 5; if (x + 3 > x1) return;
        const v = 1 + Math.round(Math.abs(c.c - c.o) * 1.4) % 7;
        erect(x, y1 - 1 - v, x + 2, y1 - 1, c.c >= c.o ? 50 : 120, c.c >= c.o ? 120 : 50, 60);
      });
      for (let k = 0; k < 18; k++) epx(x1 - 30 + k, y0 + 1 + (k >> 1), 255, 255, 255, 0.06);
    }

    function drawPumpTV(t) {
      const [x0, y0, x1, y1] = L.tv.screen;
      if (tv.state) {
        const red = tv.state === 'RUGGED';
        const blink = Math.floor(tv.stateT * 5) % 2;
        erect(x0, y0, x1, y1, red ? (blink ? 120 : 60) : (blink ? 120 : 70), red ? 10 : (blink ? 90 : 50), red ? 16 : 10);
        const w = textWidth(tv.state) * 2;
        etext(tv.state, ((x0 + x1) >> 1) - (w >> 1), ((y0 + y1) >> 1) - 5, red ? [255, 220, 210] : [255, 240, 190], 1, 2);
        etext(tv.coin, ((x0 + x1) >> 1) - (textWidth(tv.coin) >> 1), ((y0 + y1) >> 1) + 9, [255, 255, 255], 0.8);
        return;
      }
      erect(x0, y0, x1, y1, 16, 8, 28);
      for (let y = y0 + 12; y <= y1 - 12; y += 6) for (let x = x0; x <= x1; x += 3) epx(x, y, 40, 20, 60);
      etext(tv.coin, x0 + 3, y0 + 3, [255, 110, 200]);
      const mc = 'MC ' + tv.mc.toFixed(1) + 'K';
      etext(mc, x1 - 2 - textWidth(mc), y0 + 3, [190, 150, 255]);
      if (Math.floor(t * 2) % 2) erect(x0 + 34, y0 + 4, x0 + 35, y0 + 5, 255, 60, 160);
      drawChart(tv.chart, [x0 + 3, y0 + 11, x1 - 3, y1 - 13], { pitch: 5, body: 3 });
      // bonding curve progress
      const by = y1 - 9;
      etext('BONDING', x0 + 3, by, [200, 170, 255]);
      const bx0 = x0 + 32, bx1 = x1 - 20;
      erect(bx0, by, bx1, by + 4, 36, 16, 56);
      erect(bx0, by, bx0 + Math.round((bx1 - bx0) * tv.bond / 100), by + 4, 210, 90, 255);
      for (let x = bx0; x <= bx1; x += 4) epx(x, by + 2, 255, 255, 255, 0.15);
      const pct = Math.floor(tv.bond) + '%';
      etext(pct, x1 - 2 - textWidth(pct), by, [255, 214, 120]);
      for (let k = 0; k < 18; k++) epx(x1 - 30 + k, y0 + 1 + (k >> 1), 255, 255, 255, 0.06);
    }

    function drawFlap(t) {
      const [x0, y0, x1, y1] = L.tv.screen;
      erect(x0, y0, x1, y1, 14, 12, 10);
      etext('MARKETS', x0 + 3, y0 + 2, [240, 210, 140]);
      const glyphsList = '0123456789';
      const rowH = 9, top = y0 + 10;
      flap.forEach((f, i) => {
        const y = top + i * rowH;
        if (y + 7 > y1) return;
        // tiles
        const sym = f.sym.padEnd(4, ' ');
        const val = f.flipT > 0 ? f.target.split('').map((c) => (c === '.' || c === ',' ? c : pick(glyphsList.split('')))).join('') : f.shown;
        const ch = (f.ch >= 0 ? '^' : 'v') + Math.abs(f.ch).toFixed(2);
        let x = x0 + 3;
        const tile = (c, col) => {
          erect(x, y, x + 4, y + 7, 30, 28, 26);
          epx(x, y + 3, 6, 6, 6); erect(x, y + 4, x + 4, y + 4, 8, 8, 8);
          if (c !== ' ') etext(c, x + 1, y + 1, col);
          x += 6;
        };
        [...sym].forEach((c) => tile(c, [240, 230, 210]));
        x += 2;
        [...val.padStart(8, ' ')].forEach((c) => tile(c, [255, 220, 150]));
        x += 2;
        [...ch].forEach((c) => tile(c, f.ch >= 0 ? [120, 240, 140] : [255, 110, 100]));
      });
    }

    function drawTicker() {
      if (!L.ticker) return;
      const [x0, y0, x1, y1] = L.ticker.rect;
      const cols = Math.floor((x1 - x0) / 2) + 1;
      const off = Math.floor(tickerOffset) % tickerCols.length;
      for (let c = 0; c < cols; c++) {
        const k = (off + c) % tickerCols.length;
        const col = tickerCols[k], rgb = tickerColors[k];
        for (let r = 0; r < 5; r++) {
          const x = x0 + c * 2, y = y0 + 2 + r * 2;
          if (y > y1) continue;
          if (col[r]) { epx(x, y, rgb[0], rgb[1], rgb[2]); epx(x + 1, y, rgb[0], rgb[1], rgb[2], 0.25); }
        }
      }
    }

    function drawLeds(t) {
      if (!L.rig) return;
      L.rig.leds.forEach(([x, y], i) => {
        const on = Math.sin(t * (2 + i * 0.7) + i) > 0.2;
        const c = (T.ledColors || [[90, 255, 120]])[i % (T.ledColors || [1]).length];
        epx(x, y, on ? c[0] : c[0] * 0.3, on ? c[1] : c[1] * 0.3, on ? c[2] : c[2] * 0.3);
        if (i % 2) epx(x, y + 2, 255, on ? 170 : 60, 40, on ? 1 : 0.4);
      });
    }

    function drawStrips(t) {
      if (!L.strips) return;
      L.strips.forEach(([x0, y, x1], si) => {
        for (let x = x0; x <= x1; x++) {
          const h = (x * 0.04 - t * 0.6 + si * 0.3) % 1;
          const k = (h + 1) % 1;
          // pink -> purple -> cyan cycle
          const c = k < 0.33 ? [255, 70, 170] : k < 0.66 ? [170, 80, 255] : [80, 220, 255];
          epx(x, y, c[0], c[1], c[2]);
          epx(x, y - 1, c[0], c[1], c[2], 0.25);
          epx(x, y + 1, c[0], c[1], c[2], 0.25);
        }
      });
    }

    function drawLaunchpad(t) {
      if (!L.launchpad) return;
      const [x0, y0, x1, y1] = L.launchpad.rect;
      erect(x0, y0, x1, y1, 14, 8, 24);
      etext('NEW LAUNCHES', x0 + 3, y0 + 3, [255, 120, 210]);
      if (Math.floor(t * 2) % 2) erect(x1 - 6, y0 + 4, x1 - 4, y0 + 6, 255, 60, 160);
      const rowH = Math.floor((y1 - y0 - 12) / launches.length);
      launches.forEach((l, i) => {
        const y = y0 + 12 + i * rowH;
        const bad = l.state === 'RUGGED', good = l.state === 'BONDED';
        const blink = l.state && Math.floor(l.t * 6) % 2;
        if (l.state) erect(x0 + 1, y - 1, x1 - 1, y + rowH - 3, bad ? (blink ? 110 : 60) : (blink ? 110 : 60), bad ? 10 : (blink ? 80 : 46), bad ? 16 : 8);
        etext(l.coin, x0 + 3, y, bad ? [255, 200, 200] : [240, 220, 255]);
        const bx0 = x0 + 34, bx1 = x1 - 22;
        if (l.state) {
          etext(l.state, bx0, y, bad ? [255, 90, 90] : [255, 220, 100]);
        } else {
          erect(bx0, y, bx1, y + 4, 40, 20, 60);
          erect(bx0, y, bx0 + Math.round((bx1 - bx0) * l.p / 100), y + 4, 200, 90, 255);
          const pct = Math.floor(l.p) + '%';
          etext(pct, x1 - 3 - textWidth(pct), y, [200, 170, 255]);
        }
      });
    }

    function drawCounter(t) {
      if (!L.counter) return;
      const [x, y, w] = L.counter.digits;
      const s = String(rugCount).padStart(3, '0');
      const flashOn = alarm > 0 && Math.floor(t * 6) % 2;
      const total = textWidth(s) * 3;
      etext(s, x + ((w - total) >> 1), y, flashOn ? [255, 240, 220] : [255, 60, 60], 1, 3);
    }

    function drawCountdown() {
      if (!L.countdown) return;
      const [x, y] = L.countdown.pos;
      const s = Math.max(0, Math.floor(countdown));
      const txt = String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
      etext(txt, x, y, s < 10 ? [255, 90, 90] : [120, 255, 200], 1, 2);
    }

    function drawSiren(t) {
      if (!L.siren) return;
      const [sx, sy] = L.siren.pos;
      const on = alarm > 0;
      const dome = on ? (Math.sin(t * 18) > 0 ? [255, 70, 60] : [200, 30, 30]) : [90, 20, 24];
      erect(sx - 3, sy - 4, sx + 3, sy, dome[0], dome[1], dome[2]);
      erect(sx - 2, sy - 5, sx + 2, sy - 5, dome[0], dome[1], dome[2]);
      if (!on) return;
      const ang = t * 7;
      for (let r = 6; r < 150; r += 1) {
        const spread = 0.18;
        for (let a = -spread; a <= spread; a += 0.02) {
          const x = sx + Math.cos(ang + a) * r, y = sy + Math.sin(ang + a) * r * 0.7;
          if (((x | 0) + (y | 0)) & 1) continue;
          epx(x, y, 255, 40, 40, 0.16 * (1 - r / 150));
        }
      }
    }

    function drawPlus(t) {
      if (!L.boss || !L.boss.plus || (bossSprite && showBoss)) return;
      const [cx, cy] = L.boss.plus;
      const pulse = 0.5 + 0.5 * Math.sin(t * 3);
      const hot = hover === -1;
      const R = 9;
      for (let y = cy - R - 4; y <= cy + R + 4; y++) for (let x = cx - R - 4; x <= cx + R + 4; x++) {
        const d = Math.hypot(x - cx, y - cy);
        if (d > R + 1 && d <= R + 3 + pulse * 1.5 && ((x + y) & 1)) epx(x, y, 255, 200, 90, 0.35 + (hot ? 0.3 : 0));
      }
      for (let y = cy - R - 1; y <= cy + R + 1; y++) for (let x = cx - R - 1; x <= cx + R + 1; x++) {
        const d = Math.hypot(x - cx, y - cy);
        if (d <= R + 0.5) epx(x, y, 20, 18, 22);
        if (d <= R - 0.6) epx(x, y, hot ? 70 : 46, hot ? 50 : 34, hot ? 24 : 20);
        if (d > R - 1.6 && d <= R - 0.6) epx(x, y, 240, 190, 80);
      }
      const c = hot ? [255, 244, 200] : [255, 214, 110];
      erect(cx - 1, cy - 5, cx, cy + 4, c[0], c[1], c[2]);
      erect(cx - 5, cy - 1, cx + 4, cy, c[0], c[1], c[2]);
      const label = 'BOSS SEAT';
      const w = textWidth(label);
      const lx = cx - (w >> 1), ly = cy + R + 5;
      erect(lx - 3, ly - 2, lx + w + 2, ly + 6, 20, 18, 22);
      erect(lx - 2, ly - 1, lx + w + 1, ly + 5, 46, 34, 20);
      etext(label, lx, ly, [255, 214, 110]);
    }

    // ---------------------------------------------------------- hover
    function deskBox(d) { return [d.x - 4, d.pos[1] - 58, d.x + 108, d.pos[1] + 44]; }
    function onMove(e) {
      const r = canvas.getBoundingClientRect();
      const x = ((e.clientX - r.left) / r.width) * W, y = ((e.clientY - r.top) / r.height) * H;
      hover = -2;
      desks.forEach((d, i) => { const b = deskBox(d); if (x >= b[0] && x <= b[2] && y >= b[1] && y <= b[3]) hover = i; });
      const bb = L.boss.chair;
      if (hover < 0 && x >= bb[0] && x <= bb[2] && y >= bb[1] && y <= bb[3]) hover = -1;
      if (hover === -2) { tip.hidden = true; canvas.style.cursor = 'default'; return; }
      canvas.style.cursor = 'pointer';
      tip.innerHTML = tipHtml(hover);
      tip.hidden = false;
      const host = canvas.parentElement.getBoundingClientRect();
      let tx = e.clientX - host.left + 16, ty = e.clientY - host.top + 16;
      tx = Math.min(tx, host.width - tip.offsetWidth - 8);
      ty = Math.min(ty, host.height - tip.offsetHeight - 8);
      tip.style.left = Math.max(8, tx) + 'px'; tip.style.top = Math.max(8, ty) + 'px';
    }
    function tipHtml(i) {
      if (i === -1) return `<b>Boss seat</b><span class="r legendary">Empty</span><p>Click to see how to get a Boss Frog NFT.</p>`;
      const d = desks[i];
      if (!d.frog) return `<b>Desk ${i + 1}</b><span class="r">Empty</span><p>Pick a frog from your crew to start trading here.</p>`;
      const f = d.frog;
      const st = f.state === 'sleep' ? 'Asleep, out of stamina' : 'Trading';
      return `<b>${f.name}</b><span class="r ${f.rarity}">${f.rarity}</span>` +
        `<div class="bar"><i style="width:${f.stamina}%"></i></div><p>${st} · ${f.stamina}/100 stamina<br>Power ${f.power} · ${f.skill}</p>`;
    }
    function drawHover() {
      const [x0, y0, x1, y1] = hover === -1 ? L.boss.chair : deskBox(desks[hover]);
      const c = [255, 196, 90];
      for (let k = 0; k < 6; k++) {
        epx(x0 + k, y0, ...c); epx(x0, y0 + k, ...c); epx(x1 - k, y0, ...c); epx(x1, y0 + k, ...c);
        epx(x0 + k, y1, ...c); epx(x0, y1 - k, ...c); epx(x1 - k, y1, ...c); epx(x1, y1 - k, ...c);
      }
    }

    // ---------------------------------------------------------- loop
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let last = 0, acc = 0;
    function loop(now) {
      if (!running) return;
      const t = now / 1000;
      const dt = Math.min(0.1, last ? t - last : 0.033);
      last = t;
      acc += dt;
      if (acc >= 1 / 30) {
        update(reduce ? acc * 0.3 : acc, t);
        render(reduce ? 0 : t);
        acc = 0;
      }
      raf = requestAnimationFrame(loop);
    }

    const ready = init();
    if (embed) {
      return {
        ready,
        desks: () => desks,
        setFrog(i, f) { if (desks[i]) desks[i].frog = f; },
        setBoss(on) { showBoss = !!on; },
        setHover(i) { hover = i; },
        /** Advances and redraws at 30 fps. Returns true when the canvas changed. */
        step(dt, t) {
          if (!loaded) return false;
          embAcc += dt;
          if (embAcc < 1 / 30) return false;
          update(embAcc, t); render(t); embAcc = 0;
          return true;
        },
        stop() {},
      };
    }
    return {
      setFrog(i, f) { if (desks[i]) desks[i].frog = f; },
      setBoss(on) { showBoss = !!on; },
      stop() {
        running = false; cancelAnimationFrame(raf);
        canvas.removeEventListener('mousemove', onMove);
        canvas.removeEventListener('pointerdown', onMove);
        canvas.removeEventListener('click', onClick);
        canvas.removeEventListener('mouseleave', onLeave);
        tip.hidden = true;
      },
    };
  }

  window.OfficeScene = { create };
})();
