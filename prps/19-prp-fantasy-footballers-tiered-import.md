# PRP-019: Fantasy Footballers Tiered Rankings Import

**Created**: 2026-05-31
**Initial**: `initials/19-init-fantasy-footballers-tiered-import.md`
**Status**: Draft

---

## Overview

### Problem Statement
PRP-017 wired the loader to read the rank-only Fantasy Footballers 2026 CSVs
(`2026 {POS} Draft Rankings - Fantasy Footballers Podcast.csv`, 6 columns).
Tier was synthesized in code via `_assign_tier()` because tiers weren't in
the source. Fantasy Footballers has now published a tiered, richer
variant of those rankings — same vendor, new filename, 13 columns
including expert tier assignments and six new analytical fields per
player (`Bye Week`, `Points`, `Risk`, `Upside`, `ADP`, `Outlook`).

The current loader cannot read these files, and `_assign_tier()` —
explicitly called out as temporary scaffolding in ADR-010 — needs to go.

### Proposed Solution
Hard cutover (same pattern as PRP-017). Re-point `data_loader.py` at the
new filename pattern (`2026_{POSITION}.csv`), expand the read to 10 of
the 13 columns, and add type coercion for the new fields. Simplify
`seed_rankings()` to source `tier` straight from the DataFrame and to
emit the six new fields on every player record. Delete `_assign_tier()`
and `TIER_BREAKPOINTS`. Migrate the three affected test files.

Full re-seed; existing `notes`/`tag` are not preserved (none have been
authored, per init). No UI changes — the new fields are persisted on
the data model only, ready for future UI work. No API surface change.

### Success Criteria
- [ ] `load_player_data(data_dir)` reads `2026_{POSITION}.csv` files and
  returns a DataFrame with columns `[name, team, position, rank, tier,
  bye_week, projected_points, risk, upside, adp, outlook]`
- [ ] FA rows preserve `team == ""`; empty `Bye Week` → `pd.NA` (yields
  `None` in JSON); empty `ADP` → `""` (yields `""` in JSON, never `"nan"`)
- [ ] `ADP` retains its string format (`"3.10"` not coerced to `3.1`)
- [ ] `Position`, `Dynasty`, `Markers` columns are silently dropped
- [ ] Missing position file → `FileNotFoundError` naming the file
- [ ] `_assign_tier()` and `TIER_BREAKPOINTS` no longer exist in `rankings.py`
- [ ] `seed_rankings(df)` emits player records with all six new fields plus
  `tier` sourced from the CSV — never from a heuristic
- [ ] `pytest tests/ -q` passes (target: ~93 — see Test Migration below)
- [ ] `ruff check backend/ tests/` — clean
- [ ] `uvicorn backend.main:app --reload` starts; after wiping
  `data/rankings/*.json`, `GET /api/rankings/QB` returns Josh Allen at
  rank 1 with `tier: 1`, `bye_week: 7`, full outlook blurb
- [ ] `cd frontend && npx vite build` — clean (sanity build; no FE code touched)
- [ ] Production deploy recipe documented (`POST /api/rankings/seed`)

---

## Context

### Related Documentation
- `docs/PLANNING.md` — data flow (CSV → loader → seed → profile JSON)
- `docs/DECISIONS.md` — ADR-002 (JSON), ADR-008 (StorageBackend / S3),
  ADR-010 (Fantasy Footballers as Seed Source — explicitly anticipates
  this tiered ingestion change)
- `docs/TESTING.md` — testing standards
- `prps/17-prp-fantasy-footballers-import.md` — prior cutover, same shape
- `initials/19-init-fantasy-footballers-tiered-import.md` — full spec

### ADR Alignment
ADR-010 (Fantasy Footballers as Seed Source) anticipates this exact
change: "Future-proofed for tiers. Fantasy Footballers will publish a
tiered version of these rankings… A follow-up re-seed will pick up
their tier assignments and replace the `_assign_tier()` heuristic."
This PRP is that follow-up. No new ADR is strictly required; init flags
ADR-011 (schema expansion) as an optional brief note for after execution.

### Dependencies
- **Required**: PRP-017 must be deployed (it is, per `docs/TASK.md`).
- **Optional**: none.

### Files to Modify / Create
```
backend/utils/data_loader.py            # MODIFY — new filename + 10-column read + coercion
backend/utils/rankings.py               # MODIFY — drop _assign_tier/TIER_BREAKPOINTS;
                                        #          seed_rankings reads tier + 6 new fields
tests/test_data_loader.py               # MODIFY — fixture: 13-column CSV; add 7 new tests
tests/test_rankings.py                  # MODIFY — _make_players adds new fields;
                                        #          +6 tests asserting new fields propagate
tests/test_profile_management.py        # MODIFY — _sample_df helper must include tier +
                                        #          new fields (Scope Expansion — see below)
data/players/2026_QB.csv                # ADD — already on disk, untracked; stage in commit
data/players/2026_RB.csv                # ADD — already on disk, untracked; stage in commit
data/players/2026_TE.csv                # ADD — already on disk, untracked; stage in commit
data/players/2026_WR.csv                # ADD — already on disk, untracked; stage in commit
"data/players/2026 QB Draft Rankings - Fantasy Footballers Podcast.csv"   # git rm
"data/players/2026 RB Draft Rankings - Fantasy Footballers Podcast.csv"   # git rm
"data/players/2026 TE Draft Rankings - Fantasy Footballers Podcast.csv"   # git rm
"data/players/2026 WR Draft Rankings - Fantasy Footballers Podcast.csv"   # git rm
initials/19-init-fantasy-footballers-tiered-import.md                     # untracked; include in commit
```

### Scope Expansion vs. Init

Init's "Files Touched" lists: `data_loader.py`, `rankings.py`,
`test_data_loader.py`, `test_rankings.py`, `tests/conftest.py`.
Three corrections / extras:

1. **`tests/test_profile_management.py`** (added). The `_sample_df()`
   helper at lines 33–38 builds rows with the *old* PRP-017 schema —
   `{name, team, position, rank}` only, no `tier`. After this PRP,
   `seed_rankings()` reads `row["tier"]` directly, so
   `test_reset_falls_back_to_csv` will KeyError without an update.
   - **Why**: downstream callsite breakage; not optional.
   - **Default chosen**: include in this PRP.
   - **Opt-out**: skip the test_profile_management.py edit and accept the
     known test failure — not recommended.

2. **`tests/conftest.py`** (removed from list). Init mentions updating
   the "shared `sample_df` fixture if used across files." There is no
   shared `sample_df` fixture in `conftest.py` (only a `storage`
   fixture). The `sample_df` fixture is local to `test_rankings.py`. No
   edit needed.
   - **Why**: init speculated; verified false.
   - **Default chosen**: skip conftest.py entirely.

3. **Legacy CSV git removal** (added). Operator already deleted the four
   `2026 {POS} Draft Rankings - …Podcast.csv` files locally (git status
   shows ` D`). Staging the deletion in this commit completes the
   filename cutover atomically and prevents a stale-tracked-file state.
   - **Why**: keeps repo and working tree in sync; matches PRP-017's
     pattern of atomic cutover.
   - **Default chosen**: include in this PRP's commit.

### Files NOT Modified (intentional)
```
backend/routers/rankings.py        # API surface unchanged (no new endpoints,
                                   #  no body schema changes); load_player_data
                                   #  callsites already correct from PRP-017
backend/utils/constants.py         # POSITIONS / VOR_REPLACEMENT_LEVELS unaffected
backend/utils/storage.py           # No storage interface change
frontend/**                        # No UI changes (out of scope per init)
data/players/{POS}_{20XX}.csv      # Legacy FantasyPros files — already
                                   #  ignored by loader; deletion deferred
```

---

## Technical Specification

### New CSV Format (input)

**Filename pattern** under `data/players/`:
```
2026_{POSITION}.csv      # POSITION ∈ {QB, RB, WR, TE}
```

**Columns** (13, header row, quoted strings):
```
Name, Position, Team, Bye Week, Rank, Points, Risk, Upside, ADP, Tier, Outlook, Dynasty, Markers
```

| Column | Type | Empty Cases | Loader Handling |
|---|---|---|---|
| `Name` | str | not observed empty | strip; passthrough |
| `Position` | str | n/a | **dropped** (filename is source of truth) |
| `Team` | str | observed for FA (e.g. nobody in QB file) | NaN → `""`; strip |
| `Bye Week` | int 5–14 | Mendoza, Beck, Watson | NaN → `pd.NA`; nullable Int64 |
| `Rank` | int 1+ | not observed empty | coerce to int |
| `Points` | float | not observed empty | float |
| `Risk` | float 0–10 | not observed empty | float |
| `Upside` | float 0–10 | not observed empty | float |
| `ADP` | str `RR.PP` | Rodgers, Smith, Beck, Cousins, Watson | **dtype=str** (preserve `"3.10"`); NaN → `""`; strip |
| `Tier` | int 1+ | not observed empty | coerce to int |
| `Outlook` | str | not observed empty | NaN → `""` |
| `Dynasty` | str | always paywall stub | **dropped** |
| `Markers` | str | always HTML stub | **dropped** |

### Output DataFrame columns (post-loader)

```python
["name", "team", "position", "rank", "tier",
 "bye_week", "projected_points", "risk", "upside", "adp", "outlook"]
```

Column renames:
- `Name` → `name`
- `Team` → `team`
- `Bye Week` → `bye_week`
- `Rank` → `rank`
- `Points` → `projected_points` (disambiguates from "scoring points")
- `Risk` → `risk`
- `Upside` → `upside`
- `ADP` → `adp`
- `Tier` → `tier`
- `Outlook` → `outlook`

`position` is added from the filename (filename overrides the
duplicate `Position` column in the source).

### `backend/utils/data_loader.py` — Updated

```python
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
```

### `backend/utils/rankings.py` — Updated

**Delete** (top of file):
- `TIER_BREAKPOINTS` dict (lines 21–26)
- `_assign_tier()` function (lines 34–43)

**Replace** `seed_rankings()` (lines 46–78):

```python
def seed_rankings(df: pd.DataFrame) -> dict:
    """Build the initial default profile from Fantasy Footballers tiered rankings.

    Sorts by rank ascending, takes top N per position per SEED_LIMITS,
    and emits player records with tier sourced directly from the CSV
    (no heuristic) plus the six new analytical fields (bye_week, adp,
    projected_points, risk, upside, outlook).
    """
    players: list[dict] = []
    for position in POSITIONS:
        pos_df = df[df["position"] == position].copy()
        pos_df = pos_df.sort_values("rank", ascending=True)
        limit = SEED_LIMITS.get(position, 20)
        pos_df = pos_df.head(limit)

        for i, (_, row) in enumerate(pos_df.iterrows(), start=1):
            bye = row["bye_week"]
            players.append({
                "position_rank": i,
                "name": row["name"],
                "team": row["team"],
                "position": position,
                "tier": int(row["tier"]),
                "bye_week": int(bye) if pd.notna(bye) else None,
                "adp": row["adp"],
                "projected_points": float(row["projected_points"]),
                "risk": float(row["risk"]),
                "upside": float(row["upside"]),
                "outlook": row["outlook"],
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

**Unchanged** in `rankings.py`: `SEED_LIMITS`, `_default_storage()`,
`load_or_seed`, `save_rankings`, `get_position_players`, `swap_players`,
`delete_player`, `set_player_tier`, `set_player_tag`, all
profile-management helpers.

**Modified** in `rankings.py`: `add_player()` is extended to emit the
same 13-field player record as the seed path, with the six new fields
accepted as optional kwargs and defaulting to `None` / `""`. This keeps
seeded and manually-added rows shape-consistent — downstream code
(future UI work for the new fields) won't need to special-case
manually-added players. The current 2-field AddPlayer dialog continues
to call the existing endpoint unchanged; the frontend and router body
schema stay the same in this PRP. Richer manual entry is deferred to
PRP-020.

New signature:

```python
def add_player(
    profile: dict,
    name: str,
    team: str,
    position: str,
    tier: int,
    *,
    bye_week: int | None = None,
    adp: str = "",
    projected_points: float | None = None,
    risk: float | None = None,
    upside: float | None = None,
    outlook: str = "",
) -> dict:
```

`None` (not `0.0`) is the default for the numeric fields — `0.0` would
look like a real low projection / risk / upside; `null` correctly
signals "unknown" to the UI.

### Player Record Shape (post-seed)

```json
{
  "position_rank": 1,
  "name": "Josh Allen",
  "team": "BUF",
  "position": "QB",
  "tier": 1,
  "bye_week": 7,
  "adp": "3.05",
  "projected_points": 428.3,
  "risk": 2.6,
  "upside": 9.7,
  "outlook": "He is him. While technically Allen finished with…",
  "notes": "",
  "tag": ""
}
```

For Aaron Rodgers (no ADP): `"adp": ""`.
For Carson Beck (no Bye Week): `"bye_week": null`.

### API — Unchanged
Zero route changes. `GET /api/rankings/QB` simply returns each player
dict with 6 extra keys. Frontend ignores unknown keys, so no breakage.

---

## Implementation Steps

### Step 1 — Rewrite `data_loader.py`
**Files**: `backend/utils/data_loader.py`

Replace the file contents per the spec above. Key edits:
- `FILENAME_TEMPLATE` becomes `"2026_{position}.csv"`
- `READ_COLUMNS` and `_RENAME` introduced
- `OUTPUT_COLUMNS` extended to 11 columns
- `_load_one()` reads with `dtype={"ADP": str}`, then performs explicit
  per-column coercion (rank/tier → int, bye_week → Int64, points/risk/
  upside → float, adp/name/team/outlook → str with `fillna("")`)

**Validation**:
```bash
ruff check backend/utils/data_loader.py
python -c "import sys; sys.path.insert(0, 'backend'); \
  from utils.data_loader import load_player_data; \
  df = load_player_data(); \
  print(df.shape); print(df.dtypes); \
  print(df[df['name']=='Josh Allen'].iloc[0].to_dict()); \
  print('FA ADP:', repr(df[df['name']=='Aaron Rodgers'].iloc[0]['adp'])); \
  print('Empty bye:', df[df['name']=='Carson Beck'].iloc[0]['bye_week'])"
```
Expected: ~305 rows × 11 cols; Josh Allen `tier=1, bye_week=7, adp='3.05'`;
Aaron Rodgers `adp=''`; Carson Beck `bye_week=<NA>`.

- [ ] File ≤ 500 lines (actual: ~75)
- [ ] Lint clean
- [ ] Smoke output matches expectations

---

### Step 2 — Simplify `seed_rankings()` + delete heuristic + extend `add_player()`
**Files**: `backend/utils/rankings.py`

1. Delete `TIER_BREAKPOINTS` (lines 21–26)
2. Delete `_assign_tier()` (lines 34–43)
3. Replace `seed_rankings()` body per spec (reads `row["tier"]` + new fields)
4. Extend `add_player()` signature with six optional kwargs
   (`bye_week`, `adp`, `projected_points`, `risk`, `upside`, `outlook`)
   and update the constructed `new_player` dict to include them. Numeric
   defaults are `None`, string defaults are `""`. The existing required
   positional args (`name`, `team`, `position`, `tier`) and all internal
   logic (insertion index, renumber loop) stay byte-identical. The
   router callsite (`backend/routers/rankings.py:287-290`) continues to
   pass only the 4 required positionals — the new kwargs all take their
   defaults, so the endpoint behaves identically for the current frontend.
5. Leave everything else byte-identical

**Validation**:
```bash
ruff check backend/utils/rankings.py
grep -n "_assign_tier\|TIER_BREAKPOINTS" backend/ tests/ -r
# expected: zero matches
```
- [ ] Both heuristic symbols gone from the repo
- [ ] `add_player()` signature has the 6 new keyword-only args with the
  right defaults
- [ ] `swap_players`, `delete_player`, `set_player_tier`, `set_player_tag`,
  all profile helpers untouched (verify via `git diff`)
- [ ] No new imports needed (`pd.notna` lives on already-imported pandas)

---

### Step 3 — Migrate `tests/test_data_loader.py`
**Files**: `tests/test_data_loader.py`

Update the `_write_csv` helper to emit the 13-column Fantasy Footballers
tiered format. Update existing assertions to the new column list. Add
edge-case tests for the new behaviours.

```python
"""Unit tests for utils.data_loader (Fantasy Footballers tiered format)."""

from __future__ import annotations

import pandas as pd
import pytest

from utils.data_loader import FILENAME_TEMPLATE, load_player_data

EXPECTED_COLUMNS = [
    "name", "team", "position", "rank", "tier",
    "bye_week", "projected_points", "risk", "upside", "adp", "outlook",
]


def _write_csv(tmp_path, position: str, rows: list[dict]) -> None:
    """Write a Fantasy Footballers tiered-format CSV for one position.

    Each row dict may supply any subset of:
      name, team, bye_week, rank, points, risk, upside, adp, tier, outlook
    Missing keys default to sensible values.
    """
    header = (
        '"Name","Position","Team","Bye Week","Rank","Points","Risk",'
        '"Upside","ADP","Tier","Outlook","Dynasty","Markers"\n'
    )
    lines = []
    for r in rows:
        lines.append(
            f'"{r.get("name","X")}",'
            f'"{position}",'                        # Position column (will be dropped)
            f'"{r.get("team","TST")}",'
            f'"{r.get("bye_week","7")}",'
            f'"{r.get("rank",1)}",'
            f'"{r.get("points","100.0")}",'
            f'"{r.get("risk","5.0")}",'
            f'"{r.get("upside","5.0")}",'
            f'"{r.get("adp","10.05")}",'
            f'"{r.get("tier",1)}",'
            f'"{r.get("outlook","Blurb.")}",'
            f'"Unlock with the 2026 UDK+."'         # Dynasty (will be dropped)
            f',"Mark Drafted Mark Keeper"'          # Markers (will be dropped)
        )
    path = tmp_path / FILENAME_TEMPLATE.format(position=position)
    path.write_text(header + "\n".join(lines) + "\n")


@pytest.fixture
def full_sample(tmp_path):
    """Four position files, 3 rows each, covering edge cases in QB."""
    _write_csv(tmp_path, "QB", [
        {"name": "Josh Allen", "team": "BUF", "bye_week": "7",
         "rank": 1, "tier": 1, "points": "428.3", "risk": "2.6",
         "upside": "9.7", "adp": "3.05", "outlook": "Elite."},
        {"name": "Aaron Rodgers", "team": "PIT", "bye_week": "5",
         "rank": 2, "tier": 2, "adp": ""},                       # empty ADP
        {"name": "Carson Beck", "team": "ARI", "bye_week": "",
         "rank": 3, "tier": 2, "adp": ""},                       # empty bye + ADP
    ])
    _write_csv(tmp_path, "RB", [{"name": "Bijan Robinson", "team": "ATL", "rank": 1, "tier": 1},
                                {"name": "Jahmyr Gibbs", "team": "DET", "rank": 2, "tier": 1},
                                {"name": "Saquon Barkley", "team": "PHI", "rank": 3, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "CeeDee Lamb", "team": "DAL", "rank": 1, "tier": 1},
                                {"name": "Justin Jefferson", "team": "MIN", "rank": 2, "tier": 1},
                                {"name": "Ja'Marr Chase", "team": "CIN", "rank": 3, "tier": 1}])
    _write_csv(tmp_path, "TE", [{"name": "Sam LaPorta", "team": "DET", "rank": 1, "tier": 1},
                                {"name": "Trey McBride", "team": "ARI", "rank": 2, "tier": 1},
                                {"name": "Brock Bowers", "team": "LV", "rank": 3, "tier": 1}])
    return tmp_path


def test_load_returns_expected_columns(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert list(df.columns) == EXPECTED_COLUMNS


def test_load_all_positions_present(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert sorted(df["position"].unique().tolist()) == ["QB", "RB", "TE", "WR"]
    assert (df["position"].value_counts() == 3).all()


def test_load_drops_dynasty_and_markers(full_sample):
    df = load_player_data(data_dir=full_sample)
    for col in ("Dynasty", "Markers", "Position"):
        assert col not in df.columns


def test_load_position_from_filename_overrides_csv_column(tmp_path):
    """Even if the in-file Position column disagreed, the filename wins."""
    _write_csv(tmp_path, "QB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "RB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "TE", [{"name": "X", "rank": 1, "tier": 1}])
    df = load_player_data(data_dir=tmp_path)
    assert df[df["position"] == "QB"].iloc[0]["position"] == "QB"


def test_load_rank_and_tier_are_int(full_sample):
    df = load_player_data(data_dir=full_sample)
    assert df["rank"].dtype == "int64"
    assert df["tier"].dtype == "int64"


def test_load_float_fields(full_sample):
    df = load_player_data(data_dir=full_sample)
    for col in ("projected_points", "risk", "upside"):
        assert df[col].dtype == "float64"


def test_load_bye_week_empty_is_na(full_sample):
    df = load_player_data(data_dir=full_sample)
    beck = df[df["name"] == "Carson Beck"].iloc[0]
    assert pd.isna(beck["bye_week"])


def test_load_bye_week_populated_is_int(full_sample):
    df = load_player_data(data_dir=full_sample)
    allen = df[df["name"] == "Josh Allen"].iloc[0]
    assert int(allen["bye_week"]) == 7


def test_load_adp_empty_is_empty_string(full_sample):
    df = load_player_data(data_dir=full_sample)
    rodgers = df[df["name"] == "Aaron Rodgers"].iloc[0]
    assert rodgers["adp"] == ""
    assert isinstance(rodgers["adp"], str)


def test_load_adp_preserves_trailing_zero(tmp_path):
    """'3.10' must stay '3.10', not be coerced to 3.1."""
    _write_csv(tmp_path, "QB", [{"name": "X", "rank": 1, "tier": 1, "adp": "3.10"}])
    _write_csv(tmp_path, "RB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "TE", [{"name": "X", "rank": 1, "tier": 1}])
    df = load_player_data(data_dir=tmp_path)
    assert df[df["position"] == "QB"].iloc[0]["adp"] == "3.10"


def test_load_outlook_passthrough(full_sample):
    df = load_player_data(data_dir=full_sample)
    allen = df[df["name"] == "Josh Allen"].iloc[0]
    assert allen["outlook"] == "Elite."


def test_load_preserves_fa_empty_team(tmp_path):
    _write_csv(tmp_path, "QB", [{"name": "FA Guy", "team": "", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "RB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "TE", [{"name": "X", "rank": 1, "tier": 1}])
    df = load_player_data(data_dir=tmp_path)
    assert df[df["name"] == "FA Guy"].iloc[0]["team"] == ""


def test_load_missing_file_raises(tmp_path):
    _write_csv(tmp_path, "QB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "RB", [{"name": "X", "rank": 1, "tier": 1}])
    _write_csv(tmp_path, "WR", [{"name": "X", "rank": 1, "tier": 1}])
    with pytest.raises(FileNotFoundError, match="TE"):
        load_player_data(data_dir=tmp_path)


def test_load_ignores_legacy_pos_year_csvs(full_sample):
    (full_sample / "QB_2025.csv").write_text(
        '"#","Player","Pos","Team","GP","AVG","TTL"\n'
        '"1","Should Not Appear","QB","XXX","16","99.9","999.9"\n'
    )
    df = load_player_data(data_dir=full_sample)
    assert "Should Not Appear" not in df["name"].values


def test_load_ignores_old_naming_pattern_csvs(full_sample):
    """The pre-PRP-019 long-form filename must not be read."""
    long_name = full_sample / "2026 QB Draft Rankings - Fantasy Footballers Podcast.csv"
    long_name.write_text(
        '"Name","Team","Rank","Andy","Jason","Mike"\n'
        '"Old Pattern","XXX","1","1","1","1"\n'
    )
    df = load_player_data(data_dir=full_sample)
    assert "Old Pattern" not in df["name"].values
```

(That's ~15 tests, replacing the prior 9.)

**Validation**:
```bash
pytest tests/test_data_loader.py -v
ruff check tests/test_data_loader.py
```
- [ ] All tests pass
- [ ] No reference to the old short-column format (`Andy`, `Jason`, `Mike`)
  in assertions

---

### Step 4 — Migrate `tests/test_rankings.py`
**Files**: `tests/test_rankings.py`

Update `_make_players` so generated DataFrame rows carry the new schema
(seed_rankings will KeyError otherwise):

```python
def _make_players(position: str, n: int) -> list[dict]:
    """Generate n fake player rows for a position (tiered schema)."""
    return [
        {
            "name": f"{position}_Player_{i}",
            "team": f"T{i:02d}",
            "position": position,
            "rank": i,
            "tier": ((i - 1) // 3) + 1,    # 3 players per tier — monotonic
            "bye_week": 7 if i % 4 else pd.NA,   # mix populated + NA
            "projected_points": 200.0 - i,
            "risk": 5.0,
            "upside": 5.0,
            "adp": f"{i // 12 + 1}.{i % 12:02d}",   # "1.01", "1.02", …
            "outlook": f"Outlook for {position} #{i}",
        }
        for i in range(1, n + 1)
    ]
```

`sample_df` fixture is unchanged in body (still `pd.DataFrame(rows)`),
but the rows now have the new columns. `pd.DataFrame` will infer
`bye_week` as `object` (mix of int and NA). That's fine — `pd.notna()`
in `seed_rankings()` handles both.

Add the following new tests after the existing seeding tests:

```python
def test_seed_tier_from_csv(sample_df):
    """Tier comes from CSV column, not a heuristic."""
    profile = seed_rankings(sample_df)
    qb1 = next(p for p in profile["players"]
               if p["position"] == "QB" and p["position_rank"] == 1)
    assert qb1["tier"] == 1   # _make_players assigns tier=1 to i=1


def test_seed_includes_bye_week_int(sample_df):
    profile = seed_rankings(sample_df)
    populated = [p for p in profile["players"] if p["bye_week"] is not None]
    assert populated, "expected at least one populated bye_week"
    for p in populated:
        assert isinstance(p["bye_week"], int)


def test_seed_bye_week_na_becomes_none(sample_df):
    profile = seed_rankings(sample_df)
    nones = [p for p in profile["players"] if p["bye_week"] is None]
    assert nones, "expected at least one None bye_week (NA in fixture)"


def test_seed_includes_adp_string(sample_df):
    profile = seed_rankings(sample_df)
    for p in profile["players"]:
        assert isinstance(p["adp"], str)


def test_seed_includes_projected_points_float(sample_df):
    profile = seed_rankings(sample_df)
    for p in profile["players"]:
        assert isinstance(p["projected_points"], float)


def test_seed_includes_risk_upside_float(sample_df):
    profile = seed_rankings(sample_df)
    for p in profile["players"]:
        assert isinstance(p["risk"], float)
        assert isinstance(p["upside"], float)


def test_seed_includes_outlook_string(sample_df):
    profile = seed_rankings(sample_df)
    for p in profile["players"]:
        assert isinstance(p["outlook"], str)
        assert p["outlook"]   # non-empty in fixture


def test_seed_no_assign_tier_symbol():
    """Sanity: _assign_tier must not exist in rankings.py."""
    from utils import rankings
    assert not hasattr(rankings, "_assign_tier")
    assert not hasattr(rankings, "TIER_BREAKPOINTS")


def test_add_player_emits_full_schema(sample_profile):
    """Manually-added players have the same 13 fields as seeded ones,
    with optional fields defaulting to None/''."""
    result = add_player(sample_profile, "Test Player", "FA", "QB", tier=5)
    new_player = next(p for p in result["players"]
                      if p["name"] == "Test Player")
    assert new_player["bye_week"] is None
    assert new_player["adp"] == ""
    assert new_player["projected_points"] is None
    assert new_player["risk"] is None
    assert new_player["upside"] is None
    assert new_player["outlook"] == ""
    # Existing fields still present:
    assert new_player["tier"] == 5
    assert new_player["notes"] == ""
    assert new_player["tag"] == ""
```

`test_seed_has_tier` and `test_seed_tier_nondecreasing` continue to
pass — `_make_players` assigns tiers `1,1,1,2,2,2,3,…` which is
non-decreasing.

**Do not** add `bye_week`/`adp`/etc. fields to `sample_profile` (the
CRUD-test fixture). The swap/add/delete tests don't care about those
fields, and `add_player()` does not emit them either (out of scope per
init).

**Validation**:
```bash
pytest tests/test_rankings.py -v
```
- [ ] All tests pass (prior 32 + 8 new seeding/sanity + 1 add_player schema = 41)
- [ ] `_assign_tier` is not importable
- [ ] Existing `add_player` tests (`test_add_player_appended_to_tier`,
  `test_add_player_rank_assigned`, `test_add_player_subsequent_ranks_shifted`,
  `test_add_player_does_not_mutate_input`) continue to pass — the 6 new
  fields are additive

---

### Step 5 — Update `tests/test_profile_management.py`
**Files**: `tests/test_profile_management.py`

Replace `_sample_df()` (lines 33–38) to emit the new schema, otherwise
`test_reset_falls_back_to_csv` will KeyError when `seed_rankings()`
reads `row["tier"]`:

```python
def _sample_df() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "name": f"QB_{i}",
            "team": "T",
            "position": "QB",
            "rank": i,
            "tier": 1,
            "bye_week": 7,
            "projected_points": 100.0,
            "risk": 5.0,
            "upside": 5.0,
            "adp": f"1.{i:02d}",
            "outlook": "",
        }
        for i in range(1, 6)
    ])
```

No other tests need changes; `_sample_profile()` builds profile dicts
directly (not via seed_rankings).

**Validation**:
```bash
pytest tests/test_profile_management.py -v
```
- [ ] All 21 tests still pass

---

### Step 6 — Full Suite + Lint
**Validation**:
```bash
pytest tests/ -q
ruff check backend/ tests/
```
- [ ] All tests pass. Target: **97** (82 baseline + 6 new in
  `test_data_loader.py` + 9 new in `test_rankings.py` [8 seeding/sanity
  + 1 add_player schema]; `test_profile_management.py` unchanged in
  count). Investigate any *decrease* from baseline.
- [ ] ruff clean

---

### Step 7 — Local Smoke Test
**Commands**:
```bash
rm -f data/rankings/default.json data/rankings/seed.json

source .venv/bin/activate
uvicorn backend.main:app --reload &
sleep 2

curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/rankings/QB | python -m json.tool | head -30
```
- [ ] `/health` returns 200
- [ ] First QB returned is Josh Allen with: `position_rank: 1`, `tier: 1`,
  `bye_week: 7`, `adp: "3.05"`, `projected_points: 428.3`, `risk: 2.6`,
  `upside: 9.7`, non-empty `outlook`
- [ ] Search response for Aaron Rodgers: `adp: ""`
- [ ] Search response for Carson Beck (if in top 30): `bye_week: null`

```bash
# Sanity: hit the React UI too (no UI changes expected)
cd frontend && npx vite build
```
- [ ] Build clean

Optional manual browser pass at `localhost:5173`:
- [ ] War Room renders 4 columns, correct depths (30/50/50/30)
- [ ] No regressions in tier dividers, team logos, gradients, search,
  draft mode toggle, profile management

> The new fields ride along in the API response but the UI doesn't
> render them yet — that's expected per init Out of Scope.

---

### Step 8 — Commit + Push
```bash
git add backend/utils/data_loader.py \
        backend/utils/rankings.py \
        tests/test_data_loader.py \
        tests/test_rankings.py \
        tests/test_profile_management.py \
        data/players/2026_QB.csv \
        data/players/2026_RB.csv \
        data/players/2026_TE.csv \
        data/players/2026_WR.csv \
        initials/19-init-fantasy-footballers-tiered-import.md
git add -u "data/players/2026 QB Draft Rankings - Fantasy Footballers Podcast.csv" \
           "data/players/2026 RB Draft Rankings - Fantasy Footballers Podcast.csv" \
           "data/players/2026 TE Draft Rankings - Fantasy Footballers Podcast.csv" \
           "data/players/2026 WR Draft Rankings - Fantasy Footballers Podcast.csv"
git commit -m "feat: ingest Fantasy Footballers tiered 2026 rankings + 6 new player fields"
git push origin main
```

> **Explicitly excluded**: `data/rankings/*.json` (gitignored since PRP-018).

- [ ] Single atomic commit pushed to `origin/main`
- [ ] `git status` clean afterward (no stray files)

---

### Step 9 — Production Deploy
**On EC2**:
```bash
git pull origin main
./scripts/deploy.sh
```

**Force fresh seed from new CSVs**:
- Option A (UI): click Reset in the toolbar. `seed.json` doesn't exist
  in S3 (verified per PRP-017), so Reset falls through to the CSV
  re-seed path.
- Option B (API):
  ```bash
  curl -X POST https://ff.jurigregg.com/api/rankings/seed \
       -H "Authorization: Bearer <cognito-token>"
  ```

**Caveat re: `seed.json`** (same as PRP-017 Step 10): if a "Set as
Default" has been clicked since the last seed, the old PRP-017-shape
baseline will live on. Either click "Set as Default" again after the
re-seed, or delete `s3://ff-draft-room-data/rankings/seed.json` via
the AWS console.

- [ ] App loads at `https://ff.jurigregg.com`
- [ ] After re-seed, the API response includes the new fields
- [ ] No 5xx in nginx / uvicorn logs

---

## Testing Requirements

### Unit Tests

**`tests/test_data_loader.py`** — ~15 tests (was 9):
- `test_load_returns_expected_columns` — 11-column shape
- `test_load_all_positions_present` — 4 positions concatenated
- `test_load_drops_dynasty_and_markers` — Dynasty/Markers/Position absent
- `test_load_position_from_filename_overrides_csv_column`
- `test_load_rank_and_tier_are_int`
- `test_load_float_fields` — projected_points/risk/upside
- `test_load_bye_week_empty_is_na`
- `test_load_bye_week_populated_is_int`
- `test_load_adp_empty_is_empty_string`
- `test_load_adp_preserves_trailing_zero` — `"3.10"` not `3.1`
- `test_load_outlook_passthrough`
- `test_load_preserves_fa_empty_team`
- `test_load_missing_file_raises`
- `test_load_ignores_legacy_pos_year_csvs`
- `test_load_ignores_old_naming_pattern_csvs` — PRP-017 filename pattern

**`tests/test_rankings.py`** — ~40 tests (was 32):
- All existing tests continue to pass with updated `_make_players`
- New: `test_seed_tier_from_csv`, `test_seed_includes_bye_week_int`,
  `test_seed_bye_week_na_becomes_none`, `test_seed_includes_adp_string`,
  `test_seed_includes_projected_points_float`,
  `test_seed_includes_risk_upside_float`,
  `test_seed_includes_outlook_string`,
  `test_seed_no_assign_tier_symbol`

**`tests/test_profile_management.py`** — 21 tests (unchanged count):
- `_sample_df()` helper updated; `test_reset_falls_back_to_csv` continues
  to pass with the new schema

### API Tests (curl, local)
```bash
BASE="http://localhost:8000/api"
curl -s $BASE/rankings/QB | python -c "
import json, sys
qb = json.load(sys.stdin)
allen = next(p for p in qb if p['name']=='Josh Allen')
assert allen['tier'] == 1, allen
assert allen['bye_week'] == 7, allen
assert allen['adp'] == '3.05', allen
assert allen['outlook'].startswith('He is him'), allen
print('OK')
"
```

### Manual Browser Tests
- War Room renders unchanged (no UI for new fields yet)
- Draft Mode toggle works
- Profile save / load / reset all work
- No console errors

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | ~93 pass, 1 skipped | ☐ |
| 2 | `ruff check backend/ tests/` | Clean | ☐ |
| 3 | `rm -f data/rankings/default.json data/rankings/seed.json` | Files gone | ☐ |
| 4 | `uvicorn backend.main:app --reload` | Starts, no errors | ☐ |
| 5 | `curl http://localhost:8000/health` | 200 OK | ☐ |
| 6 | `curl http://localhost:8000/api/rankings/QB` | 30 players; Allen #1 with tier/bye_week/adp/outlook | ☐ |
| 7 | `curl http://localhost:8000/api/rankings/RB` | 50 players, new fields present | ☐ |
| 8 | grep Aaron Rodgers in response | `adp == ""` | ☐ |
| 9 | grep Carson Beck (if in top 30) | `bye_week == null` | ☐ |
| 10 | `curl -X POST http://localhost:8000/api/rankings/seed` | Fresh profile | ☐ |
| 11 | `cd frontend && npx vite build` | Build clean | ☐ |
| 12 | `cd frontend && npm run dev` → browser | War Room renders, all features work | ☐ |
| 13 | Deploy to EC2; `POST /api/rankings/seed` | New rankings visible | ☐ |
| 14 | Inspect S3 `rankings/default.json` | Includes new fields | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| `FileNotFoundError` from loader | One of the 4 CSVs missing | Loader raises naming the file; router catches → `HTTPException(500, detail="Missing Fantasy Footballers file: ...")` (unchanged behaviour from PRP-017) |
| `ValueError` on numeric coercion | Source has non-numeric `Rank` / `Tier` / `Points` | `pd.to_numeric(..., errors="coerce")` → 0 / NaN → 0 for ints; NaN for floats. Cosmetic; operator can spot in UI |
| Empty cell on `Bye Week` | Unsigned/uncertain player | `pd.NA` in DataFrame → `None` in JSON via `pd.notna()` check in seed |
| Empty cell on `ADP` | Player without ADP data | NaN → `""` (string) via `fillna("").astype(str)` |
| Pydantic 422 on routes | Bad request body | Unchanged — same 14 endpoints, no new bodies |
| Stale S3 `default.json` after deploy | S3 still has PRP-017-shape rankings | Operator hits `POST /seed` or Reset to force a fresh rebuild |

---

## Open Questions

All resolved by the init or this PRP:

- **Preserve `notes`/`tag` across re-seed?** No — full wipe, none authored
  (init Out of Scope).
- **`adp` numerical sort?** No — stored as string; future change if needed.
- **ADR-011 for schema expansion?** Deferred — operator decides after
  execution (init Follow-ups).
- **`add_player()` shape update?** Folded in (per review feedback).
  Backend-only: signature extended with six optional kwargs defaulting
  to `None` / `""`. Router body schema and frontend dialog unchanged in
  this PRP — PRP-020 handles richer manual entry.
- **`conftest.py` shared fixture update?** Not needed — no shared `sample_df`
  fixture exists; `sample_df` is local to `test_rankings.py`.

No outstanding blockers.

---

## Rollback Plan

1. **Code**:
   ```bash
   git revert <commit-sha>
   git push origin main
   ```
   The legacy short-name CSVs were removed in this PRP's commit, but
   `git revert` restores them. The PRP-017 loader is also restored, so
   the loader expects (and finds) the short-name files.

2. **Data — local**:
   ```bash
   rm -f data/rankings/default.json
   ```
   Next request lazy-seeds from the restored PRP-017 loader + CSVs.

3. **Data — prod (EC2/S3)**:
   ```bash
   git pull origin main && ./scripts/deploy.sh
   curl -X POST https://ff.jurigregg.com/api/rankings/seed \
        -H "Authorization: Bearer <cognito-token>"
   ```
   If `seed.json` in S3 holds tiered-shape rankings (from a "Set as
   Default" click before rollback), overwrite it (re-click "Set as
   Default" under the reverted code, or delete the S3 object).

4. **Verify**: `/api/rankings/QB` returns players without the 6 new
   fields, tiers from `_assign_tier()` heuristic.

   Note: after `POST /seed` runs on the reverted code, the six new
   fields (`bye_week`, `adp`, `projected_points`, `risk`, `upside`,
   `outlook`) are gone from `s3://ff-draft-room-data/rankings/default.json`
   entirely. Rollback restores the old shape end-to-end — the rich data
   isn't hidden, it's overwritten. To recover the new fields after
   rollback, roll forward again.

Rollback is straightforward because the player record shape additions
are additive — old code reading new data simply ignores the extra keys,
and revert + reseed restores the old shape end-to-end.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Spec is precise on column-by-column behaviour; init plus inspected real CSV rows confirm every type/empty case. Function bodies given verbatim. |
| Feasibility | 10 | Pure backend refactor + test migration. ~25 LOC added to loader; ~10 LOC change in `seed_rankings`; ~30 LOC of test fixture updates. Zero infra/framework moves. |
| Completeness | 10 | All affected files identified including the two outside the init's literal list (test_profile_management.py — downstream KeyError risk; legacy CSV git-rm — atomic cutover). Conftest.py confirmed not needed. Tests + smoke + deploy + rollback covered. |
| Alignment | 10 | ADR-010 explicitly anticipates this change. No new ADR strictly required (init flags ADR-011 as optional). No conflict with ADR-002/006/008. Single-user, JSON, no external API at runtime — all preserved. |
| **Average** | **10.0** | Ready for execution. |

---

## Notes

### Why dtype={"ADP": str}, not post-hoc astype
`pd.read_csv` infers ADP as float by default ("3.05" → 3.05). Going
through float drops trailing zeros (`"3.10"` → `3.1`), which is real
data loss because Fantasy Footballers' RR.PP format treats 3.10 (round
3, pick 10) and 3.1 (round 3, pick 1) as distinct positions.
`dtype={"ADP": str}` reads the column as object dtype from the start,
preserving the original string. Tested in `test_load_adp_preserves_trailing_zero`.

### Why `pd.Int64` for bye_week
Plain `int` doesn't support NaN, and a float `bye_week` would surface
in JSON as `7.0` instead of `7`. Pandas' nullable `Int64` keeps integer
arithmetic and supports `pd.NA`, which `pd.notna()` in `seed_rankings`
converts cleanly to either Python `int` or `None`.

### `add_player()` now emits the full 13-field schema
`add_player()` now emits the full 13-field schema with optional fields
defaulting to `None` / `""`. The current 2-field AddPlayer dialog
continues to work unchanged; richer manual entry (UI + request body
schema) is the subject of PRP-020.

Per the operator: manual add will still be needed in-season (unsigned
WRs landing on rosters late summer), so seeded-vs-added shape parity
is a real consistency fix, not dead-code maintenance — it prevents
"field not present" branches in the upcoming UI work for the new fields.

### File size
`data_loader.py` ~75 lines (well under 500). `rankings.py` shrinks by
~15 lines after deleting the heuristic, then grows by ~10 lines in the
seed body — net ~−5 lines (well under 500). No split-plan needed.
