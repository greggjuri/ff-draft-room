"""History: historical stats browser."""

import pandas as pd
import streamlit as st

from utils.constants import POSITIONS, YEARS

DISPLAY_COLUMNS = {
    "rank": "Rank",
    "name": "Player",
    "team": "Team",
    "year": "Season",
    "gp": "GP",
    "ppg": "Avg Pts",
    "total_pts": "Total Pts",
}


def filter_players(
    df: pd.DataFrame,
    position: str,
    year: int,
    search: str = "",
) -> pd.DataFrame:
    """Filter and prepare player DataFrame for display.

    Operates on a copy — never mutates the input DataFrame.
    Drops position column and renames columns for display.
    """
    filtered = df[(df["year"] == year) & (df["position"] == position)].copy()

    if search:
        filtered = filtered[
            filtered["name"].str.contains(search, case=False, na=False)
        ]

    filtered = filtered.drop(columns=["position"])
    filtered = filtered.rename(columns=DISPLAY_COLUMNS)

    return filtered


def render() -> None:
    st.title("\U0001f4cb History")
    st.caption("FantasyPros Half-PPR Season Leaders, 2020\u20132025")

    df = st.session_state.get("df")
    if df is None or df.empty:
        st.warning(
            "No data loaded. Check that CSV files are present in data/players/."
        )
        return

    # Controls row
    col_year, col_search = st.columns([1, 3])
    with col_year:
        year = st.selectbox("Season", list(reversed(YEARS)), index=0)
    with col_search:
        search = st.text_input(
            "Search player", placeholder="e.g. Justin Jefferson"
        )

    # Position tabs
    tabs = st.tabs(POSITIONS)
    for tab, position in zip(tabs, POSITIONS):
        with tab:
            filtered = filter_players(df, position, year, search)

            if filtered.empty:
                if search:
                    st.info(f"No players matching '{search}'.")
                else:
                    st.info(f"No players found for {position} in {year}.")
            else:
                st.dataframe(
                    filtered,
                    use_container_width=True,
                    hide_index=True,
                )
                st.caption(f"{len(filtered)} players \u2014 {year} {position}")
