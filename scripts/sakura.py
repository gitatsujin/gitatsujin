#!/usr/bin/env python3
"""
桜 Sakura Garden — cena noturna em pixel art: Monte Fuji, sol vermelho, torii e
uma cerejeira cujas flores são os dias do seu último ano no GitHub.
A árvore floresce da esquerda para a direita (do dia mais antigo ao mais
recente); dias com commits brilham mais forte e cintilam. Pétalas caem ao vento.

Uso:
  GITHUB_TOKEN=... python sakura.py --user gitatsujin --out dist/daily.svg
  python sakura.py --mock --out sakura.svg
Sem dependências externas.
"""
import argparse, json, math, os, random, urllib.request

W, H, P = 240, 80, 4          # grade de pixels e tamanho de cada pixel
D = 16.0                      # duração do ciclo (s)
BLOOM0, BLOOM1 = 0.6, 7.0     # janela em que a árvore floresce
FADE0, FADE1 = 13.6, 15.4     # flores somem antes de recomeçar

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{contributionLevel}}}}}}"""


def fetch(user, token):
    body = json.dumps({"query": QUERY, "variables": {"login": user}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "sakura-garden"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in data:
        raise SystemExit(f"Erro da API do GitHub: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [LEVELS.get(d["contributionLevel"], 0) for w in cal["weeks"] for d in w["contributionDays"]]
    return days, cal["totalContributions"]


def mock(seed=5):
    r = random.Random(seed)
    days = [0 if r.random() < 0.6 else r.choice([1, 1, 2, 3, 4]) for _ in range(366)]
    return days, sum(days) * 3

# ------------------------------------------------------------ fonte 3x5 ---
FONT = {
    'A': "010101111101101", 'B': "110101110101110", 'C': "011100100100011", 'D': "110101101101110",
    'E': "111100110100111", 'F': "111100110100100", 'G': "011100101101011", 'H': "101101111101101",
    'I': "111010010010111", 'J': "001001001101010", 'K': "101101110101101", 'L': "100100100100111",
    'M': "101111111101101", 'N': "110101101101101", 'O': "010101101101010", 'P': "110101110100100",
    'Q': "010101101110011", 'R': "110101110101101", 'S': "011100010001110", 'T': "111010010010010",
    'U': "101101101101111", 'V': "101101101101010", 'W': "101101111111101", 'X': "101101010101101",
    'Y': "101101010010010", 'Z': "111001010100111", '0': "111101101101111", '1': "010110010010111",
    '2': "110001010100111", '3': "110001010001110", '4': "101101111001001", '5': "111100110001110",
    '6': "011100111101111", '7': "111001010010010", '8': "111101111101111", '9': "111101111001110",
    ' ': "000000000000000", '.': "000000000000010", '@': "010101111100011", '-': "000000111000000",
}


def text_cells(s, x, y):
    out = []
    for ch in s.upper():
        bits = FONT.get(ch, FONT[' '])
        for i, b in enumerate(bits):
            if b == '1':
                out.append((x + i % 3, y + i // 3))
        x += 4
    return out


# ------------------------------------------------------------- cena -------
def build(days, total, user):
    rnd = random.Random(42)
    g = [[None] * W for _ in range(H)]

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = c

    # céu em faixas com transição pontilhada (dithering)
    bands = [(0, "#06070b"), (16, "#0a0910"), (30, "#120a12"), (42, "#1c0b14"), (52, "#2a0d17"), (60, "#3a1019")]
    for y in range(H):
        idx = max(i for i, (y0, _) in enumerate(bands) if y >= y0)
        for x in range(W):
            c = bands[idx][1]
            if idx + 1 < len(bands) and y == bands[idx + 1][0] - 1 and (x + y) % 2 == 0:
                c = bands[idx + 1][1]
            g[y][x] = c

    # sol vermelho com faixas horizontais (estilo retrô)
    sx, sy, sr = 194, 27, 15
    for y in range(sy - sr, sy + sr + 1):
        for x in range(sx - sr, sx + sr + 1):
            d = math.hypot(x - sx, y - sy)
            if d <= sr + 0.3:
                c = "#c8102e" if d > sr - 3 else "#e0262f"
                if y > sy + 4 and (y - sy) % 3 == 0:
                    continue
                put(x, y, c)

    # montanhas distantes
    for x in range(W):
        top = int(56 + 3 * math.sin(x / 11) + 2 * math.sin(x / 5.3 + 1))
        for y in range(top, H):
            put(x, y, "#0f0d14")

    # Monte Fuji
    px, py, base = 150, 30, 64
    for y in range(py, base + 1):
        d = y - py
        hw = 3 + d * 2.25
        for x in range(int(px - hw), int(px + hw) + 1):
            shade = "#151620" if x < px + d * 0.4 else "#1c1e2b"
            put(x, y, shade)
    for x in range(px - 25, px + 26):
        depth = 8 + round(1.6 * math.sin(x / 2.1)) + (2 if (x // 4) % 3 == 0 else 0)
        for y in range(py, py + depth):
            d = y - py
            if abs(x - px) <= 3 + d * 2.25:
                put(x, y, "#e9e6f2" if x < px + d * 0.4 else "#c9c6d8")

    # colinas e chão
    for x in range(W):
        top = int(66 + 1.5 * math.sin(x / 7 + 2) + math.sin(x / 3.1))
        for y in range(top, H):
            put(x, y, "#0b0b10" if y > top else "#14141c")
    for x in range(0, W, 3):                      # tufos de grama
        if rnd.random() < 0.5:
            put(x, 66 + rnd.randint(0, 2), "#1d1a24")

    # torii
    tx = 214
    for y in range(49, 69):
        for x in (tx + 1, tx + 2, tx + 17, tx + 18):
            put(x, y, "#c8102e" if x in (tx + 1, tx + 17) else "#8f1018")
    for x in range(tx - 3, tx + 23):
        put(x, 45, "#14080a")
        put(x, 46, "#c8102e")
    put(tx - 4, 44, "#14080a"); put(tx + 23, 44, "#14080a")
    put(tx - 3, 44, "#14080a"); put(tx + 22, 44, "#14080a")
    for x in range(tx - 1, tx + 21):
        put(x, 50, "#c8102e"); put(x, 51, "#8f1018")
    for y in (47, 48, 49):
        put(tx + 9, y, "#8f1018"); put(tx + 10, y, "#8f1018")

    # cerejeira: tronco e galhos
    def line(x0, y0, x1, y1, c, w=1):
        n = max(abs(x1 - x0), abs(y1 - y0)) or 1
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n); y = round(y0 + (y1 - y0) * i / n)
            for dx in range(w):
                put(x + dx, y, c)
    for y in range(44, 69):
        w = 3 + (y - 44) // 9
        for dx in range(w):
            put(48 + dx - (y - 44) // 14, y, "#2a1416" if dx < w - 1 else "#3b1d20")
    for x0, y0, x1, y1, w in ((49, 46, 26, 33, 2), (50, 45, 76, 30, 2), (49, 44, 47, 18, 2),
                              (40, 40, 16, 40, 1), (60, 39, 90, 41, 1), (48, 30, 34, 20, 1), (50, 28, 66, 17, 1)):
        line(x0, y0, x1, y1, "#2a1416", w)

    # copa: elipses sobrepostas
    blobs = [(49, 25, 27, 13), (28, 33, 17, 9), (74, 31, 18, 10), (47, 14, 19, 8), (16, 39, 9, 5), (89, 38, 9, 5)]
    canopy = []
    for y in range(H):
        for x in range(W):
            if any(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1 for cx, cy, rx, ry in blobs):
                canopy.append((x, y))
    for x, y in canopy:
        put(x, y, "#3a1226" if (x * 7 + y * 3) % 5 else "#4a1830")

    for _ in range(70):                           # pétalas caídas no chão
        x = int(rnd.gauss(52, 22)); y = 67 + rnd.randint(0, 3)
        if g[y][x if 0 <= x < W else 0] in ("#0b0b10", "#14141c"):
            put(x, y, rnd.choice(["#a33a62", "#e2668f", "#5c1f38"]))

    # texto
    title = "SAKURA GARDEN"
    label = f"{total} CONTRIBUICOES"
    for x, y in text_cells(title, 140 - len(title) * 2, 4):
        put(x, y, "#f5efe3")
    for x, y in text_cells(label, 140 - len(label) * 2, 11):
        put(x, y, "#8b949e")

    # ------------------------------------------------ flores = dias do ano
    rnd2 = random.Random(7)
    slots = [c for c in canopy if (c[0] + 2 * c[1]) % 2 == 0]
    rnd2.shuffle(slots)
    slots = slots[:len(days)]
    slots.sort(key=lambda c: (c[0] + rnd2.uniform(-3, 3)))      # floresce da esquerda p/ direita
    PETAL = ["#8a2a50", "#c2416e", "#ee6f98", "#ff9dbb", "#ffe1ea"]
    groups = {}
    sparkle = []
    for i, ((x, y), lv) in enumerate(zip(slots, days)):
        b = int(24 * i / max(1, len(slots)))
        groups.setdefault(b, []).append((x, y, PETAL[lv]))
        if lv >= 2:
            sparkle.append((x, y, lv))

    # ------------------------------------------------ SVG
    def rle(grid):
        out = []
        for y, row in enumerate(grid):
            x = 0
            while x < W:
                c = row[x]
                if c is None:
                    x += 1; continue
                x1 = x
                while x1 + 1 < W and row[x1 + 1] == c:
                    x1 += 1
                out.append(f'<rect x="{x * P}" y="{y * P}" width="{(x1 - x + 1) * P}" height="{P}" fill="{c}"/>')
                x = x1 + 1
        return "".join(out)

    css = [f"""
  .bl {{ opacity: 0; animation: bloom {D}s steps(1, end) infinite; }}
  @keyframes bloom {{ 0% {{ opacity: 0; }} 2% {{ opacity: .55; }} 4% {{ opacity: 1; }}
    {FADE0 / D * 100:.2f}% {{ opacity: 1; }} {(FADE0 + FADE1) / 2 / D * 100:.2f}% {{ opacity: .5; }}
    {FADE1 / D * 100:.2f}%, 100% {{ opacity: 0; }} }}
  .sp {{ animation: sp 1.6s steps(2, end) infinite; }}
  @keyframes sp {{ 0%, 100% {{ fill: #ffffff; }} 50% {{ fill: #ff9dbb; }} }}
  .st {{ animation: st 2.4s steps(2, end) infinite; }}
  @keyframes st {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .15; }} }}
  .lan {{ animation: lan 1.3s steps(3, end) infinite alternate; }}
  @keyframes lan {{ from {{ fill: #ff5a3c; }} to {{ fill: #ffb347; }} }}
  .pt {{ animation-iteration-count: infinite; animation-timing-function: linear; }}"""]
    for b in groups:
        css.append(f"\n  .g{b} {{ animation-delay: {-(D - (BLOOM0 + (BLOOM1 - BLOOM0) * b / 24)):.2f}s; }}")

    blossoms = []
    for b, cells in sorted(groups.items()):
        rects = "".join(f'<path d="M{x * P},{(y - 1) * P}h{P}v{P}h{P}v{P}h-{P}v{P}h-{P}v-{P}h-{P}v-{P}h{P}z" fill="{c}"/>' for x, y, c in cells)
        blossoms.append(f'<g class="bl g{b}">{rects}</g>')
    spark = "".join(
        f'<rect class="sp" style="animation-delay:-{rnd.uniform(0, 1.6):.2f}s" x="{x * P + 1}" y="{y * P + 1}" width="{P - 2}" height="{P - 2}" fill="#ffffff"/>'
        for x, y, lv in sparkle if lv >= 3)

    stars = []
    for _ in range(60):
        x, y = rnd.randrange(W), rnd.randrange(0, 44)
        if g[y][x] in ("#06070b", "#0a0910", "#120a12"):
            cls = ' class="st"' if rnd.random() < 0.45 else ""
            delay = f' style="animation-delay:-{rnd.uniform(0, 2.4):.2f}s"' if cls else ""
            stars.append(f'<rect{cls}{delay} x="{x * P}" y="{y * P}" width="{P}" height="{P}" fill="{rnd.choice(["#3a3550", "#6b6488", "#cfc8e8"])}"/>')

    # lanternas penduradas nos galhos
    lanterns = ""
    for lx, ly in ((30, 36), (72, 34)):
        lanterns += (f'<rect x="{lx * P + P // 2}" y="{(ly - 3) * P}" width="2" height="{3 * P}" fill="#2a1416"/>'
                     f'<rect class="lan" x="{(lx - 1) * P}" y="{ly * P}" width="{3 * P}" height="{4 * P}" fill="#ff7a3c"/>'
                     f'<rect x="{(lx - 1) * P}" y="{ly * P}" width="{3 * P}" height="{P // 2}" fill="#14080a"/>'
                     f'<rect x="{(lx - 1) * P}" y="{(ly + 4) * P - P // 2}" width="{3 * P}" height="{P // 2}" fill="#14080a"/>')

    # pétalas ao vento
    petals = []
    for i in range(42):
        x0, y0 = rnd.choice(canopy)
        dur = rnd.uniform(6, 11)
        dx = rnd.uniform(70, 170) * P / 4
        dy = (68 - y0 + rnd.uniform(0, 4)) * P
        name = f"p{i}"
        sway = rnd.uniform(6, 14)
        css.append(f"""
  .{name} {{ animation: {name} {dur:.2f}s linear infinite; animation-delay: -{rnd.uniform(0, dur):.2f}s; }}
  @keyframes {name} {{ 0% {{ transform: translate(0px, 0px); opacity: 0; }} 6% {{ opacity: 1; }}
    35% {{ transform: translate({dx * .3:.0f}px, {dy * .35:.0f}px); }} 55% {{ transform: translate({dx * .5 + sway:.0f}px, {dy * .55:.0f}px); }}
    80% {{ transform: translate({dx * .8 - sway:.0f}px, {dy * .82:.0f}px); opacity: 1; }}
    100% {{ transform: translate({dx:.0f}px, {dy:.0f}px); opacity: 0; }} }}""")
        w, h = rnd.choice([(P, P // 2 + 1), (P // 2 + 1, P // 2 + 1), (P, P)])
        petals.append(f'<rect class="{name}" x="{x0 * P}" y="{y0 * P}" width="{w}" height="{h}" fill="{rnd.choice(["#ff9dbb", "#ffc2d4", "#e2668f"])}"/>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W * P}" height="{H * P}" viewBox="0 0 {W * P} {H * P}" shape-rendering="crispEdges">
<title>Sakura Garden: o último ano de contribuições de @{user} em pixel art</title>
<style>{''.join(css)}
</style>
<g>{rle(g)}</g>
<g>{''.join(stars)}</g>
<g>{''.join(blossoms)}</g>
<g>{spark}</g>
{lanterns}
<g>{''.join(petals)}</g>
</svg>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "gitatsujin"))
    ap.add_argument("--out", default="sakura.svg")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    days, total = mock() if a.mock else fetch(a.user, os.environ["GITHUB_TOKEN"])
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(build(days, total, a.user))
    print(f"Gerado: {a.out} ({len(days)} dias, {total} contribuições)")


if __name__ == "__main__":
    main()
