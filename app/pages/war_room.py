"""War Room: rankings board with four positional columns and tier grouping."""

from __future__ import annotations

from collections import defaultdict

import streamlit as st

from utils.constants import POSITIONS
from utils.rankings import (
    add_player,
    delete_player,
    get_position_players,
    save_rankings,
    swap_players,
)


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------


@st.dialog("\U0001f4cb Notes")
def notes_dialog(player_name: str, player_team: str, position: str, rank: int) -> None:
    """Edit notes for a player."""
    st.subheader(f"{player_name} \u00b7 {player_team}")

    # Find current notes
    profile = st.session_state.rankings
    current_notes = ""
    for p in profile["players"]:
        if p["position"] == position and p["position_rank"] == rank:
            current_notes = p["notes"]
            break

    notes = st.text_area(
        "Notes",
        value=current_notes,
        height=150,
        placeholder="Add scouting notes...",
        label_visibility="collapsed",
    )

    col_save, col_close = st.columns(2)
    with col_save:
        if st.button("Save", use_container_width=True, key="notes_save"):
            for p in st.session_state.rankings["players"]:
                if p["position"] == position and p["position_rank"] == rank:
                    p["notes"] = notes
                    break
            st.session_state.dirty = True
            st.rerun()
    with col_close:
        if st.button("Close", use_container_width=True, key="notes_close"):
            st.rerun()


@st.dialog("Add Player")
def add_player_dialog(position: str, tier: int) -> None:
    """Add a new player to a position and tier."""
    st.markdown(f"**Position:** {position}  \u2502  **Tier:** {tier}")

    name = st.text_input("Name", key="add_name")
    team = st.text_input("Team", key="add_team", max_chars=3)

    col_add, col_cancel = st.columns(2)
    with col_add:
        if st.button("Add", use_container_width=True, key="add_confirm"):
            if not name.strip() or not team.strip():
                st.error("Name and team are required")
                return
            # Duplicate check (case-insensitive within position)
            existing = get_position_players(st.session_state.rankings, position)
            if any(p["name"].lower() == name.strip().lower() for p in existing):
                st.error(f"Already in {position} rankings")
                return
            st.session_state.rankings = add_player(
                st.session_state.rankings,
                name.strip(),
                team.strip().upper(),
                position,
                tier,
            )
            st.session_state.dirty = True
            st.rerun()
    with col_cancel:
        if st.button("Cancel", use_container_width=True, key="add_cancel"):
            st.rerun()


@st.dialog("Delete Player")
def delete_confirm_dialog(
    player_name: str, player_team: str, position: str, rank: int
) -> None:
    """Confirm deletion of a player."""
    st.markdown(
        f"Remove **{player_name}** ({player_team}) from {position} rankings?"
    )
    st.caption("This cannot be undone.")

    col_del, col_cancel = st.columns(2)
    with col_del:
        if st.button(
            "Delete", use_container_width=True, key="del_confirm", type="primary"
        ):
            st.session_state.rankings = delete_player(
                st.session_state.rankings, position, rank
            )
            st.session_state.dirty = True
            st.rerun()
    with col_cancel:
        if st.button("Cancel", use_container_width=True, key="del_cancel"):
            st.rerun()


# ---------------------------------------------------------------------------
# Column rendering
# ---------------------------------------------------------------------------


def _render_position_column(position: str) -> None:
    """Render a single position column with tier groups and player rows."""
    players = get_position_players(st.session_state.rankings, position)

    st.markdown(f"### {position}")
    if not players:
        st.info(f"No {position} players in rankings.")
        return

    st.caption(f"{len(players)} players")
    last_rank = players[-1]["position_rank"]

    # Group by tier — all players with same tier together
    tier_groups: dict[int, list[dict]] = defaultdict(list)
    for p in players:
        tier_groups[p["tier"]].append(p)

    for tier in sorted(tier_groups.keys()):
        tier_players = tier_groups[tier]

        # Alternating tier header background
        tier_bg = "#132338" if tier % 2 == 0 else "#1A4A6B"
        st.markdown(
            f'<div style="background:{tier_bg}; border-radius:4px; '
            f'padding:3px 8px; margin:8px 0 4px 0; '
            f'font-size:10px; letter-spacing:2px; color:#7AAFD4;">'
            f"\u2014 TIER {tier} \u2014</div>",
            unsafe_allow_html=True,
        )

        # Player rows
        for p in tier_players:
            rank = p["position_rank"]
            name_label = p["name"]
            if p["notes"]:
                name_label += " \U0001f4dd"

            c_up, c_dn, c_rank, c_name, c_team = st.columns(
                [1, 1, 1, 6, 2]
            )

            with c_up:
                if st.button(
                    "\u25b2",
                    key=f"up_{position}_{rank}",
                    disabled=(rank == 1),
                    use_container_width=True,
                ):
                    st.session_state.rankings = swap_players(
                        st.session_state.rankings, position, rank - 1, rank
                    )
                    st.session_state.dirty = True
                    st.rerun()

            with c_dn:
                if st.button(
                    "\u25bc",
                    key=f"dn_{position}_{rank}",
                    disabled=(rank == last_rank),
                    use_container_width=True,
                ):
                    st.session_state.rankings = swap_players(
                        st.session_state.rankings, position, rank, rank + 1
                    )
                    st.session_state.dirty = True
                    st.rerun()

            with c_rank:
                st.markdown(
                    f"<span style='color:#666; font-size:0.85em;'>{rank}</span>",
                    unsafe_allow_html=True,
                )

            with c_name:
                if st.button(
                    name_label,
                    key=f"name_{position}_{rank}",
                    use_container_width=True,
                ):
                    notes_dialog(p["name"], p["team"], position, rank)

            with c_team:
                tc1, tc2 = st.columns([3, 1])
                with tc1:
                    st.markdown(
                        f"<span style='color:#666; font-size:0.85em;'>"
                        f"{p['team']}</span>",
                        unsafe_allow_html=True,
                    )
                with tc2:
                    if st.button(
                        "\u2715",
                        key=f"del_{position}_{rank}",
                        use_container_width=True,
                    ):
                        delete_confirm_dialog(
                            p["name"], p["team"], position, rank
                        )

        # Add-to-tier button at bottom of each tier group
        if st.button(
            f"+ {position} \u00b7 Tier {tier}",
            key=f"add_{position}_t{tier}",
            use_container_width=True,
        ):
            add_player_dialog(position, tier)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------


def render() -> None:
    """Render the War Room rankings board."""
    # Header row
    h_title, h_indicator, h_save = st.columns([6, 2, 1])

    with h_title:
        st.title("\U0001f3c8 WAR ROOM")

    with h_indicator:
        if st.session_state.dirty:
            st.markdown(
                "<p style='color:#0076B6; font-size:1.1em; padding-top:28px;'>"
                "\u25cf Unsaved</p>",
                unsafe_allow_html=True,
            )

    with h_save:
        st.markdown("<div style='padding-top:24px;'></div>", unsafe_allow_html=True)
        if st.button("SAVE", key="save_rankings", use_container_width=True):
            success = save_rankings(st.session_state.rankings)
            if success:
                st.session_state.dirty = False
                st.toast("Rankings saved \u2713")
                st.rerun()
            else:
                st.error("Save failed \u2014 check file permissions.")

    # Four position columns
    columns = st.columns([1, 1, 1, 1], gap="large")
    for col, position in zip(columns, POSITIONS):
        with col:
            _render_position_column(position)
