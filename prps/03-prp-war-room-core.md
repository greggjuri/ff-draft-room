# PRP-03: War Room Core — Rankings Board

**Created**: 2026-03-30
**Initial**: `initials/03-init-war-room-core.md`
**Status**: Ready

---

## Overview

### Problem Statement
The app currently has a War Room stub that says "Coming soon." The user needs a fully functional pre-draft rankings board — the entire purpose of the application. The board must display players in four positional columns (QB / RB / WR / TE), grouped by tiers, with the ability to reorder players, add/delete players, take notes, and save rankings to disk.

### Proposed Solution
Build the War Room as a four-column Streamlit layout. Each column renders one position's players grouped by tier with visual dividers. Rankings are seeded from 2025 CSV data on first launch, persisted as JSON, and managed entirely through `app/utils/rankings.py`. Player reordering uses ▲▼ buttons with automatic tier reassignment on boundary crossings.

### Success Criteria
- [ ] `streamlit run app/main.py` → War Room renders with 4 columns
- [ ] First launch: QB 30, RB 50, WR 50, TE 30 players seeded from 2025 data
- [ ] Players grouped under tier dividers within each column
- [ ] ▲▼ reorders players; ranks renumber immediately
- [ ] Moving across tier boundary updates the player's tier
- [ ] `[+ Position · Tier N]` button adds a new player to the correct tier
- [ ] `[x]` delete button with confirm dialog, ranks renumber after
- [ ] Clicking player name opens notes dialog with Save/Close
- [ ] `● Unsaved` indicator appears after any change
- [ ] SAVE button writes JSON, clears dirty, shows toast
- [ ] State persists across page reloads (JSON on disk)
- [ ] `pytest tests/test_rankings.py` passes with ≥ 80% coverage on `app/utils/rankings.py`
- [ ] `ruff check app/pages/war_room.py app/utils/rankings.py tests/test_rankings.py` — zero errors
- [ ] All files under 500 lines

---

## Context

### Related Documentation
- `docs/PLANNING.md` — Architecture overview, data model, Phase 1b definition
- `docs/DECISIONS.md` — ADR-001 (Streamlit, no drag-and-drop), ADR-002 (JSON persistence), ADR-003 (CSV data source), ADR-005 (rankings-only app)
- `docs/TESTING.md` — Testing pyramid and manual checklist

### Dependencies
- **Required**: Phase 1a complete (✅) — `data_loader.py`, `constants.py`, app skeleton
- **Optional**: None

### Files to Modify/Create
```
app/utils/rankings.py          # MODIFY: seed logic, CRUD, swap, add, delete
app/pages/war_room.py          # MODIFY: full War Room implementation
app/main.py                    # MODIFY: session state init, sidebar nav update
tests/test_rankings.py         # NEW: comprehensive unit tests
```

---

## Technical Specification

### Data Model

**Player dict** (inside profile JSON):
```python
{
    "position_rank": 1,
    "name": "Josh Allen",
    "team": "BUF",
    "position": "QB",
    "tier": 1,
    "notes": ""
}
```

**Rankings profile** (`data/rankings/default.json`):
```python
{
    "name": "2026 Draft",
    "created": "2026-03-30T00:00:00",
    "modified": "2026-03-30T00:00:00",
    "league": {"teams": 10, "scoring": "half_ppr"},
    "players": [...]  # flat list of player dicts
}
```

### Session State Keys
```python
st.session_state["rankings"]  # dict — full loaded profile
st.session_state["dirty"]     # bool — True if unsaved changes exist
```

Both initialized in `main.py` only.

### Constants (in `rankings.py`)

```python
SEED_LIMITS = {"QB": 30, "RB": 50, "WR": 50, "TE": 30}

TIER_BREAKPOINTS = {
    "QB": [(3,1), (6,2), (10,3), (14,4), (18,5), (24,6), (30,7)],
    "RB": [(4,1), (8,2), (12,3), (16,4), (24,5), (32,6), (42,7), (50,8)],
    "WR": [(4,1), (8,2), (16,3), (24,4), (36,5), (50,6)],
    "TE": [(3,1), (6,2), (10,3), (14,4), (18,5), (24,6), (30,7)],
}
```

### Utility Functions (`app/utils/rankings.py`)

```python
def seed_rankings(df: pd.DataFrame) -> dict:
    """Create initial rankings profile from 2025 data."""

def load_or_seed(df: pd.DataFrame) -> dict:
    """Load existing profile or seed from CSV data."""

def save_rankings(profile: dict) -> bool:
    """Write profile to data/rankings/default.json. Returns success bool."""

def get_position_players(profile: dict, position: str) -> list[dict]:
    """Return players for a position sorted by position_rank."""

def swap_players(profile: dict, position: str, rank_a: int, rank_b: int) -> dict:
    """Swap two adjacent players. Auto-reassign tier on boundary crossing."""

def add_player(profile: dict, name: str, team: str, position: str, tier: int) -> dict:
    """Add player at end of specified tier. Renumber subsequent ranks."""

def delete_player(profile: dict, position: str, position_rank: int) -> dict:
    """Remove player and renumber remaining ranks."""
```

### Page Layout (`app/pages/war_room.py`)

```
Header row: st.title("🏈 WAR ROOM") | unsaved indicator | SAVE button
Four columns: st.columns([1, 1, 1, 1])
Each column:
  - Position header + player count
  - For each tier:
    - Tier divider: "── TIER N ──"
    - Player rows: ▲ | ▼ | rank | name button | team | [x]
    - [+ Position · Tier N] add button
```

### Dialogs (in `war_room.py`)

```python
@st.dialog("📋 Notes")
def notes_dialog(player: dict, idx: int) -> None: ...

@st.dialog("Add Player")
def add_player_dialog(position: str, tier: int) -> None: ...

@st.dialog("Delete Player")
def delete_confirm_dialog(player: dict, position: str, rank: int) -> None: ...
```

---

## Implementation Steps

### Step 1: Rankings Utility — Core Functions
**Files**: `app/utils/rankings.py`

Implement the full `rankings.py` module with all functions specified in the init:

1. Add imports: `from __future__ import annotations`, `json`, `copy`, `datetime`, `pathlib`, `pandas`
2. Define `SEED_LIMITS` and `TIER_BREAKPOINTS` constants
3. Define `RANKINGS_DIR` using `pathlib.Path`
4. Implement `_assign_tier(position: str, rank: int) -> int` — helper that maps rank to tier using `TIER_BREAKPOINTS`
5. Implement `seed_rankings(df)` — filter to 2025, sort by `total_pts` desc, take top N per position, assign `position_rank`, `tier`, `notes`
6. Implement `load_or_seed(df)` — check for `default.json`, load or seed+save
7. Implement `save_rankings(profile)` — write JSON with updated `modified` timestamp
8. Implement `get_position_players(profile, position)` — filter + sort
9. Implement `swap_players(profile, position, rank_a, rank_b)` — deep copy, swap, tier reassign, renumber
10. Implement `add_player(profile, name, team, position, tier)` — deep copy, insert at end of tier, renumber
11. Implement `delete_player(profile, position, position_rank)` — deep copy, remove, renumber

Key rules:
- All mutating functions return new profile (deep copy), never mutate input
- `save_rankings` catches `IOError` and returns `False`
- `load_or_seed` catches `json.JSONDecodeError` and re-seeds
- Use `from __future__ import annotations` for Python 3.9 compatibility

**Validation**:
```bash
ruff check app/utils/rankings.py
```
- [ ] No lint errors
- [ ] File under 500 lines

---

### Step 2: Rankings Unit Tests
**Files**: `tests/test_rankings.py`

Create comprehensive test file with all tests from the init spec. Use `tmp_path` for file I/O tests. Patch `streamlit.warning`/`streamlit.error`/`streamlit.cache_data` as done in `test_data_loader.py`.

**Test groups** (27 tests total):

**Seeding (8 tests)**:
- `test_seed_all_positions` — QB 30, RB 50, WR 50, TE 30
- `test_seed_respects_depth_limits` — never exceeds SEED_LIMITS
- `test_seed_sorted_by_total_pts` — descending within each position
- `test_seed_position_rank_sequential` — 1..N, no gaps
- `test_seed_has_tier` — all players have `tier` as int ≥ 1
- `test_seed_tier_nondecreasing` — within a position, tiers don't decrease
- `test_seed_uses_2025_only` — all from year == 2025 input data
- `test_seed_notes_empty` — all `notes == ""`

**Persistence (5 tests)**:
- `test_load_or_seed_creates_file` — no JSON → file created
- `test_load_or_seed_loads_existing` — existing JSON → returns it
- `test_save_writes_valid_json` — output is valid JSON with `players` key
- `test_save_updates_modified_timestamp` — `modified` changes
- `test_save_returns_false_on_bad_path` — unwriteable → `False`

**Reordering (6 tests)**:
- `test_swap_exchanges_ranks` — rank 2 ↔ 3 swap
- `test_swap_same_tier_no_tier_change` — within-tier swap preserves tiers
- `test_swap_cross_boundary_up` — ▲ into lower tier → inherits tier
- `test_swap_cross_boundary_down` — ▼ into higher tier → inherits tier
- `test_swap_ranks_sequential_after` — 1..N after any swap
- `test_swap_does_not_mutate_input` — original unchanged

**Add player (4 tests)**:
- `test_add_player_appended_to_tier` — appears after last in tier
- `test_add_player_rank_assigned` — correct position_rank
- `test_add_player_subsequent_ranks_shifted` — renumbered
- `test_add_player_does_not_mutate_input` — original unchanged

**Delete player (3 tests)**:
- `test_delete_removes_player` — no longer in list
- `test_delete_renumbers_ranks` — no gaps
- `test_delete_does_not_mutate_input` — original unchanged

**Helper (1 test)**:
- `test_get_position_players_sorted` — correct position, sorted

**Fixtures**:
- `sample_df` — multi-position DataFrame with enough rows for meaningful seeding tests
- `sample_profile` — pre-built profile dict for swap/add/delete tests

**Validation**:
```bash
pytest tests/test_rankings.py -v
```
- [ ] All tests pass
- [ ] ≥ 80% coverage on `app/utils/rankings.py`

---

### Step 3: Update `main.py` — Session State & Sidebar
**Files**: `app/main.py`

1. Add session state initialization:
   ```python
   if "rankings" not in st.session_state:
       df = load_all_players()
       st.session_state.rankings = load_or_seed(df)
   if "dirty" not in st.session_state:
       st.session_state.dirty = False
   ```
2. Update sidebar navigation:
   - Remove History and Analysis from the radio options
   - Keep: `War Room` and `Live Draft (Phase 2)` (with Phase 2 greyed/disabled)
3. Update page routing dict to match
4. Import `load_or_seed` from `utils.rankings`
5. Keep sidebar footer: `"✓ {n} player-seasons loaded"`

**Validation**:
```bash
ruff check app/main.py
streamlit run app/main.py  # verify sidebar shows only War Room + Live Draft
```
- [ ] No lint errors
- [ ] App starts without errors

---

### Step 4: War Room Page — Column Rendering
**Files**: `app/pages/war_room.py`

Build the main War Room page layout:

1. Add imports: `from __future__ import annotations`, `streamlit`, `utils.rankings`
2. Header row: title + unsaved indicator + SAVE button
   - Unsaved indicator: `"● Unsaved"` styled in `#0076B6` when `dirty == True`
   - SAVE button: calls `save_rankings()`, sets `dirty = False`, shows `st.toast("Rankings saved ✓")`
3. Four columns: `st.columns([1, 1, 1, 1])` for QB, RB, WR, TE
4. Per column:
   - Position header in caps + player count caption
   - Group players by tier (consecutive `tier` values)
   - Tier divider: `st.markdown("── TIER {n} ──")` in muted style
   - Player rows using `st.columns([1, 1, 1, 5, 2, 1])`:
     - `▲` button (disabled at rank 1)
     - `▼` button (disabled at last rank)
     - Rank (muted text)
     - Name button (opens notes dialog; shows `📝` suffix if notes exist)
     - Team (muted text)
     - `[x]` delete button (opens confirm dialog)
   - `[+ Position · Tier N]` add button at end of each tier group
5. Button callbacks: update `st.session_state.rankings` via utility functions, set `dirty = True`, `st.rerun()`

Key Streamlit patterns:
- Every button needs a unique `key` — use format `f"{action}_{position}_{rank}"`
- Dialog functions decorated with `@st.dialog()`
- No session state initialization in this file (done in `main.py`)

**Validation**:
```bash
ruff check app/pages/war_room.py
streamlit run app/main.py  # verify 4 columns render with players
```
- [ ] No lint errors
- [ ] File under 500 lines
- [ ] All 4 columns render with correct player counts

---

### Step 5: Dialogs — Notes, Add, Delete
**Files**: `app/pages/war_room.py` (or split to `app/components/dialogs.py` if war_room.py approaches 500 lines)

1. **Notes dialog** (`@st.dialog("📋 Notes")`):
   - Shows player name + team as subheader
   - `st.text_area` pre-filled with existing notes
   - Save button: updates notes in session state, sets dirty, reruns
   - Close button: reruns without saving

2. **Add player dialog** (`@st.dialog("Add Player")`):
   - Displays position + tier (pre-filled, read-only)
   - `st.text_input` for name (required)
   - `st.text_input` for team (2-3 chars, required)
   - Validation: name not empty, team not empty, no case-insensitive duplicate in position
   - Add button: calls `add_player()`, sets dirty, reruns
   - Cancel button: reruns

3. **Delete confirm dialog** (`@st.dialog("Delete Player")`):
   - Shows "Remove {name} ({team}) from {position} rankings?"
   - "This cannot be undone."
   - Delete button: calls `delete_player()`, sets dirty, reruns
   - Cancel button: reruns

**Validation**:
```bash
streamlit run app/main.py
# Test each dialog manually
```
- [ ] Notes dialog opens, saves, shows 📝 indicator
- [ ] Add dialog validates and adds player to correct tier
- [ ] Delete dialog removes player, ranks renumber

---

### Step 6: Final Integration Check
**Commands**:
```bash
pytest tests/ --cov=app --cov-report=term-missing
ruff check app/ tests/
streamlit run app/main.py
```

**Validation**:
- [ ] All tests pass, coverage ≥ 80% for `app/utils/rankings.py`
- [ ] Zero lint errors across all modified files
- [ ] Full manual test checklist completed (see Integration Test Plan below)
- [ ] No debug output (`st.write`, `print`) left in code
- [ ] All files under 500 lines
- [ ] Commit: `feat: add War Room rankings board with tiers, reordering, notes, and persistence`

---

## Testing Requirements

### Unit Tests (`tests/test_rankings.py`)
```
Seeding:
  test_seed_all_positions          — correct player counts per position
  test_seed_respects_depth_limits  — never exceeds SEED_LIMITS
  test_seed_sorted_by_total_pts   — descending order within position
  test_seed_position_rank_sequential — 1..N no gaps
  test_seed_has_tier               — tier is int ≥ 1
  test_seed_tier_nondecreasing     — tiers only increase within position
  test_seed_uses_2025_only         — only 2025 data used
  test_seed_notes_empty            — notes == "" for all

Persistence:
  test_load_or_seed_creates_file          — creates default.json
  test_load_or_seed_loads_existing        — loads without re-seeding
  test_save_writes_valid_json             — valid JSON output
  test_save_updates_modified_timestamp    — modified field changes
  test_save_returns_false_on_bad_path     — returns False on IOError

Reordering:
  test_swap_exchanges_ranks               — basic swap works
  test_swap_same_tier_no_tier_change      — tiers preserved in-tier
  test_swap_cross_boundary_up             — tier adopted on ▲ cross
  test_swap_cross_boundary_down           — tier adopted on ▼ cross
  test_swap_ranks_sequential_after        — 1..N after swap
  test_swap_does_not_mutate_input         — immutability

Add:
  test_add_player_appended_to_tier        — correct insertion point
  test_add_player_rank_assigned           — correct rank
  test_add_player_subsequent_ranks_shifted — renumbering
  test_add_player_does_not_mutate_input   — immutability

Delete:
  test_delete_removes_player              — removal works
  test_delete_renumbers_ranks             — no gaps
  test_delete_does_not_mutate_input       — immutability

Helper:
  test_get_position_players_sorted        — filter + sort correct
```

### Manual Streamlit Tests
See Integration Test Plan below.

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Delete `data/rankings/default.json` if exists, then `streamlit run app/main.py` | App starts, War Room renders with 4 columns. Auto-seeds rankings. `default.json` created on disk. | ☐ |
| 2 | Count players in each column | QB: 30, RB: 50, WR: 50, TE: 30 | ☐ |
| 3 | Verify tier dividers | Each column shows multiple "── TIER N ──" dividers | ☐ |
| 4 | Click ▲ on rank 2 QB | Player moves to rank 1, old rank 1 moves to rank 2. `● Unsaved` appears. | ☐ |
| 5 | Click ▼ on last-tier-boundary player | Player crosses tier boundary, tier number updates | ☐ |
| 6 | Verify ▲ disabled on rank 1 | Button is disabled / not clickable | ☐ |
| 7 | Verify ▼ disabled on last rank | Button is disabled / not clickable | ☐ |
| 8 | Click player name | Notes dialog opens with player name + team in header | ☐ |
| 9 | Type notes, click Save | Dialog closes, `📝` appears next to name, `● Unsaved` shown | ☐ |
| 10 | Click `[+ QB · Tier 1]` | Add player dialog opens with position=QB, tier=1 pre-filled | ☐ |
| 11 | Add player with name + team | Player appears at end of Tier 1, ranks renumber | ☐ |
| 12 | Try adding duplicate name | Validation error: "Already in QB rankings" | ☐ |
| 13 | Try adding with empty name | Validation error: "Name and team are required" | ☐ |
| 14 | Click `[x]` on a player | Confirm dialog: "Remove {name}...?" | ☐ |
| 15 | Confirm delete | Player removed, ranks renumber, `● Unsaved` shown | ☐ |
| 16 | Click SAVE | Toast "Rankings saved ✓", `● Unsaved` disappears | ☐ |
| 17 | Refresh browser (F5) | Rankings persist — same players, same order, notes retained | ☐ |
| 18 | Sidebar shows only War Room + Live Draft | History and Analysis removed from nav | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| `default.json` missing | First launch | Auto-seed from 2025 data, save, continue |
| `default.json` corrupted JSON | Manual edit or disk error | `st.warning("Rankings corrupted — re-seeding.")`, re-seed |
| No 2025 data in CSVs | Missing CSV files | `st.error("No 2025 data. Check data/players/ CSV files.")` |
| Save fails (IOError) | Permissions or disk full | `st.error("Save failed: {reason}")`, `dirty` stays `True` |
| Empty position in profile | All players deleted | `st.info("No {position} players in rankings.")` in column |
| Duplicate player add | Name already exists in position | Validation error in dialog: `"Already in {position} rankings"` |
| Empty name/team in add | User submits blank fields | Validation error: `"Name and team are required"` |

---

## Open Questions

None — all resolved in the init spec.

---

## Rollback Plan

1. `git revert <commit>` — revert the War Room commit
2. `streamlit run app/main.py` — verify app starts with stub War Room
3. Delete `data/rankings/default.json` if created during testing

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Init spec is exhaustive — data model, functions, layouts, tests, error handling all specified |
| Feasibility | 9 | Standard Streamlit patterns, no exotic requirements. Minor risk: column layout with many buttons may need tuning for visual fit |
| Completeness | 9 | All files, functions, tests, session state, and error cases covered. Only gap: exact CSS styling for tier dividers may need iteration |
| Alignment | 10 | Fully consistent with ADR-001 (Streamlit, ▲▼ not drag-and-drop), ADR-002 (JSON), ADR-003 (CSV seed), ADR-005 (rankings-only) |
| **Average** | **9.5** | |

---

## Notes

- **File size awareness**: `war_room.py` with 4-column rendering + 3 dialogs may approach 500 lines. If it does, extract dialogs to `app/components/dialogs.py`.
- **Import convention**: All imports must be relative to `app/` (e.g., `from utils.rankings import ...`), never `from app.utils.rankings import ...`.
- **Python 3.9 compatibility**: Use `from __future__ import annotations` in every new file that uses type hints.
- **PLANNING.md data model divergence**: The init spec drops `overall_rank` from the player dict (per resolved open question #1). The PLANNING.md still references it — this is expected; PLANNING.md describes the original design, the init spec is authoritative.
- **Sidebar nav update**: History and Analysis pages remain as stubs but are removed from sidebar navigation per ADR-005 and init spec §11.
