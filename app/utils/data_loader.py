"""CSV data loading and normalization for FantasyPros exports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.constants import CSV_COLUMN_MAP, POSITIONS, SCHEMA_COLUMNS, YEARS

DEFAULT_DATA_DIR: Path = Path(__file__).parent.parent.parent / "data" / "players"


def _empty_dataframe() -> pd.DataFrame:
    """Return an empty DataFrame with the correct schema."""
    return pd.DataFrame(columns=SCHEMA_COLUMNS)


def load_position_year(
    position: str, year: int, data_dir: Path | None = None
) -> pd.DataFrame:
    """Load and normalize player data for a given position and year.

    Args:
        position: One of "QB", "RB", "WR", "TE".
        year: Season year (e.g. 2024).
        data_dir: Directory containing CSV files. Defaults to data/players/.

    Returns:
        Normalized DataFrame with columns matching SCHEMA_COLUMNS.
        Returns empty DataFrame on missing file or bad columns.
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    filename = f"{position}_{year}.csv"
    path = data_dir / filename

    try:
        df = pd.read_csv(path, usecols=list(CSV_COLUMN_MAP.keys()))
    except FileNotFoundError:
        st.warning(f"Missing: {filename}")
        return _empty_dataframe()
    except ValueError:
        # usecols specifies columns not in the CSV
        st.error(f"Unexpected columns in {filename}")
        return _empty_dataframe()

    df = df.rename(columns=CSV_COLUMN_MAP)

    # Add position (from parameter, not CSV) and year
    df["position"] = position
    df["year"] = year

    # Coerce numeric types
    for col in ("rank", "gp"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ("ppg", "total_pts"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Strip whitespace from string columns
    df["name"] = df["name"].str.strip()
    df["team"] = df["team"].str.strip()

    # Ensure column order matches schema
    df = df[SCHEMA_COLUMNS]

    return df


@st.cache_data
def load_all_players() -> pd.DataFrame:
    """Load all positions and years into a single DataFrame.

    Decorated with @st.cache_data so CSVs are only read once per session.
    Never raises — missing files produce empty slices.
    """
    frames: list[pd.DataFrame] = []
    for position in POSITIONS:
        for year in YEARS:
            frames.append(load_position_year(position, year))

    if not frames:
        return _empty_dataframe()

    df = pd.concat(frames, ignore_index=True)
    return df
