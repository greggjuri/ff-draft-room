"""Shared constants for FF Draft Room."""

POSITIONS: list[str] = ["QB", "RB", "WR", "TE"]

# VOR replacement level thresholds (ADR-004)
VOR_REPLACEMENT_LEVELS: dict[str, int] = {
    "QB": 13,
    "RB": 25,
    "WR": 35,
    "TE": 13,
}
