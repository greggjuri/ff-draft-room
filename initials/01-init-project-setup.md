# 01-init-project-setup.md — Project Scaffold & Foundation

## Feature Summary
Bootstrap the FF Draft Room application: dependencies, dark theme config, CSV data loading,
and a working Streamlit app skeleton with sidebar navigation. After this init, `streamlit run
app/main.py` starts cleanly, loads all 24 CSV files, and shows a multi-page shell.

## Status
- [ ] Open questions resolved
- [ ] Ready for PRP generation

---

## Requirements

### 1. Dependencies (`requirements.txt`)
Pin exact versions, arm64-compatible:
- `streamlit>=1.35.0`
- `pandas>=2.0.0`
- `plotly>=5.20.0`
- `pytest>=8.0.0`
- `pytest-cov>=5.0.0`
- `ruff>=0.4.0`

### 2. Streamlit Config (`.streamlit/config.toml`)
Dark tactical theme:
- Background: near-black (`#0E1117`)
- Primary color: green accent (`#00C805` — fantasy points green)
- Secondary background: dark card (`#1A1D23`)
- Text: off-white (`#E8E8E8`)
- Font: `sans serif`
- Wide layout, expanded sidebar by default

### 3. Directory Scaffold
Create all empty directories and `__init__.py` files:
```
app/
  __init__.py
  main.py
  pages/
    __init__.py
    war_room.py       ← stub
    history.py        ← stub
    analysis.py       ← stub
    live_draft.py     ← stub
  components/
    __init__.py
    player_table.py   ← stub
    tier_editor.py    ← stub
    vor_chart.py      ← stub
  utils/
    __init__.py
    data_loader.py    ← IMPLEMENT fully
    rankings.py       ← stub
    vor.py            ← stub
    constants.py      ← IMPLEMENT fully
assets/
  ff-logo.jpg         ← already present, do not modify
data/
  players/            ← CSVs land here (not created by scaffold)
  rankings/           ← empty, created by scaffold
tests/
  __init__.py
  test_data_loader.py ← IMPLEMENT fully
  test_rankings.py    ← stub
  test_vor.py         ← stub
```

### 4. `app/utils/constants.py`
Define all shared constants:
```python
POSITIONS = ["QB", "RB", "WR", "TE"]
YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

# FantasyPros CSV column mapping → normalized names
CSV_COLUMN_MAP = {
    "#": "rank",
    "Player": "name",
    "Team": "team",
    "Pos": "position",
    "GP": "gp",
    "AVG": "ppg",
    "TTL": "total_pts",
}

# VOR replacement level thresholds (ADR-004)
VOR_REPLACEMENT_LEVELS = {
    "QB": 13,
    "RB": 25,
    "WR": 35,
    "TE": 13,
}

# Expected player counts (soft validation, warn if off by >5)
EXPECTED_COUNTS = {
    "QB": 20,
    "RB": 40,
    "WR": 50,
    "TE": 20,
}
```

### 5. `app/utils/data_loader.py`
The critical loading layer. Must handle:

**`load_position_year(position, year) → pd.DataFrame`**
- Builds path: `data/players/{POSITION}_{YEAR}.csv`
- Uses `pathlib.Path` relative to project root: `Path(__file__).parent.parent.parent / "data" / "players"`
- Returns empty DataFrame with correct schema if file missing — logs `st.warning`
- Renames columns using `CSV_COLUMN_MAP`
- Adds `year` column (int)
- Enforces dtypes: rank→int, gp→int, ppg→float, total_pts→float
- Strips whitespace from `name` and `team` columns

**`load_all_players() → pd.DataFrame`**
- Decorated with `@st.cache_data`
- Loops all POSITIONS × YEARS (24 combinations)
- Concatenates into single DataFrame
- Returns combined df; never raises — missing files just produce empty slices
- Logs count of loaded records

**Schema of returned DataFrame:**
```
rank         int64
name         object (str)
team         object (str)
position     object (str)
year         int64
gp           int64
ppg          float64
total_pts    float64
```

### 6. `app/main.py`
Streamlit entry point:
- `st.set_page_config(layout="wide", page_title="FF Draft Room", page_icon="🏈")`
- Sidebar: logo from `assets/ff-logo.jpg` at width=200, with graceful fallback to text title if file missing
- Sidebar navigation: `st.radio` with `label_visibility="collapsed"` — options: War Room / History / Analysis / Live Draft
- Load all players once via `load_all_players()` → store in `st.session_state.df`
- Route to correct page module based on nav selection
- Show record count in sidebar footer: `"✓ {n} player-seasons loaded"`
- If 0 records loaded: show prominent warning with instructions to add CSV files

### 7. Page Stubs
Each stub (`war_room.py`, `history.py`, `analysis.py`, `live_draft.py`) renders:
```python
def render():
    st.title("Page Name")
    st.info("Coming soon — Phase X")
```
`main.py` calls `page_module.render()` — consistent interface.

### 8. Logo
- File: `assets/ff-logo.jpg` (already present — do not create or overwrite)
- Wire into sidebar: `st.image("assets/ff-logo.jpg", width=200)`
- Path resolved relative to project root using `pathlib.Path`
- If file missing for any reason: show text title `"🏈 FF Draft Room"` only — no crash

---

## Success Criteria

1. `pip install -r requirements.txt` completes without errors on macOS M1
2. `streamlit run app/main.py` starts at `localhost:8501` with no errors
3. Logo renders in sidebar from `assets/ff-logo.jpg`
4. Sidebar navigation renders 4 pages; clicking each shows stub
5. All 24 CSVs load (when present) into a single DataFrame with correct schema
6. Missing CSV file → `st.warning` shown, app continues (no crash)
7. Record count shown in sidebar footer
8. `pytest tests/test_data_loader.py` passes (see test requirements below)
9. `ruff check app/ tests/` — zero errors

---

## Test Requirements (`tests/test_data_loader.py`)

### Unit tests (no Streamlit, no `st.*` calls):
- `test_load_position_year_valid`: mock CSV file present → returns DataFrame with correct columns + dtypes
- `test_load_position_year_missing`: file not present → returns empty DataFrame with correct schema (no exception)
- `test_column_rename`: FantasyPros column names correctly mapped to normalized names
- `test_year_column_added`: `year` column present and correct int value
- `test_whitespace_stripped`: name/team with leading/trailing spaces are cleaned
- `test_dtype_enforcement`: rank and gp are int64, ppg and total_pts are float64

### Notes on testing `@st.cache_data`:
- Tests target `load_position_year` directly — the underlying function, not the cached wrapper
- `load_all_players` is integration-level; covered by manual smoke test, not unit tests

### Fixtures:
- Use `tmp_path` (pytest built-in) to create temp CSV files
- Create a `sample_qb_csv` fixture with 3 rows of valid FantasyPros-format data

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| CSV file missing | `st.warning(f"Missing: {filename}")`, return empty DataFrame |
| CSV has wrong columns | `st.error(f"Unexpected columns in {filename}: {cols}")`, return empty |
| CSV value can't cast to float | Coerce with `errors='coerce'`, fill NaN with 0.0 |
| 0 total records loaded | Sidebar warning + instructions block in main area |
| Logo file missing | Skip image, show `"🏈 FF Draft Room"` text title only |

---

## Open Questions

*All resolved — no blockers.*

1. ~~Logo file format and name?~~ → `assets/ff-logo.jpg`, already present
2. ~~Sidebar nav style?~~ → `st.radio` with `label_visibility="collapsed"`
3. ~~Session state init location?~~ → All in `main.py` (ADR-001 pattern)
4. ~~Path resolution strategy?~~ → `Path(__file__).parent.parent.parent / "data" / "players"`

---

## Out of Scope for This Init

- Actual page content (History, War Room, Analysis) — separate inits
- Rankings JSON read/write — separate init
- VOR calculation — separate init
- Any drag-and-drop or tier editing
