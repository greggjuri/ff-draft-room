# FF Draft Room - Task Tracker

## Current Sprint: Phase 1a — Foundation

### In Progress
*(none)*

### Up Next
- [ ] `init-history-browser.md` — Historical stats browser page

---

## Backlog

### Phase 1a — Foundation (start here)
- [x] `init-project-setup.md` — requirements.txt, .streamlit/config.toml, data_loader.py, main.py skeleton
- [ ] `init-history-browser.md` — History page: position/year tabs, sortable table, search, filters

### Phase 1b — Core War Room
- [ ] `init-war-room-rankings.md` — Rankings editor: load baseline from history, reorder, assign tiers, save profile
- [ ] `init-vor-calculator.md` — VOR engine (utils/vor.py) + Analysis page with positional depth charts

### Phase 1c — Polish
- [ ] `init-rankings-profiles.md` — Profile manager: multiple saves, load/copy/delete, export CSV

### Phase 2 — Live Draft
- [ ] `init-live-draft-tracker.md` — Snake draft board (10-team), mark picks mine/other, pick clock
- [ ] `init-draft-roster-view.md` — My team view, needs tracker, scarcity alerts by tier

### Future / Nice to Have
- [ ] ADP data import (FantasyPros ADP CSV)
- [ ] Mock draft simulator
- [ ] Trade evaluator
- [ ] Side-by-side player comparison

---

## Recently Completed

- [x] `init-project-setup.md` — Scaffold, deps, dark theme, data_loader, main.py, page stubs, tests (2026-03-22)

---

## Completed

*(nothing yet)*

---

## Architecture Decisions

### Data Source Decision
All player data sourced exclusively from FantasyPros half-PPR CSV exports.
No approximations, no hardcoded fallback data. If file missing → warn user, return empty DataFrame.

### Local Persistence
Rankings profiles saved as JSON to `data/rankings/`. No database.
Simple, portable, human-readable. User can back up or share profile files manually.

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
- Scoring: QB/RB/WR/TE (no K or DST in data)

### Known Issues
- Python 3.9.6 (system) — requires `from __future__ import annotations` for `X | None` type unions

---

*Last updated: 2026-03-22 (project setup complete)*
