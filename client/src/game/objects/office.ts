import { AnimatedSprite, Container, Sprite } from 'pixi.js';
import type { PathId } from '@frog-traders/shared';
import { frames, layout, tex } from '../assets';
import { Flicker } from '../animations/flicker';
import { DeskView } from './desk';

type OfficeLayout = (typeof layout.offices)[number];

/** One of the three trading offices: background, neon sign, wall ticker and five desks. */
export class OfficeView {
  readonly path: PathId;
  readonly back = new Container();
  readonly desks: DeskView[] = [];
  private flicker: Flicker;

  constructor(def: OfficeLayout, props: Container, onDesk: (d: DeskView) => void) {
    this.path = def.path as PathId;
    const bg = new Sprite(tex(`scenes/office-${def.path}`));
    bg.position.set(def.x, def.y);
    const on = tex(`scenes/sign-${def.path}-on`);
    const off = tex(`scenes/sign-${def.path}-off`);
    const sign = new Sprite(on);
    sign.position.set(def.sign.x, def.sign.y);
    this.flicker = new Flicker((lit) => (sign.texture = lit ? on : off));
    const ticker = new AnimatedSprite(frames(`sprites/ticker-${def.path}`, 44, 28));
    ticker.position.set(def.ticker.x, def.ticker.y);
    ticker.animationSpeed = 0.09;
    ticker.play();
    this.back.addChild(bg, sign, ticker);

    def.desks.forEach((d, i) => {
      const desk = new DeskView(this.path, i, d.x, d.y, onDesk);
      this.desks.push(desk);
      props.addChild(desk);
    });
  }

  update(now: number) {
    this.flicker.update(now);
  }
}
