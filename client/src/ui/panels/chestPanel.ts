import { ECONOMY, withdrawQuote } from '@frog-traders/shared';
import { api } from '../../api/client';
import type { Store } from '../../state/store';
import { button, el, icon } from '../components/el';
import { compact, duration, fmt, SYM } from '../components/format';
import { url } from '../../game/assets';
import { livePanel } from './live';

export function openChestPanel(store: Store) {
  livePanel(store, 'Chest', 'ui/icon-chest', (body) => {
    const p = store.state.player;
    const chest = store.liveChest();
    const q = withdrawQuote(chest);
    const now = store.serverNow();
    const wait = p.nextWithdrawAt && p.nextWithdrawAt > now ? p.nextWithdrawAt - now : 0;
    const w = ECONOMY.withdraw;
    let reason = '';
    if (!q) reason = `Withdraw from ${fmt(w.min)} ${SYM} in the chest.`;
    else if (wait) reason = `Next withdrawal in ${duration(wait)}.`;
    else if (p.wallet < w.walletHoldMin) reason = `Your wallet must hold ${fmt(w.walletHoldMin)} ${SYM}.`;
    const btn = button('Withdraw to wallet', () => void store.run(() => api.withdraw()), 'btn btn-main');
    btn.disabled = !!reason;

    const parts: Array<Node | null | false> = [
      el(
        'div',
        { class: 'chest-hero' },
        el('img', { class: 'chest-art', attrs: { src: url('ui/icon-chest'), alt: '' } }),
        el('div', {}, el('span', { class: 'label', text: 'In the chest' }), el('strong', { class: 'big', text: `${fmt(chest, 2)} ${SYM}` }),
          el('span', { class: 'sub', text: `+${compact(p.ratePerHour)} per hour right now` })),
      ),
      q
        ? el(
            'dl',
            { class: 'facts' },
            el('dt', { text: 'You withdraw' }), el('dd', { text: `${fmt(q.gross, 2)} ${SYM}` }),
            el('dt', { text: 'Fee 3% (back to the pool)' }), el('dd', { text: `-${fmt(q.fee, 2)}` }),
            el('dt', { text: 'You receive' }), el('dd', { text: `${fmt(q.net, 2)} ${SYM}` }),
          )
        : null,
      el('div', { class: 'actions' }, btn, reason ? el('span', { class: 'hint', text: reason }) : null),
      el(
        'ul',
        { class: 'bullets fine' },
        el('li', { text: `Minimum ${fmt(w.min)}, maximum ${fmt(w.max)} ${SYM} per withdrawal.` }),
        el('li', { text: 'One withdrawal every 24 hours.' }),
        el('li', { text: `Keep at least ${fmt(w.walletHoldMin)} ${SYM} in your wallet.` }),
        el('li', { text: 'Stage 1: the wallet is simulated. Real Solana payouts come with the wallet login.' }),
      ),
      p.withdrawals.length
        ? el(
            'table',
            { class: 'odds' },
            el('thead', {}, el('tr', {}, el('th', { text: 'Date' }), el('th', { text: 'Amount' }), el('th', { text: 'Fee' }), el('th', { text: 'Status' }))),
            el(
              'tbody',
              {},
              ...p.withdrawals.map((x) =>
                el('tr', {}, el('td', { text: new Date(x.createdAt).toLocaleString() }), el('td', { text: fmt(x.gross, 2) }), el('td', { text: fmt(x.fee, 2) }), el('td', { text: 'Paid' })),
              ),
            ),
          )
        : null,
      store.devMode
        ? el('div', { class: 'dev' }, el('span', { text: 'Dev mode' }), button([icon(url('ui/icon-coin')), 'Get 250,000 test FROG'], () => void store.run(() => api.faucet())))
        : null,
    ];
    body.append(...parts.filter((x): x is Node => !!x));
  });
}
