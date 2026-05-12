# 17 — Fantasy Footballers Rankings Import

## Goal

Replace the FantasyPros historical-stats seed pipeline with the new Fantasy
Footballers 2026 expert rankings. This is a hard cutover: FantasyPros files
are retired, the loader is rewritten, the seed logic is simplified, and
tests are migrated. When Fantasy Footballers releases their tiered files in
~1–2 weeks, we'll do a second full re-seed to pick up the tiers.

## Context

- **Current state**: `backend/utils/data_loader.py` parses FantasyPros
  half-PPR season-leaders CSVs (`{POS}_{YEAR}.csv`, weeks 2020–2025).
  `seed_rankings()` in `backend/utils/rankings.py` filters `year == 2025`,
  sorts by `total_pts desc`, takes top N per position via `SEED_LIMITS`.
- **New data source**: Fantasy Footballers Podcast 2026 expert consensus
  rankings, one file per position, no year dimension, no weekly stats.
- **Tier handling**: Fantasy Footballers' first release is rank-only. Tier
  assignment will continue to use the existing `_assign_tier()` heuristic.
  Their tiered release will follow in roughly a week and a half; we'll
  re-seed from scratch at that point (no merge with in-progress war room
  state).
- **Affected modules**:
  - `backend/utils/data_loader.py` — rewrite
  - `backend/utils/rankings.py` — simplify `seed_rankings()`
  - `tests/test_data_loader.py` — migrate fixtures (8 tests)
  - `tests/test_rankings.py` — migrate seed-related tests (~7 tests)
  - `data/players/` — old CSVs to be retired (kept on disk for now,
    loader will ignore them)

## CSV Format

**Location**: `data/players/`
**Filename pattern**: `2026 {POSITION} Draft Rankings - Fantasy Footballers Podcast.csv`
where `{POSITION}` is one of `QB`, `RB`, `WR`, `TE`.

**Columns**:
```
Name, Team, Rank, Andy, Jason, Mike
```

- `Name` — player name (string, may contain periods/apostrophes, e.g.
  `C.J. Stroud`, `J.J. McCarthy`)
- `Team` — NFL team abbreviation (string, may be empty for free agents,
  e.g. `Aaron Rodgers`)
- `Rank` — consensus rank, integer, 1-indexed, monotonically increasing
- `Andy`, `Jason`, `Mike` — individual host rankings (**ignored** by the
  loader)

**Sample rows** (from `2026 QB Draft Rankings - Fantasy Footballers Podcast.csv`):
```
"Josh Allen","BUF","1","1","1","3"
"Lamar Jackson","BAL","2","4","2","2"
"Aaron Rodgers","","34","36","37","27"
```

## Design

### `data_loader.py` — new behavior

Replace existing `load_player_data()` with a function that loads all four
position files and returns a normalized DataFrame.

**New signature**:
```python
def load_player_data(data_dir: Path | None = None) -> pd.DataFrame:
    """Load Fantasy Footballers 2026 rankings from data/players/.

    Reads one file per position using the filename pattern:
        2026 {POSITION} Draft Rankings - Fantasy Footballers Podcast.csv

    Returns a DataFrame with columns:
        name (str), team (str), position (str), rank (int)

    Missing files raise FileNotFoundError. Empty team strings are kept
    as empty strings (FA players have no team in source data).
    Andy/Jason/Mike columns are dropped — only consensus Rank is used.
    """
```

**Behavior**:
- Iterates `POSITIONS` (`["QB", "RB", "WR", "TE"]`) from `constants.py`
- Builds path: `data_dir / f"2026 {pos} Draft Rankings - Fantasy Footballers Podcast.csv"`
- Reads with `pd.read_csv()` — keeps `Name`, `Team`, `Rank`; drops the rest
- Renames columns to lowercase: `name`, `team`, `rank`
- Adds `position` column with the current position
- Coerces `rank` to `int`
- Fills NaN in `team` with empty string
- Concatenates all four DataFrames and returns
- Raises `FileNotFoundError` with a clear message if any expected file is
  missing (lists which file)
- **Ignores all other files in `data/players/`** — does not glob, does
  not try to pick up legacy `QB_2025.csv` etc.

**Drop**:
- Any week-column parsing
- Any year-extraction-from-filename logic
- Any `total_pts` / `avg_pts` / `games_played` columns
- Any multi-year concatenation

### `rankings.py` — `seed_rankings()` simplification

**New behavior**:
```python
def seed_rankings(df: pd.DataFrame) -> dict:
    """Build the initial default profile from Fantasy Footballers rankings.

    Takes top N per position (per SEED_LIMITS) sorted by rank ascending,
    assigns position_rank (1-indexed), tier (via _assign_tier), and
    empty notes/tag.
    """
```

**Changes from current**:
- Remove `df[df["year"] == 2025]` filter (no year column anymore)
- Remove "no 2025 data" early-return branch
- Sort by `rank` ascending (not `total_pts` descending)
- Everything else stays: `SEED_LIMITS`, `_assign_tier()`, profile shape,
  `position_rank` assignment

**Profile shape unchanged**:
```python
{
    "name": "2026 Draft",
    "created": "...",
    "modified": "...",
    "league": {"teams": 10, "scoring": "half_ppr"},
    "players": [
        {
            "position_rank": 1,
            "name": "Josh Allen",
            "team": "BUF",
            "position": "QB",
            "tier": 1,
            "notes": "",
            "tag": "",
        },
        ...
    ],
}
```

### Tier assignment

No change. Existing `_assign_tier(position, position_rank)` heuristic
continues to apply tier boundaries based on rank within position. When
Fantasy Footballers releases tiered files, we'll revisit.

## Test Migration

### `tests/test_data_loader.py`

- Replace `sample_csv` fixture(s) to produce Fantasy Footballers format
- Update all 8 tests to assert against new column names (`name`, `team`,
  `position`, `rank`)
- Add a test for the FA case (empty `team` string)
- Add a test for missing-file error path
- Add a test confirming legacy `{POS}_{YEAR}.csv` files in the directory
  are ignored

### `tests/test_rankings.py`

- Update `sample_df` fixture to match new DataFrame shape
- Update seeding tests:
  - `test_seed_sorted_by_total_pts` → `test_seed_sorted_by_rank`
  - `test_seed_uses_2025_only` → delete (no longer applicable)
  - Other seed tests update fixture references but logic is unchanged

### `tests/conftest.py`

- If `sample_df` is shared, update there

### Acceptance: all tests pass, ruff clean.

## Deployment

1. Place the four Fantasy Footballers CSVs in `data/players/`
   (already done locally by Juri).
2. Commit and push.
3. On EC2: `git pull && ./scripts/deploy.sh`
4. Trigger re-seed via the existing `Reset` flow in the UI (which falls
   back to CSV re-seed when `seed.json` is absent), OR delete
   `default.json` and `seed.json` from S3 to force a fresh seed on next
   request.
   - **Decision needed at deploy time**: confirm we want to wipe S3
     `default.json` and `seed.json` to force a clean seed from the new
     CSVs. If those files exist, the loader will not re-seed.

## Out of Scope

- UI changes (none)
- Tier import (will happen later when Fantasy Footballers releases
  tiered files — separate init spec)
- Preserving war room state across the re-seed (full wipe is intentional)
- Removing old `{POS}_{YEAR}.csv` files from disk (loader ignores them;
  cleanup can happen separately)
- Changes to `SEED_LIMITS` (QB 30 / RB 50 / WR 50 / TE 30 stays)

## Files Touched

- `backend/utils/data_loader.py` — rewrite
- `backend/utils/rankings.py` — simplify `seed_rankings()`
- `tests/test_data_loader.py` — migrate fixtures and assertions
- `tests/test_rankings.py` — migrate fixture and seed tests
- `tests/conftest.py` — if shared fixtures need updating

## Constraints Reminder

- Python 3.9 compatibility: `from __future__ import annotations` at top
  of every backend file (already present in affected files)
- File size limit: 500 lines
- Atomic commit after feature complete
- No Streamlit, no DB, no external API calls
