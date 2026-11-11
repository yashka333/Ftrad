import {
  bossActive,
  bossPrice,
  casinoQueue,
  drainPerMin,
  hourUtc,
  maxStamina,
  officemates,
  profitPerHour,
  restMinutes,
  restPerMin,
  shiftMinutes,
} from './formulas.js';
import { nextWithdrawAt } from './actions.js';
import type { Player, PublicFrog, PublicState, World } from './types.js';

export function publicState(world: World, p: Player, now: number): PublicState {
  const queue = casinoQueue(p);
  const hour = hourUtc(now);

  const frogs: PublicFrog[] = p.frogs.map((f) => {
    const max = maxStamina(f);
    let ratePerHour = 0;
    let staminaPerMin = 0;
    const qi = queue.findIndex((x) => x.id === f.id);
    const casinoSeat = qi >= 0 ? qi : null;
    if (f.status === 'working' && f.desk) {
      ratePerHour = profitPerHour(f, {
        path: f.desk.path,
        workedMs: now - f.statusSince,
        officemates: officemates(p, f),
        hourUtc: hour,
      });
      staminaPerMin = -drainPerMin(f);
    } else if (f.status === 'casino' && f.stamina < max) {
      staminaPerMin = restPerMin(f);
    }
    return {
      ...f,
      maxStamina: max,
      ratePerHour,
      staminaPerMin,
      casinoSeat,
      shiftMinutes: shiftMinutes(f),
      restMinutes: restMinutes(f),
    };
  });

  const { frogs: _omit, ...rest } = p;
  return {
    serverNow: now,
    bossesSold: world.bossesSold,
    bossPrice: bossPrice(world.bossesSold) ?? 0,
    player: {
      ...rest,
      frogs,
      ratePerHour: frogs.reduce((s, f) => s + f.ratePerHour, 0),
      bossActive: bossActive(p),
      nextWithdrawAt: nextWithdrawAt(p),
    },
  };
}

/** Market listings as the client shows them. */
export function publicListings(world: World) {
  return world.market.map((l) => ({
    id: l.id,
    sellerId: l.sellerId,
    sellerName: l.sellerName,
    price: l.price,
    createdAt: l.createdAt,
    frog: { ...l.frog, maxStamina: maxStamina(l.frog), shiftMinutes: shiftMinutes(l.frog), restMinutes: restMinutes(l.frog) },
  }));
}

/** The invite screen: the player's code, free packs and every friend they brought. */
export function inviteSummary(world: World, p: Player) {
  const friends = Object.values(world.players)
    .filter((x) => x.referredBy === p.id)
    .map((x) => ({ name: x.name, bought: x.boughtFrogs, packs: x.refPacksGiven, nextAt: (Math.floor(x.boughtFrogs / 10) + 1) * 10 }));
  return { refCode: p.refCode, freePacks: p.freePacks, packsEarned: p.refPacksEarned, friends };
}
