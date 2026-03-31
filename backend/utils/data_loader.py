"""CSV data loading and normalization for FantasyPros exports."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from utils.constants import CSV_COLUMN_MAP, POSITIONS, SCHEMA_COLUMNS, YEARS

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Path = Path(__file__).parent.parent.parent / "data" / "players"

_players_cache: pd.DataFrame | None = None


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
        logger.warning("Missing: %s", filename)
        return _empty_dataframe()
    except ValueError:
        # usecols specifies columns not in the CSV
        logger.error("Unexpected columns in %s", filename)
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


def load_all_players(data_dir: Path | None = None) -> pd.DataFrame:
    """Load all positions and years into a single DataFrame.

    Uses module-level cache so CSVs are only read once per process.
    Never raises — missing files produce empty slices.
    """
    global _players_cache
    if _players_cache is not None and data_dir is None:
        return _players_cache

    frames: list[pd.DataFrame] = []
    for position in POSITIONS:
        for year in YEARS:
            frames.append(load_position_year(position, year, data_dir=data_dir))

    if not frames:
        return _empty_dataframe()

    df = pd.concat(frames, ignore_index=True)

    if data_dir is None:
        _players_cache = df

    return df
