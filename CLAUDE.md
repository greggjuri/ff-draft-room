# FF Draft Room - Project Instructions

## What This Is

A personal fantasy football draft preparation tool.
Built for personal use on MacBook Air M1. Runs locally. No cloud, no auth, no external APIs.

**One purpose**: Build and manage pre-draft player rankings in a **War Room** board.
Historical FantasyPros data seeds the initial rankings baseline — it is infrastructure, not UI.

**Repository**: github.com/greggjuri/ff-draft-room
**Also mirrored to**: Gitea self-hosted (home lab)

## Tech Stack

### Backend
- **FastAPI** — REST API, runs at localhost:8000
- **Python 3.9+** — `from __future__ import annotations` required for union types
- **Pandas** — CSV processing
- **JSON files** — persistence (`data/rankings/`)
- **pytest + ruff** — testing and linting

### Frontend
- **React 18 + Vite** — runs at localhost:5173
- **Plain CSS** — full control, no CSS framework
- **fetch API** — HTTP calls to FastAPI backend

## Running the App

```bash
# Terminal 1 — Backend
source .venv/bin/activate
uvicorn backend.main:app --reload

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open `localhost:5173` in browser.

## Critical Constraints

1. **Local only** — no cloud, no auth, no external API calls at runtime
2. **File size limit: 500 lines** — split into modules when approaching
3. **Commit after every feature** — atomic, working commits
4. **Data source**: FantasyPros half-PPR CSV exports only — no approximations
5. **No Streamlit** — retired (ADR-006). Do not add Streamlit back.

## Python Import Convention

All backend imports are relative to `backend/`:

```python
# CORRECT
from utils.constants import POSITIONS
from utils.rankings import load_or_seed

# WRONG — breaks at runtime
from backend.utils.constants import POSITIONS
```

## What Is NOT in This App

- **No Streamlit** — retired due to UI limitations (ADR-006)
- **No history browser** — historical data is seed infrastructure only (ADR-005)
- **No database** — JSON files only (ADR-002)
- **No drag-and-drop** — Phase 2 consideration
- **No external API calls** — fully offline (ADR-003)

## Project Structure

```
ff-draft-room/
├── CLAUDE.md                    # This file
├── data/
│   ├── players/                 # FantasyPros CSVs (read-only)
│   └── rankings/                # JSON profiles (user data)
├── backend/
│   ├── main.py                  # FastAPI app + CORS
│   ├── routers/
│   │   └── rankings.py          # All /api/rankings/* routes
│   └── utils/                   # Core logic — DO NOT break these
│       ├── data_loader.py       ✅ tested
│       ├── rankings.py          ✅ tested
│       └── constants.py        ✅ tested
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── api/rankings.js      # All fetch() calls
│       └── components/
│           ├── WarRoom.jsx
│           ├── PositionColumn.jsx
│           ├── TierGroup.jsx
│           ├── PlayerRow.jsx
│           ├── NotesDialog.jsx
│           ├── AddPlayerDialog.jsx
│           └── DeleteConfirmDialog.jsx
└── tests/
    ├── test_data_loader.py      ✅ 8 passing
    ├── test_rankings.py         ✅ 27 passing
    └── test_vor.py              # Future
```

## API Routes

```
GET    /api/rankings
POST   /api/rankings/save
POST   /api/rankings/seed
GET    /api/rankings/{position}
POST   /api/rankings/{position}/reorder      { rank_a, rank_b }
POST   /api/rankings/{position}/add          { name, team, tier }
DELETE /api/rankings/{position}/{rank}
PUT    /api/rankings/{position}/{rank}/notes { notes }
```

## War Room UI Behaviour

- **4 columns**: QB | RB | WR | TE — all visible simultaneously
- **Tier groups**: players grouped with labeled dividers, alternating backgrounds
- **▲▼**: free reorder; crossing tier boundary auto-reassigns player's tier
- **Click player name**: notes dialog (pre-filled, Save/Close)
- **[+ Position · Tier N]**: add player dialog (name + team, placed at tier end)
- **[×]**: delete confirm dialog before removal
- **Save button**: manual save → POST /api/rankings/save
- **Unsaved indicator**: shown after any change, cleared on save
- **Player depth**: QB 30 / RB 50 / WR 50 / TE 30

## Design System

- **Background**: `#0D1B2A` (dark navy)
- **Primary accent**: `#0076B6` (Honolulu Blue — Detroit Lions)
- **Font**: monospace everywhere
- **Player name boxes**: `#1A3A5C` background, `#E8E8E8` text, hover `#0076B6`
- **Tier headers**: alternating `#132338` / `#1A4A6B`
- **Column dividers**: `1px solid #1E3A5F` with `gap="large"` equivalent spacing

## Key Project Files

Always check before starting work:
- `docs/PLANNING.md` — Architecture, API design, structure
- `docs/TASK.md` — Current sprint and status
- `docs/DECISIONS.md` — ADRs — never contradict without a new ADR

## Workflow: Claude.ai ↔ Claude Code

| Claude.ai | Claude Code |
|-----------|-------------|
| Architecture decisions | Write code |
| Create `initials/NN-init-*.md` | Run `/generate-prp` |
| Review PRPs | Run `/execute-prp` |
| Update docs | Git, tests, lint |

## Quick Reference

```bash
# Activate venv
source .venv/bin/activate

# Run backend
uvicorn backend.main:app --reload

# Run frontend
cd frontend && npm run dev

# Tests
pytest tests/ --cov=backend

# Lint
ruff check backend/ tests/

# Commit format
feat: / fix: / refactor: / docs: / test: / chore:
```

## Known Issues

- Python 3.9 on system — `Path | None` union syntax unsupported.
  Fixed with `from __future__ import annotations` at top of every backend file.
