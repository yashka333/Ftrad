import { api } from '../../api/client';
import type { Store } from '../../state/store';
import { button, el, icon } from '../components/el';
import { fmt, SYM } from '../components/format';
import { url } from '../../game/assets';
import { livePanel } from './live';

export function openManagerPanel(store: Store) {
  livePanel(store, 'Boss Frog', 'ui/icon-manager', (body) => {
    const p = store.state.player;
    const price = store.state.bossPrice;
    const buy = button([icon(url('ui/icon-coin')), `Get a Boss Frog for ${fmt(price)} ${SYM}`], () => void store.run(() => api.buyBoss()), 'btn btn-main');
    buy.disabled = p.wallet < price || price <= 0;
    body.append(
      el('p', { class: 'lead', text: 'A Boss Frog sits at the head of your offices and runs the crew for you, even while you are away.' }),
      el(
        'ul',
        { class: 'bullets' },
        el('li', { text: 'Tired frogs walk to the casino by themselves.' }),
        el('li', { text: 'The boss sends them back to their desks at 80% stamina.' }),
      ),
      p.bosses > 0
        ? el(
            'div',
            { class: 'switch-row' },
            el('span', { text: p.bossActive ? 'Boss is running the offices' : 'Boss is off' }),
            button(p.bossOn ? 'Turn off' : 'Turn on', () => void store.run(() => api.switchBoss(!p.bossOn)), p.bossOn ? 'btn' : 'btn btn-main'),
          )
        : buy,
      el('p', { class: 'fine', text: `${fmt(store.state.bossesSold)} of 250 Boss Frogs taken.` }),
    );
  });
}
