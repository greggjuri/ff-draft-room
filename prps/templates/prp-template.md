# PRP Template

## PRP-XXX: {Feature Name}

**Created**: {YYYY-MM-DD}
**Initial**: `initials/NN-init-{feature}.md`
**Status**: Draft/Ready/In Progress/Complete

---

## Overview

### Problem Statement
{What problem are we solving? Copy/adapt from init spec.}

### Proposed Solution
{High-level description of what we're building. Reference the stack
explicitly: backend changes, frontend changes, infra changes.}

### Success Criteria
- [ ] {Criterion 1 — testable}
- [ ] {Criterion 2 — testable}
- [ ] All unit tests pass (`pytest tests/ -q`) — target count: {N}
- [ ] Lint clean (`ruff check backend/ tests/`)
- [ ] Backend starts: `uvicorn backend.main:app --reload`
- [ ] Frontend builds (if touched): `cd frontend && npx vite build`

---

## Context

### Related Documentation
- `docs/PLANNING.md` — Architecture, data model, API design
- `docs/DECISIONS.md` — Relevant ADRs (cite specific numbers)
- `initials/NN-init-{feature}.md` — Full spec

### Dependencies
- **Required**: {PRPs that must be complete first, or "none"}
- **Optional**: {Features that enhance but aren't required}

### Files to Modify / Create
```
backend/utils/{file}.py             # MODIFY/CREATE — Description
backend/routers/{file}.py           # MODIFY — Description
frontend/src/components/{X}.jsx     # MODIFY/CREATE — Description
frontend/src/components/{X}.css     # MODIFY/CREATE — Description
frontend/src/api/rankings.js        # MODIFY — Add fetch wrappers
tests/test_{name}.py                # MODIFY/CREATE — Unit tests
initials/NN-init-{feature}.md       # Include in commit if untracked
```

### Scope Expansion vs. Init (if applicable)
{If the init's Files Touched list is incomplete, list the extras here with
**Why** and a **Default chosen** + opt-out path. Never silently expand.
Omit this section if scope matches the init exactly.}

### Files NOT Modified (intentional)
```
{Path}    # Reason
```

---

## Technical Specification

### Backend — Data / Storage Model
```python
# Profile / player / request body shapes
# Reference: ADR-002 (JSON persistence), ADR-008 (StorageBackend)
```

### Backend — New / Modified Utilities
```python
# backend/utils/{file}.py
from __future__ import annotations

def function_name(
    profile: dict,
    storage: StorageBackend | None = None,
) -> dict:
    """One-line docstring."""
    ...
```

### Backend — API Routes
```python
# backend/routers/rankings.py
# Named routes MUST be registered before /{position} to avoid path-param shadowing
class RequestBody(BaseModel):
    field: type

@router.post("/{position}/action")
def action(request: Request, position: str, body: RequestBody) -> dict:
    ...
```

### Frontend — Components
```
frontend/src/components/{Name}.jsx
  Props: { rankings, onChange, ... }
  Internal state: useState() for ...
  CSS file: {Name}.css
```

### Frontend — API Calls
```js
// frontend/src/api/rankings.js — All fetch() lives here
export async function newEndpoint(arg, token) { ... }
```

### Design Tokens (if UI-touching)
- Background: `#0D1B2A`
- Primary accent (Honolulu Blue): `#0076B6`
- Tier name boxes: odd `#1A3A5C`, even `#2A5A8C`, hover `#0076B6`
- Draft "mine": `#1A7A3A` bg / `#00C805` dot
- Draft "other": `#6B2FA0` bg / `#9B59B6` dot
- Font: monospace everywhere

---

## Implementation Steps

### Step 1: {First Step Title}
**Files**: `backend/utils/{file}.py`, `tests/test_{file}.py`

{Detailed description.}

```python
# Key code pattern (illustrative, not exhaustive)
```

**Validation**:
```bash
pytest tests/test_{file}.py -v
ruff check backend/utils/{file}.py
```
- [ ] Tests pass
- [ ] No lint errors

---

### Step 2: {Second Step Title}
**Files**: `backend/routers/{file}.py`

{Detailed description.}

**Validation**:
```bash
uvicorn backend.main:app --reload &
curl -s -X POST http://localhost:8000/api/rankings/... \
  -H "Content-Type: application/json" -d '{"key":"value"}'
pkill -f "uvicorn backend.main"
```
- [ ] Endpoint returns expected JSON
- [ ] Error cases return correct HTTP codes

---

### Step 3: {Frontend Step Title}
**Files**: `frontend/src/components/{X}.jsx`, `frontend/src/components/{X}.css`

{Detailed description.}

**Validation**:
```bash
cd frontend && npx vite build
# Then manual: cd frontend && npm run dev → open localhost:5173
```
- [ ] Build clean
- [ ] {Specific UI behavior works in browser}

---

### Step N: Full Validation
```bash
pytest tests/ --cov=backend --cov-report=term-missing
ruff check backend/ tests/
cd frontend && npx vite build
```
- [ ] All tests pass, coverage maintained for `backend/utils/`
- [ ] Full manual test checklist from `docs/TESTING.md` completed (if relevant)
- [ ] No `print()` / `console.log()` left in code

---

## Testing Requirements

### Unit Tests (`backend/utils/`)
```
tests/test_{feature}.py:
  - test_{function}_happy_path
  - test_{function}_missing_file
  - test_{function}_invalid_input
  - test_{function}_no_mutation         # Ensure pure / non-mutating
```

### API Tests (curl, manual)
```bash
BASE="http://localhost:8000/api"

curl -s $BASE/rankings/...
curl -s -X POST $BASE/rankings/... -H "Content-Type: application/json" -d '...'
```

### Manual Browser Tests
- {Scenario 1}: {Steps + expected result}
- {Scenario 2}: {Steps + expected result}

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | All pass, target count | ☐ |
| 2 | `ruff check backend/ tests/` | Clean | ☐ |
| 3 | `uvicorn backend.main:app --reload` | Starts, no errors | ☐ |
| 4 | `curl http://localhost:8000/health` | 200 OK | ☐ |
| 5 | {Feature curl test} | {Expected JSON} | ☐ |
| 6 | `cd frontend && npx vite build` | Build clean | ☐ |
| 7 | Browser: `localhost:5173` → {action} | {Expected UI behavior} | ☐ |
| 8 | {Error case} | {Graceful error message} | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| `FileNotFoundError` | Missing CSV / config | Raise from loader; router catches → `HTTPException(500)` |
| Pydantic 422 | Bad request body | FastAPI auto-handles; frontend surfaces inline error |
| 404 from route | Unknown position / rank | `HTTPException(404, detail="...")` |
| Storage write fails | Disk full / S3 perms | Util returns `False`; route returns 500 |
| Cognito JWT invalid (prod only) | Expired token | Middleware returns 401; frontend redirects to login |

---

## Open Questions

- [ ] {Question needing answer before implementation, or "None"}

---

## Rollback Plan

1. `git revert <commit-sha>` on `main`
2. `git push origin main`
3. **Local**: backend reloads automatically (uvicorn `--reload`); frontend `npm run dev` picks up the change
4. **Production** (if deployed): on EC2 run `git pull origin main && ./scripts/deploy.sh`
5. **S3 state cleanup** (if needed): {specify which JSON objects to wipe, or "none — no S3 schema change"}
6. **On-disk JSON cleanup** (if needed): {note — data/rankings/*.json is gitignored since PRP-018}

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | X | Are requirements unambiguous? Exact file paths, function signatures? |
| Feasibility | X | Works within FastAPI + React + JSON storage + single-user constraints? |
| Completeness | X | All files (incl. downstream callsites), tests, validation covered? |
| Alignment | X | Consistent with ADRs (especially 002, 006, 008, 010)? |
| **Average** | **X** | |

{If average < 7, list specific concerns before proceeding}

---

## Notes

{Additional context, scope-tradeoff explanations, file-size considerations}
