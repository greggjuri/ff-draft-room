# FF Draft Room - Project Planning

## Project Vision

A personal fantasy football draft tool for building and managing pre-draft rankings.
Two modes: **War Room** — a live rankings board where you reorder players, assign tiers,
add notes, and build your cheat sheet; and **Draft Mode** — mark players as drafted
during a live draft.

Runs locally on MacBook Air M1 for development. Deployed to AWS EC2 at
`ff.jurigregg.com` for access from any device on draft day.

Historical FantasyPros data (2020–2025) seeds the initial rankings baseline.
It is infrastructure, not UI.

## Architecture Overview

### Local Development
```
┌─────────────────────────────────────────────────────────┐
│              REACT FRONTEND (localhost:5173)             │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │           War Room + Draft Mode                  │   │
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
│  backend/middleware/auth.py   — Cognito JWT (prod only) │
│  backend/routers/rankings.py  — API routes (14 total)   │
│  backend/utils/               — Python logic layer      │
│    data_loader.py             — CSV parsing ✅ tested   │
│    rankings.py                — Profile CRUD ✅ tested  │
│    storage.py                 — StorageBackend ✅ tested│
│    constants.py               — Config ✅ tested        │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────┐
│  data/players/*.csv │     │  data/rankings/*.json   │
│  (seed source only) │     │  LocalStorage (dev)     │
└─────────────────────┘     └─────────────────────────┘
```

### Production (AWS)
```
Browser → https://ff.jurigregg.com
             │
             ▼
┌────────────────────────────────────────┐
│           nginx (EC2 t3.micro)         │
│  - SSL termination (certbot)           │
│  - Serves Vite dist/ (static)          │
│  - Proxies /api/* → uvicorn :8000      │
└────────────────────────────────────────┘
             │ /api/*
             ▼
┌────────────────────────────────────────┐
│        uvicorn (systemd service)       │
│        FastAPI + Cognito JWT auth      │
└────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│     S3: ff-draft-room-data             │
│     rankings/default.json             │
│     rankings/seed.json                │
│     rankings/{name}.json              │
└────────────────────────────────────────┘

Auth: AWS Cognito (ff-draft-room-users User Pool)
IAM:  EC2 instance role → S3 bucket access (no credentials in code)
```

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.9+ (`from __future__ import annotations` for union types)
- **Data**: Pandas 2.x — CSV processing
- **Persistence**: `StorageBackend` abstraction — `LocalStorage` (dev) / `S3Storage` (prod)
- **Auth**: Cognito JWT middleware (`python-jose[cryptography]`)
- **Testing**: pytest + pytest-cov + moto (S3 mocking)
- **Linting**: ruff

### Frontend
- **Framework**: React 18
- **Build tool**: Vite
- **Language**: JavaScript (JSX)
- **Styling**: Plain CSS — full control, no framework
- **HTTP**: fetch API with `Authorization: Bearer <token>` header
- **Auth**: `amazon-cognito-identity-js` — Cognito login in browser
- **Dev server**: localhost:5173 proxies /api/* to localhost:8000

### Infrastructure
- **EC2**: t3.micro, 24/7, nginx + systemd
- **S3**: `ff-draft-room-data` bucket — rankings JSON persistence
- **Cognito**: `ff-draft-room-users` User Pool — single user auth
- **CDK**: all infrastructure as code (`cdk/`)

### Environments

| | Local Dev | Production |
|---|---|---|
| Frontend | localhost:5173 (Vite dev server) | nginx static files |
| Backend | localhost:8000 (uvicorn --reload) | uvicorn via systemd |
| Storage | `LocalStorage` (`data/rankings/`) | `S3Storage` (`ff-draft-room-data`) |
| Auth | No enforcement | Cognito JWT required |
| Env var | `STORAGE_BACKEND=local` | `STORAGE_BACKEND=s3` |

## Storage Abstraction

`backend/utils/storage.py` — `StorageBackend` interface with two implementations:

```
StorageBackend (ABC)
  ├── LocalStorage    — reads/writes data/rankings/*.json (dev + all tests)
  └── S3Storage       — reads/writes S3 bucket (production)
```

Selected by `STORAGE_BACKEND` env var at startup. All 49+ tests run against
`LocalStorage` — zero AWS dependencies in test suite.

## API Design

### Rankings endpoints (14 total)
```
GET    /health                                → health check (unauthed)
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

All `/api/*` endpoints require Cognito JWT in production.
`/health` is always unauthenticated (used by deploy script).

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

### Rankings Profile
```json
{
  "name": "2026 Draft",
  "created": "2026-03-30T00:00:00",
  "modified": "2026-03-30T00:00:00",
  "league": { "teams": 10, "scoring": "half_ppr" },
  "players": [ ... ]
}
```

### Profile Storage Keys
```
default.json       ← active working profile
seed.json          ← custom reset baseline (optional)
{name}.json        ← named snapshots via Save As
```
In local dev these are files in `data/rankings/`.
In production these are S3 objects under `rankings/` prefix.

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
├── env.production.example       # Template — actual file lives on EC2 only
├── assets/
│   └── ff-logo.jpg
├── docs/
│   ├── PLANNING.md
│   ├── TASK.md
│   ├── DECISIONS.md
│   └── TESTING.md
├── initials/
├── prps/
├── cdk/
│   ├── app.py                   # CDK entry point
│   ├── ff_deploy_stack.py       # S3 + IAM + instance profile
│   ├── requirements.txt
│   └── cdk.json
├── scripts/
│   ├── deploy.sh                # EC2 deploy: pull, build, restart
│   ├── cdk-bootstrap.sh         # One-time infrastructure deploy
│   ├── nginx.conf.template
│   └── ff-draft-room.service    # systemd unit
├── data/
│   ├── players/                 # FantasyPros CSVs (read-only)
│   └── rankings/                # JSON profiles (local dev only)
├── backend/
│   ├── main.py                  # FastAPI app, CORS, storage init
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py              # Cognito JWT verification
│   ├── routers/
│   │   └── rankings.py          # /api/rankings/* routes (14 endpoints)
│   └── utils/
│       ├── __init__.py
│       ├── data_loader.py       ✅ 8 tests
│       ├── rankings.py          ✅ 27 tests — uses StorageBackend
│       ├── storage.py           ✅ tested — LocalStorage + S3Storage
│       └── constants.py        ✅
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.production          # Cognito pool IDs (not secrets, in repo)
│   └── src/
│       ├── main.jsx
│       ├── App.jsx              # Wraps in AuthContext
│       ├── App.css
│       ├── auth/
│       │   ├── cognito.js       # CognitoUserPool + helpers
│       │   └── AuthContext.jsx  # { user, token, login, logout }
│       ├── api/
│       │   └── rankings.js      # All fetch() calls (with auth headers)
│       └── components/
│           ├── LoginPage.jsx / .css
│           ├── WarRoom.jsx / .css
│           ├── PositionColumn.jsx / .css
│           ├── TierGroup.jsx / .css
│           ├── PlayerRow.jsx / .css
│           ├── SearchBar.jsx / .css
│           ├── NotesDialog.jsx
│           ├── AddPlayerDialog.jsx
│           ├── DeleteConfirmDialog.jsx
│           ├── SaveAsDialog.jsx
│           ├── LoadDialog.jsx
│           ├── ResetConfirmDialog.jsx
│           ├── SetDefaultConfirmDialog.jsx
│           └── ExitDraftConfirmDialog.jsx
└── tests/
    ├── conftest.py              # storage fixture (LocalStorage)
    ├── test_data_loader.py      ✅ 8 passing
    ├── test_rankings.py         ✅ 27 passing
    ├── test_profile_management.py ✅ 14 passing
    ├── test_storage.py          ✅ passing
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

#### 1c — AWS Deployment ✅ Complete
- [x] `09-init-aws-deploy.md` — S3 storage backend, Cognito auth, EC2 deploy

#### 1d — Polish (next)
- [ ] `10-init-k-dst.md` — Add K and D/ST columns
- [ ] Export rankings to CSV
- [ ] Rename/delete saved profiles

### Phase 2: Live Draft (future)
- [ ] Snake draft board, mark picks
- [ ] Best available board
- [ ] My roster view, scarcity alerts

### Phase 3: Multi-User (future consideration)
- [ ] User-scoped S3 keys (`rankings/{user_id}/default.json`)
- [ ] Registration flow
- [ ] Per-user profile isolation

## Key Constraints

1. **Two environments**: local dev (LocalStorage, no auth) and production (S3, Cognito JWT)
2. **File size limit: 500 lines max** — split into modules when approaching
3. **Commit after every feature** — atomic, working commits
4. **Data source**: FantasyPros half-PPR CSV exports only
5. **Python imports**: relative to `backend/` — `from utils.constants import ...`
6. **macOS M1**: Python 3.9+, `from __future__ import annotations`
7. **No credentials in code**: EC2 uses IAM instance role; Cognito IDs are not secrets
8. **Automate everything**: CDK, deploy scripts, systemd — no manual console steps
