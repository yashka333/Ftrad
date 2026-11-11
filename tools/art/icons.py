"""16x16 UI and skill icons. Placeholders in the game style; ASSETS.md lists
prompts for replacing them with generated art."""
from pix import Canvas, shade
OUT = '#1a1410'


def _o(c):
    c.outline(OUT)
    return c


def coin():
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6, 6, '#e0a82e'); c.ellipse(8, 8, 4.6, 4.6, '#f7d774')
    for (x, y) in ((6, 5), (7, 5), (8, 5), (9, 6), (8, 7), (7, 8), (6, 9), (7, 10), (8, 10), (9, 10)):
        c.set(x, y, '#b07a12')
    c.set(5, 4, '#fff6c8')
    return _o(c)


def battery():
    c = Canvas(16, 16)
    c.rect(2, 4, 11, 8, '#2e2e38'); c.rect(13, 6, 2, 4, '#2e2e38')
    c.rect(3, 5, 9, 6, '#3ddc84'); c.hline(3, 5, 9, '#8ff0b8')
    for x in (6, 9):
        c.vline(x, 5, 6, '#22a85c')
    return _o(c)


def chart():
    c = Canvas(16, 16)
    c.rect(1, 2, 14, 12, '#1d2a3a')
    pts = [(2, 11), (5, 9), (7, 10), (10, 6), (13, 3)]
    for (a, b), (cc, d) in zip(pts, pts[1:]):
        for t in range(9):
            c.set(round(a + (cc - a) * t / 8), round(b + (d - b) * t / 8), '#3ddc84')
    c.set(12, 3, '#3ddc84'); c.set(13, 4, '#3ddc84'); c.set(11, 3, '#3ddc84')
    return _o(c)


def bolt():
    c = Canvas(16, 16)
    rows = ['......###', '.....###.', '....###..', '...######', '......##.', '.....##..', '....##...', '...##....', '..#......']
    c.grid(3, 3, rows, {'#': '#f2c94c'})
    c.set(8, 3, '#fff3b0')
    return _o(c)


def chest():
    c = Canvas(16, 16)
    c.rect(2, 6, 12, 8, '#8b5a33'); c.rect(2, 3, 12, 4, '#a86c3c')
    c.hline(2, 3, 12, '#c98a50'); c.hline(2, 7, 12, '#c8961e'); c.vline(7, 3, 11, '#c8961e')
    c.rect(7, 8, 2, 2, '#f2c94c')
    return _o(c)


def pool():
    c = Canvas(16, 16)
    for k, (x, y) in enumerate(((3, 10), (8, 11), (5, 6))):
        for j in range(3):
            c.ellipse(x + 3, y + 2 - j * 2, 3, 1.5, '#e0a82e')
            c.hline(x + 1, y + 1 - j * 2, 4, '#f7d774')
    return _o(c)


def chip():
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6.5, 6.5, '#c0392b'); c.ellipse(8, 8, 4, 4, '#f4ead2'); c.ellipse(8, 8, 2.5, 2.5, '#c0392b')
    for (x, y) in ((8, 2), (8, 13), (2, 8), (13, 8)):
        c.rect(x, y, 2, 2, '#f4ead2') if x in (2, 13) else c.rect(x - 1 if x == 8 else x, y, 2, 1, '#f4ead2')
    return _o(c)


def manager():
    c = Canvas(16, 16)
    c.rect(4, 2, 9, 12, '#c8a070'); c.rect(5, 4, 7, 9, '#f4ead2')
    c.rect(6, 1, 5, 2, '#888888')
    for y in (6, 8, 10):
        c.hline(6, y, 5, '#5a5a66')
    c.set(6, 6, '#3ddc84'); c.set(6, 8, '#3ddc84')
    return _o(c)


def card():
    c = Canvas(16, 16)
    c.rect(3, 1, 10, 14, '#6b3fa0'); c.rect(4, 2, 8, 12, '#8a5cc8')
    c.ellipse(8, 8, 3, 3, '#f2c94c'); c.set(8, 8, '#6b3fa0')
    return _o(c)


def frog():
    c = Canvas(16, 16)
    c.ellipse(8, 9, 6.5, 4.5, '#4f9a45')
    c.ellipse(4.5, 5, 2.5, 2.5, '#4f9a45'); c.ellipse(11.5, 5, 2.5, 2.5, '#4f9a45')
    c.rect(4, 4, 2, 2, '#f4ead2'); c.rect(11, 4, 2, 2, '#f4ead2')
    c.set(5, 5, OUT); c.set(12, 5, OUT)
    c.hline(4, 10, 8, '#2a1a10')
    return _o(c)


def moon():
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6, 6, '#f7d774'); 
    for y in range(16):
        for x in range(16):
            if ((x + .5 - 10.5) / 5) ** 2 + ((y + .5 - 6.5) / 5) ** 2 <= 1:
                c.px[x, y] = (0, 0, 0, 0)
    return _o(c)


def magnifier():
    c = Canvas(16, 16)
    c.ellipse(6.5, 6.5, 4.5, 4.5, '#cfe9f2'); c.ellipse(6.5, 6.5, 3, 3, '#1d2a3a')
    c.set(5, 8, '#3ddc84'); c.set(6, 7, '#3ddc84'); c.set(7, 7, '#3ddc84'); c.set(8, 5, '#3ddc84')
    for i in range(4):
        c.rect(10 + i, 10 + i, 2, 2, '#8b5a33')
    return _o(c)


def diamond():
    c = Canvas(16, 16)
    rows = ['..######..', '.##BBBB##.', '##BBBBBB##', '.##BBBB##.', '..##BB##..', '...####...', '....##....']
    c.grid(3, 4, rows, {'#': '#4aa8ff', 'B': '#9fd4ff'})
    c.set(5, 5, '#ffffff')
    return _o(c)


def banana():
    c = Canvas(16, 16)
    for i, (x, y) in enumerate(((3, 4), (3, 6), (4, 8), (5, 10), (7, 11), (9, 12), (11, 12), (13, 11))):
        c.rect(x, y, 3, 2, '#f2d14c')
    c.set(3, 3, '#6b4a1a'); c.set(14, 11, '#6b4a1a')
    return _o(c)


def radar():
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6.5, 6.5, '#0d2a1a'); c.ellipse(8, 8, 4.5, 4.5, '#14402a'); c.ellipse(8, 8, 2, 2, '#0d2a1a')
    for t in range(6):
        c.set(8 + t, 8 - t // 2, '#3ddc84')
    c.set(11, 5, '#ff4d5e'); c.set(5, 10, '#ff4d5e')
    return _o(c)


def wizard():
    c = Canvas(16, 16)
    rows = ['......#.', '.....###', '....####.', '...#####.', '...######', '..#######', '.########', '##########']
    c.grid(2, 3, rows, {'#': '#6b3fa0'})
    c.hline(1, 11, 14, '#4e2c78'); c.set(8, 7, '#f2c94c'); c.set(6, 9, '#f2c94c')
    return _o(c)


def flame():
    c = Canvas(16, 16)
    rows = ['.....#....', '....##....', '...###.#..', '..#####.#.', '.#######..', '.########.', '##########', '###YYYY###', '.##YYYY##.', '..######..']
    c.grid(3, 3, rows, {'#': '#e8662f', 'Y': '#f7d774'})
    return _o(c)


def coffee():
    c = Canvas(16, 16)
    c.rect(3, 6, 8, 8, '#f4ead2'); c.rect(4, 7, 6, 2, '#6b4a1a')
    c.frame(11, 8, 3, 4, '#f4ead2')
    for x, y in ((5, 2), (6, 3), (5, 4), (8, 2), (9, 3), (8, 4)):
        c.set(x, y, '#cfcfcf')
    return _o(c)


def cursor():
    c = Canvas(16, 16)
    rows = ['#.......', '##......', '#W#.....', '#WW#....', '#WWW#...', '#WWWW#..', '#WW###..', '#.#W#...', '...#W#..', '....#...']
    c.grid(6, 3, rows, {'#': OUT, 'W': '#f4ead2'})
    for y in (5, 8, 11):
        c.hline(1, y, 3, '#f2c94c')
    return c


UI = {
    'coin': coin, 'stamina': battery, 'edge': chart, 'speed': bolt, 'chest': chest, 'pool': pool,
    'casino': chip, 'manager': manager, 'summon': card, 'frog': frog, 'sleep': moon,
}
SKILLS = {
    'patternHunter': magnifier, 'diamondHands': diamond, 'degenApe': banana, 'rugRadar': radar,
    'chartWizard': wizard, 'hotStreak': flame, 'insomniac': coffee, 'fastFingers': cursor,
}
