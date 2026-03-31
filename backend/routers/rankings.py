"""Rankings API router — all /api/rankings/* endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.constants import POSITIONS
from utils.data_loader import load_all_players
from utils.rankings import (
    add_player,
    delete_player,
    get_position_players,
    load_or_seed,
    save_rankings,
    seed_rankings,
    swap_players,
)

router = APIRouter(prefix="/rankings", redirect_slashes=False)

# ---------------------------------------------------------------------------
# Module-level state — single-user local app
# ---------------------------------------------------------------------------

_profile: dict | None = None


def get_profile() -> dict:
    """Lazy-load the rankings profile on first access."""
    global _profile
    if _profile is None:
        df = load_all_players()
        _profile = load_or_seed(df)
    return _profile


def _set_profile(profile: dict) -> None:
    """Replace the in-memory profile."""
    global _profile
    _profile = profile


def _validate_position(position: str) -> None:
    """Raise 404 if position is not valid."""
    if position not in POSITIONS:
        raise HTTPException(status_code=404, detail=f"Invalid position: {position}")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ReorderRequest(BaseModel):
    rank_a: int
    rank_b: int


class AddPlayerRequest(BaseModel):
    name: str
    team: str
    tier: int


class NotesRequest(BaseModel):
    notes: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
@router.get("/")
def get_rankings() -> dict:
    """Return full rankings profile."""
    return get_profile()


@router.post("/save")
def save() -> dict:
    """Save current in-memory profile to disk."""
    profile = get_profile()
    success = save_rankings(profile)
    if not success:
        raise HTTPException(status_code=500, detail="Save failed")
    return {"saved": True}


@router.post("/seed")
def seed() -> dict:
    """Re-seed rankings from CSV data (nuclear reset)."""
    df = load_all_players()
    if df.empty:
        raise HTTPException(
            status_code=500, detail="No 2025 data found in data/players/"
        )
    profile = seed_rankings(df)
    save_rankings(profile)
    _set_profile(profile)
    return profile


@router.get("/{position}")
def get_position(position: str) -> list[dict]:
    """Return players for a position sorted by position_rank."""
    _validate_position(position)
    return get_position_players(get_profile(), position)


@router.post("/{position}/reorder")
def reorder(position: str, body: ReorderRequest) -> list[dict]:
    """Swap two players by position_rank."""
    _validate_position(position)
    profile = get_profile()

    # Validate ranks exist
    players = get_position_players(profile, position)
    ranks = {p["position_rank"] for p in players}
    for rank in (body.rank_a, body.rank_b):
        if rank not in ranks:
            raise HTTPException(
                status_code=400,
                detail=f"Rank {rank} not found in {position}",
            )

    updated = swap_players(profile, position, body.rank_a, body.rank_b)
    _set_profile(updated)
    return get_position_players(updated, position)


@router.post("/{position}/add")
def add(position: str, body: AddPlayerRequest) -> list[dict]:
    """Add a new player at the end of the specified tier."""
    _validate_position(position)

    if not body.name.strip() or not body.team.strip():
        raise HTTPException(
            status_code=400, detail="Name and team are required"
        )

    # Duplicate check (case-insensitive)
    profile = get_profile()
    existing = get_position_players(profile, position)
    if any(p["name"].lower() == body.name.strip().lower() for p in existing):
        raise HTTPException(
            status_code=400,
            detail=f"{body.name.strip()} already exists in {position}",
        )

    updated = add_player(
        profile, body.name.strip(), body.team.strip().upper(), position, body.tier
    )
    _set_profile(updated)
    return get_position_players(updated, position)


@router.delete("/{position}/{rank}")
def delete(position: str, rank: int) -> list[dict]:
    """Delete a player at the given rank."""
    _validate_position(position)
    profile = get_profile()

    # Validate rank exists
    players = get_position_players(profile, position)
    if not any(p["position_rank"] == rank for p in players):
        raise HTTPException(
            status_code=404,
            detail=f"Rank {rank} not found in {position}",
        )

    updated = delete_player(profile, position, rank)
    _set_profile(updated)
    return get_position_players(updated, position)


@router.put("/{position}/{rank}/notes")
def update_notes(position: str, rank: int, body: NotesRequest) -> dict:
    """Update notes for a player at the given rank."""
    _validate_position(position)
    profile = get_profile()

    # Find the player
    for p in profile["players"]:
        if p["position"] == position and p["position_rank"] == rank:
            p["notes"] = body.notes
            _set_profile(profile)
            return p

    raise HTTPException(
        status_code=404,
        detail=f"Rank {rank} not found in {position}",
    )
