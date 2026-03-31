# PRP-05: React War Room Frontend

**Created**: 2026-03-31
**Initial**: `initials/05-init-react-frontend.md`
**Status**: Ready

---

## Overview

### Problem Statement
The FastAPI backend is running with all 8 rankings endpoints verified. There is no frontend — the user cannot interact with the War Room without curl. A full React UI is needed to provide the four-column rankings board with tier groups, reordering, notes, add/delete, and save.

### Proposed Solution
Build a Vite + React frontend at `frontend/` with plain CSS (no framework). Seven components render the War Room layout. All API calls go through a single `api/rankings.js` module. State is managed with React `useState` — no external state library. Native HTML `<dialog>` elements for modals.

### Success Criteria
- [ ] `npm install` completes without errors
- [ ] `npm run dev` starts at localhost:5173
- [ ] With backend running: War Room loads, 4 columns visible
- [ ] QB 30 / RB 50 / WR 50 / TE 30 players displayed
- [ ] Players grouped under tier headers with alternating backgrounds
- [ ] Column dividers visible between positions
- [ ] ▲▼ buttons reorder — ranks update immediately
- [ ] Tier boundary crossing updates player's tier
- [ ] ▲ disabled on rank 1; ▼ disabled on last rank
- [ ] Click player name → notes dialog, pre-filled, Save/Close
- [ ] Notes save → `📝` appears, unsaved indicator shown
- [ ] `[+ QB · Tier 1]` → add dialog, validation, duplicate rejected
- [ ] `[×]` → confirm dialog, delete removes player
- [ ] `● UNSAVED` indicator after any change
- [ ] SAVE button → clears indicator
- [ ] Page reload → rankings preserved (fresh from backend)
- [ ] Backend not running → graceful error message
- [ ] `ruff check backend/ tests/` still passes (no backend regressions)
- [ ] All files under 500 lines

---

## Context

### Related Documentation
- `docs/DECISIONS.md` — ADR-006 (React replaces Streamlit), ADR-002 (JSON), ADR-003 (CSV)
- `docs/PLANNING.md` — Architecture diagram, API design, frontend structure
- `CLAUDE.md` — Design system, API routes, component list

### Dependencies
- **Required**: PRP-04 (FastAPI backend) complete (✅) — all 8 endpoints verified
- **Optional**: None

### Files to Create
```
frontend/index.html
frontend/package.json
frontend/vite.config.js
frontend/src/main.jsx
frontend/src/App.jsx
frontend/src/App.css
frontend/src/api/rankings.js
frontend/src/components/WarRoom.jsx
frontend/src/components/WarRoom.css
frontend/src/components/PositionColumn.jsx
frontend/src/components/PositionColumn.css
frontend/src/components/TierGroup.jsx
frontend/src/components/TierGroup.css
frontend/src/components/PlayerRow.jsx
frontend/src/components/PlayerRow.css
frontend/src/components/NotesDialog.jsx
frontend/src/components/AddPlayerDialog.jsx
frontend/src/components/DeleteConfirmDialog.jsx
```

### Files Untouched
```
backend/           — no changes
tests/             — no changes
data/              — no changes
```

---

## Technical Specification

### State Model (`App.jsx`)

```js
const [rankings, setRankings] = useState({ QB: [], RB: [], WR: [], TE: [] })
const [dirty, setDirty] = useState(false)
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)
```

### State Update Pattern

All mutations follow the same flow:
1. Call API function (returns updated position player list)
2. `setRankings(prev => ({ ...prev, [position]: updated }))`
3. `setDirty(true)`

### Component Tree

```
App
└── WarRoom
    ├── Header (title, unsaved indicator, save button)
    ├── PositionColumn × 4 (QB, RB, WR, TE)
    │   └── TierGroup × N
    │       ├── Tier header
    │       ├── PlayerRow × M
    │       │   ├── ▲ button
    │       │   ├── ▼ button
    │       │   ├── rank
    │       │   ├── name button
    │       │   ├── team
    │       │   └── × button
    │       └── [+ add] button
    ├── NotesDialog (conditional)
    ├── AddPlayerDialog (conditional)
    └── DeleteConfirmDialog (conditional)
```

### Dialog State

Managed in `App.jsx` via state:
```js
const [notesDialog, setNotesDialog] = useState(null)    // { player, position }
const [addDialog, setAddDialog] = useState(null)         // { position, tier }
const [deleteDialog, setDeleteDialog] = useState(null)   // { player, position }
```

Dialogs use native HTML `<dialog>` with `useRef` + `showModal()`/`close()`.

### API Layer

Single file `src/api/rankings.js` — 6 functions:
- `getPositionPlayers(position)` → `GET /api/rankings/{position}`
- `reorderPlayers(position, rank_a, rank_b)` → `POST .../reorder`
- `addPlayer(position, name, team, tier)` → `POST .../add`
- `deletePlayer(position, rank)` → `DELETE .../{rank}`
- `updateNotes(position, rank, notes)` → `PUT .../{rank}/notes`
- `saveRankings()` → `POST /api/rankings/save`

All return parsed JSON. Error responses throw with the `detail` message.

---

## Implementation Steps

### Step 1: Project Scaffold
**Files**: `frontend/package.json`, `frontend/vite.config.js`, `frontend/index.html`, `frontend/src/main.jsx`

1. Create `frontend/` directory
2. Write `package.json` with React 18 + Vite dependencies
3. Write `vite.config.js` with `/api` proxy to localhost:8000
4. Write `index.html` — minimal HTML shell with `<div id="root">`
5. Write `src/main.jsx` — `ReactDOM.createRoot` + render `<App />`
6. Run `npm install`

**Validation**:
```bash
cd frontend && npm install
npm run dev  # should start, show blank page at :5173
```
- [ ] Install succeeds
- [ ] Dev server starts

---

### Step 2: Global Styles + API Layer
**Files**: `frontend/src/App.css`, `frontend/src/api/rankings.js`

1. Write `App.css` with all CSS custom properties from the design system + base styles (body, *, dialog)
2. Write `api/rankings.js` with all 6 fetch functions
3. Error handling: check `response.ok`, throw `detail` from error responses

**Validation**:
- [ ] CSS file contains all design tokens
- [ ] API module exports all 6 functions

---

### Step 3: App.jsx — State + Data Loading
**Files**: `frontend/src/App.jsx`

1. Import `App.css` and API functions
2. Set up state: `rankings`, `dirty`, `loading`, `error`, dialog states
3. `useEffect` on mount: fetch all 4 positions in parallel
4. Define handler functions: `handleReorder`, `handleAdd`, `handleDelete`, `handleNotesUpdate`, `handleSave`
5. Each handler calls API, updates state, sets dirty
6. Render loading spinner while loading, error banner if error
7. Render `<WarRoom>` passing all state + handlers

**Validation**:
```bash
npm run dev
# Open localhost:5173 with backend running
# Should see War Room loading then displaying players
```
- [ ] Data loads from backend
- [ ] 4 positions populated

---

### Step 4: WarRoom + PositionColumn Components
**Files**: `frontend/src/components/WarRoom.jsx`, `WarRoom.css`, `PositionColumn.jsx`, `PositionColumn.css`

**WarRoom.jsx**:
- Header row: title, unsaved indicator (shown when `dirty`), SAVE button
- Four-column grid: render `<PositionColumn>` for QB, RB, WR, TE
- Render dialogs conditionally based on dialog state

**PositionColumn.jsx**:
- Column header: position name + player count
- Group players by tier using reduce
- Render `<TierGroup>` for each tier group
- Column divider CSS: `border-right` on first 3 columns

**Validation**:
```bash
# Browser: 4 columns visible with headers and player counts
```
- [ ] Layout matches spec — 4 equal columns with dividers
- [ ] Player counts shown: QB 30 / RB 50 / WR 50 / TE 30

---

### Step 5: TierGroup + PlayerRow Components
**Files**: `frontend/src/components/TierGroup.jsx`, `TierGroup.css`, `PlayerRow.jsx`, `PlayerRow.css`

**TierGroup.jsx**:
- Tier header with alternating background (odd/even)
- Render `<PlayerRow>` for each player
- `[+ Position · Tier N]` add button at bottom
- Pass `isFirst`/`isLast` booleans per player for ▲▼ disable

**PlayerRow.jsx**:
- 6-column grid: ▲ | ▼ | rank | name | team | ×
- ▲ button: calls `onMoveUp`, disabled if `isFirst`
- ▼ button: calls `onMoveDown`, disabled if `isLast`
- Name button: shows `📝` suffix if notes exist, calls `onNameClick`
- × button: calls `onDeleteClick`
- All buttons use `.control-btn` base class

**Validation**:
```bash
# Browser: players visible in rows with ▲▼ buttons
# Click ▲ on rank 2 → moves to rank 1
# Click ▼ on last rank → disabled
```
- [ ] Player rows render correctly
- [ ] ▲▼ reorder works
- [ ] Disable states correct

---

### Step 6: Dialogs — Notes, Add, Delete
**Files**: `frontend/src/components/NotesDialog.jsx`, `AddPlayerDialog.jsx`, `DeleteConfirmDialog.jsx`

**NotesDialog.jsx**:
- Native `<dialog>` with `useRef` + `useEffect` to call `showModal()`
- Player name + team in header
- Textarea pre-filled with `player.notes`
- Save: calls `onSave(notes)`, Close: calls `onClose()`

**AddPlayerDialog.jsx**:
- Native `<dialog>`
- Shows position + tier (read-only)
- Name input, Team input (maxLength=4)
- Inline validation errors (empty fields, API duplicate error)
- Add: calls `onAdd(name, team)`, Cancel: calls `onClose()`

**DeleteConfirmDialog.jsx**:
- Native `<dialog>`
- Confirm message with player name + team
- "This cannot be undone."
- Delete (red styled) / Cancel buttons

**Validation**:
```bash
# Browser: click player name → notes dialog
# Type notes, save → 📝 appears
# Click [+ QB · Tier 1] → add dialog
# Add "Test Player" / "TST" → appears in list
# Try duplicate → error shown inline
# Click × → confirm dialog → delete → player removed
```
- [ ] Notes dialog opens, saves, shows 📝
- [ ] Add dialog validates, adds, rejects duplicates
- [ ] Delete dialog confirms, removes player

---

### Step 7: Save + Unsaved Indicator
**Files**: Modifications to `App.jsx` and `WarRoom.jsx` (if not already done)

1. `● UNSAVED` text appears in header when `dirty === true`
2. SAVE button calls `handleSave` → `saveRankings()` API → `setDirty(false)`
3. After save, indicator disappears
4. Page reload: fresh data from backend, `dirty` resets to `false`

**Validation**:
```bash
# Make any change → "● UNSAVED" appears
# Click SAVE → indicator disappears
# Refresh page → data persists, no unsaved indicator
```
- [ ] Unsaved indicator shows/hides correctly
- [ ] Save persists to disk

---

### Step 8: Error Handling + Final Polish
**Files**: Minor updates across components

1. Backend not running: loading → error banner: `"Cannot connect to backend"`
2. API call failure: show error message, don't update state
3. Network timeout: show error, user retries manually
4. Clean up any console.log statements

**Validation**:
```bash
# Stop backend → reload page → error message shown
# Start backend → reload → works
```
- [ ] Error states handled gracefully
- [ ] No console.log in production code

---

### Step 9: Final Integration Check
**Commands**:
```bash
# Backend
uvicorn backend.main:app --reload

# Frontend
cd frontend && npm run dev

# Tests (ensure no regressions)
pytest tests/ -q
ruff check backend/ tests/
```

**Validation**:
- [ ] All backend tests pass (35 passing)
- [ ] Zero lint errors
- [ ] Full manual test of all War Room features
- [ ] All files under 500 lines
- [ ] No debug output remaining
- [ ] Commit: `feat: add React War Room frontend with full CRUD and dialogs`

---

## Testing Requirements

### Backend Tests (existing — no changes)
```
tests/test_data_loader.py  — 8 tests
tests/test_rankings.py     — 27 tests
```

### Frontend Manual Tests
```
Load:
  - App loads with 4 columns, correct player counts
  - Tier groups visible with alternating headers
  - Column dividers present

Reorder:
  - ▲ on rank 2 → moves to rank 1
  - ▼ on rank 1 → moves to rank 2
  - Cross tier boundary → tier updates
  - ▲ disabled on rank 1
  - ▼ disabled on last rank

Notes:
  - Click name → dialog opens, notes pre-filled
  - Save → 📝 suffix appears, unsaved shown
  - Close without saving → no changes

Add:
  - Click [+ QB · Tier 1] → dialog opens
  - Add valid player → appears at end of tier
  - Empty name → inline error
  - Duplicate name → inline API error
  - Cancel → no changes

Delete:
  - Click × → confirm dialog
  - Cancel → no changes
  - Delete → player removed, ranks renumbered

Save:
  - Any change → ● UNSAVED indicator
  - SAVE → indicator clears
  - Refresh → data persists

Error:
  - Backend down → error message shown
```

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `cd frontend && npm install` | No errors | ☐ |
| 2 | Start backend + `npm run dev` | Both running | ☐ |
| 3 | Open localhost:5173 | War Room loads, 4 columns | ☐ |
| 4 | Count players per column | QB 30, RB 50, WR 50, TE 30 | ☐ |
| 5 | Verify tier headers | Alternating odd/even backgrounds | ☐ |
| 6 | Click ▲ on QB rank 2 | Moves to rank 1, unsaved shows | ☐ |
| 7 | Click ▼ on tier boundary player | Tier number changes | ☐ |
| 8 | Click QB rank 1 name | Notes dialog opens | ☐ |
| 9 | Type notes, click Save | 📝 appears, unsaved indicator | ☐ |
| 10 | Click [+ QB · Tier 1] | Add dialog opens | ☐ |
| 11 | Add "Test Player" / "TST" | Player appears in list | ☐ |
| 12 | Try adding "Test Player" again | Duplicate error shown | ☐ |
| 13 | Click × on Test Player | Confirm dialog | ☐ |
| 14 | Click Delete | Player removed, ranks renumber | ☐ |
| 15 | Click SAVE | Indicator clears | ☐ |
| 16 | Refresh browser | Data persists | ☐ |
| 17 | Stop backend, refresh | Error message shown | ☐ |
| 18 | `pytest tests/ -q` | 35 passed, 1 skipped | ☐ |

---

## Error Handling

| Error | Cause | Behavior |
|-------|-------|----------|
| Backend unreachable | Server not running | Error banner: "Cannot connect to backend" |
| API returns 400 | Validation failure | Inline error in dialog |
| API returns 404 | Invalid position/rank | Show error, don't update state |
| API returns 500 | Save/seed failure | Error banner with detail message |
| Network timeout | Connection issue | Show error, user retries manually |

---

## Open Questions

None — all resolved in the init spec.

---

## Rollback Plan

1. `rm -rf frontend/` — remove entire frontend directory
2. Backend and tests are completely unaffected
3. No backend changes to revert

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Every component, CSS rule, and interaction specified |
| Feasibility | 10 | Standard React + Vite, plain CSS, native dialog — no exotic deps |
| Completeness | 9 | All components, styles, and interactions covered. No frontend unit tests (not required for this scope) |
| Alignment | 10 | Consistent with ADR-006 (React), consumes verified API endpoints |
| **Average** | **9.75** | |

---

## Notes

- **No frontend tests**: The init spec does not require frontend unit tests. All business logic is in the backend (tested). Frontend is pure UI — manual testing is the validation method.
- **Native `<dialog>`**: Avoids z-index/overlay issues. Works in all modern browsers. `showModal()` handles backdrop and focus trapping.
- **Vite proxy**: `/api/*` proxied to localhost:8000 — no CORS issues during development.
- **File size**: With co-located CSS files, no component should approach 500 lines. `PlayerRow.jsx` and `App.jsx` are the largest — estimated ~100-150 lines each.
- **No `node_modules` in git**: Ensure `.gitignore` includes `node_modules/`.
