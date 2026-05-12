# PRP-017: Fantasy Footballers Rankings Import

**Created**: 2026-05-12
**Initial**: `initials/17-init-fantasy-footballers-import.md`
**Status**: Draft

---

## Overview

### Problem Statement
The current seed pipeline derives 2026 rankings from FantasyPros 2020–2025
half-PPR season-stats CSVs — sorting by `total_pts` of the prior season as a
proxy for expert opinion. Now that the Fantasy Footballers have released
their 2026 expert consensus rankings (one CSV per position, rank-only), we
want to use those directly as the seed source. Past-season stats are no
longer needed for ranking; the data is also the wrong shape (no
`year`/`total_pts`/`gp` columns).

### Proposed Solution
Hard cutover. Replace `data_loader.py` to read the four Fantasy Footballers
files in `data/players/` and emit a normalized `{name, team, position, rank}`
DataFrame. Simplify `seed_rankings()` to sort by `rank` ascending (no year
filter, no `total_pts` sort). Migrate all affected tests. Tier assignment
keeps using the existing `_assign_tier()` heuristic until Fantasy
Footballers ships a tiered file (separate init, ~1.5 weeks out).

No UI changes. No data-model changes to the rankings profile (player rows
keep `position_rank / name / team / position / tier / notes / tag`). Legacy
`{POS}_{YEAR}.csv` files stay on disk but the loader ignores them.

### Success Criteria
- [ ] `load_player_data(data_dir)` reads the four Fantasy Footballers files
  and returns a single DataFrame with exactly `[name, team, position, rank]`
- [ ] FA rows (empty `Team`) are preserved with `team == ""` (not NaN)
- [ ] Andy / Jason / Mike columns are dropped
- [ ] Missing position file raises `FileNotFoundError` naming the file
- [ ] Legacy `QB_2025.csv` etc. in `data/players/` are ignored — never read
- [ ] `seed_rankings(df)` sorts by `rank` ascending, top N per position via
  `SEED_LIMITS` (QB 30 / RB 50 / WR 50 / TE 30), assigns `position_rank`,
  `tier` via `_assign_tier`, empty `notes` and `tag`
- [ ] `pytest tests/ -q` — all tests pass (target: 82 passing after migration)
- [ ] `ruff check backend/ tests/` — clean
- [ ] `uvicorn backend.main:app` starts; `GET /api/rankings` after wiping
  `default.json` returns a freshly seeded profile from the new CSVs
- [ ] `cd frontend && npx vite build` — clean (no FE code touched, sanity build)
- [ ] Deployment-step recipe documented (wipe S3 `default.json` + `seed.json`
  to force re-seed from new CSVs on EC2)

---

## Context

### Related Documentation
- `docs/PLANNING.md` — data flow (CSV → loader → seed → profile JSON)
- `docs/DECISIONS.md` — ADR-002 (JSON profiles), ADR-003 (CSV-only data),
  ADR-008 (StorageBackend / S3)
- `docs/TESTING.md` — testing standards (unit tests + ruff)
- `initials/17-init-fantasy-footballers-import.md` — full spec

### ADR-003 Note
ADR-003 says "FantasyPros half-PPR season leaders CSV exports only." This
PRP changes the *source vendor* of the seed CSV (FantasyPros → Fantasy
Footballers Podcast) but keeps the ADR's underlying principle intact:
verified offline CSV exports, no approximations, no fallbacks. The new
source is rank-based rather than stat-based, which is a *better* fit for a
draft cheatsheet than a `total_pts` proxy. **An ADR update is needed but is
out of scope for this PRP** (call it out for Claude.ai to write next as
ADR-010 — Fantasy Footballers as Seed Source).

### Dependencies
- **Required**: none — pure backend refactor
- **Optional**: none

### Files to Modify
```
backend/utils/data_loader.py        # REWRITE — new function + behavior
backend/utils/rankings.py           # MODIFY — simplify seed_rankings()
backend/utils/constants.py          # MODIFY — delete YEARS, CSV_COLUMN_MAP,
                                    #          SCHEMA_COLUMNS, EXPECTED_COUNTS
backend/routers/rankings.py         # MODIFY — rename load_all_players →
                                    #          load_player_data (3 sites)
                                    #          + update stale error msg
tests/test_data_loader.py           # REWRITE — new fixtures + assertions
tests/test_rankings.py              # MODIFY — fixture shape + seed tests
tests/test_profile_management.py    # MODIFY — _sample_df helper shape
```

> **Files Touched correction vs. init**: the init listed routers/rankings.py,
> constants.py, and test_profile_management.py only implicitly. They are
> included here because:
> - `routers/rankings.py` has 3 callsites of the renamed loader and a stale
>   error string ("No 2025 data found in data/players/")
> - `constants.py` carries 4 symbols that become dead code after the loader
>   rewrite — delete in the same logical change rather than rotting on the
>   import path (resolved open question)
> - `test_profile_management.py` has a `_sample_df()` helper with the old
>   `total_pts`/`year`/`gp`/`ppg` schema that drives `load_seed_or_csv` tests

### Files NOT Modified (intentional)
```
data/players/QB_2020.csv … *_2025   # left on disk, loader ignores them
frontend/**                         # no UI changes
backend/main.py                     # no startup wiring changes
```

---

## Technical Specification

### New CSV Format

**Filename pattern** (under `data/players/`):
```
2026 {POSITION} Draft Rankings - Fantasy Footballers Podcast.csv
```
where `{POSITION}` ∈ `{QB, RB, WR, TE}`.

**Columns** (header row):
```
Name, Team, Rank, Andy, Jason, Mike
```

**Sample**:
```csv
"Name","Team","Rank","Andy","Jason","Mike"
"Josh Allen","BUF","1","1","1","3"
"Lamar Jackson","BAL","2","4","2","2"
"Aaron Rodgers","","34","36","37","27"
```

- `Name` — string, may contain periods / apostrophes (`C.J. Stroud`,
  `J.J. McCarthy`)
- `Team` — NFL abbrev or empty string for FA
- `Rank` — int, 1-indexed, monotonically increasing
- `Andy / Jason / Mike` — per-host ranks, **dropped by loader**

### `backend/utils/data_loader.py` — Rewrite

Drop everything year-related. Drop `CSV_COLUMN_MAP`, `SCHEMA_COLUMNS`,
`YEARS` imports. Drop the module-level `_players_cache` (the call cost is
trivial — 4 small files — and caching across `data_dir` overrides has been
a latent foot-gun).

```python
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
```

**Removed**:
- `load_position_year(position, year, ...)` — function entirely
- `load_all_players()` — replaced by `load_player_data()`
- `_empty_dataframe()` helper
- `_players_cache` module-level cache
- All references to `gp`, `ppg`, `total_pts`, `year`, `Pos` column, weekly
  columns

**Error semantics change**: previously, missing files produced an empty
DataFrame with a `logger.warning`. New behavior is strict — missing file =
`FileNotFoundError`. This is intentional: we expect all four files to be
present, and silent missing-file fallback masked real data problems.

> **Router upstream behavior**: the existing `seed` endpoint already
> wraps a `df.empty` check with a 500 response. We replace that branch
> with a `try/except FileNotFoundError` returning a 500 with the missing
> filename. See router changes below.

### `backend/utils/rankings.py` — `seed_rankings()` Simplification

```python
def seed_rankings(df: pd.DataFrame) -> dict:
    """Build the initial default profile from Fantasy Footballers rankings.

    Takes top N per position (per SEED_LIMITS) sorted by rank ascending,
    assigns position_rank (1-indexed), tier (via _assign_tier), and empty
    notes/tag.
    """
    players: list[dict] = []
    for position in POSITIONS:
        pos_df = df[df["position"] == position].copy()
        pos_df = pos_df.sort_values("rank", ascending=True)
        limit = SEED_LIMITS.get(position, 20)
        pos_df = pos_df.head(limit)

        for i, (_, row) in enumerate(pos_df.iterrows(), start=1):
            players.append({
                "position_rank": i,
                "name": row["name"],
                "team": row["team"],
                "position": position,
                "tier": _assign_tier(position, i),
                "notes": "",
                "tag": "",
            })

    now = datetime.now(timezone.utc).isoformat()
    return {
        "name": "2026 Draft",
        "created": now,
        "modified": now,
        "league": {"teams": 10, "scoring": "half_ppr"},
        "players": players,
    }
```

**Removed from current**:
- `df_2025 = df[df["year"] == 2025]` filter
- The early-return "no 2025 data" branch (loader now raises on missing files;
  empty DF here yields an empty `players: []` — same end shape, no log spam)
- `sort_values("total_pts", ascending=False)` → `sort_values("rank", ascending=True)`

Everything else is unchanged: `SEED_LIMITS`, `_assign_tier()`, `position_rank`
numbering, profile shape, ISO timestamps.

### `backend/routers/rankings.py` — Three Edits

1. **Import rename** (line 9):
```python
from utils.data_loader import load_player_data  # was: load_all_players
```

2. **All 3 callsites** (lines 47, 132, 194):
```python
df = load_player_data()   # was: load_all_players()
```

3. **Error message update** in `seed` endpoint (lines 130–140). Replace
the `df.empty` check with FileNotFoundError handling, since the loader
is now strict:
```python
@router.post("/seed")
def seed(request: Request) -> dict:
    """Re-seed rankings from CSV data (nuclear reset)."""
    try:
        df = load_player_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    profile = seed_rankings(df)
    save_rankings(profile, storage=_get_storage(request))
    _set_profile(profile)
    return profile
```

Apply the same `try/except FileNotFoundError` pattern to the `reset`
endpoint (line ~191) and to `get_profile`'s lazy-load path (line ~47).
For `get_profile`, the FileNotFoundError must bubble up as a 500 — wrap
with HTTPException in the route layer (or let it 500 naturally; document
which). Recommend explicit handling in `get_profile` to keep error UX
consistent.

### Data Model — Unchanged
Player rows in the rankings profile keep the existing shape:
```json
{
  "position_rank": 1,
  "name": "Josh Allen",
  "team": "BUF",
  "position": "QB",
  "tier": 1,
  "notes": "",
  "tag": ""
}
```

### Tier Assignment — Unchanged
`_assign_tier(position, position_rank)` continues to apply existing
`TIER_BREAKPOINTS` heuristic. Fantasy Footballers' tiered release (~1.5
weeks out) will warrant a separate init.

---

## Implementation Steps

### Step 1 — Rewrite `data_loader.py`
**Files**: `backend/utils/data_loader.py`

Replace entire file contents per the spec above. Delete
`load_position_year`, `load_all_players`, `_empty_dataframe`,
`_players_cache`. Add `load_player_data`, `_load_one`, `FILENAME_TEMPLATE`,
`OUTPUT_COLUMNS`. Keep `DEFAULT_DATA_DIR` and `logger`.

**Validation**:
```bash
ruff check backend/utils/data_loader.py
python -c "import sys; sys.path.insert(0, 'backend'); \
  from utils.data_loader import load_player_data; \
  df = load_player_data(); \
  print(df.shape); print(df.head()); print(df.dtypes); \
  print('positions:', df['position'].unique().tolist())"
```
Expected: ~`(N, 4)` rows where N ≈ 200+, dtypes `{name: object, team: object,
position: object, rank: int64}`, positions list = `['QB', 'RB', 'WR', 'TE']`.

- [ ] File ≤ 500 lines (actual: ~50 lines)
- [ ] No imports of removed constants (`CSV_COLUMN_MAP`, `SCHEMA_COLUMNS`,
  `YEARS`)
- [ ] FA player (e.g. Aaron Rodgers) appears with `team == ""`

---

### Step 2 — Simplify `seed_rankings()` in `rankings.py`
**Files**: `backend/utils/rankings.py`

Edit only the `seed_rankings` function (lines 46–88). Other helpers
(`_assign_tier`, `load_or_seed`, `save_rankings`, etc.) untouched. Update
the docstring to reference Fantasy Footballers (drop "from 2025 data").

**Validation**:
```bash
ruff check backend/utils/rankings.py
```
- [ ] Function body matches spec (no `df["year"]`, sorts by `rank` asc)
- [ ] No reference to `total_pts` anywhere in the file
- [ ] All other functions in `rankings.py` are byte-identical (use git diff)

---

### Step 3 — Update `routers/rankings.py`
**Files**: `backend/routers/rankings.py`

1. Rename import: `load_all_players` → `load_player_data`
2. Update 3 callsites (`get_profile`, `seed`, `reset`)
3. Wrap each callsite in `try/except FileNotFoundError` → `HTTPException(500, detail=str(e))`
4. Replace the stale `"No 2025 data found in data/players/"` 500 message

**Validation**:
```bash
ruff check backend/routers/rankings.py
grep -n "load_all_players\|total_pts\|year == 2025\|No 2025 data" \
  backend/ tests/ -r
# expected: zero matches
```
- [ ] No remaining `load_all_players` references in repo
- [ ] No remaining `total_pts` / `year` references in backend code

---

### Step 3.5 — Prune dead symbols from `constants.py`
**Files**: `backend/utils/constants.py`

After Steps 1–3, four symbols become unreferenced:
- `YEARS`
- `CSV_COLUMN_MAP`
- `SCHEMA_COLUMNS`
- `EXPECTED_COUNTS`

Delete them. Keep `POSITIONS`, `VOR_REPLACEMENT_LEVELS`, and any other
still-referenced symbols. Resulting file should be ~12 lines.

**Validation**:
```bash
ruff check backend/utils/constants.py
grep -rn "YEARS\|CSV_COLUMN_MAP\|SCHEMA_COLUMNS\|EXPECTED_COUNTS" \
  backend/ tests/
# expected: zero matches (the symbols themselves should not appear anywhere)
```
- [ ] All four symbols gone from `constants.py`
- [ ] grep across `backend/` and `tests/` returns zero matches
- [ ] `POSITIONS` and `VOR_REPLACEMENT_LEVELS` still present and unchanged

---

### Step 4 — Migrate `tests/test_data_loader.py`
**Files**: `tests/test_data_loader.py`

Full rewrite. New shape:

```python
"""Unit tests for utils.data_loader (Fantasy Footballers format)."""

from __future__ import annotations

import pandas as pd
import pytest

from utils.data_loader import FILENAME_TEMPLATE, load_player_data

EXPECTED_COLUMNS = ["name", "team", "position", "rank"]


def _write_csv(tmp_path, position: str, rows: list[tuple]) -> None:
    """Write a Fantasy Footballers-format CSV for one position."""
    header = '"Name","Team","Rank","Andy","Jason","Mike"\n'
    body = "\n".join(
        f'"{name}","{team}","{rank}","{rank}","{rank}","{rank}"'
        for (name, team, rank) in rows
    )
    path = tmp_path / FILENAME_TEMPLATE.format(position=position)
    path.write_text(header + body + "\n")


@pytest.fixture
def full_sample(tmp_path):
    """Four position files, 3 rows each."""
    _write_csv(tmp_path, "QB", [("Josh Allen", "BUF", 1),
                                ("Lamar Jackson", "BAL", 2),
                                ("Aaron Rodgers", "", 3)])
    _write_csv(tmp_path, "RB", [("Bijan Robinson", "ATL", 1),
                                ("Jahmyr Gibbs", "DET", 2),
                                ("Saquon Barkley", "PHI", 3)])
    _write_csv(tmp_path, "WR", [("CeeDee Lamb", "DAL", 1),
                                ("Justin Jefferson", "MIN", 2),
                                ("Ja'Marr Chase", "CIN", 3)])
    _write_csv(tmp_path, "TE", [("Sam LaPorta", "DET", 1),
                                ("Trey McBride", "ARI", 2),
                                ("Brock Bowers", "LV", 3)])
    return tmp_path


def test_load_returns_expected_columns(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert list(df.columns) == EXPECTED_COLUMNS


def test_load_all_positions_present(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert sorted(df["position"].unique().tolist()) == ["QB", "RB", "TE", "WR"]
    assert (df["position"].value_counts() == 3).all()


def test_load_drops_host_columns(full_sample):
    df = load_player_data(data_dir=full_sample)
    for col in ("Andy", "Jason", "Mike"):
        assert col not in df.columns


def test_load_rank_is_int(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert df["rank"].dtype == "int64"


def test_load_preserves_fa_empty_team(full_sample):
    df = load_player_data(data_dir=full_sample)
    rodgers = df[df["name"] == "Aaron Rodgers"].iloc[0]
    assert rodgers["team"] == ""
    assert rodgers["position"] == "QB"


def test_load_strips_whitespace(tmp_path):
    _write_csv(tmp_path, "QB", [(" Josh Allen ", " BUF ", 1)])
    # Other three positions still required
    _write_csv(tmp_path, "RB", [("X", "Y", 1)])
    _write_csv(tmp_path, "WR", [("X", "Y", 1)])
    _write_csv(tmp_path, "TE", [("X", "Y", 1)])
    df = load_player_data(data_dir=tmp_path)
    qb = df[df["position"] == "QB"].iloc[0]
    assert qb["name"] == "Josh Allen"
    assert qb["team"] == "BUF"


def test_load_missing_file_raises(tmp_path):
    # Only 3 of 4 files present
    _write_csv(tmp_path, "QB", [("A", "B", 1)])
    _write_csv(tmp_path, "RB", [("A", "B", 1)])
    _write_csv(tmp_path, "WR", [("A", "B", 1)])
    with pytest.raises(FileNotFoundError, match="TE"):
        load_player_data(data_dir=tmp_path)


def test_load_ignores_legacy_pos_year_csvs(full_sample):
    """Legacy {POS}_{YEAR}.csv files in data_dir must not be read."""
    # Drop a malformed legacy file that would explode if read
    (full_sample / "QB_2025.csv").write_text(
        '"#","Player","Pos","Team","GP","AVG","TTL"\n'
        '"1","Should Not Appear","QB","XXX","16","99.9","999.9"\n'
    )
    df = load_player_data(data_dir=full_sample)
    assert "Should Not Appear" not in df["name"].values


def test_load_concatenates_in_position_order(full_sample):
    df = load_player_data(data_dir=full_sample)
    # POSITIONS = ["QB", "RB", "WR", "TE"]; concat preserves that order
    first_position_block = df["position"].iloc[:3].unique().tolist()
    assert first_position_block == ["QB"]
```

**Validation**:
```bash
pytest tests/test_data_loader.py -v
ruff check tests/test_data_loader.py
```
- [ ] 9 tests pass
- [ ] No remaining reference to `load_position_year`, `total_pts`, `year`, `gp`

---

### Step 5 — Migrate `tests/test_rankings.py`
**Files**: `tests/test_rankings.py`

Update `_make_players` and `sample_df` only; the persistence / swap / add /
delete / tier / tag tests use `sample_profile` (already in the new shape)
and need **no changes**.

```python
def _make_players(position: str, n: int) -> list[dict]:
    """Generate n fake player rows for a position (new schema)."""
    return [
        {
            "name": f"{position}_Player_{i}",
            "team": f"T{i:02d}",
            "position": position,
            "rank": i,  # already 1-indexed and monotonically increasing
        }
        for i in range(1, n + 1)
    ]


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Multi-position DataFrame large enough for seeding tests."""
    rows: list[dict] = []
    for pos, limit in SEED_LIMITS.items():
        rows.extend(_make_players(pos, limit + 10))  # extras to test capping
    return pd.DataFrame(rows)
```

Rename `test_seed_sorted_by_total_pts` → `test_seed_sorted_by_rank` and
adjust the assertion to match the new sort order. The current test
already only asserts `players[0]["position_rank"] == 1`, which is
correct under rank-ascending too, but rename to keep intent clear:

```python
def test_seed_sorted_by_rank(sample_df):
    """First player per position has the lowest source rank (= position_rank 1)."""
    profile = seed_rankings(sample_df)
    for pos in SEED_LIMITS:
        players = [p for p in profile["players"] if p["position"] == pos]
        assert players[0]["position_rank"] == 1
        # And the original source rank for that player is 1
        # (i.e., we picked the top of the sorted list)
        assert players[0]["name"] == f"{pos}_Player_1"
```

**Delete `test_seed_uses_2025_only`** entirely — no `year` dimension anymore.

Leave these tests intact (they use the new `sample_df` shape transparently):
- `test_seed_all_positions`
- `test_seed_respects_depth_limits`
- `test_seed_position_rank_sequential`
- `test_seed_has_tier`
- `test_seed_tier_nondecreasing`
- `test_seed_notes_empty`
- `test_load_or_seed_*` (use `sample_df`)
- All swap / add / delete / tier / tag tests (use `sample_profile`, not `sample_df`)

**Validation**:
```bash
pytest tests/test_rankings.py -v
```
- [ ] All tests in this file pass
- [ ] `test_seed_uses_2025_only` no longer exists
- [ ] `test_seed_sorted_by_rank` exists

---

### Step 6 — Update `tests/test_profile_management.py`
**Files**: `tests/test_profile_management.py`

Replace `_sample_df()` helper at lines 33–38:

```python
def _sample_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"name": f"QB_{i}", "team": "T", "position": "QB", "rank": i}
        for i in range(1, 6)
    ])
```

No other changes needed; `test_reset_falls_back_to_csv` still passes
because `seed_rankings(df)` now sorts by `rank` and the helper rows are
already in ascending rank order.

**Validation**:
```bash
pytest tests/test_profile_management.py -v
```
- [ ] All 21 tests pass

---

### Step 7 — Full Test Suite + Lint
**Validation**:
```bash
pytest tests/ -q
ruff check backend/ tests/
```
- [ ] All tests pass (target: 82 — same as before. `test_data_loader.py`
  goes 8 → 9 (+1); `test_rankings.py` renames one test and deletes
  `test_seed_uses_2025_only` (−1); `test_profile_management.py` unchanged
  in count. Net delta: 0.)
- [ ] ruff clean

> If the count drops below 82, investigate before proceeding.

---

### Step 8 — Live Smoke Test (Local Dev)
**Commands**:
```bash
# Wipe any cached local seed/default so the new loader runs end-to-end
rm -f data/rankings/default.json data/rankings/seed.json

source .venv/bin/activate
uvicorn backend.main:app --reload &
sleep 2

curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/rankings | python -m json.tool | head -50
curl -s http://localhost:8000/api/rankings/QB | python -m json.tool | head -20
```
- [ ] `/health` returns 200
- [ ] `/api/rankings` returns a profile named `"2026 Draft"` with players
  drawn from the Fantasy Footballers CSVs (e.g. Josh Allen is QB #1)
- [ ] `/api/rankings/QB` shows 30 players with `position_rank` 1..30
- [ ] FA player (Aaron Rodgers) appears with `team == ""`

> **Do not commit `data/rankings/default.json`.** It's a regenerable
> artifact — any `POST /seed` or fresh `GET /api/rankings` will rebuild
> it from the CSVs. Committing it creates a second source of truth that
> drifts from the source data.
>
> `default.json` is currently tracked in git (pre-existing issue). **Do
> not fix that in this PRP.** Flag it for a follow-up: a separate small
> change should `git rm --cached data/rankings/default.json` and add
> `data/rankings/default.json` (and `seed.json`) to `.gitignore`. For
> this PRP: leave the currently-tracked file alone on disk and simply
> don't include it in the `git add` set below.

---

### Step 9 — Commit + Push
```bash
git add backend/utils/data_loader.py backend/utils/rankings.py \
        backend/utils/constants.py \
        backend/routers/rankings.py \
        tests/test_data_loader.py tests/test_rankings.py \
        tests/test_profile_management.py \
        "data/players/2026 QB Draft Rankings - Fantasy Footballers Podcast.csv" \
        "data/players/2026 RB Draft Rankings - Fantasy Footballers Podcast.csv" \
        "data/players/2026 TE Draft Rankings - Fantasy Footballers Podcast.csv" \
        "data/players/2026 WR Draft Rankings - Fantasy Footballers Podcast.csv"
git commit -m "feat: replace FantasyPros seed with Fantasy Footballers 2026 rankings"
git push origin main
```

> **Explicitly excluded**: `data/rankings/default.json`. See Step 8 note.

---

### Step 10 — Production Deploy
**On EC2**:
```bash
git pull origin main
./scripts/deploy.sh
```

**Force fresh seed from new CSVs**:
```bash
curl -X POST https://ff.jurigregg.com/api/rankings/seed \
     -H "Authorization: Bearer <cognito-token>"
```
This rebuilds `default.json` from the new CSVs unconditionally — no S3
console access needed.

**Caveat re: `seed.json`**: `POST /seed` does not touch `seed.json`. If
you have previously clicked "Set as Default" in the UI, the old
FantasyPros-derived baseline remains and will be restored on the next
Reset. To make the new CSVs the Reset baseline too, either:
- hit "Set as Default" again after `POST /seed` completes, or
- delete `s3://ff-draft-room-data/rankings/seed.json` via AWS console.

- [ ] App still loads at `https://ff.jurigregg.com`
- [ ] After `POST /seed`, page reload shows the Fantasy Footballers
  consensus (Josh Allen #1 QB, etc.)
- [ ] `seed.json` baseline updated (or deleted) per caveat above

---

## Testing Requirements

### Unit Tests

`tests/test_data_loader.py` — 9 tests:
- `test_load_returns_expected_columns` — column shape matches
  `[name, team, position, rank]`
- `test_load_all_positions_present` — all 4 positions concatenated
- `test_load_drops_host_columns` — Andy/Jason/Mike absent
- `test_load_rank_is_int` — `rank` coerced to int64
- `test_load_preserves_fa_empty_team` — empty `Team` cell → `""` (not NaN)
- `test_load_strips_whitespace` — leading/trailing spaces stripped from
  name and team
- `test_load_missing_file_raises` — `FileNotFoundError` names the missing
  position file
- `test_load_ignores_legacy_pos_year_csvs` — `QB_2025.csv` etc. not read
  even when present in the directory
- `test_load_concatenates_in_position_order` — preserves `POSITIONS` order

`tests/test_rankings.py` — modified seeding tests:
- `test_seed_sorted_by_rank` (replaces `test_seed_sorted_by_total_pts`)
- Remaining 7 seeding tests keep working under new `sample_df` shape
- `test_seed_uses_2025_only` — **deleted**

`tests/test_profile_management.py` — `_sample_df()` helper updated; no
test deletions.

### Manual API Tests
- After wiping `data/rankings/*.json`, hit `GET /api/rankings` and verify
  Josh Allen is QB rank 1 (sanity: matches `2026 QB Draft Rankings - …csv`
  row 1)
- Hit `POST /api/rankings/seed` directly — confirm reseed works

### No Frontend Tests Needed
Zero frontend code touched. `cd frontend && npx vite build` is a sanity
build, not a behavior check.

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | All tests pass, 82 total (net delta 0) | ☐ |
| 2 | `ruff check backend/ tests/` | Clean | ☐ |
| 3 | `rm data/rankings/default.json && rm -f data/rankings/seed.json` | Files gone | ☐ |
| 4 | `uvicorn backend.main:app --reload` | Starts, no errors | ☐ |
| 5 | `curl http://localhost:8000/health` | 200 OK | ☐ |
| 6 | `curl http://localhost:8000/api/rankings/QB` | 30 players, Josh Allen rank 1 | ☐ |
| 7 | `curl http://localhost:8000/api/rankings/RB` | 50 players | ☐ |
| 8 | Search for "Aaron Rodgers" in response | `team == ""` | ☐ |
| 9 | `curl -X POST http://localhost:8000/api/rankings/seed` | Returns freshly seeded profile | ☐ |
| 10 | `cd frontend && npx vite build` | Build clean | ☐ |
| 11 | `cd frontend && npm run dev`, open browser | War Room renders, 4 columns of Fantasy Footballers players | ☐ |
| 12 | Tier dividers / colors / logos | All work unchanged | ☐ |
| 13 | Deploy to EC2, `POST /api/rankings/seed`, reload site | New rankings visible | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| `FileNotFoundError` from loader | One of the 4 expected CSVs is missing | Raised by loader; router catches and returns `HTTPException(500, detail="Missing Fantasy Footballers file: ...")` |
| Empty DataFrame from loader | All 4 files exist but have only header rows | `seed_rankings()` returns a profile with `players: []`. UI shows empty columns. Acceptable — operator-visible signal. |
| `ValueError` on `int` coercion of `rank` | Source data has non-numeric rank | `pd.to_numeric(..., errors="coerce").fillna(0)` → rank becomes 0. Will sort first; cosmetic — operator can spot in UI. |
| Stale S3 `default.json` after deploy | S3 still has FantasyPros-shape rankings | Operator hits `POST /api/rankings/seed` per Step 10 to force a fresh rebuild from the new CSVs |

---

## Open Questions

All previously open questions have been resolved by review feedback:

- **Constants cleanup** (`YEARS`, `CSV_COLUMN_MAP`, `SCHEMA_COLUMNS`,
  `EXPECTED_COUNTS` in `constants.py`): **delete in this PRP.** Folded
  into Step 3.5. Dead code on the import path rots; trivial edit.
- **Function rename `load_all_players` → `load_player_data`**: **rename**
  per init. 3-callsite router update in Step 3.
- **ADR-010** (Fantasy Footballers as Seed Source — Supersedes ADR-003):
  **defer.** Claude.ai will author after execution succeeds.
- **Legacy `{POS}_{YEAR}.csv` cleanup**: **defer.** Loader is tested to
  ignore them; safety net stays until post-draft.

No outstanding blockers.

---

## Rollback Plan

1. **Code**:
   ```bash
   git revert <commit-sha>
   git push origin main
   ```
   The FantasyPros CSVs (`{POS}_{YEAR}.csv`) are still on disk, so the
   old loader works immediately.

2. **Data — local**:
   ```bash
   rm data/rankings/default.json
   ```
   Next request lazy-seeds from the old CSVs under the reverted code.

3. **Data — prod (EC2/S3)**:
   ```bash
   ./scripts/deploy.sh   # picks up reverted code
   curl -X POST https://ff.jurigregg.com/api/rankings/seed \
        -H "Authorization: Bearer <cognito-token>"
   ```
   `POST /seed` under the reverted code re-seeds from the old FantasyPros
   CSVs. If `seed.json` in S3 holds new-format rankings from a "Set as
   Default" click before rollback, also overwrite it (hit "Set as Default"
   again, or delete `s3://ff-draft-room-data/rankings/seed.json` via the
   AWS console).

4. **Verify**: load `/api/rankings/QB`; players should match prior
   FantasyPros-derived ordering (Lamar Jackson #1 QB by 2024 `total_pts`).

Rollback is safe and deterministic because both data sources coexist on
disk during the cutover window.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 9 | Spec is precise on file format, function signature, and what to drop. One minor ambiguity (rename vs. keep `load_all_players`) flagged with a default. |
| Feasibility | 10 | Pure backend refactor. ~50 LOC change in loader, ~6 LOC in `seed_rankings`, 3-line router rename, test migration. No framework or infrastructure changes. |
| Completeness | 9 | All affected files identified (including 2 not in init's "Files Touched" — routers and test_profile_management). Tests, manual smoke, deploy steps, rollback all covered. |
| Alignment | 8 | Conflicts with literal text of ADR-003 ("FantasyPros … only"); preserves its underlying *principle* (offline CSV, no approximations). ADR-010 follow-up flagged but not in this PRP. |
| **Average** | **9.0** | Ready for execution. |

---

## Notes

### Cache Removal Rationale
The original `_players_cache` in `data_loader.py` saved one disk read per
process — meaningful when loading 24 CSVs × multi-year stats. With 4 small
rank-only files, the cache adds complexity without measurable benefit and
has a `data_dir` override foot-gun (cached frame leaks across tests). Drop
it.

### Why a Strict Loader (FileNotFoundError) Instead of Silent Fallback
The old loader returned an empty DataFrame on missing files and logged a
warning. That silently masked a real problem (missing position file ==
broken seed). With only 4 files now, the right behavior is to fail loud at
the boundary and let the router translate to a 500 with the actual
filename. Operators (us) see what's wrong without grepping logs.

### Files on Disk vs. in Repo
The four new CSVs are already on disk locally (per `git status: ??`).
Step 9 stages them in the same commit so the seed is reproducible from a
fresh clone. Old `{POS}_{YEAR}.csv` files remain tracked in repo —
removing them is a separate cleanup PR after the first live draft using
the new data validates the cutover.
