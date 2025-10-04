import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import altair as alt
from urllib.error import URLError

# -----------------------------
# Page config & global options
# -----------------------------
st.set_page_config(
    page_title="Uber pickups in NYC — Cloud Para Dados",
    page_icon="🗽",
    layout="wide",
)

alt.data_transformers.disable_max_rows()

# -----------------------------
# Constants / defaults
# -----------------------------
DEFAULT_DATA_URL = (
    "https://s3.us-east-2.amazonaws.com/www.cloudparadados-rafael.com/uber-raw-data-sep14.csv"
)
DATE_COL_RAW = "date/time"  # as in the original tutorial after lowercase
LAT_COL = "lat"
LON_COL = "lon"
BASE_COL = "base"

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data(url: str, nrows: int | None = None) -> pd.DataFrame:
    """Load CSV from URL (or local path), normalize columns and parse datetimes.

    - Lowercases all column names
    - Parses DATE_COL_RAW to datetime tz-naive
    - Adds helper columns: hour, date, weekday
    """
    df = pd.read_csv(url, nrows=nrows)
    df.columns = [str(c).strip().lower() for c in df.columns]

    if DATE_COL_RAW not in df.columns:
        raise ValueError(
            f"Coluna '{DATE_COL_RAW}' não encontrada. Colunas disponíveis: {list(df.columns)}"
        )

    df[DATE_COL_RAW] = pd.to_datetime(df[DATE_COL_RAW], errors="coerce")
    df = df.dropna(subset=[DATE_COL_RAW, LAT_COL, LON_COL])

    # Normalize types
    df[LAT_COL] = pd.to_numeric(df[LAT_COL], errors="coerce")
    df[LON_COL] = pd.to_numeric(df[LON_COL], errors="coerce")
    df = df.dropna(subset=[LAT_COL, LON_COL])

    # Helper columns
    df.rename(columns={DATE_COL_RAW: "datetime"}, inplace=True)
    df["date"] = df["datetime"].dt.date
    df["hour"] = df["datetime"].dt.hour
    df["weekday"] = df["datetime"].dt.day_name()

    # Clean Base
    if BASE_COL in df.columns:
        df[BASE_COL] = df[BASE_COL].astype(str).str.strip().str.upper()
    else:
        df[BASE_COL] = "UNKNOWN"

    return df.reset_index(drop=True)


def kpi_card(label: str, value, help_text: str | None = None):
    """Render a small KPI card with metric-style look."""
    with st.container(border=True):
        st.caption(label)
        st.markdown(
            f"<div style='font-size: 28px; font-weight: 700; line-height:1'>{value}</div>",
            unsafe_allow_html=True,
        )
        if help_text:
            st.caption(help_text)


def get_map_layers(df: pd.DataFrame):
    # ⚠️ PyDeck precisa de dados 100% serializáveis em JSON.
    # Mantemos somente lat/lon para evitar objetos como datetime.date na serialização.
    df = df[[LAT_COL, LON_COL]].copy()
    scatter = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=[LON_COL, LAT_COL],
        get_radius=40,
        pickable=True,
        opacity=0.25,
    )
    heat = pdk.Layer(
        "HeatmapLayer",
        data=df,
        get_position=[LON_COL, LAT_COL],
        aggregation="MEAN",
        opacity=0.35,
    )
    return [heat, scatter]


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("⚙️ Configurações")
source = st.sidebar.text_input("URL do dataset", value=DEFAULT_DATA_URL, help="CSV público do tutorial da Uber")
max_rows = st.sidebar.number_input("Amostra (nrows)", min_value=1000, max_value=200000, step=1000, value=10000)

# Try data load with graceful error handling
try:
    with st.spinner("Carregando dados…"):
        df = load_data(source, int(max_rows))
except URLError as e:
    st.error(f"Não foi possível baixar a URL. Detalhes: {e}")
    st.stop()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Sidebar filters depend on data
min_date, max_date = df["datetime"].min().date(), df["datetime"].max().date()
chosen_dates = st.sidebar.date_input(
    "Período",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

hours = st.sidebar.multiselect(
    "Horas (0–23)", options=list(range(24)), default=[], help="Vazio = todas as horas"
)

bases = sorted(df[BASE_COL].unique().tolist())
base_sel = st.sidebar.multiselect("Bases", options=bases, default=[])

# -----------------------------
# Apply filters
# -----------------------------
filtered = df
if isinstance(chosen_dates, tuple) and len(chosen_dates) == 2:
    start_d, end_d = chosen_dates
    filtered = filtered[(filtered["date"] >= start_d) & (filtered["date"] <= end_d)]
if hours:
    filtered = filtered[filtered["hour"].isin(hours)]
if base_sel:
    filtered = filtered[filtered[BASE_COL].isin(base_sel)]

# URL sync (optional)
st.query_params.update({
    "start": str(min_date),
    "end": str(max_date),
})

# -----------------------------
# Header
# -----------------------------
st.title("🗽 Uber pickups in NYC — versão aprimorada")
st.markdown(
    """
    Experimento do **Bootcamp Cloud para Dados** com interface aprimorada, filtros, KPIs, gráficos interativos e mapa com *heatmap*.
    """
)

# -----------------------------
# KPIs row
# -----------------------------
col1, col2, col3, col4 = st.columns([1,1,1,1])
kpi_card("Corridas (amostra)", f"{len(filtered):,}")
with col2:
    kpi_card("Dias cobertos", filtered["date"].nunique())
with col3:
    kpi_card("Bases únicas", filtered[BASE_COL].nunique())
with col4:
    kpi_card("Janela de datas", f"{min_date} → {max_date}")

# -----------------------------
# Tabs
# -----------------------------
TAB_OVERVIEW, TAB_MAP, TAB_DATA, TAB_ABOUT = st.tabs(["📈 Visão geral", "🗺️ Mapa", "📄 Dados", "ℹ️ Sobre"])

with TAB_OVERVIEW:
    st.subheader("Distribuição por hora")
    hour_counts = (
        filtered.groupby("hour", as_index=False)
        .size()
        .rename(columns={"size": "pickups"})
        .sort_values("hour")
    )

    chart = (
        alt.Chart(hour_counts)
        .mark_bar()
        .encode(
            x=alt.X("hour:O", title="Hora do dia"),
            y=alt.Y("pickups:Q", title="Nº de corridas"),
            tooltip=["hour", "pickups"],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)

    st.divider()
    st.subheader("Top 10 locais por densidade (amostra)")
    # Rough clustering by rounding lat/lon
    quantized = (
        filtered.assign(lat_q=filtered[LAT_COL].round(3), lon_q=filtered[LON_COL].round(3))
        .groupby(["lat_q", "lon_q"], as_index=False)
        .size()
        .sort_values("size", ascending=False)
        .head(10)
    )
    st.dataframe(quantized.rename(columns={"size": "pickups"}), use_container_width=True)

with TAB_MAP:
    st.subheader("Mapa de pickups")
    if filtered.empty:
        st.info("Sem dados para o filtro atual.")
    else:
        # Focus the map roughly around NYC
        midpoint = (np.average(filtered[LAT_COL]), np.average(filtered[LON_COL]))
        r = pdk.ViewState(latitude=midpoint[0], longitude=midpoint[1], zoom=9, pitch=0)
        layers = get_map_layers(filtered)
        st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=r, layers=layers), use_container_width=True)

with TAB_DATA:
    st.subheader("Tabela de dados (filtrada)")
    st.dataframe(
        filtered[["datetime", LAT_COL, LON_COL, BASE_COL, "hour", "weekday"]],
        use_container_width=True,
        hide_index=True,
    )

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV filtrado", data=csv, file_name="uber_pickups_filtrado.csv", mime="text/csv")

with TAB_ABOUT:
    st.markdown(
        """
        **App** customizado a partir do tutorial "Uber pickups in NYC" com melhorias de:
        - Filtros por período, hora e base
        - KPIs e gráfico interativo (Altair)
        - *Heatmap* + pontos (PyDeck)
        - Download de CSV filtrado
        - Cache de dados com `st.cache_data`
        
        **Como executar**
        1. Instale dependências: `pip install streamlit pandas numpy pydeck altair`
        2. Rode: `streamlit run streamlit_uber_app.py`
        3. Ajuste a URL do dataset na barra lateral se desejar.
        """
    )
