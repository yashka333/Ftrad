import pg from 'pg';
import type { World } from '@frog-traders/shared';

/**
 * Keeps the world as one JSON row in Postgres. Same contract as JsonStore:
 * load once at start, save at most once a second, flush on shutdown.
 */
export class PgStore {
  private pool: pg.Pool;
  private timer: NodeJS.Timeout | null = null;
  private writing: Promise<void> = Promise.resolve();

  constructor(url: string) {
    const local = /localhost|127\.0\.0\.1/.test(url);
    this.pool = new pg.Pool({ connectionString: url, ssl: local ? false : { rejectUnauthorized: false }, max: 3 });
  }

  async load(): Promise<World | null> {
    await this.pool.query('create table if not exists world (id int primary key, data jsonb not null, saved_at timestamptz not null default now())');
    const r = await this.pool.query('select data from world where id = 1');
    return (r.rows[0]?.data as World) ?? null;
  }

  save(world: World): void {
    if (this.timer) return;
    this.timer = setTimeout(() => {
      this.timer = null;
      void this.flush(world);
    }, 1000);
  }

  flush(world: World): Promise<void> {
    const json = JSON.stringify(world);
    this.writing = this.writing
      .then(() => this.pool.query(
        'insert into world (id, data, saved_at) values (1, $1, now()) on conflict (id) do update set data = excluded.data, saved_at = now()',
        [json],
      ))
      .then(() => undefined)
      .catch((e) => console.error('world save failed', e));
    return this.writing;
  }

  async close(): Promise<void> {
    await this.writing;
    await this.pool.end();
  }
}
