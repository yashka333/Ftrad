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
| PROFIT | $FROG earned in one full shift |
| RISK | % chance of a x2 trade. Half that chance gives an empty trade |

| Rarity | PATIENCE | PROFIT / shift | RISK | Skills | Shift | Rest |
|---|---|---|---|---|---|---|
| Common | 10–30 | 25–31 | 3–6% | 0–1 | 1.5 min | 1 h |
| Uncommon | 40–60 | 74–94 | 6–9% | 1–2 | 5 min | 2 h |
| Rare | 70–90 | 261–333 | 9–12% | 1–2 | 30 min | 4 h |
| Epic | 100–120 | 801–1,020 | 12–15% | 2–3 | 1 h | 6 h |
| Legendary | 130–150 | 1,440–1,832 | 15–18% | 2–3 | 1.5 h | 7 h |
| Mythic | 160–180 | 3,341–4,252 | 18–21% | 3–4 | 2 h | 8 h |

Shift and rest are for the median PATIENCE of the rarity. More PATIENCE: longer shift and longer rest in the same proportion
(Common 10 = 45 s, Common 30 = 2 min 15 s).

## Work loop
Commons work a minute or two and rest an hour, so a big crew of them is played in turns.
1. ALL TO WORK (or Assign desk): rested frogs take the free desks, best first (5 desks per office, 15 in total).
2. Out of stamina: the frog walks to the casino by itself and frees its desk for the next frog.
3. Rested: status IDLE, back in the crew. Press ALL TO WORK again to put the rested frogs on the free desks.
4. Boss Frog (announcement soon): will send rested frogs back to free desks at 80% stamina.

Payback when the frog is sent back as soon as it is rested, median frog, no skills (checked by the tests):
Common 15 days, Uncommon 10, Rare 6, Epic 3, Legendary 2, Mythic 1.

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
