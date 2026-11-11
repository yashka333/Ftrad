/**
 * Rarities. Every number a frog is born with comes from this table.
 *
 * PATIENCE sets how long a frog works and rests (see STAMINA in config.ts).
 * PROFIT is $FROG per hour of work. RISK is the chance in % of a x2 trade.
 * restHours is the rest after a shift for a frog with the median PATIENCE.
 *
 * Payback of a 10,000 $FROG pack, with a boss cycling the frog non-stop:
 * Common 15 days, Uncommon 10, Rare 6, Epic 3, Legendary 2, Mythic 1.
 */
export interface RarityDef {
  id: number;
  name: string;
  color: string;
  /** Chance in percent. Kept on the server, never shown to players. */
  odds: number;
  patience: [number, number];
  profit: [number, number];
  risk: [number, number];
  /** Inclusive range of skills a frog of this rarity is born with. */
  skills: [number, number];
  restHours: number;
  outfit: string;
}

export const RARITIES: RarityDef[] = [
  { id: 0, name: 'Common', color: '#c9cdd6', odds: 83, patience: [10, 30], profit: [70, 95], risk: [3, 6], skills: [0, 1], restHours: 1, outfit: 'Ragged tank top' },
  { id: 1, name: 'Uncommon', color: '#6ee06a', odds: 10, patience: [40, 60], profit: [180, 240], risk: [6, 9], skills: [1, 2], restHours: 2, outfit: 'Hoodie' },
  { id: 2, name: 'Rare', color: '#4aa8ff', odds: 5.5, patience: [70, 90], profit: [540, 710], risk: [9, 12], skills: [1, 2], restHours: 4, outfit: 'Shirt and tie' },
  { id: 3, name: 'Epic', color: '#b66fff', odds: 1, patience: [100, 120], profit: [1550, 2050], risk: [12, 15], skills: [2, 3], restHours: 6, outfit: 'Office suit' },
  { id: 4, name: 'Legendary', color: '#ffb42e', odds: 0.46, patience: [130, 150], profit: [2700, 3550], risk: [15, 18], skills: [2, 3], restHours: 7, outfit: 'Black suit and shades' },
  { id: 5, name: 'Mythic', color: '#ff4d6d', odds: 0.04, patience: [160, 180], profit: [6100, 8000], risk: [18, 21], skills: [3, 4], restHours: 8, outfit: 'Gold suit and crown' },
];

/** Middle of the PATIENCE range: the frog that works exactly one base shift. */
export function medianPatience(rarity: number): number {
  const [lo, hi] = RARITIES[rarity]!.patience;
  return (lo + hi) / 2;
}

export function rollRarity(rand: () => number): number {
  const total = RARITIES.reduce((s, r) => s + r.odds, 0);
  let roll = rand() * total;
  for (const r of RARITIES) {
    roll -= r.odds;
    if (roll < 0) return r.id;
  }
  return 0;
}
