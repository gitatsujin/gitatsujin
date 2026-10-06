#!/usr/bin/env python3
"""
Deixa o ciclo de um jogo do Commit Arcade mais longo, desacelerando por igual
tudo o que segue o relógio principal do jogo (as animações decorativas, como
estrelas piscando, continuam no ritmo normal).

Com poucos commits uma partida dura poucos segundos; isto garante um ciclo
mínimo sem deixar o jogo lento demais.

Uso: python3 scripts/alongar_ciclo.py arquivo.svg [ciclo_minimo=30] [fator_maximo=2.5]
"""
import re
import sys
from collections import Counter

path = sys.argv[1]
minimo = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
fator_max = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5

svg = open(path, encoding="utf-8").read()
decl = re.compile(r"animation:([A-Za-z_][\w-]*) ([\d.]+)s([^;}\"]*)")
duracoes = Counter(m.group(2) for m in decl.finditer(svg))
if not duracoes:
    raise SystemExit("Nenhuma animação encontrada.")
T_txt, _ = duracoes.most_common(1)[0]          # relógio principal do jogo
T = float(T_txt)
k = max(1.0, min(fator_max, minimo / T))


def fmt(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


def ajustar(m):
    nome, dur, resto = m.groups()
    if dur != T_txt or k == 1.0:
        return m.group(0)
    resto = re.sub(r"(-?[\d.]+)s", lambda d: fmt(float(d.group(1)) * k) + "s", resto)
    return f"animation:{nome} {fmt(T * k)}s{resto}"


svg = decl.sub(ajustar, svg)
open(path, "w", encoding="utf-8").write(svg)
print(f"Ciclo: {T:.1f}s -> {T * k:.1f}s (x{k:.2f})")
