import { Assets, Rectangle, Texture, TextureSource } from 'pixi.js';
import layoutJson from '../assets/layout.json';

export const layout = layoutJson;
export type Layout = typeof layoutJson;

/** Every PNG under src/assets, keyed by its path without the extension, e.g. "sprites/desk". */
const urls = import.meta.glob('../assets/**/*.png', { eager: true, query: '?url', import: 'default' }) as Record<
  string,
  string
>;

export const assetUrl: Record<string, string> = {};
for (const [path, url] of Object.entries(urls)) {
  const key = path.replace('../assets/', '').replace(/\.png$/, '');
  assetUrl[key] = url;
}

export function url(key: string): string {
  const u = assetUrl[key];
  if (!u) throw new Error(`Missing asset ${key}`);
  return u;
}

const textures = new Map<string, Texture>();

export async function loadTextures(onProgress?: (p: number) => void): Promise<void> {
  TextureSource.defaultOptions.scaleMode = 'nearest';
  const keys = Object.keys(assetUrl);
  let done = 0;
  await Promise.all(
    keys.map(async (k) => {
      const t = await Assets.load<Texture>(assetUrl[k]!);
      t.source.scaleMode = 'nearest';
      textures.set(k, t);
      onProgress?.(++done / keys.length);
    }),
  );
}

export function tex(key: string): Texture {
  const t = textures.get(key);
  if (!t) throw new Error(`Texture ${key} not loaded`);
  return t;
}

const frameCache = new Map<string, Texture[]>();

/** Cuts a horizontal sprite sheet into frames of w x h. */
export function frames(key: string, w: number, h: number): Texture[] {
  const id = `${key}:${w}x${h}`;
  const hit = frameCache.get(id);
  if (hit) return hit;
  const base = tex(key);
  const n = Math.floor(base.width / w);
  const out: Texture[] = [];
  for (let i = 0; i < n; i++) {
    out.push(new Texture({ source: base.source, frame: new Rectangle(i * w, 0, w, h) }));
  }
  frameCache.set(id, out);
  return out;
}

export type FrogAnim = keyof Layout['frog']['anims'];

export function frogFrames(layer: 'skin' | 'outfit', variant: number, anim: FrogAnim): Texture[] {
  const all = frames(`sprites/frog-${layer}-${variant}`, layout.frog.w, layout.frog.h);
  const a = layout.frog.anims[anim];
  return all.slice(a.start, a.start + a.count);
}
