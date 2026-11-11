/**
 * Neon sign flicker: lit most of the time, now and then a short stutter.
 * Each sign gets its own random rhythm.
 */
const PATTERNS: Array<Array<[boolean, number]>> = [
  [[false, 70], [true, 60], [false, 110], [true, 0]],
  [[false, 60], [true, 90], [false, 50], [true, 140], [false, 80], [true, 0]],
  [[false, 450], [true, 0]],
  [[false, 90], [true, 0]],
];

export class Flicker {
  lit = true;
  private seq: Array<[boolean, number]> | null = null;
  private step = 0;
  private until = 0;
  private next: number;

  constructor(private apply: (lit: boolean) => void, now = performance.now()) {
    this.next = now + 600 + Math.random() * 3000;
  }

  update(now: number) {
    if (!this.seq && now > this.next) {
      this.seq = PATTERNS[Math.floor(Math.random() * PATTERNS.length)]!;
      this.step = 0;
      this.until = now;
    }
    while (this.seq && now >= this.until) {
      const [lit, ms] = this.seq[this.step]!;
      if (lit !== this.lit) {
        this.lit = lit;
        this.apply(lit);
      }
      this.until = now + ms;
      this.step++;
      if (this.step >= this.seq.length) {
        this.seq = null;
        this.next = now + 1800 + Math.random() * 4000;
      }
    }
  }
}
