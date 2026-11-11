import { AnimatedSprite, Container } from 'pixi.js';
import { frogFrames, type FrogAnim } from '../assets';

const SPEED: Record<FrogAnim, number> = { work: 0.12, sleep: 0.03, casino: 0.06, idle: 0.04 };

/**
 * A frog drawn from two stacked sheets: the body (skin color) and the
 * outfit (rarity). Both play the same frame.
 */
export class FrogActor extends Container {
  private body: AnimatedSprite;
  private clothes: AnimatedSprite;
  private anim: FrogAnim;
  private look = { skin: -1, rarity: -1 };

  constructor(skin: number, rarity: number, anim: FrogAnim) {
    super();
    this.anim = anim;
    this.body = new AnimatedSprite(frogFrames('skin', skin, anim));
    this.clothes = new AnimatedSprite(frogFrames('outfit', rarity, anim));
    this.clothes.autoUpdate = false;
    this.body.onFrameChange = (f) => this.clothes.gotoAndStop(f);
    this.addChild(this.body, this.clothes);
    this.look = { skin, rarity };
    this.start();
  }

  private start() {
    this.body.animationSpeed = SPEED[this.anim] * (0.85 + Math.random() * 0.3);
    const f = Math.floor(Math.random() * this.body.totalFrames);
    this.body.gotoAndPlay(f);
    this.clothes.gotoAndStop(f);
  }

  set(skin: number, rarity: number, anim: FrogAnim) {
    if (skin === this.look.skin && rarity === this.look.rarity && anim === this.anim) return;
    this.anim = anim;
    this.look = { skin, rarity };
    this.body.textures = frogFrames('skin', skin, anim);
    this.clothes.textures = frogFrames('outfit', rarity, anim);
    this.start();
  }
}
