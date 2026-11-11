import { PATHS } from '@frog-traders/shared';
import { api } from '../../api/client';
import type { Router } from '../../app/router';
import { ROUTE_TITLES } from '../../app/router';
import type { Store } from '../../state/store';
import { url } from '../../game/assets';
import { el, icon, clear } from '../components/el';
import { fmt } from '../components/format';

/** Top bar: who you are (or a back button on inner pages), wallet, chest, settings. */
export function mountTopbar(host: HTMLElement, store: Store, router: Router, open: { chest(): void }) {
  const left = el('div', { class: 'tb-left' });
  const wallet = el('strong', { class: 'tb-num' });
  const chest = el('strong', { class: 'tb-num' });
  const settings = el('button', { class: 'tb-btn', attrs: { type: 'button', 'aria-label': 'Settings', title: 'Sign out' } }, icon(url('ui/icon-manager')));
  settings.addEventListener('click', async () => {
    await api.signOut();
    location.reload();
  });

  host.append(
    left,
    el(
      'div',
      { class: 'tb-right' },
      el('div', { class: 'tb-chip', attrs: { title: 'FROG in your wallet' } }, icon(url('ui/icon-coin')), wallet),
      el('button', { class: 'tb-chip tb-chest', attrs: { type: 'button', title: 'Chest: what your frogs earned' }, on: { click: () => open.chest() } }, icon(url('ui/icon-chest')), chest),
      settings,
    ),
  );

  const renderLeft = () => {
    clear(left);
    const r = router.current;
    if (r.name === 'menu') {
      left.append(
        el('span', { class: 'tb-avatar' }, el('img', { attrs: { src: url('menu/boss-orig'), alt: '' } })),
        el('span', { class: 'tb-name', text: store.state.player.name }),
      );
      return;
    }
    const title = r.name === 'office' ? PATHS[r.path].name : ROUTE_TITLES[r.name];
    left.append(
      el('button', { class: 'tb-back', attrs: { type: 'button', 'aria-label': 'Back' }, on: { click: () => router.back() } }, el('span', { class: 'arrow' })),
      el('h1', { class: 'tb-title', text: title }),
    );
  };
  router.onChange(renderLeft);
  renderLeft();

  store.subscribe((s) => {
    wallet.textContent = fmt(s.player.wallet, 2);
  });
  const tick = () => {
    chest.textContent = fmt(store.liveChest(), 2);
    window.setTimeout(tick, 250);
  };
  tick();
}
