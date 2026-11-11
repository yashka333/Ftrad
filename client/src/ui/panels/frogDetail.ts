import { PATHS, PATH_IDS, RARITIES, type PathId, type PublicFrog } from '@frog-traders/shared';
import { api } from '../../api/client';
import type { Store } from '../../state/store';
import { button, el, icon } from '../components/el';
import { frogCard, skillChips, staminaBar, statusText } from '../components/frogCard';
import { compact, duration, fmt } from '../components/format';
import { url } from '../../game/assets';
import { livePanel } from './live';

export function freeDesk(store: Store, path: PathId): number | null {
  const taken = new Set(
    store.state.player.frogs.filter((f) => f.desk?.path === path).map((f) => f.desk!.desk),
  );
  for (let d = 0; d < PATHS[path].desks; d++) if (!taken.has(d)) return d;
  return null;
}

export function openFrogDetail(store: Store, frogId: number) {
  livePanel(store, 'Frog', 'ui/icon-frog', (body, m) => {
    const f = store.frog(frogId);
    if (!f) {
      m.close();
      return;
    }
    m.setTitle(`${f.name} #${f.id}`);
    const stamina = store.liveStamina(f);

    const sendTo = el(
      'div',
      { class: 'path-buttons' },
      ...PATH_IDS.map((p) => {
        const here = f.desk?.path === p;
        const free = freeDesk(store, p);
        const note = here ? 'its desk' : free === null ? 'full' : `desk ${free + 1} free`;
        const b = button(
          [el('span', { class: 'dot', style: { background: PATHS[p].color } }), PATHS[p].name, el('span', { class: 'btn-note', text: note })],
          () => {
            if (free === null) return;
            void store.run(() => api.assign(f.id, p, here ? f.desk!.desk : free));
          },
          `btn btn-path${here ? ' active' : ''}`,
        );
        b.disabled = here || free === null;
        b.title = here ? 'Already here' : free === null ? 'All 5 desks are taken' : `Desk ${free + 1} is free`;
        return b;
      }),
    );

    const actions = el('div', { class: 'actions' });
    if (f.desk && f.status !== 'working') {
      const b = button('Start trading', () => void store.run(() => api.work(f.id)), 'btn btn-main');
      b.disabled = stamina < 1;
      actions.append(b);
    }
    if (f.status !== 'casino') {
      actions.append(button([icon(url('ui/icon-casino')), 'Rest in the casino'], () => void store.run(() => api.rest(f.id))));
    }
    if (f.desk) {
      actions.append(button('Stop', () => void store.run(() => api.stop(f.id)), 'btn btn-ghost'));
    }

    const r = RARITIES[f.rarity]!;
    const full = f.staminaPerMin > 0 ? ((f.maxStamina - stamina) / f.staminaPerMin) * 60_000 : 0;
    const empty = f.staminaPerMin < 0 ? (stamina / -f.staminaPerMin) * 60_000 : 0;

    body.append(
      el(
        'div',
        { class: 'detail' },
        frogCard(f as PublicFrog, stamina),
        el(
          'div',
          { class: 'detail-side' },
          el('p', { class: 'detail-status', text: statusText(f) }),
          el(
            'dl',
            { class: 'facts' },
            el('dt', { text: 'Rarity' }), el('dd', { text: `${r.name} · ${r.outfit}`, style: { color: r.color } }),
            el('dt', { text: 'Earning now' }), el('dd', { text: f.ratePerHour > 0 ? `${compact(f.ratePerHour)} per hour` : 'Nothing right now' }),
            el('dt', { text: 'Earned in total' }), el('dd', { text: fmt(f.earned, 2) }),
            el('dt', { text: 'Stamina' }), el('dd', {}, staminaBar(stamina, f.maxStamina)),
            empty > 0 ? el('dt', { text: 'Tired in' }) : null, empty > 0 ? el('dd', { text: duration(empty) }) : null,
            full > 0 ? el('dt', { text: 'Rested in' }) : null, full > 0 ? el('dd', { text: duration(full) }) : null,
          ),
          f.skills.length ? el('h3', { text: 'Skills' }) : null,
          f.skills.length ? skillChips(f, true) : null,
          el('h3', { text: 'Send to a desk' }),
          sendTo,
          el('h3', { text: 'Actions' }),
          actions,
        ),
      ),
    );
  }, { wide: true });
}
