import { Container, Rectangle, Sprite, Text } from 'pixi.js';
import type { PublicFrog } from '@frog-traders/shared';
import { layout, tex } from '../assets';
import { FrogActor } from './frogActor';
import type { Floaters } from '../animations/floaters';

interface Bed {
  slot: Container;
  actor: FrogActor | null;
  blanket: Sprite | null;
  frogId: number | null;
}

/** Bunk beds where tired frogs sleep. Shows up to 8, then "+N". */
export class DormView {
  readonly back = new Container();
  readonly front = new Container();
  private beds: Bed[] = [];
  private more: Text;
  private nextZ = 0;

  constructor(onTap: () => void) {
    const d = layout.dorm;
    const bg = new Sprite(tex('scenes/dorm'));
    bg.position.set(d.x, d.y);
    bg.eventMode = 'static';
    bg.cursor = 'pointer';
    bg.hitArea = new Rectangle(0, 0, d.w, d.h);
    bg.on('pointertap', onTap);
    this.back.addChild(bg);
    for (const _b of d.beds) {
      const slot = new Container();
      this.front.addChild(slot);
      this.beds.push({ slot, actor: null, blanket: null, frogId: null });
    }
    this.more = new Text({
      text: '',
      style: { fontFamily: 'Silkscreen', fontSize: 8, fill: '#f7d774', stroke: { color: '#1a1410', width: 2 } },
      resolution: 2,
    });
    this.more.position.set(d.x + 150, d.y + 8);
    this.front.addChild(this.more);
  }

  sync(sleepers: PublicFrog[]) {
    const d = layout.dorm;
    this.beds.forEach((bed, i) => {
      const f = sleepers[i];
      const pos = d.beds[i]!;
      if (!f) {
        bed.actor?.destroy({ children: true });
        bed.blanket?.destroy();
        bed.actor = null;
        bed.blanket = null;
        bed.frogId = null;
        return;
      }
      if (!bed.actor) {
        bed.actor = new FrogActor(f.skin, f.rarity, 'sleep');
        bed.actor.position.set(pos.frog.x, pos.frog.y);
        bed.blanket = new Sprite(tex(`sprites/blanket-${f.rarity}`));
        bed.blanket.position.set(pos.blanket.x, pos.blanket.y);
        bed.slot.addChild(bed.actor, bed.blanket);
      } else {
        bed.actor.set(f.skin, f.rarity, 'sleep');
        bed.blanket!.texture = tex(`sprites/blanket-${f.rarity}`);
      }
      bed.frogId = f.id;
    });
    const extra = sleepers.length - this.beds.length;
    this.more.text = extra > 0 ? `+${extra} SLEEPING` : '';
  }

  /** Puffs of Zzz above sleeping frogs. */
  update(now: number, fx: Floaters) {
    if (now < this.nextZ) return;
    this.nextZ = now + 500 + Math.random() * 700;
    const busy = this.beds.filter((b) => b.frogId !== null);
    const b = busy[Math.floor(Math.random() * busy.length)];
    if (!b?.actor) return;
    fx.sprite(tex('sprites/zzz'), b.actor.x + 18, b.actor.y + 2, 2.4, 4);
  }
}
