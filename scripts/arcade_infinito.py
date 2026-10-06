#!/usr/bin/env python3
"""
Ajusta o Commit Arcade (github.com/Nicsilver/commit-arcade, licença MIT) para o
rodízio do perfil ficar "infinito", no estilo do Pac-Man de ciclo contínuo:

  1. remove a tela de "STAGE CLEAR" do fim de cada partida;
  2. remove as pausas entre partidas: o gráfico volta com um fade suave e o
     jogo recomeça na hora, sem um momento de "fim".

Uso: python3 scripts/arcade_infinito.py <pasta-do-commit-arcade>
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])

# 1) ritmo contínuo entre as partidas
game = root / "src" / "game.ts"
src = game.read_text()
new = re.sub(r"export const PACE = \{.*?\} as const;",
             "export const PACE = {\n  intro: 0.3,\n  hold: 0.0,\n  restore: 0.9,\n  rest: 0.0,\n} as const;",
             src, count=1, flags=re.S)
if new == src:
    raise SystemExit("Não encontrei PACE em src/game.ts — o Commit Arcade mudou?")
game.write_text(new)

# 2) sem a tela de STAGE CLEAR
kit = root / "src" / "kit.ts"
src = kit.read_text()
sig = "export function banner(tl: Timeline, opts: BannerOptions): string {"
if sig not in src:
    raise SystemExit("Não encontrei banner() em src/kit.ts — o Commit Arcade mudou?")
kit.write_text(src.replace(sig, sig + '\n  if (tl) return "";', 1))

# 3) Pac-Man: sem o pisca-pisca de "fase completa" no labirinto
pac = root / "src" / "games" / "pacman.ts"
src = pac.read_text()
if "const MAZE_FLASH_BEATS = 4;" not in src:
    raise SystemExit("Não encontrei MAZE_FLASH_BEATS em pacman.ts — o Commit Arcade mudou?")
src = src.replace("const MAZE_FLASH_BEATS = 4;", "const MAZE_FLASH_BEATS = 0;", 1)
pulse = "const pulse = mixColors(theme.empty, FRIGHT_BLUE, dark ? 0.2 : 0.12);"
if pulse in src:                       # chão sem o brilho azul de fim de fase
    src = src.replace(pulse, "const pulse = theme.empty;", 1)
ready = """    [0, "opacity:1"],
    [PACE.intro - 0.05, "opacity:1"],
    [PACE.intro + 0.15, "opacity:0"],
    [duration - 0.3, "opacity:0"],
    [duration, "opacity:1"],"""
if ready in src:                       # sem o "READY!" a cada recomeço
    src = src.replace(ready, """    [0, "opacity:0"],
    [duration, "opacity:0"],""", 1)
pac.write_text(src)

print("Commit Arcade ajustado: sem STAGE CLEAR e com recomeço contínuo.")
