"""CSV data loading for Fantasy Footballers 2026 tiered expert rankings."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from utils.constants import POSITIONS

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Path = Path(__file__).parent.parent.parent / "data" / "players"

FILENAME_TEMPLATE = "2026_{position}.csv"

READ_COLUMNS = [
    "Name", "Team", "Bye Week", "Rank", "Points",
    "Risk", "Upside", "ADP", "Tier", "Outlook",
]

OUTPUT_COLUMNS = [
    "name", "team", "position", "rank", "tier",
    "bye_week", "projected_points", "risk", "upside", "adp", "outlook",
]

_RENAME = {
    "Name": "name",
    "Team": "team",
    "Bye Week": "bye_week",
    "Rank": "rank",
    "Points": "projected_points",
    "Risk": "risk",
    "Upside": "upside",
    "ADP": "adp",
    "Tier": "tier",
    "Outlook": "outlook",
}


def _load_one(position: str, data_dir: Path) -> pd.DataFrame:
    path = data_dir / FILENAME_TEMPLATE.format(position=position)
    if not path.exists():
        raise FileNotFoundError(f"Missing Fantasy Footballers file: {path.name}")

    # ADP must be read as string to preserve trailing zeros ("3.10" not 3.1).
    df = pd.read_csv(path, usecols=READ_COLUMNS, dtype={"ADP": str})
    df = df.rename(columns=_RENAME)

    df["position"] = position
    df["name"] = df["name"].fillna("").astype(str).str.strip()
    df["team"] = df["team"].fillna("").astype(str).str.strip()
    df["outlook"] = df["outlook"].fillna("").astype(str)

    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(0).astype(int)
    df["tier"] = pd.to_numeric(df["tier"], errors="coerce").fillna(0).astype(int)

    # Nullable int — preserves NaN for empty cells (Mendoza, Beck, Watson)
    df["bye_week"] = pd.to_numeric(df["bye_week"], errors="coerce").astype("Int64")

    df["projected_points"] = pd.to_numeric(df["projected_points"], errors="coerce").astype(float)
    df["risk"] = pd.to_numeric(df["risk"], errors="coerce").astype(float)
    df["upside"] = pd.to_numeric(df["upside"], errors="coerce").astype(float)

    # ADP stays a string. NaN cells become "" (never "nan").
    df["adp"] = df["adp"].fillna("").astype(str).str.strip()

    return df[OUTPUT_COLUMNS]


def load_player_data(data_dir: Path | None = None) -> pd.DataFrame:
    """Load Fantasy Footballers 2026 tiered rankings from data/players/.

    Reads exactly one file per position using FILENAME_TEMPLATE. Returns
    a DataFrame with columns: name, team, position, rank, tier,
    bye_week, projected_points, risk, upside, adp, outlook.

    Raises FileNotFoundError if any of the four expected files is missing.
    The duplicate Position column and the paywalled Dynasty / HTML Markers
    columns are dropped. Empty Team strings (FA) and empty ADP strings
    are preserved. Empty Bye Week cells become pd.NA.
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    frames = [_load_one(pos, data_dir) for pos in POSITIONS]
    return pd.concat(frames, ignore_index=True)
