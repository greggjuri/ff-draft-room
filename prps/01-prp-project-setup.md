# PRP: Project Scaffold & Foundation

## 1. Overview

**Problem**: FF Draft Room has no application code yet — only documentation, CSV data files, and project config. We need a working Streamlit skeleton that loads all 24 FantasyPros CSV files, normalizes them into a single DataFrame, and presents a multi-page shell with sidebar navigation.

**Solution**: Create the full directory scaffold (`app/`, `tests/`), implement `constants.py` and `data_loader.py` utilities, wire up `main.py` as the Streamlit entry point with sidebar nav + logo, create page stubs, and write comprehensive unit tests for the data loader.

**Init Spec**: `initials/01-init-project-setup.md`

---

## 2. Success Criteria

1. `pip install -r requirements.txt` completes without errors on macOS M1
2. `streamlit run app/main.py` starts at `localhost:8501` with no errors
3. Logo renders in sidebar from `assets/ff-logo.jpg`
4. Sidebar navigation shows 4 pages; clicking each shows its stub content
5. All 24 CSVs load into a single DataFrame with schema: `rank, name, team, position, year, gp, ppg, total_pts`
6. Missing CSV file → `st.warning`, app continues without crash
7. Record count displayed in sidebar footer
8. `pytest tests/test_data_loader.py` passes with ≥80% coverage on `app/utils/`
9. `ruff check app/ tests/` — zero errors

---

## 3. Context

### Relevant ADRs
- **ADR-001** (Streamlit): Use `@st.cache_data` for CSV loading, session state in `main.py`
- **ADR-002** (JSON persistence): `data/rankings/` directory created but not used yet
- **ADR-003** (FantasyPros CSV): Sole data source, no approximations, graceful missing-file handling

### Existing Files
- `data/players/QB_2020.csv` through `TE_2025.csv` — 24 CSV files present
- `assets/ff-logo.jpg` — logo file present
- `requirements.txt` — exists but may need updating

### CSV Format (observed)
```
"#","Player","Pos","Team","GP","1","2",...,"17"[,"18"],"AVG","TTL"
```
- Weekly columns (1–17 or 1–18) vary by year — must select columns by name, not position
- Values contain "BYE" and "-" in weekly columns (irrelevant — we only use AVG/TTL)
- All values are quoted strings — need type coercion

---

## 4. Technical Specification

### 4.1 Constants (`app/utils/constants.py`)

```python
POSITIONS: list[str] = ["QB", "RB", "WR", "TE"]
YEARS: list[int] = [2020, 2021, 2022, 2023, 2024, 2025]

CSV_COLUMN_MAP: dict[str, str] = {
    "#": "rank",
    "Player": "name",
    "Team": "team",
    "GP": "gp",
    "AVG": "ppg",
    "TTL": "total_pts",
}

VOR_REPLACEMENT_LEVELS: dict[str, int] = {
    "QB": 13, "RB": 25, "WR": 35, "TE": 13,
}

EXPECTED_COUNTS: dict[str, int] = {
    "QB": 20, "RB": 40, "WR": 50, "TE": 20,
}
```

### 4.2 Data Loader (`app/utils/data_loader.py`)

**`load_position_year(position: str, year: int, data_dir: Path | None = None) → pd.DataFrame`**
- Default `data_dir`: `Path(__file__).parent.parent.parent / "data" / "players"`
- Builds filename: `{position}_{year}.csv`
- On `FileNotFoundError`: return empty DataFrame with correct schema columns
- Select only columns present in `CSV_COLUMN_MAP` keys (ignore weekly columns)
- Rename via `CSV_COLUMN_MAP`
- Add `position` column from parameter (not CSV "Pos" column — ensures consistency)
- Add `year` column
- Coerce dtypes: `rank`→int, `gp`→int, `ppg`→float, `total_pts`→float (use `pd.to_numeric(errors='coerce')`, fill NaN with 0)
- Strip whitespace from `name` and `team`
- Validate: if expected columns missing after rename, log warning and return empty DataFrame

**`load_all_players() → pd.DataFrame`**
- Decorated with `@st.cache_data`
- Iterates `POSITIONS × YEARS` (24 combos)
- Calls `load_position_year` for each
- Concatenates results, resets index
- Never raises — missing files produce empty slices

### 4.3 Main App (`app/main.py`)

**Session State Keys:**
- `st.session_state.df` — combined DataFrame from `load_all_players()`

**Layout:**
- `st.set_page_config(layout="wide", page_title="FF Draft Room", page_icon="🏈", initial_sidebar_state="expanded")`
- Sidebar: logo (`assets/ff-logo.jpg`, width=200) with try/except fallback to text
- Sidebar: `st.radio("Navigation", [...], label_visibility="collapsed")`
- Sidebar footer: `"✓ {n} player-seasons loaded"`
- Main area: route to `page_module.render()` based on selection
- If 0 records: show `st.warning` with instructions

### 4.4 Page Stubs

Each page module exposes `render()`:
```python
def render():
    st.title("Page Name")
    st.info("Coming soon — Phase X")
```

Pages: `war_room.py` (Phase 1b), `history.py` (Phase 1a), `analysis.py` (Phase 1b), `live_draft.py` (Phase 2)

### 4.5 Streamlit Config (`.streamlit/config.toml`)

```toml
[theme]
base = "dark"
primaryColor = "#00C805"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1A1D23"
textColor = "#E8E8E8"
font = "sans serif"
```

---

## 5. Implementation Steps

### Step 1: Streamlit Config
- **Create** `.streamlit/config.toml` with dark theme settings from §4.5
- **Validate**: file exists, valid TOML

### Step 2: Update `requirements.txt`
- **Edit** `requirements.txt` with pinned minimums:
  - `streamlit>=1.35.0`, `pandas>=2.0.0`, `plotly>=5.20.0`
  - `pytest>=8.0.0`, `pytest-cov>=5.0.0`, `ruff>=0.4.0`
- **Validate**: `pip install -r requirements.txt` succeeds

### Step 3: Create Directory Scaffold
- **Create** directories + `__init__.py` files:
  - `app/__init__.py`
  - `app/pages/__init__.py`
  - `app/components/__init__.py`
  - `app/utils/__init__.py`
  - `tests/__init__.py`
  - `data/rankings/` (empty directory)
- **Validate**: all directories exist

### Step 4: Implement `app/utils/constants.py`
- **Create** file with all constants from §4.1
- **Validate**: `python -c "from app.utils.constants import POSITIONS, YEARS, CSV_COLUMN_MAP"`

### Step 5: Implement `app/utils/data_loader.py`
- **Create** file with `load_position_year()` and `load_all_players()` per §4.2
- Key implementation details:
  - Use `usecols` parameter in `pd.read_csv` to select only mapped columns (avoids weekly column issues)
  - Handle the "Pos" column: present in CSV but not in our map — just skip it
  - `data_dir` parameter enables testing with `tmp_path`
- **Validate**: `python -c "from app.utils.data_loader import load_position_year"`

### Step 6: Create Utility Stubs
- **Create** `app/utils/rankings.py` — empty module with docstring
- **Create** `app/utils/vor.py` — empty module with docstring
- **Validate**: importable

### Step 7: Create Page Stubs
- **Create** `app/pages/war_room.py` — `render()` with "Coming soon — Phase 1b"
- **Create** `app/pages/history.py` — `render()` with "Coming soon — Phase 1a"
- **Create** `app/pages/analysis.py` — `render()` with "Coming soon — Phase 1b"
- **Create** `app/pages/live_draft.py` — `render()` with "Coming soon — Phase 2"
- **Validate**: each importable, `render` callable

### Step 8: Create Component Stubs
- **Create** `app/components/player_table.py` — stub with docstring
- **Create** `app/components/tier_editor.py` — stub with docstring
- **Create** `app/components/vor_chart.py` — stub with docstring
- **Validate**: importable

### Step 9: Implement `app/main.py`
- **Create** file per §4.3
- Logo path resolved via `Path(__file__).parent.parent / "assets" / "ff-logo.jpg"`
- Import page modules, call `.render()` based on radio selection
- **Validate**: `streamlit run app/main.py` starts without errors

### Step 10: Implement `tests/test_data_loader.py`
- **Create** test file with fixtures and test cases:
  - `sample_qb_csv` fixture: 3-row CSV in FantasyPros format using `tmp_path`
  - `test_load_position_year_valid` — correct columns, dtypes, row count
  - `test_load_position_year_missing` — empty DataFrame with correct schema
  - `test_column_rename` — FantasyPros names → normalized names
  - `test_year_column_added` — year column present with correct int value
  - `test_whitespace_stripped` — leading/trailing spaces cleaned from name/team
  - `test_dtype_enforcement` — rank/gp are int64, ppg/total_pts are float64
- **Validate**: `pytest tests/test_data_loader.py -v` — all pass

### Step 11: Create Test Stubs
- **Create** `tests/test_rankings.py` — placeholder with skip marker
- **Create** `tests/test_vor.py` — placeholder with skip marker
- **Validate**: `pytest tests/ -v` — all pass (stubs skipped)

### Step 12: Lint Check
- **Run** `ruff check app/ tests/` — fix any errors
- **Validate**: zero errors

### Step 13: Manual Smoke Test
- **Run** `streamlit run app/main.py`
- **Verify**:
  - App starts, dark theme applied
  - Logo visible in sidebar
  - 4 nav options, each shows stub
  - Record count in sidebar footer (expect ~3000+ player-seasons)
  - No red error boxes

---

## 6. Testing Requirements

### Unit Tests (`tests/test_data_loader.py`)

| Test | Description | Key Assertion |
|------|-------------|---------------|
| `test_load_position_year_valid` | Load from valid CSV fixture | Returns DataFrame with 8 columns, correct row count |
| `test_load_position_year_missing` | Load from nonexistent path | Returns empty DataFrame, no exception |
| `test_column_rename` | FantasyPros → normalized names | Columns match `["rank", "name", "team", "position", "year", "gp", "ppg", "total_pts"]` |
| `test_year_column_added` | Year parameter becomes column | `df["year"].iloc[0] == 2024` |
| `test_whitespace_stripped` | `" Josh Allen "` → `"Josh Allen"` | No leading/trailing spaces |
| `test_dtype_enforcement` | String numerics → correct types | `rank`/`gp` are int64, `ppg`/`total_pts` are float64 |

### Fixture: `sample_qb_csv`
```python
@pytest.fixture
def sample_qb_csv(tmp_path):
    content = (
        '"#","Player","Pos","Team","GP","1","2","AVG","TTL"\n'
        '"1"," Josh Allen ","QB"," BUF ","16","28.2","34.5","25.3","405.1"\n'
        '"2","Lamar Jackson","QB","BAL","15","22.0","30.1","24.1","361.8"\n'
        '"3","Jalen Hurts","QB","PHI","17","18.5","25.3","21.0","357.0"\n'
    )
    csv_file = tmp_path / "QB_2024.csv"
    csv_file.write_text(content)
    return tmp_path
```

### Coverage Target
- `app/utils/constants.py`: 100% (all constants imported)
- `app/utils/data_loader.py`: ≥80% (all branches tested except `@st.cache_data` wrapper)

---

## 7. Integration Test Plan (Manual)

### Prerequisites
```bash
pip install -r requirements.txt
```

### Steps
1. **Start app**: `streamlit run app/main.py`
2. **Theme**: Verify dark background, green accent color
3. **Logo**: Verify `ff-logo.jpg` renders in sidebar at proper size
4. **Navigation**: Click each of the 4 nav options — verify stub content appears
5. **Data load**: Check sidebar footer shows record count > 0
6. **Missing file test**: Temporarily rename one CSV, restart app — verify warning appears, app doesn't crash
7. **Terminal**: Verify no Python tracebacks in terminal output

---

## 8. Error Handling

| Scenario | Location | Behavior |
|----------|----------|----------|
| CSV file missing | `data_loader.load_position_year` | Return empty DataFrame with correct schema, no exception |
| CSV has unexpected columns | `data_loader.load_position_year` | Select only known columns; if key columns missing, return empty DataFrame |
| CSV value can't cast to numeric | `data_loader.load_position_year` | `pd.to_numeric(errors='coerce')`, fill NaN with 0 |
| 0 total records loaded | `main.py` | Sidebar warning + main area instructions to add CSV files |
| Logo file missing | `main.py` | Show text title "🏈 FF Draft Room" instead |
| Import error in page module | `main.py` | Should not happen — stubs are minimal; if it does, Streamlit shows traceback |

---

## 9. Open Questions

**None** — all questions resolved in the init spec:
1. Logo: `assets/ff-logo.jpg` (present)
2. Nav style: `st.radio` with `label_visibility="collapsed"`
3. Session state: initialized in `main.py`
4. Path resolution: `Path(__file__).parent` relative chains

---

## 10. Rollback Plan

This is the initial scaffold — rollback is straightforward:

```bash
# Remove all created files/directories
git clean -fd app/ tests/ .streamlit/
git checkout -- requirements.txt

# Or if committed:
git log --oneline -5  # find commit hash
git revert <hash>
```

No existing functionality is modified — this is purely additive.

---

## Confidence Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Clarity** | 9/10 | Init spec is thorough with exact function signatures, column maps, and error handling |
| **Feasibility** | 10/10 | Standard Streamlit + Pandas patterns, no exotic dependencies, M1 compatible |
| **Completeness** | 9/10 | All files, tests, session state, and error cases covered |
| **Alignment** | 10/10 | Consistent with ADR-001 (Streamlit), ADR-002 (JSON dir created), ADR-003 (CSV only) |

**Average: 9.5/10** — Ready to execute.

---

## Files Created/Modified

| Action | Path | Description |
|--------|------|-------------|
| Create | `.streamlit/config.toml` | Dark theme configuration |
| Modify | `requirements.txt` | Pin dependency versions |
| Create | `app/__init__.py` | Package init |
| Create | `app/main.py` | Streamlit entry point |
| Create | `app/pages/__init__.py` | Package init |
| Create | `app/pages/war_room.py` | Page stub |
| Create | `app/pages/history.py` | Page stub |
| Create | `app/pages/analysis.py` | Page stub |
| Create | `app/pages/live_draft.py` | Page stub |
| Create | `app/components/__init__.py` | Package init |
| Create | `app/components/player_table.py` | Component stub |
| Create | `app/components/tier_editor.py` | Component stub |
| Create | `app/components/vor_chart.py` | Component stub |
| Create | `app/utils/__init__.py` | Package init |
| Create | `app/utils/constants.py` | Shared constants |
| Create | `app/utils/data_loader.py` | CSV loading + normalization |
| Create | `app/utils/rankings.py` | Utility stub |
| Create | `app/utils/vor.py` | Utility stub |
| Create | `tests/__init__.py` | Package init |
| Create | `tests/test_data_loader.py` | Data loader unit tests |
| Create | `tests/test_rankings.py` | Test stub |
| Create | `tests/test_vor.py` | Test stub |
| Create | `data/rankings/` | Empty directory for future profiles |
