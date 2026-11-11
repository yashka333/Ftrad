import type { FastifyInstance, FastifyRequest } from 'fastify';
import {
  PATH_IDS,
  assignDesk,
  autoSeat,
  restAll,
  workAll,
  buyBoss,
  goWork,
  openPacks,
  rest,
  startWork,
  stop,
  toggleBoss,
  withdraw,
  GameError,
  buyListing,
  cancelListing,
  inviteSummary,
  listFrog,
  openFreePacks,
  publicListings,
} from '@frog-traders/shared';
import type { WorldService } from '../game/worldService.js';
import { requirePlayerId } from '../http/session.js';

const frogIdBody = {
  type: 'object',
  required: ['frogId'],
  properties: { frogId: { type: 'integer', minimum: 1 } },
} as const;

type FrogBody = { Body: { frogId: number } };

/**
 * Game commands. Each one returns { result, state } so the client never has
 * to guess what changed.
 */
export function gameRoutes(app: FastifyInstance, world: WorldService): void {
  const run = <T>(req: FastifyRequest, fn: Parameters<WorldService['withPlayer']>[1]) =>
    world.withPlayer(requirePlayerId(req), fn) as { result: T; state: unknown };

  app.post<{ Body: { count: number } }>(
    '/api/packs/open',
    {
      schema: {
        body: {
          type: 'object',
          required: ['count'],
          properties: { count: { type: 'integer', minimum: 1, maximum: 15 } },
        },
      },
    },
    async (req) =>
      run(req, (p, now) => openPacks(world.world, p, req.body.count, now, world.rand)),
  );

  app.post<{ Body: { frogId: number; path: (typeof PATH_IDS)[number]; desk?: number } }>(
    '/api/frogs/go-work',
    {
      schema: {
        body: {
          type: 'object',
          required: ['frogId', 'path'],
          properties: {
            frogId: { type: 'integer', minimum: 1 },
            path: { type: 'string', enum: PATH_IDS },
            desk: { type: 'integer', minimum: 0, maximum: 4 },
          },
        },
      },
    },
    async (req) =>
      run(req, (p, now) => goWork(p, req.body.frogId, req.body.path, now, req.body.desk)),
  );

  app.post<{ Body: { frogId: number; path: (typeof PATH_IDS)[number]; desk: number } }>(
    '/api/frogs/assign',
    {
      schema: {
        body: {
          type: 'object',
          required: ['frogId', 'path', 'desk'],
          properties: {
            frogId: { type: 'integer', minimum: 1 },
            path: { type: 'string', enum: PATH_IDS },
            desk: { type: 'integer', minimum: 0, maximum: 4 },
          },
        },
      },
    },
    async (req) => run(req, (p, now) => assignDesk(p, req.body.frogId, req.body.path, req.body.desk, now)),
  );
  app.post('/api/frogs/work-all', async (req) => run(req, (p, now) => workAll(p, now)));
  app.post('/api/frogs/rest-all', async (req) => run(req, (p, now) => restAll(p, now)));
  app.post<FrogBody>('/api/frogs/stop', { schema: { body: frogIdBody } }, async (req) =>
    run(req, (p, now) => stop(p, req.body.frogId, now)),
  );
  app.post<FrogBody>('/api/frogs/work', { schema: { body: frogIdBody } }, async (req) =>
    run(req, (p, now) => startWork(p, req.body.frogId, now)),
  );
  app.post<FrogBody>('/api/frogs/rest', { schema: { body: frogIdBody } }, async (req) =>
    run(req, (p, now) => rest(p, req.body.frogId, now)),
  );
  app.post('/api/frogs/auto-seat', async (req) => run(req, (p, now) => autoSeat(p, now)));

  app.post('/api/boss/buy', async (req) => run(req, (p) => buyBoss(world.world, p)));

  app.post<{ Body: { on: boolean } }>(
    '/api/boss/switch',
    {
      schema: {
        body: { type: 'object', required: ['on'], properties: { on: { type: 'boolean' } } },
      },
    },
    async (req) => run(req, (p) => toggleBoss(p, req.body.on)),
  );

  app.post('/api/withdrawals', async (req) => run(req, (p, now) => withdraw(world.world, p, now)));

  app.post<{ Body: { count: number } }>(
    '/api/packs/open-free',
    { schema: { body: { type: 'object', required: ['count'], properties: { count: { type: 'integer', minimum: 1, maximum: 100 } } } } },
    async (req) => run(req, (p, now) => openFreePacks(p, req.body.count, now, world.rand)),
  );

  // ---- invites
  app.get('/api/invite', async (req) => {
    const id = requirePlayerId(req);
    return world.read((w) => {
      const p = w.players[String(id)];
      if (!p) throw new GameError('unauthorized', 401);
      return inviteSummary(w, p);
    });
  });

  // ---- market: Legendary and Mythic only
  app.get('/api/market', async (req) => {
    requirePlayerId(req);
    return world.read((w) => ({ listings: publicListings(w) }));
  });
  app.post<{ Body: { frogId: number; price: number } }>(
    '/api/market/list',
    {
      schema: {
        body: {
          type: 'object',
          required: ['frogId', 'price'],
          properties: { frogId: { type: 'integer', minimum: 1 }, price: { type: 'integer', minimum: 1 } },
        },
      },
    },
    async (req) => run(req, (p, now) => listFrog(world.world, p, req.body.frogId, req.body.price, now)),
  );
  const listingBody = { type: 'object', required: ['listingId'], properties: { listingId: { type: 'integer', minimum: 1 } } } as const;
  app.post<{ Body: { listingId: number } }>('/api/market/cancel', { schema: { body: listingBody } },
    async (req) => run(req, (p, now) => cancelListing(world.world, p, req.body.listingId, now)));
  app.post<{ Body: { listingId: number } }>('/api/market/buy', { schema: { body: listingBody } },
    async (req) => run(req, (p, now) => buyListing(world.world, p, req.body.listingId, now)));
}
