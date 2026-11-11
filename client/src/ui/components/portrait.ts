import type { Frog } from '@frog-traders/shared';
import { layout, tex } from '../../game/assets';

/**
 * Draws a frog onto a canvas for cards and panels, using the same sheets as
 * the game scene. `frame` is an index in the idle animation.
 */
export function portrait(frog: Pick<Frog, 'skin' | 'rarity'>, scale = 4, frame = 0): HTMLCanvasElement {
  const { w, h, anims } = layout.frog;
  const c = document.createElement('canvas');
  c.width = w * scale;
  c.height = h * scale;
  c.className = 'portrait';
  const ctx = c.getContext('2d')!;
  ctx.imageSmoothingEnabled = false;
  const i = anims.idle.start + frame;
  for (const key of [`sprites/frog-skin-${frog.skin}`, `sprites/frog-outfit-${frog.rarity}`]) {
    const src = tex(key).source.resource as CanvasImageSource;
    ctx.drawImage(src, i * w, 0, w, h, 0, 0, w * scale, h * scale);
  }
  return c;
}
