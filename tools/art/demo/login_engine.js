/* Login screen (live game): connect Phantom, sign the one-time message, enter the game.
 * Registers window.FTScreens.login for HomeScene.
 */
(function () {
  'use strict';
  const st = { busy: false, msg: null, err: false };
  const inBox = (b, x, y) => x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h;

  function wrap(ctx, s, w) {
    const out = []; let line = '';
    for (const word of s.split(' ')) {
      const t = line ? line + ' ' + word : word;
      if (ctx.gwidth(t, 'body') > w && line) { out.push(line); line = word; } else line = t;
    }
    if (line) out.push(line);
    return out;
  }

  const mod = {
    enter() { st.busy = false; st.msg = null; st.err = false; },
    hit(ctx, x, y) { return inBox(ctx.L.connect, x, y) && !st.busy ? { key: 'connect' } : null; },
    click(ctx) {
      st.busy = true; st.msg = 'CHECK THE PHANTOM WINDOW'; st.err = false;
      FTLive.signIn()
        .then((r) => {
          if (r && r.pending) { st.msg = 'OPENING THE PHANTOM APP...'; return; }
          ctx.toast('WELCOME TO FROGOTRADERZ', [126, 224, 84]);
          ctx.go('home');
        })
        .catch((e) => {
          st.err = true;
          const m = String(e && e.message || e);
          st.msg = /reject|denied|cancel/i.test(m) ? 'SIGN-IN CANCELLED IN PHANTOM' : m.toUpperCase().replace(/\.$/, '');
        })
        .finally(() => { st.busy = false; });
    },
    frame(ctx, t) {
      const L = ctx.L, b = L.connect, hov = ctx.hover && ctx.hover.kind === 'mod';
      const down = ctx.press && ctx.press.kind === 'mod';
      const y = b.y + (down ? 1 : hov ? -1 : 0);
      if (hov && !st.busy) for (let i = 1; i <= 3; i++) for (let xx = b.x - i; xx <= b.x + b.w - 1 + i; xx++) {
        if ((xx + i) % 2) { ctx.px(xx, y - i, '#ab9ff2', 0.5 / i); ctx.px(xx, y + b.h - 1 + i, '#ab9ff2', 0.5 / i); }
      }
      ctx.g.drawImage(ctx.img[st.busy ? 'btn-connect-busy' : 'btn-connect'], b.x, y);
      const [sx, sy] = L.status;
      let lines;
      if (st.msg) lines = wrap(ctx, st.msg, 236);
      else if (FTLive.provider()) lines = ['PHANTOM FOUND. CLICK CONNECT,', 'THEN APPROVE THE SIGN-IN MESSAGE.'];
      else if (FTLive.mobile()) lines = ['ON A PHONE THE GAME OPENS', 'INSIDE THE PHANTOM APP.'];
      else lines = ['PHANTOM IS NOT INSTALLED.', 'CONNECT OPENS THE DOWNLOAD PAGE.'];
      lines.slice(0, 3).forEach((ln, i) => ctx.gtext(ln, sx, sy + i * 10, st.err ? '#ff8a9a' : '#f2e7d4', 'body', { align: 'center', shadow: null }));
      if (FTLive.ref) ctx.gtext('YOU WERE INVITED BY A FRIEND', sx, 104, '#7ee054', 'body', { align: 'center' });
      if (st.busy) {
        const k = Math.floor(t * 4) % 4;
        for (let i = 0; i < 3; i++) ctx.rect(sx - 6 + i * 5, sy + 30, sx - 5 + i * 5, sy + 31, i < k ? '#ab9ff2' : '#3a3046');
      }
    },
  };
  window.FTScreens = window.FTScreens || {};
  window.FTScreens.login = mod;
})();
