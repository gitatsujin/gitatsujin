#!/usr/bin/env python3
"""
Recolore no preto e vermelho do perfil os SVGs gerados (tema github-dark) pelo
Pac-Man Contribution Graph (github.com/abozanona/pacman-contribution-graph).

Uso: python3 scripts/recolorir_arcade.py entrada.svg saida.svg
"""
import re
import sys

MAPA = {
    # fundo e texto
    "#0d1117": "#0d1117",
    "#000000": "#0d1117",   # fundo do Galaga
    "#8b949e": "#8b949e",
    # dias de contribuição (vazio -> mais commits)
    "#161b22": "#1b2129",
    "#0e4429": "#4a0d14",
    "#006d32": "#7d111c",
    "#26a641": "#b3141f",
    "#39d353": "#ff2a2a",
    # paredes do labirinto do Pac-Man
    "#ffffff": "#e0262f",
    # bolhas verdes do Puzzle Bobble viram flores de sakura
    "#2ecc71": "#ff9dbb",
}

entrada, saida = sys.argv[1], sys.argv[2]
svg = open(entrada, encoding="utf-8").read()
padrao = re.compile("|".join(re.escape(c) for c in MAPA), re.IGNORECASE)
svg = padrao.sub(lambda m: MAPA[m.group(0).lower()], svg)
open(saida, "w", encoding="utf-8").write(svg)
print(f"Recolorido: {saida}")
