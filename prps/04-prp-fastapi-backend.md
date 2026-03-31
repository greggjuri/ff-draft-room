# PRP-04: FastAPI Backend

**Created**: 2026-03-31
**Initial**: `initials/04-init-fastapi-backend.md`
**Status**: Ready

---

## Overview

### Problem Statement
The Streamlit frontend has been retired (ADR-006). The existing Python utility layer (`data_loader.py`, `rankings.py`, `constants.py`) is fully tested and working but has no way to serve data to a frontend. A REST API backend is needed to expose all rankings operations over HTTP.

### Proposed Solution
Create a FastAPI backend at `backend/` that wraps the existing utility functions as REST endpoints. Move `app/utils/` to `backend/utils/` unchanged. Add 8 API endpoints covering rankings CRUD, reordering, notes, and persistence. Update test paths. Verify all endpoints with curl.

### Success Criteria
- [ ] `pip install -r requirements.txt` — installs FastAPI + uvicorn, no errors
- [ ] `uvicorn backend.main:app --reload` starts at localhost:8000
- [ ] `GET /health` → `{"status": "ok"}`
- [ ] `GET /api/rankings` → full profile JSON
- [ ] `GET /api/rankings/QB` → 30 QB players sorted by position_rank
- [ ] `POST /api/rankings/QB/reorder` with `{"rank_a":1,"rank_b":2}` → players swapped
- [ ] `POST /api/rankings/QB/add` with `{"name":"Test","team":"TST","tier":1}` → player added
- [ ] `DELETE /api/rankings/QB/1` → player removed, ranks renumbered
- [ ] `PUT /api/rankings/QB/1/notes` with `{"notes":"Top target"}` → notes updated
- [ ] `POST /api/rankings/save` → `{"saved":true}`, file updated on disk
- [ ] `POST /api/rankings/seed` → re-seeds from CSV, returns profile
- [ ] `pytest tests/ -v` → all existing tests pass (43 total)
- [ ] `ruff check backend/ tests/` → zero errors
- [ ] All files under 500 lines

---

## Context

### Related Documentation
- `docs/DECISIONS.md` — ADR-002 (JSON persistence), ADR-003 (CSV data), ADR-005 (rankings-only), ADR-006 (Streamlit retired)
- `docs/PLANNING.md` — New architecture diagram, API design
- `docs/TASK.md` — Phase 1b migration in progress

### Dependencies
- **Required**: Phase 1a utilities complete (✅) — `data_loader.py`, `rankings.py`, `constants.py` all tested
- **Optional**: None

### Files to Create
```
backend/__init__.py              # Empty package init
backend/main.py                  # FastAPI app + CORS + health endpoint
backend/routers/__init__.py      # Empty package init
backend/routers/rankings.py      # All /api/rankings/* routes + Pydantic models
backend/utils/__init__.py        # Empty package init
backend/utils/data_loader.py     # MOVED from app/utils/data_loader.py
backend/utils/rankings.py        # MOVED from app/utils/rankings.py
backend/utils/constants.py       # MOVED from app/utils/constants.py
```

### Files to Modify
```
requirements.txt                 # Add fastapi, uvicorn; remove streamlit, plotly
tests/conftest.py                # Update sys.path from app/ to backend/
```

### Files Left Untouched
```
data/players/                    # CSVs unchanged
data/rankings/                   # JSON profiles unchanged
tests/test_data_loader.py        # Test logic unchanged
tests/test_rankings.py           # Test logic unchanged
```

---

## Technical Specification

### Pydantic Models (`backend/routers/rankings.py`)

```python
class ReorderRequest(BaseModel):
    rank_a: int
    rank_b: int

class AddPlayerRequest(BaseModel):
    name: str
    team: str
    tier: int

class NotesRequest(BaseModel):
    notes: str
```

### Module-Level State (`backend/routers/rankings.py`)

```python
_profile: dict | None = None

def get_profile() -> dict:
    global _profile
    if _profile is None:
        df = load_all_players()
        _profile = load_or_seed(df)
    return _profile
```

Single-user local app — module-level state is correct. No auth, no concurrency concerns.

### API Endpoints

| Method | Path | Request Body | Response | Errors |
|--------|------|-------------|----------|--------|
| GET | `/health` | — | `{"status": "ok"}` | — |
| GET | `/api/rankings` | — | Full profile dict | — |
| POST | `/api/rankings/save` | — | `{"saved": true}` | 500 on disk error |
| POST | `/api/rankings/seed` | — | Full profile dict | 500 if no 2025 data |
| GET | `/api/rankings/{position}` | — | `list[dict]` | 404 invalid position |
| POST | `/api/rankings/{position}/reorder` | `ReorderRequest` | `list[dict]` | 400 rank out of bounds |
| POST | `/api/rankings/{position}/add` | `AddPlayerRequest` | `list[dict]` | 400 validation errors |
| DELETE | `/api/rankings/{position}/{rank}` | — | `list[dict]` | 404 rank not found |
| PUT | `/api/rankings/{position}/{rank}/notes` | `NotesRequest` | `dict` (player) | 404 rank not found |

### Import Changes in Moved Utils

The three utils files use `from utils.constants import ...` internally. Since they're moved to `backend/utils/` and `backend/` is on the Python path, these imports work unchanged.

**Critical change**: `data_loader.py` currently imports `streamlit` for `@st.cache_data` and `st.warning`/`st.error`. These must be removed:
- Remove `@st.cache_data` decorator (not needed — FastAPI handles caching differently)
- Replace `st.warning(...)` / `st.error(...)` with `logging.warning(...)` / `logging.error(...)`
- Remove `import streamlit as st`

Similarly, `rankings.py` uses `st.error` and `st.warning` — replace with `logging`.

---

## Implementation Steps

### Step 1: Update `requirements.txt`
**Files**: `requirements.txt`

Replace contents:
```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
pandas>=2.0.0
pytest>=8.0.0
pytest-cov>=5.0.0
ruff>=0.4.0
```

Run `pip install -r requirements.txt`.

**Validation**:
```bash
pip install -r requirements.txt
python -c "import fastapi; import uvicorn; print('OK')"
```
- [ ] Install succeeds
- [ ] Imports work

---

### Step 2: Move Utils to `backend/utils/`
**Files**: Create `backend/`, `backend/__init__.py`, `backend/utils/__init__.py`, move 3 utils files

1. Create directory structure: `backend/`, `backend/utils/`, `backend/routers/`
2. Create empty `__init__.py` in each
3. Copy `app/utils/data_loader.py` → `backend/utils/data_loader.py`
4. Copy `app/utils/rankings.py` → `backend/utils/rankings.py`
5. Copy `app/utils/constants.py` → `backend/utils/constants.py`
6. In `backend/utils/data_loader.py`:
   - Remove `import streamlit as st`
   - Remove `@st.cache_data` decorator from `load_all_players()`
   - Replace `st.warning(...)` with `logging.warning(...)`
   - Replace `st.error(...)` with `logging.error(...)`
   - Add `import logging` at top
7. In `backend/utils/rankings.py`:
   - Remove `import streamlit as st`
   - Replace `st.warning(...)` with `logging.warning(...)`
   - Replace `st.error(...)` with `logging.error(...)`
   - Add `import logging` at top

**Do NOT delete `app/` yet** — keep it until all tests pass from the new location.

**Validation**:
```bash
cd backend && python -c "from utils.constants import POSITIONS; print(POSITIONS)"
cd backend && python -c "from utils.rankings import SEED_LIMITS; print(SEED_LIMITS)"
```
- [ ] Imports resolve from `backend/` context
- [ ] No streamlit imports remain in backend/utils/

---

### Step 3: Update Test Configuration
**Files**: `tests/conftest.py`

Update `sys.path` to point at `backend/` instead of `app/`:

```python
"""Pytest configuration — add backend/ to sys.path."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
```

Update test files: remove `streamlit` mocking.
- `tests/test_data_loader.py`: Remove `patch("streamlit.warning")`, `patch("streamlit.error")`, `patch("streamlit.cache_data", ...)` — these are no longer needed since the backend utils don't import streamlit.
- `tests/test_rankings.py`: Same — remove all streamlit patches.

**Validation**:
```bash
pytest tests/ -v
```
- [ ] All 43 tests pass (8 data_loader + 27 rankings + 8 history — history tests may need removal or skip)
- [ ] No streamlit import errors

---

### Step 4: Create FastAPI App
**Files**: `backend/main.py`

```python
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import rankings

app = FastAPI(title="FF Draft Room API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rankings.router, prefix="/api")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

**Validation**:
```bash
ruff check backend/main.py
```
- [ ] No lint errors
- [ ] File under 500 lines

---

### Step 5: Create Rankings Router
**Files**: `backend/routers/rankings.py`

Implement all 8 endpoints as specified in the init:

1. Module-level `_profile` state with `get_profile()` lazy loader
2. Position validation helper using `POSITIONS` from constants
3. `GET /rankings` — return full profile
4. `POST /rankings/save` — call `save_rankings()`, handle failure
5. `POST /rankings/seed` — re-seed from CSV, replace in-memory profile
6. `GET /rankings/{position}` — return position players, 404 on invalid
7. `POST /rankings/{position}/reorder` — swap players, 400 on bad ranks
8. `POST /rankings/{position}/add` — validate, add, 400 on errors
9. `DELETE /rankings/{position}/{rank}` — delete, 404 on missing rank
10. `PUT /rankings/{position}/{rank}/notes` — update notes, 404 on missing

Pydantic models: `ReorderRequest`, `AddPlayerRequest`, `NotesRequest`

Error responses use `HTTPException` with appropriate status codes.

**Validation**:
```bash
ruff check backend/routers/rankings.py
```
- [ ] No lint errors
- [ ] File under 500 lines

---

### Step 6: Start Server & Curl Verification
**Commands**:

Start the server:
```bash
uvicorn backend.main:app --reload --port 8000
```

Run curl verification (from init spec):
```bash
BASE="http://localhost:8000/api"

curl -s http://localhost:8000/health | python3 -m json.tool
curl -s $BASE/rankings | python3 -m json.tool | head -20
curl -s $BASE/rankings/QB | python3 -m json.tool | head -30
curl -s -X POST $BASE/rankings/QB/reorder \
  -H "Content-Type: application/json" \
  -d '{"rank_a":1,"rank_b":2}' | python3 -m json.tool | head -10
curl -s -X POST $BASE/rankings/QB/add \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Player","team":"TST","tier":1}' | python3 -m json.tool | head -10
curl -s -X PUT $BASE/rankings/QB/1/notes \
  -H "Content-Type: application/json" \
  -d '{"notes":"Elite arm talent"}' | python3 -m json.tool
curl -s -X DELETE $BASE/rankings/QB/31 | python3 -m json.tool | head -10
curl -s -X POST $BASE/rankings/save | python3 -m json.tool
```

**Validation**:
- [ ] All 8 endpoints return expected responses
- [ ] Error cases return correct status codes (400, 404, 500)

---

### Step 7: Clean Up Old Streamlit Files
**Files**: Remove Streamlit-specific files

After all tests pass and endpoints verified:
1. Remove `app/pages/` directory (all Streamlit pages)
2. Remove `app/components/` directory
3. Remove `app/main.py`
4. Remove `.streamlit/config.toml`
5. Keep `app/utils/` temporarily if any tests still reference it, otherwise remove
6. Remove `tests/test_history.py` (history page tests — Streamlit-specific)

**Validation**:
```bash
pytest tests/ -v
ruff check backend/ tests/
```
- [ ] All remaining tests pass
- [ ] No orphaned imports

---

### Step 8: Final Integration Check
**Commands**:
```bash
pytest tests/ --cov=backend --cov-report=term-missing
ruff check backend/ tests/
uvicorn backend.main:app --reload  # manual smoke test
```

**Validation**:
- [ ] All tests pass, coverage ≥ 80% for `backend/utils/`
- [ ] Zero lint errors
- [ ] Server starts cleanly
- [ ] All curl checks pass
- [ ] All files under 500 lines
- [ ] No debug output remaining
- [ ] Commit: `feat: add FastAPI backend with REST API for rankings operations`

---

## Testing Requirements

### Unit Tests (existing — path updated)
```
tests/test_data_loader.py  — 8 tests (unchanged logic, streamlit patches removed)
tests/test_rankings.py     — 27 tests (unchanged logic, streamlit patches removed)
```

### API Integration Tests (curl)
```
GET  /health                              → {"status": "ok"}
GET  /api/rankings                        → profile with players array
GET  /api/rankings/QB                     → 30 player dicts
GET  /api/rankings/INVALID                → 404
POST /api/rankings/QB/reorder {1,2}       → swapped players
POST /api/rankings/QB/reorder {99,100}    → 400
POST /api/rankings/QB/add valid           → player added
POST /api/rankings/QB/add empty name      → 400
POST /api/rankings/QB/add duplicate       → 400
DELETE /api/rankings/QB/1                 → player removed
DELETE /api/rankings/QB/999               → 404
PUT  /api/rankings/QB/1/notes             → notes updated
PUT  /api/rankings/QB/999/notes           → 404
POST /api/rankings/save                   → {"saved": true}
POST /api/rankings/seed                   → re-seeded profile
```

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pip install -r requirements.txt` | Installs without errors | ☐ |
| 2 | `uvicorn backend.main:app --reload` | Server starts at :8000 | ☐ |
| 3 | `curl localhost:8000/health` | `{"status":"ok"}` | ☐ |
| 4 | `curl localhost:8000/api/rankings` | Full profile JSON | ☐ |
| 5 | `curl localhost:8000/api/rankings/QB` | 30 QB players | ☐ |
| 6 | `curl localhost:8000/api/rankings/K` | 404 error | ☐ |
| 7 | POST reorder QB rank 1↔2 | Players swapped | ☐ |
| 8 | POST add player to QB tier 1 | Player added, ranks updated | ☐ |
| 9 | POST add duplicate name | 400 error | ☐ |
| 10 | DELETE QB rank 31 (test player) | Player removed | ☐ |
| 11 | PUT notes on QB rank 1 | Notes updated, returned | ☐ |
| 12 | POST save | `{"saved":true}`, file on disk updated | ☐ |
| 13 | POST seed | Profile re-seeded from CSV | ☐ |
| 14 | `pytest tests/ -v` | All tests pass | ☐ |
| 15 | `ruff check backend/ tests/` | Zero errors | ☐ |

---

## Error Handling

| Error | Cause | Response |
|-------|-------|----------|
| Invalid position | Path param not in QB/RB/WR/TE | 404 `{"detail": "Invalid position: X"}` |
| Rank out of bounds | Rank doesn't exist in position | 400/404 `{"detail": "Rank N not found in POS"}` |
| Duplicate player name | Case-insensitive match on add | 400 `{"detail": "NAME already exists in POS"}` |
| Empty name/team | Blank fields on add | 400 `{"detail": "Name and team are required"}` |
| Save disk error | IOError on write | 500 `{"detail": "Save failed: reason"}` |
| No 2025 CSV data | Missing files on seed | 500 `{"detail": "No 2025 data found in data/players/"}` |

---

## Open Questions

None — all resolved in the init spec.

---

## Rollback Plan

1. `git revert <commit>` — revert the FastAPI commits
2. Restore `app/` from git history if deleted
3. Revert `requirements.txt` to include streamlit
4. Revert `tests/conftest.py` to point at `app/`

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Init spec defines every endpoint, request/response shape, error code |
| Feasibility | 10 | Standard FastAPI patterns, wrapping existing tested functions |
| Completeness | 9 | All endpoints, tests, file moves covered. Minor: may need httpx for pytest API tests (future) |
| Alignment | 10 | Fully consistent with ADR-002, 003, 005, 006 |
| **Average** | **9.75** | |

---

## Notes

- **Streamlit removal from utils**: The biggest gotcha is removing `@st.cache_data` and `st.warning`/`st.error` from the moved utils. Replace with `logging` — straightforward but must be done carefully.
- **Test patches**: All `@patch("streamlit.warning")` etc. in test files must be removed since the backend utils no longer import streamlit.
- **`app/` cleanup**: Keep `app/` until tests pass from `backend/`, then delete. Don't delete prematurely.
- **conftest.py**: The single line change from `app/` to `backend/` is what makes all 43 tests work from the new location.
- **History tests**: `tests/test_history.py` tests the Streamlit history page — these should be removed since the page is retired.
- **Python 3.9**: Continue using `from __future__ import annotations` in all new backend files.
