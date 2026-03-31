# FF Draft Room - Project Planning

## Project Vision

A personal fantasy football draft tool for building and managing pre-draft rankings.
One mode: **War Room** — a live rankings board where you reorder players, assign tiers,
add notes, and build your cheat sheet for the upcoming season.
Runs locally on MacBook Air M1. No cloud, no subscriptions, no ads.

Historical FantasyPros data (2020–2025) seeds the initial rankings baseline.
It is infrastructure, not UI.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              REACT FRONTEND (localhost:5173)             │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                   War Room                       │   │
│  │   QB | RB | WR | TE  (side-by-side columns)     │   │
│  │   Tier groups · ▲▼ reorder · notes dialog       │   │
│  │   Add player · Delete player · Save              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │ REST API
                          ▼
┌─────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (localhost:8000)            │
│                                                         │
│  backend/main.py              — FastAPI app + CORS      │
│  backend/routers/rankings.py  — API routes              │
│  backend/utils/               — Python logic layer      │
│    data_loader.py             — CSV parsing ✅ tested   │
│    rankings.py                — Profile CRUD ✅ tested  │
│    constants.py               — Config ✅ tested        │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────┐
│  data/players/*.csv │     │  data/rankings/*.json   │
│  (seed source only) │     │  (user rankings state)  │
└─────────────────────┘     └─────────────────────────┘
```

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.9+ (`from __future__ import annotations` for union types)
- **Data**: Pandas 2.x — CSV processing
- **Persistence**: JSON files (`data/rankings/`)
- **Testing**: pytest + pytest-cov
- **Linting**: ruff

### Frontend
- **Framework**: React 18
- **Build tool**: Vite
- **Language**: JavaScript (JSX)
- **Styling**: Plain CSS — full control, no framework
- **HTTP**: fetch API
- **Dev server**: localhost:5173 proxies /api/* to localhost:8000

### Platform
- macOS M1, runs fully locally
- Backend: `uvicorn backend.main:app --reload` → localhost:8000
- Frontend: `npm run dev` → localhost:5173

## API Design

### Rankings endpoints
```
GET    /api/rankings                          → load current profile
POST   /api/rankings/save                     → save current profile
POST   /api/rankings/seed                     → re-seed from CSV (reset)

GET    /api/rankings/{position}               → players for one position
POST   /api/rankings/{position}/reorder       → swap two players (▲▼)
POST   /api/rankings/{position}/add           → add a new player
DELETE /api/rankings/{position}/{rank}        → delete a player
PUT    /api/rankings/{position}/{rank}/notes  → update player notes
```

### Request/Response shapes
```json
// POST /api/rankings/{position}/reorder
{ "rank_a": 2, "rank_b": 3 }

// POST /api/rankings/{position}/add
{ "name": "Josh Allen", "team": "BUF", "tier": 1 }

// PUT /api/rankings/{position}/{rank}/notes
{ "notes": "Elite rushing upside" }

// All mutation responses return updated position player list
[{ "position_rank": 1, "name": "...", "team": "...", "tier": 1, "notes": "" }]
```

## Data Model

### Player (JSON)
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

### Rankings Profile (data/rankings/default.json)
```json
{
  "name": "2026 Draft",
  "created": "2026-03-30T00:00:00",
  "modified": "2026-03-30T00:00:00",
  "league": { "teams": 10, "scoring": "half_ppr" },
  "players": [ ... ]
}
```

### Seeding Limits
```
QB: top 30 · RB: top 50 · WR: top 50 · TE: top 30
```

## Project Structure

```
ff-draft-room/
├── CLAUDE.md
├── README.md
├── .gitignore
├── assets/
│   └── ff-logo.jpg
├── docs/
│   ├── PLANNING.md
│   ├── TASK.md
│   └── DECISIONS.md
├── initials/
├── prps/
├── data/
│   ├── players/             # FantasyPros CSVs (read-only)
│   └── rankings/            # JSON profiles (user data)
├── backend/
│   ├── main.py              # FastAPI app, CORS
│   ├── routers/
│   │   └── rankings.py      # /api/rankings/* routes
│   └── utils/               # Ported from app/utils/
│       ├── __init__.py
│       ├── data_loader.py   ✅
│       ├── rankings.py      ✅
│       └── constants.py     ✅
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       ├── api/
│       │   └── rankings.js       # All fetch() calls
│       └── components/
│           ├── WarRoom.jsx
│           ├── PositionColumn.jsx
│           ├── TierGroup.jsx
│           ├── PlayerRow.jsx
│           ├── NotesDialog.jsx
│           ├── AddPlayerDialog.jsx
│           └── DeleteConfirmDialog.jsx
└── tests/
    ├── test_data_loader.py  ✅ 8 passing
    ├── test_rankings.py     ✅ 27 passing
    └── test_vor.py          # Future
```

## Development Phases

### Phase 1: War Room

#### 1a — Foundation ✅ Complete
- [x] CSV loading + normalization (`data_loader.py`)
- [x] Rankings CRUD + seed logic (`rankings.py`)
- [x] 43 tests passing, 84% coverage on utils

#### 1b — Stack Migration (current focus)
- [ ] `04-init-fastapi-react-migration.md`
  - Retire Streamlit entirely
  - FastAPI backend wrapping existing utils
  - Vite + React frontend — full War Room UI
  - All features from Streamlit version, done properly

#### 1c — Polish (future)
- [ ] K and D/ST columns
- [ ] Multiple named profiles
- [ ] Export rankings to CSV

### Phase 2: Live Draft (future)
- [ ] Snake draft board, mark picks
- [ ] Best available board
- [ ] My roster view, scarcity alerts

## Key Constraints

1. **Local only** — no cloud, no auth, no external API calls at runtime
2. **File size limit: 500 lines max** — split into modules when approaching
3. **Commit after every feature** — atomic, working commits
4. **Data source**: FantasyPros half-PPR CSV exports only
5. **Python imports**: relative to `backend/` — `from utils.constants import ...`
6. **macOS M1**: Python 3.9+, `from __future__ import annotations`
