# -*- coding: utf-8 -*-
"""Calcula os MINUTOS jogados por atleta a partir de fontes OFICIAIS, sem inferir:

  • substituições  -> página 2 do PMSR ("Match Summary - Teams"): cada reserva
    que entrou traz o minuto de entrada; cada titular substituído traz o minuto
    de saída. Minutos de gol/cartão aparecem junto — são descartados pelo
    PAREAMENTO (a saída de um titular casa com a entrada de um reserva).
  • acréscimos por tempo -> added_time.py (relógio do 4º árbitro).

Trava de segurança: só preenche o CSV se AMBOS os times passarem na validação
estrutural (11 titulares, nº de entradas = nº de saídas, todas pareadas, e o
total de minutos = 11 × duração da partida). Caso contrário, NÃO grava — o
usuário não aceita minutos inferidos/aproximados.

Uso:
    python pmsr_minutes.py PARTIDA.pdf                 # só mostra (dry-run)
    python pmsr_minutes.py PARTIDA.pdf "ARQUIVO.csv"   # valida e preenche
"""
import re
import sys
import fitz

from added_time import added_time_for
from positions_data import canon

MIN = re.compile(r"^(?:120\+\d+|105\+\d+|90\+\d+|45\+\d+|\d{1,3})'$")
POSRE = re.compile(r"^(GK|DF|MF|FW)(\d*)$")


def _reg(mtok):
    """Minuto para pareamento entrada/saída e duração.
    O acréscimo do 2º tempo é convertido para minuto CONTÍNUO (90+8 -> 98) — o
    PMSR mistura os dois formatos para o mesmo lance, e o contínuo casa e conta
    a parada. Acréscimos de 1ºT/ET (45+x, 105+x, 120+x) ficam na fronteira."""
    s = mtok.rstrip("'")
    if "+" in s:
        base, plus = s.split("+")
        return 90 + int(plus) if base == "90" else int(base)
    return int(s)


def _rows(pg):
    d = {}
    for w in pg.get_text("words"):
        y = round(w[1] / 2) * 2
        d.setdefault(y, []).append((round(w[0]), w[4]))
    return {y: sorted(v) for y, v in d.items()}


def _headers(R):
    h = {"A_start": None, "A_sub": None, "B_start": None, "B_sub": None}
    for y, toks in R.items():
        for x, t in toks:
            if t == "STARTING":
                k = "A_start" if x < 400 else "B_start"
                h[k] = y if h[k] is None else min(h[k], y)
            elif t == "SUBSTITUTES":
                k = "A_sub" if x < 400 else "B_sub"
                h[k] = y if h[k] is None else min(h[k], y)
    return h


def _players(R, side, y0, y1):
    """[(jersey, [min_reg...])] para o lado ('A' esq. / 'B' dir.) na faixa."""
    res = []
    for y in sorted(R):
        if not (y0 < y < y1):
            continue
        toks = R[y]
        jersey, mins = None, []
        for x, t in toks:
            m = POSRE.match(t)
            if side == "A":
                if x < 60 and t.isdigit():
                    jersey = t
                if 108 <= x < 300 and MIN.match(t):   # janela larga: nomes curtos
                    mins.append(_reg(t))               # empurram o minuto p/ esquerda
            else:
                if m and m.group(2):                 # pos+nº colado (ex.: FW10)
                    jersey = m.group(2)
                if 895 <= x <= 912 and t.isdigit():
                    jersey = t
                if 640 <= x < 832 and MIN.match(t):   # nomes longos jogam p/ direita
                    mins.append(_reg(t))
        if any(POSRE.match(t) for _, t in toks) and jersey:
            res.append((jersey, sorted(set(mins))))
    return res


def _team_minutes(starters, reserves, added):
    """added = (a1,a2) tempo normal OU (a1,a2,a3,a4) com prorrogação.
    -> (dict jersey->minutos, info de validação)."""
    bounds = [45, 90, 105, 120][:len(added)]          # fim de cada período (regulamento)
    T = bounds[-1] + sum(added)                        # duração total da partida
    # o acréscimo do ÚLTIMO período é a fase final (sem intervalo depois): só
    # conta para quem ficou em campo (full = T). Quem saiu no minuto exato da
    # troca antes desse período não o joga -> usa só as fronteiras de intervalo.
    breaks = bounds[:-1]

    def off_played(m):                                # minutos de quem saiu no minuto m
        # limitado a T: um sub no fim (ex.: "90+7" com acréscimo só de +6) não
        # pode exceder a duração — o que entra joga ~0, quem sai jogou ~tudo.
        return min(m + sum(a for a, bnd in zip(added, breaks) if m >= bnd), T)

    on = [(j, min(ms)) for j, ms in reserves if ms]   # reserva entrou no MENOR minuto
    pool = {j: list(ms) for j, ms in starters}
    off, unmatched = {}, []
    for _, m in sorted(on, key=lambda e: e[1]):
        cand = [j for j, ms in pool.items() if m in ms and j not in off]
        if cand:
            off[cand[0]] = m
            pool[cand[0]].remove(m)
        else:
            unmatched.append(m)
    mins = {j: round(off_played(off[j]) if j in off else T, 1) for j, _ in starters}
    for j, m in on:
        mins[j] = round(max(0.0, T - off_played(m)), 1)
    total = round(sum(mins.values()), 1)
    info = dict(on=on, off=off, unmatched=unmatched, nstart=len(starters),
                total=total, expected=round(11 * T, 1))
    info["ok"] = (info["nstart"] == 11 and not unmatched
                  and len(on) == len(off) and total == info["expected"])
    return mins, info


def compute(pdf_path, dnp=None):
    """-> ({canon(time): {jersey: minutos}}, {canon(time): info}) ou (None, None).
    dnp = {canon(time): {camisas}} — reservas com minuto FANTASMA que não jogaram
    (identificados por distância 0 no CSV); são removidos das substituições."""
    from pdf_to_csv import parse_pmsr
    doc = fitz.open(pdf_path)
    R = _rows(doc[1])
    h = _headers(R)
    tp, _ = parse_pmsr(pdf_path)
    tA, tB = tp[0][0], tp[1][0]
    at = added_time_for(tA, tB)
    if not at:
        return None, None
    dnp = dnp or {}
    out, status = {}, {}
    for nm, side in [(tA, "A"), (tB, "B")]:
        st = _players(R, side, h[side + "_start"], h[side + "_sub"])
        rv = _players(R, side, h[side + "_sub"], 99999)
        skip = dnp.get(canon(nm), set())
        rv = [(j, ms) for j, ms in rv if j not in skip]
        mins, info = _team_minutes(st, rv, tuple(at))
        out[canon(nm)], status[canon(nm)] = mins, info
    return out, status


def fill_csv(pdf_path, csv_path):
    """Valida e grava Total Duration no CSV. Levanta erro se não validar."""
    lines = open(csv_path, encoding="utf-8").read().splitlines()
    H = lines[0].split(";")
    ti, ji, di = H.index("Team Name"), H.index("Jersey #"), H.index("Total Duration (min)")
    disti = H.index("Total Distance (m)")
    # DNP: jogadores com distância 0 no CSV (não entraram) -> ignora subs fantasma
    dnp = {}
    for ln in lines[1:]:
        if not ln.strip():
            continue
        f = ln.split(";")
        try:
            zero = float(f[disti].replace(".", "").replace(",", ".")) == 0
        except ValueError:
            zero = False
        if zero:
            dnp.setdefault(canon(f[ti]), set()).add(f[ji].strip())

    mins, status = compute(pdf_path, dnp=dnp)
    if not mins:
        raise SystemExit("Sem acréscimo armazenado em added_time.py — abortado.")
    for tm, info in status.items():
        flag = "OK" if info["ok"] else "*** REVISAR ***"
        print(f"  {tm}: total {info['total']}/{info['expected']} "
              f"unmatched={info['unmatched']} [{flag}]")
    if not all(i["ok"] for i in status.values()):
        raise SystemExit("Validação falhou — minutos NÃO gravados.")

    out, missing = [lines[0]], []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        f = ln.split(";")
        tmc, jr = canon(f[ti]), f[ji].strip()
        if jr in dnp.get(tmc, set()):
            f[di] = ""                       # DNP: duração em branco (não jogou)
            out.append(";".join(f))
            continue
        val = mins.get(tmc, {}).get(jr)
        if val is None:
            missing.append((f[ti], f[ji]))
        else:
            f[di] = str(val).replace(".", ",")
        out.append(";".join(f))
    if missing:
        raise SystemExit(f"Jogadores sem minuto ({missing}) — revisar antes de gravar.")
    open(csv_path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"GRAVADO: {len(out) - 1} jogadores.")


if __name__ == "__main__":
    pdf = sys.argv[1]
    if len(sys.argv) > 2:
        fill_csv(pdf, sys.argv[2])
    else:
        mins, status = compute(pdf)
        if not mins:
            print("Sem acréscimo armazenado para este jogo (added_time.py).")
        else:
            for tm, info in status.items():
                flag = "OK" if info["ok"] else "*** REVISAR ***"
                print(f"\n{tm}: total {info['total']}/{info['expected']} [{flag}]")
                print(f"  entradas {info['on']}")
                print(f"  saídas   {info['off']}")
