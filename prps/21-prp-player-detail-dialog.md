# PRP-021: Player Detail Dialog (Outlook + Notes Split Panel)

**Created**: 2026-05-31
**Initial**: `initials/21-init-player-detail-dialog.md`
**Status**: Draft

---

## Overview

### Problem Statement
PRP-019 added six new fields to every seeded player record
(`bye_week`, `adp`, `projected_points`, `risk`, `upside`, `outlook`).
PRP-020 made `add_player()` and the AddPlayer dialog symmetric on
those fields. Both PRPs landed the data in the model. Nothing renders
any of it in the UI — it's been sitting in S3 doing nothing.

Today, clicking a player's name in the war room opens a small
`NotesDialog` — a single-textarea modal that pre-dates the schema
expansion and doesn't know any of the new fields exist.

### Proposed Solution
Pure frontend change: replace `NotesDialog.jsx` with a new
`PlayerDetailDialog.jsx` that lays out two side-by-side panels —
**left** = Fantasy Footballers' projection metadata (`Proj` /
`ADP` / `Bye`) plus the full `outlook` blurb; **right** = the
existing notes textarea, Save / Close buttons, behaviour preserved
verbatim.

Per operator preference: `risk` / `upside` stay hidden (data captured,
UI silent); per-row layouts stay tight (no row-level metadata); the
war room is unchanged everywhere except the dialog that opens on
player-name click.

### Success Criteria
- [ ] Clicking a player name in the war room opens `PlayerDetailDialog`
  with the two-panel layout described in the init.
- [ ] Header reads `📋 {name} · {position} · {team}` followed by close ✕.
- [ ] Left panel: metadata strip (`Proj X · ADP Y · Bye Z`) where each
  segment is omitted when its field is null / empty; outlook prose
  fills the rest of the panel and scrolls within its bounds.
- [ ] Outlook empty (`""`) renders the italic muted placeholder
  *"No outlook available."*; metadata strip independently shows what
  data exists or nothing if all three are missing.
- [ ] Right panel: existing notes textarea + Save / Close, same `onSave`
  semantics (no dirty-state warning — there isn't one today).
- [ ] At viewport `< 700px`, panels stack vertically (outlook on top).
- [ ] Vertical cap ~80% viewport height; each panel scrolls within bounds.
- [ ] `NotesDialog.jsx` deleted; no remaining references in
  `frontend/src/`.
- [ ] `pytest tests/ -q` passes (target: **98**, no delta — no backend
  work, no tests added/removed).
- [ ] `ruff check backend/ tests/` clean (no backend touched, but
  baseline must hold).
- [ ] `uvicorn backend.main:app --reload` starts (sanity check).
- [ ] `cd frontend && npx vite build` clean.

---

## Context

### Related Documentation
- `docs/PLANNING.md` — Architecture; React component layout
- `docs/DECISIONS.md` — ADR-006 (FastAPI + React, full CSS control);
  ADR-010 (Fantasy Footballers seed, source of `outlook` /
  `projected_points` / `bye_week` / `adp`). No new ADR needed —
  surfacing existing data, not adding a new architectural pattern.
- `prps/19-prp-fantasy-footballers-tiered-import.md` — Added the six
  fields to seeded records; outlook can be very long (multi-paragraph)
- `prps/20-prp-add-delete-ux-overhaul.md` — Made manually-added
  players carry the same shape; surfaces edge case where `outlook ==
  ""`, `projected_points == None`, etc.
- `initials/21-init-player-detail-dialog.md` — Full spec

### ADR Alignment
No conflict with any ADR. Single-user / JSON / React stack unchanged.
The dialog reads fields that have lived on the player record since
PRP-019; no API surface change.

### Dependencies
- **Required**: PRP-019 (player record carries the 6 new fields).
  Verified — see e.g. `add_player()` at `backend/utils/rankings.py`.
- **Optional**: none.

### Open Question Resolutions (Init §"Open Questions for PRP")

| Init Question | Resolution |
|---|---|
| **Q1**: Where does NotesDialog state currently live? | **`App.jsx`** at line 50 (`const [notesDialog, setNotesDialog] = useState(null)`). The **render** lives in `WarRoom.jsx:107-114`. State shape is `{ player, position }`, where `player` already carries the full 13-field record (set from `PlayerRow.jsx` → `onNameClick`). **No App.jsx state rename or shape change needed** — only the WarRoom.jsx import + render switches. |
| **Q2**: Is there an existing `var(--text-muted)`? | **Yes** — defined at `App.css:10` as `#6A8CAA`. Reuse it for the metadata strip and the "No outlook available." placeholder. No new design token. |
| **Q3**: Does NotesDialog have a dirty-state check on close? | **No**. The current `NotesDialog.jsx:29` Close button calls `onClose` directly with no guard. The init's manual-test bullet "Close without saving warns of unsaved changes if dirty (existing behavior)" is describing behavior that doesn't exist. **Resolution**: preserve the no-warn behavior (out of scope per init) and reword the checklist item to "Close discards in-flight notes silently (existing behavior — verify no regression)". |

### Files to Modify / Create / Delete

```
frontend/src/components/PlayerDetailDialog.jsx   # CREATE — new component
frontend/src/components/PlayerDetailDialog.css   # CREATE — split-panel layout
frontend/src/components/NotesDialog.jsx          # DELETE — replaced
frontend/src/components/WarRoom.jsx              # MODIFY — import + render
initials/21-init-player-detail-dialog.md         # untracked; include in commit
```

### Scope Expansion vs. Init

Two corrections to the init's "Files Touched" list. Both make the
scope **smaller**, not larger:

1. **`NotesDialog.css` is not listed for deletion** — it doesn't exist.
   The current dialog reuses shared `.dialog-header` / `.dialog-textarea`
   / `.dialog-buttons` / `.btn-primary` / `.btn-cancel` rules from
   `App.css`. The init said "delete NotesDialog.css"; that's a no-op
   nothing to delete.
   - **Default chosen**: drop from the file list. The shared classes
     in `App.css` remain (still used by `AddPlayerDialog`,
     `DeleteConfirmDialog`, etc.).
   - **Opt-out**: none — the file genuinely does not exist.

2. **`App.jsx` not modified** — init said "if NotesDialog state lives
   here, rename state and pass full player object." Verified: state
   lives in App.jsx, but it already holds `{ player, position }` where
   `player` is the full record. The new dialog reads the same prop
   shape, no rename needed.
   - **Default chosen**: leave App.jsx untouched.
   - **Opt-out**: rename `notesDialog` → `playerDetailDialog` for
     symmetry with the component rename. Not done — it would touch
     six lines in App.jsx for zero functional benefit and pollute the
     diff. If operator wants the rename later, it's a one-PRP cleanup.

### Files NOT Modified (intentional)
```
backend/**                       # No backend changes (init explicit)
frontend/src/api/rankings.js     # No new endpoints; existing GET
                                 #  already returns the 13 fields
frontend/src/App.jsx             # See Scope Expansion #2
frontend/src/components/PlayerRow.jsx      # Row stays tight per operator
frontend/src/components/TierGroup.jsx      # Untouched
frontend/src/components/ContextMenu.jsx    # Tag/Edit menu from PRP-020 unchanged
frontend/src/App.css             # var(--text-muted) already exists; no new tokens
data/players/2026_{POS}.csv      # Read-only seed data
```

---

## Technical Specification

### Component — `PlayerDetailDialog.jsx`

```jsx
import { useRef, useEffect, useState } from 'react'
import './PlayerDetailDialog.css'

export default function PlayerDetailDialog({ isOpen, player, onSave, onClose }) {
  const dialogRef = useRef(null)
  const [notes, setNotes] = useState(player?.notes ?? '')

  useEffect(() => {
    if (isOpen) dialogRef.current?.showModal()
    else dialogRef.current?.close()
  }, [isOpen])

  // Reset textarea when a different player is selected
  useEffect(() => {
    if (player) setNotes(player.notes ?? '')
  }, [player])

  if (!player) return null

  // Build metadata segments, omitting empties. ADP is a string ("",
  // "3.05"); projected_points / bye_week are number or null.
  const segments = []
  if (player.projected_points != null) {
    segments.push(`Proj ${player.projected_points}`)
  }
  if (player.adp) {
    segments.push(`ADP ${player.adp}`)
  }
  if (player.bye_week != null) {
    segments.push(`Bye ${player.bye_week}`)
  }

  return (
    <dialog ref={dialogRef} onClose={onClose} className="player-detail-dialog">
      <div className="pdd-header">
        <span className="pdd-title">
          📋 {player.name} · {player.position} · {player.team}
        </span>
        <button className="pdd-close" onClick={onClose} aria-label="Close">✕</button>
      </div>

      <div className="pdd-body">
        <section className="pdd-left">
          {segments.length > 0 && (
            <div className="pdd-meta">{segments.join(' · ')}</div>
          )}
          {player.outlook
            ? <div className="pdd-outlook">{player.outlook}</div>
            : <div className="pdd-outlook-empty">No outlook available.</div>}
        </section>

        <section className="pdd-right">
          <textarea
            className="dialog-textarea pdd-notes"
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Add scouting notes..."
          />
          <div className="dialog-buttons pdd-buttons">
            <button className="btn-primary" onClick={() => onSave(notes)}>Save</button>
            <button className="btn-cancel" onClick={onClose}>Close</button>
          </div>
        </section>
      </div>
    </dialog>
  )
}
```

**Key decisions encoded above**:
- Props: `isOpen`, `player` (full object), `onSave(notes)`, `onClose`.
  `position` prop dropped — it's already on `player.position`.
- `onSave` signature unchanged (`(notes) => …`) so `WarRoom.jsx`'s
  inline wrapper (`(notes) => onNotesUpdate(position, rank, notes)`)
  needs no functional change.
- `if (!player) return null` guards the first render when `notesDialog`
  is null but the parent is mid-transition.
- The metadata strip uses `!= null` to handle both `null` and `undefined`
  cleanly (matches the JSON the backend sends — `bye_week: null`,
  `projected_points: null`).
- `player.adp` is a string; truthy-check on `""` correctly omits.
- Outlook empty-string also evaluates falsy → placeholder branch.
- Reuses existing `.dialog-textarea`, `.dialog-buttons`, `.btn-primary`,
  `.btn-cancel` classes from `App.css` so the inner widgets stay
  visually consistent with other dialogs.

### Styles — `PlayerDetailDialog.css`

```css
.player-detail-dialog {
  /* Override the App.css `dialog { min-width: 320px }` default */
  min-width: 720px;
  max-width: 90vw;
  max-height: 80vh;
  padding: 0;             /* header + body manage their own padding */
  display: flex;          /* dialog is one column: header on top, body fills */
  flex-direction: column;
  overflow: hidden;       /* dialog itself never scrolls; panels do */
}

.pdd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
  font-weight: bold;
}

.pdd-title { letter-spacing: 0.5px; }

.pdd-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
}
.pdd-close:hover { color: var(--text-primary); background: rgba(255, 255, 255, 0.05); }

.pdd-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  flex: 1 1 auto;
  min-height: 0;          /* required for nested overflow:auto to work */
}

.pdd-left, .pdd-right {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.pdd-left {
  border-right: 1px solid var(--border);
}

.pdd-meta {
  color: var(--text-muted);
  font-size: 11px;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.pdd-outlook {
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;  /* preserve paragraph breaks if any */
  overflow-y: auto;
  flex: 1 1 auto;
}

.pdd-outlook-empty {
  color: var(--text-muted);
  font-style: italic;
  font-size: 12px;
}

.pdd-notes {
  flex: 1 1 auto;
  min-height: 0;
  margin-bottom: 0;       /* override App.css's .dialog-textarea margin if any */
}

.pdd-buttons {
  margin-top: 12px;
  justify-content: flex-end;
}
.pdd-buttons button { flex: 0 0 auto; padding: 6px 18px; }

/* Narrow viewports — stack vertically */
@media (max-width: 700px) {
  .player-detail-dialog {
    min-width: 0;
    width: 92vw;
  }
  .pdd-body {
    grid-template-columns: 1fr;
  }
  .pdd-left {
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
}
```

**Layout reasoning**:
- `dialog { padding: 0 }` so the header's border-bottom can span edge-
  to-edge. Inner sections re-apply their own padding.
- `min-height: 0` on `.pdd-body` + `.pdd-left` + `.pdd-right` is the
  CSS-grid/flex idiom that lets nested `overflow: auto` actually
  trigger (the default `min-height: auto` would let content push the
  parent open).
- `white-space: pre-wrap` preserves single-line breaks inside `outlook`
  if any. Most outlook blurbs are one long paragraph, so this is
  belt-and-suspenders; harmless when blurbs lack newlines.
- The narrow-viewport stack keeps both panels usable on a tablet. The
  init explicitly de-prioritizes mobile drafting, so this is "doesn't
  look broken when resized", not a fully tuned mobile UX.

### `WarRoom.jsx` — Import + Render

Two surgical edits. No prop changes upstream.

```jsx
// Line 4: rename import
- import NotesDialog from './NotesDialog'
+ import PlayerDetailDialog from './PlayerDetailDialog'

// Lines 107-114: swap component name + drop `position` prop (lives on player)
  {notesDialog && (
-    <NotesDialog
+    <PlayerDetailDialog
      isOpen={true}
      player={notesDialog.player}
-      position={notesDialog.position}
      onSave={(notes) => onNotesUpdate(notesDialog.position, notesDialog.player.position_rank, notes)}
      onClose={onNotesClose}
    />
  )}
```

The `notesDialog` *state name* in App.jsx and the `onNotesUpdate` /
`onNotesClose` prop names stay as-is. They describe what the state
holds (the notes-save flow), which still accurately describes the
right-panel behaviour. Renaming them would churn six lines in App.jsx
for no functional gain — see Scope Expansion #2.

### Design Tokens (reaffirmed)
- Dialog background: existing `dialog { background: var(--bg-secondary) }`
- Border / divider: `var(--border)` (`#1E3A5F`)
- Muted text (metadata strip + placeholder): `var(--text-muted)` (`#6A8CAA`)
- Primary text: existing default
- Font: `var(--font)` (monospace)
- Accent on focus: `var(--accent)` via existing `.dialog-textarea:focus`

---

## Implementation Steps

### Step 1 — Create `PlayerDetailDialog.{jsx,css}`
**Files**:
- `frontend/src/components/PlayerDetailDialog.jsx` (create)
- `frontend/src/components/PlayerDetailDialog.css` (create)

Write both files per the Technical Specification.

**Validation**:
```bash
wc -l frontend/src/components/PlayerDetailDialog.jsx \
     frontend/src/components/PlayerDetailDialog.css
ls frontend/src/components/PlayerDetailDialog.*
```
- [ ] Both files exist
- [ ] JSX < 500 lines (target: ~60)
- [ ] CSS < 500 lines (target: ~80)

> No build run yet — Step 3 is the first build. The intermediate state
> (new component present but unused, NotesDialog still referenced) is
> internally consistent but not worth a per-step Vite invocation.
> Same per-step-build deferral pattern as PRP-020.

---

### Step 2 — Swap `WarRoom.jsx` import + render; delete `NotesDialog.jsx`
**Files**:
- `frontend/src/components/WarRoom.jsx`
- `frontend/src/components/NotesDialog.jsx` (`git rm`)

Apply the two edits from the spec (import rename, render swap +
drop `position` prop). Then `git rm` the old file.

**Validation**:
```bash
grep -rn "NotesDialog" frontend/src/
# expected: zero matches
git status --short frontend/src/components/
```
- [ ] Zero remaining `NotesDialog` references anywhere in `frontend/src/`
- [ ] `git status` shows `D NotesDialog.jsx` and `A PlayerDetailDialog.{jsx,css}` and `M WarRoom.jsx`

---

### Step 3 — Full build + sanity
**Validation**:
```bash
source .venv/bin/activate
pytest tests/ -q
ruff check backend/ tests/
cd frontend && npx vite build
```
- [ ] 98 tests pass, 1 skipped (baseline; no test count change expected)
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
Open `http://localhost:5173` and walk the manual checklist (see
Testing Requirements below). If browser isn't available in the
execution environment, say so explicitly — do not claim success.

---

### Step 5 — Commit + push
```bash
git add frontend/src/components/PlayerDetailDialog.jsx \
        frontend/src/components/PlayerDetailDialog.css \
        frontend/src/components/WarRoom.jsx \
        initials/21-init-player-detail-dialog.md
git rm frontend/src/components/NotesDialog.jsx

git commit -m "feat: PlayerDetailDialog — outlook + notes split-panel"
git push origin main
```

---

## Testing Requirements

### Unit Tests (`backend/utils/`)
- **None**. No backend code is changed; baseline 98 tests still pass.

### API Tests (curl, local)
- **None**. No API surface change.

### Manual Browser Tests (post-deploy checklist)
Reworded from the init to align with current code (Q3-driven
correction marked **★**):

- [ ] Click a seeded player name (e.g. Josh Allen) → dialog opens with
  two-panel layout
- [ ] Header reads `📋 Josh Allen · QB · BUF` with close ✕ at the
  right
- [ ] Left panel metadata strip reads `Proj 428.3 · ADP 3.05 · Bye 7`
- [ ] Outlook prose renders below the strip in the left panel
- [ ] Long outlook scrolls within the left panel without breaking
  layout (the dialog itself does not scroll)
- [ ] Right panel shows the existing notes textarea, pre-populated with
  saved notes if any
- [ ] Typing in notes does not affect outlook
- [ ] Save persists notes and closes (existing behavior)
- [ ] **★** Close discards in-flight notes silently — *there is no
  dirty-state warning today; this PRP does not add one* (existing
  behavior preserved)
- [ ] Esc key closes dialog (native `<dialog>` behavior — verify no
  regression)
- [ ] Click on Aaron Rodgers (no ADP) → metadata reads `Proj X · Bye Y`
  with no ADP segment and no broken separators
- [ ] Add a player via the toolbar AddPlayer dialog with no outlook
  and no metadata. Click that player. Outlook panel shows
  *"No outlook available."* in italic muted text. Metadata strip is
  not rendered. Notes textarea works normally.
- [ ] Drag the browser window to <700px wide. Panels stack vertically:
  outlook on top, notes below.
- [ ] Dialog still works in Draft Mode (same component, no mode-aware
  behavior — verify no regression)
- [ ] No console errors

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | 98 passed, 1 skipped (baseline, no change) | ☐ |
| 2 | `ruff check backend/ tests/` | Clean | ☐ |
| 3 | `cd frontend && npx vite build` | Build clean | ☐ |
| 4 | `grep -rn "NotesDialog" frontend/src/` | Zero matches | ☐ |
| 5 | `uvicorn backend.main:app --reload` | Starts, no errors | ☐ |
| 6 | Browser: click Josh Allen | Two-panel dialog opens; Proj/ADP/Bye populated; outlook visible | ☐ |
| 7 | Browser: header reads `📋 Josh Allen · QB · BUF` | Match | ☐ |
| 8 | Browser: long outlook on a long-blurb player (any seeded RB) | Scrolls within left panel; dialog doesn't grow past ~80vh | ☐ |
| 9 | Browser: click Aaron Rodgers | Metadata reads `Proj X · Bye Y` (no ADP) | ☐ |
| 10 | Browser: type notes, click Save | Notes persist; dialog closes | ☐ |
| 11 | Browser: open same player again | Notes pre-populated | ☐ |
| 12 | Browser: type notes, click Close | Edits discarded silently (existing behavior) | ☐ |
| 13 | Browser: Esc closes dialog | Closes; no console error | ☐ |
| 14 | Browser: add a player with no outlook / no metadata; click them | "No outlook available." placeholder; no metadata strip; textarea works | ☐ |
| 15 | Browser: resize window to <700px | Panels stack vertically | ☐ |
| 16 | Browser: enter Draft Mode, click a player name | Dialog still opens (existing behavior — but note: drafting mode disables `onNameClick` in `PlayerRow.jsx` today; verify) | ☐ |

> Step 16 note: looking at `PlayerRow.jsx:73` (draft branch), the
> player name `<span>` in Draft Mode has no `onClick` handler. So the
> dialog won't open from a click in Draft Mode — same as today, not a
> regression. Document this in the result column when running the test.

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| `player` is null | Race during state transition | `if (!player) return null` guard at top of component |
| `player.outlook === ""` | Manually-added player or missing seed field | Falsy check renders the italic placeholder |
| `player.adp === ""` | Aaron Rodgers, Geno Smith, etc. (PRP-019 cases) | Truthy check omits the ADP segment cleanly |
| `player.projected_points === null` | Manually-added player who skipped the field | `!= null` check omits the Proj segment |
| `player.bye_week === null` | Manually-added player or unsigned player in seed (Mendoza, Beck, Watson are in CSV but outside the top-30 cap, so unlikely in practice) | `!= null` check omits the Bye segment |
| Vite build error | Stale NotesDialog import somewhere | Step 2's grep catches this before build |
| Native `<dialog>` not supported | Very old browser | App already uses `<dialog>` elsewhere; no new browser requirement |

---

## Open Questions

All three init Open Questions resolved (see Context →
"Open Question Resolutions"). No outstanding blockers.

---

## Rollback Plan

1. `git revert <commit-sha>` on `main`
2. `git push origin main`
3. **Local**: Vite HMR picks up the revert — `NotesDialog.jsx` is
   restored, `PlayerDetailDialog.{jsx,css}` are removed. WarRoom.jsx
   import goes back to NotesDialog.
4. **Production**: on EC2 run `./scripts/deploy.sh` (which itself
   runs `git pull origin main`).
5. **S3 / on-disk JSON cleanup**: none — pure frontend change, no
   schema or data touched.

Rollback is trivial and risk-free.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Component JSX/CSS spec given verbatim. All three init Open Questions resolved against live code, with file:line citations. The two Files-Touched corrections (NotesDialog.css doesn't exist, App.jsx untouched) are surfaced as scope *contractions*, not silent simplifications. |
| Feasibility | 10 | Pure frontend, ~60 JSX + ~80 CSS lines, zero backend / API / schema work. Reuses existing `var(--text-muted)`, `.dialog-textarea`, `.dialog-buttons` styling. Native `<dialog>` element already in use across the app. |
| Completeness | 10 | All affected files identified (including the implicit ones — verified `NotesDialog.css` doesn't exist; verified App.jsx state shape already carries the full player object; verified Step 16 Draft-Mode quirk in `PlayerRow.jsx`). Manual test checklist reworded where init was inaccurate (Q3). |
| Alignment | 10 | No ADR conflict. Single-user JSON-persistence / FastAPI + React stack respected. Surfaces existing data, doesn't add any new architectural pattern. Matches operator's stated "keep rows tight" preference by intentionally *not* adding row-level metadata. |
| **Average** | **10.0** | Ready for execution. |

---

## Notes

### Why pass the full `player` object instead of separate props
Init §"Props shape" explicitly calls for this — and it's right.
PRP-019 added six fields; another schema expansion is plausible
(`risk` / `upside` may surface later; `notes` history may be
considered). Each future expansion would otherwise touch both the
dialog props list and every callsite. Whole-object pass-through is
already the pattern in `DeleteConfirmDialog` (`player` prop) and
fits naturally here.

### Why `<dialog>` `padding: 0` instead of overriding inner padding
The App.css default `dialog { padding: 24px }` would shrink the
inner panels' available width and prevent the header's
`border-bottom` from spanning edge-to-edge. Zero-padding the dialog
and letting the header/body manage their own padding gives the
split-panel layout the full dialog rectangle.

### Why no test count change
No backend code touched. No tests are added or removed — the only
tests in the repo are backend unit tests. Frontend has no automated
tests by design (per `docs/TESTING.md`, "Frontend has zero unit
tests — manual browser verification is the test for UI changes").

### File-size considerations
- `PlayerDetailDialog.jsx` ~60 lines (was 33 in `NotesDialog.jsx`).
- `PlayerDetailDialog.css` ~80 lines (was 0 — `NotesDialog` had no
  CSS file).
- `WarRoom.jsx` ~+0 lines net (one import rename, one prop dropped).

All well under 500. No split planned.
