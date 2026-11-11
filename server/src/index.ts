import { buildApp } from './app.js';
import { loadEnv } from './env.js';
import { WorldService } from './game/worldService.js';
import { JsonStore, type Store } from './store/jsonStore.js';
import { PgStore } from './store/pgStore.js';

const env = loadEnv();
const store: Store & { close?: () => Promise<void> } = env.databaseUrl ? new PgStore(env.databaseUrl) : new JsonStore(env.dataFile);

// Game clock. TIME_SCALE > 1 speeds the world up for testing; it is anchored to the start so it never jumps.
const start = Date.now();
const clock = env.timeScale === 1 ? Date.now : () => start + (Date.now() - start) * env.timeScale;

const world = await WorldService.open(store, env.devMode, clock);
const app = await buildApp(env, world);

// Keep the world moving even when nobody is online.
const ticker = setInterval(() => world.tick(), 30_000);

async function shutdown() {
  clearInterval(ticker);
  world.tick();
  await world.flush();
  await store.close?.();
  await app.close();
  process.exit(0);
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

await app.listen({ port: env.port, host: '0.0.0.0' });
app.log.info(`Frogotraderz server on http://localhost:${env.port} (dev mode ${env.devMode}, ${env.databaseUrl ? 'postgres' : 'json file'}, time x${env.timeScale})`);
