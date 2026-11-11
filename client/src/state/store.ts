import type { PublicFrog, PublicState } from '@frog-traders/shared';
import { api, ApiError, type CommandResult } from '../api/client';
import { toast } from '../ui/components/toast';

type Listener = (s: PublicState) => void;

const POLL_MS = 5_000;

/**
 * Holds the latest server state and keeps the client clock in step with the
 * server. Between polls the HUD and the scene extrapolate from the rates the
 * server sent (tokens per hour, stamina per minute).
 */
export class Store {
  state: PublicState;
  devMode = false;
  /** serverNow - Date.now() at the moment the state arrived. */
  private offset = 0;
  private receivedAt = 0;
  private listeners = new Set<Listener>();
  private timer: number | undefined;

  constructor(initial: PublicState) {
    this.state = initial;
    this.accept(initial);
  }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn);
    fn(this.state);
    return () => this.listeners.delete(fn);
  }

  private accept(s: PublicState) {
    this.state = s;
    this.receivedAt = Date.now();
    this.offset = s.serverNow - this.receivedAt;
    for (const fn of this.listeners) fn(s);
  }

  start() {
    this.stop();
    this.timer = window.setInterval(() => void this.refresh(), POLL_MS);
    document.addEventListener('visibilitychange', this.onVisible);
  }

  stop() {
    if (this.timer) window.clearInterval(this.timer);
    document.removeEventListener('visibilitychange', this.onVisible);
  }

  private onVisible = () => {
    if (document.visibilityState === 'visible') void this.refresh();
  };

  async refresh() {
    try {
      this.accept(await api.state());
    } catch (e) {
      if (e instanceof ApiError && e.code === 'unauthorized') location.reload();
    }
  }

  /** Runs a command, shows its error as a toast, and returns null on failure. */
  async run<T>(call: () => Promise<CommandResult<T>>): Promise<T | null> {
    try {
      const out = await call();
      this.accept(out.state);
      return out.result;
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Something went wrong.', 'error');
      return null;
    }
  }

  /** Re-renders listeners without a network call (UI-only changes). */
  poke() {
    for (const fn of this.listeners) fn(this.state);
  }

  serverNow(): number {
    return Date.now() + this.offset;
  }

  /** Seconds since the last state arrived. */
  elapsedSec(): number {
    return (Date.now() - this.receivedAt) / 1000;
  }

  liveChest(): number {
    return this.state.player.chest + (this.state.player.ratePerHour * this.elapsedSec()) / 3600;
  }

  liveStamina(f: PublicFrog): number {
    const v = f.stamina + (f.staminaPerMin * this.elapsedSec()) / 60;
    return Math.max(0, Math.min(f.maxStamina, v));
  }

  frog(id: number): PublicFrog | undefined {
    return this.state.player.frogs.find((f) => f.id === id);
  }
}
