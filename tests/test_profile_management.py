"""Unit tests for profile management in utils.rankings."""

from __future__ import annotations

import pandas as pd
import pytest

from utils.rankings import (
    delete_profile,
    list_profiles,
    load_profile,
    load_seed_or_csv,
    rename_profile,
    save_profile_as,
    save_seed,
)
from utils.storage import LocalStorage


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
    store = LocalStorage(tmp_path)
    assert list_profiles(storage=store) == []


def test_get_profiles_lists_files(tmp_path):
    store = LocalStorage(tmp_path)
    store.write("Mock_Draft_1.json", {})
    store.write("Final_Board.json", {})
    result = list_profiles(storage=store)
    assert "Final Board" in result
    assert "Mock Draft 1" in result


def test_get_profiles_excludes_reserved(tmp_path):
    store = LocalStorage(tmp_path)
    store.write("default.json", {})
    store.write("seed.json", {})
    store.write("My_Board.json", {})
    result = list_profiles(storage=store)
    assert result == ["My Board"]


# ---------------------------------------------------------------------------
# save_profile_as
# ---------------------------------------------------------------------------


def test_save_as_creates_file(tmp_path):
    store = LocalStorage(tmp_path)
    profile = _sample_profile()
    result = save_profile_as(profile, "Mock Draft 1", storage=store)
    assert result["saved"] is True
    assert result["filename"] == "Mock_Draft_1.json"
    assert store.exists("Mock_Draft_1.json")


def test_save_as_sanitizes_name(tmp_path):
    store = LocalStorage(tmp_path)
    profile = _sample_profile()
    result = save_profile_as(profile, "  My Board  ", storage=store)
    assert result["filename"] == "My_Board.json"
    assert result["name"] == "My Board"


def test_save_as_rejects_empty_name(tmp_path):
    store = LocalStorage(tmp_path)
    with pytest.raises(ValueError, match="required"):
        save_profile_as(_sample_profile(), "", storage=store)


def test_save_as_rejects_path_traversal(tmp_path):
    store = LocalStorage(tmp_path)
    with pytest.raises(ValueError, match="Invalid"):
        save_profile_as(_sample_profile(), "../evil", storage=store)


# ---------------------------------------------------------------------------
# load_profile
# ---------------------------------------------------------------------------


def test_load_profile_loads_file(tmp_path):
    store = LocalStorage(tmp_path)
    profile = _sample_profile("Loaded")
    store.write("My_Board.json", profile)
    loaded = load_profile("My Board", storage=store)
    assert loaded["name"] == "Loaded"


def test_load_profile_copies_to_default(tmp_path):
    store = LocalStorage(tmp_path)
    profile = _sample_profile("Loaded")
    store.write("My_Board.json", profile)
    load_profile("My Board", storage=store)
    default = store.read("default.json")
    assert default["name"] == "Loaded"


def test_load_profile_404_if_missing(tmp_path):
    store = LocalStorage(tmp_path)
    with pytest.raises(FileNotFoundError):
        load_profile("Nonexistent", storage=store)


def test_load_rejects_reserved_names(tmp_path):
    store = LocalStorage(tmp_path)
    with pytest.raises(ValueError, match="reserved"):
        load_profile("default", storage=store)
    with pytest.raises(ValueError, match="reserved"):
        load_profile("seed", storage=store)


# ---------------------------------------------------------------------------
# save_seed / load_seed_or_csv
# ---------------------------------------------------------------------------


def test_set_default_writes_seed_json(tmp_path):
    store = LocalStorage(tmp_path)
    profile = _sample_profile()
    assert save_seed(profile, storage=store)
    assert store.exists("seed.json")
    data = store.read("seed.json")
    assert data["name"] == "Test"


def test_reset_uses_seed_json_if_exists(tmp_path):
    store = LocalStorage(tmp_path)
    seed = _sample_profile("Seed Baseline")
    store.write("seed.json", seed)
    result = load_seed_or_csv(pd.DataFrame(), storage=store)
    assert result["name"] == "Seed Baseline"


def test_reset_falls_back_to_csv(tmp_path):
    store = LocalStorage(tmp_path)
    # No seed.json — should fall back to seed_rankings
    df = _sample_df()
    result = load_seed_or_csv(df, storage=store)
    assert len(result["players"]) > 0
    assert result["name"] == "2026 Draft"


# ---------------------------------------------------------------------------
# rename_profile
# ---------------------------------------------------------------------------


def test_rename_profile_renames_file(tmp_path):
    store = LocalStorage(tmp_path)
    store.write("Old_Name.json", _sample_profile("Old Name"))
    rename_profile("Old Name", "New Name", storage=store)
    assert not store.exists("Old_Name.json")
    assert store.exists("New_Name.json")


def test_rename_profile_updates_name_field(tmp_path):
    store = LocalStorage(tmp_path)
    store.write("Old_Name.json", _sample_profile("Old Name"))
    rename_profile("Old Name", "New Name", storage=store)
    data = store.read("New_Name.json")
    assert data["name"] == "New Name"


def test_rename_profile_rejects_reserved(tmp_path):
    store = LocalStorage(tmp_path)
    store.write("My_Board.json", _sample_profile())
    with pytest.raises(ValueError, match="reserved"):
        rename_profile("My Board", "default", storage=store)


def test_rename_profile_404_if_missing(tmp_path):
    store = LocalStorage(tmp_path)
    with pytest.raises(FileNotFoundError):
        rename_profile("Nonexistent", "New Name", storage=store)


# ---------------------------------------------------------------------------
# delete_profile
# ---------------------------------------------------------------------------


def test_delete_profile_removes_file(tmp_path):
    store = LocalStorage(tmp_path)
    store.write("To_Delete.json", _sample_profile())
    delete_profile("To Delete", storage=store)
    assert not store.exists("To_Delete.json")


def test_delete_profile_rejects_reserved(tmp_path):
    store = LocalStorage(tmp_path)
    with pytest.raises(ValueError, match="reserved"):
        delete_profile("default", storage=store)
    with pytest.raises(ValueError, match="reserved"):
        delete_profile("seed", storage=store)


def test_delete_profile_404_if_missing(tmp_path):
    store = LocalStorage(tmp_path)
    with pytest.raises(FileNotFoundError):
        delete_profile("Nonexistent", storage=store)
