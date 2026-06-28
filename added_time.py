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
    # URU 0–1 ESP · rodada 3 · 1ºT +8 (2:19 +8) · 2ºT +5 (3:17 +5) → 103 min
    _key("Uruguay", "Spain"): (8, 5),
    # NZL 1–4 BEL · rodada 3 · 1ºT +6 (3:55 +6) · 2ºT +4 (0:40 +4) → 100 min
    _key("New Zealand", "Belgium"): (6, 4),
    # EGY 1–1 IRN · rodada 3 · 1ºT +5 (0:22 +5) · 2ºT +6 (1:22 +6) → 101 min
    _key("Egypt", "IR Iran"): (5, 6),
    # CPV 0–0 KSA · rodada 3 · 1ºT +6 (0:48 +6) · 2ºT +5 (1:52 +5) → 101 min
    _key("Cabo Verde", "Saudi Arabia"): (6, 5),
    # PAN 0–2 ENG · rodada 3 · 1ºT +3 (2:40 +3) · 2ºT +6 (5:58 +6) → 99 min
    _key("Panama", "England"): (3, 6),
    # COL 0–0 POR · rodada 3 · 1ºT +3 (3:01 +3) · 2ºT +5 (4:40 +5) → 98 min
    _key("Colombia", "Portugal"): (3, 5),
    # CRO 2–1 GHA · rodada 3 · 1ºT +3 (3:03 +3) · 2ºT +7 (6:50 +7) → 100 min
    _key("Croatia", "Ghana"): (3, 7),
    # ALG 3–3 AUT · rodada 3 · 1ºT +4 (4:05 +4) · 2ºT +4 (6:29 +4) → 98 min
    _key("Algeria", "Austria"): (4, 4),
    # JOR 1–3 ARG · rodada 3 · 1ºT +5 (4:57 +5) · 2ºT +5 (5:00 +5) → 100 min
    _key("Jordan", "Argentina"): (5, 5),
    # COD 3–1 UZB · rodada 3 · 1ºT +7 (6:59 +7) · 2ºT +8 (8:02 +8) → 105 min
    _key("Congo DR", "Uzbekistan"): (7, 8),
}


def added_time_for(team_a, team_b):
    """(acréscimo 1ºT, acréscimo 2ºT) em minutos, ou None se não registrado."""
    return ADDED_TIME.get(_key(team_a, team_b))


def total_minutes(team_a, team_b):
    """Duração de um jogo completo (90 + acréscimos), ou None."""
    at = added_time_for(team_a, team_b)
    return 90 + at[0] + at[1] if at else None
