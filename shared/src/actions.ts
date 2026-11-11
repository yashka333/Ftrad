/**
 * Every change a player can make. The server calls these after moving the
 * world to "now", so all checks run against fresh state.
 */
import { ECONOMY, INVITE, MARKET, PATHS, PATH_IDS, type PathId } from './config.js';
import { GameError } from './errors.js';
import { createFrog } from './frogs.js';
import { bossPrice, maxStamina, withdrawQuote } from './formulas.js';
import type { Frog, Listing, Player, World } from './types.js';

export function newWorld(now: number): World {
  return {
    version: 5,
    createdAt: now,
    lastTickAt: now,
    totalPaidOut: 0,
    totalSpent: 0,
    bossesSold: 0,
    totalBurned: 0,
    market: [],
    nextListingId: 1,
    nextPlayerId: 1,
    players: {},
  };
}

export function newPlayer(
  world: World,
  name: string,
  now: number,
  devMode: boolean,
  opts: { address?: string | null; refCode?: string; referredBy?: number | null } = {},
): Player {
  const id = world.nextPlayerId++;
  const p: Player = {
    id,
    name,
    address: opts.address ?? null,
    refCode: opts.refCode ?? `f${id.toString(36)}`,
    referredBy: opts.referredBy && world.players[String(opts.referredBy)] ? opts.referredBy : null,
    boughtFrogs: 0,
    refPacksGiven: 0,
    freePacks: 0,
    refPacksEarned: 0,
    createdAt: now,
    lastSeenAt: now,
    wallet: devMode ? ECONOMY.devStartingWallet : 0,
    chest: 0,
    frogs: [],
    nextFrogId: 1,
    bosses: 0,
    bossOn: false,
    withdrawals: [],
    lastWithdrawAt: null,
    totalEarned: 0,
  };
  world.players[String(p.id)] = p;
  return p;
}

function spend(world: World, p: Player, amount: number): void {
  if (p.wallet < amount) throw new GameError('insufficient-token');
  p.wallet -= amount;
  world.totalSpent += amount;
}

function getFrog(p: Player, id: number): Frog {
  const f = p.frogs.find((x) => x.id === id);
  if (!f) throw new GameError('frog-not-found', 404);
  return f;
}

function setStatus(f: Frog, status: Frog['status'], now: number): void {
  if (f.status !== status) {
    f.status = status;
    f.statusSince = now;
  }
}

/** Opens packs. One frog per pack. */
export function openPacks(world: World, p: Player, count: number, now: number, rand: () => number): Frog[] {
  if (!(ECONOMY.packSizes as readonly number[]).includes(count)) throw new GameError('bad-pack');
  if (p.frogs.length + count > ECONOMY.maxFrogs) throw new GameError('frog-limit');
  const price = ECONOMY.packPrice * count;
  if (p.wallet < price) throw new GameError('insufficient-token');
  // Roll first, charge second: a failure while rolling never costs tokens.
  const out: Frog[] = [];
  for (let i = 0; i < count; i++) out.push(createFrog(p.nextFrogId + i, now, rand));
  spend(world, p, price);
  p.nextFrogId += count;
  p.frogs.push(...out);
  p.boughtFrogs += count;
  rewardInviter(world, p);
  return out;
}

/** Free packs the inviter has earned from a friend who bought `bought` frogs. */
export function invitePacksFor(bought: number): number {
  const steps = Math.floor(bought / INVITE.step);
  return steps < 1 ? 0 : INVITE.firstReward + (steps - 1) * INVITE.nextReward;
}

function rewardInviter(world: World, p: Player): void {
  if (p.referredBy === null) return;
  const inviter = world.players[String(p.referredBy)];
  if (!inviter) return;
  const due = invitePacksFor(p.boughtFrogs) - p.refPacksGiven;
  if (due <= 0) return;
  inviter.freePacks += due;
  inviter.refPacksEarned += due;
  p.refPacksGiven += due;
}

/** Opens free packs from invites. They cost nothing and do not count as bought frogs. */
export function openFreePacks(p: Player, count: number, now: number, rand: () => number): Frog[] {
  if (!Number.isInteger(count) || count < 1 || count > p.freePacks) throw new GameError('no-free-packs');
  if (p.frogs.length + count > ECONOMY.maxFrogs) throw new GameError('frog-limit');
  const out: Frog[] = [];
  for (let i = 0; i < count; i++) out.push(createFrog(p.nextFrogId + i, now, rand));
  p.nextFrogId += count;
  p.frogs.push(...out);
  p.freePacks -= count;
  return out;
}

/** Puts a Legendary or Mythic frog on the market. It leaves the crew (and its desk) until sold or taken back. */
export function listFrog(world: World, p: Player, frogId: number, price: number, now: number): Listing {
  const f = getFrog(p, frogId);
  if (f.rarity < MARKET.minRarity) throw new GameError('not-tradeable');
  if (!Number.isInteger(price) || price < MARKET.minPrice || price > MARKET.maxPrice) throw new GameError('bad-price');
  if (world.market.filter((l) => l.sellerId === p.id).length >= MARKET.maxListings) throw new GameError('too-many-listings');
  p.frogs = p.frogs.filter((x) => x.id !== f.id);
  f.desk = null;
  setStatus(f, 'idle', now);
  const l: Listing = { id: world.nextListingId++, sellerId: p.id, sellerName: p.name, price, createdAt: now, frog: f };
  world.market.unshift(l);
  return l;
}

/** Takes a listing back into the seller's crew. */
export function cancelListing(world: World, p: Player, listingId: number, now: number): Frog {
  const l = world.market.find((x) => x.id === listingId);
  if (!l) throw new GameError('listing-not-found', 404);
  if (l.sellerId !== p.id) throw new GameError('not-your-listing', 403);
  if (p.frogs.length >= ECONOMY.maxFrogs) throw new GameError('frog-limit');
  world.market = world.market.filter((x) => x !== l);
  const f = l.frog;
  f.id = p.nextFrogId++;
  setStatus(f, 'idle', now);
  p.frogs.push(f);
  return f;
}

/** Buys a listing: the seller gets the price minus the burned fee, the frog joins the buyer's crew. */
export function buyListing(world: World, p: Player, listingId: number, now: number): { frog: Frog; fee: number } {
  const l = world.market.find((x) => x.id === listingId);
  if (!l) throw new GameError('listing-not-found', 404);
  if (l.sellerId === p.id) throw new GameError('own-listing');
  if (p.frogs.length >= ECONOMY.maxFrogs) throw new GameError('frog-limit');
  const seller = world.players[String(l.sellerId)];
  if (p.wallet < l.price) throw new GameError('insufficient-token');
  p.wallet -= l.price;
  const fee = Math.ceil(l.price * MARKET.feeRate);
  if (seller) seller.wallet += l.price - fee;
  world.totalBurned += fee;
  world.market = world.market.filter((x) => x !== l);
  const f = l.frog;
  f.id = p.nextFrogId++;
  f.desk = null;
  setStatus(f, 'idle', now);
  p.frogs.push(f);
  return { frog: f, fee };
}

export function freeDesk(p: Player, path: PathId): number | null {
  for (let d = 0; d < PATHS[path].desks; d++) {
    if (!p.frogs.some((f) => f.desk?.path === path && f.desk.desk === d)) return d;
  }
  return null;
}

/** "Go work": take a desk in an office and start trading. Picks the first free desk when none is given. */
export function goWork(p: Player, frogId: number, path: PathId, now: number, desk?: number): void {
  if (!PATHS[path]) throw new GameError('bad-desk');
  const f = getFrog(p, frogId);
  const d = desk ?? (f.desk?.path === path ? f.desk.desk : freeDesk(p, path));
  if (d === null) throw new GameError('office-full');
  if (!Number.isInteger(d) || d < 0 || d >= PATHS[path].desks) throw new GameError('bad-desk');
  const holder = p.frogs.find((x) => x.desk && x.desk.path === path && x.desk.desk === d);
  if (holder && holder.id !== f.id) throw new GameError('desk-taken');
  if (f.stamina < 1) throw new GameError('too-tired');
  f.desk = { path, desk: d };
  setStatus(f, 'working', now);
}

/** Put a frog at a desk without starting work. A rested frog waits there as READY. */
export function assignDesk(p: Player, frogId: number, path: PathId, desk: number, now: number): void {
  if (!PATHS[path] || !Number.isInteger(desk) || desk < 0 || desk >= PATHS[path].desks) throw new GameError('bad-desk');
  const f = getFrog(p, frogId);
  const holder = p.frogs.find((x) => x.desk && x.desk.path === path && x.desk.desk === desk);
  if (holder && holder.id !== f.id) throw new GameError('desk-taken');
  if (f.status === 'casino' && f.stamina < 1) throw new GameError('too-tired');
  f.desk = { path, desk };
  if (f.status === 'idle' || f.status === 'casino') setStatus(f, 'ready', now);
}

/**
 * "All to work": frogs waiting at their desks start trading, then the best rested frogs
 * without a desk take the free desks. Frogs resting in the casino stay there. Returns how many started.
 */
export function workAll(p: Player, now: number): number {
  let n = 0;
  for (const f of p.frogs) {
    if (f.desk && f.status !== 'working' && f.status !== 'casino' && f.stamina >= 1) {
      setStatus(f, 'working', now);
      n++;
    }
  }
  return n + autoSeat(p, now);
}

/** "All to the casino": every frog that is not fully rested goes to rest and frees its desk. Returns how many went. */
export function restAll(p: Player, now: number): number {
  let n = 0;
  for (const f of p.frogs) {
    if (f.status !== 'casino' && (f.status === 'working' || f.stamina < maxStamina(f))) {
      setStatus(f, 'casino', now);
      f.desk = null;
      n++;
    }
  }
  return n;
}

/** Back to work at the frog's own desk (after a rest). */
export function startWork(p: Player, frogId: number, now: number): void {
  const f = getFrog(p, frogId);
  if (!f.desk) throw new GameError('no-desk');
  if (f.status === 'working') throw new GameError('already-working');
  if (f.stamina < 1) throw new GameError('too-tired');
  setStatus(f, 'working', now);
}

/** "Rest": send the frog to the casino now. Its desk is freed for the next frog. */
export function rest(p: Player, frogId: number, now: number): void {
  const f = getFrog(p, frogId);
  if (f.status === 'casino') throw new GameError('already-resting');
  setStatus(f, 'casino', now);
  f.desk = null;
}

/** "Stop": the frog leaves its desk. */
export function stop(p: Player, frogId: number, now: number): void {
  const f = getFrog(p, frogId);
  f.desk = null;
  if (f.status !== 'casino') setStatus(f, 'idle', now);
}

export function buyBoss(world: World, p: Player): void {
  const price = bossPrice(world.bossesSold);
  if (price === null) throw new GameError('sold-out');
  spend(world, p, price);
  world.bossesSold++;
  p.bosses++;
  p.bossOn = true;
}

export function toggleBoss(p: Player, on: boolean): void {
  if (p.bosses < 1) throw new GameError('no-boss');
  p.bossOn = on;
}

export function nextWithdrawAt(p: Player): number | null {
  return p.lastWithdrawAt === null ? null : p.lastWithdrawAt + ECONOMY.withdraw.cooldownMs;
}

export function withdraw(world: World, p: Player, now: number) {
  const q = withdrawQuote(p.chest);
  if (!q) throw new GameError('below-withdrawal-minimum');
  const next = nextWithdrawAt(p);
  if (next !== null && next > now) throw new GameError('withdrawal-too-soon');
  if (p.wallet < ECONOMY.withdraw.walletHoldMin) throw new GameError('wallet-below-minimum');
  p.chest -= q.gross;
  p.wallet += q.net;
  p.lastWithdrawAt = now;
  const w = { id: p.withdrawals.length + 1, createdAt: now, ...q, state: 'paid' as const };
  p.withdrawals.unshift(w);
  p.withdrawals = p.withdrawals.slice(0, 30);
  return w;
}

export function devFaucet(p: Player): void {
  p.wallet += ECONOMY.devFaucetAmount;
}

/** Fill every free desk with the best rested frogs that have no desk. */
export function autoSeat(p: Player, now: number): number {
  let seated = 0;
  const free = p.frogs
    .filter((f) => !f.desk && f.status === 'idle' && f.stamina >= 1)
    .sort((a, b) => b.rarity - a.rarity || b.stats.profit - a.stats.profit);
  for (const path of PATH_IDS) {
    let d = freeDesk(p, path);
    while (d !== null) {
      const f = free.shift();
      if (!f) return seated;
      goWork(p, f.id, path, now, d);
      seated++;
      d = freeDesk(p, path);
    }
  }
  return seated;
}
