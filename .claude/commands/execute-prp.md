# Execute PRP

Execute a Project Requirement Plan step-by-step.

## Arguments
- `$ARGUMENTS` - Path to PRP file (e.g., `prps/NN-prp-feature-name.md`)

## Instructions

You are executing a PRP for the **FF Draft Room** project — a single-user FastAPI + React fantasy football draft tool. Local dev uses LocalStorage; production runs on AWS EC2 + S3 + Cognito.

### Step 0: Pre-flight Checks

Before starting:
1. Read `CLAUDE.md` for conventions
2. Read the PRP at `$ARGUMENTS` completely
3. Verify all dependencies (previous PRPs) are complete via `docs/TASK.md`
4. Check confidence score ≥ 7 (if not, stop and report)
5. Activate venv: `source .venv/bin/activate`
6. Verify baseline is green: `pytest tests/ -q && ruff check backend/ tests/`

### Step 1: Execute Implementation Steps

For each implementation step in the PRP:

1. **Announce**: State which step you're starting (one sentence)
2. **Implement**: Make the edits per the PRP. Follow conventions in CLAUDE.md.
3. **Validate**: Run the step's `Validation:` block
4. **Track**: Mark the step's task `completed` (via TaskCreate/TaskUpdate) before moving on

```bash
# Typical validation per step
pytest tests/test_<file>.py -v       # Targeted tests
ruff check backend/ tests/           # Lint
```

Defer the **single atomic feature commit** until all steps validate, per CLAUDE.md ("Commit after every feature — atomic, working commits"). Don't commit per-step.

### Step 2: Stack-Specific Patterns

**Backend (FastAPI + Pandas + StorageBackend)**

```python
# Every backend file needs this at the top (Python 3.9 union syntax)
from __future__ import annotations

# Imports are relative to backend/, not from backend/
from utils.constants import POSITIONS
from utils.rankings import load_or_seed
from utils.storage import StorageBackend, LocalStorage

# StorageBackend is dependency-injected; never read/write filesystem directly
def some_op(profile: dict, storage: StorageBackend | None = None) -> dict:
    if storage is None:
        storage = _default_storage()
    ...

# Pydantic models for request bodies
class ReorderRequest(BaseModel):
    rank_a: int
    rank_b: int

# Named routes MUST register before /{position} routes — FastAPI matches greedily
@router.get("/profiles")        # OK — registered before /{position}
@router.get("/{position}")
```

**Frontend (React + Vite + plain CSS)**

```jsx
// All fetch() calls live in frontend/src/api/rankings.js — never in components
import { getRankings, savePlayer } from '../api/rankings'

// AuthContext provides token; api functions handle the Authorization header
const { user, token } = useAuth()

// Plain CSS with design tokens — no framework, no CSS-in-JS
// Per-component .css file (e.g., PlayerRow.jsx + PlayerRow.css)
```

**Tests**

```python
# conftest.py provides a storage fixture (LocalStorage backed by tmp_path)
def test_something(storage):
    save_rankings(profile, storage=storage)
    assert storage.exists("default.json")
```

### Step 3: Handle Failures

If a step fails:
1. **Diagnose**: Check pytest output / uvicorn logs / vite build output
2. **Fix**: Minimal change to resolve
3. **Document**: Note the fix in the final commit body (not in code comments)
4. **Continue**: Only proceed when the step validates

Common failure modes:
- **FastAPI route shadowing**: named route registered after `/{position}` — reorder routes
- **Pydantic validation 422**: request body shape mismatch — check the Pydantic model and the frontend `fetch()` payload
- **CORS errors in browser**: backend not running or wrong port — backend on `:8000`, vite dev server on `:5173` proxies `/api/*`
- **Cognito JWT failures in production only**: middleware is conditional via env var — local dev has no auth
- **`from utils...` ImportError**: someone used `from backend.utils...` — fix to relative

If unable to proceed: report blocker clearly, suggest options, ask for guidance.

### Step 4: Run Integration Tests

After all implementation steps:

```bash
# Terminal 1 — Backend
source .venv/bin/activate
uvicorn backend.main:app --reload   # localhost:8000

# Terminal 2 — Frontend (if frontend touched)
cd frontend && npm run dev          # localhost:5173
```

Execute the PRP's Integration Test Plan table — curl steps against `localhost:8000`, browser steps at `localhost:5173`. Record pass/fail. Fix failures before committing.

For UI-only changes you can verify in a browser, **actually open the browser**. Type checks and tests verify code correctness, not feature correctness. If you can't browse, say so explicitly rather than claim success.

### Step 5: Final Validation

```bash
pytest tests/ --cov=backend --cov-report=term-missing
ruff check backend/ tests/
cd frontend && npx vite build      # If frontend touched
```

Verify:
- [ ] All tests pass (count matches PRP's target — flag any regression)
- [ ] Coverage maintained for `backend/utils/`
- [ ] Ruff clean
- [ ] Vite build clean (if frontend touched)
- [ ] All Success Criteria from PRP met
- [ ] No `print()` / debug `console.log` left in code
- [ ] No file over 500 lines (split if needed)

### Step 6: Commit + Push

Per repo convention (CLAUDE.md + memory):
- **One atomic feature commit** with all production code + tests + init file
- **Commit trailer**: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
- **Use HEREDOC** for the message to preserve formatting
- **Push to origin/main** automatically — no confirmation needed
- **Do not stage** `data/rankings/*.json` — gitignored as of PRP-018; if something landed there as a `D` or `M`, restore from git before commit unless the PRP explicitly says otherwise
- Include the init spec (`initials/NN-init-*.md`) in the same commit if it's untracked — they're tracked by convention

### Step 7: Update Documentation

In a **separate follow-up commit** (not bundled with the feature):

1. Update `docs/TASK.md`:
   - Move task to "Recently Completed" with a 3–6 bullet summary
   - Update the "Last updated" line at the bottom
2. If new architectural decisions were made: add ADR to `docs/DECISIONS.md` (or note as a follow-up if user prefers to author via Claude.ai)

Auto-commit + push this docs change too.

### Step 8: Report Completion

```
## PRP Execution Complete

**PRP**: prps/NN-prp-{feature}.md
**Status**: Complete / Partial / Blocked

### Commits Made
- {hash}: {message}
- {hash}: {message}

### Tests
- Unit: X passing (delta vs. baseline: ±N)
- API curl: X/Y passing
- Manual UI: X/Y passing (or "not run, no browser available")

### Success Criteria
- [x] Criterion 1
- [x] Criterion 2
- [ ] Criterion 3 (explain if incomplete)

### Issues Encountered
{Specific issues + resolutions, not generic narration}

### Follow-up Items
{What's left for TASK.md or future PRPs — be specific}
```

## Commit Message Format

```
feat: add roster panel for draft mode
fix: handle missing CSV file gracefully in data_loader
refactor: extract player table into reusable component
test: add unit tests for set_player_tier
docs: update PLANNING.md with new API routes
chore: add data/rankings/*.json to .gitignore
```

## Quality Standards

- **No file over 500 lines** — split if approaching
- **Tests for utils** — preserve existing coverage on `backend/utils/`
- **Atomic feature commits** — app must work after every commit on `main`
- **No hardcoded credentials** — IAM role on EC2, Cognito IDs are public, JWTs via Authorization header only
- **Backend imports relative to `backend/`** — `from utils.X import Y`, not `from backend.utils.X`
- **`from __future__ import annotations`** at the top of every backend `.py` file (Python 3.9 union syntax)

## Emergency Stop

Stop and report before proceeding if you encounter:
- A need to re-introduce Streamlit (violates ADR-006)
- A need for an external API call at runtime beyond AWS S3 / Cognito (violates ADR-002/008)
- A database requirement (violates ADR-002 — JSON only)
- A multi-user requirement (violates ADR-007 — single user)
- A contradiction with existing ADRs without a new ADR
- File approaching 500 lines without a clear split plan
- A scope expansion beyond what the PRP describes — flag it before doing the work

## Notes

- App runs on Debian (local dev) and AWS EC2 (Amazon Linux) — Python 3.9+
- The app is personal/single-user — no auth in dev, Cognito JWT in prod
- Data CSVs in `data/players/` are read-only seed source — never modify them
- Rankings JSON in `data/rankings/` is gitignored runtime state — local dev only; production reads/writes S3
- Frontend has zero unit tests — manual browser verification is the test for UI changes
