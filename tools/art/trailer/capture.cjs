// Grabs office footage frame by frame: node capture.cjs shots.json
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const FPS = 30, STEP = 1000 / FPS + 0.02;
const shots = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const only = process.argv[3];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 640, height: 360 } });
  await page.goto('file://' + path.join(__dirname, 'build/capture.html'));
  for (const shot of shots) {
    if (only && shot.name !== only) continue;
    const dir = path.join(__dirname, 'build/frames', shot.name);
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    await page.evaluate((s) => { window.__seed(s.seed || 7); window.makeScene(s.room, s); }, shot);
    await page.waitForFunction(() => window.__cbs.length > 0);
    // pre-roll so charts and tickers are already moving
    const pre = Math.round((shot.preroll ?? 2) * FPS);
    await page.evaluate(([n, st]) => { for (let i = 0; i < n; i++) window.__step(st); }, [pre, STEP]);
    const total = Math.round(shot.seconds * FPS);
    const events = (shot.events || []).map((e) => ({ ...e, f: Math.round(e.t * FPS) }));
    for (let f = 0; f < total; f++) {
      for (const e of events) if (e.f === f) await page.evaluate((ev) => {
        if (ev.setFrog) window.scene.setFrog(ev.setFrog[0], ev.setFrog[1]);
        if ('setBoss' in ev) window.scene.setBoss(ev.setBoss);
      }, e);
      const url = await page.evaluate((st) => { window.__step(st); return document.getElementById('c').toDataURL('image/png'); }, STEP);
      fs.writeFileSync(path.join(dir, String(f).padStart(4, '0') + '.png'), Buffer.from(url.split(',')[1], 'base64'));
    }
    console.log(shot.name, total, 'frames');
  }
  await browser.close();
})();
