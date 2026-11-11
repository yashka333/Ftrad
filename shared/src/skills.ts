/**
 * The 14 skills. Effects are applied in formulas.ts; this file holds the
 * names, texts and how often each one is rolled.
 */
export type SkillId =
  | 'diamondHands'
  | 'powerNap'
  | 'fastFingers'
  | 'caffeine'
  | 'stopLoss'
  | 'hotStreak'
  | 'dipBuyer'
  | 'degenMode'
  | 'luckyCharm'
  | 'copyTrader'
  | 'nightOwl'
  | 'whaleHunter'
  | 'rugRadar'
  | 'insider';

export type SkillTier = 'common' | 'normal' | 'rare';

export interface SkillDef {
  id: SkillId;
  name: string;
  description: string;
  tier: SkillTier;
}

/** Relative roll weight per tier. */
export const SKILL_WEIGHT: Record<SkillTier, number> = { common: 12, normal: 7, rare: 3 };

export const SKILLS: Record<SkillId, SkillDef> = {
  diamondHands: { id: 'diamondHands', tier: 'common', name: 'Diamond Hands', description: 'Never panics. Shifts last 20% longer, rest stays the same.' },
  powerNap: { id: 'powerNap', tier: 'common', name: 'Power Nap', description: 'Rests 15% faster.' },
  fastFingers: { id: 'fastFingers', tier: 'common', name: 'Fast Fingers', description: 'Walks 50% faster to the desk and to the casino.' },
  caffeine: { id: 'caffeine', tier: 'common', name: 'Caffeine', description: '+30% PROFIT for the first 10 minutes of a shift.' },
  stopLoss: { id: 'stopLoss', tier: 'common', name: 'Stop Loss', description: 'Half as many empty trades from RISK.' },
  hotStreak: { id: 'hotStreak', tier: 'normal', name: 'Hot Streak', description: 'Profit grows while it keeps trading: +6%, +11%, +15%, then +18%.' },
  dipBuyer: { id: 'dipBuyer', tier: 'normal', name: 'Dip Buyer', description: '+50% profit on coins that dropped more than 25%.' },
  degenMode: { id: 'degenMode', tier: 'normal', name: 'Degen Mode', description: '+20% PROFIT, +5% RISK.' },
  luckyCharm: { id: 'luckyCharm', tier: 'normal', name: 'Lucky Charm', description: '+5% chance of a x2 trade, no extra empty trades.' },
  copyTrader: { id: 'copyTrader', tier: 'normal', name: 'Copy Trader', description: '+3% profit for every other frog of yours trading in the same office.' },
  nightOwl: { id: 'nightOwl', tier: 'normal', name: 'Night Owl', description: '+15% profit at night (00:00 to 06:00 UTC).' },
  whaleHunter: { id: 'whaleHunter', tier: 'rare', name: 'Whale Hunter', description: '+50% profit while the big screen shows a pump.' },
  rugRadar: { id: 'rugRadar', tier: 'rare', name: 'Rug Radar', description: 'Rug pulls in Pump.fun never wipe its trades.' },
  insider: { id: 'insider', tier: 'rare', name: 'Insider', description: '5% chance a trade pays x3.' },
};

export const SKILL_IDS = Object.keys(SKILLS) as SkillId[];

/** Hot Streak: one step per 5 minutes of uninterrupted work. */
export const HOT_STREAK_STEPS = [0, 0.06, 0.11, 0.15, 0.18];
export const HOT_STREAK_STEP_MS = 5 * 60_000;

/** Picks `count` different skills, weighted by tier. */
export function rollSkills(count: number, rand: () => number): SkillId[] {
  const pool = [...SKILL_IDS];
  const out: SkillId[] = [];
  while (out.length < count && pool.length > 0) {
    const total = pool.reduce((s, id) => s + SKILL_WEIGHT[SKILLS[id].tier], 0);
    let roll = rand() * total;
    let pick = pool.length - 1;
    for (let i = 0; i < pool.length; i++) {
      roll -= SKILL_WEIGHT[SKILLS[pool[i]!].tier];
      if (roll < 0) {
        pick = i;
        break;
      }
    }
    out.push(pool[pick]!);
    pool.splice(pick, 1);
  }
  return out;
}
