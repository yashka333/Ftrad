import type { FastifyInstance } from 'fastify';
import type { WorldService } from '../game/worldService.js';
import { clearSession, requirePlayerId, setSession } from '../http/session.js';

export function sessionRoutes(app: FastifyInstance, world: WorldService, nameLogin: boolean): void {
  // Name login is for tests and local play only; players sign in with a wallet.
  if (nameLogin) app.post<{ Body: { name: string } }>(
    '/api/session',
    {
      schema: {
        body: {
          type: 'object',
          required: ['name'],
          properties: { name: { type: 'string', maxLength: 40 } },
        },
      },
    },
    async (req, reply) => {
      const p = world.login(req.body.name);
      setSession(reply, p.id);
      return world.withPlayer(p.id, () => null).state;
    },
  );

  app.post('/api/session/sign-out', async (_req, reply) => {
    clearSession(reply);
    return { ok: true };
  });

  /** Who is signed in. Answers 200 either way, so the first visit does not log an error. */
  app.get('/api/me', async (req) => {
    try {
      const id = requirePlayerId(req);
      return { logged: true, state: world.withPlayer(id, () => null).state };
    } catch {
      return { logged: false };
    }
  });

  app.get('/api/state', async (req) => {
    const id = requirePlayerId(req);
    return world.withPlayer(id, () => null).state;
  });
}
