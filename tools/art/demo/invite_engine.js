/* Invite screen (live game): your invite link, the reward rules, free packs and the friends you brought.
 * Registers window.FTScreens.invite for HomeScene.
 */
(function () {
  'use strict';
  const st = { data: null, at: 0, copied: 0, scroll: 0 };
  const inBox = (b, x, y) => x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h;
  const link = () => (st.data ? `${location.origin}/?ref=${st.data.refCode}` : '');

  function load() { FTLive.invite().then((d) => { st.data = d; st.at = Date.now(); }).catch(() => {}); }

  function copy(ctx) {
    const s = link(); if (!s) return;
    const ok = () => { st.copied = 2; ctx.toast('INVITE LINK COPIED', [90, 170, 240]); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(s).then(ok).catch(() => fallback(ctx, s, ok));
    else fallback(ctx, s, ok);
  }
  /** Clipboard API blocked: copy through a hidden text field. */
  function fallback(ctx, s, ok) {
    const ta = document.createElement('textarea');
    ta.value = s; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    let done = false;
    try { done = document.execCommand('copy'); } catch (e) { done = false; }
    ta.remove();
    if (done) ok(); else ctx.toast('COPY BLOCKED: ' + s.toUpperCase(), [90, 170, 240]);
  }

  const mod = {
    enter() { st.scroll = 0; load(); },
    hit(ctx, x, y) {
      const B = ctx.L.buttons;
      if (inBox(B.copy, x, y)) return { key: 'copy' };
      if (inBox(B.open, x, y) && st.data && st.data.freePacks > 0) return { key: 'open' };
      return null;
    },
    click(ctx, it) {
      if (it.key === 'copy') copy(ctx);
      if (it.key === 'open') ctx.go('recruit');
    },
    wheel(ctx, dy) {
      const n = st.data ? st.data.friends.length : 0;
      st.scroll = Math.max(0, Math.min(Math.max(0, n - ctx.L.list.rows), st.scroll + (dy > 0 ? 1 : -1)));
    },
    frame(ctx, t, dt) {
      const L = ctx.L, g = ctx.g, img = ctx.img, d = st.data;
      const hov = ctx.hover && ctx.hover.kind === 'mod' ? ctx.hover.item : null;
      const down = ctx.press && ctx.press.kind === 'mod' ? ctx.press.item : null;
      if (Date.now() - st.at > 15000 && st.at) { st.at = Date.now(); load(); }
      st.copied = Math.max(0, st.copied - dt);
      const [lx, ly, lx1] = L.link;
      let s = d ? link().replace(/^https?:\/\//, '').toUpperCase() : 'LOADING...';
      while (ctx.gwidth(s, 'body') > lx1 - lx && s.length > 8) s = s.slice(0, -4) + '...';
      ctx.gtext(s, lx, ly + 1, st.copied ? '#7ee054' : '#ffe282', 'body', { shadow: null });
      for (const [k, b] of Object.entries(L.buttons)) {
        const ok = k === 'copy' ? !!d : !!(d && d.freePacks > 0);
        const h = ok && hov && hov.key === k, dn = ok && down && down.key === k;
        const name = k === 'copy' ? 'btn-copy' : ok ? 'btn-open' : 'btn-open-off';
        g.drawImage(img[name], b.x, b.y + (dn ? 1 : h ? -1 : 0));
      }
      if (d) {
        const S = L.stats;
        const vals = { friends: d.friends.length, earned: d.packsEarned, free: d.freePacks };
        for (const [k, [x, y]] of Object.entries(S)) {
          ctx.gtext(String(vals[k]), x, y, k === 'free' && vals[k] ? '#ffe282' : '#f2e7d4', 'title', { align: 'center', shadow: '#141216' });
        }
      }
      // friends list
      const li = L.list;
      if (!d || !d.friends.length) {
        ctx.gtext(d ? 'NO FRIENDS YET' : 'LOADING...', li.x + li.w / 2, li.y + 40, '#8a8096', 'body', { align: 'center', shadow: null });
        if (d) ctx.gtext('SHARE YOUR LINK TO START', li.x + li.w / 2, li.y + 52, '#6d6475', 'body', { align: 'center', shadow: null });
        return;
      }
      d.friends.slice(st.scroll, st.scroll + li.rows).forEach((f, i) => {
        const y = li.y + i * li.row;
        ctx.rect(li.x, y, li.x + li.w - 1, y + li.row - 3, i % 2 ? '#1c1822' : '#221d29');
        ctx.gtext(f.name.toUpperCase(), li.x + 6, y + 4, '#f2e7d4', 'body', { shadow: null });
        ctx.gtext(String(f.bought), li.x + li.w - 82, y + 4, '#c8c0d0', 'body', { align: 'right', shadow: null });
        ctx.gtext(String(f.packs), li.x + li.w - 6, y + 4, f.packs ? '#ffe282' : '#8a8096', 'body', { align: 'right', shadow: null });
        // progress to the next reward
        const into = f.bought % 10, bx = li.x + 6, bw = li.w - 160;
        ctx.rect(bx, y + 13, bx + bw, y + 16, '#0c0a0e');
        ctx.rect(bx + 1, y + 14, bx + 1 + Math.round((bw - 2) * into / 10), y + 15, '#5aaaf0');
        ctx.gtext(`${10 - into} TO NEXT`, bx + bw + 4, y + 12, '#6d6475', 'body', { shadow: null });
      });
    },
  };
  window.FTScreens = window.FTScreens || {};
  window.FTScreens.invite = mod;
})();
