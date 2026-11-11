import type { PathId } from './config.js';
import type { SkillId } from './skills.js';

/**
 * idle: no desk or stopped. working: at its desk, trading.
 * casino: resting (frogs go there by themselves when tired). ready: rested, waiting at its desk.
 */
export type FrogStatus = 'idle' | 'working' | 'casino' | 'ready';

export interface FrogStats {
  /** How long it works and rests. Stamina bar = PATIENCE x 5. */
  patience: number;
  /** $FROG per hour of work. */
  profit: number;
  /** Chance in % of a x2 trade. Half as many trades come out empty. */
  risk: number;
}

export interface DeskSlot {
  path: PathId;
  desk: number;
}

export interface Frog {
  id: number;
  name: string;
  rarity: number;
  /** Skin color variant, 0..3. */
  skin: number;
  stats: FrogStats;
  skills: SkillId[];
  stamina: number;
  status: FrogStatus;
  /** When the current status started (ms). Used for Caffeine, Hot Streak and the casino queue. */
  statusSince: number;
  /** Desk the frog owns. It keeps the desk while it rests. */
  desk: DeskSlot | null;
  earned: number;
  bornAt: number;
}

export interface Withdrawal {
  id: number;
  createdAt: number;
  gross: number;
  fee: number;
  net: number;
  state: 'paid';
}

export interface Player {
  id: number;
  name: string;
  /** Solana address the player signed in with (null for test accounts). */
  address: string | null;
  /** Code in the player's invite link. */
  refCode: string;
  /** Player who invited this one. */
  referredBy: number | null;
  /** Frogs bought with paid packs (free packs do not count). Drives the inviter's reward. */
  boughtFrogs: number;
  /** Free packs this player has already earned for their inviter. */
  refPacksGiven: number;
  /** Free packs waiting to be opened. */
  freePacks: number;
  /** Free packs earned from invites, all time. */
  refPacksEarned: number;
  createdAt: number;
  lastSeenAt: number;
  /** Tokens in the player's wallet. Stage 1: simulated. */
  wallet: number;
  /** Tokens earned in the game and not withdrawn yet. */
  chest: number;
  frogs: Frog[];
  nextFrogId: number;
  /** Boss Frog NFTs owned. One is enough to automate every office. */
  bosses: number;
  bossOn: boolean;
  withdrawals: Withdrawal[];
  lastWithdrawAt: number | null;
  totalEarned: number;
}

/** A Legendary or Mythic frog up for sale. The frog leaves the seller's crew while it is listed. */
export interface Listing {
  id: number;
  sellerId: number;
  sellerName: string;
  price: number;
  createdAt: number;
  frog: Frog;
}

export interface World {
  version: 5;
  createdAt: number;
  lastTickAt: number;
  totalPaidOut: number;
  totalSpent: number;
  bossesSold: number;
  /** Market fees burned, all time. */
  totalBurned: number;
  market: Listing[];
  nextListingId: number;
  nextPlayerId: number;
  players: Record<string, Player>;
}

/** What the client receives. */
export interface PublicFrog extends Frog {
  maxStamina: number;
  /** Tokens per hour at this moment (0 when not working). */
  ratePerHour: number;
  /** Stamina change per minute at this moment. */
  staminaPerMin: number;
  /** Seat number in the casino, or null while resting in the lobby. */
  casinoSeat: number | null;
  /** Full shift and full rest of this frog, in minutes. */
  shiftMinutes: number;
  restMinutes: number;
}

export interface PublicState {
  serverNow: number;
  bossesSold: number;
  bossPrice: number;
  player: Omit<Player, 'frogs'> & {
    frogs: PublicFrog[];
    ratePerHour: number;
    bossActive: boolean;
    nextWithdrawAt: number | null;
  };
}
