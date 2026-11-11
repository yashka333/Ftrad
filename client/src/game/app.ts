import { Application } from 'pixi.js';
import type { PathId, PublicState } from '@frog-traders/shared';
import { FloorScene, type SceneEvents } from './scenes/floorScene';

/**
 * Owns the Pixi application. The scene is drawn at 480x270 and scaled up by
 * whole numbers when the window allows it, so pixels stay square.
 */
export class GameView {
  readonly app = new Application();
  scene!: FloorScene;

  async mount(host: HTMLElement, events: SceneEvents) {
    await this.app.init({
      resizeTo: host,
      background: '#0f0d16',
      antialias: false,
      roundPixels: true,
      autoDensity: true,
      resolution: Math.min(window.devicePixelRatio || 1, 2),
    });
    host.append(this.app.canvas);
    this.scene = new FloorScene(events);
    this.app.stage.addChild(this.scene);
    this.app.renderer.on('resize', () => this.fit());
    this.fit();
    this.app.ticker.add((t) => this.scene.update(t.deltaMS / 1000, performance.now()));
  }

  private fit() {
    const { width, height } = this.app.screen;
    // Fill the space. Whole-number scales keep pixels perfectly square; when
    // the window is just short of the next whole step we still fill it.
    const raw = Math.min(width / FloorScene.W, height / FloorScene.H);
    const whole = Math.floor(raw);
    const scale = whole >= 1 && raw - whole < 0.12 ? whole : raw;
    this.scene.scale.set(scale);
    this.scene.position.set(
      Math.round((width - FloorScene.W * scale) / 2),
      Math.round((height - FloorScene.H * scale) / 2),
    );
  }

  sync(s: PublicState) {
    this.scene.sync(s);
  }
}

export type { PathId };
