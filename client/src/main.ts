import '@fontsource/jersey-10/400.css';
import '@fontsource/silkscreen/400.css';
import './styles/base.css';
import './styles/shell.css';
import './styles/menu.css';
import './styles/work.css';
import './styles/panels.css';
import './styles/cards.css';
import './styles/login.css';

import { PATHS, type PublicState } from '@frog-traders/shared';
import { api, ApiError } from './api/client';
import { Router, type Route } from './app/router';
import { Store } from './state/store';
import { loadTextures, url } from './game/assets';
import { el, clear } from './ui/components/el';
import { mountTopbar } from './ui/shell/topbar';
import { renderMenu } from './ui/screens/menu';
import { renderWork } from './ui/screens/work';
import { renderPlaceholder } from './ui/screens/placeholder';
import { showLogin } from './ui/login';
import { openChestPanel } from './ui/panels/chestPanel';

async function boot() {
  const app = document.getElementById('app')!;
  const loading = el('div', { class: 'loading' }, el('p', { class: 'loading-logo', text: 'FROG TRADERS' }), el('div', { class: 'loading-bar' }, el('i')));
  app.append(loading);
  const bar = loading.querySelector('i')!;

  await Promise.all([
    document.fonts.load('8px Silkscreen'),
    document.fonts.load('20px "Jersey 10"'),
    loadTextures((p) => (bar.style.width = `${Math.round(p * 100)}%`)),
  ]);
  const health = await api.health().catch(() => ({ status: 'down', devMode: false }));

  let state: PublicState;
  try {
    state = await api.state();
    loading.remove();
  } catch (e) {
    loading.remove();
    if (!(e instanceof ApiError) || e.code !== 'unauthorized') {
      app.append(el('p', { class: 'fatal', text: 'The game server is not reachable. Start it with "npm run dev" and reload.' }));
      return;
    }
    state = await showLogin(app);
  }
  startGame(app, state, !!health.devMode);
}

function startGame(app: HTMLElement, initial: PublicState, devMode: boolean) {
  const store = new Store(initial);
  store.devMode = devMode;
  const router = new Router();

  const topbar = el('header', { class: 'topbar' });
  const screen = el('main', { class: 'screen' });
  app.append(el('div', { class: 'shell', style: { '--tile': `url(${url('menu/bg-tile')})` } }, topbar, screen));

  mountTopbar(topbar, store, router, { chest: () => openChestPanel(store) });

  let cleanup: (() => void) | void;
  const show = (r: Route) => {
    cleanup?.();
    cleanup = undefined;
    clear(screen);
    screen.dataset.route = r.name;
    switch (r.name) {
      case 'menu':
        renderMenu(screen, router, {
          fusion: () => router.go({ name: 'fusion' }),
          market: () => router.go({ name: 'market' }),
        });
        break;
      case 'work':
        cleanup = renderWork(screen, store, router);
        break;
      case 'office':
        renderPlaceholder(screen, PATHS[r.path].name, 'The office interior is the next screen to design.');
        break;
      default:
        renderPlaceholder(screen, r.name, 'This page is designed after the menu is approved.');
    }
  };
  router.onChange(show);
  show(router.current);
  store.start();
}

void boot();
