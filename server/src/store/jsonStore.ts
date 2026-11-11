import fs from 'node:fs';
import path from 'node:path';
import type { World } from '@frog-traders/shared';

/**
 * Keeps the world in one JSON file. Good enough for stage 1 and local play.
 * Swap this class for a Postgres store later: the rest of the server only
 * talks to `load` and `save`.
 */
export class JsonStore {
  private timer: NodeJS.Timeout | null = null;

  constructor(private file: string) {}

  load(): World | null {
    if (!fs.existsSync(this.file)) return null;
    return JSON.parse(fs.readFileSync(this.file, 'utf8')) as World;
  }

  /** Writes at most once per second. A crash loses at most one second. */
  save(world: World): void {
    if (this.timer) return;
    this.timer = setTimeout(() => {
      this.timer = null;
      this.flush(world);
    }, 1000);
  }

  flush(world: World): void {
    fs.mkdirSync(path.dirname(this.file), { recursive: true });
    const tmp = `${this.file}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(world));
    fs.renameSync(tmp, this.file);
  }
}

/** Keeps everything in memory. Used by tests. */
export class MemoryStore {
  world: World | null = null;
  load() {
    return this.world;
  }
  save(world: World) {
    this.world = world;
  }
  flush(world: World) {
    this.world = world;
  }
}

export interface Store {
  load(): World | null | Promise<World | null>;
  save(world: World): void;
  flush(world: World): void | Promise<void>;
}
