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
