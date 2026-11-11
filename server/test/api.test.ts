import { describe, expect, it } from 'vitest';
import { mulberry32 } from '@frog-traders/shared';
import { buildApp } from '../src/app.js';
import { WorldService } from '../src/game/worldService.js';
import { MemoryStore } from '../src/store/jsonStore.js';

async function setup() {
  let now = 1_700_000_000_000;
  const world = new WorldService(new MemoryStore(), true, () => now, mulberry32(3));
  const app = await buildApp(
    { port: 0, sessionSecret: 'test-secret-test-secret-test-secret', dataFile: '', databaseUrl: null, devMode: true, nameLogin: true, timeScale: 1, secureCookies: false, clientDist: '/nope' },
    world,
  );
  const login = await app.inject({ method: 'POST', url: '/api/session', payload: { name: 'jam' } });
  const cookie = login.cookies.map((c) => `${c.name}=${c.value}`).join('; ');
  const post = (url: string, payload?: object) =>
    app.inject({ method: 'POST', url, payload: payload ?? {}, headers: { cookie } });
  return { app, post, cookie, advance: (ms: number) => (now += ms), login };
}

describe('api', () => {
  it('rejects requests without a session', async () => {
    const { app } = await setup();
    const res = await app.inject({ method: 'GET', url: '/api/state' });
    expect(res.statusCode).toBe(401);
    expect(res.json().error).toBe('unauthorized');
  });

  it('runs a full loop: summon, seat, earn, withdraw rules', async () => {
    const { post, advance, app, cookie } = await setup();
    const s = await post('/api/packs/open', { count: 5 });
    expect(s.statusCode).toBe(200);
    expect(s.json().result).toHaveLength(5);

    const seat = await post('/api/frogs/auto-seat');
    expect(seat.json().result).toBe(5);

    advance(40_000);
    const st = await app.inject({ method: 'GET', url: '/api/state', headers: { cookie } });
    const state = st.json();
    expect(state.player.chest).toBeGreaterThan(0);
    expect(state.player.frogs.filter((f: { status: string }) => f.status === 'working')).toHaveLength(5);

    const w = await post('/api/withdrawals');
    expect(w.statusCode).toBe(400);
    expect(w.json().error).toBe('below-withdrawal-minimum');
  });

  it('validates request bodies', async () => {
    const { post } = await setup();
    const res = await post('/api/frogs/go-work', { frogId: 1, path: 'casino' });
    expect(res.statusCode).toBe(400);
    expect(res.json().error).toBe('invalid-request');
  });
});

describe('secure random', () => {
  it('returns numbers in [0, 1)', async () => {
    const { secureRandom } = await import('../src/game/worldService.js');
    for (let i = 0; i < 1000; i++) {
      const v = secureRandom();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });
});
