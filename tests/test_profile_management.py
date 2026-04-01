"""Unit tests for profile management in utils.rankings."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from utils.rankings import (
    list_profiles,
    load_profile,
    load_seed_or_csv,
    save_profile_as,
    save_seed,
)


def _sample_profile(name: str = "Test") -> dict:
    return {
        "name": name,
        "created": "2026-01-01T00:00:00",
        "modified": "2026-01-01T00:00:00",
        "league": {"teams": 10, "scoring": "half_ppr"},
        "players": [
            {"position_rank": 1, "name": "P1", "team": "AA",
             "position": "QB", "tier": 1, "notes": ""},
        ],
    }


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"name": f"QB_{i}", "team": "T", "position": "QB", "year": 2025,
         "rank": i, "gp": 16, "ppg": 20.0, "total_pts": 300.0 - i}
        for i in range(1, 6)
    ])


# ---------------------------------------------------------------------------
# list_profiles
# ---------------------------------------------------------------------------


def test_get_profiles_empty(tmp_path):
    assert list_profiles(rankings_dir=tmp_path) == []


def test_get_profiles_lists_files(tmp_path):
    (tmp_path / "Mock_Draft_1.json").write_text("{}")
    (tmp_path / "Final_Board.json").write_text("{}")
    result = list_profiles(rankings_dir=tmp_path)
    assert "Final Board" in result
    assert "Mock Draft 1" in result


def test_get_profiles_excludes_reserved(tmp_path):
    (tmp_path / "default.json").write_text("{}")
    (tmp_path / "seed.json").write_text("{}")
    (tmp_path / "My_Board.json").write_text("{}")
    result = list_profiles(rankings_dir=tmp_path)
    assert result == ["My Board"]


# ---------------------------------------------------------------------------
# save_profile_as
# ---------------------------------------------------------------------------


def test_save_as_creates_file(tmp_path):
    profile = _sample_profile()
    result = save_profile_as(profile, "Mock Draft 1", rankings_dir=tmp_path)
    assert result["saved"] is True
    assert result["filename"] == "Mock_Draft_1.json"
    assert (tmp_path / "Mock_Draft_1.json").exists()


def test_save_as_sanitizes_name(tmp_path):
    profile = _sample_profile()
    result = save_profile_as(profile, "  My Board  ", rankings_dir=tmp_path)
    assert result["filename"] == "My_Board.json"
    assert result["name"] == "My Board"


def test_save_as_rejects_empty_name(tmp_path):
    with pytest.raises(ValueError, match="required"):
        save_profile_as(_sample_profile(), "", rankings_dir=tmp_path)


def test_save_as_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError, match="Invalid"):
        save_profile_as(_sample_profile(), "../evil", rankings_dir=tmp_path)


# ---------------------------------------------------------------------------
# load_profile
# ---------------------------------------------------------------------------


def test_load_profile_loads_file(tmp_path):
    profile = _sample_profile("Loaded")
    (tmp_path / "My_Board.json").write_text(json.dumps(profile))
    # Also need default.json to exist for the copy
    (tmp_path / "default.json").write_text("{}")
    loaded = load_profile("My Board", rankings_dir=tmp_path)
    assert loaded["name"] == "Loaded"


def test_load_profile_copies_to_default(tmp_path):
    profile = _sample_profile("Loaded")
    (tmp_path / "My_Board.json").write_text(json.dumps(profile))
    load_profile("My Board", rankings_dir=tmp_path)
    default = json.loads((tmp_path / "default.json").read_text())
    assert default["name"] == "Loaded"


def test_load_profile_404_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_profile("Nonexistent", rankings_dir=tmp_path)


def test_load_rejects_reserved_names(tmp_path):
    with pytest.raises(ValueError, match="reserved"):
        load_profile("default", rankings_dir=tmp_path)
    with pytest.raises(ValueError, match="reserved"):
        load_profile("seed", rankings_dir=tmp_path)


# ---------------------------------------------------------------------------
# save_seed / load_seed_or_csv
# ---------------------------------------------------------------------------


def test_set_default_writes_seed_json(tmp_path):
    profile = _sample_profile()
    assert save_seed(profile, rankings_dir=tmp_path)
    assert (tmp_path / "seed.json").exists()
    data = json.loads((tmp_path / "seed.json").read_text())
    assert data["name"] == "Test"


def test_reset_uses_seed_json_if_exists(tmp_path):
    seed = _sample_profile("Seed Baseline")
    (tmp_path / "seed.json").write_text(json.dumps(seed))
    result = load_seed_or_csv(pd.DataFrame(), rankings_dir=tmp_path)
    assert result["name"] == "Seed Baseline"


def test_reset_falls_back_to_csv(tmp_path):
    # No seed.json — should fall back to seed_rankings
    df = _sample_df()
    result = load_seed_or_csv(df, rankings_dir=tmp_path)
    assert len(result["players"]) > 0
    assert result["name"] == "2026 Draft"
