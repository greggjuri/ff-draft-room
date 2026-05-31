# 19 — Fantasy Footballers Tiered Rankings Import

## Goal

Re-seed the war room from Fantasy Footballers' tiered 2026 rankings.
Tier comes from the source data (retiring the `_assign_tier()` heuristic).
While we're touching the loader, capture six additional fields per
player — bye week, projected points, risk, upside, ADP, and the
written outlook blurb — that the new CSV exposes and that will inform
upcoming UI features.

Full re-seed; no preservation of existing `notes`/`tag` (none have been
authored).

## Context

- PRP-017 introduced the Fantasy Footballers expert consensus rankings
  as the seed source (`Name, Team, Rank, Andy, Jason, Mike`). Tier was
  assigned by the `_assign_tier()` heuristic in `backend/utils/rankings.py`
  because the source didn't ship tiers.
- Fantasy Footballers has now released the tiered version of the same
  rankings, with substantially more data per player (see CSV Format
  below). This supersedes the previous CSVs entirely.
- The old files (`2026 QB Draft Rankings - Fantasy Footballers Podcast.csv`
  and siblings) are being deleted manually by the operator. The loader
  should not look for them or fall back to them.
- `_assign_tier()` was always temporary scaffolding (per ADR-010). It's
  being deleted in this change.

## CSV Format

**Location**: `data/players/`
**Filename pattern**: `2026_{POSITION}.csv` where `{POSITION}` is one of
`QB`, `RB`, `WR`, `TE`.

**Columns**:
```
Name, Position, Team, Bye Week, Rank, Points, Risk, Upside, ADP, Tier, Outlook, Dynasty, Markers
```

- `Name` — player name, string, may include periods and apostrophes
- `Position` — duplicate of what filename encodes, **ignored** by loader
- `Team` — NFL team abbreviation, string, may be empty (FA, rookies)
- `Bye Week` — integer 5–14, may be empty for unsigned/uncertain players
- `Rank` — consensus rank, integer, 1-indexed, monotonically increasing
- `Points` — Fantasy Footballers' projected season fantasy points, float
- `Risk` — risk score 0–10, float
- `Upside` — upside score 0–10, float
- `ADP` — average draft position, string in `RR.PP` format (e.g. `3.05`),
  may be empty for players without ADP data
- `Tier` — integer, 1-indexed, monotonically grouped (all tier 1s, then
  tier 2s, etc.)
- `Outlook` — full-paragraph analyst blurb, string, may be very long
- `Dynasty` — **ignored** (paywalled; every row reads "Unlock with the
  2026 UDK+. Get the UDK+.")
- `Markers` — **ignored** (HTML UI artifacts from the source page)

**Sample row** (from `2026_QB.csv`):
```
"Josh Allen","QB","BUF","7","1","428.3","2.6","9.7","3.05","1","He is him...","Unlock with...","Mark Drafted ..."
```

**Empty-value cases observed in the QB file**:
- `Bye Week`: empty for Fernando Mendoza, Carson Beck, Deshaun Watson
- `ADP`: empty for Aaron Rodgers, Geno Smith, Carson Beck, Kirk Cousins,
  Deshaun Watson
- `Team`: not observed empty in the QB file, but handled defensively
  the same way as before

## Design

### `data_loader.py` — updated behavior

**Signature unchanged**:
```python
def load_player_data(data_dir: Path | None = None) -> pd.DataFrame:
```

**Behavior**:
- Filename pattern is now `2026_{POSITION}.csv` (no spaces, no suffix
  description).
- Read `Name`, `Team`, `Bye Week`, `Rank`, `Points`, `Risk`, `Upside`,
  `ADP`, `Tier`, `Outlook`. Drop `Position`, `Dynasty`, `Markers`.
- Rename columns to: `name`, `team`, `bye_week`, `rank`, `projected_points`,
  `risk`, `upside`, `adp`, `tier`, `outlook`.
  - `Points` → `projected_points` (disambiguates from "league scoring
    points" and similar future fields).
  - `Bye Week` → `bye_week`.
- Add `position` column from the filename.
- Type coercion:
  - `rank`, `tier`: `int`
  - `bye_week`: nullable int. Empty string → `pd.NA`. Stored as Python
    `int` or `None` after going through `.where()` / `.to_dict()`.
  - `projected_points`, `risk`, `upside`: `float`
  - `adp`: keep as `str` (never coerce to float — `"3.10"` and `"3.5"`
    are not numerically comparable as draft positions). Empty → `""`.
  - `outlook`, `team`, `name`: `str`. NaN → `""`.
- Raise `FileNotFoundError` on missing file, naming the exact path
  expected (unchanged from PRP-017).
- Ignore all other files in `data/players/` (unchanged).

### `rankings.py` — `seed_rankings()` simplification

**New behavior**: read tier directly from the DataFrame. Delete
`_assign_tier()`.

```python
def seed_rankings(df: pd.DataFrame) -> dict:
    """Build the initial default profile from Fantasy Footballers tiered rankings.

    Sorts by rank ascending, takes top N per position per SEED_LIMITS,
    and emits player records with tier sourced directly from the CSV.
    """
```

**Player record shape**:
```python
{
    "position_rank": 1,
    "name": "Josh Allen",
    "team": "BUF",
    "position": "QB",
    "tier": 1,                    # from CSV, not heuristic
    "bye_week": 7,                # NEW — int or None
    "adp": "3.05",                # NEW — str, "" if missing
    "projected_points": 428.3,    # NEW
    "risk": 2.6,                  # NEW
    "upside": 9.7,                # NEW
    "outlook": "He is him. ...",  # NEW
    "notes": "",                  # user-owned, untouched on re-seed
    "tag": "",                    # user-owned, untouched on re-seed
}
```

### Deleted

- `_assign_tier()` in `backend/utils/rankings.py` and all tests for it
- Any constants tied exclusively to the heuristic (audit during execution)

### What stays the same

- `SEED_LIMITS` (QB 30 / RB 50 / WR 50 / TE 30)
- Sorting: by `rank` ascending (the new `Tier` column doesn't affect
  ordering — tiers are grouped by rank already)
- `position_rank` assignment (1-indexed within position, post-sort)
- Profile envelope (`name`, `created`, `modified`, `league`, `players`)
- Loader strictness (missing file → `FileNotFoundError`)
- API surface — zero route changes

## Test Migration

### `tests/test_data_loader.py`
- Update CSV fixtures to the new format (13 columns including the
  ignored ones).
- Update existing assertions to match new column names (`name`, `team`,
  `bye_week`, `rank`, `projected_points`, `risk`, `upside`, `adp`,
  `tier`, `outlook`, `position`).
- Add tests for the new edge cases:
  - Empty `Bye Week` produces `None`/`pd.NA` (not `NaN` string or `0`).
  - Empty `ADP` produces `""` (string), not `NaN`.
  - `Dynasty` and `Markers` columns present in fixture are silently
    dropped.
  - `Position` column present in fixture is overridden by the
    filename-derived position (sanity check — they should always match,
    but the filename is the source of truth).

### `tests/test_rankings.py`
- Update `sample_df` fixture to include all new columns.
- Delete all tests for `_assign_tier()` (function is gone).
- Update seeding tests to assert tier is read directly from the
  DataFrame (not assigned by heuristic).
- Add a test that the player record output includes all six new fields
  with correct types.

### `tests/conftest.py`
- Update shared `sample_df` fixture if used across files.

### Acceptance
- All tests pass, ruff clean.
- Live smoke test: Josh Allen at QB #1 with `tier: 1`, `bye_week: 7`,
  `outlook` is the full Allen blurb.
- Aaron Rodgers row exists with `adp: ""`.
- An FA-style player (if any) shows `team: ""`.

## Deployment

Same recipe as PRP-017:

1. Operator places the four `2026_{POSITION}.csv` files in `data/players/`
   and deletes the old `2026 {POSITION} Draft Rankings - Fantasy Footballers Podcast.csv` files.
2. Local: `pytest tests/ -q` should pass.
3. Local: hit Reset in the war room → verify the new fields populate.
4. Commit, push.
5. EC2: `git pull && ./scripts/deploy.sh`.
6. In the production UI, hit `Reset`. (`seed.json` doesn't exist in S3,
   so Reset falls through to the CSV re-seed path. Same trick worked for
   PRP-017.) Alternative: `curl -X POST https://ff.jurigregg.com/api/rankings/seed`
   with a Cognito bearer token if Reset misbehaves.
7. Reload, verify Josh Allen has a tier and an outlook blurb visible in
   the API response.

## Out of Scope

- **UI changes.** New fields are captured in the data model only. The
  UI continues to display name/team/tier as it does today. Operator has
  ideas for exposing the new fields and will spec UI work separately.
- **Preserving `notes`/`tag` across re-seed.** Full wipe, none have been
  authored.
- **`adp` numerical parsing/sorting.** Stored as string; if/when we want
  to sort by ADP, that's a separate small change.
- **Deleting the old `Draft Rankings` CSVs.** Operator handles manually.
- **Schema migration handling.** Profiles in S3 from PRP-017 don't have
  the new fields. The re-seed overwrites `default.json` wholesale, so
  no migration needed. Named profiles (if any exist) would be stale —
  but no named profiles exist yet.

## Files Touched

- `backend/utils/data_loader.py` — filename pattern + column handling
- `backend/utils/rankings.py` — `seed_rankings()` simplification + delete
  `_assign_tier()`
- `tests/test_data_loader.py` — fixtures + assertions
- `tests/test_rankings.py` — fixtures, delete heuristic tests, add new
  field tests
- `tests/conftest.py` — shared fixture if used

## Constraints Reminder

- `from __future__ import annotations` at top of every backend file
  (already present in affected files)
- File size limit: 500 lines
- Atomic commit after feature complete
- No Streamlit, no DB, no external API calls
- Python 3.9 compatibility on local dev

## Follow-ups (out of scope for this PRP)

- ADR-011 (optional) — document the schema expansion. ADR-010 anticipates
  this; a brief note in DECISIONS.md may be enough rather than a full
  new ADR. Decide after execution.
- UI work to expose new fields (operator-driven).
- Delete legacy `2026 {POSITION} Draft Rankings - Fantasy Footballers Podcast.csv`
  files — operator manual.
