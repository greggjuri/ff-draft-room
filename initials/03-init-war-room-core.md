# 03-init-war-room-core.md — War Room Rankings Board

## Feature Summary
Build the core War Room page: a side-by-side four-column board (QB | RB | WR | TE),
each column showing players grouped into tiers with visual dividers. Players can be
freely reordered with ▲▼ buttons; crossing a tier boundary auto-reassigns the player's
tier. Clicking a player name opens a notes dialog. Players can be added (manually, placed
at the end of a chosen tier) or deleted (with a confirm dialog). A manual Save button
persists rankings to JSON. On first launch, rankings are auto-seeded from 2025 total points.

This is the entire app — the primary and only active page.

## Status
- [x] Open questions resolved
- [x] Ready for PRP generation

---

## Requirements

### 1. Page Entry Point
- File: `app/pages/war_room.py`
- Replace existing stub's `render()` with full implementation
- Called by `main.py` as `war_room.render()`

### 2. Player Depth

Seeding and display limits per position:
```
QB: top 30 by 2025 total_pts
RB: top 50 by 2025 total_pts
WR: top 50 by 2025 total_pts
TE: top 30 by 2025 total_pts
```

These are seeding limits only — user can add players beyond these counts manually.

### 3. Data Model

**Player dict** (inside profile JSON):
```json
{
  "position_rank": 1,
  "name": "Josh Allen",
  "team": "BUF",
  "position": "QB",
  "tier": 1,
  "notes": ""
}
```

**Full rankings profile** (`data/rankings/default.json`):
```json
{
  "name": "2026 Draft",
  "created": "2026-03-30T00:00:00",
  "modified": "2026-03-30T00:00:00",
  "league": {
    "teams": 10,
    "scoring": "half_ppr"
  },
  "players": [ ... ]
}
```

**Session state keys** (initialized in `main.py`):
```python
st.session_state.rankings   # dict — loaded profile
st.session_state.dirty      # bool — True if unsaved changes exist
```

### 4. Seeding Logic (`app/utils/rankings.py`)

**`SEED_LIMITS`** constant:
```python
SEED_LIMITS = {"QB": 30, "RB": 50, "WR": 50, "TE": 30}
```

**`TIER_BREAKPOINTS`** constant:
```python
TIER_BREAKPOINTS = {
    "QB": [(3,1), (6,2), (10,3), (14,4), (18,5), (24,6), (30,7)],
    "RB": [(4,1), (8,2), (12,3), (16,4), (24,5), (32,6), (42,7), (50,8)],
    "WR": [(4,1), (8,2), (16,3), (24,4), (36,5), (50,6)],
    "TE": [(3,1), (6,2), (10,3), (14,4), (18,5), (24,6), (30,7)],
}
# Format: (max_rank_inclusive, tier_number)
# Players beyond last breakpoint rank get the last tier number
```

**`seed_rankings(df: pd.DataFrame) -> dict`**
- Filters `df` to `year == 2025`
- For each position in `["QB", "RB", "WR", "TE"]`:
  - Filter by position, sort by `total_pts` descending
  - Take top N using `SEED_LIMITS[position]`
  - Assign `position_rank` 1..N
  - Assign `tier` using `TIER_BREAKPOINTS`
  - `notes = ""`
- Returns full profile dict with metadata and flat `players` list

**`load_or_seed(df: pd.DataFrame) -> dict`**
- Checks if `data/rankings/default.json` exists
- If yes: load and return parsed JSON
- If no: call `seed_rankings(df)`, save to disk, return
- Handles corrupted JSON: `st.warning` + re-seed

**`save_rankings(profile: dict) -> bool`**
- Writes to `data/rankings/default.json`
- Updates `profile["modified"]` timestamp before writing
- Returns `True` on success, `False` on failure
- Never raises — catches `IOError`

**`get_position_players(profile: dict, position: str) -> list[dict]`**
- Returns players for a position sorted by `position_rank`

**`swap_players(profile: dict, position: str, rank_a: int, rank_b: int) -> dict`**
- Swaps two adjacent players by `position_rank` within a position
- Tier auto-reassign after swap:
  - Compare the moved player's new tier to their new neighbor's tier
    in the direction of movement (neighbor above if ▲, below if ▼)
  - If tiers differ, moved player adopts the neighbor's tier
- Renumbers `position_rank` 1..N (no gaps)
- Returns new profile dict — does not mutate input

**`add_player(profile: dict, name: str, team: str, position: str, tier: int) -> dict`**
- Appends new player at the end of the specified tier within the position list
  - Find the last player with matching `position` and `tier`
  - Insert new player immediately after that player
  - If no player with that tier exists: append at end of position list, assign next tier
- Assigns `position_rank` = (rank of last player in that tier) + 1
  then renumbers all subsequent players in the position (+1 each)
- New player: `{"position_rank": N, "name": name, "team": team,
  "position": position, "tier": tier, "notes": ""}`
- Returns new profile dict — does not mutate input

**`delete_player(profile: dict, position: str, position_rank: int) -> dict`**
- Removes player with matching `position` and `position_rank`
- Renumbers remaining players in position 1..N (no gaps)
- Returns new profile dict — does not mutate input

### 5. Page Layout

```
┌──────────────────────────────────────────────────────────────┐
│  🏈 WAR ROOM                         [● Unsaved]    [SAVE]  │
├──────────┬──────────────┬──────────────┬──────────────────── │
│    QB    │      RB      │      WR      │         TE          │
│ 30 plyrs │  50 plyrs    │   50 plyrs   │      30 plyrs       │
│          │              │              │                      │
│ ─ T1 ─── │  ─ T1 ───   │  ─ T1 ───   │  ─ T1 ───           │
│ ▲▼ 1 Allen BUF    [x]  │ ...          │  ...                 │
│ ▲▼ 2 Hurts PHI    [x]  │              │                      │
│  [+ add to T1]         │              │                      │
│          │              │              │                      │
│ ─ T2 ─── │  ─ T2 ───   │  ─ T2 ───   │  ─ T2 ───           │
│ ▲▼ 3 Murray ARI   [x]  │ ...          │  ...                 │
│  [+ add to T2]         │              │                      │
│ ...      │ ...          │ ...          │  ...                 │
└──────────┴──────────────┴──────────────┴────────────────────-┘
```

**Header** (above the 4 columns):
- Left: `st.title("🏈 WAR ROOM")`
- Right: unsaved indicator + SAVE button

**Unsaved indicator**:
- `dirty == True`: `"● Unsaved"` in Honolulu Blue (`#0076B6`) via `st.markdown`
- `dirty == False`: empty `st.empty()` placeholder — no layout shift

**Save button**: label `"SAVE"`, on click: save, `dirty = False`, `st.toast("Rankings saved ✓")`

**Four columns**: `st.columns([1, 1, 1, 1])`

### 6. Column Rendering (per position)

**Column header**:
- Position name in caps
- Player count caption: `"30 players"` (updates as players are added/deleted)

**Tier groups**:
- Group players by consecutive `tier` value
- For each tier group:
  1. Tier divider: `st.markdown("── TIER {n} ──")` in muted style
  2. Player rows (see below)
  3. Add-to-tier button at bottom of each group (see §7)

**Player row** layout via `st.columns([1, 1, 1, 5, 2, 1])`:
- `▲` — `key=f"up_{position}_{rank}"`, disabled if rank == 1
- `▼` — `key=f"dn_{position}_{rank}"`, disabled if rank == last
- Rank — plain muted text
- Name — `st.button(name, key=f"name_{position}_{rank}")` → opens notes dialog
- Team — plain muted text
- `[x]` — delete button, `key=f"del_{position}_{rank}"` → opens confirm dialog

**📝 indicator**: shown in name button label suffix if `player["notes"] != ""`
e.g. `"Josh Allen 📝"` vs `"Josh Allen"`

**On ▲/▼ click**: `swap_players()`, set dirty, `st.rerun()`
**On name click**: `notes_dialog(player, global_idx)`
**On [x] click**: `delete_confirm_dialog(player, position, rank)`

### 7. Add Player Button

At the bottom of each tier group, below the last player row:
```
[+ QB · Tier 1]
```
- Small, muted button: `key=f"add_{position}_t{tier}"`
- On click: opens `add_player_dialog(position, tier)`

**`add_player_dialog`** (`@st.dialog("Add Player")`):
```
Position: QB  |  Tier: 1          (pre-filled, display only)
Name:  [________________]         (text_input, required)
Team:  [____]                     (text_input, 2-3 chars, required)
       [Add]  [Cancel]
```
- Validates: name not empty, team not empty, name not already in that position
- On Add: `add_player()`, set dirty, `st.rerun()`
- On Cancel: `st.rerun()`
- Duplicate check: case-insensitive match on `name` within the same `position`

### 8. Delete Confirm Dialog

**`delete_confirm_dialog`** (`@st.dialog("Delete Player")`):
```
Remove {name} ({team}) from {position} rankings?
This cannot be undone.
        [Delete]   [Cancel]
```
- On Delete: `delete_player()`, set dirty, `st.rerun()`
- On Cancel: `st.rerun()`

### 9. Notes Dialog

**`notes_dialog`** (`@st.dialog("📋 Notes")`):
```python
st.subheader(f"{player['name']} · {player['team']}")
notes = st.text_area("", value=player["notes"], height=150,
                     placeholder="Add scouting notes...")
# [Save]  [Close]
```
- Save: update notes in session state, set dirty, `st.rerun()`
- Close: `st.rerun()` with no changes

### 10. Initialization in `main.py`

```python
if "rankings" not in st.session_state:
    df = load_all_players()
    st.session_state.rankings = load_or_seed(df)

if "dirty" not in st.session_state:
    st.session_state.dirty = False
```

### 11. Sidebar

- Logo (`assets/ff-logo.jpg`)
- Navigation: `War Room` · `Live Draft (Phase 2)` — greyed
- Footer: `"✓ {n} player-seasons loaded"`
- Remove History and Analysis from nav

---

## Success Criteria

1. `streamlit run app/main.py` → War Room renders, 4 columns visible
2. First launch: QB 30, RB 50, WR 50, TE 30 players seeded from 2025 data
3. Each column shows players grouped under tier dividers
4. ▲▼ reorders freely; ranks renumber immediately
5. Moving across a tier boundary updates the player's tier
6. ▲ disabled at rank 1; ▼ disabled at last rank
7. `[+ Position · Tier N]` button at bottom of each tier group
8. Add dialog: pre-filled position + tier, name + team inputs, duplicate validation
9. New player appears at end of the correct tier, dirty set
10. `[x]` on any row opens confirm dialog before deleting
11. After delete, ranks renumber with no gaps
12. Clicking player name opens notes dialog, notes pre-filled
13. Notes save updates `📝` suffix and sets dirty
14. `"● Unsaved"` appears after any change
15. SAVE writes JSON, clears dirty, shows toast
16. All state persists across page reloads
17. `pytest tests/test_rankings.py` passes
18. `ruff check app/pages/war_room.py app/utils/rankings.py tests/test_rankings.py` — zero errors

---

## Test Requirements (`tests/test_rankings.py`)

**Seeding:**
- `test_seed_all_positions`: QB 30, RB 50, WR 50, TE 30 players
- `test_seed_respects_depth_limits`: never exceeds `SEED_LIMITS` per position
- `test_seed_sorted_by_total_pts`: `total_pts` descending within each position
- `test_seed_position_rank_sequential`: `position_rank` is 1..N, no gaps
- `test_seed_has_tier`: all players have `tier` as int ≥ 1
- `test_seed_tier_nondecreasing`: tier values non-decreasing within a position
- `test_seed_uses_2025_only`: all players from year == 2025
- `test_seed_notes_empty`: all `notes == ""`

**Persistence:**
- `test_load_or_seed_creates_file`: no JSON → file created (use `tmp_path`)
- `test_load_or_seed_loads_existing`: JSON present → returns it, no re-seed
- `test_save_writes_valid_json`: saved file is valid JSON with `players` list
- `test_save_updates_modified_timestamp`: `modified` changes on each save
- `test_save_returns_false_on_bad_path`: unwriteable path → `False`, no exception

**Reordering:**
- `test_swap_exchanges_ranks`: swap rank 2 ↔ 3 → they exchange
- `test_swap_same_tier_no_tier_change`: swap within same tier → tiers unchanged
- `test_swap_cross_boundary_up`: move ▲ into lower tier → inherits that tier
- `test_swap_cross_boundary_down`: move ▼ into higher tier → inherits that tier
- `test_swap_ranks_sequential_after`: ranks still 1..N after any swap
- `test_swap_does_not_mutate_input`: original profile unchanged

**Add player:**
- `test_add_player_appended_to_tier`: new player appears after last player in tier
- `test_add_player_rank_assigned`: new player gets correct `position_rank`
- `test_add_player_subsequent_ranks_shifted`: players after insertion point renumbered
- `test_add_player_does_not_mutate_input`: original profile unchanged

**Delete player:**
- `test_delete_removes_player`: player no longer in list after delete
- `test_delete_renumbers_ranks`: no rank gaps after delete
- `test_delete_does_not_mutate_input`: original profile unchanged

**Helper:**
- `test_get_position_players_sorted`: correct position, sorted by `position_rank`

**Fixture:**
```python
@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "name":      ["Josh Allen", "Lamar Jackson", "Jalen Hurts", "Joe Burrow"],
        "team":      ["BUF", "BAL", "PHI", "CIN"],
        "position":  ["QB", "QB", "QB", "QB"],
        "year":      [2025, 2025, 2025, 2025],
        "rank":      [1, 2, 3, 4],
        "gp":        [16, 15, 16, 17],
        "ppg":       [25.3, 24.1, 21.0, 20.5],
        "total_pts": [405.1, 361.8, 336.0, 318.7],
    })
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `default.json` missing | Auto-seed, save, continue |
| `default.json` corrupted | `st.warning("Rankings corrupted — re-seeding.")`, re-seed |
| No 2025 data in CSVs | `st.error("No 2025 data. Check data/players/ CSV files.")` |
| Save fails | `st.error("Save failed: {reason}")`, dirty stays True |
| Empty position | `st.info("No {position} players in rankings.")` in column |
| Duplicate add | Validation error in add dialog: `"Already in {position} rankings"` |
| Add with empty name/team | Validation error: `"Name and team are required"` |

---

## Open Questions

*All resolved.*

1. ~~Overall rank?~~ → Dropped. Position rank only.
2. ~~Layout?~~ → 4 columns side by side
3. ~~Tiers?~~ → Visual dividers, tier auto-reassigns on boundary crossing
4. ~~Player depth?~~ → QB 30 / RB 50 / WR 50 / TE 30
5. ~~Add player?~~ → Manual (name + team), placed at end of chosen tier
6. ~~Delete?~~ → Confirm dialog first, then remove + renumber
7. ~~Save?~~ → Manual SAVE + `st.toast`
8. ~~Notes?~~ → `st.dialog` popup, Save/Close

---

## Out of Scope for This Init

- K (Kicker) and D/ST columns — `04-init-k-dst.md`
- Multiple named profiles — `05-init-rankings-profiles.md`
- Export to CSV — Phase 1c
- Manual tier boundary editing — future
- VOR calculations — future
- Live Draft — Phase 2
