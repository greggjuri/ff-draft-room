# PRP-016: My Roster Panel

**Created**: 2026-04-17
**Initial**: `initials/16-init-roster-panel.md`
**Status**: Complete

---

## Overview

### Problem Statement
In Draft Mode, players marked "mine" are scattered across four position
columns. There's no consolidated view of your drafted team — you have to
visually scan all columns to see who you've picked.

### Proposed Solution
A fixed bottom-anchored drawer panel visible only in Draft Mode. A handle
bar at the viewport bottom shows live pick counts. Clicking it toggles
open a panel displaying "mine" players grouped by position, with tag icons,
team logos, and accent colors matching the existing design system.

Pure frontend — zero backend changes, no new tests.

### Success Criteria
- [ ] Handle bar visible at viewport bottom in Draft Mode only
- [ ] Pick summary (`QB 0 · RB 2 · ...`) updates in real time
- [ ] Clicking handle bar toggles panel with slide animation
- [ ] Panel shows 4 position sections, empty sections show `— empty —`
- [ ] Player rows show tag icon, name, team abbrev, team logo
- [ ] Players appear/disappear instantly on dot click
- [ ] Panel absent in War Room mode
- [ ] Draft exit wipes panel and collapses it
- [ ] Main columns not hidden under panel (padding-bottom applied)
- [ ] `cd frontend && npx vite build` — no errors

---

## Context

### Related Documentation
- `initials/16-init-roster-panel.md` — Full design spec
- PRP-007 (draft mode — draftState, status cycling, exit confirm)

### Dependencies
- **Required**: Draft Mode (PRP-007), team logos (PRP-012), player tags (PRP-015)

### Data Flow
No new state needed. `RosterPanel` is a pure derived-display component
reading from two existing sources:
1. `rankings` — `{ QB: [...], RB: [...], ... }` for player details
2. `draftState` — `{ 'QB-1': 'mine', ... }` for status

### Files to Create/Modify
```
# NEW
frontend/src/components/RosterPanel.jsx    # Panel component
frontend/src/components/RosterPanel.css    # Panel + handle bar styles

# MODIFIED
frontend/src/components/WarRoom.jsx        # rosterPanelOpen state + render
frontend/src/components/WarRoom.css        # padding-bottom for draft mode
```

No backend changes. No new API routes. No test changes.

---

## Technical Specification

### `RosterPanel.jsx`

**Props:**
```jsx
RosterPanel({
  rankings,       // { QB: [...], RB: [...], WR: [...], TE: [...] }
  draftState,     // { 'QB-1': 'mine', 'RB-3': 'other', ... }
  isOpen,         // boolean
  onToggle,       // () => void
})
```

**Derived data:**
```js
const myPicks = POSITIONS.reduce((acc, pos) => {
  acc[pos] = (rankings[pos] ?? [])
    .filter(p => draftState[`${pos}-${p.position_rank}`] === 'mine')
  return acc
}, {})
```

**Rendering:**
- Handle bar: always visible, fixed bottom, shows `MY ROSTER` + per-position counts
- Panel drawer: fixed above handle bar, `max-height: 40vh`, slide animation
- 4 position sections with accent-colored headers
- Player rows: tag icon + name + team abbrev + logo (reuse `getLogoUrl` pattern)
- Empty sections: `— empty —` in muted italic

### `WarRoom.jsx`

New state:
```js
const [rosterPanelOpen, setRosterPanelOpen] = useState(false)
```

Reset on draft exit (in `confirmExitDraft` callback area — the parent
`App.jsx` controls this but WarRoom can reset its local panel state via
a prop or by keying the panel on `isDraft`).

Since `rosterPanelOpen` is local to WarRoom and the panel only renders
when `isDraft` is true, exiting draft mode unmounts the panel entirely.
Re-entering draft mode creates a fresh component with `isOpen=false`.

Render `<RosterPanel>` inside the draft mode conditional.

### `WarRoom.css`

Draft mode padding-bottom to prevent content clipping:
```css
.war-room.draft-mode .war-room-columns {
  padding-bottom: 36px;  /* handle bar height */
}
.war-room.draft-mode.roster-open .war-room-columns {
  padding-bottom: calc(40vh + 36px);
}
```

Add `roster-open` class to the root `.war-room` div when panel is open.

### Design Tokens

Handle bar: `#0D1B2A` bg, `#1E3A5F` border-top, hover → `#0076B6` border.
Panel drawer: `#0D1B2A` bg, `#0076B6` 2px top border.
Position accent colors: reuse existing `--pos-color` CSS variables.
Slide animation: `transform: translateY(100%)` → `translateY(0)`, 200ms ease.

---

## Implementation Steps

### Step 1: RosterPanel component + styles
**Files**: `frontend/src/components/RosterPanel.jsx`,
`frontend/src/components/RosterPanel.css`

Create the panel component with handle bar, position sections, player
rows, empty placeholders, slide animation.

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds

---

### Step 2: Wire into WarRoom
**Files**: `frontend/src/components/WarRoom.jsx`,
`frontend/src/components/WarRoom.css`

1. Add `rosterPanelOpen` state
2. Render `<RosterPanel>` when `isDraft`
3. Add `roster-open` class toggle on root div
4. Add padding-bottom rules for draft mode

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds
- [ ] Manual: enter Draft Mode, handle bar visible
- [ ] Manual: click handle bar, panel slides open
- [ ] Manual: mark player "mine", appears in panel
- [ ] Manual: exit draft, panel gone

---

### Step 3: Final verification
```bash
cd frontend && npx vite build
pytest tests/ -q  # backend unchanged, should still be 82
```
- [ ] Build clean
- [ ] 82 tests pass
- [ ] No file over 500 lines

---

## Testing Requirements

### No Automated Tests
Pure frontend display component — no backend, no logic requiring tests.

### Manual Browser Tests
- [ ] Handle bar visible at bottom in Draft Mode
- [ ] Handle bar absent in War Room
- [ ] Pick counts update when dots clicked
- [ ] Panel slides open/closed on handle click
- [ ] 4 position sections always shown
- [ ] Empty sections show `— empty —`
- [ ] Player rows: tag + name + team + logo
- [ ] Mark player mine → appears; cycle away → disappears
- [ ] Many picks → panel scrolls
- [ ] Draft exit → panel gone, handle bar gone
- [ ] Content not hidden under panel (padding applied)
- [ ] Position accent colors on section headers

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `cd frontend && npx vite build` | Build succeeds | ☐ |
| 2 | Start dev servers | Both start | ☐ |
| 3 | Open War Room | No handle bar | ☐ |
| 4 | Switch to Draft Mode | Handle bar appears at bottom | ☐ |
| 5 | Handle bar shows `QB 0 · RB 0 · WR 0 · TE 0` | Correct | ☐ |
| 6 | Click handle bar | Panel slides open, 4 empty sections | ☐ |
| 7 | Mark a QB player "mine" | Appears in QB section, count → 1 | ☐ |
| 8 | Mark 2 RB players "mine" | Both appear in RB section | ☐ |
| 9 | Cycle RB player to "other" | Disappears from panel | ☐ |
| 10 | Click handle bar again | Panel slides closed | ☐ |
| 11 | Exit Draft Mode | Handle bar + panel gone | ☐ |
| 12 | Re-enter Draft Mode | Fresh panel, all counts 0 | ☐ |

---

## Error Handling

No error handling needed — pure derived display from in-memory state.

---

## Open Questions

None.

---

## Rollback Plan

```bash
git revert <commit>
cd frontend && npx vite build
```

Two new files + minor edits to WarRoom. Revert is clean.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Complete wireframes, CSS specs, data flow, edge cases |
| Feasibility | 10 | Standard fixed-position panel with CSS transform animation |
| Completeness | 10 | All files listed, every edge case covered, design tokens specified |
| Alignment | 10 | Pure frontend, no backend, follows existing design system |
| **Average** | **10** | Ready for execution |

---

## Notes

### Panel is Unmounted, Not Hidden
When Draft Mode exits, `isDraft` becomes false and `<RosterPanel>` is
not rendered at all. This means all panel state is automatically wiped
without explicit cleanup. Re-entering draft mode creates a fresh instance.

### Reusing Existing Patterns
- Team logos: same `getLogoUrl()` from `teamLogos.js`
- Tag icons: same `TAG_ICONS` map and class names from PlayerRow
- Position accent colors: same `--pos-color` CSS variables from PositionColumn

### File Size Check
- `frontend/src/components/WarRoom.jsx`: ~140 lines → ~155 after
- `frontend/src/components/RosterPanel.jsx`: new, ~120 lines estimated
All well under 500.
