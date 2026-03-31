"""Unit tests for utils.rankings."""

from __future__ import annotations

import copy
import json
from unittest.mock import patch

import pandas as pd
import pytest

with patch("streamlit.warning"), patch("streamlit.error"), patch(
    "streamlit.cache_data", lambda f: f
):
    from utils.rankings import (
        SEED_LIMITS,
        add_player,
        delete_player,
        get_position_players,
        load_or_seed,
        save_rankings,
        seed_rankings,
        swap_players,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_players(position: str, n: int, year: int = 2025) -> list[dict]:
    """Generate n fake player rows for a position."""
    return [
        {
            "name": f"{position}_Player_{i}",
            "team": f"T{i:02d}",
            "position": position,
            "year": year,
            "rank": i,
            "gp": 16,
            "ppg": round(25.0 - i * 0.3, 1),
            "total_pts": round(400.0 - i * 5.0, 1),
        }
        for i in range(1, n + 1)
    ]


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Multi-position DataFrame large enough for seeding tests."""
    rows: list[dict] = []
    for pos, limit in SEED_LIMITS.items():
        # Provide more rows than SEED_LIMITS to test capping
        rows.extend(_make_players(pos, limit + 10))
    return pd.DataFrame(rows)


@pytest.fixture
def sample_profile() -> dict:
    """Pre-built profile with 6 QB players across 2 tiers for CRUD tests."""
    return {
        "name": "Test",
        "created": "2026-01-01T00:00:00",
        "modified": "2026-01-01T00:00:00",
        "league": {"teams": 10, "scoring": "half_ppr"},
        "players": [
            {"position_rank": 1, "name": "P1", "team": "AA", "position": "QB", "tier": 1, "notes": ""},
            {"position_rank": 2, "name": "P2", "team": "BB", "position": "QB", "tier": 1, "notes": ""},
            {"position_rank": 3, "name": "P3", "team": "CC", "position": "QB", "tier": 1, "notes": ""},
            {"position_rank": 4, "name": "P4", "team": "DD", "position": "QB", "tier": 2, "notes": ""},
            {"position_rank": 5, "name": "P5", "team": "EE", "position": "QB", "tier": 2, "notes": ""},
            {"position_rank": 6, "name": "P6", "team": "FF", "position": "QB", "tier": 2, "notes": ""},
            # RB player to verify cross-position isolation
            {"position_rank": 1, "name": "RB1", "team": "GG", "position": "RB", "tier": 1, "notes": ""},
        ],
    }


# ---------------------------------------------------------------------------
# Seeding tests
# ---------------------------------------------------------------------------


@patch("streamlit.error")
def test_seed_all_positions(mock_err, sample_df):
    profile = seed_rankings(sample_df)
    for pos, expected in SEED_LIMITS.items():
        count = len([p for p in profile["players"] if p["position"] == pos])
        assert count == expected, f"{pos}: expected {expected}, got {count}"


@patch("streamlit.error")
def test_seed_respects_depth_limits(mock_err, sample_df):
    profile = seed_rankings(sample_df)
    for pos, limit in SEED_LIMITS.items():
        count = len([p for p in profile["players"] if p["position"] == pos])
        assert count <= limit


@patch("streamlit.error")
def test_seed_sorted_by_total_pts(mock_err, sample_df):
    profile = seed_rankings(sample_df)
    for pos in SEED_LIMITS:
        players = [p for p in profile["players"] if p["position"] == pos]
        # Players should be in descending total_pts order (rank 1 = highest)
        assert players[0]["position_rank"] == 1


@patch("streamlit.error")
def test_seed_position_rank_sequential(mock_err, sample_df):
    profile = seed_rankings(sample_df)
    for pos in SEED_LIMITS:
        players = sorted(
            [p for p in profile["players"] if p["position"] == pos],
            key=lambda p: p["position_rank"],
        )
        ranks = [p["position_rank"] for p in players]
        assert ranks == list(range(1, len(players) + 1))


@patch("streamlit.error")
def test_seed_has_tier(mock_err, sample_df):
    profile = seed_rankings(sample_df)
    for p in profile["players"]:
        assert isinstance(p["tier"], int)
        assert p["tier"] >= 1


@patch("streamlit.error")
def test_seed_tier_nondecreasing(mock_err, sample_df):
    profile = seed_rankings(sample_df)
    for pos in SEED_LIMITS:
        players = sorted(
            [p for p in profile["players"] if p["position"] == pos],
            key=lambda p: p["position_rank"],
        )
        for i in range(1, len(players)):
            assert players[i]["tier"] >= players[i - 1]["tier"], (
                f"{pos} rank {players[i]['position_rank']}: "
                f"tier {players[i]['tier']} < {players[i-1]['tier']}"
            )


@patch("streamlit.error")
def test_seed_uses_2025_only(mock_err):
    """Seed ignores non-2025 data."""
    rows_2024 = _make_players("QB", 5, year=2024)
    rows_2025 = _make_players("QB", 5, year=2025)
    df = pd.DataFrame(rows_2024 + rows_2025)
    profile = seed_rankings(df)
    qbs = [p for p in profile["players"] if p["position"] == "QB"]
    assert len(qbs) == 5  # only 2025 rows


@patch("streamlit.error")
def test_seed_notes_empty(mock_err, sample_df):
    profile = seed_rankings(sample_df)
    for p in profile["players"]:
        assert p["notes"] == ""


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


@patch("streamlit.warning")
@patch("streamlit.error")
def test_load_or_seed_creates_file(mock_err, mock_warn, sample_df, tmp_path):
    json_path = tmp_path / "default.json"
    assert not json_path.exists()
    profile = load_or_seed(sample_df, rankings_dir=tmp_path)
    assert json_path.exists()
    assert len(profile["players"]) > 0


@patch("streamlit.warning")
@patch("streamlit.error")
def test_load_or_seed_loads_existing(mock_err, mock_warn, tmp_path):
    existing = {
        "name": "Existing",
        "players": [{"position_rank": 1, "name": "X", "team": "Y", "position": "QB", "tier": 1, "notes": ""}],
    }
    (tmp_path / "default.json").write_text(json.dumps(existing))
    df = pd.DataFrame()  # should not matter — existing file used
    profile = load_or_seed(df, rankings_dir=tmp_path)
    assert profile["name"] == "Existing"
    assert len(profile["players"]) == 1


def test_save_writes_valid_json(tmp_path):
    profile = {
        "name": "Test",
        "players": [{"position_rank": 1, "name": "A", "team": "B", "position": "QB", "tier": 1, "notes": ""}],
    }
    assert save_rankings(profile, rankings_dir=tmp_path)
    data = json.loads((tmp_path / "default.json").read_text())
    assert "players" in data
    assert len(data["players"]) == 1


def test_save_updates_modified_timestamp(tmp_path):
    profile = {"name": "Test", "modified": "2020-01-01T00:00:00", "players": []}
    save_rankings(profile, rankings_dir=tmp_path)
    data = json.loads((tmp_path / "default.json").read_text())
    assert data["modified"] != "2020-01-01T00:00:00"


def test_save_returns_false_on_bad_path(tmp_path):
    profile = {"name": "Test", "players": []}
    bad_dir = tmp_path / "no" / "such" / "deeply" / "nested"
    # Make a file where a directory is expected so mkdir fails
    (tmp_path / "no").write_text("block")
    result = save_rankings(profile, rankings_dir=bad_dir)
    assert result is False


# ---------------------------------------------------------------------------
# Reordering tests
# ---------------------------------------------------------------------------


def test_swap_exchanges_ranks(sample_profile):
    result = swap_players(sample_profile, "QB", 2, 3)
    qbs = get_position_players(result, "QB")
    assert qbs[1]["name"] == "P3"
    assert qbs[2]["name"] == "P2"


def test_swap_same_tier_no_tier_change(sample_profile):
    result = swap_players(sample_profile, "QB", 1, 2)
    qbs = get_position_players(result, "QB")
    # Both were tier 1, should stay tier 1
    assert qbs[0]["tier"] == 1
    assert qbs[1]["tier"] == 1


def test_swap_cross_boundary_up(sample_profile):
    """Moving rank 4 (tier 2) up to rank 3 (tier 1) — adopts tier 1."""
    result = swap_players(sample_profile, "QB", 3, 4)
    qbs = get_position_players(result, "QB")
    # P4 moved to rank 3 position, should adopt tier 1
    moved = next(p for p in qbs if p["name"] == "P4")
    assert moved["tier"] == 1
    assert moved["position_rank"] == 3


def test_swap_cross_boundary_down(sample_profile):
    """Moving rank 3 (tier 1) down to rank 4 (tier 2) — adopts tier 2."""
    result = swap_players(sample_profile, "QB", 3, 4)
    qbs = get_position_players(result, "QB")
    moved = next(p for p in qbs if p["name"] == "P3")
    assert moved["tier"] == 2
    assert moved["position_rank"] == 4


def test_swap_ranks_sequential_after(sample_profile):
    result = swap_players(sample_profile, "QB", 2, 3)
    qbs = get_position_players(result, "QB")
    ranks = [p["position_rank"] for p in qbs]
    assert ranks == list(range(1, len(qbs) + 1))


def test_swap_does_not_mutate_input(sample_profile):
    original = copy.deepcopy(sample_profile)
    swap_players(sample_profile, "QB", 2, 3)
    assert sample_profile == original


# ---------------------------------------------------------------------------
# Add player tests
# ---------------------------------------------------------------------------


def test_add_player_appended_to_tier(sample_profile):
    result = add_player(sample_profile, "NewGuy", "ZZ", "QB", 1)
    qbs = get_position_players(result, "QB")
    # Tier 1 had ranks 1-3; new player should be at end of tier 1
    tier1 = [p for p in qbs if p["tier"] == 1]
    assert tier1[-1]["name"] == "NewGuy"


def test_add_player_rank_assigned(sample_profile):
    result = add_player(sample_profile, "NewGuy", "ZZ", "QB", 2)
    qbs = get_position_players(result, "QB")
    new = next(p for p in qbs if p["name"] == "NewGuy")
    assert new["position_rank"] == 7  # was 6 QBs, now 7th


def test_add_player_subsequent_ranks_shifted(sample_profile):
    result = add_player(sample_profile, "NewGuy", "ZZ", "QB", 1)
    qbs = get_position_players(result, "QB")
    # P4 was rank 4, should now be rank 5
    p4 = next(p for p in qbs if p["name"] == "P4")
    assert p4["position_rank"] == 5


def test_add_player_does_not_mutate_input(sample_profile):
    original = copy.deepcopy(sample_profile)
    add_player(sample_profile, "NewGuy", "ZZ", "QB", 1)
    assert sample_profile == original


# ---------------------------------------------------------------------------
# Delete player tests
# ---------------------------------------------------------------------------


def test_delete_removes_player(sample_profile):
    result = delete_player(sample_profile, "QB", 3)
    qbs = get_position_players(result, "QB")
    names = [p["name"] for p in qbs]
    assert "P3" not in names
    assert len(qbs) == 5


def test_delete_renumbers_ranks(sample_profile):
    result = delete_player(sample_profile, "QB", 2)
    qbs = get_position_players(result, "QB")
    ranks = [p["position_rank"] for p in qbs]
    assert ranks == list(range(1, len(qbs) + 1))


def test_delete_does_not_mutate_input(sample_profile):
    original = copy.deepcopy(sample_profile)
    delete_player(sample_profile, "QB", 2)
    assert sample_profile == original


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


def test_get_position_players_sorted(sample_profile):
    qbs = get_position_players(sample_profile, "QB")
    assert len(qbs) == 6
    assert all(p["position"] == "QB" for p in qbs)
    ranks = [p["position_rank"] for p in qbs]
    assert ranks == sorted(ranks)
