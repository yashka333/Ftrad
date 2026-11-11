/* Frogs screen: the crew roster (portrait grid with filters), the picked frog's card,
 * live status, All to work / All to casino, and per frog Assign desk / Work / Rest / Unassign / View office.
 * Registers window.FTScreens.frogs for HomeScene.
 */
(function () {
  'use strict';
  const KEYS = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic'];
  const STATUS = {
    working: { label: 'WORKING', short: 'WORK', col: '#7ee054' },
    casino: { label: 'IN CASINO', short: 'CASINO', col: '#ff6aa8' },
    ready: { label: 'READY', short: 'READY', col: '#ffd66e' },
    idle: { label: 'IDLE', short: 'IDLE', col: '#a8a0b4' },
  };
  const OFFICE = { memecoin: 'MEMECOIN', pumpfun: 'PUMP.FUN', classic: 'CLASSIC' };
  const OFFICE_COL = { memecoin: '#ff9a52', pumpfun: '#f070f0', classic: '#5ee0c4' };
  const SHORT = {
    diamondHands: 'Shifts 20% longer', powerNap: 'Rests 15% faster', fastFingers: 'Walks 50% faster',
    caffeine: '+30% profit, first 10 min', stopLoss: 'Half the empty trades', hotStreak: 'Up to +18% on a streak',
    dipBuyer: '+50% profit on dips', degenMode: '+20% profit, +5% risk', luckyCharm: '+5% chance of x2',
    copyTrader: '+3% per frog in office', nightOwl: '+15% profit at night', whaleHunter: '+50% during pumps',
    rugRadar: 'Rugs never wipe its trades', insider: '5% chance of x3',
  };
  const ORDER = { working: 0, casino: 1, ready: 2, idle: 3 };
  const st = { tab: 'all', scroll: 0, sel: null, picking: false };
  let R = null;

  const inBox = (b, x, y) => x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h;
  const fmtMin = (m) => { m = Math.ceil(m); const h = Math.floor(m / 60), mm = m % 60; return h ? `${h}H ${mm}M` : `${mm}M`; };
  const compact = (v) => (v >= 1000 ? (v / 1000).toFixed(1).replace('.0', '') + 'K' : String(Math.round(v)));

  function list() {
    const all = FTCrew.frogs.filter((f) => st.tab === 'all' || f.status === st.tab);
    return all.sort((a, b) => ORDER[a.status] - ORDER[b.status] || b.rarity - a.rarity || b.stats.profit - a.stats.profit);
  }
  function cell(L, i) {
    const gd = L.grid, row = Math.floor(i / gd.cols) - st.scroll, col = i % gd.cols;
    if (row < 0 || row >= gd.rows) return null;
    return { x: gd.x + col * (gd.w + gd.gap), y: gd.y + row * (gd.h + gd.gap), w: gd.w, h: gd.h };
  }
  const selected = () => FTCrew.frogs.find((f) => f.id === st.sel) || null;

  function slot(L, i, d) {
    const p = L.picker;
    return { x: p.x + p.label + d * (p.w + p.gap), y: p.y + i * p.row, w: p.w, h: p.h };
  }

  function can(f, key) {
    if (!f) return false;
    if (key === 'assign') return true;
    if (key === 'work') return f.status !== 'working' && f.stamina >= 1;
    if (key === 'rest') return f.status !== 'casino';
    if (key === 'stop') return !!f.desk;
    if (key === 'view') return !!f.desk;
    return false;
  }

  const mod = {
    init(ctx) { R = ctx.D.cards.rules; FTCrew.init(R); },
    enter() { st.picking = false; },

    hit(ctx, x, y) {
      const L = ctx.L;
      for (const [k, b] of Object.entries(L.global)) if (inBox(b, x, y)) return { key: k };
      for (const t of L.tabs) if (inBox(t, x, y)) return { key: 'tab', tab: t.key };
      const items = list();
      for (let i = 0; i < items.length; i++) { const c = cell(L, i); if (c && inBox(c, x, y)) return { key: 'frog', id: items[i].id }; }
      const f = selected();
      if (f) {
        for (const [k, b] of Object.entries(L.buttons)) if (inBox(b, x, y) && can(f, k)) return { key: k };
        if (st.picking) {
          const paths = L.picker.paths;
          for (let i = 0; i < paths.length; i++) for (let d = 0; d < FTCrew.DESKS; d++) {
            if (inBox(slot(L, i, d), x, y)) return { key: 'slot', path: paths[i], desk: d };
          }
        }
      }
      return null;
    },
    click(ctx, it) {
      const f = selected();
      if (it.key === 'allwork') {
        const n = FTCrew.allToWork();
        if (n) ctx.toast(`${n} ${n === 1 ? 'FROG' : 'FROGS'} WENT TO WORK`, [126, 224, 84]);
        else {
          const desks = FTCrew.frogs.filter((x) => x.desk).length;
          ctx.toast(desks >= 15 ? 'ALL 15 DESKS ARE BUSY' : 'NO RESTED FROGS: THEY ARE CHILLING IN THE CASINO', [230, 70, 90]);
        }
        return;
      }
      if (it.key === 'allrest') {
        const n = FTCrew.allToCasino();
        ctx.toast(n ? `${n} ${n === 1 ? 'FROG' : 'FROGS'} WENT TO THE CASINO` : 'EVERYONE IS RESTED OR RESTING', n ? [255, 106, 168] : [230, 70, 90]);
        return;
      }
      if (it.key === 'tab') { st.tab = it.tab; st.scroll = 0; return; }
      if (it.key === 'frog') { st.sel = it.id; st.picking = false; return; }
      if (!f) return;
      if (it.key === 'assign') { st.picking = st.picking === 'assign' ? false : 'assign'; return; }
      if (it.key === 'work') {
        if (f.desk) { FTCrew.startWork(f); st.picking = false; return; }
        st.picking = st.picking === 'work' ? false : 'work'; return;
      }
      if (it.key === 'rest') { FTCrew.rest(f); st.picking = false; return; }
      if (it.key === 'stop') { FTCrew.stop(f); st.picking = false; return; }
      if (it.key === 'view') { FTScreens.work.focus(f.desk.path, f.desk.desk); ctx.go('work'); return; }
      if (it.key === 'slot') {
        const err = FTCrew.assignDesk(f, it.path, it.desk);
        if (err) { ctx.toast(err, [230, 70, 90]); return; }
        if (st.picking === 'work') FTCrew.startWork(f);
        st.picking = false;
      }
    },
    wheel(ctx, dy) {
      const gd = ctx.L.grid, rows = Math.ceil(list().length / gd.cols);
      st.scroll = Math.max(0, Math.min(Math.max(0, rows - gd.rows), st.scroll + (dy > 0 ? 1 : -1)));
    },

    frame(ctx, t) {
      const L = ctx.L, img = ctx.img, g = ctx.g;
      const hov = ctx.hover && ctx.hover.kind === 'mod' ? ctx.hover.item : null;
      const down = ctx.press && ctx.press.kind === 'mod' ? ctx.press.item : null;
      const crew = FTCrew.frogs;
      if (st.sel === null && crew.length) st.sel = list()[0] ? list()[0].id : crew[0].id;

      // tabs with live counts
      for (const tb of L.tabs) {
        const on = st.tab === tb.key, h = hov && hov.key === 'tab' && hov.tab === tb.key;
        const n = tb.key === 'all' ? crew.length : crew.filter((f) => f.status === tb.key).length;
        const y = tb.y + (on ? 0 : h ? -1 : 0);
        g.drawImage(img[on ? 'tab-on' : 'tab'], tb.x, y);
        ctx.gtext(`${tb.label} ${n}`, tb.x + tb.w / 2, y + 4, on ? '#ffffff' : '#c8c0d0', 'body', { align: 'center' });
      }
      for (const [k, b] of Object.entries(L.global)) {
        const h = hov && hov.key === k, d = down && down.key === k;
        g.drawImage(img['btn-' + k], b.x, b.y + (d ? 1 : h ? -1 : 0));
      }
      const seated = crew.filter((f) => f.desk).length, ft = L.footer;
      ctx.gtext(`DESKS ${seated}/15`, ft.x0, ft.y, '#f2e7d4', 'body', { shadow: '#141216' });
      ctx.gtext((FTCrew.live ? '' : 'DEMO TIME X60'), ft.x1, ft.y, '#7a7086', 'body', { align: 'right', shadow: null });

      // portrait grid
      const items = list();
      items.forEach((f, i) => {
        const c = cell(L, i); if (!c) return;
        const isSel = f.id === st.sel, h = hov && hov.key === 'frog' && hov.id === f.id;
        const y = c.y + (h && !isSel ? -1 : 0);
        g.drawImage(img['tile-' + KEYS[f.rarity]], c.x, y);
        const sp = FTCards.sprite(f.rarity, ((t * 1000 + f.id * 331) % 4100) < 130);
        const sx = Math.round((sp.width - 42) / 2);
        g.drawImage(sp, sx, 0, 42, 43, c.x + 4, y + 4, 42, 43);
        const s = STATUS[f.status];
        const frac = f.max ? f.stamina / f.max : 0;
        ctx.rect(c.x + 5, y + 50, c.x + 44, y + 51, '#141216');
        ctx.rect(c.x + 5, y + 50, c.x + 5 + Math.round(39 * frac), y + 51, s.col);
        ctx.gtext(s.short, c.x + 25, y + 54, s.col, 'body', { align: 'center', shadow: null });
        if (f.status === 'working' && Math.floor(t * 2 + f.id) % 2) ctx.px(c.x + 44, y + 6, '#7ee054');
        if (isSel) {
          const on = Math.floor(t * 4) % 2 ? '#ffe282' : '#ecba48';
          for (let k = 0; k < 2; k++) {
            ctx.rect(c.x - 1 - k, y - 1 - k, c.x + c.w + k, y - 1 - k, on);
            ctx.rect(c.x - 1 - k, y + c.h + k, c.x + c.w + k, y + c.h + k, on);
            ctx.rect(c.x - 1 - k, y - 1 - k, c.x - 1 - k, y + c.h + k, on);
            ctx.rect(c.x + c.w + k, y - 1 - k, c.x + c.w + k, y + c.h + k, on);
          }
        }
      });
      if (!items.length) ctx.gtext(st.tab === 'all' ? 'NO FROGS YET: OPEN A PACK IN THE SHOP' : 'NO FROGS HERE', 200, 196, '#a8a0b4', 'body', { align: 'center' });
      // scrollbar
      const gd = L.grid, rows = Math.ceil(items.length / gd.cols);
      if (rows > gd.rows) {
        const [sx0, sy0, sx1, sy1] = gd.scroll, span = sy1 - sy0;
        const th = Math.max(14, Math.round(span * gd.rows / rows)), ty = sy0 + Math.round((span - th) * st.scroll / (rows - gd.rows));
        ctx.rect(sx0, ty, sx1, ty + th, '#8a7f96');
        ctx.rect(sx0, ty, sx1, ty, '#b4aac0');
      }

      // picked frog
      const f = selected();
      if (!f) return;
      FTCards.draw(ctx, f, L.card[0], L.card[1], { blink: ((t * 1000 + f.id * 397) % 3700) < 140 });
      const ix = L.info.x, rw = L.rows, s = STATUS[f.status];
      ctx.gtext(s.label, ix, rw.status, s.col, 'head', { shadow: '#141216' });
      if (f.status === 'working') ctx.gtext(`+${compact(FTCrew.ratePerHour(f))} $FROG/H`, ix, rw.rate, '#ffe282', 'body', { shadow: null });
      ctx.gtext(f.desk ? `${OFFICE[f.desk.path]} DESK ${f.desk.desk + 1}` : 'NO DESK', ix, rw.desk, f.desk ? '#f2e7d4' : '#8a8096', 'body', { shadow: null });
      const [bx0, by0, bx1, by1] = rw.bar, frac = f.stamina / f.max;
      ctx.rect(bx0, by0, bx0 + Math.round((bx1 - bx0) * frac), by1, s.col);
      const eta = FTCrew.etaMin(f);
      const ttxt = f.status === 'working' ? `TIRED IN ${fmtMin(eta)}` : f.status === 'casino' ? `RESTED IN ${fmtMin(eta)}` : 'FULLY RESTED';
      ctx.gtext(ttxt, ix, rw.time, '#c8c0d0', 'body', { shadow: null });

      for (const [k, b] of Object.entries(L.buttons)) {
        const ok = can(f, k), h = ok && hov && hov.key === k, d = ok && down && down.key === k;
        const y = b.y + (d ? 1 : h ? -1 : 0);
        g.drawImage(img['btn-' + k + (ok ? '' : '-off')], b.x, y);
        if (st.picking === k) ctx.rect(b.x + 2, y + b.h, b.x + b.w - 3, y + b.h, '#ffe282');
      }

      // office picker or skills list under the card
      const sk = L.skills;
      ctx.rect(sk.x, sk.y - 12, sk.x + sk.w, sk.y - 6, '#1a161e');
      if (st.picking) {
        const pk = L.picker;
        const hs = hov && hov.key === 'slot' ? hov : null, hh = hs ? FTCrew.holder(hs.path, hs.desk) : null;
        ctx.gtext(st.picking === 'work' ? 'PICK A DESK TO WORK AT' : 'PICK A DESK', sk.x, sk.y - 12, '#ffe282', 'body', { shadow: null });
        if (hs) {
          const txt = hh ? (hh === f ? 'HERE NOW' : `#${hh.id} ${hh.name.toUpperCase()}`) : `${OFFICE[hs.path]} ${hs.desk + 1}`;
          ctx.gtext(txt, sk.x + sk.w, sk.y - 12, hh && hh !== f ? '#ff8a9a' : '#c8c0d0', 'body', { align: 'right', shadow: null });
        }
        pk.paths.forEach((path, i) => {
          const ry = pk.y + i * pk.row;
          ctx.gtext(OFFICE[path], pk.x, ry + 3, OFFICE_COL[path], 'body', { shadow: '#141216' });
          ctx.gtext(`${FTCrew.freeDesks(path)} FREE`, pk.x, ry + 12, '#8a8096', 'body', { shadow: null });
          for (let d = 0; d < FTCrew.DESKS; d++) {
            const c = slot(L, i, d), h = FTCrew.holder(path, d), over = hs && hs.path === path && hs.desk === d;
            g.drawImage(img.slot, c.x, c.y);
            if (h) {
              ctx.rect(c.x + 1, c.y + 1, c.x + c.w - 2, c.y + c.h - 2, '#1c1822');
              const sp = FTCards.sprite(h.rarity, false), sx = Math.round((sp.width - 40) / 2);
              g.drawImage(sp, sx, 2, 40, 36, c.x + 2, c.y + 1, 20, 18);
              ctx.rect(c.x + c.w - 4, c.y + 2, c.x + c.w - 3, c.y + 3, STATUS[h.status].col);
            }
            const mine = h === f;
            const edge = mine ? (Math.floor(t * 4) % 2 ? '#ffe282' : '#ecba48') : over ? (h ? '#e6465a' : '#ffe282') : null;
            if (edge) {
              ctx.rect(c.x, c.y, c.x + c.w - 1, c.y, edge); ctx.rect(c.x, c.y + c.h - 1, c.x + c.w - 1, c.y + c.h - 1, edge);
              ctx.rect(c.x, c.y, c.x, c.y + c.h - 1, edge); ctx.rect(c.x + c.w - 1, c.y, c.x + c.w - 1, c.y + c.h - 1, edge);
            }
          }
        });
      } else {
        ctx.gtext('SKILLS', sk.x, sk.y - 12, '#82788a', 'body', { shadow: null });
        if (!f.skills.length) ctx.gtext('NO SKILLS', sk.x, sk.y, '#6d6475', 'body', { shadow: null });
        f.skills.forEach((id, i) => {
          const y = sk.y + i * 19;
          FTCards.icon(ctx, 'skill-' + id, sk.x, y);
          ctx.gtext(R.skills[id].name.toUpperCase(), sk.x + 20, y, '#ffd66e', 'body', { shadow: null });
          ctx.gtext(SHORT[id] || '', sk.x + 20, y + 9, '#b0a6bc', 'body', { shadow: null });
        });
      }
    },
  };

  window.FTScreens = window.FTScreens || {};
  window.FTScreens.frogs = mod;
})();
