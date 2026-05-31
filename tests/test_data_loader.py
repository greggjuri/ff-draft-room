"""Unit tests for utils.data_loader (Fantasy Footballers tiered format)."""

from __future__ import annotations

import pandas as pd
import pytest

from utils.data_loader import FILENAME_TEMPLATE, load_player_data

EXPECTED_COLUMNS = [
    "name", "team", "position", "rank", "tier",
    "bye_week", "projected_points", "risk", "upside", "adp", "outlook",
]


def _write_csv(tmp_path, position: str, rows: list[dict]) -> None:
    """Write a Fantasy Footballers tiered-format CSV for one position.

    Each row dict may supply any subset of:
      name, team, bye_week, rank, points, risk, upside, adp, tier, outlook
    Missing keys default to sensible values.
    """
    header = (
        '"Name","Position","Team","Bye Week","Rank","Points","Risk",'
        '"Upside","ADP","Tier","Outlook","Dynasty","Markers"\n'
    )
    lines = []
    for r in rows:
        lines.append(
            f'"{r.get("name","X")}",'
            f'"{position}",'                        # Position column (will be dropped)
            f'"{r.get("team","TST")}",'
            f'"{r.get("bye_week","7")}",'
            f'"{r.get("rank",1)}",'
            f'"{r.get("points","100.0")}",'
            f'"{r.get("risk","5.0")}",'
            f'"{r.get("upside","5.0")}",'
            f'"{r.get("adp","10.05")}",'
            f'"{r.get("tier",1)}",'
            f'"{r.get("outlook","Blurb.")}",'
            f'"Unlock with the 2026 UDK+."'         # Dynasty (will be dropped)
            f',"Mark Drafted Mark Keeper"'          # Markers (will be dropped)
        )
    path = tmp_path / FILENAME_TEMPLATE.format(position=position)
    path.write_text(header + "\n".join(lines) + "\n")


@pytest.fixture
def full_sample(tmp_path):
    """Four position files, 3 rows each, covering edge cases in QB."""
    _write_csv(tmp_path, "QB", [
        {"name": "Josh Allen", "team": "BUF", "bye_week": "7",
         "rank": 1, "tier": 1, "points": "428.3", "risk": "2.6",
         "upside": "9.7", "adp": "3.05", "outlook": "Elite."},
        {"name": "Aaron Rodgers", "team": "PIT", "bye_week": "5",
         "rank": 2, "tier": 2, "adp": ""},                       # empty ADP
        {"name": "Carson Beck", "team": "ARI", "bye_week": "",
         "rank": 3, "tier": 2, "adp": ""},                       # empty bye + ADP
    ])
    _write_csv(tmp_path, "RB", [{"name": "Bijan Robinson", "team": "ATL", "rank": 1, "tier": 1},
                                {"name": "Jahmyr Gibbs", "team": "DET", "rank": 2, "tier": 1},
                                {"name": "Saquon Barkley", "team": "PHI", "rank": 3, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "CeeDee Lamb", "team": "DAL", "rank": 1, "tier": 1},
                                {"name": "Justin Jefferson", "team": "MIN", "rank": 2, "tier": 1},
                                {"name": "Ja'Marr Chase", "team": "CIN", "rank": 3, "tier": 1}])
    _write_csv(tmp_path, "TE", [{"name": "Sam LaPorta", "team": "DET", "rank": 1, "tier": 1},
                                {"name": "Trey McBride", "team": "ARI", "rank": 2, "tier": 1},
                                {"name": "Brock Bowers", "team": "LV", "rank": 3, "tier": 1}])
    return tmp_path


def test_load_returns_expected_columns(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert list(df.columns) == EXPECTED_COLUMNS


def test_load_all_positions_present(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert sorted(df["position"].unique().tolist()) == ["QB", "RB", "TE", "WR"]
    assert (df["position"].value_counts() == 3).all()


def test_load_drops_dynasty_and_markers(full_sample):
    df = load_player_data(data_dir=full_sample)
    for col in ("Dynasty", "Markers", "Position"):
        assert col not in df.columns


def test_load_position_from_filename_overrides_csv_column(tmp_path):
    """Even if the in-file Position column disagreed, the filename wins."""
    _write_csv(tmp_path, "QB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "RB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "TE", [{"name": "X", "rank": 1, "tier": 1}])
    df = load_player_data(data_dir=tmp_path)
    assert df[df["position"] == "QB"].iloc[0]["position"] == "QB"


def test_load_rank_and_tier_are_int(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert df["rank"].dtype == "int64"
    assert df["tier"].dtype == "int64"


def test_load_float_fields(full_sample):
    df = load_player_data(data_dir=full_sample)
    for col in ("projected_points", "risk", "upside"):
        assert df[col].dtype == "float64"


def test_load_bye_week_empty_is_na(full_sample):
    df = load_player_data(data_dir=full_sample)
    beck = df[df["name"] == "Carson Beck"].iloc[0]
    assert pd.isna(beck["bye_week"])


def test_load_bye_week_populated_is_int(full_sample):
    df = load_player_data(data_dir=full_sample)
    allen = df[df["name"] == "Josh Allen"].iloc[0]
    assert int(allen["bye_week"]) == 7


def test_load_adp_empty_is_empty_string(full_sample):
    df = load_player_data(data_dir=full_sample)
    rodgers = df[df["name"] == "Aaron Rodgers"].iloc[0]
    assert rodgers["adp"] == ""
    assert isinstance(rodgers["adp"], str)


def test_load_adp_preserves_trailing_zero(tmp_path):
    """'3.10' must stay '3.10', not be coerced to 3.1."""
    _write_csv(tmp_path, "QB", [{"name": "X", "rank": 1, "tier": 1, "adp": "3.10"}])
    _write_csv(tmp_path, "RB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "TE", [{"name": "X", "rank": 1, "tier": 1}])
    df = load_player_data(data_dir=tmp_path)
    assert df[df["position"] == "QB"].iloc[0]["adp"] == "3.10"


def test_load_outlook_passthrough(full_sample):
    df = load_player_data(data_dir=full_sample)
    allen = df[df["name"] == "Josh Allen"].iloc[0]
    assert allen["outlook"] == "Elite."


def test_load_preserves_fa_empty_team(tmp_path):
    _write_csv(tmp_path, "QB", [{"name": "FA Guy", "team": "", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "RB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "TE", [{"name": "X", "rank": 1, "tier": 1}])
    df = load_player_data(data_dir=tmp_path)
    assert df[df["name"] == "FA Guy"].iloc[0]["team"] == ""


def test_load_missing_file_raises(tmp_path):
    _write_csv(tmp_path, "QB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "RB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "X", "rank": 1, "tier": 1}])
    with pytest.raises(FileNotFoundError, match="TE"):
        load_player_data(data_dir=tmp_path)


def test_load_ignores_legacy_pos_year_csvs(full_sample):
    (full_sample / "QB_2025.csv").write_text(
        '"#","Player","Pos","Team","GP","AVG","TTL"\n'
        '"1","Should Not Appear","QB","XXX","16","99.9","999.9"\n'
    )
    df = load_player_data(data_dir=full_sample)
    assert "Should Not Appear" not in df["name"].values


def test_load_ignores_old_naming_pattern_csvs(full_sample):
    """The pre-PRP-019 long-form filename must not be read."""
    long_name = full_sample / "2026 QB Draft Rankings - Fantasy Footballers Podcast.csv"
    long_name.write_text(
        '"Name","Team","Rank","Andy","Jason","Mike"\n'
        '"Old Pattern","XXX","1","1","1","1"\n'
    )
    df = load_player_data(data_dir=full_sample)
    assert "Old Pattern" not in df["name"].values
