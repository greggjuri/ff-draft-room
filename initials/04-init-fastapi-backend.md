# 04-init-fastapi-backend.md — FastAPI Backend

## Feature Summary
Replace the Streamlit app with a FastAPI backend that exposes all rankings
operations as a REST API. Port `app/utils/` to `backend/utils/` unchanged.
Wire up all 8 API endpoints. Verify each with curl before frontend work begins.

After this init: `uvicorn backend.main:app --reload` runs at localhost:8000,
all endpoints respond correctly, all existing tests pass from their new location.

## Status
- [x] Open questions resolved
- [x] Ready for PRP generation

---

## Requirements

### 1. Project Structure Changes

**Move** (not copy — update imports if needed):
```
app/utils/data_loader.py  → backend/utils/data_loader.py
app/utils/rankings.py     → backend/utils/rankings.py
app/utils/constants.py    → backend/utils/constants.py
```

**Create**:
```
backend/__init__.py
backend/main.py
backend/routers/__init__.py
backend/routers/rankings.py
backend/utils/__init__.py
```

**Update**:
```
requirements.txt   — add fastapi, uvicorn[standard]
tests/             — update sys.path to point at backend/ not app/
```

**Leave untouched**:
```
data/players/      — CSVs unchanged
data/rankings/     — JSON profiles unchanged
tests/test_data_loader.py
tests/test_rankings.py
```

### 2. Dependencies (`requirements.txt`)

Add:
```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
```

Keep existing:
```
pandas>=2.0.0
pytest>=8.0.0
pytest-cov>=5.0.0
ruff>=0.4.0
```

Remove:
```
streamlit
plotly
```

### 3. `backend/main.py`

```python
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import rankings

app = FastAPI(title="FF Draft Room API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rankings.router, prefix="/api")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

### 4. `backend/routers/rankings.py`

All routes prefixed `/api` (from main.py). Full prefix = `/api/rankings/...`

**State**: rankings profile held in module-level variable, loaded on startup.
```python
_profile: dict | None = None

def get_profile() -> dict:
    global _profile
    if _profile is None:
        df = load_all_players()
        _profile = load_or_seed(df)
    return _profile
```

**Endpoints**:

```
GET  /rankings
```
Returns full profile dict.

```
POST /rankings/save
```
Saves current in-memory profile to disk. Returns `{"saved": true}`.

```
POST /rankings/seed
```
Re-seeds from CSV data (nuclear reset). Overwrites in-memory profile and disk.
Returns seeded profile.

```
GET  /rankings/{position}
```
Returns list of player dicts for that position, sorted by `position_rank`.
404 if position not in `["QB", "RB", "WR", "TE"]`.

```
POST /rankings/{position}/reorder
Body: { "rank_a": int, "rank_b": int }
```
Swaps two players. Returns updated position player list.
400 if ranks out of bounds.

```
POST /rankings/{position}/add
Body: { "name": str, "team": str, "tier": int }
```
Adds player at end of specified tier. Returns updated position player list.
400 if name empty, team empty, or name already exists in position (case-insensitive).

```
DELETE /rankings/{position}/{rank}
```
Deletes player at given rank. Returns updated position player list.
404 if rank doesn't exist.

```
PUT /rankings/{position}/{rank}/notes
Body: { "notes": str }
```
Updates player notes. Returns updated player dict.
404 if rank doesn't exist.

**Pydantic models**:
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

### 5. Import Updates in `backend/utils/`

All three utils files use relative imports — no changes needed if moved as-is.
Verify: `from utils.constants import POSITIONS` works from `backend/` context.

### 6. Test Path Updates

`tests/conftest.py` currently adds `app/` to `sys.path`. Update to `backend/`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
```

No test logic changes — only the path.

---

## Success Criteria

1. `pip install -r requirements.txt` — no errors
2. `uvicorn backend.main:app --reload` starts at localhost:8000
3. `GET /health` → `{"status": "ok"}`
4. `GET /api/rankings` → full profile JSON
5. `GET /api/rankings/QB` → 30 QB players
6. `POST /api/rankings/QB/reorder` `{"rank_a":1,"rank_b":2}` → players swapped
7. `POST /api/rankings/QB/add` `{"name":"Test Player","team":"TST","tier":1}` → player added
8. `DELETE /api/rankings/QB/1` → player removed, ranks renumbered
9. `PUT /api/rankings/QB/1/notes` `{"notes":"Top target"}` → notes updated
10. `POST /api/rankings/save` → `{"saved":true}`, file updated on disk
11. `pytest tests/ -v` → all 43 tests pass
12. `ruff check backend/ tests/` → zero errors

---

## Curl Verification Script

Claude Code should run these after implementation to verify all endpoints:

```bash
BASE="http://localhost:8000/api"

# Health
curl -s http://localhost:8000/health | python3 -m json.tool

# Load rankings
curl -s $BASE/rankings | python3 -m json.tool | head -20

# Get QB list
curl -s $BASE/rankings/QB | python3 -m json.tool | head -30

# Reorder QB rank 1 and 2
curl -s -X POST $BASE/rankings/QB/reorder \
  -H "Content-Type: application/json" \
  -d '{"rank_a":1,"rank_b":2}' | python3 -m json.tool | head -10

# Add a player
curl -s -X POST $BASE/rankings/QB/add \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Player","team":"TST","tier":1}' | python3 -m json.tool | head -10

# Update notes
curl -s -X PUT $BASE/rankings/QB/1/notes \
  -H "Content-Type: application/json" \
  -d '{"notes":"Elite arm talent"}' | python3 -m json.tool

# Delete player at rank 1
curl -s -X DELETE $BASE/rankings/QB/31 | python3 -m json.tool | head -10

# Save
curl -s -X POST $BASE/rankings/save | python3 -m json.tool
```

---

## Error Handling

| Scenario | Response |
|----------|----------|
| Invalid position (e.g. `/api/rankings/K`) | 404 `{"detail": "Invalid position: K"}` |
| Rank out of bounds | 400 `{"detail": "Rank {n} not found in {position}"}` |
| Duplicate player name on add | 400 `{"detail": "{name} already exists in {position}"}` |
| Empty name or team on add | 400 `{"detail": "Name and team are required"}` |
| Save fails (disk error) | 500 `{"detail": "Save failed: {reason}"}` |
| CSV files missing on seed | 500 `{"detail": "No 2025 data found in data/players/"}` |

---

## Open Questions

*All resolved.*

1. ~~In-memory state vs load-per-request?~~ → Module-level `_profile`, loaded once on
   first request. Save flushes to disk. Simple and correct for single-user local app.
2. ~~Auth?~~ → None. Local only.
3. ~~CORS origins?~~ → `localhost:5173` only (Vite dev server).

---

## Out of Scope for This Init

- React frontend — `05-init-react-frontend.md`
- K and D/ST positions — after migration complete
- Multiple profiles — Phase 1c
- WebSocket live updates — Phase 2
