# Картинки для генерации

Всё в игре уже нарисовано (`npm run art` генерирует пиксель-арт кодом). Этот список нужен, если хочешь заменить картинки на сгенерированные в ChatGPT или другом сервисе.

## Как заменять

1. Генерируй крупно (512×512 или 1024×1024), на прозрачном фоне, в пиксель-арт стиле.
2. Уменьши до точного размера из таблицы **без сглаживания** (Nearest Neighbor). Пришли мне картинку, и я переведу её в чистую пиксельную сетку и подгоню палитру, как с жабами.
3. Положи PNG с тем же именем в указанную папку. Код трогать не нужно.

К каждому промпту добавляй общий стиль:

> pixel art, crisp 1px dark outline, limited palette, flat shading, no anti-aliasing, transparent background, centered, game UI asset, no text

## Иконки интерфейса (16×16, `client/src/assets/ui/`)

| Файл | Что это | Промпт |
| --- | --- | --- |
| `icon-coin.png` | токен FROG | a gold coin with a tiny frog face embossed in the middle |
| `icon-stamina.png` | стамина | a green battery, three charge bars |
| `icon-edge.png` | стат Edge | a small dark trading screen with a green line chart going up |
| `icon-speed.png` | стат Speed | a yellow lightning bolt |
| `icon-chest.png` | сундук | a small wooden treasure chest with gold trim |
| `icon-pool.png` | пул наград | three stacks of gold coins |
| `icon-casino.png` | казино | a red and white casino chip |
| `icon-manager.png` | менеджер | a clipboard with a checklist and green ticks |
| `icon-summon.png` | призыв | a purple trading card back with a gold frog emblem |
| `icon-frog.png` | жабы | a cute green frog head, front view |
| `icon-sleep.png` | сон | a yellow crescent moon |

## Иконки скиллов (16×16, `client/src/assets/ui/`)

| Файл | Скилл | Промпт |
| --- | --- | --- |
| `skill-patternHunter.png` | Pattern Hunter, +5% | a magnifying glass over a green chart pattern |
| `skill-diamondHands.png` | Diamond Hands, −20% стамины | a shiny blue diamond |
| `skill-degenApe.png` | Degen Ape, +25% в Memecoin Trading | a yellow banana |
| `skill-rugRadar.png` | Rug Radar, +40% в Pump.fun Rugs | a green radar screen with two red blips |
| `skill-chartWizard.png` | Chart Wizard, +25% в Classic Trading | a purple wizard hat with gold stars |
| `skill-hotStreak.png` | Hot Streak, растущий бонус | an orange flame |
| `skill-insomniac.png` | Insomniac, быстрее отдыхает | a white coffee cup with steam |
| `skill-fastFingers.png` | Fast Fingers, торгует быстрее | a mouse cursor arrow with yellow speed lines |

## Карточки и логотип (`client/src/assets/ui/`)

| Файл | Размер | Промпт |
| --- | --- | --- |
| `card-back.png` | 48×64 | back of a collectible trading card, deep purple with a gold border and a frog emblem in the center |
| `logo.png` | любой по ширине, высота 11 | pixel logo text "FROG TRADERS", bright green letters with a dark green drop shadow (тут текст нужен) |

## Жабы (`client/src/assets/sprites/`)

Жаба собирается из двух слоёв одинакового размера: тело (`frog-skin-0..3.png`, 4 цвета кожи) и одежда (`frog-outfit-0..5.png`, по редкости). Каждый файл это лента кадров 24×24: 6 кадров работы, 2 сна, 4 казино, 2 покоя. Такие ленты сложно получить генерацией, поэтому лучше генерировать **портреты для карточек** и отдельные позы, а ленты кадров я соберу из них.

Общий промпт жабы:

> a skinny broke frog trader, big round eyes on top of the head, wide frog grin, thin arms, sitting at a desk, front view, upper body only

Одежда по редкости:

| Редкость | Одежда |
| --- | --- |
| Common | stained grey tank top with holes, a band-aid on the head |
| Uncommon | green hoodie with a dollar sign |
| Rare | white shirt and red tie |
| Epic | purple office suit |
| Legendary | black suit, dark sunglasses, gold chain |
| Mythic | gold suit, small gold crown, gold chain |

## Сцены (`client/src/assets/scenes/`)

| Файл | Размер | Промпт |
| --- | --- | --- |
| `office-memecoin.png` | 160×150 | interior of a messy night-time trading office, warm orange accents, striped wallpaper, a window with a night city, a wall screen, a "WAGMI" poster, wooden floor, empty floor space for desks |
| `office-pumpfun.png` | 160×150 | same office in purple, checkered floor, a "RUG?" poster with a pill |
| `office-classic.png` | 160×150 | same office in teal, calm and tidy, a "HODL" poster with a chart |
| `dorm.png` | 200×120 | a cheap dormitory at night, four wooden bunk beds, a window with the moon, wooden floor |
| `casino.png` | 280×120 | a small casino interior, red walls with gold trim, slot machines on the left, a bar with bottles on the right, red patterned carpet |
| `casino-closed.png` | 280×120 | the same room boarded up with planks, dark, abandoned |
| `hub.png` | 250×250 | уже готова: перекрёсток с тремя зданиями |

Вывески (`sign-*-on.png` 148×20, `casino-sign-on.png` 64×16) лучше оставить кодом: в них текст, и у каждой есть выключенная версия для мигания.
