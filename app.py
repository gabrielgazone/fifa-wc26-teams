import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
from fpdf import FPDF
from datetime import datetime

from positions_data import (
    get_position, POSITION_LABELS, POSITION_ORDER,
    team_code, flag_url, team_latlon, canon,
)
try:
    from technical_data import tech_for, TECH_COLS, TECH
except Exception:        # módulo opcional (dados técnico-táticos do PMSR)
    tech_for, TECH_COLS, TECH = (lambda *a: None), [], {}

# ── configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="FIFA WC 2026 · Physical Metrics",
    page_icon="⚽",
    layout="wide",
)

# ── tema visual "broadcast FIFA" (#20) ────────────────────────────────────────
st.markdown(
    """
    <style>
      :root { --fifa-maroon:#7a1f3d; --fifa-gold:#f0a500; }
      .stApp { background:
        radial-gradient(1200px 500px at 10% -10%, rgba(122,31,61,.10), transparent),
        radial-gradient(1000px 400px at 110% 0%, rgba(240,165,0,.08), transparent); }
      h1, h2, h3 { letter-spacing:.2px; }
      /* faixa superior do título */
      .fifa-hero { background: linear-gradient(100deg, #5e1730 0%, #7a1f3d 55%, #9c2b4e 100%);
        color:#fff; padding:14px 20px; border-radius:14px; margin-bottom:6px;
        box-shadow:0 6px 22px rgba(122,31,61,.35);
        border:1px solid rgba(255,255,255,.08); }
      .fifa-hero h2 { color:#fff; margin:0; }
      .fifa-hero .sub { color:#ffd98a; font-size:.86rem; }
      /* cartões de métrica */
      div[data-testid="stMetric"] { background:rgba(122,31,61,.06);
        border:1px solid rgba(122,31,61,.18); border-radius:12px; padding:12px 14px; }
      div[data-testid="stMetricValue"] { color:var(--fifa-maroon); font-weight:700; }
      /* abas */
      .stTabs [data-baseweb="tab-list"] { gap:4px; }
      .stTabs [data-baseweb="tab"] { border-radius:8px 8px 0 0; padding:6px 12px; }
      .stTabs [aria-selected="true"] { background:var(--fifa-maroon); color:#fff; }
      /* botões */
      .stButton>button, .stDownloadButton>button {
        border-radius:10px; border:1px solid var(--fifa-maroon);
        background:var(--fifa-maroon); color:#fff; font-weight:600; }
      .stButton>button:hover, .stDownloadButton>button:hover {
        background:#9c2b4e; border-color:#9c2b4e; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── banco de dados de partidas / estádios WC 2026 ────────────────────────────
# Fonte: FIFA.com + beIN Sports + CBC News (consultado jun/2026)
def _M(a, ga, b, gb, date, **extra):
    """Cria a entrada de uma partida (chave = par de seleções, não Match ID)."""
    e = {"teams": (a, b), "goals": {canon(a): ga, canon(b): gb},
         "score": f"{ga}–{gb}", "date": date, "round": "Fase de Grupos"}
    e.update(extra)
    return e


# Resultados conhecidos. A chave é o PAR de seleções — independe do Match ID,
# então qualquer arquivo novo (rodadas futuras) funciona sem mexer no código.
# Fonte: FIFA.com, ESPN, CBS, Yahoo, Olympics.com, Al Jazeera (jun/2026).
MATCHES = [
    # rodada 1 — grupos A–H
    _M("MEXICO", 2, "SOUTH AFRICA", 0, "11/06/2026",
       stadium="Estadio Azteca (Mexico City Stadium)", city="Cidade do México",
       country="México", capacity=80_824,
       note="Estádio de abertura — único a sediar 3 Copas (1970, 1986, 2026)."),
    _M("KOREA REPUBLIC", 2, "CZECHIA", 1, "11/06/2026"),
    _M("CANADA", 1, "BOSNIA AND HERZEGOVINA", 1, "12/06/2026",
       stadium="BMO Field (Toronto Stadium)", city="Toronto", country="Canadá",
       capacity=45_736),
    _M("USA", 4, "PARAGUAY", 1, "12/06/2026"),
    _M("HAITI", 0, "SCOTLAND", 1, "13/06/2026"),
    _M("AUSTRALIA", 2, "TÜRKIYE", 0, "13/06/2026", group="D",
       stadium="BC Place (Vancouver Stadium)", city="Vancouver", country="Canadá",
       capacity=48_821, surface="Grama natural", roof="Teto retrátil",
       scorers="Irankunda 27', Metcalfe 75' (AUS) · GK Patrick Beach: 8 defesas",
       note="Único estádio do torneio com Final da Copa Feminina (2015)."),
    _M("BRAZIL", 1, "MOROCCO", 1, "13/06/2026"),
    _M("QATAR", 1, "SWITZERLAND", 1, "13/06/2026"),
    _M("CÔTE D'IVOIRE", 1, "ECUADOR", 0, "14/06/2026"),
    _M("GERMANY", 7, "CURAÇAO", 1, "14/06/2026", note="Maior goleada da 1ª rodada."),
    _M("NETHERLANDS", 2, "JAPAN", 2, "14/06/2026"),
    _M("SWEDEN", 5, "TUNISIA", 1, "14/06/2026"),
    _M("SAUDI ARABIA", 1, "URUGUAY", 1, "15/06/2026"),
    _M("SPAIN", 0, "CABO VERDE", 0, "15/06/2026",
       note="Cabo Verde segurou os campeões europeus num dia histórico de 4 empates."),
    _M("IR IRAN", 2, "NEW ZEALAND", 2, "15/06/2026"),
    _M("BELGIUM", 1, "EGYPT", 1, "15/06/2026"),
    # rodada 1 — grupos I–L
    _M("FRANCE", 3, "SENEGAL", 1, "16/06/2026"),
    _M("NORWAY", 4, "IRAQ", 1, "16/06/2026"),
    _M("ARGENTINA", 3, "ALGERIA", 0, "16/06/2026"),
    _M("AUSTRIA", 3, "JORDAN", 1, "16/06/2026"),
    _M("PORTUGAL", 1, "CONGO DR", 1, "17/06/2026"),
    _M("COLOMBIA", 3, "UZBEKISTAN", 1, "17/06/2026"),
    _M("ENGLAND", 4, "CROATIA", 2, "17/06/2026"),
    _M("GHANA", 1, "PANAMA", 0, "18/06/2026"),
    # rodada 2 (vão sendo adicionados conforme a Copa avança)
    _M("BRAZIL", 3, "HAITI", 0, "19/06/2026", round="Fase de Grupos",
       stadium="Lincoln Financial Field (Philadelphia Stadium)", city="Filadélfia",
       country="EUA"),
    _M("CZECHIA", 1, "SOUTH AFRICA", 1, "18/06/2026", round="Fase de Grupos",
       stadium="Mercedes-Benz Stadium (Atlanta Stadium)", city="Atlanta",
       country="EUA",
       scorers="Sadílek 6' (CZE) · Mokoena 83' (pênalti, RSA)"),
    _M("MEXICO", 1, "KOREA REPUBLIC", 0, "18/06/2026", round="Fase de Grupos",
       scorers="Luis Romo 50' (MEX)"),
    _M("CANADA", 6, "QATAR", 0, "18/06/2026", round="Fase de Grupos",
       scorers="J. David x3, Larin, Saliba, Manai (gc) · 2 expulsões do Catar"),
    _M("SWITZERLAND", 4, "BOSNIA AND HERZEGOVINA", 1, "18/06/2026",
       round="Fase de Grupos",
       scorers="Manzambi x2, Vargas, Xhaka (pên.) · Mahmić (BIH)"),
    _M("SCOTLAND", 0, "MOROCCO", 1, "19/06/2026", round="Fase de Grupos",
       scorers="Saibari 2' (MAR)"),
    _M("TÜRKIYE", 0, "PARAGUAY", 1, "19/06/2026", round="Fase de Grupos",
       scorers="Galarza 2' (PAR) · Almirón expulso (45+3)"),
    _M("USA", 2, "AUSTRALIA", 0, "19/06/2026", round="Fase de Grupos",
       scorers="Burgess (gc) 11', Freeman 45' (USA)"),
    _M("GERMANY", 2, "CÔTE D'IVOIRE", 1, "20/06/2026", round="Fase de Grupos",
       scorers="Kessié 30' (CIV) · Undav x2 (68', 90+4', GER)"),
    _M("ECUADOR", 0, "CURAÇAO", 0, "20/06/2026", round="Fase de Grupos",
       scorers="Eloy Room: 15 defesas (recorde do torneio)"),
    _M("NETHERLANDS", 5, "SWEDEN", 1, "20/06/2026", round="Fase de Grupos",
       scorers="Brobbey x2, Gakpo x2, Summerville · Elanga (SWE)"),
    _M("TUNISIA", 0, "JAPAN", 4, "20/06/2026", round="Fase de Grupos"),
    _M("SPAIN", 4, "SAUDI ARABIA", 0, "21/06/2026", round="Fase de Grupos",
       scorers="Yamal 10', Oyarzabal x2 (21', 24'), Altambakti (gc) 49'"),
    _M("URUGUAY", 2, "CABO VERDE", 2, "21/06/2026", round="Fase de Grupos",
       scorers="Maxi Araújo, Canobbio (URU) · Kevin Pina, Hélio Varela (CPV)"),
    _M("NEW ZEALAND", 1, "EGYPT", 3, "21/06/2026", round="Fase de Grupos",
       scorers="Zico, Salah, Trezeguet (EGY) · primeira vitória do Egito em Copas"),
    _M("BELGIUM", 0, "IR IRAN", 0, "21/06/2026", round="Fase de Grupos",
       scorers="Beiranvand: 7 defesas · Ngoy (BEL) expulso aos 66'"),
    _M("NORWAY", 3, "SENEGAL", 2, "22/06/2026", round="Fase de Grupos",
       scorers="Haaland x2 (NOR) · Mané, Jackson (SEN)"),
    _M("FRANCE", 3, "IRAQ", 0, "22/06/2026", round="Fase de Grupos",
       scorers="Mbappé x2 (FRA)"),
    _M("ARGENTINA", 2, "AUSTRIA", 0, "22/06/2026", round="Fase de Grupos",
       scorers="Messi (recorde de presenças em Copas) · L. Martínez"),
    _M("JORDAN", 1, "ALGERIA", 2, "22/06/2026", round="Fase de Grupos",
       scorers="Gouiri, Mahrez (ALG) · Al-Taamari (JOR)"),
    _M("PORTUGAL", 5, "UZBEKISTAN", 0, "23/06/2026", round="Fase de Grupos",
       scorers="Cristiano Ronaldo x2 (1º a marcar em 6 Copas)"),
    _M("COLOMBIA", 1, "CONGO DR", 0, "23/06/2026", round="Fase de Grupos",
       scorers="Colômbia classificada às oitavas"),
    _M("ENGLAND", 0, "GHANA", 0, "23/06/2026", round="Fase de Grupos",
       scorers="Jogo truncado, sem gols"),
    _M("PANAMA", 0, "CROATIA", 1, "23/06/2026", round="Fase de Grupos",
       scorers="Budimir (CRO)"),
    # rodada 3 (matchday 3)
    _M("SCOTLAND", 0, "BRAZIL", 3, "24/06/2026", round="Fase de Grupos"),
    _M("MOROCCO", 4, "HAITI", 2, "24/06/2026", round="Fase de Grupos"),
    _M("SWITZERLAND", 2, "CANADA", 1, "24/06/2026", round="Fase de Grupos",
       scorers="Suíça vence o Grupo B"),
    _M("BOSNIA AND HERZEGOVINA", 3, "QATAR", 1, "24/06/2026", round="Fase de Grupos"),
    _M("CZECHIA", 0, "MEXICO", 3, "24/06/2026", round="Fase de Grupos"),
    _M("SOUTH AFRICA", 1, "KOREA REPUBLIC", 0, "24/06/2026", round="Fase de Grupos",
       scorers="Maseko (RSA) · África do Sul avança"),
    _M("CURAÇAO", 0, "CÔTE D'IVOIRE", 2, "25/06/2026", round="Fase de Grupos"),
    _M("ECUADOR", 2, "GERMANY", 1, "25/06/2026", round="Fase de Grupos",
       scorers="Equador surpreende a Alemanha"),
    _M("JAPAN", 1, "SWEDEN", 1, "25/06/2026", round="Fase de Grupos"),
    _M("TUNISIA", 1, "NETHERLANDS", 3, "25/06/2026", round="Fase de Grupos"),
    _M("TÜRKIYE", 3, "USA", 2, "25/06/2026", round="Fase de Grupos",
       scorers="Türkiye vence nos acréscimos; EUA avançam mesmo assim"),
    _M("PARAGUAY", 0, "AUSTRALIA", 0, "25/06/2026", round="Fase de Grupos"),
    # Rodada 3 (26/06/2026)
    _M("NORWAY", 1, "FRANCE", 4, "26/06/2026"),
    _M("SENEGAL", 5, "IRAQ", 0, "26/06/2026"),
    _M("EGYPT", 1, "IR IRAN", 1, "26/06/2026"),
    _M("NEW ZEALAND", 1, "BELGIUM", 5, "26/06/2026"),
    _M("CABO VERDE", 0, "SAUDI ARABIA", 0, "26/06/2026"),
    _M("URUGUAY", 0, "SPAIN", 1, "26/06/2026"),
    _M("PANAMA", 0, "ENGLAND", 2, "27/06/2026"),
    _M("CROATIA", 2, "GHANA", 1, "27/06/2026"),
    _M("ALGERIA", 3, "AUSTRIA", 3, "27/06/2026"),
    _M("JORDAN", 1, "ARGENTINA", 3, "27/06/2026"),
    _M("COLOMBIA", 0, "PORTUGAL", 0, "27/06/2026"),
    _M("CONGO DR", 3, "UZBEKISTAN", 1, "27/06/2026"),
    # ── Mata-mata · Round of 32 ──
    _M("SOUTH AFRICA", 0, "CANADA", 1, "28/06/2026", round="Round of 32"),
    _M("BRAZIL", 2, "JAPAN", 1, "29/06/2026", round="Round of 32"),
    _M("GERMANY", 1, "PARAGUAY", 1, "29/06/2026", round="Round of 32",
       scorers="1–1 no tempo normal; decidido nos pênaltis (prorrogação)"),
    _M("NETHERLANDS", 1, "MOROCCO", 1, "29/06/2026", round="Round of 32",
       scorers="1–1 no tempo normal; decidido nos pênaltis (prorrogação)"),
]

# índice por par de seleções (canônico)
RESULTS = {frozenset(e["goals"].keys()): e for e in MATCHES}


def result_for(*teams):
    """Entrada da partida pelo par de seleções (qualquer ordem/grafia)."""
    key = frozenset(canon(t) for t in teams if t is not None)
    return RESULTS.get(key)

STADIUM_DB = {
    "BC Place (Vancouver Stadium)": {
        "city": "Vancouver", "country": "Canadá", "capacity": 48_821,
        "matches_hosted": 7, "surface": "Grama natural", "roof": "Teto retrátil",
    },
    "AT&T Stadium (Arlington Stadium)": {
        "city": "Arlington (Dallas)", "country": "EUA", "capacity": 92_967,
        "matches_hosted": 9, "surface": "Grama sintética", "roof": "Cobertura fixa c/ abertura",
    },
    "MetLife Stadium (New York New Jersey Stadium)": {
        "city": "East Rutherford (Nova York)", "country": "EUA", "capacity": 82_500,
        "matches_hosted": 8, "surface": "Grama natural", "roof": "Aberto",
        "note": "Sede da Final (19/07/2026)",
    },
    "Estadio Azteca (Mexico City Stadium)": {
        "city": "Cidade do México", "country": "México", "capacity": 80_824,
        "matches_hosted": 5, "surface": "Grama natural", "roof": "Aberto",
        "note": "Único estádio a sediar 3 Copas do Mundo (1970, 1986, 2026). Jogo de abertura (11/06/2026).",
    },
    "Levi's Stadium (San Francisco Bay Area Stadium)": {
        "city": "Santa Clara", "country": "EUA", "capacity": 70_909,
        "matches_hosted": 6, "surface": "Grama natural", "roof": "Aberto",
    },
    "SoFi Stadium (Los Angeles Stadium)": {
        "city": "Inglewood (Los Angeles)", "country": "EUA", "capacity": 70_240,
        "matches_hosted": 8, "surface": "Grama natural", "roof": "Cobertura translúcida",
    },
    "Arrowhead Stadium (Kansas City Stadium)": {
        "city": "Kansas City", "country": "EUA", "capacity": 76_416,
        "matches_hosted": 6, "surface": "Grama natural", "roof": "Aberto",
    },
    "NRG Stadium (Houston Stadium)": {
        "city": "Houston", "country": "EUA", "capacity": 72_220,
        "matches_hosted": 6, "surface": "Grama natural", "roof": "Teto retrátil",
    },
    "Lincoln Financial Field (Philadelphia Stadium)": {
        "city": "Filadélfia", "country": "EUA", "capacity": 69_328,
        "matches_hosted": 6, "surface": "Grama natural", "roof": "Aberto",
    },
    "Gillette Stadium (Boston Stadium)": {
        "city": "Foxborough (Boston)", "country": "EUA", "capacity": 65_878,
        "matches_hosted": 6, "surface": "Grama natural", "roof": "Aberto",
    },
    "Hard Rock Stadium (Miami Stadium)": {
        "city": "Miami Gardens (Miami)", "country": "EUA", "capacity": 64_767,
        "matches_hosted": 6, "surface": "Grama natural", "roof": "Aberto",
    },
    "Empower Field at Mile High (Denver Stadium)": {
        "city": "Denver", "country": "EUA", "capacity": 76_125,
        "matches_hosted": 6, "surface": "Grama natural", "roof": "Aberto",
    },
    "Seattle Stadium (Lumen Field)": {
        "city": "Seattle", "country": "EUA", "capacity": 68_740,
        "matches_hosted": 6, "surface": "Grama natural", "roof": "Parcialmente coberto",
    },
    "BMO Field (Toronto Stadium)": {
        "city": "Toronto", "country": "Canadá", "capacity": 45_736,
        "matches_hosted": 6, "surface": "Grama natural", "roof": "Aberto",
    },
    "Estadio Akron (Guadalajara Stadium)": {
        "city": "Guadalajara", "country": "México", "capacity": 49_850,
        "matches_hosted": 5, "surface": "Grama natural", "roof": "Parcialmente coberto",
    },
    "Estadio BBVA (Monterrey Stadium)": {
        "city": "Monterrey", "country": "México", "capacity": 53_500,
        "matches_hosted": 5, "surface": "Grama natural", "roof": "Aberto",
    },
}

# ── constantes do domínio FIFA EPTS ──────────────────────────────────────────
SPEED_ZONES = {
    "Caminhada (1–7 km/h)":   "1-7 km/h (m)",
    "Corrida leve (7–15 km/h)": "7-15 km/h (m)",
    "Alta velocidade (15–20 km/h)": "15-20 km/h (m)",
    "Muito alta velocidade (20–25 km/h)": "20-25 km/h (m)",
    "Sprint (25+ km/h)":       "25+ km/h (m)",
}
ZONE_COLORS = ["#4e9af1", "#36c2a8", "#f5c518", "#ff7043", "#e53935"]
NUMERIC_COLS = [
    "Total Duration (min)", "Total Distance (m)",
    "1-7 km/h (m)", "7-15 km/h (m)", "15-20 km/h (m)",
    "20-25 km/h (m)", "25+ km/h (m)",
    "Max Speed (km/h)", "# Speed Runs", "# Sprints",
]

# ── helpers ───────────────────────────────────────────────────────────────────

def parse_number(s):
    """Converte '10.810,959' ou '10810,959' ou '10810.959' para float."""
    if pd.isna(s):
        return float("nan")
    s = str(s).strip().replace(" ", "")
    # formato europeu com ponto de milhar: 1.234,56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")


@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes, filename: str) -> pd.DataFrame:
    raw = file_bytes.decode("utf-8", errors="replace")
    sep = ";" if raw.count(";") > raw.count(",") else ","
    df = pd.read_csv(io.StringIO(raw), sep=sep)
    df.columns = df.columns.str.strip()
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = df[col].apply(parse_number)
    if "_arquivo" not in df.columns:
        df["_arquivo"] = filename
    return df


RESULT_COLS = ["Resultado", "Gols Marcados", "Gols Sofridos", "Saldo de Gols",
               "Pontos", "Adversário"]
RESULT_ORDER = ["Vitória", "Empate", "Derrota"]
RESULT_COLORS = {"Vitória": "#2e9e4f", "Empate": "#f5c518", "Derrota": "#e53935"}


def manual_key(a, b):
    """Chave estável para um par de seleções (independe da ordem)."""
    return "|".join(sorted([canon(a), canon(b)]))


def teams_of_match(df, mid):
    """Seleções presentes em uma partida, na ordem em que aparecem nos dados."""
    sub = df[df["Match ID"] == mid]
    return list(dict.fromkeys(sub["Team Name"].dropna().tolist()))


def match_entry(df, mid):
    """Entrada de resultado (conhecida OU manual) para a partida `mid`."""
    teams = teams_of_match(df, mid)
    if len(teams) < 2:
        return None, teams
    manual = st.session_state.get("manual_results", {})
    entry = manual.get(manual_key(teams[0], teams[1])) or result_for(teams[0], teams[1])
    return entry, teams


def enrich_results(df: pd.DataFrame) -> pd.DataFrame:
    """Anexa o resultado a cada jogador descobrindo o adversário a partir dos
    PRÓPRIOS dados (as 2 seleções da partida) e buscando o placar pelo par de
    seleções — conhecido ou informado manualmente. Funciona para qualquer
    arquivo novo, sem depender de Match ID cadastrado."""
    if "Match ID" not in df.columns or "Team Name" not in df.columns:
        return df
    df = df.copy()
    match_teams = {mid: teams_of_match(df, mid)
                   for mid in df["Match ID"].dropna().unique()}
    manual = st.session_state.get("manual_results", {})

    def outcome(row):
        team = row["Team Name"]
        teams = match_teams.get(row["Match ID"], [])
        opp = next((t for t in teams if canon(t) != canon(team)), None)
        if opp is None:
            return pd.Series([pd.NA] * len(RESULT_COLS), index=RESULT_COLS)
        entry = manual.get(manual_key(team, opp)) or result_for(team, opp)
        if not entry:
            return pd.Series([pd.NA] * len(RESULT_COLS), index=RESULT_COLS)
        gf, ga = entry["goals"].get(canon(team)), entry["goals"].get(canon(opp))
        if gf is None or ga is None:
            return pd.Series([pd.NA] * len(RESULT_COLS), index=RESULT_COLS)
        if gf > ga:
            res, pts = "Vitória", 3
        elif gf < ga:
            res, pts = "Derrota", 0
        else:
            res, pts = "Empate", 1
        return pd.Series([res, gf, ga, gf - ga, pts, opp], index=RESULT_COLS)

    df[RESULT_COLS] = df.apply(outcome, axis=1)

    # posição oficial (GK/DF/MF/FW) por seleção + número da camisa
    if "Jersey #" in df.columns:
        df["Posição"] = df.apply(
            lambda r: get_position(r.get("Team Name"), r.get("Jersey #")), axis=1
        )
        df["Posição (nome)"] = df["Posição"].map(POSITION_LABELS)
    return df


def build_pdf(df: pd.DataFrame, stats: pd.DataFrame,
              charts: list[tuple[str, bytes]], log: list[str]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # capa
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.ln(20)
    pdf.cell(0, 12, "FIFA World Cup 2026", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Player Physical Metrics — Relatório de Análise", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(
        0, 6,
        "Dados coletados pelo sistema EPTS da FIFA via 16 câmeras ópticas de rastreamento "
        "por estádio (até 172 milhões de pontos de dados por partida, 50 amostras/segundo).",
        align="C",
    )

    # log
    if log:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "Operações realizadas", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for item in log:
            pdf.cell(0, 6, f"  • {item}", ln=True)

    # resumo estatístico
    if not stats.empty:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "Resumo Estatístico", ln=True)
        pdf.set_font("Helvetica", "", 7)
        idx_label = [""] + [str(i)[:16] for i in stats.index]
        show_cols = list(stats.columns)[:8]
        col_w = 190 / (len(show_cols) + 1)
        pdf.set_fill_color(220, 220, 220)
        for h in idx_label[:1] + show_cols:
            pdf.cell(col_w, 5, str(h)[:18], border=1, fill=True)
        pdf.ln()
        for idx, row in stats[show_cols].iterrows():
            pdf.cell(col_w, 5, str(idx)[:16], border=1)
            for v in row:
                try:
                    txt = f"{float(v):.1f}"
                except Exception:
                    txt = str(v)
                pdf.cell(col_w, 5, txt[:16], border=1)
            pdf.ln()

    # dados (50 linhas)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, f"Dados filtrados ({min(len(df), 50)} de {len(df)} linhas)", ln=True)
    pdf.set_font("Helvetica", "", 7)
    show_c = [c for c in df.columns if c not in ("_arquivo",)][:9]
    cw = 190 / len(show_c) if show_c else 20
    pdf.set_fill_color(220, 220, 220)
    for c in show_c:
        pdf.cell(cw, 5, str(c)[:18], border=1, fill=True)
    pdf.ln()
    for _, row in df[show_c].head(50).iterrows():
        for v in row:
            pdf.cell(cw, 5, str(v)[:18], border=1)
        pdf.ln()

    # lista de gráficos gerados (visualizáveis no app)
    if charts:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "Gráficos gerados no app", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(
            0, 7,
            "Os gráficos abaixo estão disponíveis na aba 'Análise Física' do aplicativo. "
            "A exportação de imagens foi desativada para garantir carregamento rápido no Streamlit Cloud.",
        )
        pdf.ln(3)
        for i, (title, _) in enumerate(charts, 1):
            pdf.cell(0, 7, f"  {i}. {title}", ln=True)

    return bytes(pdf.output())


# ── estatística ───────────────────────────────────────────────────────────────

def cohens_d(a, b):
    """Tamanho de efeito padronizado (diferença de médias / desvio combinado)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) < 2 or len(b) < 2:
        return np.nan
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2)
                 / (na + nb - 2))
    return (a.mean() - b.mean()) / sp if sp > 0 else np.nan


def cliffs_delta(a, b):
    """Tamanho de efeito não-paramétrico (-1 a 1)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return np.nan
    gt = sum((x > b).sum() for x in a)
    lt = sum((x < b).sum() for x in a)
    return (gt - lt) / (len(a) * len(b))


def interpret_effect(d):
    """Classifica magnitude do efeito (escala de Cohen)."""
    if np.isnan(d):
        return "—"
    ad = abs(d)
    if ad < 0.2:
        return "desprezível"
    if ad < 0.5:
        return "pequeno"
    if ad < 0.8:
        return "médio"
    return "grande"


def mann_whitney(a, b):
    """Retorna (p-valor, Cliff's delta). p via scipy (import tardio)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) < 3 or len(b) < 3:
        return np.nan, cliffs_delta(a, b)
    try:
        from scipy.stats import mannwhitneyu
        _, p = mannwhitneyu(a, b, alternative="two-sided")
    except Exception:
        p = np.nan
    return p, cliffs_delta(a, b)


# ── métricas derivadas (reutilizável) ─────────────────────────────────────────

def add_derived(frame):
    """Acrescenta métricas de intensidade (por minuto) e eficiência."""
    f = frame.copy()
    if "Total Duration (min)" not in f.columns:
        return f
    dur = f["Total Duration (min)"].replace(0, np.nan)
    full = all(c in f.columns for c in SPEED_ZONES.values())
    if "Total Distance (m)" in f.columns:
        f["Distância/min"] = f["Total Distance (m)"] / dur
    if full:
        f["HID (m)"] = f["15-20 km/h (m)"] + f["20-25 km/h (m)"] + f["25+ km/h (m)"]
        f["HID/min"] = f["HID (m)"] / dur
        f["Z4+Z5 (m)"] = f["20-25 km/h (m)"] + f["25+ km/h (m)"]
        f["Sprint (m)"] = f["25+ km/h (m)"]
        f["Sprint/min"] = f["25+ km/h (m)"] / dur
        if "Total Distance (m)" in f.columns:
            f["% Sprint"] = (f["25+ km/h (m)"]
                             / f["Total Distance (m)"].replace(0, np.nan) * 100)
    if "# Sprints" in f.columns:
        f["Sprints/min"] = f["# Sprints"] / dur
        if full:
            f["m por sprint"] = f["25+ km/h (m)"] / f["# Sprints"].replace(0, np.nan)
    if "# Speed Runs" in f.columns:
        f["Speed runs/min"] = f["# Speed Runs"] / dur
    return f


def metric_lists(frame):
    """Retorna (raw, derived, all, intensity) — listas de métricas presentes."""
    raw = [c for c in NUMERIC_COLS if c in frame.columns]
    derived = [c for c in ["Distância/min", "HID (m)", "HID/min", "Z4+Z5 (m)",
                           "Sprint (m)", "Sprint/min", "% Sprint", "Sprints/min",
                           "Speed runs/min", "m por sprint"] if c in frame.columns]
    intensity = [c for c in ["Distância/min", "HID/min", "Sprint/min", "Sprints/min",
                             "Speed runs/min", "Max Speed (km/h)", "% Sprint",
                             "m por sprint"] if c in frame.columns]
    return raw, derived, raw + derived, intensity


def team_match_totals(frame, value_cols):
    """Total da equipe (soma dos jogadores) por (seleção, partida)."""
    cols = [c for c in value_cols if c in frame.columns]
    if "Team Name" not in frame.columns or "Match ID" not in frame.columns or not cols:
        return pd.DataFrame()
    return frame.groupby(["Team Name", "Match ID"])[cols].sum().reset_index()


def pct_vs(value, series):
    """Percentil (0-100) de `value` dentro de `series`."""
    s = series.dropna()
    if len(s) < 2 or pd.isna(value):
        return np.nan
    return round((s < value).mean() * 100)


def scout_report(df_all, team):
    """Gera um relatório textual (markdown) do perfil físico de uma seleção."""
    d = add_derived(df_all)
    team_df = d[d["Team Name"] == team]
    if team_df.empty:
        return "Sem dados para esta seleção."
    lines = [f"# Scout Report — {team}", ""]

    # contexto de resultado
    if "Resultado" in team_df.columns and team_df["Resultado"].notna().any():
        res = team_df["Resultado"].dropna().iloc[0]
        opp = team_df["Adversário"].dropna().iloc[0] if "Adversário" in team_df else "—"
        gm = int(team_df["Gols Marcados"].dropna().iloc[0]) if "Gols Marcados" in team_df else "?"
        gs = int(team_df["Gols Sofridos"].dropna().iloc[0]) if "Gols Sofridos" in team_df else "?"
        lines.append(f"**Resultado:** {res} vs {opp} ({gm}–{gs})")
        lines.append("")

    # totais de equipe vs torneio
    tt = team_match_totals(d, ["Total Distance (m)", "Z4+Z5 (m)", "25+ km/h (m)"])
    if not tt.empty:
        all_teams = tt.groupby("Team Name").mean(numeric_only=True)
        row = all_teams.loc[team]
        for col, lbl, unit, div in [("Total Distance (m)", "distância total", "km", 1000),
                                     ("Z4+Z5 (m)", "alta intensidade (≥20 km/h)", "m", 1),
                                     ("25+ km/h (m)", "sprint (≥25 km/h)", "m", 1)]:
            if col in all_teams.columns:
                val = row[col] / div
                avg = all_teams[col].mean() / div
                p = pct_vs(row[col], all_teams[col])
                diff = (val / avg - 1) * 100 if avg else 0
                comp = "acima" if diff >= 0 else "abaixo"
                lines.append(f"- **{lbl.capitalize()}:** {val:,.1f} {unit} "
                             f"({abs(diff):.0f}% {comp} da média do torneio · "
                             f"percentil {p:.0f}).")
        lines.append("")

    # posição que mais corre
    if "Posição" in team_df.columns and "Distância/min" in team_df.columns:
        bypos = team_df.groupby("Posição")["Distância/min"].mean()
        if not bypos.empty:
            top_pos = bypos.idxmax()
            lines.append(f"- **Setor mais intenso:** {POSITION_LABELS.get(top_pos, top_pos)} "
                         f"({bypos.max():.1f} m/min em média).")

    # destaque individual
    if "Distância/min" in team_df.columns and "Player Name" in team_df.columns:
        top = team_df.loc[team_df["Distância/min"].idxmax()]
        lines.append(f"- **Destaque físico:** {top['Player Name']} "
                     f"({top['Distância/min']:.1f} m/min, "
                     f"vel. máx. {top.get('Max Speed (km/h)', float('nan')):.1f} km/h).")
        if "# Sprints" in team_df.columns:
            sp = team_df.loc[team_df["# Sprints"].idxmax()]
            lines.append(f"- **Mais sprints:** {sp['Player Name']} "
                         f"({int(sp['# Sprints'])} sprints).")

    lines.append("")
    lines.append(f"_Gerado por FIFA WC 2026 Physical Metrics · {datetime.now():%d/%m/%Y %H:%M}_")
    return "\n".join(lines)


def _lat(s):
    """Sanitiza texto para as fontes core do fpdf (latin-1)."""
    return str(s).encode("latin-1", "replace").decode("latin-1")


def build_team_infographic(df_all, team):
    """Infográfico A4 de uma página com o perfil físico da seleção (#19)."""
    d = add_derived(df_all)
    tdf = d[d["Team Name"] == team]
    M, G = (122, 31, 61), (240, 165, 0)
    pdf = FPDF(orientation="P", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(False)

    pdf.set_fill_color(*M); pdf.rect(0, 0, 210, 34, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(12, 7); pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 11, _lat(f"{team}  ({team_code(team)})"), ln=True)
    pdf.set_x(12); pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, "FIFA World Cup 2026  -  Perfil Fisico de Equipe", ln=True)
    pdf.set_fill_color(*G); pdf.rect(0, 34, 210, 2, "F")
    pdf.set_text_color(30, 30, 30)

    tt = team_match_totals(d, ["Total Distance (m)", "Z4+Z5 (m)", "25+ km/h (m)"])
    kpis = []
    if not tt.empty:
        allt = tt.groupby("Team Name").mean(numeric_only=True)
        if team in allt.index:
            row = allt.loc[team]
            for col, lbl, div in [("Total Distance (m)", "Distancia total (km)", 1000),
                                  ("Z4+Z5 (m)", "Alta int. >=20 (km)", 1000),
                                  ("25+ km/h (m)", "Sprint >=25 (km)", 1000)]:
                if col in allt.columns:
                    kpis.append((lbl, f"{row[col] / div:,.2f}", pct_vs(row[col], allt[col])))
    if "Max Speed (km/h)" in tdf.columns and not tdf.empty:
        kpis.append(("Vel. maxima (km/h)", f"{tdf['Max Speed (km/h)'].max():.1f}", None))

    x0, y, w, h, gap = 12, 46, 44, 32, 3
    for i, (lbl, val, p) in enumerate(kpis[:4]):
        x = x0 + i * (w + gap)
        pdf.set_fill_color(245, 238, 241); pdf.rect(x, y, w, h, "F")
        pdf.set_xy(x + 2, y + 3); pdf.set_text_color(90, 90, 90); pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(w - 4, 4, _lat(lbl))
        pdf.set_xy(x + 2, y + 14); pdf.set_text_color(*M); pdf.set_font("Helvetica", "B", 15)
        pdf.cell(w - 4, 8, _lat(val))
        if p is not None and not (isinstance(p, float) and np.isnan(p)):
            pdf.set_xy(x + 2, y + 24); pdf.set_text_color(120, 120, 120); pdf.set_font("Helvetica", "", 7)
            pdf.cell(w - 4, 4, _lat(f"percentil {p:.0f}/100"))
    pdf.set_text_color(30, 30, 30)

    # top 5 jogadores por intensidade
    yy = y + h + 10
    pdf.set_xy(12, yy); pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Top 5 - intensidade (m/min)", ln=True)
    pdf.set_font("Helvetica", "", 10)
    if "Distância/min" in tdf.columns:
        top5 = tdf.dropna(subset=["Distância/min"]).nlargest(5, "Distância/min")
        for _, r in top5.iterrows():
            pos = r.get("Posição (nome)") if pd.notna(r.get("Posição (nome)")) else "-"
            pdf.set_x(14)
            pdf.cell(0, 7, _lat(f"- {r['Player Name']}  ({pos})  -  "
                                f"{r['Distância/min']:.1f} m/min  |  "
                                f"vel. max {r.get('Max Speed (km/h)', float('nan')):.1f} km/h"),
                     ln=True)

    pdf.set_y(282); pdf.set_font("Helvetica", "I", 7); pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, _lat("Metodologia de benchmark: Bradley (2024), Biology of Sport 41(1):271-278."),
             align="C")
    return bytes(pdf.output())


# ── tabela contextual: 1 linha por equipe-jogo (físico + resultado + técnico) ──
CTX_PHYS = ["Dist. total (km)", "Z4+Z5 (km)", "Sprint Z5 (km)", "# Sprints", "# Speed Runs"]


def build_context_table(df):
    if "Team Name" not in df.columns or "Match ID" not in df.columns:
        return pd.DataFrame(), [], []
    d = add_derived(df)
    full = all(c in d.columns for c in SPEED_ZONES.values())
    if not full:
        return pd.DataFrame(), [], []
    # físico somado por equipe-jogo
    g = d.groupby(["Team Name", "Match ID"])
    tab = pd.DataFrame({
        "Dist. total (km)": g["Total Distance (m)"].sum() / 1000,
        "Z4+Z5 (km)": g["Z4+Z5 (m)"].sum() / 1000,
        "Sprint Z5 (km)": g["25+ km/h (m)"].sum() / 1000,
        "# Sprints": g["# Sprints"].sum(),
        "# Speed Runs": g["# Speed Runs"].sum(),
    }).reset_index()
    # resultado (constante dentro da equipe-jogo)
    for col, src in [("Gols feitos", "Gols Marcados"), ("Gols sofridos", "Gols Sofridos"),
                     ("Pontos", "Pontos"), ("Resultado", "Resultado")]:
        if src in d.columns:
            tab[col] = tab.apply(
                lambda r: d[(d["Team Name"] == r["Team Name"])
                            & (d["Match ID"] == r["Match ID"])][src].iloc[0], axis=1)
    # técnico (via par de seleções)
    match_teams = {mid: teams_of_match(d, mid) for mid in d["Match ID"].dropna().unique()}
    tech_present = TECH_COLS if TECH_COLS else []
    for c in tech_present:
        tab[c] = pd.NA

    def fill_tech(row):
        teams = match_teams.get(row["Match ID"], [])
        opp = next((t for t in teams if canon(t) != canon(row["Team Name"])), None)
        if not opp:
            return pd.Series([pd.NA] * len(tech_present), index=tech_present)
        entry = tech_for(row["Team Name"], opp)
        if not entry:
            return pd.Series([pd.NA] * len(tech_present), index=tech_present)
        st_team = entry.get(canon(row["Team Name"]))
        if not st_team:
            return pd.Series([pd.NA] * len(tech_present), index=tech_present)
        return pd.Series([st_team.get(c, pd.NA) for c in tech_present], index=tech_present)

    if tech_present:
        tab[tech_present] = tab.apply(fill_tech, axis=1)
    tab["Sigla"] = tab["Team Name"].map(team_code)

    # força numérico (pd.NA + floats geram dtype object, que quebra mean/std)
    for c in tech_present + ["Gols feitos", "Gols sofridos", "Pontos"]:
        if c in tab.columns:
            tab[c] = pd.to_numeric(tab[c], errors="coerce")

    phys_cols = [c for c in CTX_PHYS if c in tab.columns]
    res_cols = [c for c in ["Gols feitos", "Gols sofridos", "Pontos"] if c in tab.columns]
    tech_cols = [c for c in tech_present if c in tab.columns and tab[c].notna().any()]
    return tab, phys_cols + res_cols, tech_cols


def context_diff(ctx, metric_cols):
    """Diferencial intra-jogo (time − adversário do MESMO jogo) por equipe-jogo.
    Devolve colunas 'Δ <métrica>' + 'ΔGols' (saldo) + Resultado. Controla o
    contexto do jogo (árbitro, adversário, clima): sinal muito mais limpo."""
    cols = [c for c in metric_cols if c in ctx.columns]
    work = ctx.copy()
    for c in cols:
        work[c] = pd.to_numeric(work[c], errors="coerce")
    if {"Gols feitos", "Gols sofridos"}.issubset(work.columns):
        work["_saldo"] = (pd.to_numeric(work["Gols feitos"], errors="coerce")
                          - pd.to_numeric(work["Gols sofridos"], errors="coerce"))
    else:
        work["_saldo"] = np.nan
    rows = []
    for mid, grp in work.groupby("Match ID"):
        if len(grp) != 2:
            continue
        ra, rb = grp.iloc[0], grp.iloc[1]
        for r, o in ((ra, rb), (rb, ra)):
            rec = {"Match ID": mid, "Team Name": r["Team Name"], "Sigla": r.get("Sigla"),
                   "Resultado": r.get("Resultado"), "ΔGols": r["_saldo"]}
            for c in cols:
                rec["Δ " + c] = r[c] - o[c]
            rows.append(rec)
    return pd.DataFrame(rows)


def partial_spearman(x, y, z):
    """Spearman parcial de x,y controlando z. Retorna (rho_parcial, p, n)."""
    from scipy.stats import spearmanr, t as tdist
    x, y, z = (np.asarray(v, float) for v in (x, y, z))
    m = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
    x, y, z = x[m], y[m], z[m]
    n = len(x)
    if n < 6:
        return np.nan, np.nan, n
    rxy = spearmanr(x, y).correlation
    rxz = spearmanr(x, z).correlation
    ryz = spearmanr(y, z).correlation
    den = np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    if not np.isfinite(den) or den == 0:
        return np.nan, np.nan, n
    rp = (rxy - rxz * ryz) / den
    dfree = n - 3
    if dfree <= 0 or abs(rp) >= 1:
        return rp, np.nan, n
    tval = rp * np.sqrt(dfree / (1 - rp ** 2))
    return rp, float(2 * tdist.sf(abs(tval), dfree)), n


# radar técnico-tático (variáveis "quanto maior, mais") e fases de jogo
TECH_RADAR = ["Posse (%)", "xG", "Finalizações", "Acerto passe (%)", "Line breaks",
              "Progressões", "Recep. terço final", "Pressões def.", "Turnovers forçados"]
PHASE_IN = ["Construção livre (%)", "Construção pressionada (%)", "Progressão fase (%)",
            "Ataque terço final (%)", "Bola longa (%)", "Transição ofensiva (%)",
            "Contra-ataque (%)", "Bola parada (%)"]
PHASE_OUT = ["Pressão alta (%)", "Pressão média (%)", "Pressão baixa (%)", "Bloco alto (%)",
             "Bloco médio (%)", "Bloco baixo (%)", "Recuperação (%)", "Transição defensiva (%)",
             "Counter-press (%)"]


def team_technical_profiles(team_names):
    """Perfil técnico-tático MÉDIO por seleção (média entre seus jogos), a partir do
    technical_data, com PPDA e Field tilt derivados (ajuste pela posse do adversário).
    Índice = nome de exibição; colunas = TECH_COLS + PPDA + Field tilt (%)."""
    want = {canon(t): t for t in team_names}
    bucket = {}
    for entry in TECH.values():
        names = list(entry.keys())
        if len(names) != 2:
            continue
        a, b = names
        for tm, opp in ((a, b), (b, a)):
            if tm not in want:
                continue
            s, op = dict(entry[tm]), entry[opp]
            if op.get("Passes") and s.get("Pressões def."):
                s["PPDA"] = op["Passes"] / s["Pressões def."]   # passes do rival / pressões
            ra, rb = s.get("Recep. terço final"), op.get("Recep. terço final")
            if ra is not None and rb is not None and (ra + rb) > 0:
                s["Field tilt (%)"] = 100 * ra / (ra + rb)      # domínio territorial
            bucket.setdefault(want[tm], []).append(s)
    if not bucket:
        return pd.DataFrame()
    cols = list(TECH_COLS) + ["PPDA", "Field tilt (%)"]
    rows = {disp: {c: np.nanmean([x.get(c, np.nan) for x in lst]) for c in cols}
            for disp, lst in bucket.items()}
    return pd.DataFrame(rows).T


def render_kpis(df):
    """4 cartões-resumo (Partidas/Seleções/Jogadores/Linhas) — topo de cada aba."""
    ok = isinstance(df, pd.DataFrame) and not df.empty
    n_matches = df["Match ID"].nunique() if ok and "Match ID" in df.columns else 0
    teams = df["Team Name"].nunique() if ok and "Team Name" in df.columns else 0
    players = df["Player ID"].nunique() if ok and "Player ID" in df.columns else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Partidas", n_matches)
    c2.metric("Seleções", teams)
    c3.metric("Jogadores únicos", players)
    c4.metric("Total de linhas", f"{len(df):,}" if ok else 0)
    st.divider()


# ── estado global ─────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "log" not in st.session_state:
    st.session_state.log = []
if "charts_pdf" not in st.session_state:
    st.session_state.charts_pdf = []

# ── barra lateral: referência de estádios ────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚽ FIFA World Cup 2026")
    st.caption("Canada · México · EUA · 48 seleções · 104 jogos")
    st.divider()
    with st.expander(f"🏟️ Estádios do torneio ({len(STADIUM_DB)})", expanded=False):
        st.caption("Informação contextual — o foco do app são as análises físicas.")
        for nome, s in STADIUM_DB.items():
            st.markdown(
                f"**{s['city']}** — {nome.split('(')[0].strip()}  \n"
                f"{s['country']} · {s['capacity']:,} lug. · {s['matches_hosted']} jogos · "
                f"{s['surface']}"
            )
            if s.get("note"):
                st.caption(s["note"])
            st.divider()
    st.divider()
    st.caption(
        "Sistema de rastreamento: **EPTS FIFA**  \n"
        "16 câmeras ópticas/estádio · 50 Hz  \n"
        "Até 172 M pontos de dados/jogo"
    )
    with st.expander("📚 Referência científica"):
        st.markdown(
            "**Bradley, P. S. (2024).** *'Setting the Benchmark' Part 2: "
            "Contextualising the Physical Demands of Teams in the FIFA World Cup "
            "Qatar 2022.* **Biology of Sport, 41(1), 271–278.**  \n"
            "[doi.org/10.5114/biolsport.2024.131091]"
            "(https://doi.org/10.5114/biolsport.2024.131091)  \n\n"
            "As análises de benchmark de equipe (totais absolutos, zonas Z4+Z5 e Z5, "
            "coeficiente de variação e mapas de quadrantes) seguem a metodologia deste estudo."
        )

# ── cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="fifa-hero">
      <h2>⚽ FIFA World Cup 2026 · Player Physical Metrics</h2>
      <div class="sub">Sistema EPTS — 16 câmeras ópticas por estádio · 50 Hz · até 172 M pontos de dados/jogo</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── abas ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab_dest, tab_ctx, tab4, tab5 = st.tabs([
    "📂 Upload",
    "📋 Tabela & Filtros",
    "📊 Análise Física",
    "✨ Destaques",
    "🧩 Contextual",
    "⚙️ Transformar",
    "📄 Relatório PDF",
])

# ════════════════════════════════════════════════════════════════════════════
# ABA 1 — Upload
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Upload de arquivos CSV da FIFA")
    st.info(
        "**Formato esperado:** arquivos gerados pelo sistema EPTS da FIFA — "
        "separador `;` (ponto-e-vírgula), decimais com vírgula. "
        "Você pode carregar múltiplas partidas de uma vez.",
        icon="ℹ️",
    )
    uploaded = st.file_uploader(
        "Arraste ou clique para selecionar arquivos .csv",
        type="csv",
        accept_multiple_files=True,
    )

    if uploaded:
        frames = []
        for f in uploaded:
            with st.spinner(f"Lendo {f.name}…"):
                try:
                    df_tmp = load_csv(f.read(), f.name)
                    frames.append(df_tmp)
                    st.success(f"✅ {f.name} — {len(df_tmp)} jogadores")
                except Exception as e:
                    st.error(f"Erro em {f.name}: {e}")
        if frames:
            st.session_state.df = enrich_results(pd.concat(frames, ignore_index=True))
            st.session_state.log = []
            st.session_state.charts_pdf = []

    df = st.session_state.df
    render_kpis(df)
    if not df.empty:
        # ── painel de contexto por partida ────────────────────────────────
        if "Match ID" in df.columns:
            match_ids = df["Match ID"].dropna().unique().tolist()
            st.divider()
            st.subheader("🏟️ Informações das partidas")
            com_result = sum(1 for mid in match_ids if match_entry(df, mid)[0])
            st.caption(f"{com_result} de {len(match_ids)} partidas com resultado cadastrado.")
            sem_result = []
            for mid in match_ids:
                entry, teams = match_entry(df, mid)
                if entry:
                    a, b = entry.get("teams", (teams + ["?", "?"])[:2])
                    grp = f" — Grupo {entry['group']}" if entry.get("group") else ""
                    with st.container(border=True):
                        st.markdown(f"### {a} {entry.get('score', '')} {b}")
                        st.caption(f"📅 {entry.get('date', '—')}  ·  "
                                   f"{entry.get('round', 'Fase de Grupos')}{grp}  ·  "
                                   f"Match ID: {mid}")
                        linhas = []
                        if entry.get("stadium"):
                            linhas.append(f"**🏟️ Estádio:** {entry['stadium']}")
                        if entry.get("city"):
                            linhas.append(f"**📍 Cidade:** {entry['city']}, "
                                          f"{entry.get('country', '')}".rstrip(", "))
                        if entry.get("capacity"):
                            linhas.append(f"**👥 Capacidade:** {entry['capacity']:,} pessoas")
                        if entry.get("surface"):
                            linhas.append(f"**🌿 Superfície:** {entry['surface']}  ·  "
                                          f"**🔲 Cobertura:** {entry.get('roof', '—')}")
                        if linhas:
                            st.markdown("  \n".join(linhas))
                        if entry.get("scorers"):
                            st.markdown(f"**⚽ Destaque:** {entry['scorers']}")
                        if entry.get("note"):
                            st.info(entry["note"], icon="ℹ️")
                else:
                    sem_result.append((mid, teams))
                    lbl = " × ".join(team_code(t) for t in teams) if teams else str(mid)
                    with st.container(border=True):
                        st.markdown(f"### {lbl}")
                        st.caption(f"Match ID: {mid} — resultado ainda não cadastrado")

            # ── entrada manual de resultados (rodadas novas) ──────────────
            if sem_result:
                st.divider()
                st.subheader("✍️ Informar placar de partidas novas")
                st.caption("Para jogos que o app ainda não conhece (rodadas seguintes, "
                           "mata-mata). Informar o placar habilita todas as análises por "
                           "resultado. As métricas físicas já funcionam mesmo sem o placar.")
                st.session_state.setdefault("manual_results", {})
                for mid, teams in sem_result:
                    if len(teams) < 2:
                        st.caption(f"Match ID {mid}: só uma seleção nos dados — não dá "
                                   "para inferir o confronto.")
                        continue
                    a, b = teams[0], teams[1]
                    with st.form(f"mr_{mid}"):
                        st.markdown(f"**{a} × {b}**")
                        cga, cgb = st.columns(2)
                        ga = cga.number_input(f"Gols {team_code(a)}", 0, 30, 0, key=f"ga_{mid}")
                        gb = cgb.number_input(f"Gols {team_code(b)}", 0, 30, 0, key=f"gb_{mid}")
                        if st.form_submit_button("💾 Salvar resultado"):
                            st.session_state.manual_results[manual_key(a, b)] = {
                                "teams": (a, b),
                                "goals": {canon(a): int(ga), canon(b): int(gb)},
                                "score": f"{int(ga)}–{int(gb)}", "date": "",
                                "round": "Fase de Grupos"}
                            st.session_state.df = enrich_results(st.session_state.df)
                            st.success(f"Resultado {a} {int(ga)}–{int(gb)} {b} salvo!")
                            st.rerun()

        st.divider()
        st.subheader("Prévia dos dados")
        st.dataframe(df.head(20), use_container_width=True)
    else:
        st.warning("Nenhum arquivo carregado. Faça upload acima.")


# ════════════════════════════════════════════════════════════════════════════
# ABA 2 — Tabela & Filtros
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    df = st.session_state.df
    render_kpis(df)
    if df.empty:
        st.info("Carregue arquivos na aba **Upload** primeiro.")
    else:
        st.header("Tabela de dados com filtros")
        df_view = df.copy()

        with st.expander("🔧 Filtros", expanded=True):
            f1, f2, f3 = st.columns(3)
            if "Team Name" in df.columns:
                teams_opt = ["Todas"] + sorted(df["Team Name"].dropna().unique().tolist())
                sel_team = f1.selectbox("Seleção", teams_opt)
                if sel_team != "Todas":
                    df_view = df_view[df_view["Team Name"] == sel_team]

            if "Match ID" in df.columns:
                match_opt = ["Todas"] + sorted(df_view["Match ID"].dropna().astype(str).unique().tolist())
                sel_match = f2.selectbox("Partida (Match ID)", match_opt)
                if sel_match != "Todas":
                    df_view = df_view[df_view["Match ID"].astype(str) == sel_match]

            if "Player Name" in df.columns:
                player_opt = ["Todos"] + sorted(df_view["Player Name"].dropna().unique().tolist())
                sel_player = f3.selectbox("Jogador", player_opt)
                if sel_player != "Todos":
                    df_view = df_view[df_view["Player Name"] == sel_player]

            if "Total Distance (m)" in df.columns:
                mn = float(df_view["Total Distance (m)"].min())
                mx = float(df_view["Total Distance (m)"].max())
                rng = st.slider("Distância total (m)", mn, mx, (mn, mx))
                df_view = df_view[df_view["Total Distance (m)"].between(*rng)]

            if "Max Speed (km/h)" in df.columns:
                mn2 = float(df_view["Max Speed (km/h)"].min())
                mx2 = float(df_view["Max Speed (km/h)"].max())
                spd = st.slider("Velocidade máxima (km/h)", mn2, mx2, (mn2, mx2))
                df_view = df_view[df_view["Max Speed (km/h)"].between(*spd)]

        st.write(f"**{len(df_view):,} jogadores** exibidos")
        st.dataframe(df_view[[c for c in df_view.columns if c != "_arquivo"]], use_container_width=True)

        csv_dl = df_view.to_csv(index=False, sep=";").encode("utf-8")
        st.download_button("⬇️ Baixar tabela filtrada (.csv)", csv_dl,
                           "dados_filtrados.csv", "text/csv")


# ════════════════════════════════════════════════════════════════════════════
# ABA 3 — Análise Física (coração do app)
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    df = st.session_state.df
    render_kpis(df)
    if df.empty:
        st.info("Carregue arquivos na aba **Upload** primeiro.")
    else:
        st.header("Análise Física — EPTS FIFA WC 2026")

        zone_cols = [v for v in SPEED_ZONES.values() if v in df.columns]
        full_zones = len(zone_cols) == len(SPEED_ZONES)
        has_result = "Resultado" in df.columns and df["Resultado"].notna().any()
        has_position = "Posição" in df.columns and df["Posição"].notna().any()

        # ── filtros globais (valem para todas as análises) ───────────────────
        fa, fb, fc, fd = st.columns(4)
        df_a = df.copy()
        if "Team Name" in df.columns:
            teams_a = ["Todas"] + sorted(df["Team Name"].dropna().unique().tolist())
            sel_a = fa.selectbox("Seleção", teams_a, key="an_team")
            if sel_a != "Todas":
                df_a = df_a[df_a["Team Name"] == sel_a]
        if "Match ID" in df.columns:
            match_a = ["Todas"] + sorted(df_a["Match ID"].dropna().astype(str).unique().tolist())
            sel_m = fb.selectbox("Partida", match_a, key="an_match")
            if sel_m != "Todas":
                df_a = df_a[df_a["Match ID"].astype(str) == sel_m]
        if has_result:
            res_opts = [r for r in RESULT_ORDER if r in df_a["Resultado"].dropna().unique()]
            sel_r = fc.multiselect("Resultado", res_opts, default=res_opts, key="an_result")
            if sel_r:
                df_a = df_a[df_a["Resultado"].isin(sel_r)]
        if has_position:
            pos_opts = [p for p in POSITION_ORDER if p in df_a["Posição"].dropna().unique()]
            sel_p = fd.multiselect(
                "Posição", pos_opts, default=pos_opts, key="an_pos",
                format_func=lambda p: POSITION_LABELS.get(p, p),
            )
            if sel_p:
                df_a = df_a[df_a["Posição"].isin(sel_p)]

        st.caption(
            "ℹ️ Por padrão as comparações usam **intensidade por minuto (m/min)**, "
            "para não confundir volume com efeito de substituição (quem é substituído "
            "joga menos minutos)."
        )

        # ── métricas derivadas (intensidade e eficiência) ────────────────────
        df_a = add_derived(df_a)
        raw_metrics, derived_metrics, all_metrics, intensity_metrics = metric_lists(df_a)
        ZONE_LABELS = list(SPEED_ZONES.keys())

        st.divider()
        charts_pdf = []

        sub_tabs = st.tabs([
            "📊 Visão geral",
            "🏟️ Torneio (benchmark)",
            "🏆 Por resultado",
            "🧍 Por posição",
            "🧠 Avançado",
            "👤 Jogador",
        ])

        # ===================================================================
        # VISÃO GERAL
        # ===================================================================
        with sub_tabs[0]:
            st.caption("Para comparar **seleções**, use a aba **🏟️ Torneio** "
                       "(totais absolutos da equipe, no estilo do benchmark da FIFA).")

            if full_zones and "Player Name" in df_a.columns:
                # agrega por jogador (MÉDIA por jogo) — evita somar partidas do
                # mesmo nome no eixo X (que dava distâncias impossíveis >20 km)
                ngames = (df_a.groupby("Player Name")["Match ID"].nunique()
                          if "Match ID" in df_a.columns else None)
                multi = ngames is not None and ngames.max() > 1
                st.subheader("🏃 Zonas de velocidade por jogador"
                             + (" — média por jogo (top 30)" if multi else " (top 30)"))
                zmean = df_a.groupby("Player Name")[zone_cols].mean()
                zmean["_tot"] = zmean.sum(axis=1)
                dz = zmean.sort_values("_tot", ascending=False).head(30).reset_index()
                fig_zones = go.Figure()
                for (label, col), color in zip(SPEED_ZONES.items(), ZONE_COLORS):
                    fig_zones.add_trace(go.Bar(name=label, x=dz["Player Name"],
                                               y=dz[col], marker_color=color))
                fig_zones.update_layout(
                    barmode="stack", xaxis_tickangle=-45,
                    yaxis_title="Metros (média por jogo)" if multi else "Metros",
                    legend=dict(orientation="h", y=-0.4), height=520)
                st.plotly_chart(fig_zones, use_container_width=True)
                if multi:
                    st.caption("Jogadores com mais de uma partida entram com a **média por jogo** "
                               "(não a soma) — por isso nenhuma barra passa de ~13 km.")
                charts_pdf.append(("Zonas de velocidade por jogador", None))

            st.subheader("🏅 Rankings")
            rank_cols = [c for c in ["Distância/min", "Max Speed (km/h)", "Sprint/min"]
                         if c in df_a.columns]
            if rank_cols and "Player Name" in df_a.columns:
                cols = st.columns(len(rank_cols))
                for box, mc in zip(cols, rank_cols):
                    top = (df_a[["Player Name", "Team Name", mc]]
                           .dropna(subset=[mc]).nlargest(10, mc))
                    box.markdown(f"**Top 10 — {mc}**")
                    box.dataframe(top.reset_index(drop=True), hide_index=True,
                                  use_container_width=True)

            if {"Distância/min", "Max Speed (km/h)", "Player Name"}.issubset(df_a.columns):
                st.subheader("🔵 Intensidade × Velocidade máxima")
                opts = ((["Resultado"] if has_result else [])
                        + (["Posição (nome)"] if has_position else []) + ["Seleção"])
                cor = st.radio("Colorir por", opts, horizontal=True, key="vg_scat")
                if cor == "Resultado":
                    cc, cmap = "Resultado", RESULT_COLORS
                elif cor == "Posição (nome)":
                    cc, cmap = "Posição (nome)", None
                else:
                    cc, cmap = ("Team Name" if "Team Name" in df_a.columns else None), None
                hov = [c for c in ["Team Name", "Resultado", "Posição (nome)", "# Sprints"]
                       if c in df_a.columns]
                size_col = "Sprint/min" if "Sprint/min" in df_a.columns else None
                need = ["Distância/min", "Max Speed (km/h)"] + ([size_col] if size_col else [])
                ds = df_a.dropna(subset=need)
                if ds.empty:
                    st.info("Sem jogadores com dados suficientes para o gráfico.")
                else:
                    fig_s = px.scatter(ds, x="Distância/min", y="Max Speed (km/h)",
                                       color=cc, color_discrete_map=cmap,
                                       hover_name="Player Name", hover_data=hov,
                                       size=size_col, size_max=18,
                                       title="Intensidade (m/min) × Velocidade máxima")
                    st.plotly_chart(fig_s, use_container_width=True)
                    charts_pdf.append(("Intensidade × Velocidade máxima", None))

        # ===================================================================
        # TORNEIO (benchmark estilo FIFA — totais absolutos por equipe)
        # ===================================================================
        with sub_tabs[1]:
            if "Team Name" not in df_a.columns or "Match ID" not in df_a.columns:
                st.info("Dados insuficientes para o benchmark por seleção.")
            else:
                st.subheader("🏟️ Benchmark de equipe (totais absolutos)")
                st.caption(
                    "Total **da equipe** (soma de todos os jogadores) por partida — não a média "
                    "por jogador. Barra = média entre as partidas da seleção; pontos = cada "
                    "partida; linha tracejada = média do conjunto. "
                    "Referência: Bradley (2024), Biology of Sport 41(1):271–278."
                )

                bench_defs = []
                if "Total Distance (m)" in df_a.columns:
                    bench_defs.append(("Distância total", "Total Distance (m)", "km", 1000))
                if "Z4+Z5 (m)" in df_a.columns:
                    bench_defs.append(("Alta intensidade Z4+Z5 (≥20 km/h)", "Z4+Z5 (m)", "m", 1))
                if "25+ km/h (m)" in df_a.columns:
                    bench_defs.append(("Sprint Z5 (≥25 km/h)", "25+ km/h (m)", "m", 1))

                if not bench_defs:
                    st.info("Colunas de distância não encontradas.")
                else:
                    pick = st.selectbox("Métrica de equipe", [b[0] for b in bench_defs],
                                        key="trn_metric")
                    _, col, unit, div = next(b for b in bench_defs if b[0] == pick)

                    tm = (df_a.groupby(["Team Name", "Match ID"])[col].sum() / div).reset_index()
                    tm.rename(columns={col: "val"}, inplace=True)
                    team_stat = (tm.groupby("Team Name")["val"]
                                 .agg(media="mean", desvio="std", jogos="count")
                                 .reset_index().sort_values("media", ascending=False))
                    team_stat["CV"] = team_stat["desvio"] / team_stat["media"] * 100
                    avg = team_stat["media"].mean()

                    order = team_stat["Team Name"].tolist()
                    code_map = {t: team_code(t) for t in order}
                    codes = [code_map[t] for t in order]

                    fig_b = go.Figure()
                    fig_b.add_trace(go.Bar(
                        x=codes, y=team_stat["media"], marker_color="#7a1f3d",
                        text=team_stat["media"].round(1), textposition="outside",
                        name="Média", hovertext=team_stat["Team Name"],
                    ))
                    fig_b.add_trace(go.Scatter(
                        x=tm["Team Name"].map(code_map), y=tm["val"], mode="markers",
                        marker=dict(color="#f0a500", size=7,
                                    line=dict(color="#7a1f3d", width=1)),
                        name="Por partida", hovertext=tm["Team Name"],
                    ))
                    fig_b.add_hline(y=avg, line_dash="dot", line_color="black",
                                    annotation_text=f"Média {avg:.1f} {unit}",
                                    annotation_position="top right")
                    fig_b.update_layout(
                        title=f"{pick} por seleção ({unit})",
                        yaxis_title=f"{pick} ({unit})", height=470, xaxis_tickangle=-60,
                        legend=dict(orientation="h", y=1.1),
                    )
                    st.plotly_chart(fig_b, use_container_width=True)
                    charts_pdf.append((f"Benchmark — {pick}", None))

                    cv_ok = team_stat.dropna(subset=["CV"])
                    if not cv_ok.empty:
                        cmin = cv_ok.loc[cv_ok["CV"].idxmin()]
                        cmax = cv_ok.loc[cv_ok["CV"].idxmax()]
                        cc1, cc2 = st.columns(2)
                        cc1.metric(f"Mais consistente — {cmin['Team Name']}",
                                   f"CV {cmin['CV']:.1f}%")
                        cc2.metric(f"Mais variável — {cmax['Team Name']}",
                                   f"CV {cmax['CV']:.1f}%")
                    else:
                        st.caption("ℹ️ O coeficiente de variação (CV) entre partidas aparece "
                                   "quando uma seleção tiver ≥ 2 jogos carregados.")

                if {"Total Distance (m)", "Z4+Z5 (m)", "25+ km/h (m)"}.issubset(df_a.columns):
                    st.divider()
                    st.subheader("🗺️ Mapa de quadrantes (com bandeiras)")
                    st.caption("Cada seleção posicionada pelo total da equipe. As linhas marcam "
                               "as médias do conjunto, dividindo em quadrantes (alto/baixo).")

                    agg_t = (df_a.groupby(["Team Name", "Match ID"])
                             .agg(td=("Total Distance (m)", "sum"),
                                  z45=("Z4+Z5 (m)", "sum"),
                                  z5=("25+ km/h (m)", "sum")).reset_index())
                    team_xy = (agg_t.groupby("Team Name")
                               .agg(td=("td", "mean"), z45=("z45", "mean"),
                                    z5=("z5", "mean")).reset_index())
                    for c in ["td", "z45", "z5"]:
                        team_xy[c] /= 1000  # km

                    def quad_chart(ycol, ylab):
                        mx, my = team_xy["td"].mean(), team_xy[ycol].mean()
                        xr = (team_xy["td"].max() - team_xy["td"].min()) or 1
                        yr = (team_xy[ycol].max() - team_xy[ycol].min()) or 1
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=team_xy["td"], y=team_xy[ycol], mode="text",
                            text=[team_code(t) for t in team_xy["Team Name"]],
                            textposition="bottom center", textfont=dict(size=9),
                            hovertext=team_xy["Team Name"], name="",
                        ))
                        for _, rr in team_xy.iterrows():
                            url = flag_url(rr["Team Name"])
                            if url:
                                fig.add_layout_image(dict(
                                    source=url, x=rr["td"], y=rr[ycol],
                                    sizex=xr * 0.05, sizey=yr * 0.07, xref="x", yref="y",
                                    xanchor="center", yanchor="middle", layer="above"))
                        fig.add_vline(x=mx, line_dash="dash", line_color="gray")
                        fig.add_hline(y=my, line_dash="dash", line_color="gray")
                        fig.update_layout(title=f"{ylab} × Distância total",
                                          xaxis_title="Distância total (km)",
                                          yaxis_title=f"{ylab} (km)", height=480,
                                          showlegend=False)
                        return fig

                    qa, qb = st.columns(2)
                    qa.plotly_chart(quad_chart("z45", "Z4+Z5 (≥20 km/h)"),
                                    use_container_width=True)
                    qb.plotly_chart(quad_chart("z5", "Z5 sprint (≥25 km/h)"),
                                    use_container_width=True)
                    charts_pdf.append(("Mapa de quadrantes (bandeiras)", None))

        # ===================================================================
        # POR RESULTADO  (#1 intensidade · #2 alta intensidade · #3 teste · #10 distribuição)
        # ===================================================================
        with sub_tabs[2]:
            df_r = df_a[df_a["Resultado"].notna()].copy() if has_result else pd.DataFrame()
            present = ([r for r in RESULT_ORDER if r in df_r["Resultado"].unique()]
                       if not df_r.empty else [])
            if not present:
                st.info("Nenhum jogador com resultado nos filtros atuais. "
                        "Ajuste os filtros ou informe o placar na aba **Upload**.")
            else:
                st.subheader("🏆 Perfil físico por resultado")
                st.caption("Cada jogador entra com o resultado da equipe na partida. "
                           "Métricas em intensidade (por minuto).")

                kpi = st.columns(len(present))
                for box, res in zip(kpi, present):
                    s = df_r[df_r["Resultado"] == res]
                    with box:
                        st.markdown(f"#### {res}")
                        st.caption(f"{s['Player Name'].nunique()} jog. · "
                                   f"{s['Team Name'].nunique()} eq.")
                        if "Distância/min" in s:
                            st.metric("Intensidade", f"{s['Distância/min'].mean():.1f} m/min")
                        if "Sprint/min" in s:
                            st.metric("Sprint", f"{s['Sprint/min'].mean():.2f} m/min")
                        if "Max Speed (km/h)" in s:
                            st.metric("Vel. máx.", f"{s['Max Speed (km/h)'].mean():.1f} km/h")

                m_res = st.selectbox("Métrica (#1/#2)", intensity_metrics or all_metrics,
                                     key="res_metric")
                agg = (df_r.groupby("Resultado")[m_res].mean()
                       .reindex(present).reset_index())
                fig_r = px.bar(agg, x="Resultado", y=m_res, color="Resultado",
                               color_discrete_map=RESULT_COLORS, text_auto=".2f",
                               title=f"Média de {m_res} por resultado")
                fig_r.update_layout(showlegend=False, height=360)
                st.plotly_chart(fig_r, use_container_width=True)
                charts_pdf.append((f"{m_res} por resultado", None))

                if full_zones:
                    rows = []
                    for res in present:
                        s = df_r[df_r["Resultado"] == res]
                        dur = s["Total Duration (min)"].replace(0, np.nan)
                        for label, col in SPEED_ZONES.items():
                            rows.append({"Resultado": res, "Zona": label,
                                         "m/min": (s[col] / dur).mean()})
                    fig_zr = px.bar(pd.DataFrame(rows), x="Zona", y="m/min",
                                    color="Resultado", color_discrete_map=RESULT_COLORS,
                                    barmode="group",
                                    title="Intensidade por zona de velocidade × resultado (#2)")
                    fig_zr.update_xaxes(tickangle=-20)
                    fig_zr.update_layout(height=420, legend=dict(orientation="h", y=-0.35))
                    st.plotly_chart(fig_zr, use_container_width=True)
                    charts_pdf.append(("Zonas (m/min) por resultado", None))

                st.markdown("##### 📦 #10 Distribuição (não só a média)")
                m_dist = st.selectbox("Métrica", intensity_metrics or all_metrics, key="res_dist")
                kind = st.radio("Tipo", ["Boxplot", "Violino"], horizontal=True, key="res_dist_kind")
                if kind == "Boxplot":
                    fig_d = px.box(df_r, x="Resultado", y=m_dist, color="Resultado",
                                   color_discrete_map=RESULT_COLORS,
                                   category_orders={"Resultado": present}, points="outliers",
                                   title=f"Distribuição de {m_dist} por resultado")
                else:
                    fig_d = px.violin(df_r, x="Resultado", y=m_dist, color="Resultado",
                                      color_discrete_map=RESULT_COLORS,
                                      category_orders={"Resultado": present}, box=True,
                                      points=False,
                                      title=f"Distribuição de {m_dist} por resultado")
                fig_d.update_layout(showlegend=False, height=420)
                st.plotly_chart(fig_d, use_container_width=True)

                st.markdown("##### 🔬 #3 Vitória × Derrota: diferença real ou acaso?")
                if "Vitória" in present and "Derrota" in present:
                    rows = []
                    for m in (intensity_metrics or all_metrics):
                        a = df_r[df_r["Resultado"] == "Vitória"][m]
                        b = df_r[df_r["Resultado"] == "Derrota"][m]
                        p, delta = mann_whitney(a, b)
                        rows.append({
                            "Métrica": m,
                            "Mediana Vitória": round(a.median(), 2),
                            "Mediana Derrota": round(b.median(), 2),
                            "Cliff's δ": round(delta, 2) if not np.isnan(delta) else np.nan,
                            "Efeito": interpret_effect(delta),
                            "p-valor": round(p, 4) if not np.isnan(p) else np.nan,
                            "Signif. (p<0,05)": "✅" if (not np.isnan(p) and p < 0.05) else "—",
                        })
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                    st.caption("Teste de Mann-Whitney (não-paramétrico). Cliff's δ mede o tamanho "
                               "do efeito (0 = sem diferença; ±1 = separação total). Com poucos "
                               "jogos, p-valores devem ser lidos com cautela.")
                else:
                    st.info("É preciso ter jogadores de **Vitória** e **Derrota** no filtro atual.")

        # ===================================================================
        # POR POSIÇÃO  (#2 por posição · #4 z-score · #10 distribuição)
        # ===================================================================
        with sub_tabs[3]:
            if not has_position:
                st.info("Sem informação de posição para os dados carregados.")
            else:
                dfp = df_a[df_a["Posição"].notna()].copy()
                pos_present = [p for p in POSITION_ORDER if p in dfp["Posição"].unique()]

                st.subheader("🧍 Perfil físico por posição")
                m_pos = st.selectbox("Métrica", intensity_metrics or all_metrics, key="pos_metric")
                agg = dfp.groupby("Posição")[m_pos].mean().reindex(pos_present).reset_index()
                agg["Posição"] = agg["Posição"].map(POSITION_LABELS)
                fig_p = px.bar(agg, x="Posição", y=m_pos, color="Posição",
                               text_auto=".2f", title=f"Média de {m_pos} por posição")
                fig_p.update_layout(showlegend=False, height=360)
                st.plotly_chart(fig_p, use_container_width=True)
                charts_pdf.append((f"{m_pos} por posição", None))

                if full_zones:
                    rows = []
                    for p in pos_present:
                        s = dfp[dfp["Posição"] == p]
                        dur = s["Total Duration (min)"].replace(0, np.nan)
                        for label, col in SPEED_ZONES.items():
                            rows.append({"Posição": POSITION_LABELS[p], "Zona": label,
                                         "m/min": (s[col] / dur).mean()})
                    fig_pz = px.bar(pd.DataFrame(rows), x="Zona", y="m/min", color="Posição",
                                    barmode="group",
                                    title="Intensidade por zona de velocidade × posição (#2)")
                    fig_pz.update_xaxes(tickangle=-20)
                    fig_pz.update_layout(height=420, legend=dict(orientation="h", y=-0.35))
                    st.plotly_chart(fig_pz, use_container_width=True)
                    charts_pdf.append(("Zonas (m/min) por posição", None))

                st.markdown("##### 📐 #4 Outliers físicos por posição (z-score)")
                st.caption("Cada jogador comparado aos da MESMA posição. "
                           "z = desvios-padrão acima (+) ou abaixo (−) da média da posição.")
                m_z = st.selectbox("Métrica", intensity_metrics or all_metrics, key="pos_z")
                g = dfp.groupby("Posição")[m_z]
                dfp["_z"] = ((dfp[m_z] - g.transform("mean")) / g.transform("std")) \
                    .replace([np.inf, -np.inf], np.nan)
                show = dfp.dropna(subset=["_z"]).copy()
                show["z-score"] = show["_z"].round(2)
                cshow = ["Player Name", "Team Name", "Posição (nome)", m_z, "z-score"]
                c1, c2 = st.columns(2)
                c1.markdown("**Acima da média da posição**")
                c1.dataframe(show.nlargest(10, "_z")[cshow].reset_index(drop=True),
                             hide_index=True, use_container_width=True)
                c2.markdown("**Abaixo da média da posição**")
                c2.dataframe(show.nsmallest(10, "_z")[cshow].reset_index(drop=True),
                             hide_index=True, use_container_width=True)

                st.markdown("##### 📦 #10 Distribuição por posição")
                m_pd = st.selectbox("Métrica", intensity_metrics or all_metrics, key="pos_dist")
                fig_pd = px.box(dfp.assign(Pos=dfp["Posição"].map(POSITION_LABELS)),
                                x="Pos", y=m_pd, color="Pos", points="outliers",
                                title=f"Distribuição de {m_pd} por posição")
                fig_pd.update_layout(showlegend=False, height=420)
                st.plotly_chart(fig_pd, use_container_width=True)

        # ===================================================================
        # AVANÇADO  (#5 eficiência · #6 densidade · #7 clustering · #8 correlação · #9 benchmark)
        # ===================================================================
        with sub_tabs[4]:
            st.subheader("⚡ #5 Eficiência de sprint")
            if {"m por sprint", "# Sprints", "Sprint (m)"}.issubset(df_a.columns):
                st.caption("Metros por sprint = comprimento típico do sprint (qualidade) "
                           "vs. número de sprints (quantidade).")
                de = df_a.dropna(subset=["# Sprints", "m por sprint", "Sprint (m)"])
                de = de[de["Sprint (m)"] >= 0]
                fig_eff = px.scatter(de, x="# Sprints", y="m por sprint",
                                     color="Posição (nome)" if has_position else None,
                                     hover_name="Player Name", size="Sprint (m)", size_max=18,
                                     title="Quantidade × comprimento dos sprints")
                st.plotly_chart(fig_eff, use_container_width=True)
                charts_pdf.append(("Eficiência de sprint", None))
            else:
                st.info("Métricas de sprint indisponíveis.")

            st.subheader("💥 #6 Densidade explosiva")
            dens = [c for c in ["Sprints/min", "Speed runs/min"] if c in df_a.columns]
            if dens and "Player Name" in df_a.columns:
                m_de = st.selectbox("Métrica de densidade", dens, key="adv_dens")
                top = df_a[["Player Name", "Team Name", m_de]].dropna().nlargest(15, m_de)
                fig_de = px.bar(top, x="Player Name", y=m_de, title=f"Top 15 — {m_de}")
                fig_de.update_xaxes(tickangle=-45)
                st.plotly_chart(fig_de, use_container_width=True)
                charts_pdf.append((f"Densidade explosiva — {m_de}", None))

            st.subheader("🧬 #7 Perfis físicos (clustering)")
            st.caption("Agrupa jogadores com comportamento físico parecido (k-means sobre "
                       "métricas padronizadas; projeção PCA em 2D).")
            feats = [c for c in intensity_metrics if df_a[c].notna().sum() > 5]
            if len(feats) >= 2 and len(df_a) >= 6:
                k = st.slider("Número de perfis (k)", 2, 6, 3, key="adv_k")
                base = df_a.dropna(subset=feats).copy()
                if len(base) >= k:
                    try:
                        from sklearn.preprocessing import StandardScaler
                        from sklearn.cluster import KMeans
                        from sklearn.decomposition import PCA
                        X = StandardScaler().fit_transform(base[feats])
                        km = KMeans(n_clusters=k, n_init=10, random_state=42)
                        base["Perfil"] = "P" + (km.fit_predict(X) + 1).astype(str)
                        pca = PCA(n_components=2).fit_transform(X)
                        base["_pc1"], base["_pc2"] = pca[:, 0], pca[:, 1]
                        fig_cl = px.scatter(
                            base, x="_pc1", y="_pc2", color="Perfil", hover_name="Player Name",
                            hover_data=[c for c in ["Team Name", "Posição (nome)"]
                                        if c in base.columns],
                            labels={"_pc1": "Componente 1", "_pc2": "Componente 2"},
                            title="Perfis físicos (projeção PCA 2D)")
                        st.plotly_chart(fig_cl, use_container_width=True)
                        prof = base.groupby("Perfil")[feats].mean().round(2)
                        prof.insert(0, "Jogadores", base.groupby("Perfil").size())
                        st.markdown("**Perfil médio de cada grupo**")
                        st.dataframe(prof, use_container_width=True)
                        charts_pdf.append(("Clustering de perfis físicos", None))
                    except Exception as e:
                        st.warning(f"Não foi possível rodar o clustering: {e}")
                else:
                    st.info("Poucos jogadores para esse número de perfis.")
            else:
                st.info("Dados insuficientes para clustering.")

            st.subheader("📈 #8 O que se associa a vencer?")
            if has_result and "Pontos" in df_a.columns and intensity_metrics:
                st.caption("Correlação de Spearman entre a média de cada métrica por equipe e os "
                           "pontos (3 vitória / 1 empate / 0 derrota).")
                team_agg = (df_a.dropna(subset=["Pontos"])
                            .groupby(["Team Name", "Match ID"])
                            .agg({**{m: "mean" for m in intensity_metrics}, "Pontos": "first"})
                            .reset_index())
                if len(team_agg) >= 4:
                    corr = (team_agg[intensity_metrics + ["Pontos"]]
                            .corr(method="spearman")["Pontos"].drop("Pontos").sort_values())
                    fig_corr = px.bar(x=corr.values, y=corr.index, orientation="h",
                                      labels={"x": "ρ de Spearman", "y": ""},
                                      color=corr.values, color_continuous_scale="RdBu",
                                      range_color=[-1, 1],
                                      title="Correlação (Spearman) com pontos")
                    st.plotly_chart(fig_corr, use_container_width=True)
                    st.caption(f"n = {len(team_agg)} equipes-jogo. Correlação não implica "
                               "causalidade; amostra pequena exige cautela.")
                    charts_pdf.append(("Correlação com resultado", None))
                else:
                    st.info("Carregue mais partidas para esta análise (mín. 4 equipes-jogo).")
            else:
                st.info("Sem dados de resultado para correlacionar.")

            st.subheader("🎯 #9 Benchmark vs torneio")
            if "Team Name" in df.columns and intensity_metrics:
                st.caption("Percentil de uma seleção comparada às demais carregadas.")
                try:
                    base_team = add_derived(df).groupby("Team Name")[intensity_metrics].mean()
                    if len(base_team) >= 3:
                        team_sel = st.selectbox("Seleção", sorted(base_team.index), key="adv_bm")
                        pct = base_team.rank(pct=True).loc[team_sel] * 100
                        bm = pd.DataFrame({"Métrica": pct.index, "Percentil": pct.values.round(0)})
                        fig_bm = px.bar(bm, x="Percentil", y="Métrica", orientation="h",
                                        range_x=[0, 100], color="Percentil",
                                        color_continuous_scale="Greens",
                                        title=f"{team_sel} — percentil por métrica")
                        fig_bm.add_vline(x=50, line_dash="dash", line_color="gray")
                        st.plotly_chart(fig_bm, use_container_width=True)
                        charts_pdf.append((f"Benchmark — {team_sel}", None))
                    else:
                        st.info("Carregue ao menos 3 seleções para o benchmark.")
                except Exception:
                    st.info("Benchmark indisponível para os dados atuais.")

        # ===================================================================
        # JOGADOR
        # ===================================================================
        with sub_tabs[5]:
            if "Player Name" in df_a.columns and full_zones:
                st.subheader("👤 Perfil individual")
                jog = st.selectbox("Jogador", sorted(df_a["Player Name"].dropna().unique()),
                                   key="pl_sel")
                row = df_a[df_a["Player Name"] == jog].iloc[0]
                pos_lbl = row.get("Posição (nome)") if pd.notna(row.get("Posição (nome)")) else "—"
                camisa = int(row["Jersey #"]) if pd.notna(row.get("Jersey #")) else "—"
                st.caption(f"{row.get('Team Name','')} · {pos_lbl} · camisa {camisa}")
                pcols = st.columns(4)
                pcols[0].metric("Distância", f"{row.get('Total Distance (m)', 0):,.0f} m")
                pcols[1].metric("Intensidade", f"{row.get('Distância/min', float('nan')):.1f} m/min")
                pcols[2].metric("Vel. máx.", f"{row.get('Max Speed (km/h)', 0):.1f} km/h")
                pcols[3].metric("Sprints", f"{int(row.get('# Sprints', 0))}")

                dur = row.get("Total Duration (min)", np.nan)
                vals = [row[c] / dur if dur else 0 for c in zone_cols]
                fig_rad = go.Figure(go.Scatterpolar(r=vals, theta=ZONE_LABELS,
                                                    fill="toself", line_color="#e53935"))
                fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True)),
                                      title=f"Perfil de zonas (m/min) — {jog}", height=400)
                st.plotly_chart(fig_rad, use_container_width=True)
                charts_pdf.append((f"Perfil individual — {jog}", None))

                if has_position and pd.notna(row.get("Posição")):
                    peers = df_a[df_a["Posição"] == row["Posição"]]
                    st.markdown(f"**Percentil entre {POSITION_LABELS.get(row['Posição'])}s "
                                f"(n={len(peers)})**")
                    prow = {}
                    for m in intensity_metrics:
                        if m in peers and peers[m].notna().sum() > 1 and pd.notna(row.get(m)):
                            prow[m] = round((peers[m] < row[m]).mean() * 100)
                    if prow:
                        pbar = pd.DataFrame({"Métrica": list(prow.keys()),
                                             "Percentil": list(prow.values())})
                        fig_pp = px.bar(pbar, x="Percentil", y="Métrica", orientation="h",
                                        range_x=[0, 100], color="Percentil",
                                        color_continuous_scale="Blues")
                        fig_pp.add_vline(x=50, line_dash="dash", line_color="gray")
                        st.plotly_chart(fig_pp, use_container_width=True)
            else:
                st.info("Dados insuficientes para o perfil individual.")

        st.session_state.charts_pdf = charts_pdf


# ════════════════════════════════════════════════════════════════════════════
# ABA ✨ — Destaques (recursos premium)
# ════════════════════════════════════════════════════════════════════════════
with tab_dest:
    df0 = st.session_state.df
    render_kpis(df0)
    if df0.empty:
        st.info("Carregue arquivos na aba **Upload** primeiro.")
    elif "Team Name" not in df0.columns:
        st.info("Os dados carregados não têm coluna de seleção.")
    else:
        d = add_derived(df0)
        raw_m, der_m, all_m, int_m = metric_lists(d)
        teams_all = sorted(d["Team Name"].dropna().unique())
        has_pos = "Posição" in d.columns and d["Posição"].notna().any()
        has_res = "Resultado" in d.columns and d["Resultado"].notna().any()
        full = all(c in d.columns for c in SPEED_ZONES.values())

        dsub = st.tabs([
            "📝 Scout Report", "🧬 DNA & Confronto", "🆚 Comparador",
            "🐝 Distribuição", "📈 Evolução", "🔮 Preditivo",
        ])

        # ---- #1 SCOUT REPORT ------------------------------------------------
        with dsub[0]:
            st.subheader("📝 Scout Report automático")
            st.caption("Resumo em texto do perfil físico da seleção, pronto para a comissão técnica.")
            t = st.selectbox("Seleção", teams_all, key="scout_team")
            md = scout_report(df0, t)
            st.markdown(md)
            st.download_button("⬇️ Baixar relatório (.md)", md.encode("utf-8"),
                               f"scout_{team_code(t)}.md", "text/markdown")

        # ---- #3 DNA + #4 CONFRONTO -----------------------------------------
        with dsub[1]:
            st.subheader("🧬 DNA físico da seleção")
            techprof = team_technical_profiles(teams_all)
            sel = []
            if not int_m or len(teams_all) < 2:
                st.info("Carregue mais seleções para comparar o DNA físico.")
            else:
                teamagg = d.groupby("Team Name")[int_m].mean()
                pctagg = teamagg.rank(pct=True) * 100
                sel = st.multiselect("Seleções (até 3)", teams_all,
                                     default=teams_all[:2], max_selections=3, key="dna_sel")
                if sel:
                    figd = go.Figure()
                    for tn in sel:
                        figd.add_trace(go.Scatterpolar(
                            r=pctagg.loc[tn].values, theta=int_m, fill="toself",
                            name=team_code(tn)))
                    figd.update_layout(
                        polar=dict(radialaxis=dict(range=[0, 100], visible=True)),
                        title="DNA físico — percentil no torneio (0–100)", height=460)
                    st.plotly_chart(figd, use_container_width=True)
                    st.caption("Quanto mais para a borda, mais alto o percentil da seleção "
                               "naquela métrica em relação às demais carregadas.")

                    # DNA técnico-tático — mesmo conceito de percentil, outra esfera
                    tr = [c for c in TECH_RADAR if c in techprof.columns]
                    if tr and any(t in techprof.index for t in sel):
                        st.markdown("**🧠 DNA técnico-tático — percentil no torneio**")
                        tpct = techprof[tr].rank(pct=True) * 100
                        figt = go.Figure()
                        for tn in sel:
                            if tn in tpct.index:
                                figt.add_trace(go.Scatterpolar(
                                    r=tpct.loc[tn].values, theta=tr, fill="toself",
                                    name=team_code(tn)))
                        figt.update_layout(
                            polar=dict(radialaxis=dict(range=[0, 100], visible=True)),
                            height=460)
                        st.plotly_chart(figt, use_container_width=True)
                        st.caption("Perfil técnico-tático médio da seleção nos seus jogos. "
                                   "Cruzado com o radar físico acima: o time é mais 'motor' "
                                   "(corre/sprinta) ou mais 'cérebro' (posse/xG/progressão)?")

            st.divider()
            st.subheader("⚔️ Simulador de confronto")
            duo = sel[:2]
            if len(duo) < 2:
                st.info("Selecione **duas** seleções no DNA físico acima — elas entram "
                        "automaticamente aqui no confronto.")
            else:
                ta, tb = duo[0], duo[1]
                if len(sel) > 2:
                    st.caption(f"Usando as duas primeiras seleções: "
                               f"**{team_code(ta)}** e **{team_code(tb)}**.")
                ca, cb = team_code(ta), team_code(tb)
                st.markdown(f"### {ca} × {cb}")
                st.caption("Um gráfico por variável — todas as métricas de intensidade.")

                metrics_mu = int_m or all_m
                summ = []
                cols = st.columns(2)
                for i, m in enumerate(metrics_mu):
                    if has_pos:
                        rows = []
                        for p in POSITION_ORDER:
                            va = d[(d["Team Name"] == ta) & (d["Posição"] == p)][m].mean()
                            vb = d[(d["Team Name"] == tb) & (d["Posição"] == p)][m].mean()
                            rows.append({"Posição": POSITION_LABELS[p], ca: va, cb: vb})
                        mu = pd.DataFrame(rows)
                        figm = px.bar(mu.melt(id_vars="Posição", var_name="Seleção",
                                              value_name=m),
                                      x="Posição", y=m, color="Seleção", barmode="group",
                                      color_discrete_sequence=["#7a1f3d", "#f0a500"], title=m)
                    else:
                        va = d[d["Team Name"] == ta][m].mean()
                        vb = d[d["Team Name"] == tb][m].mean()
                        figm = px.bar(pd.DataFrame({"Seleção": [ca, cb], m: [va, vb]}),
                                      x="Seleção", y=m, color="Seleção",
                                      color_discrete_sequence=["#7a1f3d", "#f0a500"], title=m)
                    figm.update_layout(height=330, showlegend=(i == 0),
                                       margin=dict(t=46, b=8, l=8, r=8),
                                       title_font_size=14)
                    figm.update_xaxes(tickangle=-15)
                    cols[i % 2].plotly_chart(figm, use_container_width=True)

                    wa = d[d["Team Name"] == ta][m].mean()
                    wb = d[d["Team Name"] == tb][m].mean()
                    if pd.notna(wa) and pd.notna(wb):
                        summ.append({"Variável": m, ca: round(wa, 2), cb: round(wb, 2),
                                     "Vantagem": ca if wa > wb else cb})

                if summ:
                    sdf = pd.DataFrame(summ)
                    st.markdown("**Resumo — vantagem por variável**")
                    st.dataframe(sdf, hide_index=True, use_container_width=True)
                    wa_n = int((sdf["Vantagem"] == ca).sum())
                    wb_n = int((sdf["Vantagem"] == cb).sum())
                    champ = ca if wa_n > wb_n else cb
                    st.success(f"**Vantagem física geral: {champ}** "
                               f"({max(wa_n, wb_n)} de {len(sdf)} variáveis)")

                    # ===== camada TÉCNICO-TÁTICA do confronto =====
                    if not techprof.empty and ta in techprof.index and tb in techprof.index:
                        st.divider()
                        st.markdown("**🧠 Resumo técnico-tático — vantagem por variável**")
                        tt = []
                        for m in TECH_RADAR + ["Field tilt (%)"]:
                            if m not in techprof.columns:
                                continue
                            va, vb = techprof.loc[ta, m], techprof.loc[tb, m]
                            if pd.notna(va) and pd.notna(vb):
                                tt.append({"Variável": m, ca: round(va, 1), cb: round(vb, 1),
                                           "Vantagem": ca if va > vb else cb})
                        if "PPDA" in techprof.columns and pd.notna(techprof.loc[ta, "PPDA"]) \
                                and pd.notna(techprof.loc[tb, "PPDA"]):
                            va, vb = techprof.loc[ta, "PPDA"], techprof.loc[tb, "PPDA"]
                            tt.append({"Variável": "PPDA (↓ = + pressão)", ca: round(va, 1),
                                       cb: round(vb, 1), "Vantagem": ca if va < vb else cb})
                        tdf = pd.DataFrame(tt)
                        st.dataframe(tdf, hide_index=True, use_container_width=True)
                        ta_n = int((tdf["Vantagem"] == ca).sum())
                        tb_n = int((tdf["Vantagem"] == cb).sum())
                        tchamp = ca if ta_n >= tb_n else cb
                        st.caption("Médias dos jogos da seleção. **PPDA** = passes do adversário "
                                   "por pressão (menor = pressão mais intensa). **Field tilt** = "
                                   "domínio territorial (recepções no terço final vs o rival).")

                        st.markdown("**🎭 Choque de estilos (fases de jogo)**")
                        for title, phs in [("⚔️ Com a bola", PHASE_IN),
                                           ("🛡️ Sem a bola", PHASE_OUT)]:
                            ph = [c for c in phs if c in techprof.columns
                                  and pd.notna(techprof.loc[ta, c])
                                  and pd.notna(techprof.loc[tb, c])]
                            if not ph:
                                continue
                            dfp = pd.DataFrame({"Fase": ph,
                                                ca: [techprof.loc[ta, c] for c in ph],
                                                cb: [techprof.loc[tb, c] for c in ph]})
                            figp = px.bar(dfp.melt(id_vars="Fase", var_name="Seleção",
                                                   value_name="%"),
                                          x="Fase", y="%", color="Seleção", barmode="group",
                                          color_discrete_sequence=["#7a1f3d", "#f0a500"],
                                          title=title)
                            figp.update_layout(height=360, xaxis_tickangle=-30, xaxis_title="")
                            st.plotly_chart(figp, use_container_width=True)

                        st.markdown("#### 🧭 Leitura do confronto (dois eixos)")
                        st.info(f"**Físico:** vantagem **{champ}** ({max(wa_n, wb_n)}/{len(sdf)}) "
                                f"· **Técnico-tático:** vantagem **{tchamp}** "
                                f"({max(ta_n, tb_n)}/{len(tdf)}).")
                        if champ == tchamp:
                            st.success(f"**{champ} leva nas duas esferas** — físico e jogo "
                                       "apontam para o mesmo lado; favorito claro no papel.")
                        else:
                            st.warning(f"**Choque de perfis:** **{champ}** impõe o físico, "
                                       f"**{tchamp}** controla o jogo. O confronto se decide em "
                                       "quem dita o ritmo — leia o choque de fases acima.")

        # ---- #17 COMPARADOR DE JOGADORES -----------------------------------
        with dsub[2]:
            st.subheader("🆚 Comparador de jogadores")
            if "Player Name" not in d.columns or not int_m:
                st.info("Dados insuficientes.")
            else:
                players = sorted(d["Player Name"].dropna().unique())
                c1, c2 = st.columns(2)
                pa = c1.selectbox("Jogador A", players, key="cmp_a")
                pb = c2.selectbox("Jogador B", players,
                                  index=min(1, len(players) - 1), key="cmp_b")
                ra = d[d["Player Name"] == pa].iloc[0]
                rb = d[d["Player Name"] == pb].iloc[0]
                pa_pct = [pct_vs(ra[m], d[m]) for m in int_m]
                pb_pct = [pct_vs(rb[m], d[m]) for m in int_m]
                figc = go.Figure()
                figc.add_trace(go.Scatterpolar(r=pa_pct, theta=int_m, fill="toself",
                                               name=pa, line_color="#7a1f3d"))
                figc.add_trace(go.Scatterpolar(r=pb_pct, theta=int_m, fill="toself",
                                               name=pb, line_color="#f0a500"))
                figc.update_layout(polar=dict(radialaxis=dict(range=[0, 100], visible=True)),
                                   title="Percentil por métrica (vs todos os jogadores)",
                                   height=460)
                st.plotly_chart(figc, use_container_width=True)
                st.markdown("##### Comparação por variável")
                comp_rows = []
                cols = st.columns(2)
                for i, m in enumerate(int_m):
                    va, vb = ra.get(m), rb.get(m)
                    figm = px.bar(pd.DataFrame({"Jogador": [pa, pb], m: [va, vb]}),
                                  x="Jogador", y=m, color="Jogador",
                                  color_discrete_sequence=["#7a1f3d", "#f0a500"], title=m)
                    figm.update_layout(height=300, showlegend=False,
                                       margin=dict(t=44, b=8, l=8, r=8), title_font_size=14)
                    cols[i % 2].plotly_chart(figm, use_container_width=True)
                    win = pa if (pd.notna(va) and pd.notna(vb) and va > vb) else (
                        pb if pd.notna(vb) else "—")
                    comp_rows.append({"Métrica": m, pa: round(va, 2) if pd.notna(va) else None,
                                      pb: round(vb, 2) if pd.notna(vb) else None,
                                      "Vantagem": win})
                sdf = pd.DataFrame(comp_rows)
                st.markdown("**Resumo — vantagem por variável**")
                st.dataframe(sdf, hide_index=True, use_container_width=True)
                wa_n = int((sdf["Vantagem"] == pa).sum())
                wb_n = int((sdf["Vantagem"] == pb).sum())
                if wa_n or wb_n:
                    champ = pa if wa_n >= wb_n else pb
                    st.success(f"**Mais completo fisicamente: {champ}** "
                               f"({max(wa_n, wb_n)} de {len(sdf)} variáveis)")

        # ---- BEESWARM / DISTRIBUIÇÃO ---------------------------------------
        with dsub[3]:
            st.subheader("🐝 Distribuição (beeswarm)")
            st.caption("Cada ponto é um jogador — revela a dispersão real, não só a média.")
            groups = ([("Resultado", "Resultado")] if has_res else []) + \
                     ([("Posição (nome)", "Posição")] if has_pos else [])
            if not groups or not int_m:
                st.info("Carregue dados com resultado/posição.")
            else:
                gcol = st.radio("Agrupar por", [g[1] for g in groups], horizontal=True,
                                key="bee_group")
                gfield = dict((g[1], g[0]) for g in groups)[gcol]
                bmetric = st.selectbox("Métrica", int_m, key="bee_metric")
                dd = d.dropna(subset=[gfield, bmetric])
                figb = px.strip(dd, x=gfield, y=bmetric, color=gfield,
                                stripmode="overlay", hover_name="Player Name",
                                color_discrete_map=RESULT_COLORS if gfield == "Resultado" else None,
                                title=f"Distribuição de {bmetric} por {gcol}")
                figb.update_traces(jitter=0.35, marker=dict(size=6, opacity=0.7))
                figb.update_layout(height=460, showlegend=False)
                st.plotly_chart(figb, use_container_width=True)

        # ---- EVOLUÇÃO / BUMP CHART -----------------------------------------
        with dsub[4]:
            st.subheader("📈 Evolução do ranking ao longo da Copa")
            st.caption("Fica mais rico a cada rodada que você carregar. Ranking por jogo "
                       "acumulado de cada seleção.")
            tt = team_match_totals(d, ["Total Distance (m)", "Z4+Z5 (m)", "25+ km/h (m)"])
            if tt.empty:
                st.info("Dados insuficientes.")
            else:
                bm_lbl = {"Distância total": "Total Distance (m)"}
                if "Z4+Z5 (m)" in tt.columns:
                    bm_lbl["Alta intensidade Z4+Z5"] = "Z4+Z5 (m)"
                if "25+ km/h (m)" in tt.columns:
                    bm_lbl["Sprint Z5"] = "25+ km/h (m)"
                pick = st.selectbox("Métrica", list(bm_lbl), key="bump_metric")
                col = bm_lbl[pick]
                tt = tt.copy()
                date_map = {mid: (match_entry(d, mid)[0] or {}).get("date")
                            for mid in tt["Match ID"].unique()}
                tt["data"] = tt["Match ID"].map(date_map)
                tt["data"] = pd.to_datetime(tt["data"], format="%d/%m/%Y", errors="coerce")
                # quem não tem data cai para a ordem do Match ID
                tt["data"] = tt["data"].fillna(
                    pd.to_datetime("2026-01-01") + pd.to_timedelta(
                        tt["Match ID"].rank(method="dense").fillna(0), unit="D"))
                tt = tt.sort_values(["Team Name", "data"])
                tt["jogo"] = tt.groupby("Team Name").cumcount() + 1
                tt["acum"] = tt.groupby("Team Name")[col].transform(
                    lambda s: s.expanding().mean())
                tt["rank"] = tt.groupby("jogo")["acum"].rank(ascending=False, method="min")
                figbump = px.line(tt, x="jogo", y="rank", color="Team Name",
                                  markers=False, hover_name="Team Name",
                                  title=f"Ranking acumulado — {pick}")
                jmin, jmax = tt["jogo"].min(), tt["jogo"].max()
                nrank = tt["rank"].max()
                # eixos com folga p/ as bandeiras não cortarem nas bordas
                figbump.update_xaxes(title="Jogo da seleção", dtick=1,
                                     range=[jmin - 0.35, jmax + 0.35])
                figbump.update_yaxes(title="Posição no ranking",
                                     range=[nrank + 0.6, 0.4])  # invertido (1 no topo)
                # bandeira de cada seleção em cada ponto (no lugar do marcador)
                xspan = max(jmax - jmin, 1)
                nteams = tt["Team Name"].nunique()
                # altura da bandeira = fração de UMA posição (não do span todo),
                # para nunca sobrepor as vizinhas
                sx, sy = xspan * 0.045, 0.85
                for _, r in tt.iterrows():
                    url = flag_url(r["Team Name"])
                    if url:
                        figbump.add_layout_image(dict(
                            source=url, x=r["jogo"], y=r["rank"],
                            sizex=sx, sizey=sy, xref="x", yref="y",
                            xanchor="center", yanchor="middle", layer="above"))
                # cresce com o nº de seleções p/ dar espaço a cada bandeira
                alt = int(max(560, 34 * nteams))
                figbump.update_layout(height=alt, showlegend=(nteams <= 12))
                st.plotly_chart(figbump, use_container_width=True)
                if tt["jogo"].max() == 1:
                    st.info("Com apenas 1 rodada o ranking é estático. Suba as próximas "
                            "rodadas para ver as seleções subindo e descendo. 📈")

        # ---- MODELO PREDITIVO ----------------------------------------------
        with dsub[5]:
            st.subheader("🔮 O físico prevê o resultado?")
            if not has_res or not int_m:
                st.info("É preciso ter resultado e métricas físicas.")
            else:
                tagg = (d.dropna(subset=["Resultado"])
                        .groupby(["Team Name", "Match ID"])
                        .agg({**{m: "mean" for m in int_m},
                              "Resultado": "first"}).reset_index())
                tagg["venceu"] = (tagg["Resultado"] == "Vitória").astype(int)
                n, npos = len(tagg), tagg["venceu"].sum()
                if n < 10 or npos < 3 or npos > n - 3:
                    st.info(f"Amostra pequena/desbalanceada (n={n}, vitórias={npos}). "
                            "Carregue mais partidas.")
                else:
                    try:
                        from sklearn.preprocessing import StandardScaler
                        from sklearn.linear_model import LogisticRegression
                        from sklearn.model_selection import cross_val_score
                        from sklearn.pipeline import make_pipeline
                        X, y = tagg[int_m].fillna(tagg[int_m].mean()), tagg["venceu"]
                        pipe = make_pipeline(StandardScaler(),
                                             LogisticRegression(max_iter=1000))
                        acc = cross_val_score(pipe, X, y, cv=5, scoring="accuracy").mean()
                        pipe.fit(X, y)
                        coef = pipe.named_steps["logisticregression"].coef_[0]
                        cdf = (pd.DataFrame({"Métrica": int_m, "Peso": coef})
                               .sort_values("Peso"))
                        st.metric("Acurácia (validação cruzada 5-fold)", f"{acc*100:.0f}%",
                                  help="Base de comparação: chutar sempre 'não venceu' acertaria "
                                       f"{max(npos, n-npos)/n*100:.0f}%.")
                        figp = px.bar(cdf, x="Peso", y="Métrica", orientation="h",
                                      color="Peso", color_continuous_scale="RdBu",
                                      title="Peso de cada métrica para prever vitória")
                        figp.add_vline(x=0, line_color="gray")
                        st.plotly_chart(figp, use_container_width=True)
                        st.caption("Peso positivo (azul) = associada a vencer; negativo (vermelho) "
                                   "= associada a não vencer. Modelo ilustrativo — amostra pequena "
                                   "exige muita cautela; não é relação de causa e efeito.")
                    except Exception as e:
                        st.warning(f"Não foi possível treinar o modelo: {e}")


# ════════════════════════════════════════════════════════════════════════════
# ABA 🧩 — Análise Contextual (físico × técnico-tático)
# ════════════════════════════════════════════════════════════════════════════
with tab_ctx:
    df0 = st.session_state.df
    render_kpis(df0)
    if df0.empty:
        st.info("Carregue arquivos na aba **Upload** primeiro.")
    else:
        ctx, ctx_xcols, ctx_ycols = build_context_table(df0)
        if ctx.empty or not ctx_ycols:
            st.info("Sem dados técnico-táticos para cruzar nestes jogos. O técnico vem dos "
                    "relatórios PMSR da FIFA (posse, xG, finalizações…) — disponível para a "
                    "maioria dos jogos da fase de grupos.")
        else:
            cdf = ctx[ctx[ctx_ycols].notna().any(axis=1)].copy()
            st.header("🧩 Análise Contextual — físico × técnico-tático")
            st.caption(f"{len(cdf)} equipes-jogo com dados técnicos (posse, xG, finalizações, "
                       "passes, line breaks, pressão, turnovers) cruzados com o físico de "
                       "equipe. Fonte técnica: relatório oficial PMSR da FIFA.")
            csub = st.tabs(["🏆 O que vence", "⚡ Eficiência", "📊 Perfil por quadrante",
                            "🔵 Dispersão + correlação", "🌡️ Matriz de correlação",
                            "🎯 Fases de jogo"])

            # variáveis testáveis (exclui as que DEFINEM o resultado)
            metric_all = [c for c in ctx_xcols + ctx_ycols
                          if c not in ("Gols feitos", "Gols sofridos", "Pontos")]
            has_res = "Resultado" in cdf.columns and cdf["Resultado"].notna().any()

            # 0) O QUE VENCE — effect sizes (Vit×Der) + diferencial vs adversário
            with csub[0]:
                if not has_res:
                    st.info("Defina os placares (aba Upload) para esta análise por resultado.")
                else:
                    st.subheader("🏅 O que separa quem vence de quem perde")
                    win = cdf[cdf["Resultado"] == "Vitória"]
                    los = cdf[cdf["Resultado"] == "Derrota"]
                    rows = []
                    for c in metric_all:
                        a = pd.to_numeric(win[c], errors="coerce").dropna().values
                        b = pd.to_numeric(los[c], errors="coerce").dropna().values
                        if len(a) < 5 or len(b) < 5:
                            continue
                        p, d = mann_whitney(a, b)
                        rows.append({"Variável": c, "delta": d, "p": p,
                                     "sig": bool(pd.notna(p) and p < 0.05)})
                    ef = (pd.DataFrame(rows, columns=["Variável", "delta", "p", "sig"])
                          .dropna(subset=["delta"]).sort_values("delta"))
                    if not ef.empty:
                        ef["rótulo"] = np.where(ef["sig"], "★ " + ef["Variável"], ef["Variável"])
                        ef["dir"] = np.where(ef["delta"] >= 0, "Mais em vitórias", "Mais em derrotas")
                        fig = px.bar(ef, x="delta", y="rótulo", orientation="h", color="dir",
                                     color_discrete_map={"Mais em vitórias": "#f0a500",
                                                         "Mais em derrotas": "#7a1f3d"},
                                     labels={"delta": "Cliff's δ (Vitória vs Derrota)", "rótulo": ""},
                                     title="Tamanho de efeito por variável  (★ = p<0,05)")
                        fig.update_layout(height=max(360, 22 * len(ef)), legend_title="")
                        fig.add_vline(x=0, line_color="gray")
                        st.plotly_chart(fig, use_container_width=True)
                        sig = ef[ef["sig"]].copy()
                        sig["abs"] = sig["delta"].abs()
                        sig = sig.sort_values("abs", ascending=False)
                        if len(sig):
                            top = " · ".join(f"{r['Variável']} (δ={r['delta']:+.2f})"
                                             for _, r in sig.head(6).iterrows())
                            st.success(f"**Diferenciam com significância (p<0,05):** {top}")
                        else:
                            st.info("Nenhuma variável atinge p<0,05 — amostra pequena; "
                                    "leia os δ como tendências, não como prova.")
                        st.caption(f"δ>0 (dourado) = maior em vitórias. |δ|: 0,15 pequeno · 0,33 médio "
                                   f"· 0,47 grande. n={len(win)} vitórias × {len(los)} derrotas.")

                    st.markdown("---")
                    st.subheader("⚖️ Diferencial vs adversário → saldo de gols")
                    st.caption("Para cada jogo, a diferença contra o adversário daquele jogo "
                               "(1 linha por partida). Como ambos dividem o mesmo contexto, o Δ é "
                               "um sinal limpo do que realmente pesa no placar.")
                    diff = context_diff(ctx, metric_all).drop_duplicates("Match ID")
                    dcols = [c for c in diff.columns if c.startswith("Δ ")]
                    if not diff.empty and diff["ΔGols"].notna().any():
                        from scipy.stats import spearmanr
                        rr = []
                        for c in dcols:
                            s = diff[[c, "ΔGols"]].dropna()
                            if len(s) < 6:
                                continue
                            rho, pp = spearmanr(s[c], s["ΔGols"])
                            rr.append({"Variável": c[2:], "rho": rho,
                                       "sig": bool(pd.notna(pp) and pp < 0.05)})
                        rk = (pd.DataFrame(rr, columns=["Variável", "rho", "sig"])
                              .dropna(subset=["rho"]).sort_values("rho"))
                        if not rk.empty:
                            rk["rótulo"] = np.where(rk["sig"], "★ Δ" + rk["Variável"],
                                                    "Δ" + rk["Variável"])
                            fig = px.bar(rk, x="rho", y="rótulo", orientation="h", color="rho",
                                         color_continuous_scale="RdBu", range_color=[-0.6, 0.6],
                                         labels={"rho": "Spearman(Δvariável, Δgols)", "rótulo": ""},
                                         title="O que — feito melhor que o rival — vira saldo (★ p<0,05)")
                            fig.update_layout(height=max(360, 22 * len(rk)), coloraxis_showscale=False)
                            fig.add_vline(x=0, line_color="gray")
                            st.plotly_chart(fig, use_container_width=True)
                        pickd = st.selectbox("Ver dispersão de um diferencial",
                                             [c[2:] for c in dcols], key="ctx_diff_pick")
                        col = "Δ " + pickd
                        s = diff[[col, "ΔGols", "Resultado", "Sigla"]].dropna(subset=[col, "ΔGols"])
                        if len(s) >= 4:
                            rho, pp = spearmanr(s[col], s["ΔGols"])
                            fig = px.scatter(s, x=col, y="ΔGols", color="Resultado",
                                             color_discrete_map=RESULT_COLORS, hover_name="Sigla",
                                             title=f"Δ{pickd} × saldo de gols  (ρ={rho:.2f}, p={pp:.3f}, n={len(s)})")
                            fig.add_vline(x=0, line_color="gray")
                            fig.add_hline(y=0, line_color="gray")
                            fig.update_layout(height=460)
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Sem saldo de gols disponível para o diferencial.")

            # 1) EFICIÊNCIA — custo físico do produto tático
            with csub[1]:
                st.subheader("⚡ Eficiência: custo físico do produto tático")
                st.caption("Quanto de esforço físico cada produto técnico custou — separa quem é "
                           "eficiente de quem 'corre muito para pouco'.")
                e = cdf.copy()
                specs = [
                    ("m alta intensidade / progressão", "Z4+Z5 (km)", "Progressões", 1000, "menor = melhor"),
                    ("m alta intensidade / line break", "Z4+Z5 (km)", "Line breaks", 1000, "menor = melhor"),
                    ("m alta intensidade / finalização", "Z4+Z5 (km)", "Finalizações", 1000, "menor = melhor"),
                    ("xG por km de Z4+Z5", "xG", "Z4+Z5 (km)", 1, "maior = melhor"),
                    ("Pressões por km", "Pressões def.", "Dist. total (km)", 1, "densidade de pressão"),
                    ("Finalizações por 100 passes", "Finalizações", "Passes", 100, "maior = mais direto"),
                ]
                effcols = []
                for name, a, b, k, _ in specs:
                    if a in e.columns and b in e.columns:
                        num = pd.to_numeric(e[a], errors="coerce")
                        den = pd.to_numeric(e[b], errors="coerce").replace(0, np.nan)
                        e[name] = num / den * k
                        effcols.append(name)
                if not effcols:
                    st.info("Faltam variáveis para calcular eficiência.")
                else:
                    pick = st.selectbox("Métrica de eficiência", effcols, key="ctx_eff")
                    note = next(s[4] for s in specs if s[0] == pick)
                    st.caption(f"**{pick}** — interpretação: _{note}_.")
                    asc = "menor" in note
                    cc1, cc2 = st.columns(2)
                    if has_res:
                        agg = (e.dropna(subset=[pick]).groupby("Resultado")[pick].mean()
                               .reindex(["Vitória", "Empate", "Derrota"]).dropna().reset_index())
                        fig = px.bar(agg, x="Resultado", y=pick, color="Resultado",
                                     color_discrete_map=RESULT_COLORS,
                                     title="Média por resultado")
                        fig.update_layout(showlegend=False, height=380)
                        cc1.plotly_chart(fig, use_container_width=True)
                    rank = (e.dropna(subset=[pick])[["Sigla", pick]]
                            .sort_values(pick, ascending=asc).head(12))
                    figr = px.bar(rank, x=pick, y="Sigla", orientation="h",
                                  color_discrete_sequence=["#f0a500"],
                                  title=("Mais eficientes" if asc else "Mais produtivos") + " (top 12)")
                    figr.update_layout(height=380, yaxis=dict(autorange="reversed"))
                    cc2.plotly_chart(figr, use_container_width=True)
                    st.caption("Equipe-jogo individuais; um mesmo país aparece mais de uma vez "
                               "(uma por partida).")

            # 2) PERFIL POR QUADRANTE (com Kruskal-Wallis e IC 95%)
            with csub[2]:
                st.subheader("Indicadores técnicos por perfil físico (TD × Z4+Z5)")
                st.caption("Cada equipe-jogo é classificada por distância total (TD) e por "
                           "distância em alta intensidade (Z4+Z5), abaixo/acima da mediana.")
                use_ci = st.checkbox("Barras de erro = IC 95% (em vez de desvio-padrão)",
                                     value=True, key="ctx_ci")
                base = cdf.dropna(subset=["Dist. total (km)", "Z4+Z5 (km)"]).copy()
                td_med, z_med = base["Dist. total (km)"].median(), base["Z4+Z5 (km)"].median()
                base["Perfil"] = (np.where(base["Dist. total (km)"] >= td_med, "TD alto", "TD baixo")
                                  + " / " + np.where(base["Z4+Z5 (km)"] >= z_med,
                                                     "Z4+Z5 alto", "Z4+Z5 baixo"))
                order = [o for o in ["TD baixo / Z4+Z5 baixo", "TD alto / Z4+Z5 baixo",
                                     "TD baixo / Z4+Z5 alto", "TD alto / Z4+Z5 alto"]
                         if o in base["Perfil"].unique()]
                metrics4 = [m for m in ["xG", "Gols feitos", "Gols sofridos", "Posse (%)"]
                            if m in base.columns]
                from scipy.stats import kruskal
                cols = st.columns(len(metrics4))
                for box, m in zip(cols, metrics4):
                    agg = base.dropna(subset=[m]).groupby("Perfil")[m].agg(
                        ["mean", "std", "count"]).reindex(order)
                    err = (1.96 * agg["std"] / np.sqrt(agg["count"])) if use_ci else agg["std"]
                    grps = [base[base["Perfil"] == o][m].dropna().values for o in order]
                    grps = [g for g in grps if len(g) >= 2]
                    try:
                        kwp = kruskal(*grps).pvalue if len(grps) >= 2 else np.nan
                    except Exception:
                        kwp = np.nan
                    ttl = m + (f"  (KW p={kwp:.3f})" if pd.notna(kwp) else "")
                    fig = go.Figure(go.Bar(x=order, y=agg["mean"],
                                           error_y=dict(type="data", array=err.fillna(0)),
                                           marker_color="#7a1f3d"))
                    fig.update_layout(title=ttl, height=380, xaxis_tickangle=-30,
                                      margin=dict(t=46, b=90), showlegend=False)
                    box.plotly_chart(fig, use_container_width=True)
                st.caption(f"Medianas: TD {td_med:.1f} km · Z4+Z5 {z_med:.2f} km. "
                           "KW = Kruskal-Wallis (p<0,05 ⇒ algum quadrante difere de verdade). "
                           "Barras = " + ("IC 95%." if use_ci else "desvio-padrão."))

            # 3) DISPERSÃO + CORRELAÇÃO (com correlação parcial)
            with csub[3]:
                st.subheader("Dispersão físico × técnico")
                c1, c2, c3 = st.columns(3)
                xv = c1.selectbox("Eixo X (físico / resultado)", ctx_xcols,
                                  index=min(1, len(ctx_xcols) - 1), key="ctx_x")
                yv = c2.selectbox("Eixo Y (técnico-tático)", ctx_ycols, key="ctx_y")
                ctrl_opts = ["(nenhum)"] + [c for c in ["Posse (%)", "Passes", "Dist. total (km)"]
                                            if c in cdf.columns and c not in (xv, yv)]
                ctrl = c3.selectbox("Controlar por (corr. parcial)", ctrl_opts, key="ctx_ctrl")
                sc = cdf.copy()
                sc[xv] = pd.to_numeric(sc[xv], errors="coerce")
                sc[yv] = pd.to_numeric(sc[yv], errors="coerce")
                sc = sc.dropna(subset=[xv, yv])
                if len(sc) >= 4:
                    from scipy.stats import spearmanr
                    rho, p = spearmanr(sc[xv], sc[yv])
                    ttl = f"{yv} × {xv}  (ρ={rho:.2f}, p={p:.3f}, n={len(sc)})"
                    if ctrl != "(nenhum)":
                        rp, pp, _ = partial_spearman(
                            sc[xv].values, sc[yv].values,
                            pd.to_numeric(sc[ctrl], errors="coerce").values)
                        ttl += f"  |  parcial (controle: {ctrl}) ρ={rp:.2f}, p={pp:.3f}"
                    fig = px.scatter(sc, x=xv, y=yv,
                                     color="Resultado" if "Resultado" in sc.columns else None,
                                     color_discrete_map=RESULT_COLORS, hover_name="Team Name",
                                     hover_data=["Sigla"], title=ttl)
                    mm, bb = np.polyfit(sc[xv], sc[yv], 1)
                    xs = np.array([sc[xv].min(), sc[xv].max()])
                    fig.add_trace(go.Scatter(x=xs, y=mm * xs + bb, mode="lines",
                                             line=dict(dash="dash", color="gray"),
                                             name="tendência", showlegend=False))
                    fig.update_layout(height=520)
                    st.plotly_chart(fig, use_container_width=True)
                    cap = "Cada ponto é uma equipe-jogo. Correlação não implica causalidade."
                    if ctrl != "(nenhum)":
                        cap += (f" A correlação parcial remove o efeito de {ctrl}: se ρ cai muito, "
                                f"a associação era explicada por {ctrl} (ex.: ter mais a bola).")
                    st.caption(cap)
                else:
                    st.info("Poucos dados para o gráfico.")

            # 4) MATRIZ DE CORRELAÇÃO
            with csub[4]:
                st.subheader("Matriz de correlação (físico × técnico)")
                allv = ctx_xcols + ctx_ycols
                default = [v for v in ["Dist. total (km)", "Z4+Z5 (km)", "# Sprints", "Pontos",
                                       "xG", "Posse (%)", "Finalizações", "Passes", "Pressões def."]
                           if v in allv]
                pick = st.multiselect("Variáveis", allv, default=default, key="ctx_corr")
                if len(pick) >= 2:
                    cm = cdf[pick].apply(pd.to_numeric, errors="coerce").corr(method="spearman")
                    fig = px.imshow(cm, text_auto=".2f", aspect="auto",
                                    color_continuous_scale="RdBu", zmin=-1, zmax=1,
                                    title="Correlação de Spearman (físico × técnico)")
                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("Azul = relação positiva; vermelho = negativa. "
                               "Ex.: ver se mais alta intensidade anda junto com mais xG/pressão.")
                else:
                    st.info("Selecione ao menos 2 variáveis.")

            # 4) FASES DE JOGO POR RESULTADO
            with csub[5]:
                st.subheader("Distribuição de fases de jogo por resultado")
                IN_PH = ["Construção livre (%)", "Construção pressionada (%)",
                         "Progressão fase (%)", "Ataque terço final (%)", "Bola longa (%)",
                         "Transição ofensiva (%)", "Contra-ataque (%)", "Bola parada (%)"]
                OUT_PH = ["Pressão alta (%)", "Pressão média (%)", "Pressão baixa (%)",
                          "Bloco alto (%)", "Bloco médio (%)", "Bloco baixo (%)",
                          "Recuperação (%)", "Transição defensiva (%)", "Counter-press (%)"]
                in_ph = [c for c in IN_PH if c in cdf.columns and cdf[c].notna().any()]
                out_ph = [c for c in OUT_PH if c in cdf.columns and cdf[c].notna().any()]
                has_res = "Resultado" in cdf.columns and cdf["Resultado"].notna().any()
                if not in_ph and not out_ph:
                    st.info("Sem dados de fases de jogo nestes jogos.")
                elif not has_res:
                    st.info("Defina os placares (aba Upload) para comparar fases por resultado.")
                else:
                    st.caption("Média do % de tempo em cada fase, por resultado. "
                               "Lê o estilo: quem vence pressiona mais alto? constrói mais livre? "
                               "Fonte: 'Phases of Play' do PMSR da FIFA.")
                    for title, phs in [("⚔️ Com a bola (in-possession)", in_ph),
                                       ("🛡️ Sem a bola (out-of-possession)", out_ph)]:
                        if not phs:
                            continue
                        lng = cdf.dropna(subset=["Resultado"]).melt(
                            id_vars=["Resultado"], value_vars=phs,
                            var_name="Fase", value_name="pct")
                        lng["pct"] = pd.to_numeric(lng["pct"], errors="coerce")
                        agg = lng.groupby(["Fase", "Resultado"])["pct"].mean().reset_index()
                        fig = px.bar(agg, x="Fase", y="pct", color="Resultado", barmode="group",
                                     color_discrete_map=RESULT_COLORS, title=title,
                                     labels={"pct": "% médio do tempo"},
                                     category_orders={"Fase": phs,
                                                      "Resultado": ["Vitória", "Empate", "Derrota"]})
                        fig.update_layout(height=430, xaxis_tickangle=-30, xaxis_title="")
                        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# ABA 4 — Transformar
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    df = st.session_state.df
    render_kpis(df)
    if df.empty:
        st.info("Carregue arquivos na aba **Upload** primeiro.")
    else:
        st.header("Transformações e cálculos personalizados")
        num_cols_t = [c for c in NUMERIC_COLS if c in df.columns]
        all_cols_t = [c for c in df.columns if c not in ("_arquivo",)]

        op = st.selectbox("Operação", [
            "Criar nova coluna (operação entre colunas numéricas)",
            "Calcular % da distância em sprint (25+ km/h)",
            "Agrupar por seleção e agregar",
            "Remover coluna",
            "Renomear coluna",
        ])

        if op == "Criar nova coluna (operação entre colunas numéricas)":
            c1, c2 = st.columns(2)
            col_a = c1.selectbox("Coluna A", num_cols_t, key="ta")
            col_b = c1.selectbox("Coluna B", num_cols_t, key="tb")
            oper  = c2.selectbox("Operação", ["A + B", "A - B", "A × B", "A ÷ B"])
            nome  = c2.text_input("Nome da nova coluna", "nova_coluna")
            if st.button("Criar coluna"):
                try:
                    if oper == "A + B":   st.session_state.df[nome] = df[col_a] + df[col_b]
                    elif oper == "A - B": st.session_state.df[nome] = df[col_a] - df[col_b]
                    elif oper == "A × B": st.session_state.df[nome] = df[col_a] * df[col_b]
                    elif oper == "A ÷ B": st.session_state.df[nome] = df[col_a] / df[col_b].replace(0, float("nan"))
                    st.session_state.log.append(f"Nova coluna '{nome}': {col_a} {oper[-3:]} {col_b}")
                    st.success(f"Coluna '{nome}' criada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        elif op == "Calcular % da distância em sprint (25+ km/h)":
            if "25+ km/h (m)" in df.columns and "Total Distance (m)" in df.columns:
                st.session_state.df["% Sprint"] = (
                    df["25+ km/h (m)"] / df["Total Distance (m)"] * 100
                ).round(2)
                st.session_state.log.append("Coluna '% Sprint' criada (sprint / dist. total × 100)")
                st.success("Coluna '% Sprint' criada!")
                st.rerun()
            else:
                st.error("Colunas necessárias não encontradas.")

        elif op == "Agrupar por seleção e agregar":
            if "Team Name" not in df.columns:
                st.warning("Coluna 'Team Name' não encontrada.")
            else:
                agg_col = st.selectbox("Coluna para calcular", num_cols_t)
                func    = st.selectbox("Função", ["soma", "média", "máximo", "mínimo", "contagem"])
                func_map = {"soma": "sum", "média": "mean", "máximo": "max", "mínimo": "min", "contagem": "count"}
                if st.button("Agrupar"):
                    res = df.groupby("Team Name")[agg_col].agg(func_map[func]).reset_index()
                    res.columns = ["Team Name", f"{func}_{agg_col}"]
                    st.session_state.df = res
                    st.session_state.log.append(f"Agrupado por seleção — {func} de '{agg_col}'")
                    st.success("Agrupamento aplicado!")
                    st.rerun()

        elif op == "Remover coluna":
            col_rm = st.selectbox("Coluna", all_cols_t)
            if st.button("Remover"):
                st.session_state.df = df.drop(columns=[col_rm])
                st.session_state.log.append(f"Coluna '{col_rm}' removida")
                st.success("Removida!")
                st.rerun()

        elif op == "Renomear coluna":
            col_old = st.selectbox("Coluna original", all_cols_t)
            col_new = st.text_input("Novo nome")
            if st.button("Renomear") and col_new:
                st.session_state.df = df.rename(columns={col_old: col_new})
                st.session_state.log.append(f"'{col_old}' → '{col_new}'")
                st.success("Renomeada!")
                st.rerun()

        st.divider()
        st.subheader("Dados atuais")
        st.dataframe(st.session_state.df[[c for c in st.session_state.df.columns
                                          if c != "_arquivo"]].head(25), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# ABA 5 — Relatório PDF
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    df = st.session_state.df
    render_kpis(df)
    if df.empty:
        st.info("Carregue arquivos na aba **Upload** primeiro.")
    else:
        st.header("Gerar Relatório PDF")
        num_cols_r = [c for c in NUMERIC_COLS if c in df.columns]

        st.subheader("Resumo Estatístico")
        if num_cols_r:
            stats = df[num_cols_r].describe().round(2)
            st.dataframe(stats, use_container_width=True)
        else:
            stats = pd.DataFrame()

        st.subheader("Operações registradas")
        if st.session_state.log:
            for item in st.session_state.log:
                st.write(f"• {item}")
        else:
            st.write("Nenhuma transformação registrada.")

        n_charts = len(st.session_state.charts_pdf)
        st.info(
            f"{'Nenhum gráfico' if n_charts == 0 else f'{n_charts} gráfico(s)'} "
            "da aba **Análise Física** serão incluídos no PDF. "
            "Visite essa aba para gerar/atualizar os gráficos antes de exportar.",
            icon="📊",
        )

        if st.button("⬇️ Gerar e baixar PDF"):
            with st.spinner("Montando o PDF…"):
                try:
                    pdf_bytes = build_pdf(
                        df, stats,
                        st.session_state.charts_pdf,
                        st.session_state.log,
                    )
                    st.download_button(
                        label="📥 Clique aqui para baixar o PDF",
                        data=pdf_bytes,
                        file_name=f"FIFA_WC2026_Physical_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                    )
                    st.success("PDF gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

        st.divider()
        st.subheader("🎨 Infográfico de uma seleção (1 página)")
        if "Team Name" in df.columns:
            teams_ig = sorted(df["Team Name"].dropna().unique())
            tig = st.selectbox("Seleção", teams_ig, key="ig_team")
            if st.button("⬇️ Gerar infográfico"):
                with st.spinner("Montando o infográfico…"):
                    try:
                        ig = build_team_infographic(df, tig)
                        st.download_button(
                            "📥 Baixar infográfico (PDF)", ig,
                            file_name=f"infografico_{team_code(tig)}.pdf",
                            mime="application/pdf",
                        )
                        st.success("Infográfico gerado!")
                    except Exception as e:
                        st.error(f"Erro ao gerar infográfico: {e}")
        else:
            st.caption("Carregue dados com seleção para gerar o infográfico.")
