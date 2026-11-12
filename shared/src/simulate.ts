import { ECONOMY, PATHS, PATH_IDS, SIM_STEP_MS } from './config.js';
import {
  bossActive,
  drainPerMin,
  hourUtc,
  maxStamina,
  officemates,
  profitPerHour,
  restPerMin,
} from './formulas.js';
import type { DeskSlot, Player, World } from './types.js';

/** Longest offline gap the server will catch up on in one go (7 days). */
const MAX_CATCH_UP_MS = 7 * 86_400_000;

/**
 * Moves the whole world forward to `now`. Everything that happens while a
 * player is away (trading, getting tired, resting) is computed here in fixed
 * steps, so the result does not depend on how often players log in.
 */
export function advanceWorld(world: World, now: number): void {
  let t = Math.max(world.lastTickAt, now - MAX_CATCH_UP_MS);
  while (t < now) {
    const dt = Math.min(SIM_STEP_MS, now - t);
    for (const p of Object.values(world.players)) world.totalPaidOut += stepPlayer(p, t, dt);
    t += dt;
  }
  world.lastTickAt = Math.max(world.lastTickAt, now);
}

function firstFreeDesk(p: Player): DeskSlot | null {
  for (const path of PATH_IDS) {
    for (let d = 0; d < PATHS[path].desks; d++) {
      if (!p.frogs.some((x) => x.desk?.path === path && x.desk.desk === d)) return { path, desk: d };
    }
  }
  return null;
}

function stepPlayer(p: Player, t0: number, dt: number): number {
  const boss = bossActive(p);
  const hour = hourUtc(t0);
  const t1 = t0 + dt;
  let earned = 0;

  for (const f of p.frogs) {
    const max = maxStamina(f);

    if (f.status === 'working' && f.desk) {
      const drain = (drainPerMin(f) * dt) / 60_000;
      let workMs = dt;
      if (f.stamina <= drain) {
        workMs = drain > 0 ? dt * (f.stamina / drain) : 0;
        f.stamina = 0;
      } else {
        f.stamina -= drain;
      }
      const rate = profitPerHour(f, {
        path: f.desk.path,
        workedMs: t0 - f.statusSince,
        officemates: officemates(p, f),
        hourUtc: hour,
      });
      const e = (rate * workMs) / 3_600_000;
      f.earned += e;
      earned += e;
      // Out of stamina: the frog walks to the casino by itself and frees its desk for the next one.
      if (f.stamina <= 0) {
        f.status = 'casino';
        f.statusSince = t0 + workMs;
        f.desk = null;
      }
      continue;
    }

    if (f.status === 'casino') {
      f.stamina = Math.min(max, f.stamina + (restPerMin(f) * dt) / 60_000);
      const home = f.home && !p.frogs.some((x) => x.desk?.path === f.home!.path && x.desk.desk === f.home!.desk) ? { ...f.home } : null;
      const free = boss && f.stamina >= max * ECONOMY.boss.returnAt ? home ?? firstFreeDesk(p) : null;
      if (free) {
        // The boss sends rested frogs back to any free desk.
        f.desk = free;
        f.status = 'working';
        f.statusSince = t1;
      } else if (f.stamina >= max) {
        f.status = f.desk ? 'ready' : 'idle';
        f.statusSince = t1;
      }
      continue;
    }

    // Ready or idle frogs sitting with a bit of stamina left: the boss puts them to work.
    if (boss && f.desk && f.status === 'ready' && f.stamina >= 1) {
      f.status = 'working';
      f.statusSince = t1;
    }
  }

  p.chest += earned;
  p.totalEarned += earned;
  return earned;
}
