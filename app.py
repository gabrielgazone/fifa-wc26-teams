import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
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
    151626: {
        "home": "AUSTRALIA", "away": "TÜRKIYE", "score": "2–0",
        "date": "13/06/2026", "group": "D", "round": "Fase de Grupos",
        "stadium": "BC Place (Vancouver Stadium)", "city": "Vancouver",
        "country": "Canadá", "capacity": 48_821,
        "surface": "Grama natural", "roof": "Teto retrátil",
        "note": "Único estádio do torneio com Final da Copa do Mundo Feminina (2015). "
                "Inaugurado em 1983; maior cobertura retrátil do tipo no mundo.",
    },
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


def fig_to_png(fig) -> bytes:
    return pio.to_image(fig, format="png", width=1000, height=480)


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

    # gráficos
    for title, img_bytes in charts:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 9, title, ln=True)
        pdf.image(io.BytesIO(img_bytes), x=10, w=190)

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
    st.image(
        "https://upload.wikimedia.org/wikipedia/en/thumb/2/27/2026_FIFA_World_Cup_emblem.svg/220px-2026_FIFA_World_Cup_emblem.svg.png",
        width=120,
    )
    st.markdown("### FIFA World Cup 2026")
    st.caption("Canada · México · EUA · 48 seleções · 104 jogos")
    st.divider()
    st.markdown("**🏟️ Estádios do torneio**")
    st.caption("Clique para expandir")
    for nome, s in STADIUM_DB.items():
        with st.expander(f"{s['city']} — {nome.split('(')[0].strip()}"):
            st.write(f"**País:** {s['country']}")
            st.write(f"**Capacidade:** {s['capacity']:,}")
            st.write(f"**Jogos:** {s['matches_hosted']}")
            st.write(f"**Superfície:** {s['surface']}")
            st.write(f"**Cobertura:** {s.get('roof', '—')}")
            if s.get("note"):
                st.caption(s["note"])
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
            st.session_state.df = pd.concat(frames, ignore_index=True)
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
                    with st.container(border=True):
                        left, right = st.columns([2, 1])
                        with left:
                            st.markdown(
                                f"### {info['home']} {info['score']} {info['away']}"
                            )
                            st.caption(
                                f"📅 {info['date']}  ·  {info['round']} — Grupo {info['group']}  ·  Match ID: {mid_int}"
                            )
                            st.markdown(
                                f"**🏟️ Estádio:** {info['stadium']}  \n"
                                f"**📍 Cidade:** {info['city']}, {info['country']}  \n"
                                f"**👥 Capacidade:** {info['capacity']:,} pessoas  \n"
                                f"**🌿 Superfície:** {info['surface']}  ·  **🔲 Cobertura:** {info['roof']}"
                            )
                            if info.get("note"):
                                st.info(info["note"], icon="ℹ️")
                else:
                    st.caption(f"Match ID {mid_int} — informações do estádio não disponíveis na base local.")

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

        # ── filtro rápido de seleção/partida ─────────────────────────────────
        fa, fb = st.columns(2)
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

        st.divider()
        charts_pdf = []

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
            try:
                charts_pdf.append(("Distância por zona de velocidade", fig_to_png(fig_zones)))
            except Exception:
                pass

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
            try:
                charts_pdf.append((f"Média de {metric_team} por seleção", fig_to_png(fig_team)))
            except Exception:
                pass

        # ── 4. Dispersão velocidade máx × distância ───────────────────────────
        if {"Max Speed (km/h)", "Total Distance (m)", "Player Name"}.issubset(df_a.columns):
            st.subheader("🔵 Velocidade Máxima × Distância Total")
            color_col = "Team Name" if "Team Name" in df_a.columns else None
            fig_scat = px.scatter(
                df_a, x="Total Distance (m)", y="Max Speed (km/h)",
                color=color_col, hover_name="Player Name",
                hover_data=["# Sprints"] if "# Sprints" in df_a.columns else None,
                title="Relação entre distância percorrida e velocidade máxima",
                size="# Sprints" if "# Sprints" in df_a.columns else None,
                size_max=18,
            )
            st.plotly_chart(fig_scat, use_container_width=True)
            try:
                charts_pdf.append(("Velocidade Máxima × Distância Total", fig_to_png(fig_scat)))
            except Exception:
                pass

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
            try:
                charts_pdf.append((f"Perfil de zonas — {jogador}", fig_to_png(fig_radar)))
            except Exception:
                pass

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
