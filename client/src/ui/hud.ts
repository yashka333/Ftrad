import type { Store } from '../state/store';
import { api } from '../api/client';
import { el, icon, button } from './components/el';
import { compact, fmt, SYM } from './components/format';
import { url } from '../game/assets';

/** Top bar with the live chest counter and wallet. */
export function mountHud(host: HTMLElement, store: Store, open: { chest(): void }) {
  const chest = el('strong', { class: 'num' });
  const rate = el('span', { class: 'rate' });
  const wallet = el('strong', { class: 'num' });
  const online = el('span', { class: 'dot-live', attrs: { title: 'Connected' } });

  const chestBtn = el(
    'button',
    { class: 'hud-chip hud-chest', attrs: { type: 'button', title: 'Open the chest' }, on: { click: () => open.chest() } },
    icon(url('ui/icon-chest')),
    el('span', { class: 'hud-col' }, el('span', { class: 'label', text: 'Chest' }), chest),
    rate,
  );

  host.append(
    el('div', { class: 'hud-left' }, el('img', { class: 'logo', attrs: { src: url('ui/logo'), alt: 'Frog Traders' } }), online),
    el(
      'div',
      { class: 'hud-mid' },
      chestBtn,
      el('div', { class: 'hud-chip' }, icon(url('ui/icon-coin')), el('span', { class: 'hud-col' }, el('span', { class: 'label', text: 'Wallet' }), wallet)),
    ),
    el(
      'div',
      { class: 'hud-right' },
      el('span', { class: 'player', text: store.state.player.name }),
      button('Sign out', async () => {
        await api.signOut();
        location.reload();
      }, 'btn btn-ghost btn-small'),
    ),
  );

  store.subscribe((s) => {
    wallet.textContent = `${fmt(s.player.wallet)} ${SYM}`;
    rate.textContent = s.player.ratePerHour > 0 ? `+${compact(s.player.ratePerHour)}/h` : 'idle';
    online.classList.add('on');
  });
  const tick = () => {
    chest.textContent = fmt(store.liveChest(), 2);
    window.setTimeout(tick, 250);
  };
  tick();
}
