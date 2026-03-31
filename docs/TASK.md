# FF Draft Room - Task Tracker

## Current Sprint: Phase 1b — Stack Migration

### In Progress
- [ ] `04-init-fastapi-react-migration.md` — Retire Streamlit, build FastAPI + React

---

## Backlog

### Phase 1b — Migration (current focus)
- [ ] `04-init-fastapi-react-migration.md` — Full stack replacement:
  - FastAPI backend with REST API wrapping existing utils/
  - Vite + React frontend
  - Full War Room: QB/RB/WR/TE columns, tier groups, ▲▼ reorder,
    notes dialog, add player, delete player, save

### Phase 1c — Polish (future)
- [ ] `05-init-k-dst.md` — Add K and D/ST columns
- [ ] `06-init-rankings-profiles.md` — Multiple saved profiles
- [ ] Export rankings to CSV

### Phase 2 — Live Draft (future)
- [ ] Snake draft board, mark picks mine/other
- [ ] Best available board
- [ ] My roster view, needs tracker, scarcity alerts

---

## Recently Completed

- [x] `03-init-war-room-core.md` — War Room in Streamlit
  - Commit: `dede688`
  - 43 tests passing, 84% coverage
  - All core features working: tiers, reorder, notes, add, delete, save
  - Retired due to Streamlit UI limitations (CSS/layout constraints)

- [x] `01-init-project-setup.md` — Project scaffold, data loader, Streamlit skeleton
  - Commit: `6a5f313`
  - 8 tests passing, 81% coverage on app/utils/

---

## Dropped / Descoped

- ~~Streamlit UI~~ — **Retired** (2026-03-30)
  - Reason: Streamlit cannot support the dense, interactive war room layout.
    Background colors behind widgets, precise CSS control, and custom layouts
    are not achievable within Streamlit's rendering model.
  - All Python utility logic (data_loader, rankings, constants) is kept and
    ported to backend/utils/. Tests unchanged.
  - ADR-006 documents this decision.

- ~~`02-init-history-browser.md`~~ — **Dropped** (2026-03-30)
  - Reason: App is rankings-only. Historical data is seed infrastructure.

---

## Architecture Decisions

### Import Convention (Backend)
All backend Python imports are relative to `backend/`:
```python
# CORRECT
from utils.constants import POSITIONS
from utils.rankings import load_or_seed

# WRONG
from backend.utils.constants import POSITIONS
```

### What Is Kept from Streamlit Version
- `backend/utils/data_loader.py` — unchanged, fully tested
- `backend/utils/rankings.py` — unchanged, fully tested
- `backend/utils/constants.py` — unchanged
- `tests/` — all 43 tests carry over

### What Is Scrapped
- `app/main.py` — Streamlit entry point
- `app/pages/` — all Streamlit pages
- `app/components/` — Streamlit components
- `.streamlit/config.toml` — Streamlit config
- All Streamlit CSS injection

---

## Notes

### Running the New Stack
```bash
# Backend
cd ff-draft-room
source .venv/bin/activate
uvicorn backend.main:app --reload
# → localhost:8000

# Frontend (separate terminal)
cd frontend
npm run dev
# → localhost:5173
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
- Positions: QB, RB, WR, TE (K and D/ST in Phase 1c)

### Known Issues (Streamlit era — resolved by migration)
- Python 3.9: `from __future__ import annotations` still required in backend utils

---

*Last updated: 2026-03-30 (pivot to FastAPI + React)*
