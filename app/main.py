"""FF Draft Room — Streamlit entry point and navigation."""

from pathlib import Path

import streamlit as st

from pages import live_draft, war_room
from utils.data_loader import load_all_players
from utils.rankings import load_or_seed

st.set_page_config(
    page_title="FF Draft Room",
    page_icon="\U0001f3c8",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Lighter background — dark navy instead of near-black */
.stApp { background-color: #0D1B2A !important; }

/* Hide sidebar completely */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] { display: none !important; }

/* Smaller, tighter base font */
html, body, [class*="css"] { font-size: 11px !important; }

/* Vertical divider between columns */
[data-testid="column"] {
    border-right: 2px solid #1E3A5F !important;
    padding-right: 28px !important;
    padding-left: 28px !important;
    margin-right: 8px !important;
}
[data-testid="column"]:last-child {
    border-right: none !important;
    margin-right: 0 !important;
}

/* Compact buttons — kill padding, tighten height */
.stButton > button {
    padding: 1px 4px !important;
    font-size: 11px !important;
    line-height: 1.1 !important;
    min-height: 0 !important;
    height: 24px !important;
}

/* Player name — visible box, fixed height, left-aligned text */
.stButton > button[kind="secondary"] {
    background: #1A3A5C !important;
    border: 1px solid #2A5A8C !important;
    border-radius: 4px !important;
    text-align: left !important;
    padding: 2px 8px !important;
    color: #E8E8E8 !important;
    width: 100% !important;
    height: 28px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #0076B6 !important;
    border-color: #0076B6 !important;
    color: #FFFFFF !important;
}

/* Kill gap between rows */
[data-testid="stVerticalBlock"] > div { gap: 2px !important; }

/* Tier divider text — muted, no extra space */
hr { margin: 4px 0 !important; border-color: #1E3A5F !important; }
</style>
""", unsafe_allow_html=True)

# -- Data loading & session state ---------------------------------------------

df = load_all_players()

if "df" not in st.session_state:
    st.session_state.df = df

if "rankings" not in st.session_state:
    st.session_state.rankings = load_or_seed(df)

if "dirty" not in st.session_state:
    st.session_state.dirty = False

# -- Sidebar ------------------------------------------------------------------

with st.sidebar:
    # Logo with graceful fallback
    logo_path = Path(__file__).parent.parent / "assets" / "ff-logo.jpg"
    if logo_path.exists():
        st.image(str(logo_path), width=200)
    else:
        st.title("\U0001f3c8 FF Draft Room")

    page = st.radio(
        "Navigation",
        ["War Room", "Live Draft"],
        label_visibility="collapsed",
    )

# -- Sidebar footer ------------------------------------------------------------

with st.sidebar:
    n = len(df)
    if n > 0:
        st.caption(f"\u2713 {n} player-seasons loaded")
    else:
        st.warning("No player data found. Add CSV files to data/players/.")

# -- Page routing --------------------------------------------------------------

PAGES = {
    "War Room": war_room,
    "Live Draft": live_draft,
}

PAGES[page].render()
