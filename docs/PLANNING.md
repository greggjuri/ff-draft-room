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
│  │   Save As · Load · Reset · Set Default           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │ REST API
                          ▼
┌─────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (localhost:8000)            │
│                                                         │
│  backend/main.py              — FastAPI app + CORS      │
│  backend/routers/rankings.py  — API routes (14 total)   │
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

### Rankings endpoints (13 total)
```
GET    /health                                → health check
GET    /api/rankings                          → load current profile
POST   /api/rankings/save                     → save current profile
POST   /api/rankings/seed                     → re-seed from CSV (nuclear)

GET    /api/rankings/profiles                 → list saved profiles
POST   /api/rankings/save-as                  → save as named profile
POST   /api/rankings/load                     → load a named profile
POST   /api/rankings/set-default              → set seed.json baseline
POST   /api/rankings/reset                    → reset to baseline or CSV

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

// POST /api/rankings/save-as
{ "name": "Mock Draft 1" }

// POST /api/rankings/load
{ "name": "Mock Draft 1" }
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

### Profile Storage
```
data/rankings/
  default.json       ← active working profile
  seed.json          ← custom reset baseline (optional)
  {name}.json        ← named snapshots via Save As
```

### Seeding Limits
```
QB: top 30 · RB: top 50 · WR: top 50 · TE: top 30
```

## Project Structure

```
ff-draft-room/
├── CLAUDE.md
├── .gitignore
├── requirements.txt
├── assets/
│   └── ff-logo.jpg
├── docs/
│   ├── PLANNING.md
│   ├── TASK.md
│   ├── DECISIONS.md
│   └── TESTING.md
├── initials/
├── prps/
├── data/
│   ├── players/             # FantasyPros CSVs (read-only)
│   └── rankings/            # JSON profiles (user data)
├── backend/
│   ├── main.py              # FastAPI app, CORS, sys.path
│   ├── routers/
│   │   └── rankings.py      # /api/rankings/* routes (13 endpoints)
│   └── utils/
│       ├── __init__.py
│       ├── data_loader.py   ✅ 8 tests
│       ├── rankings.py      ✅ 41 tests (27 core + 14 profile)
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
│       │   └── rankings.js       # All fetch() calls (11 functions)
│       └── components/
│           ├── WarRoom.jsx
│           ├── WarRoom.css
│           ├── PositionColumn.jsx
│           ├── PositionColumn.css
│           ├── TierGroup.jsx
│           ├── TierGroup.css
│           ├── PlayerRow.jsx
│           ├── PlayerRow.css
│           ├── NotesDialog.jsx
│           ├── AddPlayerDialog.jsx
│           ├── DeleteConfirmDialog.jsx
│           ├── SaveAsDialog.jsx
│           ├── LoadDialog.jsx
│           ├── ResetConfirmDialog.jsx
│           ├── SetDefaultConfirmDialog.jsx
│           ├── ExitDraftConfirmDialog.jsx
│           └── SearchBar.jsx
└── tests/
    ├── conftest.py              # sys.path → backend/
    ├── test_data_loader.py      ✅ 8 passing
    ├── test_rankings.py         ✅ 27 passing
    ├── test_profile_management.py ✅ 14 passing
    └── test_vor.py              # Future
```

## Development Phases

### Phase 1: War Room

#### 1a — Foundation ✅ Complete
- [x] CSV loading + normalization (`data_loader.py`)
- [x] Rankings CRUD + seed logic (`rankings.py`)
- [x] 43 tests passing, 84% coverage on utils

#### 1b — Stack Migration ✅ Complete
- [x] `04-init-fastapi-backend.md` — FastAPI backend, 13 endpoints
- [x] `05-init-react-frontend.md` — React frontend, 13 components
- [x] `06-init-profile-management.md` — Save As, Load, Reset, Set Default
- [x] `07-init-draft-mode.md` — Draft mode with status dot cycling
- [x] `08-init-search.md` — Global player search with scroll-to-highlight

#### 1c — Polish (next)
- [ ] K and D/ST columns
- [ ] Export rankings to CSV
- [ ] Rename/delete saved profiles

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
