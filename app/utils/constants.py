"""Shared constants for FF Draft Room."""

POSITIONS: list[str] = ["QB", "RB", "WR", "TE"]
YEARS: list[int] = [2020, 2021, 2022, 2023, 2024, 2025]

# FantasyPros CSV column mapping -> normalized names
CSV_COLUMN_MAP: dict[str, str] = {
    "#": "rank",
    "Player": "name",
    "Team": "team",
    "GP": "gp",
    "AVG": "ppg",
    "TTL": "total_pts",
}

# Normalized schema column order (after adding position + year)
SCHEMA_COLUMNS: list[str] = [
    "rank", "name", "team", "position", "year", "gp", "ppg", "total_pts",
]

# VOR replacement level thresholds (ADR-004)
VOR_REPLACEMENT_LEVELS: dict[str, int] = {
    "QB": 13,
    "RB": 25,
    "WR": 35,
    "TE": 13,
}

# Expected player counts per position (soft validation)
EXPECTED_COUNTS: dict[str, int] = {
    "QB": 20,
    "RB": 40,
    "WR": 50,
    "TE": 20,
}
