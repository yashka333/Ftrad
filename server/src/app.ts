import fs from 'node:fs';
import Fastify from 'fastify';
import cookie from '@fastify/cookie';
import fastifyStatic from '@fastify/static';
import type { Env } from './env.js';
import { WorldService } from './game/worldService.js';
import { registerErrorHandler } from './http/errors.js';
import { devRoutes } from './routes/dev.js';
import { gameRoutes } from './routes/game.js';
import { sessionRoutes } from './routes/session.js';
import { authRoutes } from './routes/auth.js';

export async function buildApp(env: Env, world: WorldService) {
  const app = Fastify({ logger: { level: process.env.LOG_LEVEL ?? 'info' } });

  await app.register(cookie, { secret: env.sessionSecret });
  registerErrorHandler(app);

  app.addHook('onSend', async (_req, reply) => {
    reply.header('x-content-type-options', 'nosniff');
    reply.header('referrer-policy', 'no-referrer');
  });

  app.get('/api/health', async () => ({ status: 'ok', devMode: env.devMode, timeScale: env.timeScale }));
  authRoutes(app, world, env.secureCookies);
  sessionRoutes(app, world, env.nameLogin);
  gameRoutes(app, world);
  devRoutes(app, world, env.devMode, env.nameLogin);

  // In production the server also hands out the built game.
  if (fs.existsSync(env.clientDist)) {
    await app.register(fastifyStatic, { root: env.clientDist });
    app.setNotFoundHandler((req, reply) => {
      if (req.url.startsWith('/api/')) return reply.status(404).send({ error: 'not-found' });
      return reply.sendFile('index.html');
    });
  }

  return app;
}
