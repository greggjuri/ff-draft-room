# FF Draft Room - Project Planning

## Project Vision

A personal fantasy football draft tool for building and managing pre-draft rankings.
Two modes: **War Room** — a live rankings board where you reorder players, assign tiers,
add notes, and build your cheat sheet; and **Draft Mode** — mark players as drafted
during a live draft.

Runs locally on MacBook Air M1 for development. Deployed to AWS EC2 at
`ff.jurigregg.com` for access from any device on draft day.

Fantasy Footballers Podcast 2026 expert consensus rankings (ADR-010,
tiered ingest per PRP-019) seed the initial rankings baseline.
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
│  data/players/      │     │  data/rankings/*.json   │
│  2026_{POS}.csv     │     │  LocalStorage (dev)     │
│  (FF Podcast seed)  │     │  gitignored runtime     │
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

### Rankings endpoints (17 total)
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
POST   /api/rankings/rename                   → rename a saved profile
DELETE /api/rankings/profile/{name}           → delete a saved profile

GET    /api/rankings/{position}               → players for one position
POST   /api/rankings/{position}/reorder       → swap two players (▲▼)
POST   /api/rankings/{position}/add           → add a new player (10 fields)
DELETE /api/rankings/{position}/{rank}        → delete a player
PUT    /api/rankings/{position}/{rank}/tier   → reassign player tier
PUT    /api/rankings/{position}/{rank}/tag    → set/clear player tag
PUT    /api/rankings/{position}/{rank}/notes  → update player notes
```

All `/api/*` endpoints require Cognito JWT in production.
`/health` is always unauthenticated (used by deploy script).

### Request/Response shapes
```json
// POST /api/rankings/{position}/reorder
{ "rank_a": 2, "rank_b": 3 }

// POST /api/rankings/{position}/add  (required: name/team/tier; rest optional, null/"" defaults)
{ "name": "Josh Allen", "team": "BUF", "tier": 1,
  "bye_week": 7, "adp": "3.05", "projected_points": 428.3,
  "risk": 2.6, "upside": 9.7,
  "outlook": "Elite passer with rushing floor." }

// PUT /api/rankings/{position}/{rank}/tier
{ "tier": 2 }     // must be adjacent (±1) to current tier

// PUT /api/rankings/{position}/{rank}/tag
{ "tag": "fire" } // one of: "", heart, fire, gem, warning, cross, skull, flag

// PUT /api/rankings/{position}/{rank}/notes
{ "notes": "Elite rushing upside" }

// POST /api/rankings/save-as | POST /api/rankings/load | DELETE /api/rankings/profile/{name}
{ "name": "Mock Draft 1" }

// POST /api/rankings/rename
{ "name": "Old Name", "new_name": "New Name" }
```

## Data Model

### Player (JSON)
Shape established by PRP-019 (tiered ingest) + PRP-020 (manual-add
parity). See ADR-011. Seeded and manually-added records share this
shape exactly.

```json
{
  "position_rank": 1,
  "name": "Josh Allen",
  "team": "BUF",
  "position": "QB",
  "tier": 1,
  "bye_week": 7,
  "adp": "3.05",
  "projected_points": 428.3,
  "risk": 2.6,
  "upside": 9.7,
  "outlook": "He is him. While technically Allen finished with...",
  "notes": "",
  "tag": ""
}
```

Field nullability:
- `bye_week`: `int | null` (null for unsigned/uncertain players)
- `adp`: `str` — always present, `""` when missing. Kept as string to
  preserve trailing zeros in `RR.PP` format (`"3.10"` not `3.1`)
- `projected_points`, `risk`, `upside`: `float | null` (null for
  manually-added players who skip the field)
- `outlook`: `str` — always present, `""` when missing
- `notes`, `tag`: user-owned, `""` until set

`risk` / `upside` are captured but not currently surfaced in the UI.

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
│   ├── players/                 # 2026_{POS}.csv — FF Podcast tiered (read-only)
│   └── rankings/                # JSON profiles (local dev only, gitignored)
├── backend/
│   ├── main.py                  # FastAPI app, CORS, storage init
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py              # Cognito JWT verification
│   ├── routers/
│   │   └── rankings.py          # /api/rankings/* routes (17 endpoints)
│   └── utils/
│       ├── __init__.py
│       ├── data_loader.py       ✅ 15 tests
│       ├── rankings.py          ✅ 47 tests — uses StorageBackend
│       ├── storage.py           ✅ 15 tests — LocalStorage + S3Storage
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
│           ├── TierSeparator.jsx / .css       # Draggable boundaries (ADR-009)
│           ├── PlayerRow.jsx / .css
│           ├── SearchBar.jsx / .css
│           ├── RosterPanel.jsx / .css         # Draft-mode bottom drawer
│           ├── PlayerDetailDialog.jsx / .css  # Outlook + notes (PRP-021/022)
│           ├── ContextMenu.jsx / .css         # Right-click menu (PRP-020)
│           ├── AddPlayerDialog.jsx / .css     # 10-field add (PRP-020)
│           ├── DeleteConfirmDialog.jsx
│           ├── SaveAsDialog.jsx
│           ├── LoadDialog.jsx
│           ├── ResetConfirmDialog.jsx
│           ├── SetDefaultConfirmDialog.jsx
│           └── ExitDraftConfirmDialog.jsx
└── tests/
    ├── conftest.py              # storage fixture (LocalStorage)
    ├── test_data_loader.py      ✅ 15 passing
    ├── test_rankings.py         ✅ 47 passing
    ├── test_profile_management.py ✅ 21 passing
    ├── test_storage.py          ✅ 15 passing
    └── test_vor.py              # 1 skipped placeholder
    # Total: 98 passing, 1 skipped
```

## Development Phases

### Phase 1: War Room

#### 1a — Foundation ✅ Complete
- [x] CSV loading + normalization (`data_loader.py`)
- [x] Rankings CRUD + seed logic (`rankings.py`)
- [x] 98 tests passing — coverage maintained on `backend/utils/`

#### 1b — Stack Migration ✅ Complete
- [x] `04-init-fastapi-backend.md` — FastAPI backend, 13 endpoints
- [x] `05-init-react-frontend.md` — React frontend, 13 components
- [x] `06-init-profile-management.md` — Save As, Load, Reset, Set Default
- [x] `07-init-draft-mode.md` — Draft mode with status dot cycling
- [x] `08-init-search.md` — Global player search with scroll-to-highlight

#### 1c — AWS Deployment ✅ Complete
- [x] `09-init-aws-deploy.md` — S3 storage backend, Cognito auth, EC2 deploy

#### 1d — Polish ✅ Complete
- [x] `10-init-tier-drag.md` — Draggable tier separators (ADR-009)
- [x] `11-init-visual-polish.md` — Position-specific accent colors
- [x] `12-init-team-logos.md` — NFL team logos on rows
- [x] `13-init-team-gradients.md` — Team color gradients
- [x] `14-init-profile-rename-delete.md` — Profile rename + delete
- [x] `15-init-player-tags.md` — 7 tag icons + tag picker
- [x] `16-init-roster-panel.md` — Draft-mode roster drawer
- [x] `17-init-fantasy-footballers-import.md` — FF Podcast seed (ADR-010)
- [x] `18-init-untrack-rankings-and-doc-cleanup.md` — Repo hygiene
- [x] `19-init-fantasy-footballers-tiered-import.md` — Tiered ingest + 6 new fields
- [x] `20-init-add-delete-ux-overhaul.md` — Toolbar add + ContextMenu
- [x] `21-init-player-detail-dialog.md` — Outlook + notes split panel
- [x] `22-init-player-detail-in-draft-mode.md` — Click-to-detail in Draft Mode

Dropped: K and D/ST (handled separately during drafts), Export to CSV.

### Phase 2: Live Draft (future)
- [ ] Snake draft board, mark picks
- [ ] Best available board
- [ ] My roster view, scarcity alerts

### Phase 3: Multi-User (future consideration)
- [ ] User-scoped S3 keys (`rankings/{user_id}/default.json`)
- [ ] Registration flow
- [ ] Per-user profile isolation

## PRP Review Process

Before Claude Code runs `/execute-prp`, the generated PRP is reviewed
in Claude.ai against the init spec. The review checks:

1. **Completeness** — all files from the init are covered
2. **Correctness** — logic matches the spec (edge cases, validation, data model)
3. **Consistency** — no contradictions with existing ADRs or patterns
4. **Test coverage** — new tests cover the new behaviour
5. **Scope** — nothing out of scope has crept in

PRPs scoring 9.5–10/10 proceed to execution unchanged.
PRPs with issues get specific change requests before execution.

## Key Constraints

1. **Two environments**: local dev (LocalStorage, no auth) and production (S3, Cognito JWT)
2. **File size limit: 500 lines max** — split into modules when approaching
3. **Commit after every feature** — atomic, working commits
4. **Data source**: Fantasy Footballers Podcast 2026 expert consensus
   CSVs only (ADR-010, tiered ingest per PRP-019). No approximations,
   no fallbacks.
5. **Python imports**: relative to `backend/` — `from utils.constants import ...`
6. **Python 3.9+**: `from __future__ import annotations` at top of every backend file
   for union types (`int | None`, `Path | None`, etc.)
7. **No credentials in code**: EC2 uses IAM instance role; Cognito IDs are not secrets
8. **Automate everything**: CDK, deploy scripts, systemd — no manual console steps
