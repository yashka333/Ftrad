/* Boss Frogs screen placeholder: black room, title baked in, a slow pulsing "ANNOUNCEMENT SOON".
 * Registers window.FTScreens.boss for HomeScene.
 */
(function () {
  'use strict';
  const mod = {
    hit() { return null; },
    click() {},
    frame(ctx, t) {
      const [x, y] = ctx.L.soon;
      const k = (Math.sin(t * 2.2) + 1) / 2;
      const c = (a, b) => Math.round(a + (b - a) * k);
      const col = `rgb(${c(150, 255)},${c(110, 226)},${c(52, 130)})`;
      ctx.gtext('ANNOUNCEMENT SOON', x, y, col, 'head', { align: 'center', shadow: '#000000' });
      const dots = Math.floor(t * 2) % 4;
      for (let i = 0; i < 3; i++) ctx.rect(x - 5 + i * 5, y + 18, x - 4 + i * 5, y + 19, i < dots ? '#ecba48' : '#2a2018');
    },
  };
  window.FTScreens = window.FTScreens || {};
  window.FTScreens.boss = mod;
})();
