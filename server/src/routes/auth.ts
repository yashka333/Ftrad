import { randomBytes } from 'node:crypto';
import bs58 from 'bs58';
import nacl from 'tweetnacl';
import type { FastifyInstance } from 'fastify';
import { GameError } from '@frog-traders/shared';
import type { WorldService } from '../game/worldService.js';
import { setSession } from '../http/session.js';

const NONCE_TTL = 5 * 60_000;
const ADDRESS = '^[1-9A-HJ-NP-Za-km-z]{32,44}$';

/** The exact text Phantom shows the player. The server rebuilds it to check the signature. */
export function signInMessage(address: string, nonce: string, host: string): string {
  return [
    'Frogotraderz wants you to sign in with your Solana account:',
    address,
    '',
    'This only proves you own the wallet. It costs nothing and sends no transaction.',
    '',
    `Domain: ${host}`,
    `Nonce: ${nonce}`,
  ].join('\n');
}

/**
 * Sign in with Phantom: the client asks for a one-time message, the wallet signs it,
 * the server checks the ed25519 signature against the address and opens a session.
 */
export function authRoutes(app: FastifyInstance, world: WorldService, secureCookies: boolean): void {
  const nonces = new Map<string, { nonce: string; host: string; expires: number }>();

  app.post<{ Body: { address: string } }>(
    '/api/auth/nonce',
    { schema: { body: { type: 'object', required: ['address'], properties: { address: { type: 'string', pattern: ADDRESS } } } } },
    async (req) => {
      const now = Date.now();
      for (const [k, v] of nonces) if (v.expires < now) nonces.delete(k);
      if (nonces.size > 10_000) throw new GameError('rate-limited', 429);
      const nonce = randomBytes(16).toString('hex');
      const host = req.headers.host ?? 'frogotraderz';
      nonces.set(req.body.address, { nonce, host, expires: now + NONCE_TTL });
      return { message: signInMessage(req.body.address, nonce, host) };
    },
  );

  app.post<{ Body: { address: string; signature: string; ref?: string } }>(
    '/api/auth/verify',
    {
      schema: {
        body: {
          type: 'object',
          required: ['address', 'signature'],
          properties: {
            address: { type: 'string', pattern: ADDRESS },
            signature: { type: 'string', maxLength: 200 },
            ref: { type: 'string', maxLength: 20 },
          },
        },
      },
    },
    async (req, reply) => {
      const { address, signature, ref } = req.body;
      const n = nonces.get(address);
      nonces.delete(address);
      if (!n || n.expires < Date.now()) throw new GameError('nonce-expired', 401);
      let ok = false;
      try {
        const msg = new TextEncoder().encode(signInMessage(address, n.nonce, n.host));
        const key = bs58.decode(address);
        const sig = bs58.decode(signature);
        ok = key.length === 32 && sig.length === 64 && nacl.sign.detached.verify(msg, sig, key);
      } catch {
        ok = false;
      }
      if (!ok) throw new GameError('bad-signature', 401);
      const p = world.loginWallet(address, ref ?? null);
      setSession(reply, p.id, secureCookies);
      return world.withPlayer(p.id, () => null).state;
    },
  );
}
