import { AnimatedSprite, Container, Rectangle, Sprite, Text } from 'pixi.js';
import type { PublicFrog } from '@frog-traders/shared';
import { frames, layout, tex } from '../assets';
import { Flicker } from '../animations/flicker';
import { FrogActor } from './frogActor';

/**
 * The casino is where tired frogs recover faster (Mini Hero's forge).
 * Closed and boarded up until the player buys one.
 */
export class CasinoView {
  readonly back = new Container();
  readonly seats = new Container();
  readonly front = new Container();
  private bg: Sprite;
  private sign: Sprite;
  private forSale: Sprite;
  private roulette: AnimatedSprite;
  private lights: AnimatedSprite[] = [];
  private flicker: Flicker;
  private actors = new Map<number, FrogActor>();
  private frontArt: Sprite;
  private queue: Text;
  private open = false;

  constructor(onTap: () => void) {
    const c = layout.casino;
    this.bg = new Sprite(tex('scenes/casino-closed'));
    this.bg.position.set(c.x, c.y);
    this.bg.eventMode = 'static';
    this.bg.cursor = 'pointer';
    this.bg.hitArea = new Rectangle(0, 0, c.w, c.h);
    this.bg.on('pointertap', onTap);
    const on = tex('scenes/casino-sign-on');
    const off = tex('scenes/casino-sign-off');
    this.sign = new Sprite(off);
    this.sign.position.set(c.sign.x, c.sign.y);
    this.flicker = new Flicker((lit) => {
      if (this.open) this.sign.texture = lit ? on : off;
    });
    this.back.addChild(this.bg, this.sign);
    for (const p of c.slotLights) {
      const l = new AnimatedSprite(frames('sprites/slot-lights', 16, 4));
      l.position.set(p.x, p.y);
      l.animationSpeed = 0.06;
      this.lights.push(l);
      this.back.addChild(l);
    }
    this.frontArt = new Sprite(tex('scenes/casino-front'));
    this.frontArt.position.set(c.x, c.y);
    this.roulette = new AnimatedSprite(frames('sprites/roulette', 28, 16));
    this.roulette.position.set(c.roulette.x, c.roulette.y);
    this.roulette.animationSpeed = 0.25;
    this.forSale = new Sprite(tex('scenes/casino-for-sale'));
    this.forSale.position.set(c.forSale.x, c.forSale.y);
    this.queue = new Text({
      text: '',
      style: { fontFamily: 'Silkscreen', fontSize: 8, fill: '#f7d774', stroke: { color: '#1a1410', width: 2 } },
      resolution: 2,
    });
    this.queue.position.set(c.x + 6, c.y + c.h - 14);
    this.seats.sortableChildren = true;
    this.front.addChild(this.frontArt, this.roulette, this.forSale, this.queue);
    this.setOpen(false);
  }

  private setOpen(open: boolean) {
    this.open = open;
    this.bg.texture = tex(open ? 'scenes/casino' : 'scenes/casino-closed');
    this.sign.texture = tex(open ? 'scenes/casino-sign-on' : 'scenes/casino-sign-off');
    this.frontArt.visible = open;
    this.roulette.visible = open;
    this.forSale.visible = !open;
    for (const l of this.lights) {
      l.visible = open;
      if (open) l.play();
      else l.stop();
    }
    if (open) this.roulette.play();
    else this.roulette.stop();
  }

  sync(open: boolean, frogs: PublicFrog[], onFrog: (id: number) => void) {
    if (open !== this.open) this.setOpen(open);
    const seated = frogs.filter((f) => f.status === 'casino' && f.casinoSeat !== null);
    const waiting = frogs.filter((f) => f.status === 'casino' && f.casinoSeat === null).length;
    const keep = new Set<number>();
    for (const f of seated) {
      const seat = layout.casino.seats[f.casinoSeat!];
      if (!seat) continue;
      keep.add(f.id);
      let a = this.actors.get(f.id);
      if (!a) {
        a = new FrogActor(f.skin, f.rarity, 'casino');
        a.eventMode = 'static';
        a.cursor = 'pointer';
        a.on('pointertap', () => onFrog(f.id));
        this.actors.set(f.id, a);
        this.seats.addChild(a);
      }
      a.set(f.skin, f.rarity, 'casino');
      a.position.set(seat.x, seat.y);
      a.zIndex = seat.y;
    }
    for (const [id, a] of this.actors) {
      if (!keep.has(id)) {
        a.destroy({ children: true });
        this.actors.delete(id);
      }
    }
    this.queue.text = waiting > 0 ? `${waiting} WAITING FOR A SEAT` : '';
  }

  update(now: number) {
    this.flicker.update(now);
  }
}
