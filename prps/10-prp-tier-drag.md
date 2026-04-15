# PRP-010: Draggable Tier Boundaries

**Created**: 2026-04-15
**Initial**: `initials/10-init-tier-drag.md`
**Status**: Complete

---

## Overview

### Problem Statement
Tier boundaries are fixed at seeding time. Moving a player between tiers
requires repeated ▲▼ presses until they cross the boundary — slow and
tedious when reorganizing multiple tiers before a draft.

### Proposed Solution
Render a draggable separator line between adjacent tier groups. Dragging
down promotes the first player of the lower tier into the upper tier.
Dragging up demotes the last player of the upper tier into the lower tier.
Movement snaps one player at a time. A new backend function and endpoint
update the player's `tier` field without changing `position_rank`.

### Success Criteria
- [ ] Draggable separator line between every pair of adjacent tiers
- [ ] Drag down → first player of lower tier moves up one tier
- [ ] Drag up → last player of upper tier moves down one tier
- [ ] `position_rank` values unchanged after tier reassignment
- [ ] Empty tier impossible — drag stops at 1-player limit
- [ ] Separator hidden in Draft Mode
- [ ] Touch drag works (mobile / `ff.jurigregg.com`)
- [ ] Unsaved indicator appears after tier reassignment
- [ ] All 64 existing tests pass
- [ ] New tests: >= 5 unit for `set_player_tier`, >= 3 endpoint tests
- [ ] `ruff check backend/ tests/` — zero errors
- [ ] `cd frontend && npx vite build` — no errors
- [ ] No file exceeds 500 lines

---

## Context

### Related Documentation
- `docs/PLANNING.md` — Architecture, data model, project structure
- `docs/DECISIONS.md` — ADR-002 (JSON), ADR-006 (FastAPI + React)
- `initials/10-init-tier-drag.md` — ADR-009 (Draggable Tier Boundaries)

### Dependencies
- **Required**: All Phase 1b features complete (PRP 04–08), PRP-009 (AWS deploy)
- **None external** — pure frontend/backend feature

### Files to Modify/Create
```
# NEW
frontend/src/components/TierSeparator.jsx   # Draggable tier boundary
frontend/src/components/TierSeparator.css   # Separator styles

# MODIFIED — Backend
backend/utils/rankings.py                   # add set_player_tier()
backend/routers/rankings.py                 # add PUT /{position}/{rank}/tier

# MODIFIED — Frontend
frontend/src/api/rankings.js                # add setPlayerTier()
frontend/src/components/PositionColumn.jsx  # render TierSeparator, measure rows
frontend/src/components/PositionColumn.css  # separator gap layout
frontend/src/components/WarRoom.jsx         # pass onTierMove prop
frontend/src/App.jsx                        # handleTierMove handler

# MODIFIED — Tests
tests/test_rankings.py                      # set_player_tier unit tests

# MODIFIED — Docs
docs/DECISIONS.md                           # add ADR-009
docs/TASK.md                                # update status
```

---

## Technical Specification

### Backend Utility — `set_player_tier()` in `backend/utils/rankings.py`

```python
def set_player_tier(
    profile: dict, position: str, position_rank: int, new_tier: int
) -> dict:
    """Reassign a single player's tier without changing their rank.

    Returns a new profile dict — does not mutate input.
    Raises ValueError if the player is not found.
    """
```

Only changes the `tier` field on one player. No renumbering, no cascading.
Tier boundaries are implicit (gap between adjacent players with different
tier values), so a single field update is sufficient.

### API Endpoint — `PUT /api/rankings/{position}/{rank}/tier`

```python
class SetTierRequest(BaseModel):
    tier: int

@router.put("/{position}/{rank}/tier")
def set_tier(request: Request, position: str, rank: int, body: SetTierRequest):
```

**Validation:**
- `position` must be in `POSITIONS` (404 if not)
- `rank` must exist in position's player list (404 if not)
- `tier` must be a positive integer (422 via Pydantic)
- `tier` must be adjacent to current tier (±1 only) — 400 if not

**Response:** updated list of position players (same as reorder/add/delete).

**Route order:** registered alongside existing `/{position}/{rank}/notes`
— both are sub-routes of `/{position}/{rank}`, so no ordering conflict
with `/{position}`.

### Frontend API — `setPlayerTier()` in `api/rankings.js`

```js
export const setPlayerTier = (position, rank, tier) =>
  request(`${BASE}/${position}/${rank}/tier`, {
    method: 'PUT',
    body: JSON.stringify({ tier })
  })
```

### Frontend Component — `TierSeparator.jsx`

A thin draggable line rendered by `PositionColumn` between adjacent tier groups.

**Props:**
```jsx
<TierSeparator
  position="QB"
  upperTier={1}
  lowerTier={2}
  upperCount={3}       // players in upper tier
  lowerCount={2}       // players in lower tier
  rowHeight={29}       // measured from PlayerRow ref
  onBoundaryMove={fn}  // (position, rank, newTier) => void
  upperPlayers={[...]} // need last player of upper tier
  lowerPlayers={[...]} // need first player of lower tier
/>
```

**Visual design:**
- At rest: `2px` horizontal rule, `#1E3A5F`, centered grip `⠿` in `#0076B6`
- Hover: grip brightens, cursor `ns-resize`
- Dragging: line highlighted `#0076B6`, opacity 0.8

**Drag mechanics:**
- `onMouseDown` starts drag, tracks start Y
- `onMouseMove` accumulates delta; when `|delta| >= rowHeight`:
  - `delta > 0` (down): move first player of lower tier up →
    call `onBoundaryMove(position, lowerPlayers[0].position_rank, upperTier)`
  - `delta < 0` (up): move last player of upper tier down →
    call `onBoundaryMove(position, upperPlayers[upperPlayers.length-1].position_rank, lowerTier)`
  - Reset accumulator
- `onMouseUp` ends drag

**Touch support:** `onTouchStart` / `onTouchMove` / `onTouchEnd` mirrors
mouse handlers using `touches[0].clientY`.

**Empty tier guard:** Before calling `onBoundaryMove`:
- Dragging down: `lowerCount > 1` — lower tier is giving a player to upper,
  must keep at least one
- Dragging up: `upperCount > 1` — upper tier is giving a player to lower,
  must keep at least one

### `PositionColumn.jsx` Changes

1. Add `ref` on the first `PlayerRow` to measure `rowHeight` via
   `useRef` + `useEffect` reading `getBoundingClientRect().height`
2. Render `<TierSeparator>` between each pair of adjacent tier groups
3. Not rendered in Draft Mode (separator checks `isDraft` in parent)
4. New prop: `onTierMove(position, rank, newTier)`

### `WarRoom.jsx` Changes

Pass `onTierMove` prop through to each `PositionColumn`.

### `App.jsx` Changes

New `handleTierMove` handler following the exact same pattern as the
existing `handleReorder` / `handleAdd` / `handleDelete` handlers — call
the API, merge the returned position player list into `rankings` state,
and set dirty.

---

## Implementation Steps

### Step 1: Backend — `set_player_tier()` + tests
**Files**: `backend/utils/rankings.py`, `tests/test_rankings.py`

Add `set_player_tier()` function to `rankings.py`. Add tests:
- `test_set_player_tier_changes_tier` — tier updated correctly
- `test_set_player_tier_does_not_mutate_input` — deep equality check
- `test_set_player_tier_unknown_player` — raises ValueError
- `test_set_player_tier_preserves_rank` — position_rank unchanged
- `test_set_player_tier_does_not_affect_others` — other players unchanged

**Validation:**
```bash
pytest tests/test_rankings.py -v
ruff check backend/utils/rankings.py
```
- [ ] All tests pass
- [ ] No lint errors

---

### Step 2: Backend — API endpoint
**Files**: `backend/routers/rankings.py`

Add `SetTierRequest` model and `PUT /{position}/{rank}/tier` endpoint.
Validate position, rank existence, tier adjacency (±1).

**Validation:**
```bash
ruff check backend/routers/rankings.py
pytest tests/ -q
```
- [ ] Lint clean
- [ ] All tests pass

---

### Step 3: Frontend — API function
**Files**: `frontend/src/api/rankings.js`

Add `setPlayerTier(position, rank, tier)` function following the existing
`request()` pattern with auth headers.

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds

---

### Step 4: Frontend — TierSeparator component
**Files**: `frontend/src/components/TierSeparator.jsx`,
`frontend/src/components/TierSeparator.css`

Create the draggable separator component with mouse and touch support.
Includes empty-tier guards. Not rendered in Draft Mode (parent controls).

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds

---

### Step 5: Frontend — Wire into PositionColumn, WarRoom, App
**Files**: `frontend/src/components/PositionColumn.jsx`,
`frontend/src/components/PositionColumn.css`,
`frontend/src/components/WarRoom.jsx`,
`frontend/src/App.jsx`

1. `PositionColumn`: measure `rowHeight` via ref, render `TierSeparator`
   between tier groups, pass through `onTierMove`
2. `WarRoom`: accept and pass `onTierMove` prop
3. `App`: add `handleTierMove` handler, import `setPlayerTier`, pass to
   `WarRoom`

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds
- [ ] Manual test: start both servers, verify separators render between tiers
- [ ] Manual test: drag separator down → player moves to upper tier
- [ ] Manual test: drag separator up → player moves to lower tier
- [ ] Manual test: touch drag works
- [ ] Manual test: separator hidden in Draft Mode

---

### Step 6: Documentation — ADR-009
**Files**: `docs/DECISIONS.md`, `docs/TASK.md`

Add ADR-009: Draggable Tier Boundaries to `DECISIONS.md`.
Update `TASK.md` to mark 10 as complete.

---

### Step 7: Final Integration Check
**Commands:**
```bash
pytest tests/ --cov=backend --cov-report=term-missing
ruff check backend/ tests/
cd frontend && npx vite build
```

**Validation:**
- [ ] All tests pass (64 existing + ~5 new)
- [ ] Coverage >= 80% for `backend/utils/`
- [ ] Zero lint errors
- [ ] Frontend builds cleanly
- [ ] No file exceeds 500 lines
- [ ] No debug output left

---

## Testing Requirements

### Unit Tests — `tests/test_rankings.py` (additions)
```
test_set_player_tier_changes_tier         — tier updated on target player
test_set_player_tier_does_not_mutate      — input profile unchanged
test_set_player_tier_unknown_player       — raises ValueError
test_set_player_tier_preserves_rank       — position_rank unchanged
test_set_player_tier_does_not_affect_others — other players' tiers unchanged
```

### Manual Browser Tests
- [ ] Separator visible between each pair of adjacent tiers (all 4 columns)
- [ ] Cursor changes to `ns-resize` on hover
- [ ] Drag down one row → first player of lower tier joins upper tier
- [ ] Drag up one row → last player of upper tier joins lower tier
- [ ] Multiple snaps in one drag gesture work correctly
- [ ] Separator stops at 1-player tier (cannot empty a tier)
- [ ] Position ranks unchanged after drag
- [ ] Unsaved indicator appears after drag
- [ ] Save persists the tier changes
- [ ] Separator hidden in Draft Mode
- [ ] Touch drag works on mobile (test at `ff.jurigregg.com`)
- [ ] Search still works after tier changes

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | All tests pass (64 + ~5 new) | ☐ |
| 2 | `ruff check backend/ tests/` | Zero errors | ☐ |
| 3 | `cd frontend && npx vite build` | Build succeeds | ☐ |
| 4 | Start backend + frontend | Both start cleanly | ☐ |
| 5 | Open War Room | Separator lines visible between tier groups | ☐ |
| 6 | Drag QB Tier 1/2 boundary down | First Tier 2 player joins Tier 1 | ☐ |
| 7 | Drag same boundary up | Last Tier 1 player returns to Tier 2 | ☐ |
| 8 | Drag past limit (1 player in tier) | Separator stops, no empty tier | ☐ |
| 9 | Check unsaved indicator | Shows "UNSAVED" after drag | ☐ |
| 10 | Click SAVE | Saves successfully, indicator clears | ☐ |
| 11 | Reload page | Tier changes persisted | ☐ |
| 12 | Switch to Draft Mode | Separators disappear | ☐ |
| 13 | Switch back to War Room | Separators reappear | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| 404 on position | Invalid position in URL | HTTPException, frontend shows error banner |
| 404 on rank | Player not found at that rank | HTTPException, frontend shows error banner |
| 400 non-adjacent tier | Frontend bug sending wrong tier | HTTPException with "must be adjacent" message |
| Network error during drag | Connection lost mid-drag | Drag gesture ends, error banner shown, state rolls back |

---

## Open Questions

None — the init spec is complete:
- Drag direction semantics are clear (down = expand upper tier)
- Empty tier guard logic is specified
- No data model changes needed
- Touch support explicitly required
- Route ordering is not a problem

---

## Rollback Plan

```bash
git revert <commit>
pytest tests/ -q
uvicorn backend.main:app --reload
cd frontend && npm run dev
```

The feature is additive — `set_player_tier` is a new function, the endpoint
is new, and `TierSeparator` is a new component. Revert removes everything
cleanly.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 9 | Init spec is detailed — drag mechanics, data model, validation, guards all specified |
| Feasibility | 9 | Standard mouse/touch drag in React, simple backend — one field update per snap |
| Completeness | 9 | All files listed, test cases enumerated, touch support included |
| Alignment | 10 | ADR-009 explicitly carves out tier dragging from the old "no drag-and-drop" constraint. No other ADRs affected |
| **Average** | **9.25** | Ready for execution |

---

## Notes

### Row Height Measurement
`PositionColumn` measures row height from the first `PlayerRow` via a ref.
The player row grid is `height: 26px` (name button) + `3px` gap = `29px`.
Use a fallback constant of `29` if the ref measurement fails (e.g., empty
column).

### Drag Accumulator Pattern
The drag uses a cumulative delta pattern rather than per-event position
comparison. This ensures smooth multi-snap drags: the user can drag three
rows in one gesture, and the API is called three times (once per snap).
Each snap resets the accumulator by the row height amount, not to zero,
to preserve sub-row-height remainder for the next snap.

### File Size Check
Current line counts of files being modified:
- `backend/utils/rankings.py`: ~290 lines → ~310 after (well under 500)
- `backend/routers/rankings.py`: ~280 lines → ~310 after (well under 500)
- `frontend/src/components/PositionColumn.jsx`: 49 lines → ~90 after
- `frontend/src/App.jsx`: 291 lines → ~305 after
- `tests/test_rankings.py`: 326 lines → ~380 after
All safe.
