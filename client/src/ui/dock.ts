import type { Store } from '../state/store';
import { el, icon } from './components/el';
import { url } from '../game/assets';

export interface DockActions {
  frogs(): void;
  summon(): void;
  casino(): void;
  manager(): void;
  chest(): void;
}

export function mountDock(host: HTMLElement, store: Store, a: DockActions) {
  const count = el('span', { class: 'badge' });
  const item = (iconKey: string, label: string, fn: () => void, extra?: HTMLElement) =>
    el('button', { class: 'dock-btn', attrs: { type: 'button' }, on: { click: fn } }, icon(url(iconKey)), el('span', { text: label }), extra ?? null);
  host.append(
    item('ui/icon-frog', 'Frogs', a.frogs, count),
    item('ui/icon-summon', 'Summon', a.summon),
    item('ui/icon-casino', 'Casino', a.casino),
    item('ui/icon-manager', 'Manager', a.manager),
    item('ui/icon-chest', 'Chest', a.chest),
  );
  store.subscribe((s) => {
    count.textContent = String(s.player.frogs.length);
  });
}
