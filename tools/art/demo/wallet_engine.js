/* Wallet screen (live game): balance, what the frogs earned, withdraw, test deposit, sign out.
 * Registers window.FTScreens.wallet for HomeScene.
 */
(function () {
  'use strict';
  const st = { busy: false };
  const inBox = (b, x, y) => x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h;
  const fmt = (v) => Math.floor(v).toLocaleString('en-US');

  function can(key, R) {
    const p = FTLive.player; if (!p || st.busy) return false;
    if (key === 'withdraw') {
      const w = R.withdraw, next = p.nextWithdrawAt;
      return FTLive.chest >= w.min && (!next || next <= Date.now()) && FTLive.wallet >= w.walletHoldMin;
    }
    if (key === 'deposit') return FTLive.devMode;
    return true;
  }

  const mod = {
    enter() { st.busy = false; FTLive.refresh(); },
    hit(ctx, x, y) {
      for (const [k, b] of Object.entries(ctx.L.buttons)) if (inBox(b, x, y)) return { key: k };
      return null;
    },
    click(ctx, it) {
      const R = ctx.D.cards.rules;
      if (!can(it.key, R)) {
        if (it.key === 'withdraw') {
          const p = FTLive.player, w = R.withdraw;
          if (FTLive.chest < w.min) ctx.toast(`WITHDRAW FROM ${fmt(w.min)} $FROG EARNED`, [230, 70, 90]);
          else if (p.nextWithdrawAt && p.nextWithdrawAt > Date.now()) ctx.toast('ONE WITHDRAWAL A DAY', [230, 70, 90]);
          else ctx.toast(`KEEP ${fmt(w.walletHoldMin)} $FROG IN YOUR BALANCE`, [230, 70, 90]);
        }
        return;
      }
      if (it.key === 'signout') {
        st.busy = true;
        FTLive.signOut().finally(() => { st.busy = false; ctx.go('login'); });
        return;
      }
      st.busy = true;
      const p = it.key === 'withdraw' ? FTLive.withdraw() : FTLive.deposit();
      p.then((r) => {
        if (it.key === 'withdraw') ctx.toast(`WITHDREW ${fmt(r.net)} $FROG (FEE ${fmt(r.fee)})`, [126, 224, 84]);
        else ctx.toast('TEST $FROG ADDED', [126, 224, 84]);
      }).catch(() => {}).finally(() => { st.busy = false; });
    },
    frame(ctx, t) {
      const L = ctx.L, g = ctx.g, img = ctx.img, R = ctx.D.cards.rules, p = FTLive.player;
      const hov = ctx.hover && ctx.hover.kind === 'mod' ? ctx.hover.item : null;
      const down = ctx.press && ctx.press.kind === 'mod' ? ctx.press.item : null;
      const rows = L.rows;
      ctx.gtext(fmt(FTLive.wallet) + ' $FROG', rows.balance[0], rows.balance[1], '#ffe282', 'title', { shadow: '#141216' });
      ctx.gtext(fmt(FTLive.chest) + ' $FROG', rows.chest[0], rows.chest[1], '#7ee054', 'title', { shadow: '#141216' });
      const rate = p ? FTCrew.frogs.reduce((s, f) => s + FTCrew.ratePerHour(f), 0) * FTLive.scale : 0;
      ctx.gtext(`+${fmt(rate)} / H`, 508, rows.chest[1] + 3, '#a8e890', 'body', { align: 'right', shadow: null });
      for (const [k, b] of Object.entries(L.buttons)) {
        const ok = can(k, R), h = ok && hov && hov.key === k, d = ok && down && down.key === k;
        g.drawImage(img['btn-' + k + (ok || k === 'withdraw' ? '' : '-off')], b.x, b.y + (d ? 1 : h ? -1 : 0));
        if (k === 'withdraw' && !ok) ctx.rect(b.x, b.y, b.x + b.w - 1, b.y + b.h - 1, '#000000', 0.45);
      }
      const [ix, iy, ix1] = L.info, w = R.withdraw;
      const next = p && p.nextWithdrawAt && p.nextWithdrawAt > Date.now() ? Math.ceil((p.nextWithdrawAt - Date.now()) / 60000) : 0;
      const lines = [
        ['WALLET', p && p.address ? p.address : '', '#f2e7d4'],
        ['', '', ''],
        ['WITHDRAW', `FROM ${fmt(w.min)} EARNED, FEE ${Math.round(w.feeRate * 100)}%, ONCE A DAY`, '#c8c0d0'],
        ['NEXT WITHDRAW', next ? `IN ${Math.floor(next / 60)}H ${next % 60}M` : 'NOW', next ? '#ffd66e' : '#7ee054'],
        ['', '', ''],
        ['TEST MODE', 'BALANCES ARE TEST $FROG, NOT REAL TOKENS.', '#ffd66e'],
        ['', 'TEST DEPOSIT ADDS ' + fmt(R.faucet || 250000) + ' TEST $FROG.', '#c8c0d0'],
        ['', 'WITHDRAW MOVES WHAT YOUR FROGS EARNED INTO BALANCE.', '#c8c0d0'],
      ];
      lines.forEach(([a, b, c], i) => {
        if (a) ctx.gtext(a, ix, iy + i * 12, '#8a8096', 'body', { shadow: null });
        if (b) ctx.gtext(b, a === 'WALLET' ? ix + 52 : ix + 88, iy + i * 12, c, 'body', { shadow: null });
      });
      if (st.busy) ctx.gtext('...', ix1, iy, '#ab9ff2', 'body', { align: 'right', shadow: null });
    },
  };
  window.FTScreens = window.FTScreens || {};
  window.FTScreens.wallet = mod;
})();
