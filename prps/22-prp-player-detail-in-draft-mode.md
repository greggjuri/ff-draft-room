# PRP-022: PlayerDetailDialog in Draft Mode

**Created**: 2026-06-01
**Initial**: `initials/22-init-player-detail-in-draft-mode.md`
**Status**: Draft

---

## Overview

### Problem Statement
PRP-021 introduced `PlayerDetailDialog` and wired its click handler on
the **War Room** branch of `PlayerRow.jsx` only. In Draft Mode, the
player-name span has no click handler — clicking a player name during
a live draft does nothing. Mid-draft this is exactly when the outlook
+ bye-week view is most valuable (comparing 2-3 players with a pick
clock running).

### Proposed Solution
Pure frontend change. Two surgical edits, no new components, no API
work, no schema:

1. **`PlayerRow.jsx:73`** (Draft Mode name span) — add
   `onClick={onNameClick}` to wire the click handler that already
   exists on the War Room branch.
2. **`TierGroup.jsx:29`** — remove the `!isDraft &&` short-circuit on
   the `onNameClick` callback so the handler actually invokes
   `onNotesOpen(...)` in Draft Mode.

The `onNameClick` prop is already passed to `PlayerRow` in both modes
(verified). The dialog itself is mode-agnostic. Notes save semantics
are unchanged.

### Success Criteria
- [ ] Clicking a player name in Draft Mode opens `PlayerDetailDialog`
- [ ] Clicking the status dot still cycles `undrafted → mine → other →
  undrafted` (no collision)
- [ ] Right-click still opens the context menu (Tags / Edit) from
  PRP-020
- [ ] Notes saved from the dialog while in Draft Mode persist to S3
  exactly like in War Room mode
- [ ] `mine` (green) / `other` (purple) row backgrounds remain
  unchanged when the dialog opens or closes
- [ ] `pytest tests/ -q` passes (target: **98**, no delta — no backend
  / no tests touched)
- [ ] `ruff check backend/ tests/` clean (baseline preserved)
- [ ] `uvicorn backend.main:app --reload` starts (sanity)
- [ ] `cd frontend && npx vite build` clean

---

## Context

### Related Documentation
- `docs/PLANNING.md` — Architecture, two-mode UI (War Room / Draft)
- `docs/DECISIONS.md` — ADR-006 (FastAPI + React, full CSS control);
  no new ADR
- `prps/21-prp-player-detail-dialog.md` — Created
  `PlayerDetailDialog`; left Draft Mode click wiring as a follow-up
  (PRP-021 §"Integration Test Plan" Step 16 note)
- `initials/22-init-player-detail-in-draft-mode.md` — Full spec

### ADR Alignment
No conflict with any ADR. Surfaces an existing dialog in an existing
mode. Single-user / JSON / React stack unchanged.

### Dependencies
- **Required**: PRP-021 (`PlayerDetailDialog` exists). Verified —
  `frontend/src/components/PlayerDetailDialog.jsx` is present.
- **Optional**: none.

### Open Question Resolutions (Init §"Open Questions for PRP")

| Init Question | Resolution |
|---|---|
| **Q1**: Line number for Draft Mode branch in PlayerRow.jsx | **Confirmed at `PlayerRow.jsx:64-79`** (name span at line 73). PRP-021 didn't touch this file — line numbers match the init's expectation exactly. |
| **Q2**: Is `cursor: pointer` already on `.player-name-btn`, or branch-scoped? | **Already on the base class** at `PlayerRow.css:17`. Both branches use `nameClasses = 'player-name-btn ...'` (assembled at `PlayerRow.jsx:31`), so both already get the pointer cursor. **No CSS edit needed**. |
| **Q3**: Click target overlap with status dot | **No overlap.** The Draft row uses CSS grid `grid-template-columns: 12px 24px 1fr` (`PlayerRow.css:93`). Dot lives in column 1 (12px), name in column 3 (1fr). They are distinct grid cells and their click areas cannot collide. |
| **Q4**: Is `onNameClick` already passed to `PlayerRow` in Draft Mode? | **Yes — but it's a no-op.** `TierGroup.jsx:29` passes `onNameClick={() => !isDraft && onNotesOpen(player, position)}`. The prop is always wired, but the body short-circuits when `isDraft` is true. **This makes TierGroup.jsx a required edit** (init listed only PlayerRow.{jsx,css}). See Scope Expansion. |

### Files to Modify / Create / Delete
```
frontend/src/components/PlayerRow.jsx        # MODIFY — 1-line add: onClick on Draft span
frontend/src/components/TierGroup.jsx        # MODIFY — 1-line: drop !isDraft gate
initials/22-init-player-detail-in-draft-mode.md  # untracked; include in commit
```

### Scope Expansion vs. Init

Init's "Files Touched" lists `PlayerRow.jsx` + `PlayerRow.css`. Two
corrections:

1. **`TierGroup.jsx` added.** Init assumed adding `onClick` in
   `PlayerRow` was sufficient. It isn't — `TierGroup.jsx:29` passes
   `onNameClick={() => !isDraft && onNotesOpen(...)}` which
   short-circuits in Draft Mode. Without removing that gate, the
   PlayerRow click fires but nothing happens.
   - **Why required**: literally the only thing standing between the
     PlayerRow `onClick` and the dialog opening.
   - **Default chosen**: include — non-optional for the feature to
     work.
   - **Opt-out**: pass a *different* callback shape (e.g. an explicit
     `onNameClickDraft`) instead of removing the gate. More code, no
     functional gain — rejected.

2. **`PlayerRow.css` dropped from the list.** Init said "verify (and
   add if missing) `cursor: pointer` on `.player-name` for the Draft
   Mode branch." Verified at `PlayerRow.css:17` — the rule is on
   `.player-name-btn` base class and applies in both branches today.
   No edit needed.
   - **Default chosen**: skip — nothing to add.
   - **Opt-out**: none (no work to do).

### Files NOT Modified (intentional)
```
backend/**                                          # No backend work
frontend/src/api/rankings.js                        # No new endpoint
frontend/src/App.jsx                                # State + handlers
                                                    #  already wired
                                                    #  end-to-end
frontend/src/components/PlayerDetailDialog.{jsx,css}# Mode-agnostic; reused as-is
frontend/src/components/PlayerRow.css               # cursor: pointer already
                                                    #  on .player-name-btn base
frontend/src/components/WarRoom.jsx                 # Render unchanged
frontend/src/components/PositionColumn.jsx          # Pass-through unchanged
data/players/2026_{POS}.csv                         # Read-only seed
```

---

## Technical Specification

### Edit 1 — `PlayerRow.jsx` (Draft Mode branch)

```jsx
// Before (line 73):
        <span className={nameClasses} style={nameStyle} onContextMenu={handleContextMenu}>

// After:
        <span className={nameClasses} style={nameStyle} onClick={onNameClick} onContextMenu={handleContextMenu}>
```

Matches the War Room branch pattern at line 104:
`<button ... onClick={onNameClick} onContextMenu={handleContextMenu}>`.

The init's mock proposed `onClick={() => onNameClick(position, player)}`
with explicit args. The actual existing pattern passes `onNameClick`
*directly* as the handler — TierGroup's wrapper already has `player`
and `position` bound from closure (see Edit 2). Matching the existing
pattern keeps the call sites symmetric.

### Edit 2 — `TierGroup.jsx`

```jsx
// Before (line 29):
          onNameClick={() => !isDraft && onNotesOpen(player, position)}

// After:
          onNameClick={() => onNotesOpen(player, position)}
```

The `!isDraft` gate dates from before the dialog existed in Draft
Mode. Removing it lets the click in Draft Mode actually invoke
`onNotesOpen`, which sets `notesDialog` state in App.jsx → renders
`<PlayerDetailDialog>` via WarRoom.

### What stays the same
- `onNameClick` prop in PlayerRow's destructure (already present at
  line 25, used in War Room branch at line 104).
- `PlayerDetailDialog` itself — no mode awareness inside, no prop
  changes, no CSS changes.
- Notes save flow — `onNotesUpdate(position, rank, notes)` from
  App.jsx is unchanged; persists to S3 in production identical to
  War Room mode behavior.
- Status dot click — `onClick={onStatusClick}` on the dot span (line
  69) is untouched.
- Right-click context menu — `onContextMenu={handleContextMenu}` on
  the name span (line 73) is preserved alongside the new `onClick`.

### Design Tokens
Nothing new. The existing Draft Mode visual treatment
(`mine` `#1A7A3A` / `other` `#6B2FA0`) carries through unchanged via
the existing `.player-name-btn.status-mine` / `.status-other` CSS
rules.

---

## Implementation Steps

### Step 1 — Add `onClick` to Draft Mode name span
**Files**: `frontend/src/components/PlayerRow.jsx`

Edit line 73 per the spec — insert `onClick={onNameClick}` between
`style` and `onContextMenu`.

**Validation**:
```bash
grep -n "onClick={onNameClick}" frontend/src/components/PlayerRow.jsx
# expected: two matches (Draft span line ~73, War Room button line ~104)
```
- [ ] Both branches now have the same onClick handler

---

### Step 2 — Remove `!isDraft` gate in TierGroup
**Files**: `frontend/src/components/TierGroup.jsx`

Edit line 29 per the spec — drop the `!isDraft &&` short-circuit.

**Validation**:
```bash
grep -n "isDraft" frontend/src/components/TierGroup.jsx
# expected: only the prop destructure (line 5) and the
#           draftStatus ternary (line 25). NOT in onNameClick.
```
- [ ] No `!isDraft` short-circuit remains in `onNameClick`
- [ ] `isDraft` is still used for `draftStatus` ternary (line 25) —
  do not touch that

---

### Step 3 — Full build + sanity
**Validation**:
```bash
source .venv/bin/activate
pytest tests/ -q
ruff check backend/ tests/
cd frontend && npx vite build
```
- [ ] 98 tests pass, 1 skipped (baseline; no change expected)
- [ ] Ruff clean
- [ ] Vite build clean

---

### Step 4 — Local smoke (browser)
**Setup**:
```bash
# Terminal 1
source .venv/bin/activate && uvicorn backend.main:app --reload

# Terminal 2
cd frontend && npm run dev
```
Open `http://localhost:5173`, toggle to Draft Mode, walk the manual
checklist (Testing Requirements below). If no browser available in
the execution environment, say so explicitly — do not claim success.

---

### Step 5 — Commit + push
```bash
git add frontend/src/components/PlayerRow.jsx \
        frontend/src/components/TierGroup.jsx \
        initials/22-init-player-detail-in-draft-mode.md
git commit -m "feat: open PlayerDetailDialog from Draft Mode player rows"
git push origin main
```

---

## Testing Requirements

### Unit Tests (`backend/utils/`)
- **None**. No backend code is changed.

### API Tests (curl, local)
- **None**. No API surface change.

### Manual Browser Tests (post-deploy checklist)

- [ ] Enter Draft Mode via the WAR ROOM / DRAFT toggle in the header
- [ ] Click any player's name → `PlayerDetailDialog` opens
- [ ] Dialog shows the same content as in War Room mode (header,
  metadata strip, outlook, notes textarea)
- [ ] Click the status dot of the same row → status cycles, dialog
  does NOT open (existing behavior preserved, no collision)
- [ ] Right-click anywhere on the row → context menu opens (Tags /
  Edit — PRP-020 behavior preserved)
- [ ] In the open dialog, type notes, click Save → notes persist;
  re-open the same player → notes are pre-populated (proves save
  worked across the dialog open/close cycle in Draft Mode)
- [ ] Esc key closes dialog (native `<dialog>` behavior)
- [ ] Click a player marked `mine` (green) → dialog opens; row
  background stays green
- [ ] Click a player marked `other` (purple) → dialog opens; row
  background stays purple
- [ ] Toggle back to War Room while dialog is open → dialog stays
  open above the war room. Close dialog → mode swap is already
  applied. (Existing modal behavior; no regression)
- [ ] No console errors

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | 98 passed, 1 skipped (baseline, no change) | ☐ |
| 2 | `ruff check backend/ tests/` | Clean | ☐ |
| 3 | `cd frontend && npx vite build` | Build clean | ☐ |
| 4 | `grep -n "onClick={onNameClick}" frontend/src/components/PlayerRow.jsx` | Two matches (both branches) | ☐ |
| 5 | `grep -n "!isDraft" frontend/src/components/TierGroup.jsx` | Zero matches | ☐ |
| 6 | Browser: enter Draft Mode | Toggle works; controls hidden | ☐ |
| 7 | Browser: click any player name in Draft Mode | Dialog opens | ☐ |
| 8 | Browser: click the status dot of the same player | Dot cycles; dialog does NOT open | ☐ |
| 9 | Browser: right-click the player | Context menu (Tags / Edit) opens | ☐ |
| 10 | Browser: type notes in dialog, Save, reopen | Notes pre-populated | ☐ |
| 11 | Browser: Esc closes dialog | Closes; no console error | ☐ |
| 12 | Browser: click a `mine`-marked player | Dialog opens; row stays green | ☐ |
| 13 | Browser: click an `other`-marked player | Dialog opens; row stays purple | ☐ |
| 14 | Browser: War Room mode still works (regression check) | Click in War Room still opens dialog | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| Status dot click bubbles to name span | If `onStatusClick` didn't `stopPropagation` and grid cells overlapped | Verified non-issue: dot and name are in distinct CSS grid cells (`12px / 24px / 1fr`); the click events fire on the targeted element only |
| Dialog opens but notes don't pre-populate | `player.notes` not on the object passed to `setNotesDialog` | Verified non-issue: `notesDialog` state carries the full `player` object (set at `App.jsx:324`) and PRP-021's `PlayerDetailDialog` reads `player.notes` directly |
| Notes save fails in Draft Mode | If `onNotesUpdate` had a draft-mode guard | Verified non-issue: `handleNotesUpdate` at `App.jsx:209` has no mode awareness; calls `updateNotes(position, rank, notes)` unconditionally |
| Dialog steals focus from a draft action | Modal `<dialog>` does grab focus | Acceptable / desired: mid-draft, opening a player's detail is an intentional focusing act. User can Esc to dismiss instantly. |

---

## Open Questions

All four init Open Questions resolved against live code (see Context →
"Open Question Resolutions"). No outstanding blockers.

---

## Rollback Plan

1. `git revert <commit-sha>` on `main`
2. `git push origin main`
3. **Local**: Vite HMR picks up the revert immediately — Draft Mode
   name span goes back to no-op click, TierGroup gate restored.
4. **Production**: on EC2 run `./scripts/deploy.sh` (it runs
   `git pull origin main` itself).
5. **S3 / on-disk JSON cleanup**: none — pure frontend interaction
   change, no schema or data touched.

Rollback is trivial and risk-free. Any notes that were saved from
Draft Mode while the feature was live are still on the player records
(notes are user-owned, not mode-scoped); rollback just removes the
ability to *open* the dialog from Draft Mode again.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Two 1-line edits with exact before/after diffs. All four init Open Questions resolved against live code with file:line citations. The crucial Q4 finding (TierGroup gate) surfaced as required scope. |
| Feasibility | 10 | Smaller than PRP-021. Two single-line edits, no new files, no new state, no styles. Reuses everything from PRP-021. |
| Completeness | 10 | All affected files identified (incl. TierGroup, which the init missed). Init's PlayerRow.css line item correctly dropped (no edit needed — verified). Manual checklist covers the four real risk areas: dialog opens, dot still cycles, context menu still works, notes persist. |
| Alignment | 10 | No ADR conflict. Single-user / JSON / FastAPI + React stack. Operator preference (Draft Mode mid-pick utility) honored. |
| **Average** | **10.0** | Ready for execution. |

---

## Notes

### Why `onClick={onNameClick}` and not `onClick={() => onNameClick(position, player)}`
The init's mock used explicit args. The actual TierGroup wrapper
already binds `player` and `position` from closure
(`() => onNotesOpen(player, position)`), so PlayerRow can just hand
the wrapper directly to React. This matches the War Room branch at
line 104 byte-for-byte and avoids introducing a divergent call shape.

### Why removing `!isDraft` is the right fix (vs. a separate prop)
The gate was a defensive measure from before the dialog existed in
Draft Mode. The whole point of this PRP is "let it exist in Draft
Mode." Adding a parallel prop (e.g. `onNameClickDraft`) would push the
mode-awareness up one level for no functional benefit — the wrapper
body would be identical and the dialog component is mode-agnostic.

### Why no PlayerRow.css change
`.player-name-btn` has `cursor: pointer` on the base class at
`PlayerRow.css:17`. Both branches assemble the class via
`nameClasses` at `PlayerRow.jsx:31`. The Draft `<span>` already
shows the pointer cursor on hover — what was missing was the click
handler behind it. A user testing Draft Mode today probably already
*expects* the click to do something because the row visually invites
it; this PRP delivers on that visual promise.

### File-size considerations
- `PlayerRow.jsx`: 114 lines → 114 lines (one attribute added, no
  line delta).
- `TierGroup.jsx`: 36 lines → 36 lines (one short edit).

Both well under the 500-line limit.
