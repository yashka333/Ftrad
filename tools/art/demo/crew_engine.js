/* The player's crew for the browser demo: rolls frogs and runs the work loop with the shared rules
 * (shift, casino rest, ready). Demo time runs 60x faster so a 30 minute shift takes 30 seconds.
 * window.FTCrew: init(rules), frogs, makeFrog(), add(list), autoSeat(list), goWork(f, path), rest(f), stop(f), tick(dt)
 */
(function () {
  'use strict';
  const SPEED = 60;
  const PATHS = ['memecoin', 'pumpfun', 'classic'];
  const DESKS = 5;
  let R = null, nextId = 18788;
  const frogs = [];
  const randInt = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));

  function rollRarity() {
    const total = R.rarities.reduce((s, r) => s + r.odds, 0);
    let roll = Math.random() * total;
    for (const r of R.rarities) { roll -= r.odds; if (roll < 0) return r.id; }
    return 0;
  }
  function rollSkills(count) {
    const pool = Object.keys(R.skills), out = [];
    while (out.length < count && pool.length) {
      const total = pool.reduce((s, id) => s + R.skillWeight[R.skills[id].tier], 0);
      let roll = Math.random() * total, pick = pool.length - 1;
      for (let i = 0; i < pool.length; i++) { roll -= R.skillWeight[R.skills[pool[i]].tier]; if (roll < 0) { pick = i; break; } }
      out.push(pool[pick]); pool.splice(pick, 1);
    }
    return out;
  }
  function makeFrog(rarity) {
    rarity = rarity == null ? rollRarity() : rarity;
    const r = R.rarities[rarity];
    const f = {
      id: nextId++, rarity, name: R.names[Math.floor(Math.random() * R.names.length)],
      stats: { patience: randInt(...r.patience), profit: randInt(...r.profit), risk: randInt(...r.risk) },
      skills: rollSkills(randInt(...r.skills)),
      status: 'idle', desk: null, earned: 0,
    };
    f.max = f.stats.patience * 5;
    f.stamina = f.max;
    return f;
  }

  // ------------------------------------------------------------ rules (mirror shared/src/formulas.ts)
  const median = (f) => (R.rarities[f.rarity].patience[0] + R.rarities[f.rarity].patience[1]) / 2;
  const drainPerMin = (f) => (median(f) * 5 / R.rarities[f.rarity].shiftMinutes) / (f.skills.includes('diamondHands') ? 1.2 : 1);
  const restPerMin = (f) => (median(f) * 5 / (R.rarities[f.rarity].restHours * 60)) / (f.skills.includes('powerNap') ? 0.85 : 1);
  function ratePerHour(f) {
    if (f.status !== 'working') return 0;
    let risk = f.stats.risk, empty = f.stats.risk;
    let bonus = 0;
    if (f.skills.includes('degenMode')) { bonus += 0.2; risk += 5; empty += 5; }
    if (f.skills.includes('luckyCharm')) risk += 5;
    let e = (empty / 100) / 2; if (f.skills.includes('stopLoss')) e /= 2;
    let out = 1 + risk / 100 - e;
    if (f.skills.includes('insider')) out += 0.1;
    return (f.stats.profit * 60 / R.rarities[f.rarity].shiftMinutes) * (1 + bonus) * out;
  }

  function freeDesk(path) {
    for (let d = 0; d < DESKS; d++) if (!frogs.some((f) => f.desk && f.desk.path === path && f.desk.desk === d)) return d;
    return null;
  }
  function freeDesks(path) { let n = 0; for (let d = 0; d < DESKS; d++) if (!frogs.some((f) => f.desk && f.desk.path === path && f.desk.desk === d)) n++; return n; }

  function goWork(f, path) {
    if (!path) path = PATHS.find((p) => freeDesk(p) !== null);
    if (!path) return 'ALL 15 DESKS ARE TAKEN';
    if (!f.desk || f.desk.path !== path) {
      const d = freeDesk(path);
      if (d === null) return 'OFFICE IS FULL';
      f.desk = { path, desk: d };
    }
    if (f.status === 'casino' && f.stamina < 1) return null;
    if (f.stamina < 1) { f.status = 'casino'; return null; }
    f.status = 'working';
    return null;
  }
  const holder = (path, desk) => frogs.find((f) => f.desk && f.desk.path === path && f.desk.desk === desk) || null;
  /** Manual seat (mirrors shared assignDesk): a rested frog waits there as READY. */
  function assignDesk(f, path, desk) {
    const h = holder(path, desk);
    if (h && h !== f) return 'DESK TAKEN';
    f.desk = { path, desk };
    if (f.status === 'idle') f.status = 'ready';
    return null;
  }
  /** Mirrors shared workAll: every frog with a desk and stamina starts trading. */
  function allToWork() {
    let n = 0;
    for (const f of frogs) if (f.desk && f.status !== 'working' && f.status !== 'casino' && f.stamina >= 1) { f.status = 'working'; n++; }
    const idle = frogs.filter((f) => !f.desk && f.status === 'idle' && f.stamina >= 1).sort((a, b) => b.rarity - a.rarity);
    for (const path of PATHS) { let d = freeDesk(path); while (d !== null && idle.length) { const f = idle.shift(); f.desk = { path, desk: d }; f.status = 'working'; n++; d = freeDesk(path); } }
    return n;
  }
  /** Mirrors shared restAll: every frog that is working or not fully rested goes to the casino. */
  function allToCasino() {
    let n = 0;
    for (const f of frogs) if (f.status !== 'casino' && (f.status === 'working' || f.stamina < f.max)) { f.status = 'casino'; f.desk = null; n++; }
    return n;
  }
  function startWork(f) { if (f.desk && f.stamina >= 1) f.status = 'working'; }
  function rest(f) { f.status = 'casino'; f.desk = null; }
  function stop(f) { f.desk = null; if (f.status !== 'casino') f.status = 'idle'; }
  function autoSeat(list) {
    let n = 0;
    for (const f of list) {
      const path = PATHS.find((p) => freeDesk(p) !== null);
      if (!path) break;
      goWork(f, path); n++;
    }
    return n;
  }

  /** Advances the crew by `dt` real seconds. Returns $FROG earned. */
  function tick(dt) {
    const min = (dt * SPEED) / 60;
    let earned = 0;
    for (const f of frogs) {
      if (f.status === 'working') {
        const e = ratePerHour(f) * (min / 60);
        f.earned += e; earned += e;
        f.stamina -= drainPerMin(f) * min;
        if (f.stamina <= 0) { f.stamina = 0; f.status = 'casino'; f.desk = null; }
      } else if (f.status === 'casino') {
        f.stamina = Math.min(f.max, f.stamina + restPerMin(f) * min);
        if (f.stamina >= f.max) f.status = f.desk ? 'ready' : 'idle';
      }
    }
    return earned;
  }

  /** Minutes (game time) until the frog is tired or rested. */
  function etaMin(f) {
    if (f.status === 'working') return f.stamina / drainPerMin(f);
    if (f.status === 'casino') return (f.max - f.stamina) / restPerMin(f);
    return 0;
  }

  function seed() {
    const plan = [[5, 'working', 'memecoin'], [2, 'working', 'memecoin'], [0, 'working', 'memecoin'], [1, 'working', 'pumpfun'],
      [0, 'working', 'pumpfun'], [3, 'casino', 'classic'], [0, 'casino', 'classic'], [4, 'ready', 'classic'], [1, 'ready', 'pumpfun'],
      [0, 'idle', null], [0, 'idle', null], [2, 'idle', null], [0, 'casino', null], [1, 'idle', null]];
    for (const [r, status, path] of plan) {
      const f = makeFrog(r);
      if (path) f.desk = { path, desk: freeDesk(path) };
      f.status = status;
      if (status === 'working') f.stamina = f.max * (0.25 + Math.random() * 0.7);
      if (status === 'casino') f.stamina = f.max * Math.random() * 0.6;
      frogs.push(f);
    }
  }

  window.FTCrew = {
    PATHS, DESKS, frogs,
    init(rules) { R = rules; if (!frogs.length) seed(); },
    makeFrog, add: (list) => frogs.push(...list), autoSeat, goWork, startWork, assignDesk, allToWork, allToCasino, holder, rest, stop, tick, etaMin, ratePerHour,
    freeDesks, speed: SPEED,
  };
})();
