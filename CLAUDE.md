# CLAUDE.md - Claude Code Instructions

This file provides project-specific instructions and conventions for Claude Code.

## Project Overview

**FF Draft Room**: A local Python/Streamlit fantasy football draft preparation and live draft tracking tool.  
Runs locally on MacBook Air M1. No cloud, no auth, no external APIs required.

**Tech Stack**: Streamlit | Python 3.11+ | Pandas | Plotly | JSON (local persistence)

## Quick Commands

```bash
# Start the app
cd ff-draft-room && streamlit run app/main.py

# Run tests
cd ff-draft-room && pytest tests/ --cov=app --cov-report=term-missing

# Install dependencies
pip install -r requirements.txt

# Lint
cd ff-draft-room && ruff check app/ tests/
```

## File Structure

```
ff-draft-room/
├── CLAUDE.md                    # This file
├── README.md                    # Project readme
├── requirements.txt             # Python dependencies
├── .gitignore
├── docs/
│   ├── PLANNING.md              # Architecture overview
│   ├── TASK.md                  # Current tasks
│   ├── DECISIONS.md             # ADRs
│   └── TESTING.md               # Testing standards
├── initials/                    # Feature specifications (init-*.md)
├── prps/                        # Implementation plans (prp-*.md)
│   └── templates/
│       └── prp-template.md
├── .claude/
│   └── commands/
│       ├── generate-prp.md
│       └── execute-prp.md
├── data/
│   ├── players/                 # Source CSV files (FantasyPros exports)
│   │   ├── QB_2020.csv ... QB_2025.csv
│   │   ├── RB_2020.csv ... RB_2025.csv
│   │   ├── WR_2020.csv ... WR_2025.csv
│   │   └── TE_2020.csv ... TE_2025.csv
│   └── rankings/                # Saved ranking profiles (JSON)
│       └── *.json
├── app/
│   ├── main.py                  # Streamlit entry point + navigation
│   ├── pages/
│   │   ├── war_room.py          # War Room: rankings editor + tier builder
│   │   ├── history.py           # Historical stats browser
│   │   ├── analysis.py          # VOR + positional analysis
│   │   └── live_draft.py        # Live draft tracker (Phase 2)
│   ├── components/
│   │   ├── player_table.py      # Reusable sortable player table
│   │   ├── tier_editor.py       # Tier assignment UI
│   │   └── vor_chart.py         # VOR visualization
│   └── utils/
│       ├── data_loader.py       # CSV parsing + data normalization
│       ├── rankings.py          # Rankings save/load/manage
│       ├── vor.py               # VOR calculation logic
│       └── constants.py         # Positions, scoring, tier defaults
└── tests/
    ├── test_data_loader.py
    ├── test_rankings.py
    └── test_vor.py
```

## Critical Rules

### 1. File Size Limit
- **Maximum 500 lines per file**
- When approaching limit: split into modules
- Prefer many small files over few large files

### 2. Commit Strategy
- **Commit after every feature** — atomic, working commits
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Each commit should leave the app runnable

### 3. Testing Requirements
- **Unit test coverage**: 80% minimum for `utils/`
- Run tests before committing
- Manual Streamlit testing after each page feature

### 4. Documentation
- Update `docs/TASK.md` when starting/completing tasks
- Create ADR in `docs/DECISIONS.md` for architectural choices
- Add learnings when debugging issues

## Coding Conventions

### Python (Streamlit + Pandas)

```python
# Type hints everywhere
def load_players(position: str, year: int) -> pd.DataFrame:
    """Load and normalize player data for a given position and year."""
    pass

# Use dataclasses for structured data
@dataclass
class PlayerRanking:
    rank: int
    name: str
    team: str
    position: str
    year: int
    gp: int
    ppg: float
    total_pts: float
    tier: int = 1
    notes: str = ""

# Streamlit session state pattern
if "rankings" not in st.session_state:
    st.session_state.rankings = load_default_rankings()

# Pandas — explicit dtypes, no silent coercions
df = pd.read_csv(path, dtype={"GP": int, "AVG": float, "TTL": float})
```

### Streamlit Conventions

```python
# Page config always first in main.py
st.set_page_config(
    page_title="FF Draft Room",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Use columns for layout, not nested expanders
col1, col2, col3 = st.columns([2, 1, 1])

# Cache data loading — never reload CSVs on every rerun
@st.cache_data
def load_all_players() -> pd.DataFrame:
    ...

# Sidebar for navigation and filters
with st.sidebar:
    page = st.radio("Navigation", ["War Room", "History", "Analysis"])
```

### Data Handling

```python
# All player data normalized to this schema after loading:
# columns: rank, name, team, position, year, gp, ppg, total_pts
# tier and notes added by user in War Room

# Positions: "QB", "RB", "WR", "TE"
# Years: 2020, 2021, 2022, 2023, 2024, 2025

# Rankings profiles saved as JSON:
# { "name": str, "created": ISO, "modified": ISO, "players": [...] }
```

## Error Handling Patterns

```python
# Data loading — graceful degradation
try:
    df = pd.read_csv(path)
except FileNotFoundError:
    st.warning(f"Data file not found: {path}")
    return pd.DataFrame()

# Rankings save/load
try:
    with open(profile_path, "r") as f:
        profile = json.load(f)
except (json.JSONDecodeError, KeyError) as e:
    st.error(f"Could not load ranking profile: {e}")
    return None
```

## Streamlit Dark Theme

The app uses a custom dark theme defined in `.streamlit/config.toml`:
```toml
[theme]
base = "dark"
primaryColor = "#00c8ff"
backgroundColor = "#050a12"
secondaryBackgroundColor = "#0a1520"
textColor = "#c8d8e8"
font = "monospace"
```

## PRP Workflow

### Generating PRPs
```bash
/generate-prp initials/init-{feature}.md
```

### Executing PRPs
```bash
/execute-prp prps/prp-{feature}.md
```

## Debugging Checklist

When something isn't working:

1. **Streamlit errors**: Check terminal output where `streamlit run` is running
2. **Data issues**: Use `st.dataframe(df.head())` to inspect mid-page
3. **Session state**: Use `st.write(st.session_state)` to debug state
4. **Cache issues**: Press `C` in browser or use `st.cache_data.clear()`
5. **Recent changes**: `git log --oneline -10`

## DO NOT

- Commit CSV data files with sensitive info
- Use `st.experimental_*` deprecated APIs
- Create files over 500 lines
- Contradict existing ADRs without discussion
- Use `time.sleep()` or blocking calls in Streamlit callbacks
- Hardcode file paths — use `pathlib.Path` relative to project root

## Reference Documents

- `docs/PLANNING.md` — Architecture and data models
- `docs/DECISIONS.md` — Past decisions to respect
- `docs/TASK.md` — Current work status
- `docs/TESTING.md` — Testing standards
