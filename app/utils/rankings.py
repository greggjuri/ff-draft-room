"""Rankings profile save/load/manage operations."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.constants import POSITIONS

RANKINGS_DIR: Path = Path(__file__).parent.parent.parent / "data" / "rankings"

SEED_LIMITS: dict[str, int] = {"QB": 30, "RB": 50, "WR": 50, "TE": 30}

TIER_BREAKPOINTS: dict[str, list[tuple[int, int]]] = {
    "QB": [(3, 1), (6, 2), (10, 3), (14, 4), (18, 5), (24, 6), (30, 7)],
    "RB": [(4, 1), (8, 2), (12, 3), (16, 4), (24, 5), (32, 6), (42, 7), (50, 8)],
    "WR": [(4, 1), (8, 2), (16, 3), (24, 4), (36, 5), (50, 6)],
    "TE": [(3, 1), (6, 2), (10, 3), (14, 4), (18, 5), (24, 6), (30, 7)],
}


def _assign_tier(position: str, rank: int) -> int:
    """Map a position rank to a tier number using TIER_BREAKPOINTS."""
    breakpoints = TIER_BREAKPOINTS.get(position, [])
    for max_rank, tier in breakpoints:
        if rank <= max_rank:
            return tier
    # Beyond last breakpoint — return last tier number
    if breakpoints:
        return breakpoints[-1][1]
    return 1


def seed_rankings(df: pd.DataFrame) -> dict:
    """Create initial rankings profile from 2025 data.

    Filters to year == 2025, takes top N per position by total_pts,
    assigns position_rank, tier, and empty notes.
    """
    df_2025 = df[df["year"] == 2025]
    if df_2025.empty:
        st.error("No 2025 data. Check data/players/ CSV files.")
        return {
            "name": "2026 Draft",
            "created": datetime.now(timezone.utc).isoformat(),
            "modified": datetime.now(timezone.utc).isoformat(),
            "league": {"teams": 10, "scoring": "half_ppr"},
            "players": [],
        }

    players: list[dict] = []
    for position in POSITIONS:
        pos_df = df_2025[df_2025["position"] == position].copy()
        pos_df = pos_df.sort_values("total_pts", ascending=False)
        limit = SEED_LIMITS.get(position, 20)
        pos_df = pos_df.head(limit)

        for i, (_, row) in enumerate(pos_df.iterrows(), start=1):
            players.append({
                "position_rank": i,
                "name": row["name"],
                "team": row["team"],
                "position": position,
                "tier": _assign_tier(position, i),
                "notes": "",
            })

    now = datetime.now(timezone.utc).isoformat()
    return {
        "name": "2026 Draft",
        "created": now,
        "modified": now,
        "league": {"teams": 10, "scoring": "half_ppr"},
        "players": players,
    }


def load_or_seed(df: pd.DataFrame, rankings_dir: Path | None = None) -> dict:
    """Load existing profile or seed from CSV data.

    If default.json exists and is valid, load it.
    If missing or corrupted, seed from data and save.
    """
    if rankings_dir is None:
        rankings_dir = RANKINGS_DIR

    path = rankings_dir / "default.json"

    if path.exists():
        try:
            with open(path) as f:
                profile = json.load(f)
            if "players" in profile:
                return profile
        except (json.JSONDecodeError, KeyError):
            st.warning("Rankings corrupted \u2014 re-seeding.")

    # Seed and save
    profile = seed_rankings(df)
    rankings_dir.mkdir(parents=True, exist_ok=True)
    save_rankings(profile, rankings_dir=rankings_dir)
    return profile


def save_rankings(
    profile: dict, rankings_dir: Path | None = None
) -> bool:
    """Write profile to data/rankings/default.json.

    Updates modified timestamp before writing.
    Returns True on success, False on failure. Never raises.
    """
    if rankings_dir is None:
        rankings_dir = RANKINGS_DIR

    profile["modified"] = datetime.now(timezone.utc).isoformat()
    path = rankings_dir / "default.json"

    try:
        rankings_dir.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(profile, f, indent=2)
        return True
    except IOError:
        return False


def get_position_players(profile: dict, position: str) -> list[dict]:
    """Return players for a position sorted by position_rank."""
    return sorted(
        [p for p in profile.get("players", []) if p["position"] == position],
        key=lambda p: p["position_rank"],
    )


def swap_players(
    profile: dict, position: str, rank_a: int, rank_b: int
) -> dict:
    """Swap two adjacent players by position_rank within a position.

    After swapping, the moved player adopts the tier of their new neighbor
    in the direction of movement (the player they displaced).
    Returns a new profile dict — does not mutate input.
    """
    new_profile = copy.deepcopy(profile)
    pos_players = [
        p for p in new_profile["players"] if p["position"] == position
    ]

    player_a = next((p for p in pos_players if p["position_rank"] == rank_a), None)
    player_b = next((p for p in pos_players if p["position_rank"] == rank_b), None)

    if player_a is None or player_b is None:
        return new_profile

    # Swap ranks
    player_a["position_rank"], player_b["position_rank"] = (
        player_b["position_rank"],
        player_a["position_rank"],
    )

    # Tier auto-reassign: moved player adopts the tier of the neighbor
    # in the direction of movement (i.e., the player they displaced).
    # player_a moved to rank_b's old position, so adopts rank_b's old tier.
    # player_b moved to rank_a's old position, so adopts rank_a's old tier.
    old_tier_a = player_a["tier"]
    old_tier_b = player_b["tier"]
    if old_tier_a != old_tier_b:
        player_a["tier"] = old_tier_b
        player_b["tier"] = old_tier_a

    # Renumber to ensure 1..N with no gaps
    pos_players_sorted = sorted(pos_players, key=lambda p: p["position_rank"])
    for i, p in enumerate(pos_players_sorted, start=1):
        p["position_rank"] = i

    return new_profile


def add_player(
    profile: dict,
    name: str,
    team: str,
    position: str,
    tier: int,
) -> dict:
    """Add a new player at the end of the specified tier.

    Inserts after the last player with matching position and tier.
    Renumbers all subsequent players in the position.
    Returns a new profile dict — does not mutate input.
    """
    new_profile = copy.deepcopy(profile)
    players = new_profile["players"]

    # Find insertion index: after the last player with this position+tier
    insert_idx = None
    for i, p in enumerate(players):
        if p["position"] == position and p["tier"] == tier:
            insert_idx = i

    if insert_idx is not None:
        # The rank of the new player = last player in tier's rank + 1
        new_rank = players[insert_idx]["position_rank"] + 1
        insert_idx += 1  # insert after
    else:
        # No player with that tier — append at end of position list
        last_pos_idx = None
        for i, p in enumerate(players):
            if p["position"] == position:
                last_pos_idx = i
        if last_pos_idx is not None:
            new_rank = players[last_pos_idx]["position_rank"] + 1
            insert_idx = last_pos_idx + 1
        else:
            new_rank = 1
            insert_idx = len(players)

    new_player = {
        "position_rank": new_rank,
        "name": name,
        "team": team,
        "position": position,
        "tier": tier,
        "notes": "",
    }

    players.insert(insert_idx, new_player)

    # Renumber all players in this position sequentially
    rank = 1
    for p in players:
        if p["position"] == position:
            p["position_rank"] = rank
            rank += 1

    return new_profile


def delete_player(
    profile: dict, position: str, position_rank: int
) -> dict:
    """Remove a player and renumber remaining ranks.

    Returns a new profile dict — does not mutate input.
    """
    new_profile = copy.deepcopy(profile)
    new_profile["players"] = [
        p
        for p in new_profile["players"]
        if not (p["position"] == position and p["position_rank"] == position_rank)
    ]

    # Renumber remaining players in this position
    rank = 1
    for p in new_profile["players"]:
        if p["position"] == position:
            p["position_rank"] = rank
            rank += 1

    return new_profile
