import { AnimatedSprite, Container, Rectangle, Sprite, Text } from 'pixi.js';
import type { PathId, PublicFrog } from '@frog-traders/shared';
import { frames, layout, tex } from '../assets';
import { FrogActor } from './frogActor';

export type DeskMode = 'empty' | 'working' | 'away';

/** One desk: chair, the frog, the monitor with a live chart, and the desk itself. */
export class DeskView extends Container {
  readonly path: PathId;
  readonly index: number;
  frogId: number | null = null;
  mode: DeskMode = 'empty';
  private actor: FrogActor | null = null;
  private screen: AnimatedSprite;
  private awayTag: Text;
  private frogPos: { x: number; y: number };

  constructor(path: PathId, index: number, x: number, y: number, onTap: (d: DeskView) => void) {
    super();
    this.path = path;
    this.index = index;
    const d = layout.desk;
    const at = (v: number[]) => v as [number, number];
    const [fx, fy] = at(d.frog);
    const [cx, cy] = at(d.chair);
    const [mx, my] = at(d.monitor);
    const [sx, sy] = at(d.screen);
    this.zIndex = y;
    this.frogPos = { x: x + fx, y: y + fy };

    const chair = new Sprite(tex('sprites/chair'));
    chair.position.set(x + cx, y + cy);
    const monitor = new Sprite(tex('sprites/monitor'));
    monitor.position.set(x + mx, y + my);
    this.screen = new AnimatedSprite(frames(`sprites/screen-${path}`, 12, 9));
    this.screen.position.set(x + sx, y + sy);
    this.screen.animationSpeed = 0.05 + Math.random() * 0.03;
    this.screen.visible = false;
    const desk = new Sprite(tex('sprites/desk'));
    desk.position.set(x, y);
    this.awayTag = new Text({
      text: 'zz',
      style: { fontFamily: 'Silkscreen', fontSize: 8, fill: '#c9cdd6', stroke: { color: '#1a1410', width: 2 } },
      resolution: 2,
    });
    this.awayTag.position.set(x + 24, y - 14);
    this.awayTag.visible = false;

    this.addChild(chair, this.slot, monitor, this.screen, desk, this.awayTag);
    this.eventMode = 'static';
    this.cursor = 'pointer';
    this.hitArea = new Rectangle(x, y - 18, d.w, d.h + 18);
    this.on('pointertap', () => onTap(this));
  }

  private slot = new Container();

  /** Head position for popups. */
  get head() {
    return { x: this.frogPos.x + 12, y: this.frogPos.y + 2 };
  }

  setFrog(frog: PublicFrog | null) {
    const mode: DeskMode = !frog ? 'empty' : frog.status === 'working' ? 'working' : 'away';
    this.frogId = frog?.id ?? null;
    this.mode = mode;
    if (mode === 'working' && frog) {
      if (!this.actor) {
        this.actor = new FrogActor(frog.skin, frog.rarity, 'work');
        this.actor.position.set(this.frogPos.x, this.frogPos.y);
        this.slot.addChild(this.actor);
      } else {
        this.actor.set(frog.skin, frog.rarity, 'work');
      }
    } else if (this.actor) {
      this.actor.destroy({ children: true });
      this.actor = null;
    }
    this.screen.visible = mode === 'working';
    if (mode === 'working') this.screen.play();
    else this.screen.stop();
    this.awayTag.visible = mode === 'away';
  }
}
