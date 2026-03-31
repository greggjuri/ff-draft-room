# 02-init-history-browser.md — Historical Stats Browser

## Feature Summary
Build the History page: a browsable, sortable, searchable table of FantasyPros half-PPR
season data for all positions and years. Users select a year via dropdown, then explore
each position via tabs. Data is already loaded in `st.session_state.df` by `main.py`.

## Status
- [x] Open questions resolved
- [x] Ready for PRP generation

---

## Requirements

### 1. Page Entry Point
- File: `app/pages/history.py`
- Replace existing stub's `render()` with full implementation
- Called by `main.py` as `history.render()` — interface unchanged

### 2. Layout

**Top of page:**
- `st.title("📋 History")` + subtitle: `"FantasyPros Half-PPR Season Leaders, 2020–2025"`

**Controls row (single row, horizontal):**
- Year selectbox: label `"Season"`, options `[2025, 2024, 2023, 2022, 2021, 2020]` (descending), default `2025`
- Player name search: `st.text_input("Search player", placeholder="e.g. Justin Jefferson")`
- Controls laid out with `st.columns([1, 3])` — year selector narrow, search wider

**Position tabs:**
- `st.tabs(["QB", "RB", "WR", "TE"])`
- Each tab renders the filtered + searched table for that position
- Tabs share the year filter and search string — both apply across all tabs

### 3. Data Table

**Columns displayed** (in this order):
```
rank | name | team | year | gp | ppg | total_pts
```
`position` column excluded (implied by tab context).

**Column display labels** (rename for UI only — don't mutate session_state.df):
```python
DISPLAY_COLUMNS = {
    "rank":       "Rank",
    "name":       "Player",
    "team":       "Team",
    "year":       "Season",
    "gp":         "GP",
    "ppg":        "Avg Pts",
    "total_pts":  "Total Pts",
}
```

**Rendering:**
- Use `st.dataframe()` with `use_container_width=True`
- Default sort: `rank` ascending (matches FantasyPros ordering)
- `st.dataframe` built-in column sorting enabled (user can click headers)
- Hide the DataFrame index (use `hide_index=True`)

**Empty state:**
- If filtered DataFrame is empty: `st.info("No players found for {position} in {year}.")`
- If search returns no matches: `st.info("No players matching '{search_term}'.")`

### 4. Filtering Logic

Applied in this order:
1. Filter `st.session_state.df` by selected `year`
2. Filter by `position` (current tab)
3. If search string non-empty: filter where `name.str.contains(search_term, case=False, na=False)`
4. Drop `position` column for display
5. Rename columns using `DISPLAY_COLUMNS`

All filtering operates on a copy — never mutates `st.session_state.df`.

### 5. Record Count
Below the table in each tab:
```
"{n} players — {year} {position}"
```
e.g. `"50 players — 2025 WR"`

### 6. Performance
- Filtering is fast (< 200ms) since the full DataFrame is already cached in session state
- No additional `@st.cache_data` needed on this page — data is pre-loaded
- Do not reload CSVs on this page

---

## Success Criteria

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

## Test Requirements (`tests/test_history.py`)

Unit tests on the **filtering logic only** — extract filter logic into a pure helper
function so it's testable without Streamlit:

**Helper function** (in `app/pages/history.py`):
```python
def filter_players(
    df: pd.DataFrame,
    position: str,
    year: int,
    search: str = "",
) -> pd.DataFrame:
    """Filter and prepare player DataFrame for display."""
    ...
```

**Tests:**
- `test_filter_by_year`: only rows with matching year returned
- `test_filter_by_position`: only rows with matching position returned
- `test_filter_by_search_case_insensitive`: `"justin"` matches `"Justin Jefferson"`
- `test_filter_empty_search`: empty string returns all rows for position/year
- `test_filter_no_results`: non-matching search returns empty DataFrame
- `test_filter_does_not_mutate`: original DataFrame unchanged after filtering
- `test_display_columns`: returned DataFrame has correct 7 display columns in correct order
- `test_position_column_excluded`: `position` column not present in returned DataFrame

**Fixture:**
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

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `st.session_state.df` is empty (no CSVs loaded) | `st.warning("No data loaded. Check that CSV files are present in data/players/.")` — return early |
| Year has no data for a position | `st.info("No players found for {position} in {year}.")` |
| Search matches nothing | `st.info("No players matching '{search_term}'.")` |

---

## Open Questions

*All resolved.*

1. ~~Position selector style?~~ → `st.tabs(["QB", "RB", "WR", "TE"])`
2. ~~Year filter behavior?~~ → Single year selectbox, default 2025
3. ~~Columns to display?~~ → rank, name, team, year, gp, ppg, total_pts (no position)
4. ~~Sort default?~~ → rank ascending

---

## Out of Scope for This Init

- Sparklines or multi-year trend charts — Analysis page
- Player detail drill-down / click-to-expand — future
- Export to CSV button — Phase 1c
- Comparison mode (two players side by side) — future
