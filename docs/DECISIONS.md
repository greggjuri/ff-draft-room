# FF Draft Room - Architecture Decisions

## ADR-001: Streamlit as UI Framework

**Date**: 2026-03-22
**Status**: Superseded by ADR-006

### Decision
Use Streamlit for the UI layer.

### Superseded Because
Streamlit cannot support the dense, interactive war room layout required.
See ADR-006.

---

## ADR-002: JSON Files for Rankings Persistence

**Date**: 2026-03-22
**Status**: Accepted

### Decision
Use JSON files in `data/rankings/` for all ranking profiles.

### Rationale
- Human-readable, no setup, portable, easy to back up
- Profiles are small (< 200 players, ~50KB max)

### Consequences
- Zero setup, works out of the box
- No query capability — load entire profile into memory (acceptable)

---

## ADR-003: FantasyPros CSV as Sole Data Source

**Date**: 2026-03-22
**Status**: Accepted

### Decision
Use exclusively FantasyPros half-PPR season leaders CSV exports.
No approximations, no fallbacks, no hardcoded data.

### Rationale
- 24 CSV files already collected (4 positions × 6 years)
- Verified authoritative source
- Fully offline at runtime

---

## ADR-004: VOR Replacement Level Thresholds

**Date**: 2026-03-22
**Status**: Accepted

### Decision
Default replacement levels for 10-team half-PPR:
- QB: Rank 13 · RB: Rank 25 · WR: Rank 35 · TE: Rank 13

Configurable per ranking profile.

---

## ADR-005: Rankings-Only App — No History Browser

**Date**: 2026-03-30
**Status**: Accepted

### Decision
Drop History and Analysis pages. Historical CSV data seeds the initial
rankings baseline only. No user-facing history view.

### Rationale
App is a draft preparation tool, not a stats browser.
Tighter scope = faster path to a usable tool.

---

## ADR-006: Retire Streamlit — Migrate to FastAPI + React

**Date**: 2026-03-30
**Status**: Accepted

### Context
The War Room was fully implemented in Streamlit (commit dede688, 43 tests
passing). During UI polish, Streamlit's fundamental rendering model
repeatedly blocked desired UI behaviour:

- Background colors cannot be applied to sections containing widgets —
  Streamlit strips custom HTML div wrappers around interactive elements
- CSS selectors targeting Streamlit's internal DOM structure are fragile
  and break across versions
- `nth-child` / `nth-of-type` selectors cannot reliably target tier groups
  because Streamlit inserts unpredictable wrapper elements
- MutationObserver JavaScript injection was required just to attempt basic
  alternating row colors — and still failed
- The war room is a dense, interactive, pixel-precise layout that Streamlit
  was never designed to support

Streamlit is the right tool for data dashboards with charts and tables.
It is the wrong tool for a custom interactive board UI.

### Decision
Retire Streamlit entirely. Migrate to:
- **Backend**: FastAPI — REST API serving rankings data
- **Frontend**: Vite + React — full UI ownership, full CSS control

### What Is Kept
- `backend/utils/data_loader.py` — ported unchanged, all tests pass
- `backend/utils/rankings.py` — ported unchanged, all tests pass
- `backend/utils/constants.py` — ported unchanged
- All 43 unit tests — carry over to `tests/`
- `data/players/` CSV files — unchanged
- `data/rankings/default.json` — unchanged

### What Is Scrapped
- `app/main.py` and all Streamlit pages
- `.streamlit/config.toml`
- All CSS injection and JavaScript workarounds

### Alternatives Considered
| Option | Verdict |
|--------|---------|
| Keep Streamlit, accept limitations | Rejected — too many layout blockers |
| Streamlit + custom component | Rejected — high complexity, still limited |
| Flask + vanilla HTML/JS | Rejected — FastAPI is more modern, better DX |
| Reflex | Rejected — less mature, smaller community |
| FastAPI + React (Vite) | **Selected** |

### Consequences
**Positive:**
- Full CSS control — any layout, any color, any interaction
- Real drag-and-drop possible in future
- Clean separation of concerns: Python handles data, React handles UI
- Existing Python utility layer is fully preserved and tested

**Negative:**
- Two processes to run (backend + frontend dev server)
- JavaScript required for frontend — new language in the stack
- More initial setup than Streamlit

---

## Template for New Decisions

```markdown
## ADR-XXX: Title

**Date**: YYYY-MM-DD
**Status**: Proposed/Accepted/Deprecated/Superseded

### Context
### Decision
### Rationale
### Alternatives Considered
### Consequences
```

## Key Principles

1. **No approximations**: All player data from verified CSV exports
2. **Local first**: No cloud, no API keys, no network calls at runtime
3. **Rankings-only UI**: Historical data is seed infrastructure, not a feature
4. **Graceful degradation**: Missing files warn the user, never crash
5. **Full UI control**: React owns the frontend — no CSS framework fighting
