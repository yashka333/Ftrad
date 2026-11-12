import { describe, expect, it } from 'vitest';
import {
  ECONOMY,
  RARITIES,
  SKILL_IDS,
  advanceWorld,
  buyBoss,
  createFrog,
  goWork,
  maxStamina,
  medianPatience,
  mulberry32,
  newPlayer,
  newWorld,
  openPacks,
  profitPerHour,
  publicState,
  rest,
  assignDesk,
  workAll,
  restAll,
  restMinutes,
  rollRarity,
  shiftMinutes,
  startWork,
  stop,
  withdraw,
  GameError,
  buyListing,
  cancelListing,
  invitePacksFor,
  inviteSummary,
  listFrog,
  openFreePacks,
  type Frog,
} from '../src/index.js';

const T0 = Date.UTC(2026, 10, 4, 12, 0, 0); // noon UTC, outside Night Owl hours
const MIN = 60_000;
const HOUR = 60 * MIN;
const DAY = 24 * HOUR;

function setup(seed = 1) {
  const world = newWorld(T0);
  const p = newPlayer(world, 'jam', T0, true);
  const rand = mulberry32(seed);
  return { world, p, rand };
}

/** A frog with the median stats of its rarity and no skills. */
function medianFrog(rarity: number, id = 1): Frog {
  const r = RARITIES[rarity]!;
  const f = createFrog(id, T0, mulberry32(id), rarity);
  f.stats = {
    patience: medianPatience(rarity),
    profit: (r.profit[0] + r.profit[1]) / 2,
    risk: (r.risk[0] + r.risk[1]) / 2,
  };
  f.skills = [];
  f.stamina = maxStamina(f);
  return f;
}

describe('rarity', () => {
  it('odds add up to 100% and match the table', () => {
    expect(RARITIES.reduce((s, r) => s + r.odds, 0)).toBeCloseTo(100, 6);
    const rand = mulberry32(42);
    const counts = new Array(RARITIES.length).fill(0);
    const n = 300_000;
    for (let i = 0; i < n; i++) counts[rollRarity(rand)]++;
    expect(counts[0] / n).toBeCloseTo(0.83, 2);
    expect(counts[1] / n).toBeCloseTo(0.1, 2);
    expect(counts[2] / n).toBeCloseTo(0.055, 2);
  });

  it('rolls stats and skill counts inside the rarity ranges', () => {
    const rand = mulberry32(3);
    for (let i = 0; i < 3000; i++) {
      const f = createFrog(i + 1, T0, rand);
      const r = RARITIES[f.rarity]!;
      expect(f.stats.patience).toBeGreaterThanOrEqual(r.patience[0]);
      expect(f.stats.patience).toBeLessThanOrEqual(r.patience[1]);
      expect(f.stats.profit).toBeGreaterThanOrEqual(r.profit[0]);
      expect(f.stats.profit).toBeLessThanOrEqual(r.profit[1]);
      expect(f.skills.length).toBeGreaterThanOrEqual(r.skills[0]);
      expect(f.skills.length).toBeLessThanOrEqual(r.skills[1]);
      expect(new Set(f.skills).size).toBe(f.skills.length);
    }
  });

  it('has 14 skills', () => {
    expect(SKILL_IDS).toHaveLength(14);
  });
});

describe('shifts and rest', () => {
  it('a median frog works its rarity shift and rests its rarity hours', () => {
    const shifts = [1.5, 5, 30, 60, 90, 120];
    for (const r of RARITIES) {
      const f = medianFrog(r.id);
      expect(shiftMinutes(f)).toBeCloseTo(shifts[r.id]!, 6);
      expect(restMinutes(f)).toBeCloseTo(r.restHours * 60, 6);
    }
  });

  it('more PATIENCE means a longer shift and a longer rest', () => {
    const low = medianFrog(0);
    const high = medianFrog(0, 2);
    low.stats.patience = 10;
    high.stats.patience = 30;
    expect(shiftMinutes(low)).toBeCloseTo(0.75, 6);
    expect(shiftMinutes(high)).toBeCloseTo(2.25, 6);
    expect(restMinutes(high) / restMinutes(low)).toBeCloseTo(3, 6);
  });
});

describe('payback', () => {
  const target = [15, 10, 6, 3, 2, 1];
  for (const r of RARITIES) {
    it(`${r.name} pays a pack back in about ${target[r.id]} days when sent back as soon as it is rested`, () => {
      const { world, p } = setup();
      const f = medianFrog(r.id);
      p.frogs.push(f);
      p.lastSeenAt = T0;
      // the player presses ALL TO WORK every minute, measured over 15 days so long cycles average out
      const days = 15;
      for (let m = 0; m < days * 1440; m++) {
        advanceWorld(world, T0 + m * MIN);
        workAll(p, T0 + m * MIN);
      }
      const payback = ECONOMY.packPrice / (p.chest / days);
      expect(payback).toBeGreaterThan(target[r.id]! * 0.93);
      expect(payback).toBeLessThan(target[r.id]! * 1.07);
    });
  }
});

describe('rotation', () => {
  it('a tired frog walks to the casino and frees its desk', () => {
    const { world, p } = setup();
    const f = medianFrog(0);
    p.frogs.push(f);
    goWork(p, f.id, 'memecoin', T0);
    advanceWorld(world, T0 + 2 * MIN);
    expect(f.status).toBe('casino');
    expect(f.desk).toBeNull();
    const earned = p.chest;
    expect(earned).toBeGreaterThan(0);
    advanceWorld(world, T0 + 2 * MIN + 61 * MIN);
    expect(f.status).toBe('idle');
    advanceWorld(world, T0 + 5 * HOUR);
    expect(p.chest).toBe(earned); // nobody clicked, nothing earned
  });

  it('ALL TO WORK fills the freed desks with rested frogs', () => {
    const { world, p } = setup();
    for (let i = 1; i <= 20; i++) p.frogs.push(medianFrog(0, i));
    expect(workAll(p, T0)).toBe(15);
    advanceWorld(world, T0 + 3 * MIN);
    expect(p.frogs.filter((f) => f.status === 'casino')).toHaveLength(15);
    expect(workAll(p, T0 + 3 * MIN)).toBe(5);            // the 5 rested ones take desks
    expect(p.frogs.filter((f) => f.status === 'working')).toHaveLength(5);
  });

  it('Rest and Stop buttons', () => {
    const { p } = setup();
    const f = medianFrog(2);
    p.frogs.push(f);
    goWork(p, f.id, 'pumpfun', T0);
    rest(p, f.id, T0);
    expect(f.status).toBe('casino');
    expect(f.desk).toBeNull();
    expect(() => rest(p, f.id, T0)).toThrow(GameError);
  });

  it('5 desks per office', () => {
    const { p } = setup();
    for (let i = 1; i <= 6; i++) p.frogs.push(medianFrog(0, i));
    for (let i = 1; i <= 5; i++) goWork(p, i, 'classic', T0);
    expect(() => goWork(p, 6, 'classic', T0)).toThrow('All 5 desks');
  });
});

describe('desks and bulk actions', () => {
  it('assign a desk, then send everyone to work and to the casino', () => {
    const { p } = setup();
    for (let i = 1; i <= 4; i++) p.frogs.push(medianFrog(0, i));
    assignDesk(p, 1, 'memecoin', 0, T0);
    expect(p.frogs[0]!.status).toBe('ready');
    expect(() => assignDesk(p, 2, 'memecoin', 0, T0)).toThrow(GameError);
    expect(workAll(p, T0)).toBe(4);              // the ready one plus 3 seated on free desks
    // ALL TO CASINO only takes frogs that stopped working and are not rested
    stop(p, 2, T0);
    p.frogs[1]!.stamina = 10;
    expect(restAll(p, T0)).toBe(1);
    expect(p.frogs.filter((f) => f.status === 'working')).toHaveLength(3);
    expect(p.frogs[1]!.status).toBe('casino');
  });

  it('a frog put at a desk by hand goes back to that desk first', () => {
    const { world, p } = setup();
    for (let i = 1; i <= 16; i++) p.frogs.push(medianFrog(0, i));
    assignDesk(p, 16, 'classic', 4, T0);         // last desk in the last office
    workAll(p, T0);
    expect(p.frogs[15]!.desk).toEqual({ path: 'classic', desk: 4 });
    advanceWorld(world, T0 + 3 * MIN);           // everyone tired, desks freed
    advanceWorld(world, T0 + 3 * MIN + 2 * HOUR);
    expect(p.frogs.every((f) => f.status === 'idle')).toBe(true);
    workAll(p, T0 + 3 * MIN + 2 * HOUR);
    expect(p.frogs[15]!.desk).toEqual({ path: 'classic', desk: 4 });
  });
});

describe('skills', () => {
  const ctx = { path: 'classic' as const, workedMs: 0, officemates: 0, hourUtc: 12 };

  it('Degen Mode, Lucky Charm and Insider raise the expected profit', () => {
    const base = medianFrog(3);
    const plain = profitPerHour(base, ctx);
    for (const s of ['degenMode', 'luckyCharm', 'insider', 'stopLoss'] as const) {
      expect(profitPerHour({ ...base, skills: [s] }, ctx)).toBeGreaterThan(plain);
    }
  });

  it('Caffeine only in the first 10 minutes, Hot Streak grows with time', () => {
    const f = { ...medianFrog(1), skills: ['caffeine' as const] };
    expect(profitPerHour(f, { ...ctx, workedMs: 5 * MIN })).toBeGreaterThan(profitPerHour(f, { ...ctx, workedMs: 15 * MIN }));
    const h = { ...medianFrog(1), skills: ['hotStreak' as const] };
    expect(profitPerHour(h, { ...ctx, workedMs: 25 * MIN })).toBeGreaterThan(profitPerHour(h, { ...ctx, workedMs: 1 * MIN }));
  });

  it('Rug Radar removes the rug loss in Pump.fun', () => {
    const f = medianFrog(2);
    const pump = { ...ctx, path: 'pumpfun' as const };
    expect(profitPerHour({ ...f, skills: ['rugRadar'] }, pump)).toBeGreaterThan(profitPerHour(f, pump));
  });

  it('Diamond Hands lengthens the shift, Power Nap shortens the rest', () => {
    const f = medianFrog(2);
    expect(shiftMinutes({ ...f, skills: ['diamondHands'] })).toBeCloseTo(36, 6); // Rare: 30 min x 1.2
    expect(restMinutes({ ...f, skills: ['powerNap'] })).toBeCloseTo(4 * 60 * 0.85, 6);
  });
});

describe('packs, casino, boss', () => {
  it('a pack costs 10,000 and gives one frog', () => {
    const { world, p, rand } = setup();
    const frogs = openPacks(world, p, 5, T0, rand);
    expect(frogs).toHaveLength(5);
    expect(p.wallet).toBe(ECONOMY.devStartingWallet - 5 * 10_000);
    expect(() => openPacks(world, p, 3, T0, rand)).toThrow(GameError);
  });

  it('the casino is free and rests every frog at the same speed', () => {
    const { world, p } = setup();
    for (let i = 1; i <= 20; i++) {
      const f = medianFrog(1, i);
      f.stamina = 0;
      p.frogs.push(f);
      rest(p, f.id, T0);
    }
    advanceWorld(world, T0 + 60 * MIN);
    const s0 = p.frogs[0]!.stamina;
    expect(s0).toBeCloseTo(maxStamina(p.frogs[0]!) / 2, 3);   // 2h rest, half way after 1h
    for (const f of p.frogs) expect(f.stamina).toBeCloseTo(s0, 6);
  });

  it('only 250 Boss Frogs', () => {
    const { world, p } = setup();
    p.wallet = 1e12;
    world.bossesSold = 249;
    buyBoss(world, p);
    expect(p.bosses).toBe(1);
    expect(() => buyBoss(world, p)).toThrow('Sold out');
  });
});

describe('withdraw', () => {
  it('applies minimum, fee and daily cooldown', () => {
    const { world, p } = setup();
    expect(() => withdraw(world, p, T0)).toThrow('Withdraw from');
    p.chest = 200_000;
    const w = withdraw(world, p, T0);
    expect(w.fee).toBe(6_000);
    p.chest = 200_000;
    expect(() => withdraw(world, p, T0 + MIN)).toThrow('One withdrawal a day');
  });
});

describe('public state', () => {
  it('reports the rate, shift and rest of each frog', () => {
    const { world, p } = setup();
    const f = medianFrog(4);
    p.frogs.push(f);
    goWork(p, f.id, 'memecoin', T0);
    const s = publicState(world, p, T0);
    const pf = s.player.frogs[0]!;
    expect(pf.ratePerHour).toBeGreaterThan(1000);
    expect(pf.shiftMinutes).toBeCloseTo(90, 6);
    expect(pf.restMinutes).toBeCloseTo(7 * 60, 6);
    expect(s.player.ratePerHour).toBeCloseTo(pf.ratePerHour);
  });
});

describe('invites', () => {
  it('1 free pack at 10 frogs bought, then 2 for every next 10', () => {
    expect([0, 9, 10, 19, 20, 30, 45].map(invitePacksFor)).toEqual([0, 0, 1, 1, 3, 5, 7]);
  });

  it('a friend buying frogs earns the inviter free packs', () => {
    const { world, p, rand } = setup();
    const friend = newPlayer(world, 'friend', T0, true, { referredBy: p.id });
    openPacks(world, friend, 5, T0, rand);
    expect(p.freePacks).toBe(0);
    openPacks(world, friend, 5, T0, rand);
    expect(p.freePacks).toBe(1);
    openPacks(world, friend, 10, T0, rand);
    expect(p.freePacks).toBe(3);
    const frogs = openFreePacks(p, 3, T0, rand);
    expect(frogs).toHaveLength(3);
    expect(p.freePacks).toBe(0);
    expect(p.boughtFrogs).toBe(0); // free packs do not count
    expect(inviteSummary(world, p).friends[0]).toMatchObject({ name: 'friend', bought: 20, packs: 3 });
    expect(() => openFreePacks(p, 1, T0, rand)).toThrow(GameError);
  });
});

describe('market', () => {
  it('only Legendary and Mythic frogs, 5% fee burned', () => {
    const { world, p } = setup();
    const buyer = newPlayer(world, 'buyer', T0, true);
    p.frogs.push(medianFrog(3, 1), medianFrog(4, 2));
    expect(() => listFrog(world, p, 1, 50_000, T0)).toThrow('Only Legendary and Mythic');
    goWork(p, 2, 'classic', T0);
    const l = listFrog(world, p, 2, 100_000, T0);
    expect(p.frogs).toHaveLength(1);
    expect(() => buyListing(world, p, l.id, T0)).toThrow(GameError);
    const sellerBefore = p.wallet, buyerBefore = buyer.wallet;
    const { frog, fee } = buyListing(world, buyer, l.id, T0);
    expect(fee).toBe(5_000);
    expect(p.wallet).toBe(sellerBefore + 95_000);
    expect(buyer.wallet).toBe(buyerBefore - 100_000);
    expect(world.totalBurned).toBe(5_000);
    expect(frog.desk).toBeNull();
    expect(buyer.frogs).toContain(frog);
    expect(world.market).toHaveLength(0);
  });

  it('a seller can take a listing back', () => {
    const { world, p } = setup();
    p.frogs.push(medianFrog(5, 1));
    const l = listFrog(world, p, 1, 5_000, T0);
    cancelListing(world, p, l.id, T0);
    expect(p.frogs).toHaveLength(1);
    expect(world.market).toHaveLength(0);
  });
});
