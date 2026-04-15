# FF Draft Room - Task Tracker

## Current Sprint: Phase 1d — Polish

### In Progress
_None_

---

## Backlog

### Phase 1d — Polish
- [ ] Export rankings to CSV
- [ ] Rename / delete saved profiles

### Phase 2 — Live Draft (future)
- [ ] Full draft board with round/pick tracking
- [ ] Best available board
- [ ] My roster view, needs tracker, scarcity alerts

---

## Recently Completed

- [x] `14-init-profile-rename-delete.md` — Profile rename and delete
  - Inline rename input + delete confirm in Load dialog
  - Active profile indicator (● dot)
  - rename_profile() + delete_profile() backend utilities
  - POST /rename + DELETE /profile/{name} endpoints
  - 7 new tests (76 total passing)

- [x] `11-init-visual-polish.md` — Position-specific column accent colors
  - QB gold, RB green, WR blue, TE orange — header border + tier left-border
  - depth · N sub-label on column headers
  - Background texture attempted and rolled back — clean navy reads better

- [x] `12-init-team-logos.md` — NFL team logos on player name boxes
  - ESPN CDN, right-aligned inside name box, 18px, opacity 72%
  - JAC→jax normalization, silent fallback for FA/unknown

- [x] `13-init-team-gradients.md` — Team color gradients on player name boxes
  - Flat tier color left → team tint (22%) right, kicks in at 45%
  - Applies in War Room and Draft Mode (tints draft status colors too)

- [x] `10-init-tier-drag.md` — Draggable Tier Boundaries
  - `set_player_tier()` backend utility + `PUT /{position}/{rank}/tier` endpoint
  - `TierSeparator` component with mouse + touch drag support
  - Empty tier guard prevents dragging below 1 player
  - Adjacency validation (±1 only) on backend
  - 5 new unit tests (69 total passing)
  - ADR-009 (Draggable Tier Boundaries)

- [x] `09-init-aws-deploy.md` — AWS Deployment
  - S3 StorageBackend abstraction (LocalStorage + S3Storage)
  - Cognito JWT auth middleware (conditional — prod only)
  - Frontend auth: LoginPage + AuthContext + token headers
  - CDK stack: S3 bucket + IAM role + instance profile
  - Deploy scripts: deploy.sh, cdk-bootstrap.sh, nginx, systemd
  - 15 new storage tests (64 total passing)
  - ADR-007 (EC2 + nginx), ADR-008 (S3 Storage Backend)

- [x] `08-init-search.md` — Global Player Search
  - Commit: `f7d3743`
  - SearchBar component with dropdown overlay, in-memory filtering
  - Scroll-to-player with 1.5s highlight on result click
  - Works in both War Room and Draft Mode

- [x] `07-init-draft-mode.md` — Draft Mode
  - Commit: `7992c01`
  - WAR ROOM | DRAFT toggle in header
  - Status dot per player: undrafted → mine → other cycling
  - Controls hidden in draft mode, exit confirm dialog
  - Pure frontend — no backend changes

- [x] `06-init-profile-management.md` — Profile Management
  - Commits: `a190560`, `83922b4`, `5dc8df4`
  - Save As, Load, Reset, Set as Default
  - 5 new backend endpoints, 4 new frontend dialogs
  - 14 new tests (49 total passing)

- [x] `05-init-react-frontend.md` — React War Room Frontend
  - Commit: `89a7c20`
  - 7 components: WarRoom, PositionColumn, TierGroup, PlayerRow,
    NotesDialog, AddPlayerDialog, DeleteConfirmDialog
  - Full CSS control with design tokens, native HTML `<dialog>`
  - Vite proxy to FastAPI backend

- [x] `04-init-fastapi-backend.md` — FastAPI Backend
  - Commits: `5017f03`, `770efd6`, `363a3df`, `12e4f2f`
  - 8 API endpoints for rankings CRUD + profile management
  - Ported utils from app/ to backend/, removed Streamlit deps
  - All tests updated to import from backend/

- [x] `03-init-war-room-core.md` — War Room in Streamlit
  - Commit: `dede688`
  - Retired due to Streamlit UI limitations (ADR-006)

- [x] `01-init-project-setup.md` — Project scaffold, data loader
  - Commit: `6a5f313`

---

## Dropped / Descoped

- ~~Streamlit UI~~ — **Retired** (2026-03-30)
  - Replaced by FastAPI + React (ADR-006)

- ~~`02-init-history-browser.md`~~ — **Dropped** (2026-03-30)
  - App is rankings-only. Historical data is seed infrastructure.

- ~~K and D/ST columns~~ — **Dropped** (2026-04-14)
  - Not needed — handled separately during drafts

---

## Architecture Decisions

### Import Convention (Backend)
All backend Python imports are relative to `backend/`:
```python
# CORRECT
from utils.constants import POSITIONS
from utils.rankings import load_or_seed
from utils.storage import get_storage

# WRONG
from backend.utils.constants import POSITIONS
```

### Profile Storage Model
```
default.json       ← active profile (always present)
seed.json          ← custom reset baseline (optional)
{name}.json        ← named profiles created via Save As
```
In local dev: files in `data/rankings/`
In production: S3 objects under `rankings/` prefix

---

## Notes

### Running the Stack
```bash
# Backend
source .venv/bin/activate
uvicorn backend.main:app --reload   # → localhost:8000

# Frontend
cd frontend && npm run dev          # → localhost:5173
```

### Production Deploy
```bash
# On EC2
git pull origin main
./scripts/deploy.sh
```

### Tests
```bash
pytest tests/ --cov=backend         # 64 passing
ruff check backend/ tests/          # zero errors
```

### CSV File Naming
```
data/players/QB_2020.csv  through  QB_2025.csv
data/players/RB_2020.csv  through  RB_2025.csv
data/players/WR_2020.csv  through  WR_2025.csv
data/players/TE_2020.csv  through  TE_2025.csv
```

### League Defaults
- 10 teams, half-PPR, standard roster
- Positions: QB, RB, WR, TE

---

*Last updated: 2026-04-14 (AWS deployment complete)*
