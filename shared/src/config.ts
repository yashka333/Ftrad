/**
 * Every number that shapes the economy lives here (rarity numbers live in
 * rarity.ts), so balancing the game means editing one or two files.
 * Server and client both read it.
 */

export const TOKEN = {
  symbol: 'FROG',
  name: 'Frogotraderz',
} as const;

export type PathId = 'memecoin' | 'pumpfun' | 'classic';

export interface PathDef {
  id: PathId;
  name: string;
  blurb: string;
  desks: number;
  /** Accent color of the office (hex). */
  color: string;
  /** Profit multiplier of the office. Pump.fun pays more to make up for rugs. */
  profit: number;
  /** Share of trades that hit a pump (Whale Hunter), a dip (Dip Buyer) or a rug (zero, unless Rug Radar). */
  pumpRate: number;
  dipRate: number;
  rugRate: number;
}

export const PATHS: Record<PathId, PathDef> = {
  memecoin: {
    id: 'memecoin', name: 'Memecoin Trading', blurb: 'Ape into fresh memecoins and ride the pumps.',
    desks: 5, color: '#e8662f', profit: 1, pumpRate: 0.12, dipRate: 0.1, rugRate: 0,
  },
  pumpfun: {
    id: 'pumpfun', name: 'Pump.fun Rugs', blurb: 'Snipe new launches and get out before the rug.',
    desks: 5, color: '#9a5cf0', profit: 1.09, pumpRate: 0.1, dipRate: 0.08, rugRate: 0.08,
  },
  classic: {
    id: 'classic', name: 'Classic Trading', blurb: 'Charts, patterns and patience.',
    desks: 5, color: '#3cc6a8', profit: 1, pumpRate: 0.05, dipRate: 0.12, rugRate: 0,
  },
};

export const PATH_IDS: PathId[] = ['memecoin', 'pumpfun', 'classic'];

/** Market: only the two top rarities can be traded. The fee is burned. */
export const MARKET = {
  minRarity: 4,
  feeRate: 0.05,
  minPrice: 1_000,
  maxPrice: 1_000_000_000,
  maxListings: 20,
} as const;

/** Invites: when a friend has bought 10 frogs the inviter gets 1 free pack, then 2 for every next 10. */
export const INVITE = {
  step: 10,
  firstReward: 1,
  nextReward: 2,
} as const;

export const ECONOMY = {
  packPrice: 10_000,
  packSizes: [1, 5, 10, 15],
  maxFrogs: 500,
  /** Test tokens a new account gets while DEV_MODE is on. */
  devStartingWallet: 500_000,
  devFaucetAmount: 250_000,
  withdraw: {
    min: 100_000,
    max: 10_000_000,
    feeRate: 0.03,
    cooldownMs: 86_400_000,
    walletHoldMin: 2_500,
  },
  boss: {
    /** Boss Frogs NFT collection size. */
    supply: 250,
    /** Stage 1 price in $FROG (the real sale is 1 SOL or token, WL discount). */
    price: 500_000,
    /** The boss sends a frog back to its desk once it has this share of stamina. */
    returnAt: 0.8,
  },
} as const;

export const STAMINA = {
  /** Stamina bar = PATIENCE x this. */
  perPatience: 5,
} as const;

/** Odds of the extra trade outcomes. */
export const TRADES = {
  /** Half of RISK turns into empty trades (no profit). */
  emptyShareOfRisk: 0.5,
  degenProfit: 0.2,
  degenRisk: 5,
  luckyRisk: 5,
  caffeineBonus: 0.3,
  caffeineMs: 10 * 60_000,
  dipBonus: 0.5,
  whaleBonus: 0.5,
  copyBonus: 0.03,
  nightBonus: 0.15,
  insiderChance: 0.05,
  insiderMultiplier: 3,
  diamondShift: 1.2,
  napRest: 0.85,
} as const;

/** The server advances the world in steps of this size. */
export const SIM_STEP_MS = 30_000;
