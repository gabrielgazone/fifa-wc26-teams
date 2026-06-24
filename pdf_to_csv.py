# -*- coding: utf-8 -*-
"""Converte um relatório oficial PMSR (PDF da FIFA Training Centre) no CSV de
métricas físicas no mesmo formato dos arquivos do app.

Extrai EXATAMENTE (via PyMuPDF) as páginas "Physical Data" das duas seleções:
distância total, zonas 1–5, # Speed Runs, # Sprints e Top Speed.

Limitação honesta: o PDF NÃO traz os minutos jogados de forma recuperável
(não há tabela por-minuto; os minutos da súmula misturam gols/cartões/subs).
Por isso 'Total Duration (min)' fica em branco — as análises de TOTAL ABSOLUTO
(aba Torneio) funcionam 100%; as de intensidade (m/min) ficam indisponíveis
para esta partida até haver o CSV oficial com a duração.

Uso:
    python pdf_to_csv.py CAMINHO.pdf NN [PASTA_SAIDA]
onde NN é o número da partida (ex.: 29).
"""
import re
import sys
import zlib
import unicodedata

import fitz  # PyMuPDF

try:
    from positions_data import team_code, canon
except Exception:  # fallback se rodar fora da pasta
    def team_code(x):
        return str(x).strip().upper()[:3]

    def canon(x):
        return str(x).strip().upper()

HEADER = ("Competition Name;Match ID;Team Name;Player ID;Player Name;Jersey #;"
          "Total Duration (min);Total Distance (m);1-7 km/h (m);7-15 km/h (m);"
          "15-20 km/h (m);20-25 km/h (m);25+ km/h (m);Max Speed (km/h);"
          "# Speed Runs;# Sprints")

_NUM = re.compile(r"^-?\d+(\.\d+)?$")


def _strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _lines(pg):
    rows = {}
    for w in pg.get_text("words"):
        y = round(w[1] / 3) * 3
        rows.setdefault(y, []).append((w[0], w[4]))
    return [" ".join(t for _, t in sorted(v)) for _, v in sorted(rows.items())]


def _player_id(team, name):
    key = f"{canon(team)}|{_strip_accents(name).upper()}".encode("utf-8")
    return zlib.crc32(key) % 1_000_000  # ID estável entre partidas


def _eu(x):
    """Float -> texto com vírgula decimal (estilo dos CSV da FIFA)."""
    return str(x).replace(".", ",")


def parse_pmsr(pdf_path):
    doc = fitz.open(pdf_path)
    venue_date = None
    teams = []
    for i, pg in enumerate(doc):
        txt = pg.get_text()
        if "Physical Data" not in txt:
            continue
        ls = _lines(pg)
        phys_line = next((l for l in ls if "Physical Data" in l), "")
        team = phys_line.replace("Physical Data", "").strip()
        if not team:  # título e nome do time em linhas separadas
            idx = next((k for k, l in enumerate(ls) if "Physical Data" in l), 0)
            for l in ls[max(0, idx - 1):idx + 2]:
                cand = l.replace("Physical Data", "").strip()
                if cand and not any(ch.isdigit() for ch in cand):
                    team = cand
                    break
        players = []
        for line in ls:
            toks = line.split()
            if len(toks) >= 11 and toks[0].isdigit():
                nums = toks[-9:]
                if all(_NUM.match(n) for n in nums):
                    jersey = toks[0]
                    name = " ".join(toks[1:len(toks) - 9])
                    players.append((jersey, name, nums))
            if venue_date is None and "2026" in line and "-" in line:
                venue_date = line
        if players:
            teams.append((team, players))
    return teams, venue_date


def to_csv(pdf_path, match_no, out_dir="."):
    teams, venue_date = parse_pmsr(pdf_path)
    if len(teams) < 2:
        raise SystemExit("Não encontrei as duas páginas 'Physical Data'.")
    match_id = 900_000 + int(match_no)
    codes = [team_code(t[0]) for t in teams]

    # data (DDMMYYYY) a partir do rodapé "19 June 2026 - ..."
    months = {m: i for i, m in enumerate(
        ["January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"], 1)}
    ymd = "20260101"
    if venue_date:
        m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(2026)", venue_date)
        if m:
            ymd = f"{m.group(3)}{months.get(m.group(2),1):02d}{int(m.group(1)):02d}"

    rows = [HEADER]
    for team, players in teams:
        tname = team.upper()
        for jersey, name, nums in players:
            pid = _player_id(team, name)
            vals = ";".join(_eu(n) for n in nums[:6])  # dist + 5 zonas
            top = _eu(nums[6 + 2])  # Top Speed é o 9º número (índice 8)
            # ordem dos 9 números no PDF: dist, z1, z2, z3, z4, z5, HSR, Sprints, TopSpeed
            dist, z1, z2, z3, z4, z5, hsr, spr, top = nums
            row = ";".join([
                "WC2026", str(match_id), tname, str(pid), name.upper(), jersey,
                "",  # Total Duration (min) — indisponível no PDF
                _eu(dist), _eu(z1), _eu(z2), _eu(z3), _eu(z4), _eu(z5),
                _eu(top), hsr.split(".")[0], spr.split(".")[0],
            ])
            rows.append(row)

    fname = f"{ymd}_FWC_{int(match_no):02d}_{codes[0]}-{codes[1]}_FIFA_Player_Physical_Metrics_Data.csv"
    out = f"{out_dir.rstrip('/').rstrip(chr(92))}\\{fname}"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    return out, sum(len(p) for _, p in teams)


if __name__ == "__main__":
    pdf, no = sys.argv[1], sys.argv[2]
    out_dir = sys.argv[3] if len(sys.argv) > 3 else "."
    path, n = to_csv(pdf, no, out_dir)
    print(f"OK: {n} jogadores -> {path}")
