#!/usr/bin/env python3
"""
侍 Samurai Contributions — gera um SVG animado em que um samurai corre pelo
gráfico de contribuições do GitHub e corta cada quadradinho com a katana.

Uso:
  GITHUB_TOKEN=... python samurai.py --user gitatsujin --out dist
  python samurai.py --mock --out dist          # dados de exemplo (teste local)

Gera: samurai.svg (tema claro), samurai-dark.svg (tema escuro) e hanko.svg.
Sem dependências externas (apenas biblioteca padrão do Python).
"""
import argparse
import json
import os
import random
import urllib.request

# ----------------------------------------------------------------- dados ---

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionLevel weekday } }
      }
    }
  }
}"""


def fetch_weeks(user, token):
    body = json.dumps({"query": QUERY, "variables": {"login": user}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": "samurai-contributions"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"Erro da API do GitHub: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    grid = []
    for w in weeks:
        col = [None] * 7
        for d in w["contributionDays"]:
            col[d["weekday"]] = LEVELS.get(d["contributionLevel"], 0)
        grid.append(col)
    return grid


def mock_weeks(seed=42):
    rnd = random.Random(seed)
    grid = []
    for c in range(53):
        col = []
        for r in range(7):
            if c == 52 and r > 3:
                col.append(None)
                continue
            x = rnd.random()
            col.append(0 if x < 0.45 else 1 if x < 0.65 else 2 if x < 0.8 else 3 if x < 0.92 else 4)
        grid.append(col)
    return grid

# ---------------------------------------------------------------- temas ---

THEMES = {
    "dark": {
        "levels": ["#161b22", "#3d0c11", "#6e1018", "#a3111f", "#e0262f"],
        "body": "#f5efe3", "accent": "#e0262f", "blade": "#dfe6ee",
        "slash": "#ffffff", "slash_glow": "#ff4d4d", "gold": "#d4a017",
    },
    "light": {
        "levels": ["#ebedf0", "#f6c9c4", "#ec8a80", "#d94a3d", "#a8141f"],
        "body": "#1b1b1b", "accent": "#c8102e", "blade": "#6b7280",
        "slash": "#c8102e", "slash_glow": "#ff8a80", "gold": "#b8860b",
    },
}

# ------------------------------------------------------------ geometria ---

CELL, GAP = 11, 3
STEP = CELL + GAP
PAD_X, TOP, PAD_B = 18, 82, 14
ZAN_PATH = "M-35.2 -17.0V13.8H-34.0C-30.880000000000003 13.8 -27.6 12.04 -27.6 11.32V9.559999999999999H-23.84V18.84H-38.08L-37.44 21.159999999999997H-23.84V37.4H-22.24C-17.68 37.4 -14.96 35.56 -14.96 35.0V21.159999999999997H-0.3200000000000003L0.1600000000000037 21.08C-1.2800000000000011 26.759999999999998 -3.6799999999999997 31.96 -7.600000000000001 36.68L-6.719999999999999 37.56C9.840000000000003 27.56 11.04 12.04 11.04 -1.6400000000000006V-5.880000000000003H18.96V37.48H20.64C25.440000000000005 37.48 28.160000000000004 35.8 28.240000000000002 35.32V-5.880000000000003H35.839999999999996C36.96 -5.880000000000003 37.839999999999996 -6.280000000000001 38.080000000000005 -7.160000000000004C34.720000000000006 -10.280000000000001 29.119999999999997 -14.759999999999998 29.119999999999997 -14.759999999999998L24.240000000000002 -8.200000000000003H11.04V-24.520000000000003C18.4 -25.4 26.240000000000002 -27.0 31.199999999999996 -28.440000000000005C33.839999999999996 -27.800000000000004 35.52 -28.04 36.4 -28.840000000000003L25.199999999999996 -37.480000000000004C22.240000000000002 -34.44 16.64 -29.96 11.439999999999998 -26.68L2.240000000000002 -29.64V-1.7199999999999989C2.240000000000002 5.32 2.0 12.279999999999998 0.6400000000000006 18.84C-2.479999999999997 16.119999999999997 -6.640000000000001 12.919999999999998 -6.640000000000001 12.919999999999998L-11.280000000000001 18.84H-14.96V9.559999999999999H-11.280000000000001V12.52H-10.0C-7.280000000000001 12.52 -3.4399999999999977 10.759999999999998 -3.3599999999999994 10.119999999999997V-13.64C-1.9200000000000017 -13.96 -0.8800000000000026 -14.600000000000001 -0.3999999999999986 -15.079999999999998L-8.32 -21.08L-12.0 -17.0H-14.96V-24.04H-1.6000000000000014C-0.4799999999999969 -24.04 0.3200000000000003 -24.440000000000005 0.5600000000000023 -25.32C-2.479999999999997 -28.120000000000005 -7.600000000000001 -32.36 -7.600000000000001 -32.36L-12.079999999999998 -26.28H-14.96V-34.519999999999996C-13.04 -34.760000000000005 -12.48 -35.56 -12.32 -36.60000000000001L-23.84 -37.56V-26.28H-37.52L-36.88 -24.04H-23.84V-17.0H-27.2L-35.2 -20.36ZM-23.2 -3.0799999999999983V7.239999999999998H-27.6V-3.0799999999999983ZM-15.52 -3.0799999999999983H-11.280000000000001V7.239999999999998H-15.52ZM-23.2 -5.32H-27.6V-14.759999999999998H-23.2ZM-15.52 -5.32V-14.759999999999998H-11.280000000000001V-5.32Z"
DURATION = 18.0          # segundos por ciclo completo
RUN_START, RUN_END = 4.0, 80.0   # % do ciclo em que o samurai corre
REGROW_FROM, REGROW_TO = 92.0, 97.0


def pct(x):
    return f"{x:.3f}%"


def samurai_figure(t):
    """Samurai original desenhado à mão, virado para a direita, pés em (0,0)."""
    b, a, k, g = t["body"], t["accent"], t["blade"], t["gold"]
    return f"""
    <g class="legs">
      <path d="M-7,-15 L7,-15 L10,0 L3,0 L0,-7 L-3,0 L-10,0 Z" fill="{b}"/>
    </g>
    <path d="M-6.5,-27 L6.5,-27 L7.5,-15 L-7.5,-15 Z" fill="{b}"/>
    <path d="M-6.5,-27 L0,-20 L6.5,-27" fill="none" stroke="{a}" stroke-width="1.2"/>
    <rect x="-8" y="-17.5" width="16" height="3" rx="1" fill="{a}"/>
    <circle cx="0" cy="-32" r="5" fill="{b}"/>
    <ellipse cx="-2.5" cy="-37.6" rx="3.2" ry="1.7" fill="{b}"/>
    <rect x="-5.2" y="-34.4" width="10.4" height="2" rx="0.8" fill="{a}"/>
    <path class="band" d="M-5,-33.6 L-13,-31 L-12,-34.5 Z" fill="{a}"/>
    <g class="sword">
      <line x1="2" y1="-24.5" x2="10" y2="-21" stroke="{b}" stroke-width="3" stroke-linecap="round"/>
      <line x1="10" y1="-21" x2="14.5" y2="-22.6" stroke="{a}" stroke-width="2.6" stroke-linecap="round"/>
      <circle cx="15" cy="-22.8" r="1.7" fill="{g}"/>
      <path d="M15.5,-23 Q27,-26.5 38,-34" fill="none" stroke="{k}" stroke-width="1.8" stroke-linecap="round"/>
      <path class="arc" d="M30,-40 Q44,-22 30,-4" fill="none" stroke="{t['slash']}" stroke-width="1.6" stroke-linecap="round" opacity="0"/>
    </g>"""


def build_svg(grid, t):
    cols = len(grid)
    width = PAD_X * 2 + cols * STEP - GAP
    height = TOP + 7 * STEP - GAP + PAD_B
    run = RUN_END - RUN_START
    col_time = DURATION * run / 100 / cols          # segundos por coluna
    x_first = PAD_X + CELL / 2 - 34
    x_last = PAD_X + (cols - 1) * STEP + CELL / 2 - 34
    feet_y = TOP - 5

    css = [f"""
  .sam {{ animation: run {DURATION}s linear infinite; }}
  .sam .sword {{ transform-box: view-box; transform-origin: 2px -24.5px;
                 animation: swing {col_time:.4f}s ease-in infinite; }}
  .sam .arc {{ animation: arc {col_time:.4f}s linear infinite; }}
  .sam .legs {{ transform-origin: 0px -15px; animation: stride {col_time*2:.4f}s ease-in-out infinite; }}
  .sam .band {{ transform-origin: -5px -33.6px; animation: flutter {col_time:.4f}s ease-in-out infinite; }}
  .half {{ transform-box: fill-box; transform-origin: center; }}
  @keyframes run {{
    0% {{ transform: translate({x_first - 60:.1f}px, {feet_y}px) scale(1.3); opacity: 1; }}
    {pct(RUN_START)} {{ transform: translate({x_first:.1f}px, {feet_y}px) scale(1.3); }}
    {pct(RUN_END)} {{ transform: translate({x_last:.1f}px, {feet_y}px) scale(1.3); opacity: 1; }}
    {pct(RUN_END + 4)} {{ transform: translate({x_last + 60:.1f}px, {feet_y}px) scale(1.3); opacity: 0; }}
    100% {{ transform: translate({x_last + 60:.1f}px, {feet_y}px) scale(1.3); opacity: 0; }}
  }}
  @keyframes swing {{ 0% {{ transform: rotate(-55deg); }} 40% {{ transform: rotate(38deg); }} 100% {{ transform: rotate(-55deg); }} }}
  @keyframes arc {{ 0%, 22% {{ opacity: 0; }} 32% {{ opacity: .9; }} 50%, 100% {{ opacity: 0; }} }}
  .zan {{ opacity: 0; animation: zan {DURATION}s ease-out infinite; transform-box: fill-box; transform-origin: center; }}
  @keyframes zan {{ 0%, {pct(RUN_END + 1)} {{ opacity: 0; transform: scale(1.6); }}
    {pct(RUN_END + 3.5)} {{ opacity: .95; transform: scale(1); }}
    {pct(REGROW_FROM - 1)} {{ opacity: .95; transform: scale(1); }}
    {pct(REGROW_FROM + 1.5)}, 100% {{ opacity: 0; transform: scale(1); }} }}
  @keyframes stride {{ 0%, 100% {{ transform: skewX(-14deg); }} 50% {{ transform: skewX(14deg); }} }}
  @keyframes flutter {{ 0%, 100% {{ transform: rotate(0deg); }} 50% {{ transform: rotate(-14deg); }} }}"""]

    base, halves, slashes = [], [], []
    for c, col in enumerate(grid):
        x = PAD_X + c * STEP
        p = RUN_START + run * (c + 0.5) / cols
        cut_a, cut_b = f"a{c}", f"b{c}"
        has_cut = False
        for r, lvl in enumerate(col):
            if lvl is None:
                continue
            y = TOP + r * STEP
            base.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{t["levels"][0]}"/>')
            if lvl == 0:
                continue
            has_cut = True
            color = t["levels"][lvl]
            # corte diagonal: triângulo superior-esquerdo e inferior-direito
            halves.append(f'<path class="half {cut_a}" d="M{x},{y + CELL} L{x},{y + 2} Q{x},{y} {x + 2},{y} L{x + CELL},{y} Z" fill="{color}"/>')
            halves.append(f'<path class="half {cut_b}" d="M{x},{y + CELL} L{x + CELL},{y} L{x + CELL},{y + CELL - 2} Q{x + CELL},{y + CELL} {x + CELL - 2},{y + CELL} Z" fill="{color}"/>')
        # rastro do corte (sempre aparece, mesmo em colunas vazias)
        y0, y1 = TOP - 4, TOP + 7 * STEP + 1
        slashes.append(
            f'<g class="s{c}"><line x1="{x - 3}" y1="{y1}" x2="{x + CELL + 3}" y2="{y0}" stroke="{t["slash_glow"]}" '
            f'stroke-width="3.5" stroke-linecap="round" opacity=".55"/>'
            f'<line x1="{x - 3}" y1="{y1}" x2="{x + CELL + 3}" y2="{y0}" stroke="{t["slash"]}" stroke-width="1.3" stroke-linecap="round"/></g>')
        css.append(f"""
  .s{c} {{ opacity: 0; animation: s{c} {DURATION}s linear infinite; }}
  @keyframes s{c} {{ 0%, {pct(p - 0.3)} {{ opacity: 0; }} {pct(p)} {{ opacity: 1; }} {pct(p + 1.6)}, 100% {{ opacity: 0; }} }}""")
        if has_cut:
            for cls, dx, dy, rot in ((cut_a, -3.5, -4.5, -18), (cut_b, 3.5, 4.5, 18)):
                css.append(f"""
  .{cls} {{ animation: {cls} {DURATION}s ease-out infinite; }}
  @keyframes {cls} {{
    0%, {pct(p)} {{ transform: none; opacity: 1; }}
    {pct(p + 3.5)} {{ transform: translate({dx}px, {dy}px) rotate({rot}deg); opacity: 0; }}
    {pct(REGROW_FROM)} {{ transform: translate({dx}px, {dy}px) rotate({rot}deg); opacity: 0; }}
    {pct(REGROW_TO)}, 100% {{ transform: none; opacity: 1; }}
  }}""")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<title>侍 Samurai cortando as contribuições</title>
<style>{''.join(css)}
</style>
<g>{''.join(base)}</g>
<g>{''.join(halves)}</g>
<g>{''.join(slashes)}</g>
<g transform="translate({width / 2:.1f},{TOP + (7 * STEP - GAP) / 2:.1f})"><path class="zan" d="{ZAN_PATH}" fill="{t['accent']}" stroke="{t['body']}" stroke-width="1.2" paint-order="stroke"/></g>
<g class="sam" transform="translate({x_first - 60},{feet_y})">{samurai_figure(t)}
</g>
</svg>"""

# ---------------------------------------------------------------- selo ---

HANKO_SVG = r'''<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
  <g transform="rotate(-4 60 60)">
    <rect x="10" y="8" width="100" height="104" rx="14" fill="#c8102e"/>
    <rect x="16" y="14" width="88" height="92" rx="9" fill="none" stroke="#f5efe3" stroke-width="3"/>
    <path d="M41.168000000000006 20.727999999999994 40.772000000000006 20.991999999999997C42.664 23.104 44.556000000000004 26.316 44.996 29.263999999999996C49.836 32.827999999999996 54.19200000000001 23.104 41.168000000000006 20.727999999999994ZM49.352000000000004 40.52799999999999C50.628 40.352 51.288000000000004 40.0 51.64 39.604L46.36 35.336L43.896 38.635999999999996H39.276L39.540000000000006 39.867999999999995H44.556000000000004V52.98C42.576 53.86 40.684000000000005 54.651999999999994 39.32 55.135999999999996L42.092000000000006 60.67999999999999C42.488 60.504 42.752 60.196 42.752 59.623999999999995C44.468 57.81999999999999 47.108000000000004 54.651999999999994 48.868 52.232C51.816 58.43599999999999 55.248000000000005 59.711999999999996 63.608000000000004 59.711999999999996C68.05199999999999 59.711999999999996 73.55199999999999 59.711999999999996 77.424 59.711999999999996C77.644 57.42399999999999 78.78800000000001 55.928 80.724 55.48799999999999V54.959999999999994C75.268 55.092 68.536 55.135999999999996 63.564 55.135999999999996C55.512 55.135999999999996 52.432 54.696 49.352000000000004 51.483999999999995ZM51.64 37.536 51.992000000000004 38.768H62.2V42.903999999999996H53.18L53.532000000000004 44.135999999999996H62.2V48.36H50.848L51.2 49.592H62.2V54.168H63.124C65.72 54.168 67.304 53.199999999999996 67.304 52.98V49.592H78.832C79.44800000000001 49.592 79.888 49.372 80.02000000000001 48.888C78.25999999999999 47.348 75.4 45.236 75.4 45.236L72.848 48.36H67.304V44.135999999999996H76.588C77.24799999999999 44.135999999999996 77.688 43.916 77.77600000000001 43.431999999999995C76.06 41.98 73.332 39.955999999999996 73.332 39.955999999999996L70.912 42.903999999999996H67.304V38.768H77.77600000000001C78.348 38.768 78.832 38.548 78.92 38.06399999999999C77.16 36.611999999999995 74.344 34.544 74.344 34.544L71.88 37.536H68.36C70.25200000000001 36.03999999999999 72.232 34.19199999999999 73.50800000000001 32.739999999999995C74.52000000000001 32.784 75.00399999999999 32.388 75.18 31.859999999999996L70.736 30.891999999999996H79.36C79.976 30.891999999999996 80.416 30.671999999999997 80.548 30.188C78.744 28.604 75.84 26.447999999999997 75.84 26.447999999999997L73.2 29.615999999999996H67.304V25.523999999999997H76.456C77.072 25.523999999999997 77.512 25.304 77.644 24.819999999999997C75.84 23.28 72.98 21.168 72.98 21.168L70.428 24.247999999999998H67.304V20.903999999999996C68.184 20.727999999999994 68.492 20.375999999999998 68.536 19.891999999999996L62.2 19.32V24.247999999999998H53.004000000000005L53.356 25.523999999999997H62.2V29.615999999999996H50.276L50.628 30.891999999999996H56.524C57.36 32.388 58.02 34.587999999999994 57.888000000000005 36.611999999999995C58.46 37.184 59.076 37.492 59.692 37.536ZM58.24 30.891999999999996H68.44800000000001C68.184 32.916 67.744 35.599999999999994 67.304 37.536H60.528000000000006C62.992000000000004 37.05199999999999 64.268 33.004 58.24 30.891999999999996Z" fill="#f5efe3"/>
    <path d="M60.616 63.674C61.76 63.498000000000005 62.111999999999995 63.102000000000004 62.199999999999996 62.442L54.983999999999995 61.738C54.94 75.73 55.379999999999995 89.898 39.275999999999996 101.646L39.76 102.262C56.215999999999994 94.386 59.428 83.122 60.263999999999996 71.902C61.364 85.894 64.664 96.234 75.708 102.042C76.324 99.182 77.996 97.378 80.67999999999999 96.894L80.72399999999999 96.366C65.67599999999999 90.822 61.53999999999999 80.57 60.616 63.674Z" fill="#f5efe3"/>
  </g>
</svg>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER"))
    ap.add_argument("--out", default="dist")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    if args.mock:
        grid = mock_weeks()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token or not args.user:
            raise SystemExit("Defina GITHUB_TOKEN e --user (ou use --mock).")
        grid = fetch_weeks(args.user, token)

    os.makedirs(args.out, exist_ok=True)
    for name, theme in (("samurai.svg", "light"), ("samurai-dark.svg", "dark")):
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            f.write(build_svg(grid, THEMES[theme]))
    with open(os.path.join(args.out, "hanko.svg"), "w", encoding="utf-8") as f:
        f.write(HANKO_SVG)
    print(f"Gerado em {args.out}/: samurai.svg, samurai-dark.svg, hanko.svg ({len(grid)} semanas)")


if __name__ == "__main__":
    main()
