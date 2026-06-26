# -*- coding: utf-8 -*-
"""Extrai estatísticas TÉCNICO-TÁTICAS de nível de equipe da página
'Match Summary - Key Statistics' do relatório oficial PMSR da FIFA.

Retorna, por jogo: (timeA, timeB, data, {time: {stats}}).
Usa PyMuPDF (mesma extração exata do físico). Coluna esquerda = time A,
direita = time B; rótulo casado com os valores pela proximidade vertical.
"""
import re
import fitz

# rótulo (substring) -> (coluna, tem_valor_entre_parenteses)
LABELS = [
    ("Possession", "Posse (%)", False),
    ("xG", "xG", False),
    ("Attempts at Goal", "Finalizações", True),         # paren = no alvo
    ("Total Passes", "Passes", True),                    # paren = completos
    ("Pass Completion", "Acerto passe (%)", False),
    ("Completed Line Breaks", "Line breaks", False),
    ("Defensive Line Breaks", "Line breaks def.", False),
    ("Receptions in the Final Third", "Recep. terço final", False),
    ("Crosses", "Cruzamentos", False),
    ("Ball Progressions", "Progressões", False),
    ("Defensive Pressures Applied", "Pressões def.", False),
    ("Forced Turnovers", "Turnovers forçados", False),
    ("Second Balls", "Segundas bolas", False),
]

# fases de jogo (página "Phases of Play"): rótulo completo -> coluna (% do tempo)
PHASES = [
    ("Build Up Unopposed", "Construção livre (%)"),
    ("Build Up Opposed", "Construção pressionada (%)"),
    ("Progression", "Progressão fase (%)"),
    ("Final Third", "Ataque terço final (%)"),
    ("Long Ball", "Bola longa (%)"),
    ("Attacking Transition", "Transição ofensiva (%)"),
    ("Counter Attack", "Contra-ataque (%)"),
    ("Set Piece", "Bola parada (%)"),
    ("High Press", "Pressão alta (%)"),
    ("Mid Press", "Pressão média (%)"),
    ("Low Press", "Pressão baixa (%)"),
    ("High Block", "Bloco alto (%)"),
    ("Mid Block", "Bloco médio (%)"),
    ("Low Block", "Bloco baixo (%)"),
    ("Recovery", "Recuperação (%)"),
    ("Defensive Transition", "Transição defensiva (%)"),
    ("Counter-press", "Counter-press (%)"),
]


def all_columns():
    """Ordem das colunas técnicas (Key Stats + Fases)."""
    cols = []
    for _, col, hasp in LABELS:
        cols.append(col)
        if hasp:
            cols.append(f"{col} (no alvo)" if "Final" in col else f"{col} (completos)")
    cols += [c for _, c in PHASES]
    return cols


_PAREN = re.compile(r"\(([\d.]+)\)")
_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _rows(pg):
    d = {}
    for w in pg.get_text("words"):
        y = round(w[1] / 3) * 3
        d.setdefault(y, []).append((w[0], w[4]))
    return {y: sorted(v) for y, v in d.items()}


def _side(tokens, lo, hi):
    return " ".join(t for x, t in tokens if lo <= x < hi)


def _main(s):
    s = _PAREN.sub("", s)           # remove parênteses
    m = _NUM.findall(s)
    return float(m[0]) if m else None


def _paren(s):
    m = _PAREN.findall(s)
    return float(m[0]) if m else None


def parse_pmsr_tech(pdf_path):
    doc = fitz.open(pdf_path)

    # times + data: reaproveita a extração robusta do conversor físico
    from pdf_to_csv import parse_pmsr
    tp, venue = parse_pmsr(pdf_path)
    teams = [t[0] for t in tp][:2]

    # página Key Statistics
    ks = next((i for i, pg in enumerate(doc) if "Key Statistics" in pg.get_text()), None)
    if ks is None or len(teams) < 2:
        return None
    rows = _rows(doc[ks])

    # linhas de valor (números na esq. e dir.) e linhas de rótulo
    val_rows, lab_rows = [], []
    for y, toks in rows.items():
        a, b = _side(toks, 0, 380), _side(toks, 580, 960)
        center = _side(toks, 300, 660)
        if _NUM.search(a) and _NUM.search(b):
            val_rows.append((y, a, b))
        # rótulo: algum texto no centro com letras
        if any(ch.isalpha() for ch in center):
            lab_rows.append((y, center))

    statsA, statsB = {}, {}
    for key, col, has_paren in LABELS:
        lab = next((l for l in lab_rows if key.lower() in l[1].lower()), None)
        if not lab:
            continue
        ly = lab[0]
        vr = min(val_rows, key=lambda r: abs(r[0] - ly), default=None)
        if not vr or abs(vr[0] - ly) > 22:
            continue
        _, a, b = vr
        statsA[col] = _main(a)
        statsB[col] = _main(b)
        if has_paren:
            pa, pb = _paren(a), _paren(b)
            sub = "no alvo" if "Final" in col else "completos"
            statsA[f"{col} ({sub})"] = pa
            statsB[f"{col} ({sub})"] = pb

    # fases de jogo (página "Phases of Play"): rótulo e valores na MESMA linha
    pi = next((i for i, pg in enumerate(doc) if "Phases of Play" in pg.get_text()), None)
    if pi is not None:
        for y, toks in _rows(doc[pi]).items():
            left = _side(toks, 0, 420)
            right = _side(toks, 560, 960)
            center = _side(toks, 420, 560)
            if "%" not in left or "%" not in right:
                continue
            for key, col in PHASES:
                if key.lower() in center.lower():
                    statsA[col] = _main(left)
                    statsB[col] = _main(right)
                    break

    return teams[0], teams[1], venue, {teams[0]: statsA, teams[1]: statsB}


if __name__ == "__main__":
    import sys
    r = parse_pmsr_tech(sys.argv[1])
    if r:
        a, b, v, st = r
        print(f"{a} x {b}  ({v})")
        for k in st[a]:
            print(f"  {k:24} {st[a][k]}  |  {st[b][k]}")
