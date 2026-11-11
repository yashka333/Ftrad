"""Hand-drawn 16x16 skill icons, redrawn from the painted concepts in source/skills/skills-ref.png.
One letter per pixel; '.' is transparent. Writes source/skills/px16/<skill>.png and a preview sheet.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
OUT = HERE / 'source/skills/px16'

PAL = {
    'k': (20, 18, 22), 'G': (62, 98, 46), 'g': (104, 146, 66), 'l': (150, 186, 94), 'L': (196, 220, 140),
    'c': (84, 206, 228), 'C': (196, 246, 252), 'd': (36, 120, 150), 'y': (236, 186, 72), 'Y': (255, 230, 140),
    'o': (242, 124, 40), 'O': (255, 196, 80), 'r': (214, 58, 50), 'R': (138, 34, 36), 'w': (246, 242, 232),
    's': (160, 156, 168), 'S': (84, 80, 94), 'n': (138, 86, 48), 'N': (88, 52, 30), 'b': (226, 206, 164),
    'B': (176, 146, 104), 'p': (124, 72, 168), 'P': (178, 126, 220), 'e': (112, 224, 80), 'E': (44, 138, 52),
    'm': (52, 150, 170), 'M': (26, 88, 108), 't': (222, 178, 92), 'T': (164, 120, 58), 'x': (40, 36, 46),
}

ICONS = {
    # green fist squeezing a cyan diamond
    'diamondHands': [
        "................",
        "....kkkkkkkk....",
        "...klgkLgkLgk...",
        "..kgglgglgglgk..",
        "..kgGgGgGgGggk..",
        "..kkkkkkkkkkgk..",
        ".kCCcCcckddkGk..",
        "kCwCCcccckddkk..",
        "kcCccccckdddk...",
        ".kcccccdddddk...",
        "..kccccdddk.....",
        "...kcccddk...c..",
        "....kcddk...cC..",
        ".c...kdk.....c..",
        "cCc...k.........",
        ".c..............",
    ],
    # sleepy frog head on a patched tan pillow, a Z above
    'powerNap': [
        "...........kkkk.",
        "...........kwwk.",
        "....kkkk....kwk.",
        "...kgglgk..kwwk.",
        "..kglggggk.kkkk.",
        ".kgkkkkkggk.....",
        ".kgwwwwwkggk....",
        "kgkkkkkkkgggk...",
        "kggggggggggk....",
        "ktkgGgGgGgktk...",
        "kttkkkkkkkttTk..",
        "kttttttttkkTTk..",
        "ktTktttttkNnTk..",
        ".kTTkttttkNNk...",
        "..kkTTTTTTkk....",
        "....kkkkkk......",
    ],
    # green fingers hammering keys, speed lines behind
    'fastFingers': [
        "................",
        ".eeee...........",
        "...eeeee..kkk...",
        "..........kglk..",
        ".eeee...kkkgglk.",
        "......kkglkgggk.",
        "...kkkgglkggGk..",
        "..kglkggGkgGk...",
        "..kggkgGkkkk....",
        "..kgGkkkbbkbbk..",
        ".kkkkbbkbbkbbk..",
        "kbbkbbkbbkbbbk..",
        "kBBkBBkBBkBBBk..",
        "kSSSSSSSSSSSSSk.",
        "kSxxxxxxxxxxxSk.",
        ".kkkkkkkkkkkkk..",
    ],
    # coffee cup with a frog peeking over the rim, green steam
    'caffeine': [
        "....e..e........",
        "...e..e..e......",
        "....e..e..e.....",
        "...kkk..kkk.....",
        "..kgwkkkkwgk....",
        "..kgkwggwkgk....",
        ".kkkkkkkkkkkk...",
        ".kbbbbbbbbbbk...",
        "..kbbbbbbbbk.e..",
        "e.knnnnnnnnk.e..",
        "..knnyNyNynk....",
        "..knnNyyyNnk....",
        "..knnnnnnnnk....",
        "...kbbbbbbk.....",
        "...kBBBBBBk.....",
        "....kkkkkk......",
    ],
    # red candle slammed into a cyan striped barrier
    'stopLoss': [
        "......kk........",
        "...s..kk..s.....",
        "......kk........",
        ".....krrk.......",
        ".....krrk.......",
        ".....krRk.......",
        ".....krRk.......",
        "..y..krRk..y....",
        "...y.krRk.y.....",
        "......kk........",
        ".kkkkkkkkkkkkk..",
        "kcdccddccddccdk.",
        "kdccddccddccddk.",
        "kkkkkkkkkkkkkkk.",
        ".kSk.......kSk..",
        ".kkk.......kkk..",
    ],
    # three rising green candles on fire
    'hotStreak': [
        "...........oo...",
        "..........oOYo..",
        "......oo..oYOo..",
        ".....oOYo.kkkk..",
        "..oo.oYOokeeEk..",
        ".oOYokkkkkeeEk..",
        ".oYOkeeEkkeeEk..",
        ".kkkkeeEkkeeEk..",
        ".keeEkeeEkkeEk..",
        ".keeEkeeEkkkkk..",
        ".keeEkeEEk..k...",
        ".keEEkkkkk......",
        ".kkkkk.k........",
        "...k............",
        "................",
        "................",
    ],
    # V chart: red slide down, green climb back up, a frog leaping the dip
    'dipBuyer': [
        "..........kkk...",
        ".........kglgk..",
        "........kgwkwgk.",
        "........kggggGk.",
        ".........kGGk...",
        "rr..............",
        "rrr..........ee.",
        ".rrr........eee.",
        "..rrr......eee..",
        "...rrr....eee...",
        "....rrr..eee....",
        ".....rrreee.....",
        "......rRee......",
        ".......Re.......",
        "kkkkkkkkkkkkkkkk",
        "................",
    ],
    # skull in a backwards purple cap, slamming the big red button
    'degenMode': [
        "...kkkkkkkk.....",
        "..kpPPPPPPpk....",
        ".kpppppppppkkk..",
        ".kkkkkkkkkkkppk.",
        ".kwwwwwwwwk.kk..",
        "kwwkkwwkkwwk....",
        "kwwkkwwkkwwk....",
        "kwwwwwkwwwwk....",
        ".kwwwwwwwwk.....",
        "..kwkwkwkk......",
        "..kkkkkkk.......",
        ".kkkkkkkkkk..y..",
        ".krrrrrrrrk.y...",
        "kRRRRRRRRRRk....",
        "kykykykykykk....",
        "kkkkkkkkkkkk....",
    ],
    # four-leaf clover with a tiny gold crown
    'luckyCharm': [
        "...kkk..kkk.....",
        "..kgggk.kgggk...",
        ".kglggkkgglgk...",
        ".kgggggkgggggk..",
        "..kggykyykygk...",
        "kkkkgkYYYkgkkk..",
        "kglggkyyykggglk.",
        "kgggggkkkgggggk.",
        ".kggggkgkggggk..",
        "..kgggkgkgggk...",
        "...kkkkGkkkk....",
        ".......kGk......",
        "........kGk.....",
        ".........kGk....",
        "..........kk....",
        "................",
    ],
    # two monitors with frog faces, a green arrow copying left to right
    'copyTrader': [
        "....kkkkkkkk....",
        "...keeeeeeeek...",
        "...kek....keek..",
        "..........keeek.",
        "kkkkkkk....kek..",
        "kMMMMMk.....k...",
        "kMggg.k.kkkkkkk.",
        "kMgwgMk.kMMMMMk.",
        "kMgggMk.kMgggMk.",
        "kMMMMMk.kMgwgMk.",
        "kkkkkkk.kMgggMk.",
        "...k....kMMMMMk.",
        "..kSk...kkkkkkk.",
        "..kkk......k....",
        "..........kSk...",
        "..........kkk...",
    ],
    # cyan crescent moon, a frog with a laptop curled inside
    'nightOwl': [
        ".....kkkkk......",
        "...kkcccck......",
        "..kccCck........",
        ".kcCck..........",
        ".kcck..kkk.kkk..",
        "kcck..kgwgkgwgk.",
        "kcck..kggggggk..",
        "kcck...kSSSSSk..",
        "kcck..kSxxxxxSk.",
        "kccck.kSxxxxxSk.",
        ".kcck.kkkkkkkkk.",
        ".kccck......c...",
        "..kcccckkkkcCc..",
        "...kkcccccck.c..",
        ".....kkkkkk.....",
        "................",
    ],
    # frog in a gaming chair firing a harpoon at a teal whale
    'whaleHunter': [
        "............kk..",
        "...........kmMk.",
        "....c.c...kmMk..",
        ".....c....kmk...",
        "....kkkkkkkmk...",
        "...kmmmmmmmmk...",
        "..kmmmmmmmmmMk..",
        ".kmwkmmmmmmmMk..",
        ".kmmmmmmmmmMk...",
        ".kcccccccMMk....",
        "..kccccckkk.....",
        "...kkkkk........",
        "kkkk............",
        "kSSSSSSSSSSSs...",
        "kkkk.......ss...",
        "................",
    ],
    # radar screen with a sweeping green beam and a purple rolled rug
    'rugRadar': [
        ".....kkkkkk.....",
        "...kkEEEEEekk...",
        "..kEEEkEEeeeEk..",
        ".kEEkEEkEeeeEEk.",
        ".kEkEEEkeeEEkEk.",
        "kEEEEEEkeEEEEEEk",
        "kEkkkkkkkkkkkkEk",
        "kEEEEkkkkEEEEEEk",
        "kEEEkpPPPkEEEEEk",
        "kEkEkpkkPpkEEkEk",
        ".kEEkpkPkpkkEEk.",
        ".kEEEkpppkpykEk.",
        "..kEEEkkkkykyk..",
        "...kkEEEEEkkk...",
        ".....kkkkkk.....",
        "................",
    ],
    # a green frog eye over a torn chart sheet
    'insider': [
        "kkkkkkkkkkkkkkk.",
        "kbbbbbbbbbbbkrk.",
        "kbBbbbbbbbbbkrk.",
        "kbbbbkkkkkbbbkbk",
        "kbbkkgggggkkbbbk",
        "kbkgggkkkgggkbbk",
        "kkgggkekkkgggkbk",
        "kkggkkeEkkkggkkk",
        "kkgggkekkkgggkbk",
        "kbkgggkkkgggkbbk",
        "kbbkkgggggkkbbbk",
        "krkbbkkkkkbbbbbk",
        "krkbbbbbbbbbkekk",
        "kkkbbBbbbbbbkek.",
        "kbbbbbbbbbbbbkk.",
        "kkkkkkkkkkkkkk..",
    ],
}


def render(rows):
    h = len(rows)
    w = 16
    a = np.zeros((16, 16, 4), np.uint8)
    for y, r in enumerate(rows[:16]):
        for x, ch in enumerate(r[:16]):
            if ch in PAL:
                a[y, x, :3] = PAL[ch]
                a[y, x, 3] = 255
    return a


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    icons = {}
    for k, rows in ICONS.items():
        bad = [i for i, r in enumerate(rows) if len(r) != 16]
        if bad or len(rows) != 16:
            print('size', k, len(rows), [(i, len(rows[i])) for i in bad])
        icons[k] = render(rows)
        Image.fromarray(icons[k], 'RGBA').save(OUT / f'{k}.png')
    sheet = np.zeros((20, 14 * 20, 4), np.uint8)
    sheet[..., :3] = (30, 26, 36); sheet[..., 3] = 255
    for i, ic in enumerate(icons.values()):
        m = ic[..., 3] > 0
        sheet[2:18, 2 + i * 20:18 + i * 20][m] = ic[m]
    Image.fromarray(sheet).resize((sheet.shape[1] * 7, sheet.shape[0] * 7), Image.NEAREST).save(
        '/tmp/claude-0/-home-claude/f782d41d-8771-50ed-9d54-4ef8681aae6f/scratchpad/skill16.png')
    return icons


if __name__ == '__main__':
    main()
    print('ok')
