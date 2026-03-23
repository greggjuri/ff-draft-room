"""Unit tests for app.utils.data_loader."""

from unittest.mock import patch

import pandas as pd
import pytest

# Patch st.warning/st.error before importing data_loader
with patch("streamlit.warning"), patch("streamlit.error"), patch("streamlit.cache_data", lambda f: f):
    from app.utils.data_loader import load_position_year

EXPECTED_COLUMNS = [
    "rank", "name", "team", "position", "year", "gp", "ppg", "total_pts",
]


@pytest.fixture
def sample_qb_csv(tmp_path):
    """Create a 3-row FantasyPros-format CSV with 'Pos' and weekly columns."""
    content = (
        '"#","Player","Pos","Team","GP","1","2","AVG","TTL"\n'
        '"1"," Josh Allen ","QB"," BUF ","16","28.2","34.5","25.3","405.1"\n'
        '"2","Lamar Jackson","QB","BAL","15","22.0","30.1","24.1","361.8"\n'
        '"3","Jalen Hurts","QB","PHI","17","18.5","25.3","21.0","357.0"\n'
    )
    csv_file = tmp_path / "QB_2024.csv"
    csv_file.write_text(content)
    return tmp_path


@patch("streamlit.warning")
def test_load_position_year_valid(mock_warn, sample_qb_csv):
    """Loading a valid CSV returns a DataFrame with correct columns and row count."""
    df = load_position_year("QB", 2024, data_dir=sample_qb_csv)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == EXPECTED_COLUMNS
    assert len(df) == 3
    mock_warn.assert_not_called()


@patch("streamlit.warning")
def test_load_position_year_missing(mock_warn, tmp_path):
    """Missing CSV returns empty DataFrame with correct schema, no exception."""
    df = load_position_year("QB", 1990, data_dir=tmp_path)
    assert df.empty
    assert list(df.columns) == EXPECTED_COLUMNS
    mock_warn.assert_called_once()


@patch("streamlit.warning")
def test_column_rename(mock_warn, sample_qb_csv):
    """FantasyPros column names are correctly mapped to normalized names."""
    df = load_position_year("QB", 2024, data_dir=sample_qb_csv)
    assert list(df.columns) == EXPECTED_COLUMNS
    # Original FantasyPros names should not be present
    assert "#" not in df.columns
    assert "Player" not in df.columns
    assert "TTL" not in df.columns


@patch("streamlit.warning")
def test_year_column_added(mock_warn, sample_qb_csv):
    """Year column is present with the correct integer value."""
    df = load_position_year("QB", 2024, data_dir=sample_qb_csv)
    assert "year" in df.columns
    assert (df["year"] == 2024).all()
    assert df["year"].dtype == int


@patch("streamlit.warning")
def test_whitespace_stripped(mock_warn, sample_qb_csv):
    """Leading/trailing spaces are cleaned from name and team."""
    df = load_position_year("QB", 2024, data_dir=sample_qb_csv)
    # The fixture has " Josh Allen " and " BUF "
    assert df.iloc[0]["name"] == "Josh Allen"
    assert df.iloc[0]["team"] == "BUF"


@patch("streamlit.warning")
def test_dtype_enforcement(mock_warn, sample_qb_csv):
    """Numeric columns have correct dtypes after coercion."""
    df = load_position_year("QB", 2024, data_dir=sample_qb_csv)
    assert df["rank"].dtype == "int64"
    assert df["gp"].dtype == "int64"
    assert df["ppg"].dtype == "float64"
    assert df["total_pts"].dtype == "float64"


@patch("streamlit.warning")
def test_position_from_parameter(mock_warn, sample_qb_csv):
    """Position column comes from the function parameter, not the CSV."""
    df = load_position_year("QB", 2024, data_dir=sample_qb_csv)
    assert (df["position"] == "QB").all()
    # Pos column from CSV should not appear
    assert "Pos" not in df.columns


@patch("streamlit.error")
def test_unexpected_columns_returns_empty(mock_error, tmp_path):
    """CSV missing expected columns returns empty DataFrame."""
    bad_csv = tmp_path / "QB_2024.csv"
    bad_csv.write_text("colA,colB\n1,2\n")
    df = load_position_year("QB", 2024, data_dir=tmp_path)
    assert df.empty
    assert list(df.columns) == EXPECTED_COLUMNS
    mock_error.assert_called_once()
