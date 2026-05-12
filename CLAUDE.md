# FF Draft Room - Project Instructions

## What This Is

A personal fantasy football draft preparation tool.
Built for personal use — runs locally on MacBook Air M1 for development,
deployed to AWS EC2 at `ff.jurigregg.com` for access from any device.

**Two modes**: **War Room** (build and manage pre-draft rankings) and
**Draft Mode** (mark players as drafted during a live draft).
Historical FantasyPros data seeds the initial rankings baseline — it is
infrastructure, not UI.

**Repository**: github.com/greggjuri/ff-draft-room
**Also mirrored to**: Gitea self-hosted (home lab)
**Live**: https://ff.jurigregg.com

## Tech Stack

### Backend
- **FastAPI** — REST API, runs at localhost:8000 (dev) / port 8000 behind nginx (prod)
- **Python 3.9+** — `from __future__ import annotations` required for union types
- **Pandas** — CSV processing
- **StorageBackend** — abstraction over LocalStorage (dev) and S3Storage (prod)
- **pytest + ruff** — testing and linting

### Frontend
- **React 18 + Vite** — runs at localhost:5173 (dev) / served as static build by nginx (prod)
- **Plain CSS** — full control, no CSS framework
- **fetch API** — HTTP calls to FastAPI backend
- **amazon-cognito-identity-js** — Cognito auth in browser

### Infrastructure
- **AWS EC2 t3.micro** — 24/7, runs uvicorn via systemd
- **AWS S3** — rankings JSON persistence in production (`ff-draft-room-data` bucket)
- **AWS Cognito** — JWT auth (`ff-draft-room-users` User Pool)
- **nginx** — reverse proxy + static file serving + SSL termination
- **CDK** — all infrastructure defined as code (`cdk/`)

## Environments

### Local Dev
```bash
STORAGE_BACKEND=local       # reads/writes data/rankings/*.json
# No auth enforcement       # Cognito middleware inactive
```

### Production (EC2)
```bash
STORAGE_BACKEND=s3          # reads/writes S3 bucket ff-draft-room-data
COGNITO_USER_POOL_ID=...    # JWT auth required on all endpoints
```

## Running the App

### Local Development
```bash
# Terminal 1 — Backend
source .venv/bin/activate
uvicorn backend.main:app --reload

# Terminal 2 — Frontend
cd frontend
npm run dev
```
Open `localhost:5173` in browser.

### Production Deploy (on EC2)
```bash
git pull origin main
./scripts/deploy.sh
```

### First-Time AWS Infrastructure Setup (from Debian machine)
```bash
./scripts/cdk-bootstrap.sh <EC2_INSTANCE_ID>
```

## Critical Constraints

1. **Two environments**: local dev uses LocalStorage + no auth; production uses S3 + Cognito JWT
2. **File size limit: 500 lines** — split into modules when approaching
3. **Commit after every feature** — atomic, working commits
4. **Data source**: Fantasy Footballers Podcast 2026 expert consensus
   rankings CSVs only (ADR-010) — no approximations, no fallbacks
5. **No Streamlit** — retired (ADR-006). Do not add Streamlit back.
6. **No credentials in code** — EC2 uses IAM instance role for S3 access; Cognito IDs are not secrets

## Python Import Convention

All backend imports are relative to `backend/`:
```python
# CORRECT
from utils.constants import POSITIONS
from utils.rankings import load_or_seed
from utils.storage import get_storage
from middleware.auth import require_auth

# WRONG — breaks at runtime
from backend.utils.constants import POSITIONS
```

## What Is NOT in This App

- **No Streamlit** — retired due to UI limitations (ADR-006)
- **No history browser** — historical data is seed infrastructure only (ADR-005)
- **No database** — JSON files (local) or S3 JSON blobs (production) only (ADR-002, ADR-008)
- **No drag-and-drop** — future consideration
- **No K or D/ST** — not needed, handled separately during drafts
- **No multi-user support** — single user only (ADR-007); future phase consideration

## Project Structure

```
ff-draft-room/
├── CLAUDE.md
├── env.production.example       # Template for EC2 .env.production (not in repo)
├── data/
│   ├── players/                 # FantasyPros CSVs (read-only seed data)
│   └── rankings/                # JSON profiles — local dev only
├── backend/
│   ├── main.py                  # FastAPI app + CORS + storage init
│   ├── middleware/
│   │   └── auth.py              # Cognito JWT verification
│   ├── routers/
│   │   └── rankings.py          # All /api/rankings/* routes
│   └── utils/
│       ├── data_loader.py       ✅ tested
│       ├── rankings.py          ✅ tested — uses StorageBackend
│       ├── storage.py           ✅ tested — LocalStorage + S3Storage
│       └── constants.py        ✅ tested
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.production          # Cognito pool identifiers (in repo, not secrets)
│   └── src/
│       ├── App.jsx              # Wraps app in AuthContext
│       ├── App.css
│       ├── auth/
│       │   ├── cognito.js       # CognitoUserPool + login/logout/getToken
│       │   └── AuthContext.jsx  # React context: { user, token, login, logout }
│       ├── api/rankings.js      # All fetch() calls — never fetch in components
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
├── cdk/
│   ├── app.py                   # CDK app entry point
│   ├── ff_deploy_stack.py       # S3 bucket + IAM role + instance profile
│   ├── requirements.txt
│   └── cdk.json
├── scripts/
│   ├── deploy.sh                # EC2 deploy: pull, build, restart
│   ├── cdk-bootstrap.sh         # One-time CDK deploy from Debian
│   ├── nginx.conf.template      # nginx config template
│   └── ff-draft-room.service    # systemd unit file
└── tests/
    ├── conftest.py              # storage fixture (LocalStorage)
    ├── test_data_loader.py      ✅ 8 passing
    ├── test_rankings.py         ✅ 27 passing
    ├── test_profile_management.py ✅ 14 passing
    ├── test_storage.py          ✅ passing
    └── test_vor.py              # Future
```

## API Routes

```
GET    /health                                    (unauthed — health check)
GET    /api/rankings                              (auth required)
POST   /api/rankings/save                         (auth required)
POST   /api/rankings/seed                         (auth required)
GET    /api/rankings/profiles                     (auth required)
POST   /api/rankings/save-as         { name }     (auth required)
POST   /api/rankings/load            { name }     (auth required)
POST   /api/rankings/set-default                  (auth required)
POST   /api/rankings/reset                        (auth required)
GET    /api/rankings/{position}                   (auth required)
POST   /api/rankings/{position}/reorder           (auth required)
POST   /api/rankings/{position}/add               (auth required)
DELETE /api/rankings/{position}/{rank}            (auth required)
PUT    /api/rankings/{position}/{rank}/notes      (auth required)
```

**Critical**: named routes (`/profiles`, `/save-as`, `/load`, etc.) must be
registered BEFORE `/{position}` to avoid FastAPI matching them as path params.

## War Room UI Behaviour

- **Sticky header**: always visible while scrolling
- **4 columns**: QB | RB | WR | TE — all visible simultaneously
- **Tier groups**: players grouped with alternating backgrounds (odd `#1A3A5C`, even `#2A5A8C`)
- **▲▼**: free reorder; crossing tier boundary auto-reassigns player's tier
- **Click player name**: notes dialog (pre-filled, Save/Close)
- **[+ Position · Tier N]**: add player dialog (name + team, placed at tier end)
- **[×]**: delete confirm dialog before removal
- **Toolbar**: SAVE · SAVE AS · LOAD · RESET · ★ SET DEFAULT
- **Unsaved indicator**: shown after any change, cleared on save
- **Player depth**: QB 30 / RB 50 / WR 50 / TE 30
- **Profile name**: shown in header, updates after Save As / Load

## Profile Management

- **Save As**: saves named snapshot, switches active profile
- **Load**: lists all named profiles, loads selected
- **Reset**: restores from seed.json if it exists, falls back to CSV re-seed
- **Set as Default**: writes seed.json — baseline for all future Resets
- Reserved names: `default` and `seed` cannot be used as profile names

## Draft Mode

- **Toggle**: `WAR ROOM | DRAFT` button in sticky header
- **Draft mode hides**: ▲▼, ×, add buttons, save toolbar
- **Status dot**: click to cycle undrafted → mine → other
  - `mine` → green dot (`#00C805`), dark green name box (`#1A7A3A`)
  - `other` → purple dot (`#9B59B6`), vivid purple name box (`#6B2FA0`)
- **In-memory only**: never sent to backend, wiped on exit
- **Exit confirm**: dialog if any picks are marked

## Search

- **In-memory filter**: all 4 positions, no API calls
- **Dropdown**: grouped by position, max 5 per group, matching text bolded
- **Click result**: scrolls to player, 1.5s Honolulu Blue highlight
- **Draft Mode**: result rows show status dots
- **Escape / outside click**: closes dropdown

## Design System

- **Background**: `#0D1B2A` (dark navy)
- **Primary accent**: `#0076B6` (Honolulu Blue — Detroit Lions)
- **Font**: monospace everywhere
- **Player name boxes**: odd tiers `#1A3A5C`, even tiers `#2A5A8C`, hover `#0076B6`
- **Draft — mine**: `#1A7A3A` background, `#00C805` dot
- **Draft — other**: `#6B2FA0` background, `#9B59B6` dot

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
| Update docs | Git, tests, lint, deploy |

## Quick Reference

```bash
# Activate venv
source .venv/bin/activate

# Run backend (local dev)
uvicorn backend.main:app --reload

# Run frontend (local dev)
cd frontend && npm run dev

# Tests
pytest tests/ --cov=backend

# Lint
ruff check backend/ tests/

# Deploy to production (run on EC2)
./scripts/deploy.sh

# CDK infrastructure (run once from Debian)
./scripts/cdk-bootstrap.sh <EC2_INSTANCE_ID>

# Commit format
feat: / fix: / refactor: / docs: / test: / chore:
```

## Known Issues

- Python 3.9 on system — `Path | None` union syntax unsupported.
  Fixed with `from __future__ import annotations` at top of every backend file.
