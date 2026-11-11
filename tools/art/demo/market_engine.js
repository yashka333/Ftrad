/* Market screen (live game): Legendary and Mythic frogs only. BUY shows other players' listings,
 * SELL shows your own frogs that can be traded, MY LISTINGS lets you take one back. The fee is burned.
 * Registers window.FTScreens.market for HomeScene (count is read by the home card).
 */
(function () {
  'use strict';
  const KEYS = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic'];
  const RCOL = ['#c9cdd6', '#6ee06a', '#4aa8ff', '#b66fff', '#ffb42e', '#ff4d6d'];
  const TABS = { buy: 'BUY', sell: 'SELL', mine: 'MY LISTINGS' };
  const st = { tab: 'buy', sel: null, scroll: 0, listings: [], at: 0, busy: false, input: null, price: '' };
  const inBox = (b, x, y) => x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h;
  const fmt = (v) => Math.floor(v).toLocaleString('en-US');
  const compact = (v) => (v >= 1e6 ? (v / 1e6).toFixed(v >= 1e7 ? 0 : 1).replace('.0', '') + 'M' : v >= 1000 ? (v / 1000).toFixed(v >= 1e4 ? 0 : 1).replace('.0', '') + 'K' : String(v));
  let R = null;

  const me = () => (FTLive.player ? FTLive.player.id : -1);
  function items() {
    if (st.tab === 'buy') return st.listings.filter((l) => l.sellerId !== me()).map((l) => ({ kind: 'listing', l, f: l.frog }));
    if (st.tab === 'mine') return st.listings.filter((l) => l.sellerId === me()).map((l) => ({ kind: 'listing', l, f: l.frog }));
    return FTCrew.frogs.filter((f) => f.rarity >= R.market.minRarity).map((f) => ({ kind: 'own', f }));
  }
  const keyOf = (it) => (it.kind === 'listing' ? 'L' + it.l.id : 'F' + it.f.id);
  const selected = () => items().find((it) => keyOf(it) === st.sel) || null;
  function cell(L, i) {
    const gd = L.grid, row = Math.floor(i / gd.cols) - st.scroll, col = i % gd.cols;
    if (row < 0 || row >= gd.rows) return null;
    return { x: gd.x + col * (gd.w + gd.gap), y: gd.y + row * gd.pitch, w: gd.w, h: gd.h + 11 };
  }

  function load() {
    FTLive.market().then((d) => {
      st.listings = d.listings.map((l) => ({ ...l, frog: { ...l.frog, uid: 'L' + l.id, max: l.frog.maxStamina } }));
      mod.count = st.listings.length;
      st.at = Date.now();
    }).catch(() => {});
  }

  // ---- price field: a real text input laid over the canvas, so phones get their number keyboard
  function showInput(ctx, on) {
    if (!on) { if (st.input) st.input.style.display = 'none'; return; }
    if (!st.input) {
      const el = document.createElement('input');
      el.type = 'text'; el.inputMode = 'numeric'; el.placeholder = 'PRICE'; el.maxLength = 13; el.autocomplete = 'off';
      el.setAttribute('aria-label', 'Price in FROG');
      Object.assign(el.style, {
        position: 'fixed', zIndex: 5, border: '0', outline: 'none', padding: '0 6px', boxSizing: 'border-box',
        background: '#100d12', color: '#ffe282', fontFamily: 'monospace', fontWeight: '700', textAlign: 'right',
        boxShadow: 'inset 0 0 0 2px #6e5a2a',
      });
      el.addEventListener('input', () => { el.value = el.value.replace(/[^0-9]/g, ''); st.price = el.value; });
      el.addEventListener('keydown', (e) => { if (e.key === 'Enter') list(ctx); });
      document.body.appendChild(el);
      st.input = el;
    }
    const r = ctx.canvas.getBoundingClientRect(), k = r.width / ctx.W, b = ctx.L.price;
    Object.assign(st.input.style, {
      display: 'block', left: r.left + b.x * k + 'px', top: r.top + b.y * k + 'px',
      width: b.w * k + 'px', height: b.h * k + 'px', fontSize: Math.round(9 * k) + 'px',
    });
  }

  function list(ctx) {
    const it = selected(); if (!it || it.kind !== 'own' || st.busy) return;
    const price = Number(st.price);
    if (!price || price < R.market.minPrice) { ctx.toast(`SET A PRICE FROM ${fmt(R.market.minPrice)} $FROG`, [230, 70, 90]); return; }
    st.busy = true;
    FTLive.list(it.f.id, price).then(() => {
      ctx.toast(`LISTED FOR ${fmt(price)} $FROG`, [126, 224, 84]);
      st.price = ''; if (st.input) st.input.value = '';
      st.tab = 'mine'; st.sel = null; load();
    }).catch(() => {}).finally(() => { st.busy = false; });
  }

  const mod = {
    count: null,
    init(ctx) {
      R = ctx.D.cards.rules;
      // keep the home card's listing count fresh
      setInterval(() => { if (FTLive.logged && !document.hidden) load(); }, 30000);
      setTimeout(() => { if (FTLive.logged) load(); }, 1500);
    },
    enter() { st.sel = null; st.scroll = 0; load(); },
    leave() { showInput(null, false); },
    hit(ctx, x, y) {
      const L = ctx.L;
      for (const tb of L.tabs) if (inBox(tb, x, y)) return { key: 'tab', tab: tb.key };
      const all = items();
      for (let i = 0; i < all.length; i++) { const c = cell(L, i); if (c && inBox(c, x, y)) return { key: 'item', id: keyOf(all[i]) }; }
      const it = selected();
      if (it && inBox(L.button, x, y)) return { key: 'act' };
      return null;
    },
    click(ctx, it) {
      if (it.key === 'tab') { st.tab = it.tab; st.sel = null; st.scroll = 0; return; }
      if (it.key === 'item') { st.sel = it.id; return; }
      if (it.key !== 'act' || st.busy) return;
      const s = selected(); if (!s) return;
      if (st.tab === 'sell') { list(ctx); return; }
      st.busy = true;
      const p = st.tab === 'buy' ? FTLive.buy(s.l.id) : FTLive.cancel(s.l.id);
      p.then(() => {
        ctx.toast(st.tab === 'buy' ? `${s.f.name.toUpperCase()} JOINED YOUR CREW` : 'BACK IN YOUR CREW', [126, 224, 84]);
        st.sel = null; load();
      }).catch(() => load()).finally(() => { st.busy = false; });
    },
    wheel(ctx, dy) {
      const rows = Math.ceil(items().length / ctx.L.grid.cols);
      st.scroll = Math.max(0, Math.min(Math.max(0, rows - ctx.L.grid.rows), st.scroll + (dy > 0 ? 1 : -1)));
    },
    frame(ctx, t) {
      const L = ctx.L, g = ctx.g, img = ctx.img;
      const hov = ctx.hover && ctx.hover.kind === 'mod' ? ctx.hover.item : null;
      const down = ctx.press && ctx.press.kind === 'mod' ? ctx.press.item : null;
      if (st.at && Date.now() - st.at > 10000) { st.at = Date.now(); load(); }
      const all = items();
      if (st.sel === null && all.length) st.sel = keyOf(all[0]);

      for (const tb of L.tabs) {
        const on = st.tab === tb.key, h = hov && hov.key === 'tab' && hov.tab === tb.key;
        const n = tb.key === 'buy' ? st.listings.filter((l) => l.sellerId !== me()).length
          : tb.key === 'mine' ? st.listings.filter((l) => l.sellerId === me()).length
            : FTCrew.frogs.filter((f) => f.rarity >= R.market.minRarity).length;
        const y = tb.y + (on ? 0 : h ? -1 : 0);
        g.drawImage(img[on ? 'tab-on' : 'tab'], tb.x, y);
        ctx.gtext(`${TABS[tb.key]} ${n}`, tb.x + tb.w / 2, y + 4, on ? '#ffffff' : '#c8c0d0', 'body', { align: 'center' });
      }
      ctx.gtext('LEGENDARY AND MYTHIC ONLY', 630, 44, '#ffd66e', 'body', { align: 'right' });

      all.forEach((it, i) => {
        const c = cell(L, i); if (!c) return;
        const f = it.f, sel = keyOf(it) === st.sel, h = hov && hov.key === 'item' && hov.id === keyOf(it);
        const y = c.y + (h && !sel ? -1 : 0);
        g.drawImage(img['tile-' + KEYS[f.rarity]], c.x, y);
        const sp = FTCards.sprite(f.rarity, false), sx = Math.round((sp.width - 42) / 2);
        g.drawImage(sp, sx, 0, 42, 43, c.x + 4, y + 4, 42, 43);
        ctx.gtext(KEYS[f.rarity].slice(0, 4).toUpperCase(), c.x + 25, y + 53, RCOL[f.rarity], 'body', { align: 'center', shadow: null });
        const label = it.kind === 'listing' ? compact(it.l.price) : '#' + f.id;
        ctx.rect(c.x + 1, y + 64, c.x + c.w - 2, y + 73, '#141018');
        ctx.gtext(label, c.x + 25, y + 66, it.kind === 'listing' ? '#ffe282' : '#c8c0d0', 'body', { align: 'center', shadow: null });
        if (sel) {
          const on = Math.floor(t * 4) % 2 ? '#ffe282' : '#ecba48';
          ctx.rect(c.x - 1, y - 1, c.x + c.w, y - 1, on); ctx.rect(c.x - 1, y + 74, c.x + c.w, y + 74, on);
          ctx.rect(c.x - 1, y - 1, c.x - 1, y + 74, on); ctx.rect(c.x + c.w, y - 1, c.x + c.w, y + 74, on);
        }
      });
      if (!all.length) {
        const msg = st.tab === 'buy' ? ['NO FROGS ON SALE RIGHT NOW', 'LEGENDARY AND MYTHIC FROGS SHOW UP HERE']
          : st.tab === 'sell' ? ['YOU HAVE NO LEGENDARY OR MYTHIC FROGS', 'COMMON TO EPIC FROGS CANNOT BE TRADED']
            : ['YOU HAVE NOTHING LISTED', 'PICK A FROG IN SELL TO LIST IT'];
        msg.forEach((m, i) => ctx.gtext(m, 207, 190 + i * 12, i ? '#8a8096' : '#c8c0d0', 'body', { align: 'center' }));
      }

      const s = selected();
      showInput(ctx, !!(s && st.tab === 'sell'));
      if (!s) return;
      const f = s.f, ix = L.info.x, iy = L.info.y;
      FTCards.draw(ctx, f, L.card[0], L.card[1], { blink: ((t * 1000 + f.id * 397) % 3700) < 140 });
      ctx.gtext(KEYS[f.rarity].toUpperCase(), ix, iy, RCOL[f.rarity], 'head', { shadow: '#141216' });
      const rows = [
        ['PROFIT', `${compact(f.stats.profit)} /H`], ['PATIENCE', String(f.stats.patience)], ['RISK', f.stats.risk + '%'],
        ['WORKS', `${Math.round(f.shiftMinutes || 0)}M`], ['RESTS', `${Math.round((f.restMinutes || 0) / 60)}H`],
      ];
      rows.forEach(([a, b], i) => {
        ctx.gtext(a, ix, iy + 16 + i * 10, '#8a8096', 'body', { shadow: null });
        ctx.gtext(b, ix + 86, iy + 16 + i * 10, '#f2e7d4', 'body', { align: 'right', shadow: null });
      });
      const fee = R.market.feeRate;
      if (st.tab === 'sell') {
        ctx.gtext('YOUR PRICE', ix, L.price.y - 10, '#ffd66e', 'body', { shadow: null });
        const p = Number(st.price) || 0;
        if (p) ctx.gtext(`YOU GET ${compact(Math.floor(p * (1 - fee)))}`, ix, L.price.y + 22, '#7ee054', 'body', { shadow: null });
      } else {
        ctx.gtext('PRICE', ix, L.price.y - 10, '#8a8096', 'body', { shadow: null });
        ctx.gtext(fmt(s.l.price), ix + 86, L.price.y + 2, '#ffe282', 'title', { align: 'right', shadow: '#141216' });
        ctx.gtext(`BY ${s.l.sellerName.toUpperCase()}`, ix, L.price.y + 22, '#8a8096', 'body', { shadow: null });
      }
      const name = st.tab === 'buy' ? 'buy' : st.tab === 'sell' ? 'list' : 'cancel';
      const ok = !st.busy && (st.tab !== 'buy' || FTLive.wallet >= s.l.price);
      const b = L.button, h = ok && hov && hov.key === 'act', dn = ok && down && down.key === 'act';
      g.drawImage(img['btn-' + name + (ok ? '' : '-off')], b.x, b.y + (dn ? 1 : h ? -1 : 0));
      const [nx, ny] = L.notes;
      const notes = st.tab === 'buy'
        ? [`THE FROG JOINS YOUR CREW WITHOUT A DESK.`, ok ? `YOUR BALANCE: ${fmt(FTLive.wallet)} $FROG` : 'NOT ENOUGH $FROG FOR THIS FROG.']
        : st.tab === 'sell'
          ? [`A ${Math.round(fee * 100)}% FEE IS BURNED ON EVERY SALE.`, 'A LISTED FROG LEAVES ITS DESK AND YOUR CREW.', 'TAKE IT BACK ANY TIME IN MY LISTINGS.']
          : ['TAKE BACK RETURNS THE FROG TO YOUR CREW.', `A ${Math.round(fee * 100)}% FEE IS BURNED WHEN IT SELLS.`];
      notes.forEach((m, i) => ctx.gtext(m, nx, ny + i * 11, i === 1 && st.tab === 'buy' && !ok ? '#ff8a9a' : '#c8c0d0', 'body', { shadow: null }));
    },
  };
  window.FTScreens = window.FTScreens || {};
  window.FTScreens.market = mod;
})();
