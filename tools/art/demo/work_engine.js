/* Go to work screen: the three lit offices (OfficeScene in embedded mode) under the game header.
 * Frogs sit at the desks the player assigned. Click a desk to assign a frog or to send the one
 * sitting there to work, to the casino or off the desk. Tabs in the header switch offices.
 * Registers window.FTScreens.work for HomeScene. FTScreens.work.focus(path, desk) opens on a desk.
 */
(function () {
  'use strict';
  const KEYS = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic'];
  const RCOL = ['#c9cdd6', '#6ee06a', '#4aa8ff', '#b66fff', '#ffb42e', '#ff4d6d'];
  const NAME = { memecoin: 'MEMECOIN', pumpfun: 'PUMP.FUN', classic: 'CLASSIC' };
  const COL = { memecoin: '#ff9a52', pumpfun: '#f070f0', classic: '#5ee0c4' };
  const PW = 196, ROW = 22, ROWS = 4;
  const st = { room: 'memecoin', popup: null, scroll: 0, floats: [], earned: {}, focus: null };
  const scenes = {}, canvases = {};
  let OFF = 16;

  const inBox = (b, x, y) => x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h;
  const fmtMin = (m) => { m = Math.ceil(m); const h = Math.floor(m / 60), mm = m % 60; return h ? `${h}H ${mm}M` : `${mm}M`; };
  const compact = (v) => (v >= 1000 ? (v / 1000).toFixed(1).replace('.0', '') + 'K' : String(Math.round(v)));
  const scene = () => scenes[st.room];
  const layout = () => window.FT_OFFICES[st.room].layout;

  function deskBox(i) {
    const d = layout().desks[i];
    return { x: d.x - 4, y: d.frog[1] - 58 + OFF, w: 113, h: 103 };
  }
  function bossBox() { const c = layout().boss.chair; return { x: c[0], y: c[1] + OFF, w: c[2] - c[0] + 1, h: c[3] - c[1] + 1 }; }
  const freeFrogs = () => FTCrew.frogs.filter((f) => !f.desk)
    .sort((a, b) => (b.stamina >= 1) - (a.stamina >= 1) || b.rarity - a.rarity || b.stats.profit - a.stats.profit);

  /** Popup rectangle for the open desk. */
  function popupBox() {
    const p = st.popup; if (!p) return null;
    const h = FTCrew.holder(st.room, p.desk);
    const list = h ? null : freeFrogs();
    const ph = h ? 76 : 24 + Math.max(1, Math.min(ROWS, list.length)) * ROW + (list.length > ROWS ? 10 : 4);
    const b = deskBox(p.desk);
    const x = Math.max(4, Math.min(636 - PW, b.x + (b.w >> 1) - (PW >> 1)));
    return { x, y: b.y - ph - 2, w: PW, h: ph, holder: h, list };
  }
  function popupButtons(pb) {
    const f = pb.holder, x = pb.x + PW - 92;
    return [
      { key: 'work', x, y: pb.y + 6, w: 86, h: 18, ok: f.status !== 'working' && f.stamina >= 1 },
      { key: 'rest', x, y: pb.y + 28, w: 86, h: 18, ok: f.status !== 'casino' },
      { key: 'stop', x, y: pb.y + 50, w: 86, h: 18, ok: true },
    ];
  }

  function syncDesks() {
    const sc = scene(); if (!sc) return;
    for (let d = 0; d < FTCrew.DESKS; d++) {
      const h = FTCrew.holder(st.room, d);
      sc.setFrog(d, h && h.status !== 'casino' ? { rarity: KEYS[h.rarity], state: h.status === 'working' ? 'work' : 'ready' } : null);
    }
  }

  function frame(ctx, x, y, w, h, edge) {
    ctx.rect(x, y, x + w - 1, y + h - 1, '#0c0a0e');
    ctx.rect(x + 1, y + 1, x + w - 2, y + h - 2, edge);
    ctx.rect(x + 2, y + 2, x + w - 3, y + h - 3, '#1e1a24');
    ctx.rect(x + 2, y + 2, x + w - 3, y + 2, '#2c2632');
  }

  const mod = {
    async init(ctx) {
      OFF = ctx.D.screens.work.layout.offset;
      const sprites = ctx.D.cards.sprites;
      for (const [key, o] of Object.entries(window.FT_OFFICES)) {
        const images = Object.assign({}, o.images);
        for (const k of KEYS) images['frog-' + k] = sprites[k];
        const c = document.createElement('canvas');
        canvases[key] = c;
        scenes[key] = OfficeScene.create({ layout: o.layout, images, frogs: [] }, c, null, { embed: true });
        scenes[key].setBoss(false);
      }
    },
    focus(path, desk) { st.focus = { path, desk }; },
    enter() {
      st.popup = null; st.scroll = 0;
      if (st.focus) { st.room = st.focus.path; st.popup = { desk: st.focus.desk }; st.focus = null; }
    },

    hit(ctx, x, y) {
      const L = ctx.L;
      for (const t of L.tabs) if (inBox(t, x, y)) return { key: 'tab', room: t.key };
      for (const [k, b] of Object.entries(L.bottom)) if (inBox(b, x, y)) return { key: k };
      const pb = popupBox();
      if (pb) {
        if (inBox(pb, x, y)) {
          if (pb.holder) {
            for (const b of popupButtons(pb)) if (b.ok && inBox(b, x, y)) return { key: 'p-' + b.key };
            return { key: 'inside' };
          }
          const rows = pb.list.slice(st.scroll, st.scroll + ROWS);
          for (let i = 0; i < rows.length; i++) {
            if (inBox({ x: pb.x + 4, y: pb.y + 20 + i * ROW, w: PW - 8, h: ROW - 1 }, x, y)) return { key: 'pick', id: rows[i].id };
          }
          return { key: 'inside' };
        }
      }
      for (let i = 0; i < FTCrew.DESKS; i++) if (inBox(deskBox(i), x, y)) return { key: 'desk', desk: i };
      if (inBox(bossBox(), x, y)) return { key: 'boss' };
      return pb ? { key: 'bg' } : null;
    },
    click(ctx, it) {
      if (it.key === 'tab') { st.room = it.room; st.popup = null; st.floats = []; st.earned = {}; return; }
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
        ctx.toast(n ? `${n} ${n === 1 ? 'FROG' : 'FROGS'} WENT TO THE CASINO` : 'WORKING FROGS STAY, TIRED ONES ARE ALREADY THERE', n ? [255, 106, 168] : [230, 70, 90]);
        return;
      }
      if (it.key === 'boss') { ctx.go('boss'); return; }
      if (it.key === 'desk') { st.popup = st.popup && st.popup.desk === it.desk ? null : { desk: it.desk }; st.scroll = 0; return; }
      if (it.key === 'bg') { st.popup = null; return; }
      const pb = popupBox(); if (!pb) return;
      if (it.key === 'pick') {
        const f = FTCrew.frogs.find((x) => x.id === it.id);
        const err = f && FTCrew.assignDesk(f, st.room, st.popup.desk);
        if (err) ctx.toast(err, [230, 70, 90]);
        return;
      }
      const f = pb.holder; if (!f) return;
      if (it.key === 'p-work') FTCrew.startWork(f);
      if (it.key === 'p-rest') FTCrew.rest(f);
      if (it.key === 'p-stop') { FTCrew.stop(f); st.scroll = 0; }
    },
    wheel(ctx, dy) {
      const pb = popupBox(); if (!pb || pb.holder) return;
      st.scroll = Math.max(0, Math.min(Math.max(0, pb.list.length - ROWS), st.scroll + (dy > 0 ? 1 : -1)));
    },

    /** Drawn under the header: the lit office. */
    under(ctx, t, dt) {
      const sc = scene(); if (!sc) return;
      syncDesks();
      const hv = ctx.hover && ctx.hover.kind === 'mod' ? ctx.hover.item : null;
      sc.setHover(hv && hv.key === 'desk' ? hv.desk : hv && hv.key === 'boss' ? -1 : st.popup ? st.popup.desk : -2);
      sc.step(dt, t);
      ctx.g.fillStyle = '#000'; ctx.g.fillRect(0, 0, 640, 360);
      ctx.g.drawImage(canvases[st.room], 0, OFF);
    },

    frame(ctx, t, dt) {
      const L = ctx.L, img = ctx.img, g = ctx.g, lay = layout();
      const hov = ctx.hover && ctx.hover.kind === 'mod' ? ctx.hover.item : null;
      const down = ctx.press && ctx.press.kind === 'mod' ? ctx.press.item : null;

      // office tabs in the header
      for (const tb of L.tabs) {
        const on = st.room === tb.key, h = !on && hov && hov.key === 'tab' && hov.room === tb.key;
        const y = tb.y + (h ? -1 : 0);
        g.drawImage(img[on ? 'tab-' + tb.key : 'tab'], tb.x, y);
        const mine = FTCrew.frogs.filter((f) => f.desk && f.desk.path === tb.key);
        const work = mine.filter((f) => f.status === 'working').length;
        ctx.gtext(NAME[tb.key], tb.x + tb.w / 2, y + 5, on ? '#ffffff' : COL[tb.key], 'body', { align: 'center', shadow: '#141216' });
        ctx.gtext(`${mine.length}/5  ${work} WORK`, tb.x + tb.w / 2, y + 14, on ? '#fff4dc' : '#a8a0b4', 'body', { align: 'center', shadow: on ? '#141216' : null });
      }

      // live tags above the desks
      lay.desks.forEach((d, i) => {
        const f = FTCrew.holder(st.room, i), cx = d.frog[0], top = d.frog[1] - 64 + OFF;
        if (f && f.status === 'working') {
          const prev = st.earned[f.id] == null ? f.earned : st.earned[f.id];
          if (f.earned - prev >= 1 && Math.floor(t / 2.4) !== Math.floor((t - dt) / 2.4)) {
            st.floats.push({ room: st.room, x: (d.screen[0] + d.screen[2]) >> 1, y: d.screen[1] + OFF - 9, v: f.earned - prev, a: 1 });
            st.earned[f.id] = f.earned;
          } else if (st.earned[f.id] == null) st.earned[f.id] = f.earned;
        }
        if (f && f.status === 'ready') {
          const bob = Math.floor(t * 3) % 2;
          tag(ctx, 'READY', cx, top - bob, '#ffd66e', '#3a2c10');
        }
        if (f && f.status === 'casino') {
          tag(ctx, 'IN CASINO', cx, top + 16, '#ff6aa8', '#3a1426');
          ctx.gtext(`BACK IN ${fmtMin(FTCrew.etaMin(f))}`, cx, top + 30, '#f2c8da', 'body', { align: 'center', shadow: '#141216' });
        }
        if (!f && hov && hov.key === 'desk' && hov.desk === i && !st.popup) tag(ctx, '+ ASSIGN', cx, top + 16, '#7ee054', '#16301a');
      });
      for (const p of st.floats) {
        p.y -= dt * 9; p.a -= dt * 0.45;
        if (p.a > 0) ctx.gtext('+' + compact(p.v), p.x, p.y | 0, p.a > 0.3 ? '#ffe282' : '#b89a4a', 'body', { align: 'center', shadow: '#141216' });
      }
      st.floats = st.floats.filter((p) => p.a > 0 && p.room === st.room);

      // floor bar
      for (const [k, b] of Object.entries(L.bottom)) {
        const h = hov && hov.key === k, d = down && down.key === k;
        g.drawImage(img['btn-' + k], b.x, b.y + (d ? 1 : h ? -1 : 0));
      }
      const here = FTCrew.frogs.filter((f) => f.desk && f.desk.path === st.room);
      const rate = here.reduce((s, f) => s + FTCrew.ratePerHour(f), 0);
      ctx.gtext(`${NAME[st.room]} +${compact(rate)} $FROG/H`, 632, 342, '#ffe282', 'body', { align: 'right', shadow: '#141216' });
      ctx.gtext((FTCrew.live ? '' : 'DEMO TIME X60'), 632, 351, '#9a90a6', 'body', { align: 'right', shadow: '#141216' });

      // desk popup
      const pb = popupBox();
      if (!pb) return;
      const d = lay.desks[st.popup.desk], tipX = Math.max(pb.x + 8, Math.min(pb.x + PW - 9, d.frog[0]));
      frame(ctx, pb.x, pb.y, pb.w, pb.h, '#ecba48');
      ctx.rect(tipX - 3, pb.y + pb.h - 1, tipX + 3, pb.y + pb.h - 1, '#ecba48');
      ctx.rect(tipX - 2, pb.y + pb.h, tipX + 2, pb.y + pb.h, '#ecba48');
      ctx.rect(tipX - 1, pb.y + pb.h + 1, tipX + 1, pb.y + pb.h + 1, '#ecba48');
      const x0 = pb.x + 8, y0 = pb.y;
      if (pb.holder) {
        const f = pb.holder, frac = f.stamina / f.max;
        ctx.gtext(f.name.toUpperCase(), x0, y0 + 7, '#f2e7d4', 'head', { shadow: '#141216' });
        ctx.gtext(`#${f.id} ${KEYS[f.rarity].toUpperCase()}`, x0, y0 + 19, RCOL[f.rarity], 'body', { shadow: null });
        const line = f.status === 'working' ? [`+${compact(FTCrew.ratePerHour(f))} $FROG/H`, '#7ee054']
          : f.status === 'ready' ? ['READY AT DESK ' + (st.popup.desk + 1), '#ffd66e'] : ['IN CASINO', '#ff6aa8'];
        ctx.gtext(line[0], x0, y0 + 31, line[1], 'body', { shadow: null });
        ctx.rect(x0, y0 + 42, x0 + 87, y0 + 47, '#0c0a0e');
        ctx.rect(x0 + 1, y0 + 43, x0 + 1 + Math.round(85 * frac), y0 + 46, f.status === 'casino' ? '#ff6aa8' : f.status === 'working' ? '#7ee054' : '#ffd66e');
        const tt = f.status === 'working' ? `TIRED IN ${fmtMin(FTCrew.etaMin(f))}` : f.status === 'casino' ? `RESTED IN ${fmtMin(FTCrew.etaMin(f))}` : 'FULLY RESTED';
        ctx.gtext(tt, x0, y0 + 52, '#c8c0d0', 'body', { shadow: null });
        ctx.gtext('STAMINA', x0, y0 + 62, '#6d6475', 'body', { shadow: null });
        for (const b of popupButtons(pb)) {
          const h = b.ok && hov && hov.key === 'p-' + b.key, dn = b.ok && down && down.key === 'p-' + b.key;
          g.drawImage(img['btn-' + b.key + (b.ok ? '' : '-off')], b.x, b.y + (dn ? 1 : h ? -1 : 0));
        }
        return;
      }
      ctx.gtext(`DESK ${st.popup.desk + 1}: PICK A FROG`, x0, y0 + 7, '#ffe282', 'body', { shadow: '#141216' });
      if (!pb.list.length) {
        ctx.gtext('EVERY FROG HAS A DESK', x0, y0 + 26, '#c8c0d0', 'body', { shadow: null });
        return;
      }
      pb.list.slice(st.scroll, st.scroll + ROWS).forEach((f, i) => {
        const ry = y0 + 20 + i * ROW, h = hov && hov.key === 'pick' && hov.id === f.id;
        ctx.rect(pb.x + 4, ry, pb.x + PW - 5, ry + ROW - 2, h ? '#3a3046' : '#27212e');
        const sp = FTCards.sprite(f.rarity, false), sx = Math.round((sp.width - 40) / 2);
        ctx.rect(pb.x + 6, ry + 1, pb.x + 25, ry + ROW - 3, '#141018');
        g.drawImage(sp, sx, 2, 40, 36, pb.x + 6, ry + 1, 20, 18);
        ctx.gtext(f.name.toUpperCase(), pb.x + 30, ry + 4, '#f2e7d4', 'body', { shadow: null });
        ctx.gtext(KEYS[f.rarity].toUpperCase(), pb.x + 30, ry + 12, RCOL[f.rarity], 'body', { shadow: null });
        const rested = f.status !== 'casino';
        ctx.gtext(rested ? `${compact(f.stats.profit)}/H` : 'IN CASINO', pb.x + PW - 10, ry + 8, rested ? '#ffe282' : '#ff6aa8', 'body', { align: 'right', shadow: null });
      });
      if (pb.list.length > ROWS) {
        ctx.gtext(`${st.scroll + 1}-${Math.min(pb.list.length, st.scroll + ROWS)} OF ${pb.list.length}  SCROLL FOR MORE`, pb.x + PW / 2, y0 + pb.h - 9, '#8a8096', 'body', { align: 'center', shadow: null });
      }
    },
  };

  function tag(ctx, s, cx, y, col, bg) {
    const w = ctx.gwidth(s, 'body') + 8, x = Math.round(cx - w / 2);
    ctx.rect(x, y, x + w - 1, y + 10, '#0c0a0e');
    ctx.rect(x + 1, y + 1, x + w - 2, y + 9, bg);
    ctx.rect(x + 1, y + 1, x + w - 2, y + 1, col);
    ctx.gtext(s, cx, y + 3, col, 'body', { align: 'center', shadow: null });
  }

  window.FTScreens = window.FTScreens || {};
  window.FTScreens.work = mod;
})();
