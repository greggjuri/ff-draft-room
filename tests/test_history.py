"""Unit tests for history page filter logic."""

import pandas as pd
import pytest

from pages.history import DISPLAY_COLUMNS, filter_players


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "rank":      [1, 2, 1, 2],
        "name":      ["Josh Allen", "Lamar Jackson", "Justin Jefferson", "Tyreek Hill"],
        "team":      ["BUF", "BAL", "MIN", "MIA"],
        "position":  ["QB", "QB", "WR", "WR"],
        "year":      [2024, 2024, 2024, 2024],
        "gp":        [16, 15, 17, 16],
        "ppg":       [25.3, 24.1, 22.5, 21.8],
        "total_pts": [405.1, 361.8, 382.5, 348.8],
    })


def test_filter_by_year(sample_df):
    """Only rows with matching year returned."""
    result = filter_players(sample_df, "QB", 2024)
    assert len(result) == 2
    assert (result["Season"] == 2024).all()


def test_filter_by_position(sample_df):
    """Only rows with matching position returned."""
    result = filter_players(sample_df, "QB", 2024)
    assert len(result) == 2
    assert result["Player"].tolist() == ["Josh Allen", "Lamar Jackson"]


def test_filter_by_search_case_insensitive(sample_df):
    """Case-insensitive search matches partial name."""
    result = filter_players(sample_df, "WR", 2024, search="justin")
    assert len(result) == 1
    assert result.iloc[0]["Player"] == "Justin Jefferson"


def test_filter_empty_search(sample_df):
    """Empty search string returns all rows for position/year."""
    result = filter_players(sample_df, "QB", 2024, search="")
    assert len(result) == 2


def test_filter_no_results(sample_df):
    """Non-matching search returns empty DataFrame."""
    result = filter_players(sample_df, "QB", 2024, search="zzzzz")
    assert result.empty


def test_filter_does_not_mutate(sample_df):
    """Original DataFrame is unchanged after filtering."""
    original = sample_df.copy()
    filter_players(sample_df, "QB", 2024, search="allen")
    pd.testing.assert_frame_equal(sample_df, original)


def test_display_columns(sample_df):
    """Returned DataFrame has correct 7 display columns in order."""
    result = filter_players(sample_df, "QB", 2024)
    expected = list(DISPLAY_COLUMNS.values())
    assert list(result.columns) == expected


def test_position_column_excluded(sample_df):
    """Position column is not present in output."""
    result = filter_players(sample_df, "QB", 2024)
    assert "position" not in result.columns
    assert "Position" not in result.columns
