/* Casino screen: the free Lucky Frog Casino. Tired frogs chill here until they are rested.
 * Frogs take the seats in the order they arrive (card table, bar, sofa, then the armchairs where they doze);
 * the rest are counted as in the lounge. Click a frog to see its rest time or send it back to its desk.
 * Registers window.FTScreens.casino for HomeScene.
 */
(function () {
  'use strict';
  const KEYS = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic'];
  const RCOL = ['#c9cdd6', '#6ee06a', '#4aa8ff', '#b66fff', '#ffb42e', '#ff4d6d'];
  const NAME = { memecoin: 'MEMECOIN', pumpfun: 'PUMP.FUN', classic: 'CLASSIC' };
  const PW = 196, PH = 76;
  const st = { order: [], popup: null };
  let sc = null, cv = null, OFF = 16, L0 = null;

  const inBox = (b, x, y) => x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h;
  const fmtMin = (m) => { m = Math.ceil(m); const h = Math.floor(m / 60), mm = m % 60; return h ? `${h}H ${mm}M` : `${mm}M`; };
  const seats = () => L0.desks;

  /** Casino frogs in arrival order; seat i holds order[i]. */
  function syncOrder() {
    const inside = new Set(FTCrew.frogs.filter((f) => f.status === 'casino').map((f) => f.id));
    st.order = st.order.filter((id) => inside.has(id));
    for (const f of FTCrew.frogs) if (inside.has(f.id) && !st.order.includes(f.id)) st.order.push(f.id);
  }
  const byId = (id) => FTCrew.frogs.find((f) => f.id === id) || null;
  const seated = (i) => (i < st.order.length ? byId(st.order[i]) : null);
  function seatBox(i) {
    const s = seats()[i];
    return { x: s.frog[0] - 24, y: s.frog[1] - 52 + OFF, w: 48, h: s.clip - s.frog[1] + 54 };
  }
  function popupBox() {
    if (!st.popup) return null;
    const f = byId(st.popup.id);
    const i = st.order.indexOf(st.popup.id);
    if (!f || i < 0 || i >= seats().length) return null;
    const b = seatBox(i);
    const x = Math.max(4, Math.min(636 - PW, b.x + (b.w >> 1) - (PW >> 1)));
    const above = b.y - PH - 4 >= 40;
    return { x, y: above ? b.y - PH - 4 : b.y + b.h + 4, w: PW, h: PH, f, seat: i, above };
  }
  function popupButtons(pb) {
    const x = pb.x + PW - 92, f = pb.f;
    return [
      { key: 'work', x, y: pb.y + 28, w: 86, h: 18, ok: !!f.desk && f.stamina >= 1 },
      { key: 'stop', x, y: pb.y + 50, w: 86, h: 18, ok: !!f.desk },
    ];
  }

  function tag(ctx, s, cx, y, col, bg) {
    const w = ctx.gwidth(s, 'body') + 8, x = Math.round(cx - w / 2);
    ctx.rect(x, y, x + w - 1, y + 10, '#0c0a0e');
    ctx.rect(x + 1, y + 1, x + w - 2, y + 9, bg);
    ctx.rect(x + 1, y + 1, x + w - 2, y + 1, col);
    ctx.gtext(s, cx, y + 3, col, 'body', { align: 'center', shadow: null });
  }

  const mod = {
    async init(ctx) {
      OFF = ctx.D.screens.casino.layout.offset;
      L0 = window.FT_CASINO.layout;
      const images = Object.assign({}, window.FT_CASINO.images);
      for (const k of KEYS) images['frog-' + k] = ctx.D.cards.sprites[k];
      cv = document.createElement('canvas');
      sc = OfficeScene.create({ layout: L0, images, frogs: [] }, cv, null, { embed: true });
    },
    enter() { st.popup = null; },

    hit(ctx, x, y) {
      const pb = popupBox();
      if (pb && inBox(pb, x, y)) {
        for (const b of popupButtons(pb)) if (b.ok && inBox(b, x, y)) return { key: 'p-' + b.key };
        return { key: 'inside' };
      }
      for (let i = 0; i < seats().length; i++) if (seated(i) && inBox(seatBox(i), x, y)) return { key: 'frog', id: seated(i).id };
      return pb ? { key: 'bg' } : null;
    },
    click(ctx, it) {
      if (it.key === 'frog') { st.popup = st.popup && st.popup.id === it.id ? null : { id: it.id }; return; }
      if (it.key === 'bg') { st.popup = null; return; }
      const pb = popupBox(); if (!pb) return;
      if (it.key === 'p-work') {
        FTCrew.startWork(pb.f);
        ctx.toast(`${pb.f.name.toUpperCase()} WENT BACK TO ${NAME[pb.f.desk.path]}`, [126, 224, 84]);
        st.popup = null;
      }
      if (it.key === 'p-stop') FTCrew.stop(pb.f);
    },

    under(ctx, t, dt) {
      if (!sc) return;
      syncOrder();
      seats().forEach((s, i) => {
        const f = seated(i);
        sc.setFrog(i, f ? { rarity: KEYS[f.rarity], state: s.kind === 'armchair' ? 'sleep' : 'chill' } : null);
      });
      const hv = ctx.hover && ctx.hover.kind === 'mod' ? ctx.hover.item : null;
      const hi = hv && hv.key === 'frog' ? st.order.indexOf(hv.id) : st.popup ? st.order.indexOf(st.popup.id) : -1;
      sc.setHover(hi >= 0 && hi < seats().length ? hi : -2);
      sc.step(dt, t);
      ctx.g.fillStyle = '#000'; ctx.g.fillRect(0, 0, 640, 360);
      ctx.g.drawImage(cv, 0, OFF);
    },

    frame(ctx, t) {
      const g = ctx.g, img = ctx.img;
      const hov = ctx.hover && ctx.hover.kind === 'mod' ? ctx.hover.item : null;
      const down = ctx.press && ctx.press.kind === 'mod' ? ctx.press.item : null;
      const inside = st.order.map(byId).filter(Boolean);

      // rest timers over every seated frog
      seats().forEach((s, i) => {
        const f = seated(i); if (!f) return;
        const top = s.frog[1] - 64 + OFF + (s.kind === 'bar' ? -2 : 0);
        const frac = f.stamina / f.max;
        const x0 = s.frog[0] - 14;
        ctx.rect(x0 - 1, top + 11, x0 + 28, top + 14, '#0c0a0e');
        ctx.rect(x0, top + 12, x0 + Math.round(27 * frac), top + 13, '#ff6aa8');
        ctx.gtext(fmtMin(FTCrew.etaMin(f)), s.frog[0], top + 3, '#f2c8da', 'body', { align: 'center', shadow: '#141216' });
      });

      // footer
      const extra = Math.max(0, inside.length - seats().length);
      const next = inside.reduce((m, f) => Math.min(m, FTCrew.etaMin(f)), Infinity);
      ctx.gtext('FREE ENTRY. TIRED FROGS CHILL HERE UNTIL THEY ARE RESTED', 8, 345, '#f2e7d4', 'body', { shadow: '#141216' });
      ctx.gtext(inside.length ? `${inside.length} CHILLING${extra ? `, ${extra} IN THE LOUNGE` : ''}` : 'NOBODY HERE RIGHT NOW', 632, 336, '#ff8ac0', 'body', { align: 'right', shadow: '#141216' });
      if (inside.length) ctx.gtext(`NEXT RESTED IN ${fmtMin(next)}`, 632, 345, '#ffe282', 'body', { align: 'right', shadow: '#141216' });
      ctx.gtext((FTCrew.live ? '' : 'DEMO TIME X60'), 632, 354, '#9a90a6', 'body', { align: 'right', shadow: '#141216' });
      if (extra) tag(ctx, `+${extra} MORE IN THE LOUNGE`, 320, 202 + OFF, '#ff8ac0', '#3a1426');

      // popup
      const pb = popupBox();
      if (!pb) return;
      const f = pb.f, frac = f.stamina / f.max;
      ctx.rect(pb.x, pb.y, pb.x + pb.w - 1, pb.y + pb.h - 1, '#0c0a0e');
      ctx.rect(pb.x + 1, pb.y + 1, pb.x + pb.w - 2, pb.y + pb.h - 2, '#ff6aa8');
      ctx.rect(pb.x + 2, pb.y + 2, pb.x + pb.w - 3, pb.y + pb.h - 3, '#1e1a24');
      const tipX = Math.max(pb.x + 8, Math.min(pb.x + PW - 9, seats()[pb.seat].frog[0]));
      const ty = pb.above ? pb.y + pb.h : pb.y - 1, dir = pb.above ? 1 : -1;
      for (let k = 0; k < 3; k++) ctx.rect(tipX - 3 + k, ty + dir * k, tipX + 3 - k, ty + dir * k, '#ff6aa8');
      const x0 = pb.x + 8, y0 = pb.y;
      ctx.gtext(f.name.toUpperCase(), x0, y0 + 7, '#f2e7d4', 'head', { shadow: '#141216' });
      ctx.gtext(`#${f.id} ${KEYS[f.rarity].toUpperCase()}`, x0, y0 + 19, RCOL[f.rarity], 'body', { shadow: null });
      ctx.gtext('CHILLING', pb.x + PW - 10, y0 + 9, '#ff8ac0', 'body', { align: 'right', shadow: null });
      ctx.gtext(f.desk ? `DESK: ${NAME[f.desk.path]} ${f.desk.desk + 1}` : 'NO DESK', x0, y0 + 31, f.desk ? '#c8c0d0' : '#8a8096', 'body', { shadow: null });
      ctx.rect(x0, y0 + 42, x0 + 87, y0 + 47, '#0c0a0e');
      ctx.rect(x0 + 1, y0 + 43, x0 + 1 + Math.round(85 * frac), y0 + 46, '#ff6aa8');
      ctx.gtext(`RESTED IN ${fmtMin(FTCrew.etaMin(f))}`, x0, y0 + 52, '#c8c0d0', 'body', { shadow: null });
      ctx.gtext('STAMINA', x0, y0 + 62, '#6d6475', 'body', { shadow: null });
      for (const b of popupButtons(pb)) {
        const h = b.ok && hov && hov.key === 'p-' + b.key, dn = b.ok && down && down.key === 'p-' + b.key;
        g.drawImage(img['btn-' + b.key + (b.ok ? '' : '-off')], b.x, b.y + (dn ? 1 : h ? -1 : 0));
      }
    },
  };

  window.FTScreens = window.FTScreens || {};
  window.FTScreens.casino = mod;
})();
