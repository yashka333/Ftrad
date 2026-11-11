import type { FastifyError, FastifyInstance } from 'fastify';
import { GameError } from '@frog-traders/shared';

/** Every error leaves the server as { error: code, message }. */
export function registerErrorHandler(app: FastifyInstance): void {
  app.setErrorHandler((err: FastifyError | GameError, req, reply) => {
    if (err instanceof GameError) {
      return reply.status(err.status).send({ error: err.code, message: err.message });
    }
    if ((err as FastifyError).validation) {
      return reply.status(400).send({ error: 'invalid-request', message: err.message });
    }
    req.log.error(err);
    return reply.status(500).send({ error: 'internal', message: 'Something went wrong.' });
  });
}
