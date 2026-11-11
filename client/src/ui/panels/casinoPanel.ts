import type { Store } from '../../state/store';
import { el } from '../components/el';
import { livePanel } from './live';

/** The casino is free: every tired frog chills here until it is rested. */
export function openCasinoPanel(store: Store) {
  livePanel(store, 'Casino', 'ui/icon-casino', (body) => {
    const queue = store.state.player.frogs.filter((f) => f.status === 'casino');
    body.append(
      el('p', { class: 'lead', text: 'Tired frogs chill in the casino for free until they are rested.' }),
      el('p', { class: 'note', text: `${queue.length} frogs in the casino now.` }),
    );
  });
}
