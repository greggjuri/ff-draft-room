# Generate PRP

Generate a comprehensive Project Requirement Plan (PRP) for a feature.

## Arguments
- `$ARGUMENTS` - Path to initial file (e.g., `initials/NN-init-feature-name.md`)

## Instructions

You are generating a PRP for the **FF Draft Room** project — a single-user FastAPI + React fantasy football draft tool. Local dev uses LocalStorage; production runs on AWS EC2 + S3 + Cognito (ADRs 002, 006, 007, 008).

### Step 1: Gather Context

Read in parallel:
1. `CLAUDE.md` — Coding conventions, file layout, import rules, environment matrix
2. `docs/PLANNING.md` — Architecture, API design, data model, dev phases
3. `docs/DECISIONS.md` — All ADRs. Note especially: ADR-002 (JSON persistence), ADR-006 (FastAPI+React, supersedes Streamlit), ADR-008 (S3 storage), ADR-010 (Fantasy Footballers seed)
4. `docs/TASK.md` — Current sprint and recently completed PRPs
5. `docs/TESTING.md` — Testing standards and patterns
6. The init spec at `$ARGUMENTS`
7. A recent similar PRP under `prps/` for style reference
8. `prps/templates/prp-template.md` — Section structure

### Step 2: Read the Initial File

At `$ARGUMENTS`:
1. Understand the feature requirements
2. Verify all open questions are answered or flagged
3. Identify integration points (backend utils, routers, frontend components, data files)
4. Compare the init's enumerated "Files Touched" against what the change actually needs (renames, downstream callsites, stale references in files you're already editing). If extras are required, plan a **"Scope Expansion vs. Init"** section — never silently expand scope.

### Step 3: Research Codebase

1. `backend/utils/` — existing utilities to reuse or extend
2. `backend/routers/rankings.py` — API routes; named routes register **before** `/{position}` to avoid path-param matching
3. `backend/middleware/auth.py` — Cognito JWT (production only)
4. `frontend/src/components/` — existing React component patterns + CSS files
5. `frontend/src/api/rankings.js` — All fetch() calls live here, never in components
6. `tests/` — existing test patterns; `conftest.py` provides `storage` fixture backed by `LocalStorage(tmp_path)`
7. `data/players/` — Fantasy Footballers Podcast CSVs (read-only seed data)

### Step 4: Generate PRP

Create `prps/NN-prp-{feature-slug}.md` using `prps/templates/prp-template.md`. (Number matches the init's number.)

Fill in all sections with FF Draft Room specifics:
1. **Overview** — Clear problem statement + proposed solution
2. **Success Criteria** — Measurable, testable outcomes. Include:
   - `pytest tests/ -q` passes (target count after migration)
   - `ruff check backend/ tests/` clean
   - `cd frontend && npx vite build` succeeds (if frontend touched)
   - Backend starts: `uvicorn backend.main:app --reload`
3. **Context** — Reference specific ADRs and existing files
4. **Files to Modify** — Explicit list; if expanding beyond init, add a **"Scope Expansion vs. Init"** subsection with **Default chosen** + opt-out path
5. **Technical Specification** — Function signatures (with `from __future__ import annotations`), Pydantic request/response models, React component props, design tokens
6. **Implementation Steps** — Ordered, atomic, with exact file paths and validation commands per step
7. **Testing Requirements** — Unit tests for `backend/utils/`, API curl tests, manual browser tests
8. **Integration Test Plan** — Table of curl + browser steps with expected outcomes
9. **Error Handling** — Missing files, bad JSON, validation errors at API boundary, 404/400/500 expected paths
10. **Open Questions** — Block on anything unclear; otherwise list with defaults
11. **Rollback Plan** — `git revert <sha>`; note any S3 / on-disk JSON cleanup needed

### Step 5: Score Confidence

Score 1-10 on each dimension:
- **Clarity**: Are requirements unambiguous? Exact file paths, function signatures, before/after diffs?
- **Feasibility**: Compatible with FastAPI + React stack, single-user model, JSON storage, local-vs-prod parity?
- **Completeness**: All files (including downstream callsites), tests, and validation steps covered?
- **Alignment**: Consistent with all ADRs (especially ADR-002, ADR-006, ADR-008, ADR-010)?

**If average < 7**: List specific concerns, ask clarifying questions, do NOT proceed to /execute-prp.

### Step 6: Output

1. Create PRP file at `prps/NN-prp-{feature-slug}.md`
2. Auto-commit + push (per repo memory — no confirmation needed)
3. Report file path
4. Display confidence scores table
5. List any open questions, scope-expansion decisions, or concerns

## Quality Checklist

Before completing:
- [ ] Every step has specific file paths and a `Validation:` block
- [ ] Steps are atomic and individually validatable
- [ ] Unit tests cover `backend/utils/` functions (not API routes — those go in curl tests)
- [ ] Integration test plan uses real commands: `pytest tests/ -q`, `curl` against `localhost:8000`, browser at `localhost:5173`
- [ ] No ADRs contradicted (especially: no external APIs at runtime, no database, no Streamlit, no multi-user)
- [ ] Backend imports are relative to `backend/` (e.g., `from utils.constants import POSITIONS` — not `from backend.utils...`)
- [ ] Files >500 lines flagged with split plan
- [ ] Rollback plan exists
- [ ] If init's Files Touched is incomplete, expansion is surfaced explicitly

## Example Usage

```
/generate-prp initials/17-init-fantasy-footballers-import.md
/generate-prp initials/18-init-untrack-rankings-and-doc-cleanup.md
```
