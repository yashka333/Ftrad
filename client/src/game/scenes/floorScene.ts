import { Container } from 'pixi.js';
import { PATH_IDS, type PathId, type PublicFrog, type PublicState } from '@frog-traders/shared';
import { layout } from '../assets';
import { Floaters } from '../animations/floaters';
import { CasinoView } from '../objects/casino';
import type { DeskView } from '../objects/desk';
import { DormView } from '../objects/dorm';
import { OfficeView } from '../objects/office';

export interface SceneEvents {
  frog(id: number): void;
  emptyDesk(path: PathId, desk: number): void;
  casino(): void;
  dorm(): void;
}

/**
 * The whole trading floor: three offices on top, the dorm and the casino
 * below. `sync` places frogs from server state; `update` runs every frame.
 */
export class FloorScene extends Container {
  private offices: OfficeView[] = [];
  private dorm: DormView;
  private casino: CasinoView;
  private fx = new Floaters();
  private nextTrade = new Map<number, number>();
  private state: PublicState | null = null;

  constructor(private events: SceneEvents) {
    super();
    const back = new Container();
    const props = new Container();
    props.sortableChildren = true;
    const front = new Container();

    const onDesk = (d: DeskView) => {
      if (d.frogId !== null) events.frog(d.frogId);
      else events.emptyDesk(d.path, d.index);
    };
    for (const def of layout.offices) {
      const o = new OfficeView(def, props, onDesk);
      this.offices.push(o);
      back.addChild(o.back);
    }
    this.dorm = new DormView(() => events.dorm());
    this.casino = new CasinoView(() => events.casino());
    back.addChild(this.dorm.back, this.casino.back);
    front.addChild(this.casino.seats, this.casino.front, this.dorm.front);
    this.addChild(back, props, front, this.fx.layer);
  }

  sync(s: PublicState) {
    this.state = s;
    const frogs = s.player.frogs;
    const byDesk = new Map<string, PublicFrog>();
    for (const f of frogs) if (f.desk) byDesk.set(`${f.desk.path}:${f.desk.desk}`, f);
    for (const o of this.offices) {
      for (const d of o.desks) d.setFrog(byDesk.get(`${o.path}:${d.index}`) ?? null);
    }
    const sleepers = frogs
      .filter((f) => f.status === 'casino' && f.casinoSeat === null)
      .sort((a, b) => Number(!!b.desk) - Number(!!a.desk) || b.rarity - a.rarity);
    this.dorm.sync(sleepers);
    this.casino.sync(true, frogs, (id) => this.events.frog(id));
  }

  update(dt: number, now: number) {
    for (const o of this.offices) o.update(now);
    this.casino.update(now);
    this.dorm.update(now, this.fx);
    this.tradePopups(now);
    this.fx.update(dt);
  }

  /** "+0.42" above each working frog every time it closes a trade. */
  private tradePopups(now: number) {
    if (!this.state) return;
    for (const o of this.offices) {
      for (const d of o.desks) {
        if (d.mode !== 'working' || d.frogId === null) continue;
        const f = this.state.player.frogs.find((x) => x.id === d.frogId);
        if (!f) continue;
        const every = 6000; // one trade popup every few seconds, animation only
        const due = this.nextTrade.get(f.id) ?? now + Math.random() * every;
        if (now >= due) {
          const gain = (f.ratePerHour * every) / 3_600_000;
          this.fx.text(d.head.x, d.head.y, `+${gain >= 10 ? gain.toFixed(0) : gain.toFixed(2)}`, '#3ddc84');
          this.nextTrade.set(f.id, now + every * (0.8 + Math.random() * 0.4));
        } else if (!this.nextTrade.has(f.id)) {
          this.nextTrade.set(f.id, due);
        }
      }
    }
  }

  static readonly W = layout.scene.w;
  static readonly H = layout.scene.h;
  static readonly PATHS = PATH_IDS;
}
