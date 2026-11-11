import type { FastifyInstance } from 'fastify';
import { createFrog, devFaucet, GameError } from '@frog-traders/shared';
import type { WorldService } from '../game/worldService.js';
import { requirePlayerId } from '../http/session.js';

/** Test helpers. Only registered when DEV_MODE=true. */
export function devRoutes(app: FastifyInstance, world: WorldService, devMode: boolean, localOnly = false): void {
  // Local testing only (never on a hosted server): hand out a frog of a given rarity.
  if (localOnly) app.post<{ Body: { rarity: number } }>('/api/dev/grant-frog', async (req) =>
    world.withPlayer(requirePlayerId(req), (p, now) => {
      const f = createFrog(p.nextFrogId++, now, world.rand, Math.max(0, Math.min(5, Number(req.body.rarity) | 0)));
      p.frogs.push(f);
      return f;
    }));
  app.post('/api/dev/faucet', async (req) => {
    if (!devMode) throw new GameError('dev-only', 403);
    return world.withPlayer(requirePlayerId(req), (p) => devFaucet(p));
  });
}
