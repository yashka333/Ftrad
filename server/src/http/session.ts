import type { FastifyReply, FastifyRequest } from 'fastify';
import { GameError } from '@frog-traders/shared';

export const SESSION_COOKIE = 'ft_session';

export function setSession(reply: FastifyReply, playerId: number, secure = false): void {
  reply.setCookie(SESSION_COOKIE, String(playerId), {
    path: '/',
    httpOnly: true,
    secure,
    sameSite: 'lax',
    signed: true,
    maxAge: 60 * 60 * 24 * 30,
  });
}

export function clearSession(reply: FastifyReply): void {
  reply.clearCookie(SESSION_COOKIE, { path: '/' });
}

/** Reads the signed session cookie set after a wallet sign-in. */
export function requirePlayerId(req: FastifyRequest): number {
  const raw = req.cookies[SESSION_COOKIE];
  if (!raw) throw new GameError('unauthorized', 401);
  const un = req.unsignCookie(raw);
  if (!un.valid || !un.value) throw new GameError('unauthorized', 401);
  return Number(un.value);
}
