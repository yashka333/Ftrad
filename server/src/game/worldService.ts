import { randomFillSync } from 'node:crypto';
import {
  advanceWorld,
  GameError,
  newPlayer,
  newWorld,
  publicState,
  type Player,
  type World,
} from '@frog-traders/shared';
import type { Store } from '../store/jsonStore.js';

/** Crypto-backed random numbers for summons. */
const buf = new Uint32Array(2);
export function secureRandom(): number {
  randomFillSync(buf);
  // 53 random bits -> [0, 1)
  return (buf[0]! * 2 ** 21 + (buf[1]! >>> 11)) / 2 ** 53;
}

/**
 * Owns the single world object. Every request goes through `withPlayer`,
 * which first moves the world to the current time, then runs the action,
 * then schedules a save.
 */
export class WorldService {
  readonly world: World;

  constructor(
    private store: Store,
    private devMode: boolean,
    private clock: () => number = Date.now,
    readonly rand: () => number = secureRandom,
    saved: World | null = null,
  ) {
    // Worlds saved by older economies (paid casinos, no market, 30 min shifts) start fresh.
    this.world = saved && saved.version === 5 ? saved : newWorld(clock());
  }

  static async open(store: Store, devMode: boolean, clock: () => number = Date.now): Promise<WorldService> {
    return new WorldService(store, devMode, clock, secureRandom, await store.load());
  }

  now(): number {
    return this.clock();
  }

  tick(): void {
    advanceWorld(this.world, this.now());
    this.store.save(this.world);
  }

  login(name: string): Player {
    const clean = name.trim();
    if (!/^[\p{L}\p{N} .\-_]{3,20}$/u.test(clean)) throw new GameError('bad-name');
    this.tick();
    const existing = Object.values(this.world.players).find(
      (p) => p.name.toLowerCase() === clean.toLowerCase(),
    );
    const p = existing ?? newPlayer(this.world, clean, this.now(), this.devMode, { refCode: this.newRefCode() });
    p.lastSeenAt = this.now();
    this.store.save(this.world);
    return p;
  }

  /** Signs in with a Solana address. New players get a short name from the address and keep the inviter from ?ref=. */
  loginWallet(address: string, ref?: string | null): Player {
    this.tick();
    const existing = Object.values(this.world.players).find((p) => p.address === address);
    if (existing) {
      existing.lastSeenAt = this.now();
      this.store.save(this.world);
      return existing;
    }
    const inviter = ref ? Object.values(this.world.players).find((p) => p.refCode === ref) : undefined;
    const name = `${address.slice(0, 4)}...${address.slice(-4)}`;
    const p = newPlayer(this.world, name, this.now(), this.devMode, {
      address,
      refCode: this.newRefCode(),
      referredBy: inviter?.id ?? null,
    });
    this.store.save(this.world);
    return p;
  }

  private newRefCode(): string {
    const abc = 'abcdefghjkmnpqrstuvwxyz23456789';
    for (;;) {
      let code = '';
      for (let i = 0; i < 7; i++) code += abc[Math.floor(this.rand() * abc.length)];
      if (!Object.values(this.world.players).some((p) => p.refCode === code)) return code;
    }
  }

  /** Runs a read against the world after moving it to now. */
  read<T>(fn: (world: World, now: number) => T): T {
    const now = this.now();
    advanceWorld(this.world, now);
    return fn(this.world, now);
  }

  withPlayer<T>(playerId: number, fn: (p: Player, now: number) => T): { result: T; state: ReturnType<typeof publicState> } {
    const now = this.now();
    advanceWorld(this.world, now);
    const p = this.world.players[String(playerId)];
    if (!p) throw new GameError('unauthorized', 401);
    p.lastSeenAt = now;
    const result = fn(p, now);
    this.store.save(this.world);
    return { result, state: publicState(this.world, p, now) };
  }

  flush(): void | Promise<void> {
    return this.store.flush(this.world);
  }
}
