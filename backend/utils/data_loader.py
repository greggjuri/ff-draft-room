"""CSV data loading for Fantasy Footballers 2026 expert rankings."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from utils.constants import POSITIONS

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Path = Path(__file__).parent.parent.parent / "data" / "players"

FILENAME_TEMPLATE = "2026 {position} Draft Rankings - Fantasy Footballers Podcast.csv"

OUTPUT_COLUMNS = ["name", "team", "position", "rank"]


def _load_one(position: str, data_dir: Path) -> pd.DataFrame:
    path = data_dir / FILENAME_TEMPLATE.format(position=position)
    if not path.exists():
        raise FileNotFoundError(f"Missing Fantasy Footballers file: {path.name}")

    df = pd.read_csv(path, usecols=["Name", "Team", "Rank"])
    df = df.rename(columns={"Name": "name", "Team": "team", "Rank": "rank"})
    df["position"] = position
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(0).astype(int)
    df["team"] = df["team"].fillna("").astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()
    return df[OUTPUT_COLUMNS]


def load_player_data(data_dir: Path | None = None) -> pd.DataFrame:
    """Load Fantasy Footballers 2026 rankings from data/players/.

    Reads exactly one file per position using FILENAME_TEMPLATE.
    Returns a DataFrame with columns: name, team, position, rank.

    Raises FileNotFoundError if any of the four expected files is missing.
    Andy/Jason/Mike columns are ignored. Empty team strings are preserved
    for free agents. Legacy {POS}_{YEAR}.csv files in the directory are
    not read.
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    frames = [_load_one(pos, data_dir) for pos in POSITIONS]
    return pd.concat(frames, ignore_index=True)
