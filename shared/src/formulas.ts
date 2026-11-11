import { ECONOMY, PATHS, STAMINA, TRADES, type PathId } from './config.js';
import { medianPatience, RARITIES } from './rarity.js';
import { HOT_STREAK_STEPS, HOT_STREAK_STEP_MS } from './skills.js';
import type { Frog, Player } from './types.js';

type FrogCore = Pick<Frog, 'rarity' | 'stats' | 'skills'>;

export function maxStamina(frog: Pick<Frog, 'stats'>): number {
  return frog.stats.patience * STAMINA.perPatience;
}

/**
 * Stamina spent per minute at the desk. The same for every frog of a rarity,
 * so a frog with more PATIENCE (a bigger bar) works longer.
 */
export function drainPerMin(frog: FrogCore): number {
  const base = (medianPatience(frog.rarity) * STAMINA.perPatience) / STAMINA.shiftMinutes;
  return frog.skills.includes('diamondHands') ? base / TRADES.diamondShift : base;
}

/** Stamina restored per minute in the casino. The casino is free and has room for every frog. */
export function restPerMin(frog: FrogCore): number {
  const restMin = RARITIES[frog.rarity]!.restHours * 60;
  const base = (medianPatience(frog.rarity) * STAMINA.perPatience) / restMin;
  const nap = frog.skills.includes('powerNap') ? 1 / TRADES.napRest : 1;
  return base * nap;
}

export function shiftMinutes(frog: FrogCore): number {
  return maxStamina(frog) / drainPerMin(frog);
}

export function restMinutes(frog: FrogCore): number {
  return maxStamina(frog) / restPerMin(frog);
}

export function hotStreakBonus(workedMs: number): number {
  const step = Math.min(HOT_STREAK_STEPS.length - 1, Math.floor(workedMs / HOT_STREAK_STEP_MS));
  return HOT_STREAK_STEPS[step] ?? 0;
}

export interface TradeContext {
  path: PathId;
  /** Time since the shift started. */
  workedMs: number;
  /** Other frogs of the same player trading in the same office. */
  officemates: number;
  /** Hour of day, UTC. */
  hourUtc: number;
}

/** Chances of a x2 trade and of an empty trade, both 0..1. */
export function tradeOdds(frog: FrogCore): { double: number; empty: number } {
  let risk = frog.stats.risk;
  let emptyRisk = frog.stats.risk;
  if (frog.skills.includes('degenMode')) {
    risk += TRADES.degenRisk;
    emptyRisk += TRADES.degenRisk;
  }
  if (frog.skills.includes('luckyCharm')) risk += TRADES.luckyRisk;
  let empty = (emptyRisk / 100) * TRADES.emptyShareOfRisk;
  if (frog.skills.includes('stopLoss')) empty /= 2;
  return { double: risk / 100, empty };
}

/**
 * Expected $FROG per hour of work right now. Trades are rolled only for the
 * animation; the payout uses this expected value, so every frog is paid
 * exactly what its stats promise.
 */
export function profitPerHour(frog: FrogCore, ctx: TradeContext): number {
  const office = PATHS[ctx.path];
  const has = (id: Frog['skills'][number]) => frog.skills.includes(id);

  let bonus = 0;
  if (has('degenMode')) bonus += TRADES.degenProfit;
  if (has('caffeine') && ctx.workedMs < TRADES.caffeineMs) bonus += TRADES.caffeineBonus;
  if (has('hotStreak')) bonus += hotStreakBonus(ctx.workedMs);
  if (has('copyTrader')) bonus += TRADES.copyBonus * ctx.officemates;
  if (has('nightOwl') && ctx.hourUtc < 6) bonus += TRADES.nightBonus;
  if (has('dipBuyer')) bonus += TRADES.dipBonus * office.dipRate;
  if (has('whaleHunter')) bonus += TRADES.whaleBonus * office.pumpRate;

  const { double, empty } = tradeOdds(frog);
  let outcome = 1 + double - empty;
  if (has('insider')) outcome += TRADES.insiderChance * (TRADES.insiderMultiplier - 1);
  const rug = has('rugRadar') ? 0 : office.rugRate;

  return frog.stats.profit * office.profit * (1 + bonus) * outcome * (1 - rug);
}

export function bossPrice(sold: number): number | null {
  return sold >= ECONOMY.boss.supply ? null : ECONOMY.boss.price;
}

/** Frogs in the casino, in the order they arrived. The casino screen seats them in this order. */
export function casinoQueue(player: Player): Frog[] {
  return player.frogs
    .filter((f) => f.status === 'casino')
    .sort((a, b) => a.statusSince - b.statusSince || a.id - b.id);
}

export function withdrawQuote(chest: number) {
  if (chest < ECONOMY.withdraw.min) return null;
  const gross = Math.min(chest, ECONOMY.withdraw.max);
  const fee = Math.floor(gross * ECONOMY.withdraw.feeRate * 100) / 100;
  return { gross, fee, net: gross - fee };
}

export function bossActive(player: Player): boolean {
  return player.bossOn && player.bosses > 0;
}

export function officemates(player: Player, frog: Frog): number {
  if (!frog.desk) return 0;
  const path = frog.desk.path;
  return player.frogs.filter((f) => f !== frog && f.status === 'working' && f.desk?.path === path).length;
}

export function hourUtc(at: number): number {
  return new Date(at).getUTCHours();
}
