# FF Draft Room - Task Tracker

## Current Sprint: Phase 1b — War Room Core

### In Progress
_None_

---

## Backlog

### Phase 1b — War Room Core (current focus)
- [ ] `03-init-war-room-core.md` — Full War Room page:
  - Overall + QB + RB + WR + TE tabs
  - Each row: overall rank · position rank · player · team · ▲▼ buttons
  - Click player name → `st.dialog` popup with notes text area + Save/Close
  - Manual Save button → writes to `data/rankings/default.json`
  - First launch: auto-seed from 2025 total_pts via data_loader

### Phase 1c — Polish (future)
- [ ] `04-init-rankings-profiles.md` — Multiple saved profiles: create, load, copy, delete
- [ ] Export current rankings to CSV

### Phase 2 — Live Draft (future)
- [ ] `05-init-live-draft-tracker.md` — Snake draft board (10-team), mark picks mine/other
- [ ] `06-init-draft-roster-view.md` — My team view, needs tracker, scarcity alerts

---

## Recently Completed

- [x] `03-init-war-room-core.md` — War Room rankings board
  - 4-column layout (QB/RB/WR/TE) with tier grouping and visual dividers
  - ▲▼ reordering with automatic tier reassignment on boundary crossings
  - Notes dialog, add player dialog, delete confirm dialog
  - Auto-seeding from 2025 CSV data, JSON persistence
  - 27 unit tests, 84% coverage on `app/utils/rankings.py`
  - Sidebar nav simplified to War Room + Live Draft (ADR-005)

- [x] `01-init-project-setup.md` — Project scaffold, data loader, Streamlit skeleton
  - Commit: `6a5f313`
  - 8 tests passing, 81% coverage on `app/utils/`
  - Known issue: Python 3.9 on system — fixed with `from __future__ import annotations`

---

## Dropped / Descoped

- ~~`02-init-history-browser.md`~~ — **Dropped** (2026-03-30)
  - Reason: Pivot to rankings-only app. Historical data is seed infrastructure only,
    not a browsable UI feature. The data loader already handles loading; no history
    page needed.
  - PRP was generated (02-prp-history-browser.md) but never executed.

---

## Architecture Decisions

### Import Convention (Critical)
Streamlit sets `sys.path` to `app/` at runtime. All imports must be relative to `app/`:
```python
# CORRECT
from utils.constants import POSITIONS
from pages import war_room

# WRONG — causes ModuleNotFoundError at runtime
from app.utils.constants import POSITIONS
```
This bit us on first launch. All new files must follow this pattern.

### Data Source for Seeding
Rankings seeded from 2025 `total_pts` (most recent full season).
Data loader already handles this — `load_all_players()` returns full DataFrame.
Seeding logic lives in `app/utils/rankings.py`.

### Pivot: History Page Dropped
Original plan included a History browser page for browsing stats by position/year.
Dropped in favour of a tighter product: the app is purely a rankings tool.
Historical data remains as seed source only.

---

## Notes

### CSV File Naming Convention
```
data/players/QB_2020.csv  through  QB_2025.csv
data/players/RB_2020.csv  through  RB_2025.csv
data/players/WR_2020.csv  through  WR_2025.csv
data/players/TE_2020.csv  through  TE_2025.csv
```

### League Settings (defaults)
- 10 teams, half-PPR, standard roster
- Positions tracked: QB, RB, WR, TE

### Known Issues
- Python 3.9 on system — `Path | None` union syntax unsupported.
  Fixed globally with `from __future__ import annotations` at top of affected files.

---

*Last updated: 2026-03-30 (pivot to rankings-only app)*
