/* Live game client: talks to the server and exposes the same window.FTCrew the screens use in the demo.
 * The server is the source of truth. Every action changes the local copy at once (so the screen answers
 * immediately), sends the command, then takes the state the server returns. Between refreshes the crew
 * is moved forward locally with the rates the server sent.
 * window.FTLive: boot(), logged, player, wallet, chest, devMode, scale, api(), signIn(), signOut(), openPacks(), ...
 */
(function () {
  'use strict';
  const PATHS = ['memecoin', 'pumpfun', 'classic'];
  const DESKS = 5;
  const frogs = [];
  const byId = new Map();
  const live = {
    logged: false, player: null, wallet: 0, chest: 0, devMode: false, scale: 1, ref: null,
    toast: () => {}, onLogout: () => {}, address: null,
  };
  let refreshAt = 0, polling = false;

  // ------------------------------------------------------------ http
  async function api(method, url, body) {
    const r = await fetch(url, {
      method, credentials: 'same-origin',
      headers: body ? { 'content-type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    let j = null;
    try { j = await r.json(); } catch (e) { j = null; }
    if (!r.ok) {
      const err = new Error((j && j.message) || 'Something went wrong. Try again.');
      err.code = j && j.error; err.status = r.status;
      if (r.status === 401 && live.logged && !url.startsWith('/api/auth')) { live.logged = false; live.onLogout(); }
      throw err;
    }
    return j;
  }
  const say = (e) => live.toast(String(e.message || e).toUpperCase().replace(/\.$/, ''), [230, 70, 90]);

  // ------------------------------------------------------------ state
  function toFrog(pf, into) {
    const f = into || {};
    Object.assign(f, {
      id: pf.id, uid: 'f' + pf.id, name: pf.name, rarity: pf.rarity, skin: pf.skin, stats: pf.stats, skills: pf.skills,
      status: pf.status, stamina: pf.stamina, desk: pf.desk, earned: pf.earned,
      max: pf.maxStamina, rate: pf.ratePerHour || 0, spm: pf.staminaPerMin || 0,
      shiftMinutes: pf.shiftMinutes, restMinutes: pf.restMinutes,
    });
    return f;
  }
  function apply(state) {
    if (!state || !state.player) return;
    const p = state.player;
    live.player = p; live.wallet = p.wallet; live.chest = p.chest; live.address = p.address;
    const keep = new Set();
    const list = p.frogs.map((pf) => { keep.add(pf.id); const f = toFrog(pf, byId.get(pf.id)); byId.set(pf.id, f); return f; });
    for (const id of [...byId.keys()]) if (!keep.has(id)) byId.delete(id);
    frogs.length = 0; frogs.push(...list);
  }
  async function refresh() {
    if (!live.logged) return;
    try { apply(await api('GET', '/api/state')); } catch (e) { /* the next poll tries again */ }
  }
  function soon(ms) { refreshAt = Math.min(refreshAt || Infinity, Date.now() + ms); }

  /** Sends a command; the state in the answer replaces the local copy. Errors are shown and undone by a refresh. */
  async function cmd(url, body) {
    try {
      const res = await api('POST', url, body);
      apply(res.state);
      return res.result;
    } catch (e) {
      say(e); refresh();
      throw e;
    }
  }
  const quiet = (p) => p.catch(() => {});

  // ------------------------------------------------------------ crew interface used by the screens
  const holder = (path, desk) => frogs.find((f) => f.desk && f.desk.path === path && f.desk.desk === desk) || null;
  function freeDesk(path) { for (let d = 0; d < DESKS; d++) if (!holder(path, d)) return d; return null; }
  function freeDesks(path) { let n = 0; for (let d = 0; d < DESKS; d++) if (!holder(path, d)) n++; return n; }

  function assignDesk(f, path, desk) {
    const h = holder(path, desk);
    if (h && h !== f) return 'DESK TAKEN';
    f.desk = { path, desk };
    if (f.status === 'idle') f.status = 'ready';
    quiet(cmd('/api/frogs/assign', { frogId: f.id, path, desk }));
    return null;
  }
  function allToWork() {
    let n = 0;
    for (const f of frogs) if (f.desk && f.status !== 'working' && f.status !== 'casino' && f.stamina >= 1) { f.status = 'working'; n++; }
    if (n) quiet(cmd('/api/frogs/work-all'));
    return n;
  }
  function allToCasino() {
    let n = 0;
    for (const f of frogs) if (f.status !== 'casino' && (f.status === 'working' || f.stamina < f.max)) { f.status = 'casino'; f.rate = 0; n++; }
    if (n) quiet(cmd('/api/frogs/rest-all'));
    return n;
  }
  function startWork(f) {
    if (!f.desk || f.stamina < 1) return;
    f.status = 'working';
    quiet(cmd('/api/frogs/work', { frogId: f.id }));
  }
  function rest(f) { f.status = 'casino'; f.rate = 0; quiet(cmd('/api/frogs/rest', { frogId: f.id })); }
  function stop(f) { f.desk = null; if (f.status !== 'casino') f.status = 'idle'; quiet(cmd('/api/frogs/stop', { frogId: f.id })); }
  function goWork(f, path) {
    const d = f.desk && f.desk.path === path ? f.desk.desk : freeDesk(path);
    if (d === null) return 'OFFICE IS FULL';
    f.desk = { path, desk: d };
    quiet(cmd('/api/frogs/go-work', { frogId: f.id, path, desk: d }));
    return null;
  }
  /** Seats the best rested frogs without a desk. Resolves to how many sat down. */
  function autoSeat() { return cmd('/api/frogs/auto-seat').catch(() => 0); }

  function ratePerHour(f) { return f.status === 'working' ? f.rate : 0; }
  /** Real minutes until the frog is tired (working) or rested (casino). */
  function etaMin(f) {
    if (f.status === 'working' && f.spm < 0) return f.stamina / -f.spm / live.scale;
    if (f.status === 'casino' && f.spm > 0) return (f.max - f.stamina) / f.spm / live.scale;
    return 0;
  }

  /** Moves the crew forward `dt` real seconds with the server's rates. Returns $FROG earned. */
  function tick(dt) {
    if (!live.logged) return 0;
    const min = (dt * live.scale) / 60;
    let earned = 0;
    for (const f of frogs) {
      if (f.status === 'working' && f.spm < 0) {
        const e = f.rate * (min / 60);
        f.earned += e; earned += e;
        f.stamina += f.spm * min;
        if (f.stamina <= 0) { f.stamina = 0; f.status = 'casino'; f.rate = 0; f.spm = 0; soon(1500); }
      } else if (f.status === 'casino' && f.spm > 0) {
        f.stamina = Math.min(f.max, f.stamina + f.spm * min);
        if (f.stamina >= f.max) { f.status = f.desk ? 'ready' : 'idle'; f.spm = 0; soon(1500); }
      }
    }
    live.chest += earned;
    const now = Date.now();
    if (refreshAt && now >= refreshAt && !polling) {
      refreshAt = 0; polling = true;
      refresh().finally(() => { polling = false; });
    }
    return earned;
  }

  window.FTCrew = {
    PATHS, DESKS, frogs, live: true,
    init() {}, makeFrog: () => null, add() {},
    autoSeat, goWork, startWork, assignDesk, allToWork, allToCasino, holder, rest, stop, tick, etaMin, ratePerHour, freeDesks,
    speed: 1,
  };

  // ------------------------------------------------------------ wallet sign-in
  const B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
  function base58(bytes) {
    const digits = [0];
    for (const b of bytes) {
      let carry = b;
      for (let i = 0; i < digits.length; i++) { carry += digits[i] << 8; digits[i] = carry % 58; carry = (carry / 58) | 0; }
      while (carry) { digits.push(carry % 58); carry = (carry / 58) | 0; }
    }
    let out = '';
    for (const b of bytes) { if (b === 0) out += '1'; else break; }
    for (let i = digits.length - 1; i >= 0; i--) out += B58[digits[i]];
    return out;
  }
  function provider() {
    if (window.phantom && window.phantom.solana && window.phantom.solana.isPhantom) return window.phantom.solana;
    if (window.solana && window.solana.isPhantom) return window.solana;
    return null;
  }
  const mobile = () => /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  /** Opens this page inside the Phantom app (phones have no browser extension). */
  function openInPhantom() {
    const url = location.href;
    location.href = 'https://phantom.app/ul/browse/' + encodeURIComponent(url) + '?ref=' + encodeURIComponent(location.origin);
  }

  async function signIn() {
    const prov = provider();
    if (!prov) {
      if (mobile()) { openInPhantom(); return { pending: true }; }
      window.open('https://phantom.app/download', '_blank', 'noopener');
      throw new Error('Phantom not found. Install it, then reload this page.');
    }
    const resp = await prov.connect();
    const address = (resp && resp.publicKey ? resp.publicKey : prov.publicKey).toString();
    const { message } = await api('POST', '/api/auth/nonce', { address });
    const signed = await prov.signMessage(new TextEncoder().encode(message), 'utf8');
    const sig = signed && signed.signature ? signed.signature : signed;
    const state = await api('POST', '/api/auth/verify', { address, signature: base58(sig), ref: live.ref || undefined });
    live.logged = true;
    apply(state);
    try { localStorage.removeItem('ft_ref'); } catch (e) { /* storage may be blocked */ }
    return state;
  }
  async function signOut() {
    try { await api('POST', '/api/session/sign-out'); } catch (e) { /* ignore */ }
    try { const p = provider(); if (p && p.disconnect) await p.disconnect(); } catch (e) { /* ignore */ }
    live.logged = false; frogs.length = 0; byId.clear();
  }

  async function boot() {
    const q = new URLSearchParams(location.search).get('ref');
    try { if (q) localStorage.setItem('ft_ref', q); live.ref = q || localStorage.getItem('ft_ref'); } catch (e) { live.ref = q; }
    try { const h = await api('GET', '/api/health'); live.devMode = !!h.devMode; live.scale = h.timeScale || 1; } catch (e) { /* offline */ }
    try {
      const me = await api('GET', '/api/me');
      live.logged = !!me.logged;
      if (me.logged) apply(me.state);
    } catch (e) { live.logged = false; }
    setInterval(() => { if (live.logged && !document.hidden) soon(0); }, 20000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) soon(0); });
    return live.logged;
  }

  // ------------------------------------------------------------ other commands
  /** Opens paid or free packs. Resolves to the new frogs as the cards screen draws them. */
  async function openPacks(count, free) {
    const result = await cmd(free ? '/api/packs/open-free' : '/api/packs/open', { count });
    return result.map((pf) => ({ id: pf.id, uid: 'f' + pf.id, name: pf.name, rarity: pf.rarity, stats: pf.stats, skills: pf.skills }));
  }

  Object.assign(live, {
    api, boot, signIn, signOut, refresh, apply, cmd, openPacks, say, provider, mobile, openInPhantom,
    withdraw: () => cmd('/api/withdrawals'),
    deposit: () => cmd('/api/dev/faucet'),
    market: () => api('GET', '/api/market'),
    invite: () => api('GET', '/api/invite'),
    list: (frogId, price) => cmd('/api/market/list', { frogId, price }),
    buy: (listingId) => cmd('/api/market/buy', { listingId }),
    cancel: (listingId) => cmd('/api/market/cancel', { listingId }),
  });
  window.FTLive = live;
})();
