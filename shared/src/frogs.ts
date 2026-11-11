import { RARITIES, rollRarity } from './rarity.js';
import { randInt } from './rng.js';
import { rollSkills } from './skills.js';
import { maxStamina } from './formulas.js';
import type { Frog } from './types.js';

const NICKNAMES = [
  'Bagholder Bob', 'Chartie', 'Rugpull Ron', 'Ape Andy', 'Wick Willy', 'Paper Paul',
  'Diamond Dee', 'Leverage Larry', 'Fomo Fred', 'Shorty', 'Candle Carl', 'Pump Pete',
  'Gwei Greg', 'Stop-Loss Sam', 'Moon Mo', 'Dip Dan', 'Exit Liquidity Eli', 'Rekt Rick',
  'Hodl Hank', 'Sniper Sid', 'Floor Flo', 'Gas Gus', 'Liquidated Liz', 'Pivot Pat',
  'Scalper Sal', 'Whale Wally', 'Jeet Jim', 'Copium Cody', 'Alpha Al', 'Bear Bart',
];

export function createFrog(id: number, now: number, rand: () => number, rarity = rollRarity(rand)): Frog {
  const r = RARITIES[rarity]!;
  const stats = {
    patience: randInt(rand, r.patience[0], r.patience[1]),
    profit: randInt(rand, r.profit[0], r.profit[1]),
    risk: randInt(rand, r.risk[0], r.risk[1]),
  };
  const frog: Frog = {
    id,
    name: NICKNAMES[Math.floor(rand() * NICKNAMES.length)]!,
    rarity,
    skin: Math.floor(rand() * 4),
    stats,
    skills: rollSkills(randInt(rand, r.skills[0], r.skills[1]), rand),
    stamina: 0,
    status: 'idle',
    statusSince: now,
    desk: null,
    earned: 0,
    bornAt: now,
  };
  frog.stamina = maxStamina(frog);
  return frog;
}
