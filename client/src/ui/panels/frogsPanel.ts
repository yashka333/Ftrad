import type { FrogStatus, PathId, PublicFrog } from '@frog-traders/shared';
import { PATHS } from '@frog-traders/shared';
import { api } from '../../api/client';
import type { Store } from '../../state/store';
import { button, el } from '../components/el';
import { frogCard } from '../components/frogCard';
import { livePanel } from './live';
import { openFrogDetail } from './frogDetail';

type Filter = 'all' | FrogStatus;
const FILTERS: Array<[Filter, string]> = [
  ['all', 'All'],
  ['working', 'Trading'],
  ['casino', 'In casino'],
  ['ready', 'Ready'],
  ['idle', 'Bench'],
];

let filter: Filter = 'all';

function sortFrogs(list: PublicFrog[]) {
  return [...list].sort((a, b) => b.rarity - a.rarity || b.stats.profit - a.stats.profit || a.id - b.id);
}

export function openFrogsPanel(store: Store, initial?: Filter) {
  if (initial) filter = initial;
  livePanel(store, 'My frogs', 'ui/icon-frog', (body) => {
    const frogs = store.state.player.frogs;
    const tabs = el(
      'div',
      { class: 'tabs', attrs: { role: 'tablist' } },
      ...FILTERS.map(([id, label]) => {
        const n = id === 'all' ? frogs.length : frogs.filter((f) => f.status === id).length;
        const b = button(`${label} ${n}`, () => {
          filter = id;
          store.poke();
        }, `tab${filter === id ? ' active' : ''}`);
        b.setAttribute('role', 'tab');
        b.setAttribute('aria-selected', String(filter === id));
        return b;
      }),
    );
    const desksFree = 15 - frogs.filter((f) => f.desk).length;
    const toolbar = el(
      'div',
      { class: 'toolbar' },
      tabs,
      desksFree > 0 && frogs.some((f) => !f.desk && f.stamina >= 1)
        ? button(`Fill ${desksFree} empty desk${desksFree === 1 ? '' : 's'}`, () => void store.run(() => api.autoSeat()), 'btn btn-main')
        : el('span', { class: 'hint', text: desksFree === 0 ? 'All 15 desks are taken' : 'No rested frogs on the bench' }),
    );
    const list = sortFrogs(filter === 'all' ? frogs : frogs.filter((f) => f.status === filter));
    body.append(
      toolbar,
      list.length
        ? el('div', { class: 'card-grid' }, ...list.map((f) => frogCard(f, store.liveStamina(f), () => openFrogDetail(store, f.id))))
        : el('p', { class: 'empty', text: frogs.length ? 'No frogs here.' : 'No frogs yet. Summon your first ones.' }),
    );
  }, { wide: true });
}

/** Picker shown when the player clicks an empty desk. */
export function openDeskPicker(store: Store, path: PathId, desk: number) {
  livePanel(store, `${PATHS[path].name} · desk ${desk + 1}`, 'ui/icon-frog', (body, m) => {
    const free = sortFrogs(store.state.player.frogs.filter((f) => !f.desk));
    body.append(
      el('p', { class: 'lead', text: `${PATHS[path].blurb} Pick a frog for this desk.` }),
      free.length
        ? el(
            'div',
            { class: 'card-grid' },
            ...free.map((f) =>
              frogCard(f, store.liveStamina(f), async () => {
                const ok = await store.run(() => api.assign(f.id, path, desk));
                if (ok !== null) m.close();
              }),
            ),
          )
        : el('p', { class: 'empty', text: 'Every frog already has a desk. Summon more frogs.' }),
    );
  }, { wide: true });
}
