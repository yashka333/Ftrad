import type { Router } from '../../app/router';
import { url } from '../../game/assets';
import { el } from '../components/el';

interface MenuCard {
  label: string;
  art: string;
  glow: string;
  accent: string;
  go: () => void;
}

/** Main menu: big illustrated cards, one per part of the game. */
export function renderMenu(host: HTMLElement, router: Router, extra: { fusion(): void; market(): void }) {
  const cards: MenuCard[] = [
    { label: 'Frogs', art: 'menu/card-frogs', glow: '#2b3f6b', accent: '#4aa8ff', go: () => router.go({ name: 'frogs' }) },
    { label: 'Go to work', art: 'menu/card-work', glow: '#5a3a1a', accent: '#e8662f', go: () => router.go({ name: 'work' }) },
    { label: 'Fusion', art: 'menu/card-fusion', glow: '#4a1f4f', accent: '#ff4fc8', go: extra.fusion },
    { label: 'Shop', art: 'menu/card-shop', glow: '#2e2150', accent: '#9a5cf0', go: () => router.go({ name: 'shop' }) },
    { label: 'Market', art: 'menu/card-market', glow: '#4f3d12', accent: '#f2c94c', go: extra.market },
  ];
  host.append(
    el(
      'div',
      { class: 'menu' },
      ...cards.map((c) =>
        el(
          'button',
          {
            class: 'menu-card',
            attrs: { type: 'button' },
            style: { '--glow': c.glow, '--accent': c.accent },
            on: { click: c.go },
          },
          el('span', { class: 'menu-art' }, el('img', { attrs: { src: url(c.art), alt: '', draggable: 'false' } })),
          el('span', { class: 'menu-label', text: c.label }),
        ),
      ),
    ),
  );
}
