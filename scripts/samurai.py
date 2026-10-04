#!/usr/bin/env python3
"""
侍 Samurai Contributions — gera um SVG animado em que um samurai corre pelo
gráfico de contribuições do GitHub e corta cada quadradinho com a katana.
No fim, um ensō (círculo zen) se desenha em volta do kanji 斬 ("corte")
e o gráfico renasce.

Uso:
  GITHUB_TOKEN=... python samurai.py --user gitatsujin --out dist
  python samurai.py --mock --out dist        # dados de exemplo (teste local)

Gera: samurai.svg (tema claro) e samurai-dark.svg (tema escuro).
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


def mock_weeks(seed=42, density=0.55):
    rnd = random.Random(seed)
    grid = []
    for c in range(53):
        col = []
        for r in range(7):
            if c == 52 and r > 3:
                col.append(None)
                continue
            if rnd.random() > density:
                col.append(0)
            else:
                col.append(rnd.choice([1, 1, 2, 2, 3, 4]))
        grid.append(col)
    return grid

# ---------------------------------------------------------------- temas ---

THEMES = {
    "dark": {
        "levels": ["#1b2129", "#3d0c11", "#6e1018", "#a3111f", "#e0262f"],
        "ghost": "#10141a", "body": "#f5efe3", "shade": "#cfc6b5", "accent": "#e0262f",
        "blade": "#e6edf3", "saya": "#8b8b8b", "eye": "#0d0d0d", "gold": "#d4a017",
        "slash": "#ffffff", "glow": "#ff4d4d", "petal": "#ffb7c5", "ink": "#8f1018",
        "speed": "#f5efe3",
    },
    "light": {
        "levels": ["#e3e6ea", "#f6c9c4", "#ec8a80", "#d94a3d", "#a8141f"],
        "ghost": "#f3f4f6", "body": "#1b1b1b", "shade": "#3d3d3d", "accent": "#c8102e",
        "blade": "#6b7280", "saya": "#6b6b6b", "eye": "#f5efe3", "gold": "#b8860b",
        "slash": "#c8102e", "glow": "#ff8a80", "petal": "#f48fb1", "ink": "#1b1b1b",
        "speed": "#1b1b1b",
    },
}

# ------------------------------------------------------------ geometria ---

CELL, GAP = 11, 3
STEP = CELL + GAP
PAD_X, TOP, PAD_B = 22, 106, 16
SCALE = 1.45
DURATION = 20.0                       # segundos por ciclo completo
RUN_START, RUN_END = 4.0, 78.0        # % do ciclo em que o samurai corre
ENSO_FROM, ENSO_TO = 79.5, 84.5
REGROW_FROM, REGROW_TO = 92.0, 97.0
ZAN_PATH = "M-35.2 -17.0V13.8H-34.0C-30.880000000000003 13.8 -27.6 12.04 -27.6 11.32V9.559999999999999H-23.84V18.84H-38.08L-37.44 21.159999999999997H-23.84V37.4H-22.24C-17.68 37.4 -14.96 35.56 -14.96 35.0V21.159999999999997H-0.3200000000000003L0.1600000000000037 21.08C-1.2800000000000011 26.759999999999998 -3.6799999999999997 31.96 -7.600000000000001 36.68L-6.719999999999999 37.56C9.840000000000003 27.56 11.04 12.04 11.04 -1.6400000000000006V-5.880000000000003H18.96V37.48H20.64C25.440000000000005 37.48 28.160000000000004 35.8 28.240000000000002 35.32V-5.880000000000003H35.839999999999996C36.96 -5.880000000000003 37.839999999999996 -6.280000000000001 38.080000000000005 -7.160000000000004C34.720000000000006 -10.280000000000001 29.119999999999997 -14.759999999999998 29.119999999999997 -14.759999999999998L24.240000000000002 -8.200000000000003H11.04V-24.520000000000003C18.4 -25.4 26.240000000000002 -27.0 31.199999999999996 -28.440000000000005C33.839999999999996 -27.800000000000004 35.52 -28.04 36.4 -28.840000000000003L25.199999999999996 -37.480000000000004C22.240000000000002 -34.44 16.64 -29.96 11.439999999999998 -26.68L2.240000000000002 -29.64V-1.7199999999999989C2.240000000000002 5.32 2.0 12.279999999999998 0.6400000000000006 18.84C-2.479999999999997 16.119999999999997 -6.640000000000001 12.919999999999998 -6.640000000000001 12.919999999999998L-11.280000000000001 18.84H-14.96V9.559999999999999H-11.280000000000001V12.52H-10.0C-7.280000000000001 12.52 -3.4399999999999977 10.759999999999998 -3.3599999999999994 10.119999999999997V-13.64C-1.9200000000000017 -13.96 -0.8800000000000026 -14.600000000000001 -0.3999999999999986 -15.079999999999998L-8.32 -21.08L-12.0 -17.0H-14.96V-24.04H-1.6000000000000014C-0.4799999999999969 -24.04 0.3200000000000003 -24.440000000000005 0.5600000000000023 -25.32C-2.479999999999997 -28.120000000000005 -7.600000000000001 -32.36 -7.600000000000001 -32.36L-12.079999999999998 -26.28H-14.96V-34.519999999999996C-13.04 -34.760000000000005 -12.48 -35.56 -12.32 -36.60000000000001L-23.84 -37.56V-26.28H-37.52L-36.88 -24.04H-23.84V-17.0H-27.2L-35.2 -20.36ZM-23.2 -3.0799999999999983V7.239999999999998H-27.6V-3.0799999999999983ZM-15.52 -3.0799999999999983H-11.280000000000001V7.239999999999998H-15.52ZM-23.2 -5.32H-27.6V-14.759999999999998H-23.2ZM-15.52 -5.32V-14.759999999999998H-11.280000000000001V-5.32Z"                  # kanji 斬 em vetor, centrado em (0,0)


def pct(x):
    return f"{x:.3f}%"


def samurai_figure(t):
    """Samurai original, virado para a direita, com os pés em (0,0)."""
    b, s, a, k, g = t["body"], t["shade"], t["accent"], t["blade"], t["gold"]
    leg = ('<path d="M-3.2,-16 L3.2,-16 L4.6,-1.2 L-4.6,-1.2 Z"/>'
           '<path d="M-4.6,-1.4 L6,-1.4 L6,0.6 L-4.6,0.6 Z"/>')
    blade = "M16.3,-27.9 Q31,-31.5 47,-42"
    return f"""
    <g class="speed" stroke="{t['speed']}" stroke-width="1.3" stroke-linecap="round">
      <line x1="-24" y1="-31" x2="-40" y2="-31"/><line x1="-26" y1="-20" x2="-48" y2="-20"/><line x1="-23" y1="-9" x2="-37" y2="-9"/>
    </g>
    <g class="legB" fill="{s}">{leg}</g>
    <path class="sleeve" d="M-5.5,-31 Q-15,-30 -20,-22.5 Q-13,-25.5 -6.5,-25 Z" fill="{s}"/>
    <line x1="-3" y1="-21.5" x2="-20" y2="-15.2" stroke="{t['saya']}" stroke-width="2.2" stroke-linecap="round"/>
    <circle cx="-20.3" cy="-15.1" r="1.2" fill="{g}"/>
    <g class="legF" fill="{b}">{leg}</g>
    <path d="M-7,-21 L7,-21 L8.6,-11.5 L-8.6,-11.5 Z" fill="{b}"/>
    <path d="M-2.5,-21 L-3.2,-11.5 M2.5,-21 L3.2,-11.5" stroke="{s}" stroke-width=".6"/>
    <path d="M-6.2,-32 L6.2,-32 L7.6,-20 L-7.6,-20 Z" fill="{b}"/>
    <path d="M-4.2,-32 L0,-26 L4.2,-32" fill="none" stroke="{a}" stroke-width="1.3"/>
    <rect x="-8" y="-22.4" width="16" height="2.8" rx="1" fill="{a}"/>
    <g class="band" fill="{a}">
      <path d="M-5,-38.8 Q-13,-38.4 -21,-34.5 L-20,-37 Q-13,-40.3 -5,-40.3 Z"/>
      <path d="M-5,-38.6 Q-12,-36.5 -17.5,-31.5 L-18.2,-34 Q-12,-38 -5,-39.6 Z" opacity=".8"/>
    </g>
    <circle cx="0.5" cy="-37" r="5.4" fill="{b}"/>
    <ellipse cx="-2.4" cy="-43.1" rx="3.4" ry="1.6" fill="{b}"/>
    <rect x="-5.1" y="-39.8" width="11" height="2.1" rx=".8" fill="{a}"/>
    <line x1="2.4" y1="-36.6" x2="4.8" y2="-37" stroke="{t['eye']}" stroke-width="1" stroke-linecap="round"/>
    <g class="sword">
      <path d="M0.5,-31 L10,-26.6 L9,-23.8 L-0.5,-28 Z" fill="{b}"/>
      <circle cx="10.2" cy="-25.2" r="1.6" fill="{b}"/>
      <line x1="9.5" y1="-25.4" x2="15" y2="-27.4" stroke="{a}" stroke-width="2.6" stroke-linecap="round"/>
      <ellipse cx="15.7" cy="-27.6" rx=".9" ry="2.2" fill="{g}" transform="rotate(-20 15.7 -27.6)"/>
      <path d="{blade}" fill="none" stroke="{k}" stroke-width="1.9" stroke-linecap="round"/>
      <path class="glint" d="{blade}" pathLength="100" fill="none" stroke="#ffffff" stroke-width="1.9" stroke-linecap="round"/>
      <path class="arc" d="M42,-47 Q58,-26 40,-4 Q53,-26 42,-47 Z" fill="{t['slash']}"/>
    </g>"""


def build_svg(grid, t):
    cols = len(grid)
    width = PAD_X * 2 + cols * STEP - GAP
    grid_h = 7 * STEP - GAP
    height = TOP + grid_h + PAD_B
    run = RUN_END - RUN_START
    col_time = DURATION * run / 100 / cols
    feet_y = TOP - 7
    off = -52                                    # katana alcança a coluna
    x_first = PAD_X + CELL / 2 + off
    x_last = PAD_X + (cols - 1) * STEP + CELL / 2 + off
    rnd = random.Random(7)
    cx, cy = width / 2, TOP + grid_h / 2

    def tr(x):
        return f"translate({x:.1f}px, {feet_y}px) scale({SCALE})"

    css = [f"""
  .sam {{ animation: run {DURATION}s linear infinite; }}
  .sam .sword {{ transform-origin: 2px -29.5px; animation: swing {col_time:.4f}s cubic-bezier(.5,0,.9,.6) infinite; }}
  .sam .arc {{ opacity: 0; animation: arc {col_time:.4f}s linear infinite; }}
  .sam .glint {{ stroke-dasharray: 7 140; animation: glint {col_time * 2:.4f}s linear infinite; }}
  .sam .legF {{ transform-origin: 0px -16px; animation: stride {col_time * 2:.4f}s ease-in-out infinite; }}
  .sam .legB {{ transform-origin: 0px -16px; animation: stride {col_time * 2:.4f}s ease-in-out infinite reverse; }}
  .sam .band {{ transform-origin: -5px -39px; animation: flutter {col_time:.4f}s ease-in-out infinite; }}
  .sam .sleeve {{ transform-origin: -6px -28px; animation: flutter {col_time * 1.3:.4f}s ease-in-out infinite; }}
  .sam .speed {{ animation: speed {col_time:.4f}s linear infinite; }}
  .half {{ transform-box: fill-box; transform-origin: center; }}
  .trail {{ stroke-dasharray: 100; stroke-dashoffset: 100; animation: trail {DURATION}s linear infinite; }}
  .enso {{ stroke-dasharray: 100; stroke-dashoffset: 100; animation: enso {DURATION}s ease-out infinite; }}
  .enso2 {{ stroke-dasharray: 100; stroke-dashoffset: 100; animation: enso2 {DURATION}s ease-out infinite; }}
  .zan {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: zan {DURATION}s ease-out infinite; }}
  @keyframes run {{
    0% {{ transform: {tr(x_first - 70)}; opacity: 0; }}
    1% {{ opacity: 1; }}
    {pct(RUN_START)} {{ transform: {tr(x_first)}; }}
    {pct(RUN_END)} {{ transform: {tr(x_last)}; opacity: 1; }}
    {pct(RUN_END + 3)} {{ transform: {tr(x_last + 80)}; opacity: 0; }}
    100% {{ transform: {tr(x_last + 80)}; opacity: 0; }}
  }}
  @keyframes swing {{ 0% {{ transform: rotate(-62deg); }} 38% {{ transform: rotate(42deg); }} 100% {{ transform: rotate(-62deg); }} }}
  @keyframes arc {{ 0%, 18% {{ opacity: 0; }} 30% {{ opacity: .85; }} 48%, 100% {{ opacity: 0; }} }}
  @keyframes glint {{ from {{ stroke-dashoffset: 110; }} to {{ stroke-dashoffset: -10; }} }}
  @keyframes stride {{ 0%, 100% {{ transform: rotate(-28deg); }} 50% {{ transform: rotate(28deg); }} }}
  @keyframes flutter {{ 0%, 100% {{ transform: rotate(0deg); }} 50% {{ transform: rotate(-12deg); }} }}
  @keyframes speed {{ 0% {{ opacity: .1; transform: translateX(6px); }} 50% {{ opacity: .7; }} 100% {{ opacity: .1; transform: translateX(-8px); }} }}
  @keyframes trail {{ 0%, {pct(RUN_START)} {{ stroke-dashoffset: 100; opacity: .8; }}
    {pct(RUN_END)} {{ stroke-dashoffset: 0; opacity: .8; }}
    {pct(REGROW_FROM)} {{ stroke-dashoffset: 0; opacity: .8; }}
    {pct(REGROW_TO)}, 100% {{ stroke-dashoffset: 0; opacity: 0; }} }}
  @keyframes enso {{ 0%, {pct(ENSO_FROM)} {{ stroke-dashoffset: 100; opacity: 1; }}
    {pct(ENSO_TO)} {{ stroke-dashoffset: 9; opacity: 1; }}
    {pct(REGROW_FROM)} {{ stroke-dashoffset: 9; opacity: 1; }}
    {pct(REGROW_TO)}, 100% {{ stroke-dashoffset: 9; opacity: 0; }} }}
  @keyframes enso2 {{ 0%, {pct(ENSO_FROM + 1)} {{ stroke-dashoffset: 100; opacity: .45; }}
    {pct(ENSO_TO + 1)} {{ stroke-dashoffset: 30; opacity: .45; }}
    {pct(REGROW_FROM)} {{ stroke-dashoffset: 30; opacity: .45; }}
    {pct(REGROW_TO)}, 100% {{ stroke-dashoffset: 30; opacity: 0; }} }}
  @keyframes zan {{ 0%, {pct(ENSO_FROM + 2)} {{ opacity: 0; transform: scale(1.5); }}
    {pct(ENSO_TO + 1)} {{ opacity: 1; transform: scale(1); }}
    {pct(REGROW_FROM)} {{ opacity: 1; transform: scale(1); }}
    {pct(REGROW_TO)}, 100% {{ opacity: 0; transform: scale(1); }} }}"""]

    ghosts, halves, slashes, petals = [], [], [], []
    y0, y1 = TOP - 5, TOP + grid_h + 3
    for c, col in enumerate(grid):
        x = PAD_X + c * STEP
        p = RUN_START + run * (c + 0.5) / cols
        rows = [r for r, lvl in enumerate(col) if lvl is not None]
        for r in rows:
            y = TOP + r * STEP
            color = t["levels"][col[r]]
            ghosts.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.2" fill="{t["ghost"]}"/>')
            halves.append(f'<path class="half a{c}" d="M{x},{y + CELL} L{x},{y + 2.2} Q{x},{y} {x + 2.2},{y} L{x + CELL},{y} Z" fill="{color}"/>')
            halves.append(f'<path class="half b{c}" d="M{x},{y + CELL} L{x + CELL},{y} L{x + CELL},{y + CELL - 2.2} Q{x + CELL},{y + CELL} {x + CELL - 2.2},{y + CELL} Z" fill="{color}"/>')
        # corte em forma de pincelada (meia-lua fina)
        xa, xb = x - 5, x + CELL + 5
        xm, ym = (xa + xb) / 2, (y0 + y1) / 2
        slashes.append(
            f'<g class="s{c}">'
            f'<path d="M{xa},{y1} Q{xm - 3},{ym} {xb},{y0} Q{xm + 3},{ym + 3} {xa},{y1} Z" fill="{t["glow"]}" opacity=".6"/>'
            f'<path d="M{xa},{y1} Q{xm - 1.5},{ym} {xb},{y0} Q{xm + 1.2},{ym + 1.2} {xa},{y1} Z" fill="{t["slash"]}"/></g>')
        css.append(f"""
  .s{c} {{ opacity: 0; animation: s{c} {DURATION}s linear infinite; }}
  @keyframes s{c} {{ 0%, {pct(p - 0.25)} {{ opacity: 0; }} {pct(p)} {{ opacity: 1; }} {pct(p + 1.4)}, 100% {{ opacity: 0; }} }}""")
        for cls, dx, dy, rot in ((f"a{c}", -5, -6, -24), (f"b{c}", 5, 6, 24)):
            css.append(f"""
  .{cls} {{ animation: {cls} {DURATION}s ease-out infinite; }}
  @keyframes {cls} {{
    0%, {pct(p)} {{ transform: none; opacity: 1; }}
    {pct(p + 4)} {{ transform: translate({dx}px, {dy}px) rotate({rot}deg); opacity: 0; }}
    {pct(REGROW_FROM)} {{ transform: translate({dx}px, {dy}px) rotate({rot}deg); opacity: 0; }}
    {pct(REGROW_TO)}, 100% {{ transform: none; opacity: 1; }}
  }}""")
        # pétala de sakura que voa do corte (uma a cada duas colunas)
        if rows and c % 2 == 0:
            r = rnd.choice(rows)
            px, py = x + CELL / 2, TOP + r * STEP + CELL / 2
            dx, dy, rot = rnd.uniform(18, 34), rnd.uniform(20, 40), rnd.choice([-1, 1]) * rnd.uniform(160, 300)
            petals.append(f'<g transform="translate({px},{py})"><path class="pt{c}" d="M0,-3.2 C2.4,-3.4 3.4,-0.8 0,3.2 C-3.4,-0.8 -2.4,-3.4 0,-3.2 Z" fill="{t["petal"]}"/></g>')
            css.append(f"""
  .pt{c} {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: pt{c} {DURATION}s ease-out infinite; }}
  @keyframes pt{c} {{ 0%, {pct(p)} {{ opacity: 0; transform: none; }} {pct(p + 0.5)} {{ opacity: 1; }}
    {pct(p + 8)}, 100% {{ opacity: 0; transform: translate({dx:.1f}px, {dy:.1f}px) rotate({rot:.0f}deg); }} }}""")

    x_trail0 = PAD_X - 4
    x_trail1 = PAD_X + cols * STEP
    trail = (f'<path class="trail" pathLength="100" d="M{x_trail0},{feet_y + 1.5} '
             f'C{x_trail0 + 200},{feet_y + 3} {x_trail1 - 300},{feet_y - 0.5} {x_trail1},{feet_y + 1.8}" '
             f'fill="none" stroke="{t["ink"]}" stroke-width="2.4" stroke-linecap="round"/>')
    r_enso = grid_h / 2 + 8
    finale = f"""
<g transform="translate({cx:.1f},{cy:.1f}) rotate(-105)">
  <circle class="enso" r="{r_enso:.1f}" pathLength="100" fill="none" stroke="{t['accent']}" stroke-width="6.5" stroke-linecap="round"/>
  <circle class="enso2" r="{r_enso + 4:.1f}" pathLength="100" fill="none" stroke="{t['accent']}" stroke-width="1.6" stroke-linecap="round"/>
</g>
<g transform="translate({cx:.1f},{cy:.1f}) scale(.72)"><path class="zan" d="{ZAN_PATH}" fill="{t['body']}"/></g>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<title>侍 Samurai cortando as contribuições</title>
<style>{''.join(css)}
</style>
<g>{''.join(ghosts)}</g>
<g>{''.join(halves)}</g>
<g>{''.join(petals)}</g>
<g>{''.join(slashes)}</g>
{trail}{finale}
<g class="sam" transform="translate({x_first - 70},{feet_y}) scale({SCALE})">{samurai_figure(t)}
</g>
</svg>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER"))
    ap.add_argument("--out", default="dist")
    ap.add_argument("--mock", action="store_true", help="usa dados de exemplo")
    ap.add_argument("--mock-density", type=float, default=0.55)
    args = ap.parse_args()

    if args.mock:
        grid = mock_weeks(density=args.mock_density)
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token or not args.user:
            raise SystemExit("Defina GITHUB_TOKEN e --user (ou use --mock).")
        grid = fetch_weeks(args.user, token)

    os.makedirs(args.out, exist_ok=True)
    for name, theme in (("samurai.svg", "light"), ("samurai-dark.svg", "dark")):
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            f.write(build_svg(grid, THEMES[theme]))
    print(f"Gerado em {args.out}/: samurai.svg e samurai-dark.svg ({len(grid)} semanas)")


if __name__ == "__main__":
    main()
