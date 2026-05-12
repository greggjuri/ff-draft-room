"""Unit tests for utils.data_loader (Fantasy Footballers format)."""

from __future__ import annotations

import pytest

from utils.data_loader import FILENAME_TEMPLATE, load_player_data

EXPECTED_COLUMNS = ["name", "team", "position", "rank"]


def _write_csv(tmp_path, position: str, rows: list[tuple]) -> None:
    """Write a Fantasy Footballers-format CSV for one position."""
    header = '"Name","Team","Rank","Andy","Jason","Mike"\n'
    body = "\n".join(
        f'"{name}","{team}","{rank}","{rank}","{rank}","{rank}"'
        for (name, team, rank) in rows
    )
    path = tmp_path / FILENAME_TEMPLATE.format(position=position)
    path.write_text(header + body + "\n")


@pytest.fixture
def full_sample(tmp_path):
    """Four position files, 3 rows each."""
    _write_csv(tmp_path, "QB", [("Josh Allen", "BUF", 1),
                                ("Lamar Jackson", "BAL", 2),
                                ("Aaron Rodgers", "", 3)])
    _write_csv(tmp_path, "RB", [("Bijan Robinson", "ATL", 1),
                                ("Jahmyr Gibbs", "DET", 2),
                                ("Saquon Barkley", "PHI", 3)])
    _write_csv(tmp_path, "WR", [("CeeDee Lamb", "DAL", 1),
                                ("Justin Jefferson", "MIN", 2),
                                ("Ja'Marr Chase", "CIN", 3)])
    _write_csv(tmp_path, "TE", [("Sam LaPorta", "DET", 1),
                                ("Trey McBride", "ARI", 2),
                                ("Brock Bowers", "LV", 3)])
    return tmp_path


def test_load_returns_expected_columns(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert list(df.columns) == EXPECTED_COLUMNS


def test_load_all_positions_present(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert sorted(df["position"].unique().tolist()) == ["QB", "RB", "TE", "WR"]
    assert (df["position"].value_counts() == 3).all()


def test_load_drops_host_columns(full_sample):
    df = load_player_data(data_dir=full_sample)
    for col in ("Andy", "Jason", "Mike"):
        assert col not in df.columns


def test_load_rank_is_int(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert df["rank"].dtype == "int64"


def test_load_preserves_fa_empty_team(full_sample):
    df = load_player_data(data_dir=full_sample)
    rodgers = df[df["name"] == "Aaron Rodgers"].iloc[0]
    assert rodgers["team"] == ""
    assert rodgers["position"] == "QB"


def test_load_strips_whitespace(tmp_path):
    _write_csv(tmp_path, "QB", [(" Josh Allen ", " BUF ", 1)])
    _write_csv(tmp_path, "RB", [("X", "Y", 1)])
    _write_csv(tmp_path, "WR", [("X", "Y", 1)])
    _write_csv(tmp_path, "TE", [("X", "Y", 1)])
    df = load_player_data(data_dir=tmp_path)
    qb = df[df["position"] == "QB"].iloc[0]
    assert qb["name"] == "Josh Allen"
    assert qb["team"] == "BUF"


def test_load_missing_file_raises(tmp_path):
    _write_csv(tmp_path, "QB", [("A", "B", 1)])
    _write_csv(tmp_path, "RB", [("A", "B", 1)])
    _write_csv(tmp_path, "WR", [("A", "B", 1)])
    with pytest.raises(FileNotFoundError, match="TE"):
        load_player_data(data_dir=tmp_path)


def test_load_ignores_legacy_pos_year_csvs(full_sample):
    """Legacy {POS}_{YEAR}.csv files in data_dir must not be read."""
    (full_sample / "QB_2025.csv").write_text(
        '"#","Player","Pos","Team","GP","AVG","TTL"\n'
        '"1","Should Not Appear","QB","XXX","16","99.9","999.9"\n'
    )
    df = load_player_data(data_dir=full_sample)
    assert "Should Not Appear" not in df["name"].values


def test_load_concatenates_in_position_order(full_sample):
    df = load_player_data(data_dir=full_sample)
    first_position_block = df["position"].iloc[:3].unique().tolist()
    assert first_position_block == ["QB"]
