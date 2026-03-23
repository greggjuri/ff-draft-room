# FF Draft Room - Project Planning

## Project Vision

A personal fantasy football draft tool that replaces scattered spreadsheets and third-party apps.  
Two modes: **War Room** for pre-draft preparation and **Live Draft** for real-time tracking.  
Runs locally on MacBook Air M1 via Streamlit. No cloud, no subscriptions, no ads.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (localhost:8501)                      │
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │  War Room   │  │  History    │  │  Analysis   │  │Live Draft │  │
│  │  (Phase 1)  │  │  (Phase 1)  │  │  (Phase 1)  │  │(Phase 2)  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         APP LAYER                                     │
│  app/utils/data_loader.py   — CSV parsing, normalization             │
│  app/utils/rankings.py      — Save/load/manage ranking profiles      │
│  app/utils/vor.py           — VOR calculation engine                 │
│  app/utils/constants.py     — Positions, tiers, scoring settings     │
└─────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   data/players/*.csv    │     │  data/rankings/*.json   │
│   (read-only source)    │     │  (user-editable state)  │
└─────────────────────────┘     └─────────────────────────┘
```

## Tech Stack

- **UI Framework**: Streamlit 1.35+
- **Language**: Python 3.11+
- **Data Processing**: Pandas 2.x
- **Charts**: Plotly Express
- **Persistence**: JSON (local filesystem)
- **Testing**: pytest + pytest-cov
- **Linting**: ruff
- **Platform**: macOS M1 (local only)

## Data Model

### Source Data (CSV — read only)
```
Columns from FantasyPros half-PPR export:
  #         → rank (int)
  Player    → name (str)
  Team      → team (str)
  Pos       → position (str)  [QB, RB, WR, TE]
  GP        → gp (int)
  AVG       → ppg (float)
  TTL       → total_pts (float)
  year      → year (int)      [added during load]
```

### Normalized DataFrame (in-memory)
```python
# All positions combined, all years
# dtypes enforced on load
df.columns = ["rank", "name", "team", "position", "year", "gp", "ppg", "total_pts"]
```

### Rankings Profile (JSON — user data)
```json
{
  "name": "2026 Draft - My Rankings",
  "created": "2026-03-22T00:00:00",
  "modified": "2026-03-22T00:00:00",
  "league": {
    "teams": 10,
    "scoring": "half_ppr",
    "roster": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DST", "BN", "BN", "BN", "BN", "BN", "BN"]
  },
  "players": [
    {
      "rank": 1,
      "name": "Christian McCaffrey",
      "team": "SF",
      "position": "RB",
      "tier": 1,
      "notes": "",
      "locked": false
    }
  ]
}
```

### VOR Model
```
replacement_levels = {
  "QB":  QB rank 13  (last starter in 10-team 1-QB league)
  "RB":  RB rank 25  (RB2 + flex consideration)
  "WR":  WR rank 35  (WR2 + flex consideration)
  "TE":  TE rank 13  (last starter)
}

VOR = player_projected_pts - replacement_level_pts
```

## Project Structure

```
ff-draft-room/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml              # Dark theme config
├── docs/
│   ├── PLANNING.md              # This file
│   ├── TASK.md
│   ├── DECISIONS.md
│   └── TESTING.md
├── initials/                    # init-*.md feature specs
├── prps/                        # prp-*.md implementation plans
│   └── templates/
│       └── prp-template.md
├── .claude/
│   └── commands/
│       ├── generate-prp.md
│       └── execute-prp.md
├── data/
│   ├── players/                 # FantasyPros CSV exports (source of truth)
│   └── rankings/                # User-saved ranking profiles (JSON)
├── app/
│   ├── main.py                  # Entry point, page config, sidebar nav
│   ├── pages/
│   │   ├── war_room.py          # Rankings editor + tier builder
│   │   ├── history.py           # Historical stats browser
│   │   ├── analysis.py          # VOR + positional depth charts
│   │   └── live_draft.py        # Live draft tracker (Phase 2)
│   ├── components/
│   │   ├── player_table.py      # Reusable interactive player table
│   │   ├── tier_editor.py       # Tier assignment interface
│   │   └── vor_chart.py         # VOR waterfall/bar visualization
│   └── utils/
│       ├── data_loader.py       # CSV → normalized DataFrame
│       ├── rankings.py          # Profile CRUD operations
│       ├── vor.py               # VOR engine
│       └── constants.py         # Config: positions, tiers, scoring
└── tests/
    ├── test_data_loader.py
    ├── test_rankings.py
    └── test_vor.py
```

## Development Phases

### Phase 1: War Room (current)

#### 1a — Foundation
- [ ] `init-project-setup.md` — Project scaffold, dependencies, Streamlit config, CSV loading
- [ ] `init-history-browser.md` — Historical stats page: all positions/years, sortable table, filters

#### 1b — Core War Room
- [ ] `init-war-room-rankings.md` — Rankings editor: reorder players, assign tiers, save profiles
- [ ] `init-vor-calculator.md` — VOR engine + analysis page with positional depth charts

#### 1c — Polish
- [ ] `init-rankings-profiles.md` — Multiple saved profiles, load/copy/delete, export to CSV

### Phase 2: Live Draft
- [ ] `init-live-draft-tracker.md` — Snake draft board, mark picks, best available
- [ ] `init-draft-roster-view.md` — My team view, positional needs, scarcity alerts

### Future
- Import ADP data from external source
- Mock draft simulator
- Trade evaluator

## Key Constraints

1. **Local only** — no cloud, no API keys, no network calls
2. **FantasyPros CSV format** — data loader must handle their export format exactly
3. **500-line file limit** — split into modules when approaching
4. **No external drag-and-drop libs** — use Streamlit-native reordering patterns
5. **macOS M1 compatible** — test all dependencies for arm64

## Success Criteria

1. [ ] App starts with `streamlit run app/main.py` — no errors
2. [ ] All 780 player records load correctly from CSVs
3. [ ] User can browse history by position/year and sort by any column
4. [ ] User can build and save a custom ranking profile
5. [ ] VOR scores calculated and visualized for all positions
6. [ ] Rankings profiles persist between sessions (JSON)
7. [ ] App feels fast — data loads cached, no lag on filter changes

## Non-Functional Requirements

### Performance
- Initial data load: < 2 seconds
- Page navigation: < 500ms
- Filter/sort operations: < 200ms (cached DataFrames)

### Reliability
- Graceful handling of missing CSV files
- Profile save failure shows error, doesn't crash
- All user state in `st.session_state` survives page navigation

### Usability
- Dark tactical theme throughout
- Mobile not required — desktop only
- Keyboard shortcuts where Streamlit allows
