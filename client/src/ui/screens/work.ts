import { PATHS, PATH_IDS, type PathId } from '@frog-traders/shared';
import type { Router } from '../../app/router';
import type { Store } from '../../state/store';
import { Flicker } from '../../game/animations/flicker';
import { url } from '../../game/assets';
import { el, clear } from '../components/el';
import { compact } from '../components/format';

/** Where each building sits on the crossroads picture, in percent. */
const SPOTS: Record<PathId, { left: number; top: number; width: number; height: number }> = {
  memecoin: { left: 1, top: 4, width: 30, height: 66 },
  pumpfun: { left: 33, top: 1, width: 34, height: 72 },
  classic: { left: 69, top: 4, width: 30, height: 66 },
};
const SIGN_KEY: Record<PathId, string> = { memecoin: 'left', pumpfun: 'center', classic: 'right' };

function officeStats(store: Store, p: PathId) {
  const frogs = store.state.player.frogs.filter((f) => f.desk?.path === p);
  const working = frogs.filter((f) => f.status === 'working');
  const rate = working.reduce((s, f) => s + f.ratePerHour, 0);
  return { seated: frogs.length, working: working.length, rate, desks: PATHS[p].desks };
}

/** Pick a trading house: the crossroads scene with three doors. */
export function renderWork(host: HTMLElement, store: Store, router: Router): () => void {
  const overlays = new Map<PathId, HTMLImageElement>();
  const spots = new Map<PathId, HTMLButtonElement>();
  const enter = (p: PathId) => router.go({ name: 'office', path: p });

  const scene = el(
    'div',
    { class: 'crossroads' },
    el('img', { class: 'cr-base', attrs: { src: url('scenes/hub'), alt: 'Three trading houses at night' } }),
  );
  for (const p of PATH_IDS) {
    const off = el('img', { class: 'cr-layer', attrs: { src: url(`scenes/hub-sign-${SIGN_KEY[p]}-off`), alt: '' }, style: { opacity: '0' } });
    overlays.set(p, off);
    const s = SPOTS[p];
    const spot = el('button', {
      class: `cr-spot cr-${p}`,
      attrs: { type: 'button', 'aria-label': `Enter ${PATHS[p].name}` },
      style: { left: `${s.left}%`, top: `${s.top}%`, width: `${s.width}%`, height: `${s.height}%`, '--accent': PATHS[p].color },
      on: { click: () => enter(p), mouseenter: () => highlight(p), mouseleave: () => highlight(null), focus: () => highlight(p), blur: () => highlight(null) },
    });
    spot.append(el('span', { class: 'cr-tag' }, el('b', { text: PATHS[p].name }), el('span', { text: 'Enter' })));
    spots.set(p, spot);
    scene.append(off, spot);
  }

  const list = el('div', { class: 'office-list' });
  const rows = new Map<PathId, HTMLElement>();
  const highlight = (p: PathId | null) => {
    for (const [k, r] of rows) r.classList.toggle('hot', k === p);
    for (const [k, s] of spots) {
      s.classList.toggle('hot', k === p);
      s.classList.toggle('dim', p !== null && k !== p);
    }
  };

  const drawList = () => {
    clear(list);
    for (const p of PATH_IDS) {
      const st = officeStats(store, p);
      const row = el(
        'button',
        {
          class: 'office-row',
          attrs: { type: 'button' },
          style: { '--accent': PATHS[p].color },
          on: { click: () => enter(p), mouseenter: () => highlight(p), mouseleave: () => highlight(null) },
        },
        el('span', { class: 'or-name', text: PATHS[p].name }),
        el('span', { class: 'or-blurb', text: PATHS[p].blurb }),
        el(
          'span',
          { class: 'or-stats' },
          el('span', {}, el('b', { text: `${st.seated}/${st.desks}` }), ' desks'),
          el('span', {}, el('b', { text: String(st.working) }), ' trading'),
          el('span', { class: 'or-rate' }, st.rate > 0 ? `+${compact(st.rate)}/h` : 'idle'),
        ),
        el('span', { class: 'or-enter', text: 'Enter' }),
      );
      rows.set(p, row);
      list.append(row);
    }
  };

  host.append(
    el(
      'div',
      { class: 'work' },
      scene,
      el(
        'aside',
        { class: 'panel work-panel' },
        el('h2', { class: 'panel-title', text: 'Where do your frogs trade today?' }),
        el('p', { class: 'panel-sub', text: 'Each house holds 5 desks. Every house gets a third of the daily pool, split by frog power.' }),
        list,
      ),
    ),
  );

  const unsub = store.subscribe(drawList);
  const flickers = [...overlays.values()].map((img) => new Flicker((lit) => (img.style.opacity = lit ? '0' : '1')));
  let raf = 0;
  const loop = () => {
    const now = performance.now();
    for (const f of flickers) f.update(now);
    raf = requestAnimationFrame(loop);
  };
  loop();
  return () => {
    cancelAnimationFrame(raf);
    unsub();
  };
}
