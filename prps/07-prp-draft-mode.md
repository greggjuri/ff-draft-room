# PRP-07: Draft Mode

**Created**: 2026-03-31
**Initial**: `initials/07-init-draft-mode.md`
**Status**: Ready

---

## Overview

### Problem Statement
The War Room is for pre-draft preparation — ranking and organizing players. During the actual draft, users need a different view: no editing controls, just a way to mark players as they're picked (mine vs. other). Currently there's no way to track live picks against the rankings board.

### Proposed Solution
Add a Draft Mode toggle to the War Room header. Draft Mode shows the same 4-column layout without editing controls. Each player has a clickable status dot that cycles through undrafted → mine → other. Draft state is in-memory only — exiting resets all markings.

**Pure frontend feature** — no backend changes, no new API endpoints.

### Success Criteria
- [ ] Mode toggle visible: `WAR ROOM | DRAFT`
- [ ] DRAFT mode hides ▲▼, ×, add buttons, save toolbar
- [ ] 4 columns visible with tier groups in draft mode
- [ ] Grey status dot on each player name box
- [ ] Click dot cycles: undrafted → mine (green) → other (purple) → undrafted
- [ ] Mine: green background `#1B4332`, green dot `#00C805`
- [ ] Other: purple background `#2D1B4E`, purple dot `#9B59B6`
- [ ] Undrafted players dim once any pick is made
- [ ] Exit draft with picks → confirm dialog
- [ ] Exit draft without picks → immediate, no dialog
- [ ] Draft state resets each time mode toggles
- [ ] Notes dialog disabled in draft mode
- [ ] Backend tests unaffected (49 passing)
- [ ] Frontend builds with zero errors

---

## Context

### Related Documentation
- `docs/DECISIONS.md` — ADR-006 (React frontend)
- `docs/PLANNING.md` — Phase 2 Live Draft is future; this is a lightweight draft-day overlay
- `CLAUDE.md` — Component list, design system

### Dependencies
- **Required**: PRP-05 (React frontend) ✅, PRP-06 (profile management) ✅
- **Optional**: None

### Files to Create
```
frontend/src/components/ExitDraftConfirmDialog.jsx
```

### Files to Modify
```
frontend/src/App.jsx                   # mode + draftState + handlers
frontend/src/components/WarRoom.jsx    # mode toggle, conditional rendering
frontend/src/components/WarRoom.css    # mode toggle styles
frontend/src/components/PositionColumn.jsx  # pass isDraft
frontend/src/components/TierGroup.jsx       # hide add button
frontend/src/components/TierGroup.css       # (if needed)
frontend/src/components/PlayerRow.jsx       # draft dot, hide controls
frontend/src/components/PlayerRow.css       # dot + status colors
```

### Files Untouched
```
backend/                    — no changes
tests/                      — no changes
frontend/src/api/           — no new API calls
```

---

## Technical Specification

### State Model (`App.jsx`)

```js
const [mode, setMode] = useState('warroom')     // 'warroom' | 'draft'
const [draftState, setDraftState] = useState({}) // { "QB-1": "mine", ... }
```

Key format: `"{position}-{position_rank}"`
Values: `"undrafted"` (default/missing) | `"mine"` | `"other"`

### State Helpers (`App.jsx`)

```js
const getDraftStatus = (position, rank) =>
  draftState[`${position}-${rank}`] || 'undrafted'

const cycleDraftStatus = (position, rank) => {
  const key = `${position}-${rank}`
  const current = draftState[key] || 'undrafted'
  const next = { undrafted: 'mine', mine: 'other', other: 'undrafted' }[current]
  setDraftState(prev => {
    const updated = { ...prev, [key]: next }
    if (next === 'undrafted') delete updated[key]
    return updated
  })
}

const hasPicks = Object.keys(draftState).length > 0
```

### Component Prop Flow

```
App (mode, draftState, handlers)
└── WarRoom (mode, isDraft, hasPicks, onEnterDraft, onExitDraft)
    ├── Mode toggle
    ├── PositionColumn (isDraft, getDraftStatus, onStatusClick)
    │   └── TierGroup (isDraft)
    │       └── PlayerRow (isDraft, draftStatus, onStatusClick)
    └── ExitDraftConfirmDialog (conditional)
```

### Player Row Grid Changes

```css
/* War room: 24px 24px 24px 1fr 36px 24px  (▲ ▼ rank name team ×) */
/* Draft:    12px  24px  1fr  36px          (dot rank name team)    */
```

### CSS Classes on Root

- `.draft-mode` on `.war-room` when `mode === 'draft'`
- `.has-picks` when `Object.keys(draftState).length > 0`

---

## Implementation Steps

### Step 1: App.jsx — Mode State + Handlers
**Files**: `frontend/src/App.jsx`

1. Add `mode` and `draftState` state
2. Add `getDraftStatus`, `cycleDraftStatus`, `hasPicks` helpers
3. Add `enterDraftMode` (set mode, clear state) and `exitDraftMode` (check picks, confirm or exit)
4. Add `exitDraftDialog` state for confirm dialog
5. Pass new props to `<WarRoom>`: `mode`, `isDraft`, `hasPicks`, `getDraftStatus`, `onStatusClick`, `onEnterDraft`, `onExitDraft`, dialog props

**Validation**:
- [ ] No build errors

---

### Step 2: WarRoom — Mode Toggle + Conditional Rendering
**Files**: `frontend/src/components/WarRoom.jsx`, `WarRoom.css`

1. Add mode toggle button group in header: `[WAR ROOM | DRAFT]`
2. When `isDraft`:
   - Hide save toolbar (SAVE, SAVE AS, LOAD, RESET, SET DEFAULT)
   - Hide unsaved indicator
   - Add `draft-mode` and conditionally `has-picks` classes to root div
3. Pass `isDraft`, `getDraftStatus`, `onStatusClick` to `<PositionColumn>`
4. Render `<ExitDraftConfirmDialog>` conditionally

**CSS additions**:
- `.mode-toggle` flex container
- `.mode-toggle-btn` base style
- `.active-warroom` and `.active-draft` active states

**Validation**:
- [ ] Toggle visible, switches text styles
- [ ] Controls hide/show on mode switch

---

### Step 3: PositionColumn + TierGroup — Pass isDraft
**Files**: `frontend/src/components/PositionColumn.jsx`, `TierGroup.jsx`

**PositionColumn.jsx**: Accept and forward `isDraft`, `getDraftStatus`, `onStatusClick`.

**TierGroup.jsx**: Accept `isDraft`. Hide `[+ Position · Tier N]` add button when `isDraft`.

**Validation**:
- [ ] Add buttons hidden in draft mode

---

### Step 4: PlayerRow — Draft Dot + Status Colors
**Files**: `frontend/src/components/PlayerRow.jsx`, `PlayerRow.css`

1. Accept `isDraft`, `draftStatus`, `onStatusClick` props
2. When `isDraft`:
   - Hide ▲, ▼, × buttons
   - Change grid to `12px 24px 1fr 36px`
   - Render status dot `<span>` inside name area with `onClick` + `stopPropagation`
   - Disable notes dialog click (name button is no-op)
   - Add `status-{draftStatus}` class to name button
3. Status dot: 8px circle, colored by status

**CSS additions**:
- `.player-row.draft-row` grid override
- `.draft-dot` base + `.status-undrafted`, `.status-mine`, `.status-other`
- `.player-name-btn.status-mine`, `.status-other` background overrides
- `.draft-mode .player-name-btn.status-undrafted` opacity dimming

**Validation**:
- [ ] Dots visible, clickable, cycle through states
- [ ] Colors match spec

---

### Step 5: ExitDraftConfirmDialog
**Files**: `frontend/src/components/ExitDraftConfirmDialog.jsx`

Native `<dialog>` with `useEffect` open/close pattern:
- "Exit Draft Mode?"
- "All pick markings will be lost."
- [Exit] / [Stay in Draft] buttons

**Validation**:
- [ ] Dialog appears when exiting with picks
- [ ] Confirm exits, cancel stays

---

### Step 6: Final Integration Check
**Commands**:
```bash
cd frontend && npx vite build
pytest tests/ -q
ruff check backend/ tests/
```

**Validation**:
- [ ] Frontend builds (0 errors)
- [ ] Backend tests pass (49 passing)
- [ ] Lint clean
- [ ] Manual test of full draft mode flow
- [ ] All files under 500 lines
- [ ] Commit and push

---

## Testing Requirements

### Backend Tests (unchanged)
49 passing — no regressions expected (no backend changes).

### Frontend Manual Tests
```
Mode Toggle:
  - Click DRAFT → draft mode enters, controls hidden
  - Click WAR ROOM → returns to war room (if no picks)
  - Click WAR ROOM with picks → confirm dialog

Draft Mode Layout:
  - 4 columns visible with tier groups
  - ▲▼, ×, add buttons hidden
  - Save toolbar hidden
  - Rank and team labels visible
  - Tier headers visible

Status Dots:
  - Grey dot on each player
  - Click dot → green (mine)
  - Click dot again → purple (other)
  - Click dot again → grey (undrafted)
  - Dot click does NOT trigger notes dialog

Colors:
  - Mine → green background (#1B4332)
  - Other → purple background (#2D1B4E)
  - Undrafted → dimmed (opacity 0.7, then 0.55 with picks)

State Reset:
  - Exit draft → all dots reset to grey
  - Re-enter draft → clean slate
```

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Click DRAFT toggle | Draft mode enters, controls hidden | ☐ |
| 2 | Verify 4 columns visible | All positions, tier groups, players | ☐ |
| 3 | Verify ▲▼, ×, add hidden | No editing controls visible | ☐ |
| 4 | Click status dot on QB rank 1 | Dot turns green, background green | ☐ |
| 5 | Click same dot again | Dot turns purple, background purple | ☐ |
| 6 | Click same dot again | Dot turns grey, background normal | ☐ |
| 7 | Mark several players | Undrafted players dim | ☐ |
| 8 | Click player name text | Nothing happens (notes disabled) | ☐ |
| 9 | Click WAR ROOM toggle | Confirm dialog (picks exist) | ☐ |
| 10 | Cancel exit | Stay in draft mode, picks preserved | ☐ |
| 11 | Confirm exit | War Room restored, all controls back | ☐ |
| 12 | Re-enter draft | Clean slate, all dots grey | ☐ |
| 13 | Enter draft, no picks, exit | Immediate exit, no confirm | ☐ |
| 14 | `npx vite build` | Zero errors | ☐ |
| 15 | `pytest tests/ -q` | 49 passed, 1 skipped | ☐ |

---

## Error Handling

| Error | Cause | Behavior |
|-------|-------|----------|
| Exit draft with picks | User has marked players | Confirm dialog before wiping |
| Exit draft without picks | No markings made | Immediate exit, no dialog |
| Notes click in draft mode | User clicks name text | No-op (disabled) |

---

## Open Questions

None — all resolved in the init spec.

---

## Rollback Plan

1. Revert frontend commits
2. Remove `ExitDraftConfirmDialog.jsx`
3. No backend changes to revert
4. No data changes to revert

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Every interaction, CSS rule, state shape specified |
| Feasibility | 10 | Pure React state + CSS, no exotic requirements |
| Completeness | 10 | All components, styles, state, and edge cases covered |
| Alignment | 10 | No backend changes, consistent with ADR-006 |
| **Average** | **10** | |

---

## Notes

- **No backend changes**: This is entirely frontend state. Draft markings are in-memory only — never persisted.
- **Grid change**: PlayerRow switches from 6-column to 4-column grid in draft mode. The `isDraft` prop controls which grid template is used.
- **stopPropagation**: The status dot's `onClick` must call `e.stopPropagation()` to prevent triggering the name button's click handler.
- **File sizes**: PlayerRow.jsx is currently 46 lines. Adding draft mode logic will bring it to ~80-90 lines. Well under 500.
- **No `has-picks` optimization needed**: Just checking `Object.keys(draftState).length > 0` is fast enough for 160 players.
