/* Frog Traders menu screens (home, shop, ...): static pixel layers plus live details.
 * HomeScene.create(data, canvas) where data = { screens: {name: {layout, images}}, shared, fonts, start }.
 */
(function () {
  'use strict';

  function create(D, canvas, onOpen) {
    let cur = D.start || 'home';
    let L = D.screens[cur].layout;
    const W = L.size[0], H = L.size[1];
    canvas.width = W; canvas.height = H;
    let g = canvas.getContext('2d');
    g.imageSmoothingEnabled = false;
    const IMGS = {};
    let img = {};
    const shared = {};
    const BIG = parse(D.fonts.big), SMALL = parse(D.fonts.small);
    const GLYPH = {};
    for (const [k, f] of Object.entries(D.glyphs || {})) {
      GLYPH[k] = { h: f.h, g: {} };
      for (const ch in f.g) GLYPH[k].g[ch] = f.g[ch].split('|').map((r) => [...r].map((c) => c === '#'));
    }
    const wallet = { value: D.wallet || 487140 };
    const LIVE = !!window.FTLive;
    const shortAddr = (a) => (a ? a.slice(0, 4) + '...' + a.slice(-4) : 'NOT CONNECTED');
    const MODS = window.FTScreens || {};
    let mod = null;
    let hover = null, press = null, toast = null, running = true;
    const rnd = (a, b) => a + Math.random() * (b - a);

    function parse(f) {
      const o = {};
      for (const k in f) o[k] = f[k].split('|').map((r) => [...r].map((c) => c === '#'));
      return o;
    }
    function cols(s, font) {
      const out = [];
      [...s].forEach((ch, i) => {
        const gl = font[ch] || font[ch.toUpperCase()] || font[' '];
        for (let x = 0; x < gl[0].length; x++) out.push(gl.map((r) => r[x]));
        if (i < s.length - 1) out.push(gl.map(() => false));
      });
      return out;
    }
    const tw = (s, font) => cols(s, font).length;
    function px(x, y, c, a = 1) { g.globalAlpha = a; g.fillStyle = c; g.fillRect(x | 0, y | 0, 1, 1); g.globalAlpha = 1; }
    function rect(x0, y0, x1, y1, c, a = 1) { g.globalAlpha = a; g.fillStyle = c; g.fillRect(x0 | 0, y0 | 0, (x1 - x0 + 1) | 0, (y1 - y0 + 1) | 0); g.globalAlpha = 1; }
    function text(s, x, y, c, font = SMALL, shadow = '#141216') {
      const cs = cols(s, font);
      if (shadow) cs.forEach((col, i) => col.forEach((on, j) => { if (on) px(x + i + 1, y + j + 1, shadow); }));
      cs.forEach((col, i) => col.forEach((on, j) => { if (on) px(x + i, y + j, c); }));
    }
    /** Text in the baked fonts: style 'title' | 'head' | 'body'. */
    function gwidth(s, style) {
      const f = GLYPH[style]; let w = 0;
      for (const ch of String(s)) { const gl = f.g[ch] || f.g['?']; w += gl[0].length + 1; }
      return Math.max(0, w - 1);
    }
    function gtext(s, x, y, c, style = 'body', o = {}) {
      const f = GLYPH[style]; s = String(s);
      if (o.align === 'center') x -= gwidth(s, style) >> 1; else if (o.align === 'right') x -= gwidth(s, style);
      x |= 0; y |= 0;
      const draw = (ox, oy, col, a) => {
        g.globalAlpha = a == null ? 1 : a; g.fillStyle = col; let cx = x + ox;
        for (const ch of s) {
          const gl = f.g[ch] || f.g['?'];
          for (let j = 0; j < gl.length; j++) for (let i = 0; i < gl[j].length; i++) if (gl[j][i]) g.fillRect(cx + i, y + oy + j, 1, 1);
          cx += gl[0].length + 1;
        }
        g.globalAlpha = 1;
      };
      if (o.outline) for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) draw(dx, dy, o.outline, o.alpha);
      if (o.shadow !== null) draw(1, 1, o.shadow || '#141216', o.alpha);
      draw(0, 0, c, o.alpha);
      return gwidth(s, style);
    }
    function load(src) { return new Promise((res) => { const i = new Image(); i.onload = () => res(i); i.src = src; }); }

    // blink frame for the frog on the Frogs card
    function blinkOf(im) {
      const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
      const x = c.getContext('2d'); x.drawImage(im, 0, 0);
      const d = x.getImageData(0, 0, im.width, im.height), a = d.data, w = im.width, h = im.height;
      const white = (i) => a[i * 4 + 3] && a[i * 4] > 196 && a[i * 4 + 1] > 190 && a[i * 4 + 2] > 160;
      const seen = new Uint8Array(w * h), lim = (h * 0.45) | 0;
      for (let y = 0; y < lim; y++) for (let xx = 0; xx < w; xx++) {
        const s = y * w + xx; if (seen[s] || !white(s)) continue;
        const st = [s], comp = []; seen[s] = 1;
        while (st.length) {
          const p = st.pop(); comp.push(p);
          const px_ = p % w, py = (p / w) | 0;
          [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => {
            const nx = px_ + dx, ny = py + dy; if (nx < 0 || ny < 0 || nx >= w || ny >= lim) return;
            const q = ny * w + nx; if (!seen[q] && white(q)) { seen[q] = 1; st.push(q); }
          });
        }
        if (comp.length < 5) continue;
        let x0 = w, x1 = 0, y0 = h, y1 = 0;
        comp.forEach((p) => { const px_ = p % w, py = (p / w) | 0; x0 = Math.min(x0, px_); x1 = Math.max(x1, px_); y0 = Math.min(y0, py); y1 = Math.max(y1, py); });
        let lid = [116, 146, 78];
        for (let yy = y0 - 2; yy >= Math.max(0, y0 - 5); yy--) { const q = (yy * w + ((x0 + x1) >> 1)) * 4; if (a[q + 3] && a[q] + a[q + 1] + a[q + 2] > 150) { lid = [a[q], a[q + 1], a[q + 2]]; break; } }
        const src = new Uint8ClampedArray(a);
        for (let yy = y0; yy <= y1; yy++) for (let xx2 = x0; xx2 <= x1; xx2++) {
          const q = (yy * w + xx2) * 4; if (!src[q + 3]) continue;
          const lum = src[q] + src[q + 1] + src[q + 2];
          if (lum > 480 || lum < 110) { a[q] = lid[0]; a[q + 1] = lid[1]; a[q + 2] = lid[2]; }
        }
        const ly = Math.min(y1, y0 + Math.round((y1 - y0) * 0.65));
        for (let xx2 = x0; xx2 <= x1; xx2++) { const q = (ly * w + xx2) * 4; if (a[q + 3]) { a[q] = 20; a[q + 1] = 18; a[q + 2] = 22; } }
      }
      x.putImageData(d, 0, 0);
      return c;
    }

    // ------------------------------------------------------------ state
    let neonOn = true, neonT = rnd(3, 6), neonSeq = [];
    let blinkT = 2, blinking = 0;
    const dust = Array.from({ length: 24 }, () => ({ x: rnd(150, 490), y: rnd(36, 90), v: rnd(0.03, 0.09), p: rnd(0, 6) }));
    let tickerOff = 0;
    const tickerParts = [
      ['REWARD POOL ', '#ffc46e'], ['28,412,900 $FROG', '#f2e7d4'], ['   DAILY PAYOUT ', '#ffc46e'], ['10%', '#7ee054'],
      ['   FROGS TRADING ', '#ffc46e'], ['1,284', '#f2e7d4'], ['   HOT OFFICE ', '#ffc46e'], ['PUMP.FUN RUGS', '#ff5ab8'],
      ['   LAST BIG WIN ', '#ffc46e'], ['+42,000 $FROG', '#7ee054'], ['   BOSS FROGS MINT ', '#ffc46e'], ['SOON', '#f0be52'], ['      ', '#000'],
    ];
    const tick = [];
    tickerParts.forEach(([s, c]) => cols(s, SMALL).forEach((col) => tick.push([col, c])));
    const prices = ['2.4K', '2.6K', '2.1K', '3.0K', '2.8K'];
    let priceI = 0, priceT = 2.5;
    const reels = ['7', '$', 'F', '7', 'X'];

    function cardAt(x, y) {
      if (mod && mod.hit) { const m = mod.hit(ctx, x, y); if (m) return { kind: 'mod', item: m }; }
      for (const c of L.cards) if (x >= c.x && x < c.x + c.w && y >= c.y && y < c.y + c.h) return { kind: 'card', item: c };
      for (const t of L.tiles) if (x >= t.x && x < t.x + t.w && y >= t.y && y < t.y + t.h) return { kind: 'tile', item: t };
      const ph = L.hud.phantom; if (ph && x >= ph[0] && x <= ph[2] && y >= ph[1] && y <= ph[3]) return { kind: 'phantom', item: { key: 'phantom', title: 'PHANTOM WALLET', accent: [171, 159, 242] } };
      for (const k of ['wallet', 'settings']) {
        const b = L.hud[k]; if (b && x >= b[0] && x <= b[2] && y >= b[1] && y <= b[3]) return { kind: 'phantom', item: { key: 'phantom', title: 'WALLET', accent: [171, 159, 242] } };
      }
      const bk = L.hud.back; if (bk && x >= bk[0] && x <= bk[2] && y >= bk[1] && y <= bk[3]) return { kind: 'back', item: { key: 'back', title: 'BACK', accent: [200, 196, 210] } };
      return null;
    }
    function toCanvas(e) {
      const r = canvas.getBoundingClientRect();
      return [((e.clientX - r.left) / r.width) * W, ((e.clientY - r.top) / r.height) * H];
    }
    function onMove(e) { const [x, y] = toCanvas(e); hover = cardAt(x, y); if (mod && mod.hover) mod.hover(ctx, x, y); canvas.style.cursor = hover ? 'pointer' : 'default'; }
    function onDown(e) { const [x, y] = toCanvas(e); press = cardAt(x, y); }
    function onUp(e) {
      const [x, y] = toCanvas(e); const h = cardAt(x, y);
      if (h && press && h.item.key === press.item.key) {
        const k = h.item.key;
        if (k === 'back') go(L.back || 'home');
        else if (k === 'phantom' && D.screens.wallet) go('wallet');
        else if (h.kind === 'mod') mod.click(ctx, h.item);
        else if (D.screens[k]) go(k);
        else toast = { text: h.item.title, t: 1.8, accent: h.item.accent };
        if (onOpen) onOpen(k);
      }
      press = null;
    }
    function onLeave() { hover = null; press = null; }
    function go(name) {
      if (mod && mod.leave) mod.leave(ctx);
      cur = name; L = D.screens[name].layout; img = IMGS[name];
      mod = MODS[name] || null;
      if (mod && mod.enter) mod.enter(ctx);
      hover = null; press = null; toast = null;
      canvas.style.cursor = 'default';
      try { history.replaceState(null, '', '#' + name); } catch (e) {}
    }

    // ------------------------------------------------------------ draw
    const rgb = (a) => `rgb(${a[0]},${a[1]},${a[2]})`;
    function frame(t, dt) {
      // neon
      neonT -= dt;
      if (neonT <= 0 && !neonSeq.length) { neonSeq = Math.random() < 0.5 ? [[0.08, 0]] : [[0.06, 0], [0.05, 1], [0.1, 0]]; neonT = rnd(4, 9); }
      if (neonSeq.length) { neonSeq[0][0] -= dt; neonOn = !!neonSeq[0][1]; if (neonSeq[0][0] <= 0) { neonSeq.shift(); if (!neonSeq.length) neonOn = true; } }
      blinkT -= dt; if (blinkT <= 0) { blinking = 0.15; blinkT = rnd(2.5, 5); } blinking = Math.max(0, blinking - dt);
      priceT -= dt; if (priceT <= 0) { priceI = (priceI + 1) % prices.length; priceT = rnd(2, 4); }
      tickerOff += dt * 16;
      if (toast) { toast.t -= dt; if (toast.t <= 0) toast = null; }

      if (window.FTCrew && FTCrew.frogs.length) { const e = FTCrew.tick(dt); if (!LIVE) wallet.value += e; }
      if (LIVE) wallet.value = FTLive.wallet;
      if (mod && mod.under) mod.under(ctx, t, dt);
      g.drawImage(img.bg, 0, 0);
      // logo glow + tubes
      const lr = L.logo ? L.logo.rect : null;
      if (lr && neonOn) {
        g.drawImage(img.neon, 0, 0);
        for (let y = lr[1] - 3; y <= lr[3] + 3; y += 1) for (let x = lr[0] - 3; x <= lr[2] + 3; x += 2) {
          if (((x + y) & 1) === 0) continue;
          const i = (y * W + x) * 4;
          if (!D.neonMask[i + 3]) {
            let near = false;
            for (let dy = -3; dy <= 3 && !near; dy++) for (let dx = -3; dx <= 3; dx++) { const q = ((y + dy) * W + x + dx) * 4; if (D.neonMask[q + 3]) { near = true; break; } }
            if (near) px(x, y, '#6ee05a', 0.28);
          }
        }
      }
      if (lr) dust.forEach((d) => { d.y -= d.v; d.x += Math.sin(t + d.p) * 0.1; if (d.y < 34) { d.y = 92; d.x = rnd(150, 490); } px(d.x, d.y, '#d8ffc8', 0.35); });

      // HUD live bits
      if (L.hud.coin) {
      const [cx, cy] = L.hud.coin;
      const phase = (t * 1.6) % 1, wdt = Math.max(1, Math.round(Math.abs(Math.cos(phase * Math.PI)) * 6));
      rect(cx - wdt - 1, cy - 7, cx + wdt + 1, cy + 7, '#141216');
      rect(cx - wdt, cy - 6, cx + wdt, cy + 6, '#aa7828');
      rect(cx - wdt + 1, cy - 5, cx + wdt - 1, cy + 5, '#ecba48');
      if (wdt > 3) { text('F', cx - 1, cy - 2, '#aa7828', SMALL, null); px(cx - wdt + 1, cy - 3, '#ffe282'); }
      if (L.hud.timer) {
      const now = new Date(), next = new Date(now); next.setUTCHours(24, 0, 0, 0);
      let s = Math.floor((next - now) / 1000);
      const hh = String(Math.floor(s / 3600)).padStart(2, '0'); s %= 3600;
      const mm = String(Math.floor(s / 60)).padStart(2, '0'), ss = String(s % 60).padStart(2, '0');
      text(hh + ':' + mm + ':' + ss, L.hud.timer[0], L.hud.timer[1], '#f2e7d4', SMALL);
      }
      if (hover && (hover.kind === 'phantom' || hover.kind === 'back')) {
        const ph = hover.kind === 'back' ? L.hud.back : L.hud.phantom;
        for (let xx = ph[0] - 1; xx <= ph[2] + 1; xx++) if (xx % 2) { px(xx, ph[1] - 1, '#ab9ff2', 0.6); px(xx, ph[3] + 1, '#ab9ff2', 0.6); }
      }

      }
      if (L.hud.balance) {
        const [bx0, by0, bx1, by1] = L.hud.balance;
        rect(bx0, by0, bx1, by1, '#100d12');
        gtext(Math.round(wallet.value).toLocaleString('en-US'), bx0 + 2, by0 + 2, '#ffe282', 'title', { shadow: '#141216' });
      }
      if (L.hud.address) {
        const [ax, ay] = L.hud.address;
        gtext(LIVE ? shortAddr(FTLive.address) : '2FTB...3OT3', ax, ay, '#f2e7d4', 'title', { shadow: '#141216' });
        const on = !LIVE || FTLive.logged;
        rect(625, 13, 629, 17, '#141216'); rect(626, 14, 628, 16, on ? '#78f078' : '#e6465a');
      }
      if (mod) mod.frame(ctx, t, dt);
      // cards
      L.cards.forEach((c) => {
        const hot = hover && hover.item === c, down = press && press.item === c && hot;
        const lift = down ? 1 : hot ? -3 : 0;
        const x = c.x, y = c.y + lift;
        if (hot) {
          for (let k = 1; k <= 3; k++) for (let xx = x - k; xx <= x + c.w - 1 + k; xx++) {
            if ((xx + k) % 2) { px(xx, y - k, rgb(c.accent), 0.5 / k); px(xx, y + c.h - 1 + k, rgb(c.accent), 0.5 / k); }
          }
          for (let k = 1; k <= 3; k++) for (let yy = y - k; yy <= y + c.h - 1 + k; yy++) {
            if ((yy + k) % 2) { px(x - k, yy, rgb(c.accent), 0.5 / k); px(x + c.w - 1 + k, yy, rgb(c.accent), 0.5 / k); }
          }
        }
        g.drawImage(c.key === 'frogs' && blinking > 0 && img['card-frogs-blink'] ? img['card-frogs-blink'] : img['card-' + c.key], x, y);
        const m = c.meta;
        if (c.key === 'recruit') {
          const [hx, hy] = m.halo, r = 21 + Math.sin(t * 3) * 1.5;
          for (let yy = -r - 3; yy <= r + 3; yy++) for (let xx = -r - 3; xx <= r + 3; xx++) {
            const d = Math.hypot(xx, yy * 1.2); if (d > r && d < r + 2 && ((xx + yy + (t * 6 | 0)) % 3 === 0)) px(x + hx + xx, y + hy + yy, '#ffd66e', 0.5);
          }
          m.sparkles.forEach(([sx, sy], i) => {
            const k = (Math.sin(t * 2.6 + i * 1.9) + 1) / 2; if (k < 0.45) return;
            px(x + sx, y + sy, '#fff6d2', k); px(x + sx - 1, y + sy, '#d2aaff', k * 0.6); px(x + sx + 1, y + sy, '#d2aaff', k * 0.6);
            px(x + sx, y + sy - 1, '#d2aaff', k * 0.6); px(x + sx, y + sy + 1, '#d2aaff', k * 0.6);
          });
        }
        if (c.key === 'casino') {
          m.bulbs.forEach(([bx, by], i) => { if ((i + Math.floor(t * 8)) % 3 === 0) { px(x + bx, y + by, '#fff0b4'); px(x + bx, y + by - 1, '#ffd66e', 0.4); } });
          m.marquees.forEach(([mx0, my, mx1], k) => {
            const p = Math.floor(t * 10 + k * 3) % (mx1 - mx0 + 1);
            px(x + mx0 + p, y + my + 1, '#fff6d2'); px(x + mx0 + ((p + 7) % (mx1 - mx0 + 1)), y + my + 2, '#fff6d2', 0.7);
          });
          if (m.sparkles) m.sparkles.forEach(([sx, sy], i) => {
            const k = (Math.sin(t * 3.2 + i * 1.6) + 1) / 2; if (k < 0.4) return;
            px(x + sx, y + sy, '#fff6d2', k); px(x + sx - 1, y + sy, '#ffd66e', k * 0.6); px(x + sx + 1, y + sy, '#ffd66e', k * 0.6);
            px(x + sx, y + sy - 1, '#ffd66e', k * 0.6); px(x + sx, y + sy + 1, '#ffd66e', k * 0.6);
          });
          const art = m.art, conf = ['#ff5aa0', '#ffd65a', '#5ac8ff', '#7ee054', '#ffffff'];
          for (let k = 0; k < 14; k++) {
            const fall = ((t * (0.08 + (k % 5) * 0.02) + k * 0.137) % 1);
            const X = x + art[0] + ((k * 37) % (art[2] - art[0])) + Math.sin(t * 2 + k) * 2;
            const Y = y + art[1] + 26 + fall * 60;
            px(X, Y, conf[k % conf.length], Math.sin(fall * Math.PI));
          }
        }
        if (c.key === 'boss') m.sparkles.forEach(([sx, sy], i) => {
          const k = (Math.sin(t * 3 + i * 1.3) + 1) / 2; if (k < 0.4) return;
          px(x + sx, y + sy, '#fffbe0', k); px(x + sx - 1, y + sy, '#ffd66e', k * 0.6); px(x + sx + 1, y + sy, '#ffd66e', k * 0.6);
          px(x + sx, y + sy - 1, '#ffd66e', k * 0.6); px(x + sx, y + sy + 1, '#ffd66e', k * 0.6);
        });
        if (c.key === 'fusion') {
          const [ox, oy] = m.orb, r = 9 + Math.sin(t * 4) * 1.5;
          for (let k = 0; k < 6; k++) {
            const a = t * 2 + k * Math.PI / 3, X = x + ox + Math.cos(a) * (r + 7), Y = y + oy + Math.sin(a) * (r + 3);
            px(X, Y, '#ffe6ff'); px(X + 1, Y, '#c896ff', 0.6);
          }
          for (let yy = -14; yy <= 14; yy++) for (let xx = -14; xx <= 14; xx++) {
            const d = Math.hypot(xx, yy); if (d > r && d < r + 3 && ((xx + yy) & 1)) px(x + ox + xx, y + oy + yy, '#d2aaff', 0.35);
          }
        }
        if (c.key === 'shop') m.sparkles.forEach(([sx, sy], i) => {
          const k = (Math.sin(t * 3 + i * 1.7) + 1) / 2; if (k < 0.4) return;
          px(x + sx, y + sy, '#fff6d2', k); px(x + sx - 1, y + sy, '#ffd66e', k * 0.6); px(x + sx + 1, y + sy, '#ffd66e', k * 0.6);
          px(x + sx, y + sy - 1, '#ffd66e', k * 0.6); px(x + sx, y + sy + 1, '#ffd66e', k * 0.6);
        });
        if (m.foot && (c.key === 'frogs' || c.key === 'market')) {
          const n = c.key === 'frogs' ? (window.FTCrew ? FTCrew.frogs.length : 6) : (window.FTScreens && FTScreens.market && FTScreens.market.count != null ? FTScreens.market.count : LIVE ? 0 : 24);
          const label = c.key === 'frogs' ? `${n} ${n === 1 ? 'FROG' : 'FROGS'}` : `${n} ${n === 1 ? 'LISTING' : 'LISTINGS'}`;
          gtext(label, x + m.foot[0], y + m.foot[1], '#f2e7d4', 'body', { align: 'center' });
        }
        if (c.key === 'market') {
          const [tx, ty] = m.tag; rect(x + tx, y + ty, x + tx + 17, y + ty + 6, '#f0e8d2');
          text(prices[priceI], x + tx + 1, y + ty, '#b43c32', SMALL, null);
        }
      });
      // tiles
      L.tiles.forEach((tl) => {
        const hot = hover && hover.item === tl, down = press && press.item === tl && hot;
        const lift = down ? 1 : hot ? -2 : 0;
        const x = tl.x, y = tl.y + lift;
        if (hot) for (let xx = x - 1; xx <= x + tl.w; xx++) if (xx % 2) { px(xx, y - 2, rgb(tl.accent), 0.5); px(xx, y + tl.h + 1, rgb(tl.accent), 0.5); }
        g.drawImage(img['tile-' + tl.key], x, y);
        if (tl.key === 'casino') {
          const [rx, ry] = tl.meta.reels;
          for (let k = 0; k < 3; k++) {
            const spin = hot ? Math.floor(t * 12 + k * 3) : Math.floor(t * 0.6 + k * 2);
            rect(x + rx + k * 5, y + ry, x + rx + 3 + k * 5, y + ry + 7, '#f0ece0');
            text(reels[spin % reels.length], x + rx + k * 5, y + ry + 1, '#c8283c', SMALL, null);
          }
        }
        if (tl.key === 'boss') { const k = (Math.sin(t * 3) + 1) / 2; px(x + 19, y + 7, '#fffbe0', k); px(x + 12, y + 5, '#fffbe0', 1 - k); }
      });
      // ticker
      if (L.ticker) {
      const tr = L.ticker.rect;
      const n = Math.floor((tr[2] - tr[0]) / 2), off = Math.floor(tickerOff);
      for (let c = 0; c < n; c++) {
        const [col, color] = tick[(off + c) % tick.length];
        for (let r = 0; r < 5; r++) if (col[r]) { px(tr[0] + c * 2, tr[1] + 1 + r * 2, color); px(tr[0] + c * 2 + 1, tr[1] + 1 + r * 2, color, 0.25); }
      }
      }
      // toast
      if (toast) {
        const msg = toast.raw ? toast.text : toast.text + ' OPENS NEXT', w = tw(msg, SMALL) + 16, x0 = (W - w) >> 1, y0 = 68;
        const a = Math.min(1, toast.t * 3);
        g.globalAlpha = a;
        rect(x0, y0, x0 + w, y0 + 14, '#141216');
        rect(x0 + 1, y0 + 1, x0 + w - 1, y0 + 13, rgb(toast.accent));
        rect(x0 + 2, y0 + 2, x0 + w - 2, y0 + 12, '#1e1a24');
        g.globalAlpha = 1;
        text(msg, x0 + 8, y0 + 5, '#f2e7d4', SMALL);
      }
    }

    const ctx = {
      W, H, px, rect, text, gtext, gwidth, rnd, wallet, shared, D, blinkOf, canvas, live: LIVE,
      get g() { return g; }, __swap: (ng) => { g = ng; },
      get img() { return img; }, get L() { return L; }, get hover() { return hover; }, get press() { return press; },
      go: (n) => go(n), toast: (s, accent) => { toast = { text: s, t: 2.2, accent: accent || [240, 190, 80], raw: true }; },
    };
    let last = 0, raf = 0, acc = 0;
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function loop(now) {
      if (!running) return;
      const t = now / 1000, dt = Math.min(0.1, last ? t - last : 0.033); last = t; acc += dt;
      if (acc >= 1 / 30) { frame(reduce ? 0 : t, acc); acc = 0; }
      raf = requestAnimationFrame(loop);
    }

    (async () => {
      for (const [name, sc] of Object.entries(D.screens)) {
        IMGS[name] = {};
        for (const [k, v] of Object.entries(sc.images)) IMGS[name][k] = await load(v);
      }
      for (const [k, v] of Object.entries(D.shared)) shared[k] = await load(v);
      for (const m of Object.values(MODS)) if (m.init) await m.init(ctx, load);
      shared.frogBlink = blinkOf(shared.frogSprite);
      if (IMGS.home && IMGS.home.neon) {
        const c = document.createElement('canvas'); c.width = W; c.height = H;
        const x = c.getContext('2d'); x.drawImage(IMGS.home.neon, 0, 0);
        D.neonMask = x.getImageData(0, 0, W, H).data;
      }
      const start = (location.hash || '').slice(1);
      if (LIVE) {
        FTLive.toast = ctx.toast;
        FTLive.onLogout = () => go('login');
        const ok = await FTLive.boot();
        go(!ok ? 'login' : D.screens[start] && start !== 'login' ? start : 'home');
      } else go(D.screens[start] ? start : cur);
      canvas.addEventListener('mousemove', onMove);
      canvas.addEventListener('pointerdown', onDown);
      canvas.addEventListener('pointerup', onUp);
      canvas.addEventListener('mouseleave', onLeave);
      canvas.addEventListener('wheel', (e) => { if (mod && mod.wheel) { e.preventDefault(); mod.wheel(ctx, e.deltaY); } }, { passive: false });
      raf = requestAnimationFrame(loop);
    })();
    return { stop() { running = false; cancelAnimationFrame(raf); } };
  }
  window.HomeScene = { create };
})();
