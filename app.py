import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from fpdf import FPDF
from datetime import datetime

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
        has_result = "Resultado" in df.columns and df["Resultado"].notna().any()

        # ── filtros ──────────────────────────────────────────────────────────
        fa, fb, fc = st.columns(3)
        df_a = df.copy()
        if "Team Name" in df.columns:
            teams_a = ["Todas"] + sorted(df["Team Name"].dropna().unique().tolist())
            sel_a = fa.selectbox("Filtrar seleção", teams_a, key="an_team")
            if sel_a != "Todas":
                df_a = df_a[df_a["Team Name"] == sel_a]
        if "Match ID" in df.columns:
            match_a = ["Todas"] + sorted(df_a["Match ID"].dropna().astype(str).unique().tolist())
            sel_m = fb.selectbox("Filtrar partida", match_a, key="an_match")
            if sel_m != "Todas":
                df_a = df_a[df_a["Match ID"].astype(str) == sel_m]
        if has_result:
            res_opts = [r for r in RESULT_ORDER if r in df_a["Resultado"].dropna().unique()]
            sel_r = fc.multiselect("Filtrar por resultado", res_opts, default=res_opts,
                                   key="an_result")
            if sel_r:
                df_a = df_a[df_a["Resultado"].isin(sel_r)]

        # opção de normalizar métricas por minuto jogado (comparação justa)
        normalize = False
        if "Total Duration (min)" in df_a.columns:
            normalize = st.checkbox(
                "📏 Normalizar distâncias por minuto jogado (intensidade — comparação mais justa entre quem jogou tempos diferentes)",
                value=False,
            )

        def metric_series(frame, col):
            """Retorna a coluna, opcionalmente dividida pelos minutos jogados."""
            if normalize and "(m)" in col and "Total Duration (min)" in frame.columns:
                dur = frame["Total Duration (min)"].replace(0, float("nan"))
                return frame[col] / dur
            return frame[col]

        st.divider()
        charts_pdf = []

        # ════════════════════════════════════════════════════════════════════
        # PERFIL FÍSICO POR RESULTADO (núcleo do app)
        # ════════════════════════════════════════════════════════════════════
        if has_result and df_a["Resultado"].notna().any():
            st.subheader("🏆 Perfil físico por resultado da partida")
            st.caption(
                "Compara o comportamento físico de quem **venceu**, **empatou** e **perdeu**. "
                "Cada jogador entra com o resultado da sua equipe na partida."
            )

            df_r = df_a[df_a["Resultado"].notna()].copy()
            present = [r for r in RESULT_ORDER if r in df_r["Resultado"].unique()]

            # KPIs lado a lado
            kpi_cols = st.columns(len(present))
            for col_box, res in zip(kpi_cols, present):
                sub = df_r[df_r["Resultado"] == res]
                with col_box:
                    st.markdown(f"#### {res}")
                    st.caption(f"{sub['Player Name'].nunique()} jogadores · "
                               f"{sub['Team Name'].nunique()} equipe(s)")
                    if "Total Distance (m)" in sub.columns:
                        st.metric("Dist. média/jogador",
                                  f"{metric_series(sub, 'Total Distance (m)').mean():,.0f}"
                                  f"{' m/min' if normalize else ' m'}")
                    if "Max Speed (km/h)" in sub.columns:
                        st.metric("Vel. máx. média", f"{sub['Max Speed (km/h)'].mean():.1f} km/h")
                    if "# Sprints" in sub.columns:
                        st.metric("Sprints (média)", f"{sub['# Sprints'].mean():.1f}")

            # comparativo por métrica escolhida
            metric_r = st.selectbox(
                "Métrica para comparar por resultado",
                [c for c in NUMERIC_COLS if c in df_r.columns],
                key="metric_result",
            )
            comp = df_r.copy()
            comp["_val"] = metric_series(comp, metric_r)
            agg = (comp.groupby("Resultado")["_val"].mean()
                   .reindex(present).reset_index())
            ylab = f"{metric_r}{' / min' if (normalize and '(m)' in metric_r) else ''}"
            fig_res = px.bar(
                agg, x="Resultado", y="_val", color="Resultado",
                color_discrete_map=RESULT_COLORS,
                title=f"Média de {ylab} por resultado",
                labels={"_val": ylab},
                text_auto=".1f",
            )
            fig_res.update_layout(showlegend=False, height=380)
            st.plotly_chart(fig_res, use_container_width=True)
            charts_pdf.append((f"Média de {metric_r} por resultado", None))

            # perfil de zonas de velocidade por resultado (lado a lado)
            if zone_cols:
                rows = []
                for res in present:
                    sub = df_r[df_r["Resultado"] == res]
                    for label, col in SPEED_ZONES.items():
                        if col in sub.columns:
                            rows.append({
                                "Resultado": res,
                                "Zona": label,
                                "Média (m)": metric_series(sub, col).mean(),
                            })
                df_zone_res = pd.DataFrame(rows)
                fig_zr = px.bar(
                    df_zone_res, x="Zona", y="Média (m)", color="Resultado",
                    color_discrete_map=RESULT_COLORS, barmode="group",
                    title="Distância média por zona de velocidade — vencedores × perdedores",
                )
                fig_zr.update_xaxes(tickangle=-20)
                fig_zr.update_layout(height=430, legend=dict(orientation="h", y=-0.35))
                st.plotly_chart(fig_zr, use_container_width=True)
                charts_pdf.append(("Zonas de velocidade por resultado", None))

            # tabela-resumo de todas as métricas por resultado
            with st.expander("📋 Ver tabela completa de médias por resultado"):
                num_present = [c for c in NUMERIC_COLS if c in df_r.columns]
                tabela = df_r.groupby("Resultado")[num_present].mean().reindex(present).round(1)
                st.dataframe(tabela, use_container_width=True)

            st.divider()

        # ── 1. Zonas de velocidade por jogador ───────────────────────────────
        if zone_cols and "Player Name" in df_a.columns:
            st.subheader("🏃 Distância por zona de velocidade (por jogador)")
            df_zones = df_a[["Player Name"] + zone_cols].copy()
            df_zones = df_zones.sort_values("25+ km/h (m)" if "25+ km/h (m)" in zone_cols else zone_cols[-1],
                                            ascending=False)
            fig_zones = go.Figure()
            for (label, col), color in zip(SPEED_ZONES.items(), ZONE_COLORS):
                if col in df_zones.columns:
                    fig_zones.add_trace(go.Bar(
                        name=label,
                        x=df_zones["Player Name"],
                        y=df_zones[col],
                        marker_color=color,
                    ))
            fig_zones.update_layout(
                barmode="stack",
                title="Distância acumulada por zona de velocidade",
                xaxis_tickangle=-45,
                yaxis_title="Metros",
                legend=dict(orientation="h", y=-0.3),
                height=500,
            )
            st.plotly_chart(fig_zones, use_container_width=True)
            charts_pdf.append(("Distância por zona de velocidade", None))

        # ── 2. Rankings ───────────────────────────────────────────────────────
        st.subheader("🏅 Rankings")
        r1, r2, r3 = st.columns(3)
        if "Total Distance (m)" in df_a.columns and "Player Name" in df_a.columns:
            top_dist = df_a.nlargest(10, "Total Distance (m)")[["Player Name", "Team Name", "Total Distance (m)"]]
            r1.markdown("**Top 10 — Distância total**")
            r1.dataframe(top_dist.reset_index(drop=True), hide_index=True)

        if "Max Speed (km/h)" in df_a.columns and "Player Name" in df_a.columns:
            top_spd = df_a.nlargest(10, "Max Speed (km/h)")[["Player Name", "Team Name", "Max Speed (km/h)"]]
            r2.markdown("**Top 10 — Velocidade máxima**")
            r2.dataframe(top_spd.reset_index(drop=True), hide_index=True)

        if "# Sprints" in df_a.columns and "Player Name" in df_a.columns:
            top_spr = df_a.nlargest(10, "# Sprints")[["Player Name", "Team Name", "# Sprints"]]
            r3.markdown("**Top 10 — Sprints**")
            r3.dataframe(top_spr.reset_index(drop=True), hide_index=True)

        # ── 3. Comparativo por seleção ────────────────────────────────────────
        if "Team Name" in df_a.columns and "Total Distance (m)" in df_a.columns:
            st.subheader("🌍 Comparativo entre seleções")
            metric_team = st.selectbox("Métrica", [c for c in NUMERIC_COLS if c in df_a.columns],
                                       key="metric_team")
            team_avg = df_a.groupby("Team Name")[metric_team].mean().sort_values(ascending=False).reset_index()
            fig_team = px.bar(
                team_avg, x="Team Name", y=metric_team,
                title=f"Média de {metric_team} por seleção",
                color=metric_team, color_continuous_scale="Blues",
            )
            fig_team.update_xaxes(tickangle=-30)
            st.plotly_chart(fig_team, use_container_width=True)
            charts_pdf.append((f"Média de {metric_team} por seleção", None))

        # ── 4. Dispersão velocidade máx × distância ───────────────────────────
        if {"Max Speed (km/h)", "Total Distance (m)", "Player Name"}.issubset(df_a.columns):
            st.subheader("🔵 Velocidade Máxima × Distância Total")
            cor_por = st.radio(
                "Colorir por", ["Resultado", "Seleção"] if has_result else ["Seleção"],
                horizontal=True, key="scat_color",
            )
            if cor_por == "Resultado" and has_result:
                color_col, cmap = "Resultado", RESULT_COLORS
            else:
                color_col, cmap = ("Team Name" if "Team Name" in df_a.columns else None), None
            hover_extra = [c for c in ["# Sprints", "Team Name", "Resultado"]
                           if c in df_a.columns]
            fig_scat = px.scatter(
                df_a, x="Total Distance (m)", y="Max Speed (km/h)",
                color=color_col, color_discrete_map=cmap, hover_name="Player Name",
                hover_data=hover_extra,
                title="Relação entre distância percorrida e velocidade máxima",
                size="# Sprints" if "# Sprints" in df_a.columns else None,
                size_max=18,
            )
            st.plotly_chart(fig_scat, use_container_width=True)
            charts_pdf.append(("Velocidade Máxima × Distância Total", None))

        # ── 5. Perfil individual ──────────────────────────────────────────────
        if "Player Name" in df_a.columns and zone_cols:
            st.subheader("👤 Perfil individual")
            jogador = st.selectbox("Selecionar jogador", sorted(df_a["Player Name"].dropna().unique()))
            row = df_a[df_a["Player Name"] == jogador].iloc[0]
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Distância total", f'{row.get("Total Distance (m)", 0):,.0f} m')
            p2.metric("Velocidade máx.", f'{row.get("Max Speed (km/h)", 0):.1f} km/h')
            p3.metric("Sprints", int(row.get("# Sprints", 0)))
            p4.metric("Duração", f'{row.get("Total Duration (min)", 0):.0f} min')

            zone_vals = [row.get(col, 0) for col in zone_cols]
            fig_radar = go.Figure(go.Scatterpolar(
                r=zone_vals,
                theta=list(SPEED_ZONES.keys()),
                fill="toself",
                line_color="#e53935",
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                title=f"Perfil de zonas — {jogador}",
                height=400,
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            charts_pdf.append((f"Perfil de zonas — {jogador}", None))

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
