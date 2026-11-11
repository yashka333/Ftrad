import bs58 from 'bs58';
import nacl from 'tweetnacl';
import { describe, expect, it } from 'vitest';
import { mulberry32 } from '@frog-traders/shared';
import { buildApp } from '../src/app.js';
import { WorldService } from '../src/game/worldService.js';
import { MemoryStore } from '../src/store/jsonStore.js';

const env = {
  port: 0, sessionSecret: 'test-secret-test-secret-test-secret', dataFile: '', databaseUrl: null,
  devMode: true, nameLogin: false, timeScale: 1, secureCookies: false, clientDist: '/nope',
};

async function setup() {
  const world = new WorldService(new MemoryStore(), true, () => 1_700_000_000_000, mulberry32(9));
  const app = await buildApp(env, world);
  /** Signs in like Phantom does: fetch the message, sign it, send the signature. */
  async function signIn(ref?: string) {
    const kp = nacl.sign.keyPair();
    const address = bs58.encode(kp.publicKey);
    const n = await app.inject({ method: 'POST', url: '/api/auth/nonce', payload: { address } });
    const sig = nacl.sign.detached(new TextEncoder().encode(n.json().message), kp.secretKey);
    const v = await app.inject({ method: 'POST', url: '/api/auth/verify', payload: { address, signature: bs58.encode(sig), ref } });
    const cookie = v.cookies.map((c) => `${c.name}=${c.value}`).join('; ');
    const post = (url: string, payload?: object) => app.inject({ method: 'POST', url, payload: payload ?? {}, headers: { cookie } });
    const get = (url: string) => app.inject({ method: 'GET', url, headers: { cookie } });
    return { v, address, post, get, kp };
  }
  return { app, world, signIn };
}

describe('wallet sign-in', () => {
  it('accepts a real signature and rejects a forged one', async () => {
    const { app, signIn } = await setup();
    const a = await signIn();
    expect(a.v.statusCode).toBe(200);
    expect(a.v.json().player.address).toBe(a.address);
    expect(a.v.json().player.name).toMatch(/^.{4}\.\.\..{4}$/);

    const other = nacl.sign.keyPair();
    await app.inject({ method: 'POST', url: '/api/auth/nonce', payload: { address: a.address } });
    const forged = nacl.sign.detached(new TextEncoder().encode('anything'), other.secretKey);
    const bad = await app.inject({ method: 'POST', url: '/api/auth/verify', payload: { address: a.address, signature: bs58.encode(forged) } });
    expect(bad.statusCode).toBe(401);
    expect(bad.json().error).toBe('bad-signature');
  });

  it('a nonce works once', async () => {
    const { app } = await setup();
    const kp = nacl.sign.keyPair();
    const address = bs58.encode(kp.publicKey);
    const n = await app.inject({ method: 'POST', url: '/api/auth/nonce', payload: { address } });
    const signature = bs58.encode(nacl.sign.detached(new TextEncoder().encode(n.json().message), kp.secretKey));
    expect((await app.inject({ method: 'POST', url: '/api/auth/verify', payload: { address, signature } })).statusCode).toBe(200);
    expect((await app.inject({ method: 'POST', url: '/api/auth/verify', payload: { address, signature } })).statusCode).toBe(401);
  });

  it('name login is off unless enabled', async () => {
    const { app } = await setup();
    const res = await app.inject({ method: 'POST', url: '/api/session', payload: { name: 'jam' } });
    expect(res.statusCode).toBe(404);
  });
});

describe('invites and market over the api', () => {
  it('a friend from an invite link earns the inviter a free pack', async () => {
    const { signIn } = await setup();
    const inviter = await signIn();
    const code = inviter.v.json().player.refCode;
    const friend = await signIn(code);
    expect((await friend.post('/api/packs/open', { count: 10 })).statusCode).toBe(200);
    const inv = (await inviter.get('/api/invite')).json();
    expect(inv.freePacks).toBe(1);
    expect(inv.friends).toHaveLength(1);
    const open = await inviter.post('/api/packs/open-free', { count: 1 });
    expect(open.statusCode).toBe(200);
    expect(open.json().result).toHaveLength(1);
  });

  it('lists and sells a Legendary frog between two wallets', async () => {
    const { signIn, world } = await setup();
    const seller = await signIn();
    const buyer = await signIn();
    const sp = Object.values(world.world.players).find((p) => p.address === seller.address)!;
    await seller.post('/api/packs/open', { count: 1 });
    sp.frogs[0]!.rarity = 4;
    const listed = await seller.post('/api/market/list', { frogId: sp.frogs[0]!.id, price: 20_000 });
    expect(listed.statusCode).toBe(200);
    const market = (await buyer.get('/api/market')).json();
    expect(market.listings).toHaveLength(1);
    const bought = await buyer.post('/api/market/buy', { listingId: market.listings[0].id });
    expect(bought.statusCode).toBe(200);
    expect(bought.json().state.player.frogs).toHaveLength(1);
    expect((await buyer.get('/api/market')).json().listings).toHaveLength(0);
  });
});
