# PRP: Historical Stats Browser

## 1. Overview

**Problem**: The History page is a stub. Users need to browse all 24 position-year combinations of FantasyPros data in a sortable, searchable table — the foundation for evaluating players before building rankings.

**Solution**: Replace the History stub with a full page: year dropdown + search box at top, position tabs below, each rendering a filtered `st.dataframe` with display-friendly column names. Extract filtering logic into a pure `filter_players()` function for testability.

**Init Spec**: `initials/02-init-history-browser.md`

---

## 2. Success Criteria

1. `streamlit run app/main.py` → navigate to History → page renders with no errors
2. Year selectbox defaults to 2025; changing year updates all tabs immediately
3. QB / RB / WR / TE tabs each show correct position data
4. Table columns: Rank, Player, Team, Season, GP, Avg Pts, Total Pts — in that order
5. Clicking a column header sorts the table
6. Typing in search box filters visible rows across all tabs
7. Empty state message shown when no results
8. Record count line shown below each tab's table
9. `pytest tests/test_history.py` passes
10. `ruff check app/pages/history.py tests/test_history.py` — zero errors

---

## 3. Context

### Relevant ADRs
- **ADR-001** (Streamlit): No additional caching needed — data pre-loaded in `st.session_state.df`
- **ADR-003** (FantasyPros CSV): Read-only display of loaded data, no mutations

### Existing Files to Reuse
- `app/main.py` — already loads data into `st.session_state.df` and routes to `history.render()`
- `app/utils/constants.py` — `POSITIONS`, `YEARS` for tab/dropdown values
- `app/pages/history.py` — stub to replace
- `tests/conftest.py` — adds `app/` to `sys.path`

### Data Shape (from `st.session_state.df`)
```
rank(int64) | name(str) | team(str) | position(str) | year(int64) | gp(int64) | ppg(float64) | total_pts(float64)
```

---

## 4. Technical Specification

### 4.1 Display Constants (`app/pages/history.py`)

```python
DISPLAY_COLUMNS = {
    "rank":      "Rank",
    "name":      "Player",
    "team":      "Team",
    "year":      "Season",
    "gp":        "GP",
    "ppg":       "Avg Pts",
    "total_pts": "Total Pts",
}
```

These are the 7 columns shown in the table — `position` is excluded since it's implied by the active tab.

### 4.2 Pure Filter Function (`app/pages/history.py`)

```python
def filter_players(
    df: pd.DataFrame,
    position: str,
    year: int,
    search: str = "",
) -> pd.DataFrame:
```

- Operates on a **copy** — never mutates input
- Filters by `year`, then `position`
- If `search` is non-empty: `name.str.contains(search, case=False, na=False)`
- Drops `position` column
- Renames columns via `DISPLAY_COLUMNS`
- Returns display-ready DataFrame

### 4.3 Page Layout (`render()`)

```
┌─────────────────────────────────────────────────┐
│ 📋 History                                       │
│ FantasyPros Half-PPR Season Leaders, 2020–2025   │
├──────────┬──────────────────────────────────────┤
│ Season ▼ │ Search player [________________]      │
├──────────┴──────────────────────────────────────┤
│ [QB] [RB] [WR] [TE]                             │
│ ┌──────────────────────────────────────────────┐│
│ │ Rank | Player | Team | Season | GP | Avg | T ││
│ │ 1    | Josh A | BUF  | 2025   | 16 |25.3|405││
│ │ ...                                          ││
│ └──────────────────────────────────────────────┘│
│ 32 players — 2025 QB                            │
└─────────────────────────────────────────────────┘
```

**Widgets:**
- `st.columns([1, 3])` — year selector narrow, search wider
- Year selectbox: `list(reversed(YEARS))` → `[2025, 2024, ..., 2020]`, default index 0
- Search: `st.text_input("Search player", placeholder="e.g. Justin Jefferson")`
- `st.tabs(POSITIONS)` — one tab per position

**Session State**: No new keys. Reads `st.session_state.df` only.

### 4.4 Error States

| Condition | Behavior |
|-----------|----------|
| `st.session_state.df` empty or missing | `st.warning(...)` + early return |
| No data for position/year combo | `st.info("No players found for {position} in {year}.")` |
| Search matches nothing | `st.info("No players matching '{search}'.")` |

---

## 5. Implementation Steps

### Step 1: Implement `filter_players()` in `app/pages/history.py`
- **Edit** `app/pages/history.py`
- Add imports: `pandas as pd`, `from utils.constants import POSITIONS, YEARS`
- Define `DISPLAY_COLUMNS` dict
- Implement `filter_players(df, position, year, search)` per §4.2
- Keep `render()` as stub for now
- **Validate**: `python3 -c "from pages.history import filter_players"` (with sys.path including app/)

### Step 2: Implement `render()` in `app/pages/history.py`
- **Edit** `app/pages/history.py`
- Replace stub `render()` with full layout per §4.3
- Read `st.session_state.df`, guard for empty
- Year selectbox + search input in columns
- Position tabs, each calling `filter_players()` and rendering `st.dataframe()`
- Record count caption below each table
- **Validate**: `streamlit run app/main.py` → History page renders

### Step 3: Implement `tests/test_history.py`
- **Create** `tests/test_history.py`
- Fixture: `sample_df` with 4 rows (2 QB, 2 WR, year 2024)
- 8 test cases per init spec §Test Requirements
- **Validate**: `pytest tests/test_history.py -v` — all pass

### Step 4: Lint + Full Test
- **Run**: `ruff check app/pages/history.py tests/test_history.py`
- **Run**: `pytest tests/ -v` — all tests pass (old + new)
- **Fix** any issues

### Step 5: Manual Smoke Test
- `streamlit run app/main.py`
- Navigate to History
- Verify: year dropdown, search, all 4 tabs, column sorting, empty states, record count

---

## 6. Testing Requirements

### Unit Tests (`tests/test_history.py`)

| Test | Description | Key Assertion |
|------|-------------|---------------|
| `test_filter_by_year` | Year filter returns only matching rows | All rows have `year == 2024` |
| `test_filter_by_position` | Position filter returns only matching rows | Only QB rows returned |
| `test_filter_by_search_case_insensitive` | `"justin"` matches `"Justin Jefferson"` | 1 row returned |
| `test_filter_empty_search` | Empty string returns all rows for position/year | Same count as unfiltered |
| `test_filter_no_results` | `"zzzzz"` returns empty DataFrame | `df.empty` is True |
| `test_filter_does_not_mutate` | Original DataFrame unchanged after filter | Compare pre/post copy |
| `test_display_columns` | Returned columns match DISPLAY_COLUMNS values | 7 columns in correct order |
| `test_position_column_excluded` | `position` not in output columns | `"position" not in df.columns` |

### Fixture: `sample_df`
```python
@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "rank":      [1, 2, 1, 2],
        "name":      ["Josh Allen", "Lamar Jackson", "Justin Jefferson", "Tyreek Hill"],
        "team":      ["BUF", "BAL", "MIN", "MIA"],
        "position":  ["QB", "QB", "WR", "WR"],
        "year":      [2024, 2024, 2024, 2024],
        "gp":        [16, 15, 17, 16],
        "ppg":       [25.3, 24.1, 22.5, 21.8],
        "total_pts": [405.1, 361.8, 382.5, 348.8],
    })
```

---

## 7. Integration Test Plan (Manual)

### Steps
1. `streamlit run app/main.py` — navigate to History
2. **Default state**: Year shows 2025, QB tab active, table populated
3. **Change year**: Select 2020 — table updates, record count changes
4. **Switch tabs**: Click RB, WR, TE — each shows correct data
5. **Search**: Type `"allen"` — only matching players shown across tabs
6. **Clear search**: Delete text — full tables restored
7. **Empty search**: Type `"zzzzz"` — info message appears
8. **Column sort**: Click "Total Pts" header — rows reorder
9. **Terminal**: No tracebacks

---

## 8. Error Handling

| Scenario | Location | Behavior |
|----------|----------|----------|
| `st.session_state.df` empty | `render()` | Warning message + early return |
| No data for position/year | Tab render | `st.info("No players found...")` |
| Search matches nothing | Tab render | `st.info("No players matching...")` |

No file I/O on this page — all error cases are data-level.

---

## 9. Open Questions

**None** — all resolved in the init spec.

---

## 10. Rollback Plan

```bash
# Revert history.py to stub and remove test file
git log --oneline -5
git revert <hash>
```

Only two files modified/created — low risk.

---

## Confidence Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Clarity** | 10/10 | Init spec defines exact layout, columns, filter order, and test cases |
| **Feasibility** | 10/10 | Standard Streamlit widgets (selectbox, tabs, dataframe), no exotic patterns |
| **Completeness** | 9/10 | All files, tests, error states covered; no session state changes needed |
| **Alignment** | 10/10 | Pure read-only display of pre-loaded data, consistent with all ADRs |

**Average: 9.75/10** — Ready to execute.

---

## Files Created/Modified

| Action | Path | Description |
|--------|------|-------------|
| Modify | `app/pages/history.py` | Full History page implementation |
| Create | `tests/test_history.py` | Unit tests for filter_players() |
