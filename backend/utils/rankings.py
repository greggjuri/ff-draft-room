"""Rankings profile save/load/manage operations."""

from __future__ import annotations

import copy
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from utils.constants import POSITIONS
from utils.storage import LocalStorage, StorageBackend

logger = logging.getLogger(__name__)

RANKINGS_DIR: Path = Path(__file__).parent.parent.parent / "data" / "rankings"

SEED_LIMITS: dict[str, int] = {"QB": 30, "RB": 50, "WR": 50, "TE": 30}

TIER_BREAKPOINTS: dict[str, list[tuple[int, int]]] = {
    "QB": [(3, 1), (6, 2), (10, 3), (14, 4), (18, 5), (24, 6), (30, 7)],
    "RB": [(4, 1), (8, 2), (12, 3), (16, 4), (24, 5), (32, 6), (42, 7), (50, 8)],
    "WR": [(4, 1), (8, 2), (16, 3), (24, 4), (36, 5), (50, 6)],
    "TE": [(3, 1), (6, 2), (10, 3), (14, 4), (18, 5), (24, 6), (30, 7)],
}


def _default_storage() -> StorageBackend:
    """Create default LocalStorage for backward compatibility."""
    return LocalStorage(RANKINGS_DIR)


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
        logger.error("No 2025 data. Check data/players/ CSV files.")
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


def load_or_seed(
    df: pd.DataFrame, storage: StorageBackend | None = None
) -> dict:
    """Load existing profile or seed from CSV data.

    If default.json exists and is valid, load it.
    If missing or corrupted, seed from data and save.
    """
    if storage is None:
        storage = _default_storage()

    profile = storage.read("default.json")
    if profile is not None and "players" in profile:
        return profile

    if profile is not None:
        logger.warning("Rankings corrupted — re-seeding.")

    # Seed and save
    profile = seed_rankings(df)
    save_rankings(profile, storage=storage)
    return profile


def save_rankings(
    profile: dict, storage: StorageBackend | None = None
) -> bool:
    """Write profile to default.json.

    Updates modified timestamp before writing.
    Returns True on success, False on failure. Never raises.
    """
    if storage is None:
        storage = _default_storage()

    profile["modified"] = datetime.now(timezone.utc).isoformat()

    try:
        storage.write("default.json", profile)
        return True
    except (IOError, OSError):
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


def set_player_tier(
    profile: dict, position: str, position_rank: int, new_tier: int
) -> dict:
    """Reassign a single player's tier without changing their rank.

    Returns a new profile dict — does not mutate input.
    Raises ValueError if the player is not found.
    """
    new_profile = copy.deepcopy(profile)

    for p in new_profile["players"]:
        if p["position"] == position and p["position_rank"] == position_rank:
            p["tier"] = new_tier
            return new_profile

    raise ValueError(
        f"Player not found: {position} rank {position_rank}"
    )


# ---------------------------------------------------------------------------
# Profile management
# ---------------------------------------------------------------------------

RESERVED_NAMES: set[str] = {"default", "seed"}

_INVALID_CHARS = set("/\\")


def _sanitize_name(name: str) -> str:
    """Sanitize a profile name for use as a filename.

    Strips whitespace, replaces spaces with underscores.
    Raises ValueError on empty, reserved, or path-traversal names.
    """
    name = name.strip()
    if not name:
        raise ValueError("Profile name is required")
    if ".." in name or any(c in name for c in _INVALID_CHARS):
        raise ValueError("Invalid profile name")
    if name.lower() in RESERVED_NAMES:
        raise ValueError(f"'{name}' is a reserved name")
    return name.replace(" ", "_")


def list_profiles(storage: StorageBackend | None = None) -> list[str]:
    """Return sorted list of profile display names.

    Excludes default.json and seed.json.
    """
    if storage is None:
        storage = _default_storage()
    names = []
    for key in sorted(storage.list_keys()):
        stem = key.removesuffix(".json")
        if stem.lower() not in RESERVED_NAMES:
            names.append(stem.replace("_", " "))
    return names


def save_profile_as(
    profile: dict, name: str, storage: StorageBackend | None = None
) -> dict:
    """Save profile under a named file.

    Returns dict with saved status, display name, and filename.
    Raises ValueError on invalid name.
    """
    if storage is None:
        storage = _default_storage()
    sanitized = _sanitize_name(name)
    filename = f"{sanitized}.json"
    profile["name"] = name.strip()
    storage.write(filename, profile)
    return {"saved": True, "name": name.strip(), "filename": filename}


def load_profile(
    name: str, storage: StorageBackend | None = None
) -> dict:
    """Load a named profile from storage.

    Also copies to default.json so it becomes the active profile.
    Raises ValueError on reserved names, FileNotFoundError if missing.
    """
    if storage is None:
        storage = _default_storage()
    if name.strip().lower() in RESERVED_NAMES:
        raise ValueError(f"'{name}' is a reserved name")
    sanitized = name.strip().replace(" ", "_")
    filename = f"{sanitized}.json"
    profile = storage.read(filename)
    if profile is None:
        raise FileNotFoundError(f"Profile not found: {name}")
    # Copy to default.json so it's loaded on next startup
    storage.write("default.json", profile)
    return profile


def rename_profile(
    old_name: str,
    new_name: str,
    storage: StorageBackend | None = None,
) -> dict:
    """Rename a saved profile.

    Reads old file, writes under new sanitized name, deletes old file.
    Raises ValueError on invalid new_name or reserved names.
    Raises FileNotFoundError if old profile does not exist.
    """
    if storage is None:
        storage = _default_storage()

    sanitized_new = _sanitize_name(new_name)
    old_sanitized = old_name.strip().replace(" ", "_")
    old_filename = f"{old_sanitized}.json"

    profile = storage.read(old_filename)
    if profile is None:
        raise FileNotFoundError(f"Profile not found: {old_name}")

    profile["name"] = new_name.strip()
    new_filename = f"{sanitized_new}.json"
    storage.write(new_filename, profile)
    if new_filename != old_filename:
        storage.delete(old_filename)

    return {"renamed": True, "old_name": old_name.strip(), "new_name": new_name.strip()}


def delete_profile(
    name: str,
    storage: StorageBackend | None = None,
) -> dict:
    """Delete a saved profile.

    Raises ValueError if name is reserved.
    Raises FileNotFoundError if profile does not exist.
    """
    if storage is None:
        storage = _default_storage()

    if name.strip().lower() in RESERVED_NAMES:
        raise ValueError(f"'{name}' is a reserved name")

    sanitized = name.strip().replace(" ", "_")
    filename = f"{sanitized}.json"

    if not storage.exists(filename):
        raise FileNotFoundError(f"Profile not found: {name}")

    storage.delete(filename)
    return {"deleted": True, "name": name.strip()}


def save_seed(
    profile: dict, storage: StorageBackend | None = None
) -> bool:
    """Save current profile as seed.json baseline for future resets."""
    if storage is None:
        storage = _default_storage()
    try:
        storage.write("seed.json", profile)
        return True
    except (IOError, OSError):
        return False


def load_seed_or_csv(
    df: pd.DataFrame, storage: StorageBackend | None = None
) -> dict:
    """Load seed.json if it exists, otherwise seed from CSV data."""
    if storage is None:
        storage = _default_storage()
    if storage.exists("seed.json"):
        profile = storage.read("seed.json")
        if profile is not None:
            return profile
        logger.warning("seed.json corrupted — falling back to CSV seed.")
    return seed_rankings(df)
