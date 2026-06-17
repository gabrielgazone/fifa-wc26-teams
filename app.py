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
    team_code, flag_url,
)

# ── configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="FIFA WC 2026 · Physical Metrics",
    page_icon="⚽",
    layout="wide",
)

# ── banco de dados de partidas / estádios WC 2026 ────────────────────────────
# Fonte: FIFA.com + beIN Sports + CBC News (consultado jun/2026)
MATCH_DB = {
    # ── 11/06 ──
    151600: {"home": "MEXICO", "away": "SOUTH AFRICA", "home_goals": 2, "away_goals": 0,
             "score": "2–0", "date": "11/06/2026", "round": "Fase de Grupos",
             "stadium": "Estadio Azteca (Mexico City Stadium)", "city": "Cidade do México",
             "country": "México", "capacity": 80_824,
             "scorers": "Jogo de abertura da Copa do Mundo 2026.",
             "note": "Estádio de abertura — único a sediar 3 Copas (1970, 1986, 2026)."},
    151608: {"home": "KOREA REPUBLIC", "away": "CZECHIA", "home_goals": 2, "away_goals": 1,
             "score": "2–1", "date": "11/06/2026", "round": "Fase de Grupos"},
    # ── 12/06 ──
    151614: {"home": "CANADA", "away": "BOSNIA AND HERZEGOVINA", "home_goals": 1, "away_goals": 1,
             "score": "1–1", "date": "12/06/2026", "round": "Fase de Grupos",
             "stadium": "BMO Field (Toronto Stadium)", "city": "Toronto", "country": "Canadá",
             "capacity": 45_736},
    151625: {"home": "USA", "away": "PARAGUAY", "home_goals": 4, "away_goals": 1,
             "score": "4–1", "date": "12/06/2026", "round": "Fase de Grupos"},
    # ── 13/06 ──
    151619: {"home": "HAITI", "away": "SCOTLAND", "home_goals": 0, "away_goals": 1,
             "score": "0–1", "date": "13/06/2026", "round": "Fase de Grupos"},
    151626: {"home": "AUSTRALIA", "away": "TÜRKIYE", "home_goals": 2, "away_goals": 0,
             "score": "2–0", "date": "13/06/2026", "group": "D", "round": "Fase de Grupos",
             "stadium": "BC Place (Vancouver Stadium)", "city": "Vancouver",
             "country": "Canadá", "capacity": 48_821,
             "surface": "Grama natural", "roof": "Teto retrátil",
             "scorers": "Irankunda 27', Metcalfe 75' (AUS) · GK Patrick Beach: 8 defesas",
             "note": "Único estádio do torneio com Final da Copa do Mundo Feminina (2015). "
                     "Inaugurado em 1983; maior cobertura retrátil do tipo no mundo."},
    151620: {"home": "BRAZIL", "away": "MOROCCO", "home_goals": 1, "away_goals": 1,
             "score": "1–1", "date": "13/06/2026", "round": "Fase de Grupos"},
    151613: {"home": "QATAR", "away": "SWITZERLAND", "home_goals": 1, "away_goals": 1,
             "score": "1–1", "date": "13/06/2026", "round": "Fase de Grupos"},
    # ── 14/06 ──
    151632: {"home": "CÔTE D'IVOIRE", "away": "ECUADOR", "home_goals": 1, "away_goals": 0,
             "score": "1–0", "date": "14/06/2026", "round": "Fase de Grupos"},
    151631: {"home": "GERMANY", "away": "CURAÇAO", "home_goals": 7, "away_goals": 1,
             "score": "7–1", "date": "14/06/2026", "round": "Fase de Grupos",
             "note": "Maior goleada da primeira rodada."},
    151638: {"home": "NETHERLANDS", "away": "JAPAN", "home_goals": 2, "away_goals": 2,
             "score": "2–2", "date": "14/06/2026", "round": "Fase de Grupos"},
    151637: {"home": "SWEDEN", "away": "TUNISIA", "home_goals": 5, "away_goals": 1,
             "score": "5–1", "date": "14/06/2026", "round": "Fase de Grupos"},
    # ── 15/06 ──
    151650: {"home": "SAUDI ARABIA", "away": "URUGUAY", "home_goals": 1, "away_goals": 1,
             "score": "1–1", "date": "15/06/2026", "round": "Fase de Grupos"},
    151649: {"home": "SPAIN", "away": "CABO VERDE", "home_goals": 0, "away_goals": 0,
             "score": "0–0", "date": "15/06/2026", "round": "Fase de Grupos",
             "note": "Cabo Verde segurou os campeões europeus num dia histórico de 4 empates."},
    151644: {"home": "IR IRAN", "away": "NEW ZEALAND", "home_goals": 2, "away_goals": 2,
             "score": "2–2", "date": "15/06/2026", "round": "Fase de Grupos"},
    151643: {"home": "BELGIUM", "away": "EGYPT", "home_goals": 1, "away_goals": 1,
             "score": "1–1", "date": "15/06/2026", "round": "Fase de Grupos"},
}

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


def enrich_results(df: pd.DataFrame) -> pd.DataFrame:
    """Cruza Team Name + Match ID com MATCH_DB para anexar o resultado da
    partida a cada jogador (vitória/empate/derrota, gols, adversário)."""
    if "Match ID" not in df.columns or "Team Name" not in df.columns:
        return df
    df = df.copy()

    def outcome(row):
        try:
            info = MATCH_DB.get(int(row["Match ID"]))
        except (ValueError, TypeError):
            info = None
        if not info:
            return pd.Series([pd.NA] * len(RESULT_COLS), index=RESULT_COLS)
        team = str(row["Team Name"]).strip().upper()
        home, away = info["home"].strip().upper(), info["away"].strip().upper()
        hg, ag = info["home_goals"], info["away_goals"]
        if team == home:
            gf, ga, opp = hg, ag, info["away"]
        elif team == away:
            gf, ga, opp = ag, hg, info["home"]
        else:
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
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("## ⚽")
with col_title:
    st.markdown("## FIFA World Cup 2026 · Player Physical Metrics")
    st.caption(
        "Sistema EPTS — 16 câmeras ópticas por estádio · 50 Hz · até 172 M pontos de dados/jogo"
    )
st.divider()

# ── abas ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📂 Upload",
    "📋 Tabela & Filtros",
    "📊 Análise Física",
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
    if not df.empty:
        n_matches = df["Match ID"].nunique() if "Match ID" in df.columns else "—"
        teams     = df["Team Name"].nunique() if "Team Name" in df.columns else "—"
        players   = df["Player ID"].nunique() if "Player ID" in df.columns else "—"
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Partidas", n_matches)
        c2.metric("Seleções", teams)
        c3.metric("Jogadores únicos", players)
        c4.metric("Total de linhas", f"{len(df):,}")

        # ── painel de contexto por partida ────────────────────────────────
        if "Match ID" in df.columns:
            match_ids = df["Match ID"].dropna().unique().tolist()
            st.divider()
            st.subheader("🏟️ Informações das partidas")
            for mid in match_ids:
                mid_int = int(mid) if str(mid).isdigit() else mid
                info = MATCH_DB.get(mid_int)
                if info:
                    grp = f" — Grupo {info['group']}" if info.get("group") else ""
                    with st.container(border=True):
                        st.markdown(f"### {info['home']} {info['score']} {info['away']}")
                        st.caption(
                            f"📅 {info.get('date', '—')}  ·  "
                            f"{info.get('round', 'Fase de Grupos')}{grp}  ·  Match ID: {mid_int}"
                        )
                        linhas = []
                        if info.get("stadium"):
                            linhas.append(f"**🏟️ Estádio:** {info['stadium']}")
                        if info.get("city"):
                            linhas.append(
                                f"**📍 Cidade:** {info['city']}, {info.get('country', '')}".rstrip(", ")
                            )
                        if info.get("capacity"):
                            linhas.append(f"**👥 Capacidade:** {info['capacity']:,} pessoas")
                        if info.get("surface"):
                            linhas.append(
                                f"**🌿 Superfície:** {info['surface']}  ·  "
                                f"**🔲 Cobertura:** {info.get('roof', '—')}"
                            )
                        if linhas:
                            st.markdown("  \n".join(linhas))
                        if info.get("scorers"):
                            st.markdown(f"**⚽ Destaque:** {info['scorers']}")
                        if info.get("note"):
                            st.info(info["note"], icon="ℹ️")
                else:
                    st.caption(f"Match ID {mid_int} — informações da partida não disponíveis na base local.")

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
        def add_derived(frame):
            f = frame.copy()
            dur = (f["Total Duration (min)"].replace(0, np.nan)
                   if "Total Duration (min)" in f.columns else np.nan)
            if "Total Distance (m)" in f.columns:
                f["Distância/min"] = f["Total Distance (m)"] / dur
            if full_zones:
                f["HID (m)"] = (f["15-20 km/h (m)"] + f["20-25 km/h (m)"]
                                + f["25+ km/h (m)"])
                f["HID/min"] = f["HID (m)"] / dur
                f["Z4+Z5 (m)"] = f["20-25 km/h (m)"] + f["25+ km/h (m)"]
                f["Sprint (m)"] = f["25+ km/h (m)"]
                f["Sprint/min"] = f["25+ km/h (m)"] / dur
                if "Total Distance (m)" in f.columns:
                    f["% Sprint"] = (f["25+ km/h (m)"]
                                     / f["Total Distance (m)"].replace(0, np.nan) * 100)
            if "# Sprints" in f.columns:
                f["Sprints/min"] = f["# Sprints"] / dur
                if full_zones:
                    f["m por sprint"] = (f["25+ km/h (m)"]
                                         / f["# Sprints"].replace(0, np.nan))
            if "# Speed Runs" in f.columns:
                f["Speed runs/min"] = f["# Speed Runs"] / dur
            return f

        df_a = add_derived(df_a)

        raw_metrics = [c for c in NUMERIC_COLS if c in df_a.columns]
        derived_metrics = [c for c in ["Distância/min", "HID (m)", "HID/min",
                                       "Z4+Z5 (m)", "Sprint (m)", "Sprint/min", "% Sprint",
                                       "Sprints/min", "Speed runs/min", "m por sprint"]
                           if c in df_a.columns]
        all_metrics = raw_metrics + derived_metrics
        intensity_metrics = [c for c in ["Distância/min", "HID/min", "Sprint/min",
                                         "Sprints/min", "Speed runs/min",
                                         "Max Speed (km/h)", "% Sprint", "m por sprint"]
                             if c in df_a.columns]
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
                st.subheader("🏃 Zonas de velocidade por jogador (top 30 em distância)")
                dz = df_a.sort_values("Total Distance (m)", ascending=False).head(30)
                fig_zones = go.Figure()
                for (label, col), color in zip(SPEED_ZONES.items(), ZONE_COLORS):
                    fig_zones.add_trace(go.Bar(name=label, x=dz["Player Name"],
                                               y=dz[col], marker_color=color))
                fig_zones.update_layout(barmode="stack", xaxis_tickangle=-45,
                                        yaxis_title="Metros",
                                        legend=dict(orientation="h", y=-0.4), height=520)
                st.plotly_chart(fig_zones, use_container_width=True)
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
                fig_s = px.scatter(df_a, x="Distância/min", y="Max Speed (km/h)",
                                   color=cc, color_discrete_map=cmap,
                                   hover_name="Player Name", hover_data=hov,
                                   size="Sprint/min" if "Sprint/min" in df_a.columns else None,
                                   size_max=18,
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
            if not has_result:
                st.info("Sem informação de resultado para os dados carregados.")
            else:
                df_r = df_a[df_a["Resultado"].notna()].copy()
                present = [r for r in RESULT_ORDER if r in df_r["Resultado"].unique()]

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
                fig_eff = px.scatter(df_a, x="# Sprints", y="m por sprint",
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
# ABA 4 — Transformar
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    df = st.session_state.df
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
