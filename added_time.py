# -*- coding: utf-8 -*-
"""Acréscimos OFICIAIS por tempo, lidos do relógio do 4º árbitro na transmissão
e ARMAZENADOS pelo usuário. Nunca inferidos/estimados.

Chave = par de seleções canônico ('A|B' ordenado, via canon()).
Valor  = (acréscimo do 1º tempo, acréscimo do 2º tempo) em minutos inteiros.

Uso no cálculo da duração real por jogador:
    H1 = 45 + a1 ;  H2 = 45 + a2 ;  jogo completo = H1 + H2
(jogadores substituídos/que entraram recebem a fração correspondente).
"""
from positions_data import canon


def _key(a, b):
    return "|".join(sorted([canon(a), canon(b)]))


# (a1, a2) — acréscimos do 1º e do 2º tempo
ADDED_TIME = {
    # NOR 1–4 FRA · rodada 3 · 1ºT +5 (relógio 2:20 +5) · 2ºT +5 (4:46 +5) → 100 min
    _key("Norway", "France"): (5, 5),
    # SEN 5–0 IRQ · rodada 3 · 1ºT +9 (relógio 0:30 +9) · 2ºT +6 (2:11 +6) → 105 min
    _key("Senegal", "Iraq"): (9, 6),
}


def added_time_for(team_a, team_b):
    """(acréscimo 1ºT, acréscimo 2ºT) em minutos, ou None se não registrado."""
    return ADDED_TIME.get(_key(team_a, team_b))


def total_minutes(team_a, team_b):
    """Duração de um jogo completo (90 + acréscimos), ou None."""
    at = added_time_for(team_a, team_b)
    return 90 + at[0] + at[1] if at else None
