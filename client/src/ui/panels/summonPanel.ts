import { ECONOMY, RARITIES, type PublicFrog } from '@frog-traders/shared';
import { api } from '../../api/client';
import type { Store } from '../../state/store';
import { button, el, icon } from '../components/el';
import { frogCard } from '../components/frogCard';
import { fmt, SYM } from '../components/format';
import { openModal } from '../components/modal';
import { url } from '../../game/assets';
import { livePanel } from './live';

export function openSummonPanel(store: Store) {
  livePanel(store, 'Summon frogs', 'ui/icon-summon', (body) => {
    const wallet = store.state.player.wallet;
    const packs = el(
      'div',
      { class: 'packs' },
      ...ECONOMY.packSizes.map((n) => {
        const price = n * ECONOMY.packPrice;
        const b = button(
          [
            el('img', { class: 'pack-art', attrs: { src: url('ui/card-back'), alt: '' } }),
            el('strong', { text: n === 1 ? '1 frog' : `${n} frogs` }),
            el('span', { class: 'price' }, icon(url('ui/icon-coin')), fmt(price)),
          ],
          () => void summon(store, n),
          'pack',
        );
        b.disabled = wallet < price;
        return b;
      }),
    );
    const odds = el(
      'table',
      { class: 'odds' },
      el('thead', {}, el('tr', {}, el('th', { text: 'Rarity' }), el('th', { text: 'Chance' }), el('th', { text: 'Patience' }), el('th', { text: 'Profit / h' }), el('th', { text: 'Skills' }), el('th', { text: 'Outfit' }))),
      el(
        'tbody',
        {},
        ...RARITIES.map((r) =>
          el(
            'tr',
            {},
            el('td', { text: r.name, style: { color: r.color } }),
            el('td', { text: `${r.odds}%` }),
            el('td', { text: `${r.patience[0]}–${r.patience[1]}` }),
            el('td', { text: `${r.profit[0]}–${r.profit[1]}` }),
            el('td', { text: `${r.skills[0]}–${r.skills[1]}` }),
            el('td', { text: r.outfit }),
          ),
        ),
      ),
    );
    body.append(
      el('p', { class: 'lead' }, `Each pack costs ${fmt(ECONOMY.packPrice)} ${SYM} and holds one frog.`),
      packs,
      el('p', { class: 'wallet-line' }, icon(url('ui/icon-coin')), `Wallet: ${fmt(wallet)} ${SYM}`),
      el('h3', { text: 'Drop rates' }),
      odds,
    );
  }, { wide: true });
}

async function summon(store: Store, n: number) {
  const frogs = await store.run(() => api.summon(n));
  if (frogs) reveal(store, frogs);
}

/** Cards appear face down and flip one by one. */
function reveal(store: Store, frogs: PublicFrog[]) {
  const best = Math.max(...frogs.map((f) => f.rarity));
  const m = openModal(frogs.length === 1 ? 'New frog!' : `${frogs.length} new frogs!`, 'ui/icon-summon', { wide: true });
  const grid = el('div', { class: `reveal-grid${frogs.length === 1 ? ' single' : ''}` });
  const live = store.state.player.frogs;
  frogs.forEach((f, i) => {
    const full = live.find((x) => x.id === f.id) ?? (f as PublicFrog);
    const flip = el(
      'div',
      { class: `flip rarity-${f.rarity}`, style: { '--rc': RARITIES[f.rarity]!.color, animationDelay: `${0.25 + i * 0.18}s` } },
      el('div', { class: 'flip-back' }, el('img', { attrs: { src: url('ui/card-back'), alt: '' } })),
      el('div', { class: 'flip-front' }, frogCard(full, full.stamina)),
    );
    grid.append(flip);
  });
  const desks = 15 - store.state.player.frogs.filter((f) => f.desk).length;
  m.body.append(
    el('p', { class: `lead reveal-best rarity-text-${best}`, text: best >= 3 ? `${RARITIES[best]!.name} pull!` : 'Fresh traders are ready.' }),
    grid,
    el(
      'div',
      { class: 'actions center' },
      desks > 0 ? button(`Seat them at ${Math.min(desks, frogs.length)} free desks`, async () => {
        await store.run(() => api.autoSeat());
        m.close();
      }, 'btn btn-main') : null,
      button('Close', () => m.close(), 'btn btn-ghost'),
    ),
  );
}
