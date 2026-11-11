import { Container, Sprite, Text, type Texture } from 'pixi.js';

interface Floater {
  node: Container;
  vy: number;
  life: number;
  age: number;
  sway: number;
}

/** Short-lived things that drift up and fade: coin popups, Zzz, sparkles. */
export class Floaters {
  readonly layer = new Container();
  private items: Floater[] = [];

  text(x: number, y: number, value: string, color: string, life = 1.4) {
    const t = new Text({
      text: value,
      style: { fontFamily: 'Silkscreen', fontSize: 8, fill: color, stroke: { color: '#1a1410', width: 2 } },
      resolution: 2,
    });
    t.anchor.set(0.5, 1);
    t.position.set(Math.round(x), Math.round(y));
    this.add(t, -10, life, 0);
  }

  sprite(texture: Texture, x: number, y: number, life = 2.2, sway = 3) {
    const s = new Sprite(texture);
    s.anchor.set(0.5);
    s.position.set(Math.round(x), Math.round(y));
    this.add(s, -6, life, sway);
  }

  private add(node: Container, vy: number, life: number, sway: number) {
    this.layer.addChild(node);
    this.items.push({ node, vy, life, age: 0, sway });
  }

  update(dt: number) {
    for (let i = this.items.length - 1; i >= 0; i--) {
      const f = this.items[i]!;
      f.age += dt;
      f.node.y += f.vy * dt;
      if (f.sway) f.node.x += Math.sin(f.age * 4) * f.sway * dt;
      f.node.alpha = Math.max(0, 1 - Math.pow(f.age / f.life, 2));
      if (f.age >= f.life) {
        f.node.destroy();
        this.items.splice(i, 1);
      }
    }
  }
}
