import 'dotenv/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export interface Env {
  port: number;
  sessionSecret: string;
  /** JSON file used when no DATABASE_URL is set. */
  dataFile: string;
  /** Postgres connection string. When set, the world is stored there (survives restarts on free hosts). */
  databaseUrl: string | null;
  /** Test tokens for new accounts and the TEST DEPOSIT button. On for the prototype. */
  devMode: boolean;
  /** Lets tests and local play log in with a name instead of a wallet. Never on in production. */
  nameLogin: boolean;
  /** Game time runs this many times faster than real time (testing only). */
  timeScale: number;
  secureCookies: boolean;
  clientDist: string;
}

export function loadEnv(): Env {
  const prod = process.env.NODE_ENV === 'production';
  const secret = process.env.SESSION_SECRET ?? '';
  if (prod && secret.length < 32) throw new Error('SESSION_SECRET must be set to 32+ characters in production.');
  return {
    port: Number(process.env.PORT ?? 8787),
    sessionSecret: secret || 'dev-secret-change-me-dev-secret-change-me',
    dataFile: path.resolve(root, process.env.DATA_FILE ?? './data/world.json'),
    databaseUrl: process.env.DATABASE_URL || null,
    devMode: (process.env.DEV_MODE ?? 'true') === 'true',
    nameLogin: !prod && (process.env.NAME_LOGIN ?? 'true') === 'true',
    timeScale: Math.max(1, Number(process.env.TIME_SCALE ?? 1)),
    secureCookies: prod,
    clientDist: path.resolve(root, process.env.CLIENT_DIST ?? './public'),
  };
}
