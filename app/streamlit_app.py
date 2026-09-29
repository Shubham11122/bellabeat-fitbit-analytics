"""
Bellabeat x Fitbit case study - Streamlit dashboard (single file, black and orange theme)

Run from the project root:   streamlit run app/streamlit_app.py
Reads:  db/fitbit.db        (built by notebooks/Data cleaning.ipynb)
        assets/*.png        (logo files)
        .streamlit/config.toml  (base dark theme + orange accent)
"""

import base64
import inspect
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# PATHS AND DESIGN TOKENS
# =============================================================================
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "fitbit.db"
ASSETS = ROOT / "assets"

# Brand palette. Orange always means "look here" (the problem / the standout).
ORANGE = "#FC4C02"
PEACH = "#FFB08A"
EMBER = "#FF7A2F"
WHITE = "#F2F2F3"
MUTED = "#9A9AA2"
LGRAY = "#8E8E96"
GRAY = "#45454C"
STEEL = "#6E8CA0"
GOLD = "#FFD23F"
CARD = "#141416"
LINE = "#2A2A2E"
GRID = "#232327"
FONT = "Archivo, 'Segoe UI', Arial, sans-serif"

WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
STEP_GOAL = 7500
CAT_COLORS = [ORANGE, PEACH, WHITE, STEEL, GOLD, LGRAY]

PAGES = [
    "Overview",
    "Daily Activity",
    "Sleep",
    "BMI",
    "Hourly Patterns",
    "SQL Analysis",
    "Findings & Recommendations",
]


def _b64(path: Path) -> str:
    try:
        return base64.b64encode(path.read_bytes()).decode()
    except Exception:
        return ""


ICON_B64 = _b64(ASSETS / "strava_icon.png")
WORD_B64 = _b64(ASSETS / "strava_wordmark.png")

try:
    from PIL import Image

    _page_icon = Image.open(ASSETS / "strava_icon.png")
except Exception:
    _page_icon = None

st.set_page_config(
    page_title="Bellabeat x Fitbit | Activity dashboard",
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# GLOBAL CSS
# =============================================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap');

html, body, .stApp, [class*="css"] { font-family: Archivo, 'Segoe UI', Arial, sans-serif; }
.stApp { background: #0B0B0C; }
[data-testid="stHeader"] { background: transparent; }
/* hide only the Deploy button, the main menu and the footer, never the whole toolbar */
#MainMenu, footer, .stDeployButton, [data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
[data-testid="stToolbarActions"], [data-testid="stStatusWidget"] { display: none !important; }
/* keep the arrow that reopens a collapsed sidebar visible in every Streamlit version */
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] { display: flex !important; visibility: visible !important; opacity: 1 !important; }
[data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] *, [data-testid="collapsedControl"] * { color: #FC4C02 !important; }
.block-container { padding-top: 1.3rem; padding-bottom: 3rem; max-width: 1400px; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: #0F0F11; border-right: 1px solid #2A2A2E; }
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarContent"] { padding-top: 1rem; }
.side-brand { padding: .2rem .4rem 1rem .4rem; border-bottom: 1px solid #2A2A2E; margin-bottom: 1rem; }
.side-brand img { height: 30px; display: block; }
.side-brand .side-sub { color: #9A9AA2; font-size: .8rem; margin-top: .55rem; }
.side-label { color: #9A9AA2; font-size: .78rem; font-weight: 600; margin: 1rem 0 .4rem .2rem; }

[data-testid="stSidebar"] .stButton { width: 100%; }
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important; justify-content: flex-start !important; text-align: left !important;
    background: transparent !important; border: 1px solid transparent !important;
    border-left: 3px solid transparent !important; color: #C9C9CE !important;
    border-radius: 8px !important; padding: .55rem .9rem !important; font-weight: 600 !important;
    box-shadow: none !important; transition: background .15s, color .15s;
}
[data-testid="stSidebar"] .stButton > button > div { justify-content: flex-start !important; width: 100%; }
[data-testid="stSidebar"] .stButton > button p { margin: 0; font-size: .95rem; text-align: left; }
[data-testid="stSidebar"] .stButton > button:hover { background: #1B1B1E !important; color: #fff !important; }
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, rgba(252,76,2,.28), rgba(252,76,2,.05)) !important;
    border-left: 3px solid #FC4C02 !important; color: #fff !important;
}

/* ---------- header banner ---------- */
.hero {
    display: flex; justify-content: space-between; align-items: center; gap: 1.5rem;
    padding: 1.5rem 1.9rem 1.5rem 2.1rem; margin-bottom: 1.3rem; position: relative; overflow: hidden;
    border: 1px solid #2A2A2E; border-radius: 14px;
    background: radial-gradient(900px 240px at 0% 0%, rgba(252,76,2,.24), transparent 65%), linear-gradient(180deg, #171719, #0F0F11);
}
.hero::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 6px;
    background: linear-gradient(180deg, #FC4C02, #FFB08A); }
.hero-left { display: flex; align-items: center; gap: 1.3rem; min-width: 0; }
.hero-logo { height: 68px; flex: none; }
.hero-title { font-family: Archivo, sans-serif; font-stretch: 125%; font-weight: 800; font-size: 2.3rem;
    line-height: 1.05; color: #fff; margin: 0; letter-spacing: -.01em; }
.hero-sub { color: #A9A9B0; font-size: 1rem; margin-top: .4rem; max-width: 64ch; line-height: 1.45; }
.hero-right { display: flex; gap: .5rem; flex-wrap: wrap; justify-content: flex-end; max-width: 40%; }
.chip { border: 1px solid #2E2E33; background: rgba(0,0,0,.35); color: #D9D9DE; padding: .38rem .75rem;
    border-radius: 999px; font-size: .8rem; font-weight: 600; white-space: nowrap; }
.chip b { color: #FC4C02; font-weight: 700; }

/* ---------- KPI boxes ---------- */
.kpi { background: #141416; border: 1px solid #2A2A2E; border-radius: 12px; padding: 1.05rem 1.25rem 1rem 1.25rem;
    position: relative; overflow: hidden; height: 100%; }
.kpi::before { content: ""; position: absolute; left: 0; top: 0; width: 100%; height: 3px;
    background: linear-gradient(90deg, #FC4C02, rgba(252,76,2,0)); }
.kpi-label { color: #9A9AA2; font-size: .85rem; font-weight: 600; }
.kpi-value { font-family: Archivo, sans-serif; font-stretch: 112%; font-weight: 800; font-size: 2.55rem;
    line-height: 1.1; color: #fff; margin: .3rem 0 .25rem 0; letter-spacing: -.02em; }
.kpi-value small { font-size: 1rem; color: #9A9AA2; font-weight: 600; margin-left: .3rem; letter-spacing: 0; }
.kpi-sub { color: #8B8B93; font-size: .84rem; }

/* ---------- panels (boxed charts / sections) ---------- */
[class*="st-key-panel_"] { background: #141416; border: 1px solid #2A2A2E; border-radius: 14px;
    padding: 1.15rem 1.35rem .9rem 1.35rem; }
.p-kicker { color: #FC4C02; font-size: .82rem; font-weight: 700; margin-bottom: .2rem; }
.p-title { color: #fff; font-size: 1.28rem; font-weight: 700; line-height: 1.25; }
.p-sub { color: #8B8B93; font-size: .88rem; margin-top: .25rem; }
.gap { height: .9rem; }

/* ---------- callouts, lists ---------- */
.callout { border: 1px solid #2A2A2E; border-left: 4px solid #FC4C02; background: #141416; border-radius: 10px;
    padding: .9rem 1.1rem; color: #D6D6DB; font-size: .95rem; line-height: 1.5; }
.callout b { color: #fff; }
.plain-list { margin: .2rem 0 0 0; padding-left: 1.1rem; color: #D0D0D5; line-height: 1.7; font-size: .95rem; }
.plain-list b { color: #fff; }
.pagemap { width: 100%; border-collapse: collapse; font-size: .93rem; }
.pagemap td { padding: .55rem .4rem; border-bottom: 1px solid #232327; color: #C9C9CE; vertical-align: top; }
.pagemap td:first-child { color: #fff; font-weight: 700; white-space: nowrap; padding-right: 1.2rem; }
.pagemap tr:last-child td { border-bottom: none; }
.flow { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; margin-top: .3rem; }
.flow span { border: 1px solid #2E2E33; background: #0F0F11; border-radius: 8px; padding: .4rem .75rem;
    font-size: .88rem; font-weight: 600; color: #E4E4E8; }
.flow i { color: #FC4C02; font-style: normal; font-weight: 800; }

/* findings and recommendations */
.finding-stat { font-family: Archivo, sans-serif; font-stretch: 115%; font-weight: 800; font-size: 2.6rem; color: #FC4C02;
    line-height: 1; letter-spacing: -.02em; }
.finding-body { color: #CFCFD4; font-size: .95rem; line-height: 1.55; }
.finding-body b { color: #fff; }
.rec-num { display: inline-block; background: #FC4C02; color: #0B0B0C; font-weight: 800; border-radius: 6px;
    padding: .05rem .5rem; margin-right: .5rem; font-size: .95rem; }
.rec-head { color: #fff; font-weight: 700; font-size: 1.1rem; }
.rec-why { color: #8B8B93; font-size: .86rem; margin-top: .45rem; }

/* misc widgets */
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p { font-size: .88rem; }
[data-testid="stDataFrame"] { border: 1px solid #2A2A2E; border-radius: 10px; overflow: hidden; }
div[data-baseweb="tab-list"] { gap: .4rem; }
button[data-baseweb="tab"] { font-weight: 600; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =============================================================================
# SMALL UI HELPERS
# =============================================================================
_plotly_takes_width = "width" in inspect.signature(st.plotly_chart).parameters
_counter = {"panel": 0, "chart": 0}


def show(fig, height=380, legend=False):
    """Apply the dashboard look to a Plotly figure and draw it."""
    fig.update_layout(
        height=height,
        title=None,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=WHITE, size=13),
        margin=dict(l=6, r=10, t=14, b=6),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None,
                    font=dict(size=12), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#1E1E22", bordercolor=ORANGE, font=dict(family=FONT, color="#fff", size=13)),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=LINE, tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=LINE, tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    _counter["chart"] += 1
    kw = dict(theme=None, key=f"chart_{_counter['chart']}", config={"displayModeBar": False})
    if _plotly_takes_width:
        st.plotly_chart(fig, width="stretch", **kw)
    else:
        st.plotly_chart(fig, use_container_width=True, **kw)


def show_df(df: pd.DataFrame, height=None):
    df = df.copy()
    for col in ("Id",):
        if col in df.columns:
            df[col] = df[col].astype(str)
    kw = {"height": height} if height else {}
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kw)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True, **kw)


@contextmanager
def panel(kicker: str, headline: str, sub: str = ""):
    """A boxed card with a short label, an insight headline and an optional subtitle."""
    _counter["panel"] += 1
    try:
        box = st.container(key=f"panel_{_counter['panel']}")
    except TypeError:  # very old Streamlit without container keys
        box = st.container(border=True)
    with box:
        html = f'<div class="p-kicker">{kicker}</div><div class="p-title">{headline}</div>'
        if sub:
            html += f'<div class="p-sub">{sub}</div>'
        st.markdown(html, unsafe_allow_html=True)
        yield


def kpi_row(items):
    """items: list of (label, value, sub, unit)"""
    cols = st.columns(len(items), gap="medium")
    for col, item in zip(cols, items):
        label, value, sub, *rest = item
        unit = rest[0] if rest else ""
        unit_html = f"<small>{unit}</small>" if unit else ""
        col.markdown(
            f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}{unit_html}</div><div class="kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )
    gap()


def gap():
    st.markdown('<div class="gap"></div>', unsafe_allow_html=True)


def callout(text: str):
    st.markdown(f'<div class="callout">{text}</div>', unsafe_allow_html=True)


def hero(title: str, subtitle: str):
    logo = f'<img class="hero-logo" src="data:image/png;base64,{ICON_B64}" alt="logo"/>' if ICON_B64 else ""
    chips = "".join(f'<span class="chip">{c}</span>' for c in CHIPS)
    st.markdown(
        f'<div class="hero"><div class="hero-left">{logo}<div>'
        f'<div class="hero-title">{title}</div><div class="hero-sub">{subtitle}</div></div></div>'
        f'<div class="hero-right">{chips}</div></div>',
        unsafe_allow_html=True,
    )


def hour_label(h) -> str:
    h = int(h)
    return f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}"


def bmi_category(b: float) -> str:
    if b < 18.5:
        return "Underweight"
    if b < 25:
        return "Normal"
    if b < 30:
        return "Overweight"
    return "Obese"


# =============================================================================
# DATA
# =============================================================================
if not DB_PATH.exists():
    st.error(
        f"Database not found at {DB_PATH}. Run notebooks/Data cleaning.ipynb first so it creates db/fitbit.db, "
        "and make sure the file is committed if you deploy the app."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_data():
    conn = sqlite3.connect(DB_PATH)
    daily = pd.read_sql("SELECT * FROM daily_activity", conn, parse_dates=["date"])
    sleep = pd.read_sql("SELECT * FROM sleep_daily", conn, parse_dates=["date"])
    weight = pd.read_sql("SELECT * FROM weight_log", conn, parse_dates=["date"])
    hourly = pd.read_sql("SELECT * FROM hourly_activity", conn, parse_dates=["date"])
    conn.close()
    return daily, sleep, weight, hourly


@st.cache_data(show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA query_only = ON")  # read-only, even for the free-text box
        return pd.read_sql(sql, conn)
    finally:
        conn.close()


daily, sleep, weight, hourly = load_data()

# =============================================================================
# SIDEBAR: BRAND, NAVIGATION, FILTERS
# =============================================================================
if "page" not in st.session_state:
    st.session_state["page"] = PAGES[0]


def _go(name: str):
    st.session_state["page"] = name


with st.sidebar:
    brand = f'<img src="data:image/png;base64,{WORD_B64}" alt="Strava"/>' if WORD_B64 else "<b>Dashboard</b>"
    st.markdown(
        f'<div class="side-brand">{brand}<div class="side-sub">Bellabeat x Fitbit case study</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-label">Pages</div>', unsafe_allow_html=True)
    for i, name in enumerate(PAGES):
        st.button(
            name,
            key=f"nav_{i}",
            on_click=_go,
            args=(name,),
            type="primary" if st.session_state["page"] == name else "secondary",
        )

    st.markdown('<div class="side-label">Filters</div>', unsafe_allow_html=True)
    all_users = sorted(daily["Id"].unique())
    picked = st.multiselect(
        "Users", options=all_users, default=[], placeholder=f"All {len(all_users)} users",
        help="Leave empty to include everyone. Filters every page except SQL Analysis and Findings.",
    )
    users_sel = picked or all_users

    date_min, date_max = daily["date"].min().date(), daily["date"].max().date()
    date_range = st.date_input("Date range", value=(date_min, date_max), min_value=date_min, max_value=date_max)
    include_not_worn = st.checkbox(
        "Include days the tracker was off", value=False,
        help="Days with 0 steps and 1,440 sedentary minutes. They are flagged during cleaning and excluded by default.",
    )
    st.caption("Fitabase Fitbit export: 33 users, 12 Apr to 12 May 2016. Sleep covers 24 users, weight and BMI only 8.")

# ---- apply filters once, shared by every page ----
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    d_start, d_end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    d_start, d_end = pd.Timestamp(date_min), pd.Timestamp(date_max)


def _filt(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["date"] >= d_start) & (df["date"] <= d_end) & (df["Id"].isin(users_sel))]


base = _filt(daily if include_not_worn else daily[daily["is_worn"] == 1])
sleep_f = _filt(sleep)
weight_f = _filt(weight)
hourly_f = _filt(hourly)
daily_worn_all = daily[daily["is_worn"] == 1]  # unfiltered, used by Overview and Findings

CHIPS = [
    f"<b>{len(users_sel)}</b> of {len(all_users)} users",
    f"{d_start:%d %b} to {d_end:%d %b %Y}",
    "Tracker-off days included" if include_not_worn else "Worn days only",
]

# =============================================================================
# PAGE: OVERVIEW
# =============================================================================
def page_overview():
    hero(
        "Overview",
        "What 33 Fitbit users did for a month, and what it means for Bellabeat's marketing. "
        "We look at daily activity, sleep and BMI.",
    )
    n_users = daily["Id"].nunique()
    n_sleep, n_weight = sleep["Id"].nunique(), weight["Id"].nunique()
    days = (daily["date"].max() - daily["date"].min()).days + 1
    kpi_row([
        ("Users tracked", f"{n_users}", "Everyone logs daily activity"),
        ("Study period", f"{days}", "12 Apr to 12 May 2016", "days"),
        ("Users with sleep data", f"{n_sleep}", f"{n_sleep / n_users:.0%} of all users"),
        ("Users with weight data", f"{n_weight}", f"{n_weight / n_users:.0%} of all users"),
    ])

    left, right = st.columns([3, 2], gap="medium")
    with left:
        with panel(
            "Engagement",
            f"Tracking falls from {n_users} users to {n_weight} as logging gets more manual",
            "Number of users who logged each type of data",
        ):
            eng = pd.DataFrame({
                "Data type": ["Daily activity", "Sleep", "Weight and BMI"],
                "Users": [n_users, n_sleep, n_weight],
            })
            fig = go.Figure(go.Bar(
                y=eng["Data type"], x=eng["Users"], orientation="h",
                marker_color=[GRAY, PEACH, ORANGE],
                text=[f"{u} users ({u / n_users:.0%})" for u in eng["Users"]],
                textposition="outside", cliponaxis=False,
                hovertemplate="%{y}: %{x} users<extra></extra>",
            ))
            fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=14, color=WHITE))
            fig.update_xaxes(range=[0, n_users * 1.28], showgrid=False, showticklabels=False)
            show(fig, height=250)
    with right:
        with panel("About the data", "One month, three lenses"):
            st.markdown(
                f"""<ul class="plain-list">
<li><b>Daily activity:</b> {daily['Id'].nunique()} users, {len(daily):,} user-days</li>
<li><b>Sleep:</b> {sleep['Id'].nunique()} users, {len(sleep):,} nights</li>
<li><b>Weight and BMI:</b> {weight['Id'].nunique()} users, {len(weight):,} weigh-ins</li>
<li><b>Hourly activity:</b> {hourly['Id'].nunique()} users, {len(hourly):,} user-hours</li>
<li><b>Source:</b> Fitabase Fitbit export</li></ul>""",
                unsafe_allow_html=True,
            )
    gap()

    a, b = st.columns([3, 2], gap="medium")
    with a:
        with panel("Guide", "Where to find what"):
            st.markdown(
                """<table class="pagemap">
<tr><td>Daily Activity</td><td>Steps, calories, intensity minutes and weekday patterns</td></tr>
<tr><td>Sleep</td><td>Sleep duration, efficiency, weekday against weekend</td></tr>
<tr><td>BMI</td><td>BMI by user, category mix, weight trends and the link to activity</td></tr>
<tr><td>Hourly Patterns</td><td>The times of day and days of the week people move most</td></tr>
<tr><td>SQL Analysis</td><td>20 saved queries plus a box to run your own, live on the database</td></tr>
<tr><td>Findings & Recommendations</td><td>What we learned and what Bellabeat should do about it</td></tr>
</table>""",
                unsafe_allow_html=True,
            )
    with b:
        with panel("Method", "How the project was built"):
            st.markdown(
                '<div class="flow"><span>Raw CSVs</span><i>&gt;</i><span>Cleaning</span><i>&gt;</i>'
                '<span>EDA</span><i>&gt;</i><span>SQL</span><i>&gt;</i><span>Dashboard</span></div>',
                unsafe_allow_html=True,
            )
            gap()
            callout(
                "<b>Read before drawing conclusions.</b> This is a small, self-selected sample of 33 users over 31 days. "
                "Weight and BMI cover only 8 users, and 2 of them made most of the records. "
                "Minute-level and heart-rate files were left out on purpose."
            )


# =============================================================================
# PAGE: DAILY ACTIVITY
# =============================================================================
def page_daily():
    hero("Daily Activity", "Steps, calories and intensity: how much people move, and when they slow down.")
    if base.empty:
        callout("No data for the current filters. Widen the date range or clear the user filter.")
        return

    below = (base["TotalSteps"] < STEP_GOAL).mean() * 100
    kpi_row([
        ("Average steps per day", f"{base['TotalSteps'].mean():,.0f}", f"{base['Id'].nunique()} users, {len(base):,} days"),
        ("Average calories per day", f"{base['Calories'].mean():,.0f}", "kcal burned, all activity"),
        ("Active minutes per day", f"{base['total_active_minutes'].mean():,.0f}", "light + fair + very active", "min"),
        (f"Days under {STEP_GOAL:,} steps", f"{below:.0f}", "share of all user-days", "%"),
    ])

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with panel("Steps", f"{below:.0f}% of days end under {STEP_GOAL:,} steps",
                   "User-days grouped into 2,500-step buckets"):
            d = base[["TotalSteps"]].copy()
            lo, hi = f"Under {STEP_GOAL:,}", f"{STEP_GOAL:,} or more"
            d["zone"] = np.where(d["TotalSteps"] < STEP_GOAL, lo, hi)
            fig = px.histogram(d, x="TotalSteps", color="zone", color_discrete_map={lo: ORANGE, hi: GRAY},
                               category_orders={"zone": [lo, hi]})
            fig.update_traces(xbins=dict(start=0, size=2500), marker_line_width=0)
            fig.update_layout(barmode="stack", bargap=0.06)
            fig.update_xaxes(title="Steps in a day")
            fig.update_yaxes(title="Number of days")
            fig.add_vline(x=STEP_GOAL, line_dash="dash", line_color=WHITE, line_width=1.5)
            show(fig, legend=True)
    with c2:
        x, y = base["TotalSteps"].to_numpy(float), base["Calories"].to_numpy(float)
        slope, intercept = np.polyfit(x, y, 1) if len(x) > 2 else (0, 0)
        r = np.corrcoef(x, y)[0, 1] if len(x) > 2 else 0
        with panel("Steps and calories", f"Every extra 1,000 steps adds about {slope * 1000:,.0f} kcal",
                   f"Correlation r = {r:.2f}: a solid link, but body size and other exercise matter too"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="One user-day",
                                     marker=dict(color=ORANGE, size=7, opacity=.5),
                                     hovertemplate="%{x:,.0f} steps<br>%{y:,.0f} kcal<extra></extra>"))
            xs = np.linspace(x.min(), x.max(), 60)
            fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", name="Trend",
                                     line=dict(color=WHITE, width=2.5), hoverinfo="skip"))
            fig.update_xaxes(title="Steps in a day")
            fig.update_yaxes(title="Calories burned")
            show(fig, legend=True)

    gap()
    c3, c4 = st.columns([3, 2], gap="medium")
    with c3:
        dow = base.groupby("day_of_week")["TotalSteps"].mean().reindex(WEEKDAY_ORDER).dropna()
        low, high = dow.idxmin(), dow.idxmax()
        drop = (dow.max() - dow.min()) / dow.max() * 100
        with panel("Weekly rhythm", f"{low} is the quietest day, {drop:.0f}% fewer steps than {high}",
                   "Average steps per user-day. Orange is the lowest day, peach is the highest"):
            colors = [ORANGE if d == low else PEACH if d == high else GRAY for d in dow.index]
            fig = go.Figure(go.Bar(
                x=[d[:3] for d in dow.index], y=dow.values, marker_color=colors,
                text=[f"{v:,.0f}" for v in dow.values], textposition="outside", cliponaxis=False,
                hovertemplate="%{x}: %{y:,.0f} steps<extra></extra>",
            ))
            fig.add_hline(y=dow.mean(), line_dash="dot", line_color=MUTED,
                          annotation_text="weekly average", annotation_font_color=MUTED, annotation_position="top right")
            fig.update_yaxes(range=[0, dow.max() * 1.18], title="Average steps")
            fig.update_layout(bargap=0.28)
            show(fig, height=340)
    with c4:
        cols = ["SedentaryMinutes", "LightlyActiveMinutes", "FairlyActiveMinutes", "VeryActiveMinutes"]
        labels = ["Sedentary", "Lightly active", "Fairly active", "Very active"]
        totals = base[cols].sum()
        shares = totals / totals.sum() * 100
        with panel("Intensity", f"{shares.iloc[0]:.0f}% of tracked time is sedentary",
                   f"Fairly and very active minutes together are only {shares.iloc[2] + shares.iloc[3]:.1f}%"):
            fig = go.Figure(go.Pie(
                labels=labels, values=totals.values, hole=0.7, sort=False, direction="clockwise", rotation=0,
                marker=dict(colors=[GRAY, LGRAY, PEACH, ORANGE], line=dict(color=CARD, width=3)),
                textinfo="none", hovertemplate="%{label}: %{percent}<extra></extra>",
            ))
            fig.add_annotation(text=f"<b>{shares.iloc[0]:.0f}%</b><br><span style='font-size:12px;color:{MUTED}'>sedentary</span>",
                               x=0.5, y=0.5, showarrow=False, font=dict(size=30, color=WHITE))
            fig.update_layout(legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"))
            show(fig, height=340, legend=True)

    gap()
    c5, c6 = st.columns([2, 3], gap="medium")
    with c5:
        order = ["Sedentary", "Low active", "Somewhat active", "Active", "Highly active"]
        lv = base["activity_level"].value_counts().reindex(order).fillna(0)
        share_low = (lv["Sedentary"] + lv["Low active"]) / lv.sum() * 100
        with panel("Activity levels", f"{share_low:.0f}% of days are sedentary or low active",
                   "Days grouped by step count: under 5,000 / 5,000 / 7,500 / 10,000 / 12,500+"):
            fig = go.Figure(go.Bar(
                y=order, x=lv.values, orientation="h",
                marker_color=[ORANGE, EMBER, PEACH, LGRAY, GRAY],
                text=[f"{v / lv.sum():.0%}" for v in lv.values], textposition="outside", cliponaxis=False,
                hovertemplate="%{y}: %{x:,.0f} days<extra></extra>",
            ))
            fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=WHITE))
            fig.update_xaxes(range=[0, lv.max() * 1.2], showticklabels=False, showgrid=False)
            show(fig, height=340)
    with c6:
        ranked = base.groupby("Id")["TotalSteps"].mean().sort_values().reset_index()
        ranked["Id"] = ranked["Id"].astype(str)
        n_under = int((ranked["TotalSteps"] < STEP_GOAL).sum())
        with panel("Who is active", f"{n_under} of {len(ranked)} users average under {STEP_GOAL:,} steps a day",
                   "Average daily steps per user. Orange bars are below the goal line"):
            fig = go.Figure(go.Bar(
                y=ranked["Id"], x=ranked["TotalSteps"], orientation="h",
                marker_color=[ORANGE if v < STEP_GOAL else GRAY for v in ranked["TotalSteps"]],
                hovertemplate="User %{y}<br>%{x:,.0f} steps<extra></extra>",
            ))
            fig.update_yaxes(type="category", categoryorder="array", categoryarray=ranked["Id"], tickfont=dict(size=10))
            fig.add_vline(x=STEP_GOAL, line_dash="dash", line_color=WHITE, line_width=1.5)
            fig.update_xaxes(title="Average steps per day")
            fig.update_layout(bargap=0.25)
            show(fig, height=max(340, len(ranked) * 22))


# =============================================================================
# PAGE: SLEEP
# =============================================================================
SLEEP_ORDER = ["Under 6h", "6-9h (recommended)", "Over 9h"]
SLEEP_COLORS = {"Under 6h": ORANGE, "6-9h (recommended)": GRAY, "Over 9h": PEACH}


def page_sleep():
    hero("Sleep", "How long people sleep, how well they use their time in bed, and how weekends differ.")
    if sleep_f.empty:
        callout("No sleep data for the current filters. Only 24 of 33 users log sleep.")
        return

    pct_u6 = (sleep_f["hours_asleep"] < 6).mean() * 100
    kpi_row([
        ("Average sleep", f"{sleep_f['hours_asleep'].mean():.1f}", "hours asleep per night", "h"),
        ("Sleep efficiency", f"{sleep_f['sleep_efficiency'].mean() * 100:.0f}", "share of time in bed spent asleep", "%"),
        ("Nights under 6 hours", f"{pct_u6:.0f}", f"{int((sleep_f['hours_asleep'] < 6).sum())} of {len(sleep_f)} nights", "%"),
        ("Users with sleep data", f"{sleep_f['Id'].nunique()}", "of 33 in the study"),
    ])

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with panel("Duration", f"One night in {100 / max(pct_u6, 1):.0f} is under 6 hours" if pct_u6 >= 10 else "Most nights fall in the recommended range",
                   "Nights grouped into half-hour buckets. Orange marks short sleep"):
            fig = px.histogram(sleep_f, x="hours_asleep", color="sleep_category", color_discrete_map=SLEEP_COLORS,
                               category_orders={"sleep_category": SLEEP_ORDER})
            fig.update_traces(xbins=dict(start=0, size=0.5), marker_line_width=0)
            fig.update_layout(barmode="stack", bargap=0.05)
            fig.update_xaxes(title="Hours asleep")
            fig.update_yaxes(title="Number of nights")
            show(fig, legend=True)
    with c2:
        eff = sleep_f["sleep_efficiency"].mean()
        with panel("Efficiency", f"On average {eff:.0%} of time in bed is spent asleep",
                   "Points on the dashed line would mean falling asleep instantly and never waking"):
            fig = px.scatter(sleep_f, x="hours_in_bed", y="hours_asleep", color="sleep_category",
                             color_discrete_map=SLEEP_COLORS, category_orders={"sleep_category": SLEEP_ORDER}, opacity=.7)
            mx = float(max(sleep_f["hours_in_bed"].max(), sleep_f["hours_asleep"].max())) + 0.5
            fig.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines", name="100% efficient",
                                     line=dict(color=WHITE, dash="dash", width=1.5), hoverinfo="skip"))
            fig.update_traces(marker=dict(size=8), selector=dict(mode="markers"))
            fig.update_xaxes(title="Hours in bed", range=[0, mx])
            fig.update_yaxes(title="Hours asleep", range=[0, mx])
            show(fig, legend=True)

    gap()
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        wk = sleep_f.groupby("is_weekend")["hours_asleep"].mean()
        wd_h, we_h = wk.get(0, np.nan), wk.get(1, np.nan)
        head = (f"Weekend nights are {abs(we_h - wd_h) * 60:.0f} minutes {'longer' if we_h > wd_h else 'shorter'} than weekday nights"
                if not (np.isnan(wd_h) or np.isnan(we_h)) else "Weekday against weekend sleep")
        with panel("Weekday and weekend", head, "Full spread of nightly sleep. The line inside is the median"):
            fig = go.Figure()
            for flag, name, color in [(0, "Weekday", GRAY), (1, "Weekend", ORANGE)]:
                part = sleep_f[sleep_f["is_weekend"] == flag]["hours_asleep"]
                if len(part):
                    fig.add_trace(go.Violin(y=part, name=name, box_visible=True, meanline_visible=True,
                                            fillcolor=color, line_color=color if color != GRAY else LGRAY,
                                            opacity=.85, points=False, spanmode="hard"))
            fig.update_yaxes(title="Hours asleep")
            show(fig)
    with c4:
        dsl = sleep_f.groupby("day_of_week")["hours_asleep"].mean().reindex(WEEKDAY_ORDER).dropna()
        n_below = int((dsl < 7).sum())
        with panel("Night by night", f"{n_below} of {len(dsl)} days of the week average under 7 hours",
                   "Average hours asleep by the day the sleep is logged. Orange is under 7 hours"):
            fig = go.Figure(go.Bar(
                x=[d[:3] for d in dsl.index], y=dsl.values, marker_color=[ORANGE if v < 7 else GRAY for v in dsl.values],
                text=[f"{v:.1f}" for v in dsl.values], textposition="outside", cliponaxis=False,
                hovertemplate="%{x}: %{y:.2f} h<extra></extra>",
            ))
            fig.add_hline(y=7, line_dash="dash", line_color=WHITE, line_width=1.5,
                          annotation_text="7 h", annotation_font_color=WHITE, annotation_position="top left")
            fig.update_yaxes(range=[0, max(dsl.max() * 1.2, 8)], title="Hours asleep")
            fig.update_layout(bargap=0.28)
            show(fig)


# =============================================================================
# PAGE: BMI
# =============================================================================
BMI_ORDER = ["Underweight", "Normal", "Overweight", "Obese"]
BMI_COLORS = {"Underweight": STEEL, "Normal": PEACH, "Overweight": ORANGE, "Obese": "#B32B00"}


def page_bmi():
    hero("BMI", "Body mass index and weight trends. Only 8 users log weight, so read every chart as a hint, not proof.")
    if weight_f.empty:
        callout("No weight or BMI data for the current filters. Only 8 of 33 users log weight.")
        return

    per_user = weight_f.groupby("Id").agg(BMI=("BMI", "mean"), entries=("BMI", "size")).reset_index()
    per_user["category"] = per_user["BMI"].apply(bmi_category)
    n = len(per_user)
    n_high = int((per_user["BMI"] >= 25).sum())
    top2 = per_user["entries"].nlargest(2).sum()
    kpi_row([
        ("Average BMI", f"{per_user['BMI'].mean():.1f}", "average of each user's average"),
        ("Users with BMI data", f"{n}", "of 33 in the study"),
        ("Overweight or obese", f"{n_high}", f"of {n} users (BMI 25 or more)"),
        ("Weigh-ins recorded", f"{int(per_user['entries'].sum())}", f"top 2 users made {top2} of them"),
    ])

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        ordered = per_user.sort_values("BMI").copy()
        ordered["Id"] = ordered["Id"].astype(str)
        with panel("BMI by user", f"{n_high} of {n} users fall in the overweight or obese range",
                   "Each user's average BMI. Dotted lines mark the 25 and 30 category cut-offs"):
            fig = go.Figure(go.Bar(
                y=ordered["Id"], x=ordered["BMI"], orientation="h",
                marker_color=[BMI_COLORS[c] for c in ordered["category"]],
                text=[f"{v:.1f}" for v in ordered["BMI"]], textposition="outside", cliponaxis=False,
                customdata=ordered["category"], hovertemplate="User %{y}<br>BMI %{x:.1f} (%{customdata})<extra></extra>",
            ))
            for xv in (25, 30):
                fig.add_vline(x=xv, line_dash="dot", line_color=MUTED, annotation_text=str(xv),
                              annotation_font_color=MUTED, annotation_position="top")
            fig.update_yaxes(type="category", categoryorder="array", categoryarray=ordered["Id"])
            fig.update_xaxes(range=[15, max(ordered["BMI"].max() + 4, 32)], title="Average BMI")
            fig.update_layout(bargap=0.3)
            show(fig, height=max(330, n * 44))
    with c2:
        cnt = per_user["category"].value_counts().reindex(BMI_ORDER).fillna(0)
        with panel("Category mix", "Most users sit in the normal or overweight bands", "Users per WHO BMI category"):
            fig = go.Figure(go.Bar(
                x=BMI_ORDER, y=cnt.values, marker_color=[BMI_COLORS[c] for c in BMI_ORDER],
                text=[int(v) for v in cnt.values], textposition="outside", cliponaxis=False,
                hovertemplate="%{x}: %{y} users<extra></extra>",
            ))
            fig.update_yaxes(range=[0, max(cnt.max() * 1.3, 2)], title="Users", dtick=1)
            fig.update_layout(bargap=0.3)
            show(fig, height=max(330, n * 44))

    gap()
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        multi = weight_f.groupby("Id").filter(lambda g: len(g) > 3)
        two = weight_f.sort_values("date").groupby("Id").filter(lambda g: len(g) >= 2)
        if two.empty:
            with panel("Weight trend", "Not enough repeat weigh-ins to show a trend"):
                callout("Select more users, or widen the date range.")
        else:
            chg = two.sort_values("date").groupby("Id")["WeightKg"].agg(lambda s: s.iloc[-1] - s.iloc[0])
            with panel("Weight trend", f"Weight barely moves in a month (median net change {chg.median():+.1f} kg)",
                       "Users with four or more weigh-ins"):
                if multi.empty:
                    callout("No selected user has four or more weigh-ins.")
                else:
                    fig = go.Figure()
                    for i, (uid, g) in enumerate(multi.sort_values("date").groupby("Id")):
                        fig.add_trace(go.Scatter(x=g["date"], y=g["WeightKg"], mode="lines+markers", name=str(uid),
                                                 line=dict(color=CAT_COLORS[i % len(CAT_COLORS)], width=2.5),
                                                 marker=dict(size=7)))
                    fig.update_yaxes(title="Weight (kg)")
                    show(fig, legend=True)
    with c4:
        steps_user = base.groupby("Id")["TotalSteps"].mean().rename("steps").reset_index()
        m = per_user.merge(steps_user, on="Id")
        if len(m) < 3:
            with panel("BMI and activity", "Need at least three users with both BMI and step data"):
                callout("Select more users to see this comparison.")
        else:
            r = np.corrcoef(m["BMI"], m["steps"])[0, 1]
            head = ("Higher BMI goes with fewer daily steps" if r < -0.3
                    else "Higher BMI goes with more daily steps" if r > 0.3 else "No clear link between BMI and daily steps")
            with panel("BMI and activity", head, f"One dot per user. r = {r:.2f} on {len(m)} users, so treat it as suggestive"):
                fig = go.Figure()
                for cat in BMI_ORDER:
                    part = m[m["category"] == cat]
                    if len(part):
                        fig.add_trace(go.Scatter(x=part["BMI"], y=part["steps"], mode="markers", name=cat,
                                                 marker=dict(size=14, color=BMI_COLORS[cat], line=dict(color=CARD, width=1.5)),
                                                 customdata=part["Id"].astype(str),
                                                 hovertemplate="User %{customdata}<br>BMI %{x:.1f}<br>%{y:,.0f} steps<extra></extra>"))
                s, i0 = np.polyfit(m["BMI"], m["steps"], 1)
                xs = np.linspace(m["BMI"].min(), m["BMI"].max(), 30)
                fig.add_trace(go.Scatter(x=xs, y=s * xs + i0, mode="lines", name="Trend",
                                         line=dict(color=WHITE, dash="dash", width=1.5), hoverinfo="skip"))
                fig.update_xaxes(title="Average BMI")
                fig.update_yaxes(title="Average steps per day")
                show(fig, legend=True)


# =============================================================================
# PAGE: HOURLY PATTERNS
# =============================================================================
def page_hourly():
    hero("Hourly Patterns", "When during the day, and on which days, people are most active.")
    if hourly_f.empty:
        callout("No hourly data for the current filters.")
        return

    by_hour = hourly_f.groupby("hour")["StepTotal"].mean().reindex(range(24)).fillna(0)
    peak = int(by_hour.idxmax())
    split = hourly_f.groupby(["is_weekend", "hour"])["StepTotal"].mean().unstack(0).reindex(range(24)).fillna(0)
    wd_peak = int(split[0].idxmax()) if 0 in split else peak
    we_peak = int(split[1].idxmax()) if 1 in split else peak
    kpi_row([
        ("Peak hour", hour_label(peak), "highest average steps"),
        ("Steps at the peak", f"{by_hour.max():,.0f}", "average per user in that hour"),
        ("Weekday peak", hour_label(wd_peak), "Monday to Friday"),
        ("Weekend peak", hour_label(we_peak), "Saturday and Sunday"),
    ])

    with panel("Time of day", f"Activity builds from 6 AM and peaks at {hour_label(peak)}",
               "Average steps per user in each hour of the day. Darker bars are quieter hours"):
        fig = go.Figure(go.Bar(
            x=by_hour.index, y=by_hour.values,
            marker=dict(color=by_hour.values, colorscale=[[0, "#2A2A2E"], [0.5, "#B33A0C"], [1, ORANGE]], line=dict(width=0)),
            customdata=[hour_label(h) for h in by_hour.index],
            hovertemplate="%{customdata}: %{y:,.0f} steps<extra></extra>",
        ))
        fig.add_annotation(x=peak, y=by_hour.max(), text=f"Peak: {hour_label(peak)}", showarrow=True, arrowcolor=WHITE,
                           arrowhead=2, ax=0, ay=-34, font=dict(color=WHITE, size=13))
        fig.update_xaxes(tickmode="array", tickvals=list(range(0, 24, 2)), ticktext=[hour_label(h) for h in range(0, 24, 2)])
        fig.update_yaxes(title="Average steps", range=[0, by_hour.max() * 1.25])
        fig.update_layout(bargap=0.12)
        show(fig, height=340)

    gap()
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        diff = (split[1] - split[0]) if (0 in split and 1 in split) else pd.Series(0, index=range(24))
        with panel("Weekday and weekend",
                   f"Weekends start later and taper differently (peak {hour_label(we_peak)} against {hour_label(wd_peak)})"
                   if we_peak != wd_peak else f"Both day types peak at {hour_label(peak)}",
                   "Average steps per hour"):
            fig = go.Figure()
            if 0 in split:
                fig.add_trace(go.Scatter(x=split.index, y=split[0], name="Weekday", mode="lines+markers",
                                         line=dict(color=ORANGE, width=3), marker=dict(size=5)))
            if 1 in split:
                fig.add_trace(go.Scatter(x=split.index, y=split[1], name="Weekend", mode="lines+markers",
                                         line=dict(color=PEACH, width=3, dash="dot"), marker=dict(size=5)))
            fig.update_xaxes(tickmode="array", tickvals=list(range(0, 24, 3)), ticktext=[hour_label(h) for h in range(0, 24, 3)])
            fig.update_yaxes(title="Average steps")
            show(fig, height=360, legend=True)
    with c2:
        heat = (hourly_f.groupby(["day_of_week", "hour"])["StepTotal"].mean().unstack("hour")
                .reindex(index=WEEKDAY_ORDER, columns=range(24)))
        flat = heat.stack()
        best_day, best_hour = flat.idxmax() if len(flat.dropna()) else ("", 0)
        with panel("Week at a glance", f"The busiest slot is {best_day} at {hour_label(best_hour)}" if best_day else "Busiest slot",
                   "Average steps for every day and hour. Brighter means busier"):
            fig = go.Figure(go.Heatmap(
                z=heat.values, x=[hour_label(h) for h in heat.columns], y=[d[:3] for d in heat.index],
                colorscale=[[0, "#121214"], [0.35, "#5C240B"], [0.7, ORANGE], [1, "#FFD9C4"]],
                colorbar=dict(title="Steps", thickness=10, len=0.85, tickfont=dict(color=MUTED), title_font=dict(color=MUTED)),
                hovertemplate="%{y} %{x}<br>%{z:,.0f} steps<extra></extra>", xgap=2, ygap=2,
            ))
            fig.update_yaxes(autorange="reversed", showgrid=False)
            fig.update_xaxes(showgrid=False, tickangle=0, tickmode="array",
                             tickvals=[hour_label(h) for h in range(0, 24, 4)])
            show(fig, height=360)


# =============================================================================
# PAGE: SQL ANALYSIS
# =============================================================================
# (id, title, group, question, sql)
QUERIES = [
    ("Q1", "Overall steps range", "Daily activity", "How many steps do users take on a typical worn day, and what are the extremes?",
     """SELECT ROUND(AVG(TotalSteps),0) AS avg_steps, MIN(TotalSteps) AS min_steps, MAX(TotalSteps) AS max_steps
FROM daily_activity WHERE is_worn = 1;"""),
    ("Q2", "Top 5 most active users", "Daily activity", "Who are the five most active users by average daily steps?",
     """SELECT Id, ROUND(AVG(TotalSteps),0) AS avg_steps
FROM daily_activity WHERE is_worn = 1
GROUP BY Id ORDER BY avg_steps DESC LIMIT 5;"""),
    ("Q3", "Avg steps and calories by weekday", "Daily activity", "Which day of the week is busiest, and which is quietest?",
     """SELECT day_of_week, ROUND(AVG(TotalSteps),0) AS avg_steps, ROUND(AVG(Calories),0) AS avg_calories
FROM daily_activity WHERE is_worn = 1
GROUP BY day_of_week ORDER BY avg_steps DESC;"""),
    ("Q4", "Share of days below 7,500 steps", "Daily activity", "How often do users fall below the 7,500-step 'lightly active' mark?",
     """SELECT ROUND(100.0 * SUM(CASE WHEN TotalSteps < 7500 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_below_7500_steps
FROM daily_activity WHERE is_worn = 1;"""),
    ("Q5", "Share of time by intensity", "Daily activity", "How is the day split between sedentary, light, fair and very active time?",
     """SELECT
  ROUND(SUM(SedentaryMinutes)*100.0/SUM(SedentaryMinutes+LightlyActiveMinutes+FairlyActiveMinutes+VeryActiveMinutes),1) AS pct_sedentary,
  ROUND(SUM(LightlyActiveMinutes)*100.0/SUM(SedentaryMinutes+LightlyActiveMinutes+FairlyActiveMinutes+VeryActiveMinutes),1) AS pct_light,
  ROUND(SUM(FairlyActiveMinutes)*100.0/SUM(SedentaryMinutes+LightlyActiveMinutes+FairlyActiveMinutes+VeryActiveMinutes),1) AS pct_fair,
  ROUND(SUM(VeryActiveMinutes)*100.0/SUM(SedentaryMinutes+LightlyActiveMinutes+FairlyActiveMinutes+VeryActiveMinutes),1) AS pct_very
FROM daily_activity WHERE is_worn = 1;"""),
    ("Q6", "Users with the fewest logged days", "Daily activity", "Which users are the least engaged, judged by days logged?",
     """SELECT Id, COUNT(*) AS days_logged FROM daily_activity
GROUP BY Id ORDER BY days_logged ASC LIMIT 5;"""),
    ("Q7", "Average sleep and time in bed", "Sleep", "How long do users sleep, and how long do they spend in bed?",
     """SELECT ROUND(AVG(hours_asleep),2) AS avg_sleep_hours, ROUND(AVG(hours_in_bed),2) AS avg_in_bed_hours
FROM sleep_daily;"""),
    ("Q8", "Lowest sleep efficiency", "Sleep", "Which users spend the most time in bed awake?",
     """SELECT Id, ROUND(AVG(sleep_efficiency),3) AS avg_efficiency
FROM sleep_daily GROUP BY Id ORDER BY avg_efficiency ASC LIMIT 5;"""),
    ("Q9", "Sleep against total users", "Sleep", "How many users log sleep at all? (the engagement gap)",
     """SELECT
  (SELECT COUNT(DISTINCT Id) FROM sleep_daily) AS users_with_sleep,
  (SELECT COUNT(DISTINCT Id) FROM daily_activity) AS users_total;"""),
    ("Q10", "Weekday against weekend sleep", "Sleep", "Do people sleep longer on weekends?",
     """SELECT is_weekend, ROUND(AVG(hours_asleep),2) AS avg_hours
FROM sleep_daily GROUP BY is_weekend;"""),
    ("Q11", "Consistent under- or over-sleepers", "Sleep", "Who averages under 6 or over 9 hours of sleep?",
     """SELECT Id, ROUND(AVG(hours_asleep),2) AS avg_sleep, COUNT(*) AS nights
FROM sleep_daily GROUP BY Id HAVING avg_sleep < 6 OR avg_sleep > 9 ORDER BY avg_sleep;"""),
    ("Q12", "Average BMI category per user", "BMI and weight", "What is each user's average weight, BMI and BMI category?",
     """SELECT Id, ROUND(AVG(WeightKg),1) AS avg_weight_kg, ROUND(AVG(BMI),1) AS avg_bmi,
  CASE WHEN AVG(BMI) < 18.5 THEN 'Underweight'
       WHEN AVG(BMI) < 25 THEN 'Normal'
       WHEN AVG(BMI) < 30 THEN 'Overweight'
       ELSE 'Obese' END AS bmi_category
FROM weight_log GROUP BY Id ORDER BY avg_bmi;"""),
    ("Q13", "Weight against total users", "BMI and weight", "How many users log weight at all? (the engagement gap)",
     """SELECT COUNT(DISTINCT Id) AS users_with_weight FROM weight_log;"""),
    ("Q14", "Weight change, first against last", "BMI and weight", "Did anyone's weight change over the month?",
     """WITH first_last AS (
  SELECT Id,
    FIRST_VALUE(WeightKg) OVER (PARTITION BY Id ORDER BY date) AS first_w,
    FIRST_VALUE(WeightKg) OVER (PARTITION BY Id ORDER BY date DESC) AS last_w
  FROM weight_log
)
SELECT DISTINCT Id, first_w, last_w, ROUND(last_w-first_w,1) AS change_kg
FROM first_last ORDER BY change_kg;"""),
    ("Q15", "Manual against automatic entries", "BMI and weight", "Are weigh-ins typed in by hand or synced from a smart scale?",
     """SELECT IsManualReport, COUNT(*) AS n FROM weight_log GROUP BY IsManualReport;"""),
    ("Q16", "Sleep and next-day activity", "Across tables", "Does a longer night predict a more active next day?",
     """SELECT ROUND(AVG(s.hours_asleep),2) AS avg_prev_sleep,
       ROUND(AVG(a.TotalSteps),0) AS avg_next_day_steps,
       COUNT(*) AS matched_days
FROM sleep_daily s
JOIN daily_activity a ON a.Id = s.Id AND date(a.date) = date(s.date, '+1 day')
WHERE a.is_worn = 1;"""),
    ("Q17", "BMI against activity per user", "Across tables", "Do users with a lower BMI walk more?",
     """SELECT w.Id, ROUND(AVG(w.BMI),1) AS avg_bmi, ROUND(AVG(a.TotalSteps),0) AS avg_steps
FROM weight_log w JOIN daily_activity a ON a.Id = w.Id AND a.is_worn = 1
GROUP BY w.Id ORDER BY avg_bmi;"""),
    ("Q18", "Users with activity, sleep and weight", "Across tables", "Who has all three data types logged on overlapping days?",
     """SELECT a.Id, ROUND(AVG(a.TotalSteps),0) AS avg_steps,
       ROUND(AVG(s.hours_asleep),2) AS avg_sleep, ROUND(AVG(w.BMI),1) AS avg_bmi
FROM daily_activity a
JOIN sleep_daily s ON s.Id = a.Id AND date(s.date) = date(a.date)
JOIN weight_log w ON w.Id = a.Id
WHERE a.is_worn = 1
GROUP BY a.Id;"""),
    ("Q19", "Top 5 peak hours", "Hourly", "Which hours of the day have the most steps?",
     """SELECT hour, ROUND(AVG(StepTotal),0) AS avg_steps
FROM hourly_activity GROUP BY hour ORDER BY avg_steps DESC LIMIT 5;"""),
    ("Q20", "Weekday against weekend intensity", "Hourly", "How does hourly intensity differ between weekdays and weekends?",
     """SELECT is_weekend, hour, ROUND(AVG(TotalIntensity),1) AS avg_intensity
FROM hourly_activity GROUP BY is_weekend, hour ORDER BY hour, is_weekend;"""),
]


def page_sql():
    hero(
        "SQL Analysis",
        "All 20 saved queries from Sql/analysis_queries.sql, run live on db/fitbit.db. "
        "Sidebar filters do not apply here because the queries use the full dataset.",
    )
    tab_saved, tab_own = st.tabs(["Saved queries", "Run your own"])

    with tab_saved:
        groups = ["All"] + list(dict.fromkeys(q[2] for q in QUERIES))
        c1, c2 = st.columns([1, 2], gap="medium")
        group = c1.selectbox("Topic", groups)
        pool = [q for q in QUERIES if group == "All" or q[2] == group]
        labels = [f"{q[0]}: {q[1]}" for q in pool]
        choice = c2.selectbox("Query", labels)
        qid, title, grp, question, sql = pool[labels.index(choice)]

        left, right = st.columns([1, 1], gap="medium")
        with left:
            with panel(grp, question, f"{qid}: {title}"):
                st.code(sql, language="sql")
        with right:
            result = run_query(sql)
            with panel("Result", f"{len(result):,} row{'s' if len(result) != 1 else ''} returned"):
                show_df(result, height=min(420, 60 + 36 * len(result)))
                st.download_button("Download result as CSV", result.to_csv(index=False).encode(),
                                   file_name=f"{qid.lower()}_result.csv", mime="text/csv")

    with tab_own:
        with panel("Your query", "Ask your own question",
                   "Read-only. Tables: daily_activity, sleep_daily, weight_log, hourly_activity"):
            user_sql = st.text_area(
                "SQL", height=170, label_visibility="collapsed",
                value="SELECT day_of_week, ROUND(AVG(TotalSteps),0) AS avg_steps\nFROM daily_activity\nWHERE is_worn = 1\nGROUP BY day_of_week\nORDER BY avg_steps DESC;",
            )
            run = st.button("Run query", type="primary")
        if run:
            cleaned = user_sql.strip().rstrip(";").strip()
            if not cleaned.lower().startswith(("select", "with")):
                st.error("Only SELECT queries are allowed.")
            elif ";" in cleaned:
                st.error("Run one statement at a time.")
            else:
                try:
                    out = run_query(cleaned)
                    gap()
                    with panel("Result", f"{len(out):,} row{'s' if len(out) != 1 else ''} returned"):
                        show_df(out.head(1000), height=min(460, 60 + 36 * min(len(out), 10)))
                        if len(out) > 1000:
                            st.caption("Showing the first 1,000 rows.")
                except Exception as exc:
                    st.error(f"The query failed: {exc}")


# =============================================================================
# PAGE: FINDINGS & RECOMMENDATIONS
# =============================================================================
def page_findings():
    hero(
        "Findings & Recommendations",
        "What the data says and what Bellabeat should do next. Figures here use the full dataset, not the sidebar filters.",
    )
    dw = daily_worn_all
    pct_below = (dw["TotalSteps"] < STEP_GOAL).mean() * 100
    tot = dw[["SedentaryMinutes", "LightlyActiveMinutes", "FairlyActiveMinutes", "VeryActiveMinutes"]].sum()
    sed = tot.iloc[0] / tot.sum() * 100
    act = (tot.iloc[2] + tot.iloc[3]) / tot.sum() * 100
    dow = dw.groupby("day_of_week")["TotalSteps"].mean()
    low_day, high_day = dow.idxmin(), dow.idxmax()

    n_users, n_sleep, n_weight = daily["Id"].nunique(), sleep["Id"].nunique(), weight["Id"].nunique()
    top2 = weight.groupby("Id").size().nlargest(2).sum()
    overlap = dw.merge(sleep[["Id", "date"]], on=["Id", "date"])
    n_all3 = overlap[overlap["Id"].isin(weight["Id"].unique())]["Id"].nunique()

    n_u6, n_nights = int((sleep["hours_asleep"] < 6).sum()), len(sleep)
    wk = sleep.groupby("is_weekend")["hours_asleep"].mean()
    nxt = sleep[["Id", "date", "hours_asleep"]].copy()
    nxt["next"] = nxt["date"] + pd.Timedelta(days=1)
    nxt = nxt.merge(dw[["Id", "date", "TotalSteps"]], left_on=["Id", "next"], right_on=["Id", "date"])
    r_sleep = nxt["hours_asleep"].corr(nxt["TotalSteps"])

    by_hour = hourly.groupby("hour")["StepTotal"].mean()
    peak = int(by_hour.idxmax())

    bmi_user = weight.groupby("Id")["BMI"].mean().rename("BMI").reset_index()
    mc = dw.merge(bmi_user, on="Id", how="left")
    r_bmi_steps = mc["TotalSteps"].corr(mc["BMI"])
    r_bmi_act = mc["total_active_minutes"].corr(mc["BMI"])

    st.markdown('<div class="p-title" style="font-size:1.5rem;margin:.2rem 0 .8rem 0">Key findings</div>', unsafe_allow_html=True)

    def finding(stat, title, body):
        with panel("Finding", title):
            st.markdown(f'<div class="finding-stat">{stat}</div><div class="finding-body" style="margin-top:.6rem">{body}</div>',
                        unsafe_allow_html=True)

    a, b, c = st.columns(3, gap="medium")
    with a:
        finding(f"{pct_below:.0f}%", "Most users fall short of common activity guidelines",
                f"of tracked days end under {STEP_GOAL:,} steps. <b>{sed:.1f}%</b> of tracked time is sedentary and fairly plus very "
                f"active minutes add up to only <b>{act:.1f}%</b>. <b>{low_day}</b> is the quietest day and <b>{high_day}</b> the busiest.")
    with b:
        finding(f"{n_users} > {n_sleep} > {n_weight}", "Engagement drops sharply beyond step tracking",
                f"Everyone tracks activity, <b>{n_sleep}</b> log sleep ({n_sleep / n_users:.0%}) and only <b>{n_weight}</b> log weight "
                f"({n_weight / n_users:.0%}). Two users made {top2} of {len(weight)} weigh-ins. Just <b>{n_all3}</b> users have activity, "
                f"sleep and weight on overlapping days.")
    with c:
        finding(f"{n_u6 / n_nights:.0%}", "Sleep is uneven and does not predict next-day activity",
                f"of nights ({n_u6} of {n_nights}) are under 6 hours. Weekends run longer ({wk.get(1, np.nan):.2f} h against "
                f"{wk.get(0, np.nan):.2f} h). Sleep and next-day steps correlate at only <b>r = {r_sleep:.2f}</b>.")
    gap()
    d, e = st.columns(2, gap="medium")
    with d:
        finding(hour_label(peak), "Activity peaks in the early evening",
                "Steps climb from 6 AM and top out in the early evening on both weekdays and weekends. "
                "It is one consistent window across the whole user base.")
    with e:
        finding(f"r = {r_bmi_steps:.2f}", "Lower BMI goes with more activity in this small sample",
                f"With only {n_weight} users, BMI against steps is <b>{r_bmi_steps:.2f}</b> and against active minutes "
                f"<b>{r_bmi_act:.2f}</b>. The direction fits expectations, but the sample is too small to generalise.")

    gap()
    st.markdown('<div class="p-title" style="font-size:1.5rem;margin:.6rem 0 .8rem 0">Recommendations for Bellabeat</div>', unsafe_allow_html=True)

    def rec(n, head, action, why):
        with panel("Recommendation", ""):
            st.markdown(
                f'<div class="rec-head"><span class="rec-num">{n}</span>{head}</div>'
                f'<div class="finding-body" style="margin-top:.6rem">{action}</div>'
                f'<div class="rec-why">Evidence: {why}</div>', unsafe_allow_html=True)

    r1, r2 = st.columns(2, gap="medium")
    with r1:
        rec(1, "Send activity nudges at 6 to 7 PM",
            "Notifications land best when people are already moving. Time reminders and challenges for the early evening "
            "instead of trying to create momentum from nothing.",
            f"the {hour_label(peak)} hour is the daily peak on weekdays and weekends.")
    with r2:
        rec(2, f"Run a {low_day} reset challenge",
            f"{low_day} is the lowest day of the week. A short weekly challenge or streak that starts that day targets the dip directly.",
            f"average steps are lowest on {low_day} and highest on {high_day}.")
    gap()
    r3, r4 = st.columns(2, gap="medium")
    with r3:
        rec(3, "Reward sleep and weight logging, not just steps",
            "The drop-off looks like underuse, not disinterest. Streaks, weekly summaries and easy syncing with a smart scale "
            "would close the gap.",
            f"{n_users} users track activity, {n_sleep} log sleep and {n_weight} log weight.")
    with r4:
        rec(4, "Market sleep and activity as separate benefits",
            "Do not claim that better sleep makes people more active. Promote each feature on its own strengths.",
            f"last night's sleep and next-day steps correlate at only r = {r_sleep:.2f}.")
    gap()
    rec(5, "Segment messages by baseline activity",
        "Speak differently to each group: \"keep your streak\" for the most active users and \"take the first step\" for the least active.",
        f"{pct_below:.0f}% of days are under {STEP_GOAL:,} steps, and users differ widely in their averages.")

    gap()
    callout(
        "<b>Limitations.</b> Small, self-selected sample of 33 users over 31 days, so it is not representative of Bellabeat's full "
        "customer base. Sleep and especially weight conclusions rest on a minority of users. Minute-level and heart-rate data were "
        "excluded by design."
    )


# =============================================================================
# ROUTER
# =============================================================================
{
    "Overview": page_overview,
    "Daily Activity": page_daily,
    "Sleep": page_sleep,
    "BMI": page_bmi,
    "Hourly Patterns": page_hourly,
    "SQL Analysis": page_sql,
    "Findings & Recommendations": page_findings,
}[st.session_state["page"]]()
