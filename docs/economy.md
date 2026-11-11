# Frogotraderz: frogs and economy

All numbers live in `shared/src/rarity.ts`, `shared/src/config.ts` and `shared/src/skills.ts`.
Tests in `shared/test/game.test.ts` check the payback targets.

## Packs
- 1 pack = 10,000 $FROG = 1 frog. Packs of 1, 5, 10, 15.
- Drop odds (server only, never shown): Common 83%, Uncommon 10%, Rare 5.5%, Epic 1%, Legendary 0.46%, Mythic 0.04%.

## Stats
| Stat | Meaning |
|---|---|
| PATIENCE | Shift and rest length. Stamina bar = PATIENCE x 5 |
| PROFIT | $FROG per hour of work |
| RISK | % chance of a x2 trade. Half that chance gives an empty trade |

| Rarity | PATIENCE | PROFIT / h | RISK | Skills | Rest |
|---|---|---|---|---|---|
| Common | 10–30 | 70–95 | 3–6% | 0–1 | 1 h |
| Uncommon | 40–60 | 180–240 | 6–9% | 1–2 | 2 h |
| Rare | 70–90 | 540–710 | 9–12% | 1–2 | 4 h |
| Epic | 100–120 | 1,550–2,050 | 12–15% | 2–3 | 6 h |
| Legendary | 130–150 | 2,700–3,550 | 15–18% | 2–3 | 7 h |
| Mythic | 160–180 | 6,100–8,000 | 18–21% | 3–4 | 8 h |

A frog with the median PATIENCE of its rarity works 30 minutes, then rests the hours above.
More PATIENCE: longer shift and longer rest in the same proportion (Common 10 = 15 min, Common 30 = 45 min).

## Work loop
1. Go work: the frog takes a free desk in an office (5 desks per office, 15 in total).
2. Out of stamina: it walks to the casino by itself, status IN CASINO.
3. Rested: status READY. Without a boss it waits for the player to press Go work.
4. Boss Frog (NFT, 250 total): sends rested frogs back at 80% stamina, day and night.

Real payback with a boss, median frog, no skills (from the tests):
Common 14.8 days, Uncommon 9.6, Rare 5.6, Epic 2.8, Legendary 1.8, Mythic 0.9.

## Offices
All three pay the same on average. Pump.fun pays 9% more but 8% of its trades get rugged (Rug Radar saves them).
Memecoin has the most pumps (Whale Hunter), Classic the most dips (Dip Buyer).

## Casino
Free. Every tired frog chills here, as many as you have, all at the same speed (the rest hours of its rarity).
Nothing to buy. It is only a place to rest.

## Skills
Common: Diamond Hands, Power Nap, Fast Fingers, Caffeine, Stop Loss.
Normal: Hot Streak, Dip Buyer, Degen Mode, Lucky Charm, Copy Trader, Night Owl.
Rare: Whale Hunter, Rug Radar, Insider.
Texts and effects: `shared/src/skills.ts`, `shared/src/formulas.ts`.
