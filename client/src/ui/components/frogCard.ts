import { PATHS, RARITIES, SKILLS, type PublicFrog } from '@frog-traders/shared';
import { url } from '../../game/assets';
import { el, icon } from './el';
import { compact } from './format';
import { portrait } from './portrait';

export function statusText(f: PublicFrog): string {
  if (f.status === 'working' && f.desk) return `Trading · ${PATHS[f.desk.path].name}`;
  if (f.status === 'casino') return f.casinoSeat !== null ? 'In casino · VIP table' : 'In casino';
  if (f.status === 'ready') return 'Rested · ready to work';
  return f.desk ? `Desk ${f.desk.desk + 1} · ${PATHS[f.desk.path].name}` : 'On the bench';
}

export function staminaBar(value: number, max: number): HTMLElement {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  const tone = pct > 50 ? 'good' : pct > 20 ? 'mid' : 'low';
  return el(
    'div',
    { class: `bar bar-${tone}`, attrs: { role: 'meter', 'aria-valuemin': 0, 'aria-valuemax': Math.round(max), 'aria-valuenow': Math.round(value), 'aria-label': 'Stamina' } },
    el('i', { style: { width: `${pct}%` } }),
    el('em', { text: `${Math.floor(value)}/${max}` }),
  );
}

export function skillChips(f: PublicFrog, withText = false): HTMLElement {
  return el(
    'div',
    { class: 'skills' },
    ...f.skills.map((id) =>
      el(
        'span',
        { class: 'skill', attrs: { title: `${SKILLS[id].name}: ${SKILLS[id].description}` } },
        icon(url(`ui/skill-${id}`), SKILLS[id].name),
        withText ? el('span', {}, el('b', { text: SKILLS[id].name }), ' ', SKILLS[id].description) : null,
      ),
    ),
  );
}

/** A collectible-style card for one frog. */
export function frogCard(f: PublicFrog, stamina: number, onClick?: () => void): HTMLElement {
  const r = RARITIES[f.rarity]!;
  const card = el(
    onClick ? 'button' : 'div',
    {
      class: `card rarity-${f.rarity} status-${f.status}`,
      attrs: onClick ? { type: 'button', 'aria-label': `${f.name}, ${r.name}` } : {},
      style: { '--rc': r.color },
      on: onClick ? { click: onClick } : {},
    },
    el('div', { class: 'card-art' }, portrait(f, 3), el('span', { class: 'card-id', text: `#${f.id}` })),
    el('div', { class: 'card-name', text: f.name }),
    el('div', { class: 'card-rarity', text: r.name }),
    el(
      'div',
      { class: 'stats' },
      el('span', { attrs: { title: 'PATIENCE: how long it works and rests' } }, icon(url('ui/icon-stamina')), f.stats.patience),
      el('span', { attrs: { title: 'PROFIT: $FROG per hour of work' } }, icon(url('ui/icon-edge')), f.stats.profit),
      el('span', { attrs: { title: 'RISK: chance of a x2 trade' } }, icon(url('ui/icon-speed')), `${f.stats.risk}%`),
    ),
    staminaBar(stamina, f.maxStamina),
    f.skills.length ? skillChips(f) : el('div', { class: 'skills skills-none', text: 'No skills' }),
    el('div', { class: 'card-status', text: statusText(f) }),
    f.ratePerHour > 0 ? el('div', { class: 'card-rate', text: `+${compact(f.ratePerHour)}/h` }) : null,
  );
  return card;
}
