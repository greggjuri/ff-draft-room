"""Rankings API router — all /api/rankings/* endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from utils.constants import POSITIONS
from utils.data_loader import load_all_players
from utils.rankings import (
    add_player,
    delete_player,
    get_position_players,
    list_profiles,
    load_or_seed,
    load_profile,
    load_seed_or_csv,
    save_profile_as,
    save_rankings,
    save_seed,
    seed_rankings,
    set_player_tier,
    swap_players,
)

router = APIRouter(prefix="/rankings", redirect_slashes=False)

# ---------------------------------------------------------------------------
# Module-level state — single-user app
# ---------------------------------------------------------------------------

_profile: dict | None = None


def _get_storage(request: Request):
    """Get storage backend from app state."""
    return request.app.state.storage


def get_profile(request: Request) -> dict:
    """Lazy-load the rankings profile on first access."""
    global _profile
    if _profile is None:
        df = load_all_players()
        _profile = load_or_seed(df, storage=_get_storage(request))
    return _profile


def _set_profile(profile: dict) -> None:
    """Replace the in-memory profile."""
    global _profile
    _profile = profile


def _validate_position(position: str) -> None:
    """Raise 404 if position is not valid."""
    if position not in POSITIONS:
        raise HTTPException(
            status_code=404, detail=f"Invalid position: {position}"
        )


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


class SetTierRequest(BaseModel):
    tier: int


class SaveAsRequest(BaseModel):
    name: str


class LoadRequest(BaseModel):
    name: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
@router.get("/")
def get_rankings(request: Request) -> dict:
    """Return full rankings profile."""
    return get_profile(request)


@router.post("/save")
def save(request: Request) -> dict:
    """Save current in-memory profile to disk."""
    profile = get_profile(request)
    success = save_rankings(profile, storage=_get_storage(request))
    if not success:
        raise HTTPException(status_code=500, detail="Save failed")
    return {"saved": True}


@router.post("/seed")
def seed(request: Request) -> dict:
    """Re-seed rankings from CSV data (nuclear reset)."""
    df = load_all_players()
    if df.empty:
        raise HTTPException(
            status_code=500, detail="No 2025 data found in data/players/"
        )
    profile = seed_rankings(df)
    save_rankings(profile, storage=_get_storage(request))
    _set_profile(profile)
    return profile


@router.get("/profiles")
def get_profiles(request: Request) -> list[str]:
    """Return list of saved profile names (excludes default and seed)."""
    return list_profiles(storage=_get_storage(request))


@router.post("/save-as")
def save_as(request: Request, body: SaveAsRequest) -> dict:
    """Save current profile under a new name."""
    try:
        result = save_profile_as(
            get_profile(request), body.name,
            storage=_get_storage(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _set_profile(get_profile(request))  # name field was updated in-place
    return result


@router.post("/load")
def load(request: Request, body: LoadRequest) -> dict:
    """Load a named profile as the active profile."""
    try:
        profile = load_profile(
            body.name, storage=_get_storage(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    _set_profile(profile)
    return profile


@router.post("/set-default")
def set_default(request: Request) -> dict:
    """Save current profile as seed.json baseline for future resets."""
    success = save_seed(
        get_profile(request), storage=_get_storage(request)
    )
    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to save baseline"
        )
    return {"saved": True}


@router.post("/reset")
def reset(request: Request) -> dict:
    """Reset rankings to seed.json baseline or CSV data."""
    df = load_all_players()
    profile = load_seed_or_csv(df, storage=_get_storage(request))
    if not profile.get("players"):
        raise HTTPException(
            status_code=500, detail="Reset failed: no data available"
        )
    save_rankings(profile, storage=_get_storage(request))
    _set_profile(profile)
    return profile


@router.get("/{position}")
def get_position(request: Request, position: str) -> list[dict]:
    """Return players for a position sorted by position_rank."""
    _validate_position(position)
    return get_position_players(get_profile(request), position)


@router.post("/{position}/reorder")
def reorder(
    request: Request, position: str, body: ReorderRequest
) -> list[dict]:
    """Swap two players by position_rank."""
    _validate_position(position)
    profile = get_profile(request)

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
def add(
    request: Request, position: str, body: AddPlayerRequest
) -> list[dict]:
    """Add a new player at the end of the specified tier."""
    _validate_position(position)

    if not body.name.strip() or not body.team.strip():
        raise HTTPException(
            status_code=400, detail="Name and team are required"
        )

    # Duplicate check (case-insensitive)
    profile = get_profile(request)
    existing = get_position_players(profile, position)
    if any(p["name"].lower() == body.name.strip().lower() for p in existing):
        raise HTTPException(
            status_code=400,
            detail=f"{body.name.strip()} already exists in {position}",
        )

    updated = add_player(
        profile, body.name.strip(), body.team.strip().upper(),
        position, body.tier,
    )
    _set_profile(updated)
    return get_position_players(updated, position)


@router.delete("/{position}/{rank}")
def delete(request: Request, position: str, rank: int) -> list[dict]:
    """Delete a player at the given rank."""
    _validate_position(position)
    profile = get_profile(request)

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


@router.put("/{position}/{rank}/tier")
def set_tier(
    request: Request, position: str, rank: int, body: SetTierRequest
) -> list[dict]:
    """Reassign a player's tier without changing rank."""
    _validate_position(position)
    profile = get_profile(request)

    # Find the player and validate
    player = None
    for p in profile["players"]:
        if p["position"] == position and p["position_rank"] == rank:
            player = p
            break

    if player is None:
        raise HTTPException(
            status_code=404,
            detail=f"Rank {rank} not found in {position}",
        )

    if abs(player["tier"] - body.tier) != 1:
        raise HTTPException(
            status_code=400,
            detail="Tier must be adjacent (±1) to current tier",
        )

    updated = set_player_tier(profile, position, rank, body.tier)
    _set_profile(updated)
    return get_position_players(updated, position)


@router.put("/{position}/{rank}/notes")
def update_notes(
    request: Request, position: str, rank: int, body: NotesRequest
) -> dict:
    """Update notes for a player at the given rank."""
    _validate_position(position)
    profile = get_profile(request)

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
