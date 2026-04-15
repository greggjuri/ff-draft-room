# FF Draft Room 🏈

A personal fantasy football draft preparation and live-draft tracking tool.
Built for 10-team half-PPR Yahoo leagues.

**Live at**: https://ff.jurigregg.com

## Features

### War Room (Pre-Draft)
- **Rankings Board** — 4-column view (QB | RB | WR | TE), all positions visible simultaneously
- **Tier Groups** — players grouped by tier with alternating backgrounds
- **Free Reorder** — ▲▼ buttons reorder within and across tier boundaries
- **Player Notes** — click any player name to add/edit scouting notes
- **Profile Management** — Save As, Load, Reset, Set Default baseline
- **Unsaved Indicator** — tracks changes since last save

### Draft Mode (Live Draft)
- **Mode Toggle** — switch between War Room and Draft with one click
- **Status Dots** — click to cycle each player: undrafted → mine → other
- **Color Coding** — green for your picks, purple for others'
- **In-Memory** — draft state never persisted, clean slate every time

### Global Search
- **Live Search** — find any player across all 4 positions instantly
- **Scroll-to-Player** — click a result to jump and highlight the player
- **Draft-Aware** — shows pick status in search results during Draft Mode

## Tech Stack

### Backend
- **FastAPI** + Python 3.9+
- **S3** for rankings persistence in production
- **Local JSON files** for local development
- **Cognito JWT** auth on all endpoints

### Frontend
- **React 18** + Vite
- **Plain CSS** — no framework, full design control
- **Cognito** login via `amazon-cognito-identity-js`

### Infrastructure
- **AWS EC2 t3.micro** — 24/7 backend via systemd + uvicorn
- **nginx** — reverse proxy + SSL + static file serving
- **AWS CDK** — all infrastructure as code

## Data

All player data sourced from [FantasyPros](https://www.fantasypros.com) half-PPR season leaders exports.

| Position | Depth |
|----------|-------|
| QB | Top 30 |
| RB | Top 50 |
| WR | Top 50 |
| TE | Top 30 |

## Local Development

### Prerequisites
- Python 3.9+
- Node.js 18+

### Setup

```bash
# Clone the repo
git clone https://github.com/greggjuri/ff-draft-room.git
cd ff-draft-room

# Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Add your FantasyPros CSV exports to data/players/:
# QB_2025.csv, RB_2025.csv, WR_2025.csv, TE_2025.csv

# Frontend dependencies
cd frontend && npm install && cd ..
```

### Running

```bash
# Terminal 1 — Backend
source .venv/bin/activate
uvicorn backend.main:app --reload

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### Environment

Create a `.env` file in the project root for local dev:
```bash
STORAGE_BACKEND=local
RANKINGS_DIR=data/rankings
```

## Production Deployment

### First-Time Infrastructure (from Debian machine with AWS CLI + CDK)

```bash
./scripts/cdk-bootstrap.sh <EC2_INSTANCE_ID>
```

Creates S3 bucket, IAM role, and attaches instance profile to EC2.

### Deploy (on EC2)

```bash
git pull origin main
./scripts/deploy.sh
```

Builds the frontend, copies the dist, restarts uvicorn via systemd.

## CSV Format

FantasyPros half-PPR season leaders exports. Export from:
`fantasypros.com → Fantasy Football → Leaders → [Position] → Half PPR → Export CSV`

Expected columns: `#, Player, Pos, Team, GP, [week columns], AVG, TTL`

## Development Workflow

This project uses the [CE workflow](https://github.com/greggjuri/CE-templates) —
Claude.ai for planning and architecture, Claude Code for implementation.

```bash
# Tests
pytest tests/ --cov=backend

# Lint
ruff check backend/ tests/

# Generate a PRP from an init spec (in Claude Code)
/generate-prp initials/NN-init-{feature}.md

# Execute a PRP (in Claude Code)
/execute-prp prps/NN-prp-{feature}.md
```

See `docs/PLANNING.md` for architecture and `docs/TASK.md` for current status.

## Project Structure

```
ff-draft-room/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── middleware/auth.py   # Cognito JWT verification
│   ├── routers/rankings.py  # API routes
│   └── utils/               # data_loader, rankings, storage, constants
├── frontend/src/
│   ├── auth/                # Cognito + AuthContext
│   ├── api/rankings.js      # All fetch() calls
│   └── components/          # WarRoom, LoginPage, and all dialogs
├── cdk/                     # AWS CDK infrastructure stack
├── scripts/                 # deploy.sh, cdk-bootstrap.sh, nginx, systemd
├── data/
│   ├── players/             # FantasyPros CSV exports (seed data)
│   └── rankings/            # Local dev JSON profiles
├── docs/                    # PLANNING, TASK, DECISIONS
├── initials/                # Feature specs
├── prps/                    # Implementation plans
└── tests/                   # pytest unit tests
```

## License

Personal use. Not affiliated with Yahoo, FantasyPros, or the NFL.
