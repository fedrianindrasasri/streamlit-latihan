"""
India Air Quality Dashboard — Streamlit BI Application
======================================================
A public-awareness dashboard tracking SO₂, NO₂, RSPM, SPM, PM2.5
across 34 Indian states from 1987–2015 (435K+ monitoring records).

Design direction (per SKILL-frontend.md):
  Subject:  Indian air pollution — haze, industrial smoke, breathability
  Audience: Indian general public, non-technical
  Job:      Make invisible danger (air) visible and personal
  Palette:  "Smoke & Signal" — muted earth tones punctuated by alarm amber
  Signature: Pollution-level color encoding woven through every element —
             the page itself "breathes" the data's severity
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="India Air Quality Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# DESIGN SYSTEM — "Smoke & Signal"
# ──────────────────────────────────────────────
# Palette: deep charcoal canvas, warm smoke grays, amber alarm, teal clarity
BG_DARK = "#0c1017"
BG_CARD = "#141a24"
BG_CARD_HOVER = "#1a2233"
TEXT_PRIMARY = "#e2e4e9"
TEXT_DIM = "#7a8194"
AMBER = "#f0a500"       # alarm / hazardous
TEAL = "#2ec4b6"        # clarity / safe
CORAL = "#e85d4a"       # danger
SLATE = "#3d4f6f"       # structural accents
LAVENDER = "#a5b4d4"    # secondary data

# Pollution level encoding — the signature
def level_color(v):
    """NAAQS-style color: green→yellow→orange→red."""
    if v <= 60:  return "#2ec4b6"   # teal — Good
    if v <= 90:  return "#a8c256"   # lime — Moderate
    if v <= 120: return "#f0a500"   # amber — Unhealthy
    return "#e85d4a"                # coral — Hazardous

def level_label(v):
    if v <= 60:  return "Good"
    if v <= 90:  return "Moderate"
    if v <= 120: return "Unhealthy"
    return "Hazardous"

POLLUTANT_COLORS = {
    "SO₂": "#2ec4b6",
    "NO₂": "#f0a500",
    "RSPM": "#e85d4a",
    "PM2.5": "#a78bfa",
    "SPM": "#7a8194",
}

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global */
    .stApp {
        background-color: #0c1017;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111820;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown label,
    section[data-testid="stSidebar"] label {
        color: #a5b4d4 !important;
    }

    /* Headers */
    h1, h2, h3 { color: #e2e4e9 !important; font-family: 'Inter', sans-serif !important; }
    h1 { font-weight: 800 !important; letter-spacing: -0.5px !important; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #141a24, #1a2233);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 14px;
        padding: 18px 22px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetric"] label {
        color: #7a8194 !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e2e4e9 !important;
        font-weight: 800 !important;
        font-size: 32px !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px 8px 0 0;
        color: #7a8194;
        padding: 8px 20px;
        font-weight: 600;
        font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(240,165,0,0.1) !important;
        color: #f0a500 !important;
        border-bottom: 2px solid #f0a500 !important;
    }

    /* Dataframes */
    .stDataFrame { border-radius: 12px; overflow: hidden; }

    /* Plotly charts card wrapper */
    .chart-card {
        background: #141a24;
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .chart-title {
        font-size: 14px;
        font-weight: 700;
        color: #e2e4e9;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Custom divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(240,165,0,0.2), transparent);
        margin: 24px 0;
    }

    /* Footer */
    .footer-text {
        text-align: center;
        font-size: 11px;
        color: #4a5568;
        padding: 20px 0;
        border-top: 1px solid rgba(255,255,255,0.04);
        margin-top: 30px;
    }

    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    /* Expander */
    .streamlit-expanderHeader { color: #a5b4d4 !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PLOTLY TEMPLATE
# ──────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=TEXT_PRIMARY, size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", borderwidth=0,
        font=dict(size=11, color=TEXT_DIM),
        orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5
    ),
    hoverlabel=dict(bgcolor=BG_CARD, bordercolor="rgba(255,255,255,0.1)", font_color=TEXT_PRIMARY),
)

# ──────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────
@st.cache_data
def load_data():
    """Load the pre-aggregated JSON + raw CSV for detail views."""
    base_dir = os.path.dirname(os.path.abspath(__file__))

    json_path = os.path.join(base_dir, "dashboard_data.json")
    with open(json_path, "r", encoding="utf-8") as f:
        agg = json.load(f)

    csv_path = os.path.join(base_dir, "Cleaned_India_Air_Quality_Data.csv")
    df = pd.read_csv(csv_path, parse_dates=["date"], low_memory=False)

    # Normalize type column
    def norm_type(t):
        t = str(t).strip().strip('"').lower()
        if "industrial" in t: return "Industrial"
        if "sensitive" in t: return "Sensitive"
        if "residential" in t: return "Residential"
        return "Other"
    df["type_clean"] = df["type"].apply(norm_type)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")

    return agg, df


agg, df_raw = load_data()

# ──────────────────────────────────────────────
# SIDEBAR — FILTERS
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌫️ Filters")
    st.markdown('<p style="color:#4a5568; font-size:12px; margin-top:-10px;">Narrow down the data to explore specific regions, periods, or station types.</p>', unsafe_allow_html=True)

    st.markdown("---")

    # State
    all_states = ["All States"] + sorted(df_raw["state"].dropna().unique().tolist())
    sel_state = st.selectbox("🏴 State", all_states, index=0, key="filter_state")

    # Year range
    year_min = int(df_raw["year"].min())
    year_max = int(df_raw["year"].max())
    sel_years = st.slider("📅 Year Range", year_min, year_max, (year_min, year_max), key="filter_years")

    # Station type
    all_types = ["All Types"] + sorted(df_raw["type_clean"].unique().tolist())
    sel_type = st.selectbox("🏭 Station Type", all_types, index=0, key="filter_type")

    st.markdown("---")
    st.markdown(f"""
    <div style="background:rgba(240,165,0,0.08); border:1px solid rgba(240,165,0,0.15);
                border-radius:10px; padding:14px; margin-top:8px;">
        <div style="font-size:11px; color:#f0a500; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">
            About this data
        </div>
        <div style="font-size:12px; color:#a5b4d4; line-height:1.5;">
            <strong>{agg['kpis']['total_records']:,}</strong> monitoring records<br>
            <strong>{agg['kpis']['total_stations']}</strong> stations across <strong>34</strong> states<br>
            Period: <strong>{year_min}</strong> – <strong>{year_max}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# APPLY FILTERS TO RAW DATA
# ──────────────────────────────────────────────
df = df_raw.copy()
if sel_state != "All States":
    df = df[df["state"] == sel_state]
if sel_type != "All Types":
    df = df[df["type_clean"] == sel_type]
df = df[(df["year"] >= sel_years[0]) & (df["year"] <= sel_years[1])]

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:4px;">
    <h1 style="font-size:28px; margin-bottom:2px; font-weight:800;
               background: linear-gradient(135deg, #f0a500, #e85d4a);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🌫️ India Air Quality Dashboard
    </h1>
    <p style="color:#7a8194; font-size:13px; margin-top:0;">
        Monitoring pollution levels across India — because the air you breathe should never be invisible.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# KPI ROW
# ──────────────────────────────────────────────
avg_rspm = df["rspm"].dropna().mean() if len(df) > 0 else 0
avg_pm25 = df["pm2_5"].dropna().mean() if len(df) > 0 else 0
avg_so2 = df["so2"].dropna().mean() if len(df) > 0 else 0
avg_no2 = df["no2"].dropna().mean() if len(df) > 0 else 0
n_records = len(df)
n_stations = df["stn_code"].nunique() if len(df) > 0 else 0

# Worst state in filtered data
if len(df) > 0:
    worst = df.groupby("state")["rspm"].mean().idxmax()
    worst_val = df.groupby("state")["rspm"].mean().max()
else:
    worst, worst_val = "—", 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Avg RSPM (PM₁₀)", f"{avg_rspm:.1f} µg/m³", delta=level_label(avg_rspm))
with col2:
    st.metric("Avg PM2.5", f"{avg_pm25:.1f} µg/m³", delta=level_label(avg_pm25))
with col3:
    st.metric("Avg SO₂", f"{avg_so2:.1f} µg/m³")
with col4:
    st.metric("Most Polluted", worst, delta=f"{worst_val:.0f} µg/m³")
with col5:
    st.metric("Records / Stations", f"{n_records:,}", delta=f"{n_stations} stations")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_trends, tab_geo, tab_compare, tab_detail = st.tabs([
    "📈 Trends", "🗺️ Geographic", "⚖️ Comparison", "📋 Detail Table"
])

# ──────────────────────────────────────────────
# TAB 1: TRENDS
# ──────────────────────────────────────────────
with tab_trends:
    # 1A: Pollutant Trends Over Time
    st.markdown('<div class="chart-title">📈 Pollutant Trends Over Time</div>', unsafe_allow_html=True)

    yearly = df.groupby("year").agg(
        so2=("so2", "mean"),
        no2=("no2", "mean"),
        rspm=("rspm", "mean"),
        pm25=("pm2_5", "mean"),
    ).reset_index()

    fig_trend = go.Figure()
    for col_name, display, color in [
        ("so2", "SO₂", POLLUTANT_COLORS["SO₂"]),
        ("no2", "NO₂", POLLUTANT_COLORS["NO₂"]),
        ("rspm", "RSPM", POLLUTANT_COLORS["RSPM"]),
        ("pm25", "PM2.5", POLLUTANT_COLORS["PM2.5"]),
    ]:
        fig_trend.add_trace(go.Scatter(
            x=yearly["year"], y=yearly[col_name],
            name=display, mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline"),
            marker=dict(size=4),
            hovertemplate=f"{display}: %{{y:.1f}} µg/m³<extra></extra>",
        ))
    fig_trend.update_layout(**PLOTLY_LAYOUT, height=400, title=None)
    fig_trend.update_xaxes(title_text="Year", dtick=2)
    fig_trend.update_yaxes(title_text="Concentration (µg/m³)")
    st.plotly_chart(fig_trend, width="stretch")

    # 1B: Monthly Seasonal Pattern
    st.markdown('<div class="chart-title">🌡️ Monthly Pollution Pattern — Seasonal Variation</div>', unsafe_allow_html=True)

    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly = df.groupby("month").agg(rspm=("rspm","mean"), pm25=("pm2_5","mean")).reset_index()
    monthly["month_name"] = monthly["month"].apply(lambda m: month_order[m-1])
    monthly = monthly.sort_values("month")

    # Color bars by season
    def seasonal_color(m):
        if m in [11, 12, 1, 2]:   return CORAL       # Winter — peak pollution
        if m in [6, 7, 8, 9]:     return TEAL         # Monsoon — cleaner
        return AMBER                                   # Transition

    bar_colors = [seasonal_color(m) for m in monthly["month"]]

    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=monthly["month_name"], y=monthly["rspm"],
        name="RSPM", marker_color=bar_colors,
        marker_line_width=0, opacity=0.85,
        hovertemplate="RSPM: %{y:.1f} µg/m³<extra></extra>",
    ))
    fig_monthly.add_trace(go.Scatter(
        x=monthly["month_name"], y=monthly["pm25"],
        name="PM2.5", mode="lines+markers",
        line=dict(color=POLLUTANT_COLORS["PM2.5"], width=2.5),
        marker=dict(size=6),
        hovertemplate="PM2.5: %{y:.1f} µg/m³<extra></extra>",
    ))
    fig_monthly.update_layout(**PLOTLY_LAYOUT, height=350, barmode="overlay")
    fig_monthly.update_xaxes(categoryorder="array", categoryarray=month_order)
    fig_monthly.update_yaxes(title_text="µg/m³")

    # Add season annotations
    fig_monthly.add_annotation(x="Dec", y=monthly["rspm"].max()*1.05,
        text="🔴 Winter Peak", showarrow=False, font=dict(size=10, color=CORAL))
    fig_monthly.add_annotation(x="Aug", y=monthly["rspm"].min()*0.9,
        text="🟢 Monsoon Low", showarrow=False, font=dict(size=10, color=TEAL))

    st.plotly_chart(fig_monthly, width="stretch")


# ──────────────────────────────────────────────
# TAB 2: GEOGRAPHIC
# ──────────────────────────────────────────────
with tab_geo:
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # State Ranking — Horizontal Bar
        st.markdown('<div class="chart-title">🏴 State Pollution Ranking (Avg RSPM)</div>', unsafe_allow_html=True)

        state_avg = df.groupby("state")["rspm"].mean().dropna().sort_values(ascending=True).tail(20)
        bar_colors_state = [level_color(v) for v in state_avg.values]

        fig_states = go.Figure(go.Bar(
            y=state_avg.index, x=state_avg.values,
            orientation="h",
            marker_color=bar_colors_state,
            marker_line_width=0,
            hovertemplate="%{y}: %{x:.1f} µg/m³<extra></extra>",
        ))
        # WHO guideline
        fig_states.add_vline(x=60, line_dash="dash", line_color="rgba(46,196,182,0.5)",
                             annotation_text="WHO Limit (60)", annotation_position="top",
                             annotation_font_color=TEAL, annotation_font_size=10)
        fig_states.update_layout(**PLOTLY_LAYOUT, height=550, showlegend=False)
        fig_states.update_xaxes(title_text="Avg RSPM (µg/m³)")
        st.plotly_chart(fig_states, width="stretch")

    with col_right:
        # Top 10 Cities
        st.markdown('<div class="chart-title">🏙️ Top 10 Most Polluted Cities</div>', unsafe_allow_html=True)

        city_avg = df.groupby(["location","state"])["rspm"].mean().dropna().sort_values(ascending=False).head(10).reset_index()
        city_avg.columns = ["City", "State", "Avg RSPM"]
        city_avg = city_avg.sort_values("Avg RSPM", ascending=True)

        fig_cities = go.Figure(go.Bar(
            y=city_avg["City"], x=city_avg["Avg RSPM"],
            orientation="h",
            marker=dict(
                color=city_avg["Avg RSPM"],
                colorscale=[[0, AMBER], [1, CORAL]],
            ),
            text=city_avg["Avg RSPM"].round(0).astype(int),
            textposition="outside", textfont=dict(size=10, color=TEXT_DIM),
            hovertemplate="%{y}<br>State: " + city_avg["State"] + "<br>RSPM: %{x:.1f} µg/m³<extra></extra>",
        ))
        fig_cities.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
        fig_cities.update_xaxes(title_text="Avg RSPM (µg/m³)")
        st.plotly_chart(fig_cities, width="stretch")

        # Bottom 5 cleanest
        st.markdown('<div class="chart-title">🌿 5 Cleanest Cities</div>', unsafe_allow_html=True)
        city_clean = df.groupby(["location","state"])["rspm"].mean().dropna()
        city_clean = city_clean[city_clean.index.get_level_values(0).map(lambda x: df[df["location"]==x].shape[0] >= 50)]
        city_clean = city_clean.sort_values().head(5).reset_index()
        city_clean.columns = ["City", "State", "Avg RSPM"]

        for _, row in city_clean.iterrows():
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                        background:rgba(46,196,182,0.06); border-radius:8px; padding:8px 14px; margin-bottom:6px;">
                <span style="color:#e2e4e9; font-weight:600; font-size:13px;">{row['City']}</span>
                <span style="color:#2ec4b6; font-weight:700; font-size:13px;">{row['Avg RSPM']:.1f} µg/m³</span>
            </div>
            """, unsafe_allow_html=True)

    # Heatmap: State × Month
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">🗺️ Monthly Pollution Heatmap — State × Month</div>', unsafe_allow_html=True)

    hm_data = df.groupby(["state", "month"])["rspm"].mean().reset_index()
    hm_pivot = hm_data.pivot(index="state", columns="month", values="rspm").fillna(0)
    # Sort by overall average
    hm_pivot = hm_pivot.loc[hm_pivot.mean(axis=1).sort_values(ascending=False).head(18).index]
    hm_pivot.columns = month_order

    fig_hm = go.Figure(go.Heatmap(
        z=hm_pivot.values,
        x=hm_pivot.columns.tolist(),
        y=hm_pivot.index.tolist(),
        colorscale=[
            [0.0, "#1a3a2a"],     # deep forest green
            [0.25, "#2ec4b6"],    # teal
            [0.5, "#f0a500"],     # amber
            [0.75, "#e85d4a"],    # coral
            [1.0, "#8b1a1a"],     # dark crimson
        ],
        text=hm_pivot.values.round(0).astype(int),
        texttemplate="%{text}",
        textfont=dict(size=9),
        hovertemplate="State: %{y}<br>Month: %{x}<br>RSPM: %{z:.1f} µg/m³<extra></extra>",
        colorbar=dict(title=dict(text="RSPM", font=dict(color=TEXT_DIM)), tickfont=dict(color=TEXT_DIM)),
    ))
    fig_hm.update_layout(**PLOTLY_LAYOUT, height=500)
    fig_hm.update_yaxes(tickfont=dict(size=10))
    st.plotly_chart(fig_hm, width="stretch")


# ──────────────────────────────────────────────
# TAB 3: COMPARISON
# ──────────────────────────────────────────────
with tab_compare:
    col_a, col_b = st.columns(2)

    with col_a:
        # Donut: Station Type Distribution
        st.markdown('<div class="chart-title">🏭 Station Type Distribution</div>', unsafe_allow_html=True)

        type_counts = df["type_clean"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        type_colors_map = {"Industrial": "#e85d4a", "Residential": "#3d8bfd", "Sensitive": "#2ec4b6", "Other": "#f0a500"}
        type_colors = [type_colors_map.get(t, "#7a8194") for t in type_counts["Type"]]

        fig_donut = go.Figure(go.Pie(
            labels=type_counts["Type"], values=type_counts["Count"],
            hole=0.6, marker=dict(colors=type_colors, line=dict(color=BG_DARK, width=3)),
            textinfo="label+percent", textfont=dict(size=11, color=TEXT_PRIMARY),
            hovertemplate="%{label}: %{value:,} records (%{percent})<extra></extra>",
        ))
        fig_donut.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=False)
        # Center annotation
        fig_donut.add_annotation(text=f"<b>{n_records:,}</b><br><span style='font-size:10px;color:{TEXT_DIM}'>records</span>",
                                  x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=TEXT_PRIMARY))
        st.plotly_chart(fig_donut, width="stretch")

        # Type comparison bars
        type_rspm = df.groupby("type_clean")["rspm"].mean().sort_values(ascending=True)
        st.markdown('<div class="chart-title" style="margin-top:16px;">📊 Avg RSPM by Station Type</div>', unsafe_allow_html=True)
        fig_tbar = go.Figure(go.Bar(
            y=type_rspm.index, x=type_rspm.values, orientation="h",
            marker_color=[type_colors_map.get(t, "#7a8194") for t in type_rspm.index],
            text=type_rspm.round(1), textposition="outside", textfont=dict(size=10, color=TEXT_DIM),
            hovertemplate="%{y}: %{x:.1f} µg/m³<extra></extra>",
        ))
        fig_tbar.update_layout(**PLOTLY_LAYOUT, height=220, showlegend=False)
        fig_tbar.update_xaxes(title_text="µg/m³")
        st.plotly_chart(fig_tbar, width="stretch")

    with col_b:
        # Scatter: SO₂ vs NO₂
        st.markdown('<div class="chart-title">🔴 SO₂ vs NO₂ Correlation by State</div>', unsafe_allow_html=True)

        scatter_df = df.groupby("state").agg(
            so2=("so2","mean"), no2=("no2","mean"), rspm=("rspm","mean")
        ).dropna().reset_index()

        fig_sc = go.Figure(go.Scatter(
            x=scatter_df["so2"], y=scatter_df["no2"],
            mode="markers+text",
            marker=dict(
                size=scatter_df["rspm"].clip(30,200) / 8,
                color=[level_color(v) for v in scatter_df["rspm"]],
                line=dict(width=1, color="rgba(255,255,255,0.15)"),
                opacity=0.85,
            ),
            text=scatter_df["state"].apply(lambda s: s[:3]),
            textposition="top center", textfont=dict(size=8, color=TEXT_DIM),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "SO₂: %{x:.1f} µg/m³<br>"
                "NO₂: %{y:.1f} µg/m³<br>"
                "RSPM: %{customdata[1]:.1f} µg/m³<extra></extra>"
            ),
            customdata=scatter_df[["state","rspm"]].values,
        ))
        fig_sc.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
        fig_sc.update_xaxes(title_text="SO₂ (µg/m³)")
        fig_sc.update_yaxes(title_text="NO₂ (µg/m³)")
        st.plotly_chart(fig_sc, width="stretch")

        # Legend
        st.markdown("""
        <div style="display:flex; gap:16px; justify-content:center; flex-wrap:wrap; margin-top:8px;">
            <span style="font-size:11px;color:#2ec4b6;">● Good (≤60)</span>
            <span style="font-size:11px;color:#a8c256;">● Moderate (61-90)</span>
            <span style="font-size:11px;color:#f0a500;">● Unhealthy (91-120)</span>
            <span style="font-size:11px;color:#e85d4a;">● Hazardous (>120)</span>
        </div>
        <p style="font-size:10px; color:#4a5568; text-align:center; margin-top:6px;">
            Bubble size = RSPM level &nbsp;|&nbsp; Color = pollution severity
        </p>
        """, unsafe_allow_html=True)

        # SO₂ vs NO₂ Grouped Bar — Top 10 states
        st.markdown('<div class="chart-title" style="margin-top:20px;">⚖️ SO₂ vs NO₂ — Top 10 Polluted States</div>', unsafe_allow_html=True)
        top10 = scatter_df.nlargest(10, "rspm").sort_values("rspm", ascending=True)

        fig_grouped = go.Figure()
        fig_grouped.add_trace(go.Bar(
            y=top10["state"], x=top10["so2"], name="SO₂", orientation="h",
            marker_color=TEAL, opacity=0.85,
        ))
        fig_grouped.add_trace(go.Bar(
            y=top10["state"], x=top10["no2"], name="NO₂", orientation="h",
            marker_color=AMBER, opacity=0.85,
        ))
        fig_grouped.update_layout(**PLOTLY_LAYOUT, height=350, barmode="group")
        fig_grouped.update_xaxes(title_text="µg/m³")
        st.plotly_chart(fig_grouped, width="stretch")


# ──────────────────────────────────────────────
# TAB 4: DETAIL TABLE
# ──────────────────────────────────────────────
with tab_detail:
    st.markdown('<div class="chart-title">📋 State-wise Air Quality Summary</div>', unsafe_allow_html=True)

    table_df = df.groupby("state").agg(
        avg_rspm=("rspm","mean"),
        avg_pm25=("pm2_5","mean"),
        avg_so2=("so2","mean"),
        avg_no2=("no2","mean"),
        avg_spm=("spm","mean"),
        stations=("stn_code","nunique"),
        records=("stn_code","count"),
    ).round(2).reset_index()
    table_df.columns = ["State","Avg RSPM","Avg PM2.5","Avg SO₂","Avg NO₂","Avg SPM","Stations","Records"]
    table_df = table_df.sort_values("Avg RSPM", ascending=False)

    st.dataframe(
        table_df.style
            .format({"Avg RSPM":"{:.1f}","Avg PM2.5":"{:.1f}","Avg SO₂":"{:.1f}","Avg NO₂":"{:.1f}","Avg SPM":"{:.1f}","Records":"{:,.0f}"})
            .background_gradient(subset=["Avg RSPM"], cmap="YlOrRd", vmin=30, vmax=200)
            .background_gradient(subset=["Avg PM2.5"], cmap="PuRd", vmin=20, vmax=90)
            .background_gradient(subset=["Avg NO₂"], cmap="YlOrBr", vmin=5, vmax=60),
        width="stretch",
        height=600,
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Download
    csv_export = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Summary as CSV",
        data=csv_export,
        file_name="india_aq_summary.csv",
        mime="text/csv",
    )


# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────
st.markdown("""
<div class="footer-text">
    <strong>India Air Quality Dashboard</strong> — Data from 1987–2015<br>
    435,054 monitoring records &bull; 803 stations &bull; 34 states<br>
    Built for <strong>Public Awareness</strong> &bull; Dashboard by Streamlit + Plotly
</div>
""", unsafe_allow_html=True)
