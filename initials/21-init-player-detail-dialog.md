# 21 — Player Detail Dialog (Outlook + Notes Split Panel)

## Goal

Extend the existing single-panel NotesDialog into a two-panel
PlayerDetailDialog: the left panel shows the player's projection
metadata (Proj / ADP / Bye) and Fantasy Footballers' outlook blurb;
the right panel keeps the existing notes textarea. Both panels visible
at the same time so the analyst commentary and the user's own
scouting notes inform each other.

Pure frontend change. No backend work, no API changes, no schema
changes — PRP-019 already captured all the data we need; this PRP
just surfaces it.

## Context

- PRP-019 enriched every seeded player record with 6 new fields:
  `bye_week`, `adp`, `projected_points`, `risk`, `upside`, `outlook`.
  Currently none are visible in the UI — they sit in S3 doing nothing.
- The war room row design is intentionally tight (operator's words:
  "tight as in nice"). After deliberation, **no per-row metadata is
  being added**. Bye/ADP/Proj surface only in the player detail view.
- `risk` and `upside` are intentionally NOT surfaced anywhere in the
  UI. Data continues to be captured and stored (no schema change), but
  no UI affordance shows them. They can be wired up later if needed.
- The existing NotesDialog (per the operator's screenshot) is a small
  centered modal with:
  - Header: `📋 Derrick Henry · BAL` and a close ✕
  - Textarea with placeholder "Add scouting notes..."
  - Save / Close buttons
  This PRP grows that dialog into a two-panel layout.

## Design

### Dialog identity

**Rename the component** from `NotesDialog` to `PlayerDetailDialog`.

Rationale: the dialog is no longer just about notes. Keeping the old
name would mislead future readers — the textarea is one of two panels
now, not the whole content. The `NotesDialog.jsx` / `NotesDialog.css`
files are renamed to `PlayerDetailDialog.jsx` / `PlayerDetailDialog.css`
(create + delete, not rename-in-place — same convention as PRP-020's
TagPicker → ContextMenu transition for clean git history).

All callsites of `<NotesDialog>` in `WarRoom.jsx` (or wherever it's
mounted) update to `<PlayerDetailDialog>`. The dialog's props gain
`outlook`, `projected_points`, `adp`, `bye_week`, and `position` (the
existing props of `player`, `notes`, `onSave`, `onClose` stay).

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  📋 Derrick Henry · RB · BAL                              ✕    │
├──────────────────────────────┬─────────────────────────────────┤
│ Proj 281.7 · ADP 1.08 · Bye 14                                 │
│                              │                                  │
│ Henry remains one of the     │  [textarea]                      │
│ most physically dominant     │                                  │
│ runners in the league...     │  Add scouting notes...           │
│                              │                                  │
│ (rest of outlook, scrollable)│                                  │
│                              │                                  │
│                              │              [Save]  [Close]     │
└──────────────────────────────┴─────────────────────────────────┘
```

**Header**: existing 📋 icon, player name, position pill (NEW —
inserted between name and team), team abbreviation, close ✕. Single
horizontal row across the full dialog width.

The position addition is small but important: `Derrick Henry · BAL`
becomes `Derrick Henry · RB · BAL`. Consistent with the way the rest
of the app references players.

**Left panel — Player Info**:
- Metadata strip at the top (one line, muted color): `Proj 281.7 · ADP 1.08 · Bye 14`
- Empty values are handled per the rules below
- Outlook prose fills the rest of the panel, with `overflow-y: auto`
- For players with no outlook (manually-added players, where the field
  is `""`), show a placeholder: *"No outlook available."* in muted
  text, italic. The metadata strip still shows whatever's available.

**Right panel — Notes**:
- The existing textarea, exactly as it works today
- Save / Close buttons aligned to the bottom-right of this panel
- Existing save/dirty behavior preserved

### Metadata strip — empty-value handling

For each of the three metadata fields, when empty:

| Field | When empty (`""`, `None`, etc.) | Render as |
|---|---|---|
| `projected_points` | None | omit the `Proj X.X` segment |
| `adp` | `""` | omit the `ADP X.X` segment |
| `bye_week` | None | omit the `Bye N` segment |

So a player with all three values shows `Proj 281.7 · ADP 1.08 · Bye 14`.
A player with no ADP (e.g. Aaron Rodgers at first release) shows
`Proj 245.2 · Bye 6` — separators rebuild correctly around omitted
segments.

A player with none of the three fields shows nothing (the strip simply
isn't rendered). For seeded players this won't happen. For
manually-added players who skipped these fields, the strip is empty
and the outlook panel shows just the placeholder text.

### Dialog dimensions

- **Desktop (≥ 700px viewport)**: dialog grows from current ~320px to
  ~720px wide. Two panels side-by-side.
- **Narrow viewports (< 700px)**: panels stack vertically — outlook on
  top, notes below. Via CSS media query. This is a courtesy for tablet
  *viewing*; drafting remains desktop-only.
- **Vertical sizing**: the dialog should grow to fit content but cap at
  ~80% viewport height. Both panels share that height. The outlook
  panel and the notes textarea each scroll within their bounds.

### Color treatment

Match the existing app design system (per CLAUDE.md):
- Background: `#0D1B2A` (existing dialog background)
- Metadata strip text: a muted gray (use existing `var(--text-muted)`
  if defined, else `#6B7B8C` or whatever the current NotesDialog uses
  for placeholder text)
- Outlook prose: standard primary text color
- Outlook placeholder ("No outlook available."): same muted gray as
  metadata strip, italic
- Panel divider: thin vertical rule between the two panels — use
  `1px solid var(--border)` or whatever the existing column dividers
  use, consistent with the war room's column dividers

### Component file shape

The new `PlayerDetailDialog.jsx` ends up at roughly:
- ~100 lines of JSX (still well under the 500 line limit)
- Imports the position abbreviation from POSITIONS for the header pill
- One stateful piece: the notes textarea value (unchanged from current
  NotesDialog behavior)
- Outlook is read-only — no state, just rendered from props

### Props shape (PlayerDetailDialog)

```javascript
<PlayerDetailDialog
  player={{
    name: "Derrick Henry",
    team: "BAL",
    position: "RB",
    notes: "<existing user notes>",
    outlook: "<FF Boys' blurb>",
    projected_points: 281.7,
    adp: "1.08",
    bye_week: 14,
  }}
  isOpen={true}
  onSave={(notes) => ...}    // existing
  onClose={() => ...}        // existing
/>
```

Note: rather than passing each field as a separate top-level prop,
take the whole player object as one prop. Cleaner, fewer
prop-drilling churn points if the schema grows again.

## Frontend Architecture

### Files touched

```
frontend/src/components/NotesDialog.jsx           # DELETE — replaced
frontend/src/components/NotesDialog.css           # DELETE — replaced
frontend/src/components/PlayerDetailDialog.jsx    # CREATE — new component
frontend/src/components/PlayerDetailDialog.css    # CREATE — new styles
frontend/src/components/WarRoom.jsx               # MODIFY — rename import,
                                                  #          update render to
                                                  #          pass full player obj
frontend/src/App.jsx                              # MODIFY (if applicable) —
                                                  #          state name updates
                                                  #          if NotesDialog state
                                                  #          lives in App
```

Code should verify during PRP generation where the NotesDialog state
currently lives (likely App.jsx but possibly WarRoom.jsx) and update
accordingly.

### What is NOT changed

- No backend changes. The API already returns the full 13-field player
  record per PRP-019.
- No `PlayerRow.jsx` changes — the row itself stays exactly as it is.
  The dialog is what changes when you click a player name.
- No context menu changes — the menu from PRP-020 stays.
- No data model changes — `risk` and `upside` remain in the player
  record, just not displayed.

## Tests

### Backend
- None. No backend code changed.

### Frontend
- No automated frontend tests exist. Manual browser walk-through only.

### Manual browser test checklist (post-deploy)

- [ ] Click any seeded player name → dialog opens with two-panel layout
- [ ] Header shows player name · position · team · close ✕
- [ ] Left panel shows metadata strip with Proj / ADP / Bye
- [ ] Left panel shows outlook blurb below the metadata strip
- [ ] Long outlook scrolls within its panel without breaking layout
- [ ] Right panel shows the existing notes textarea
- [ ] Typing in notes does not affect outlook
- [ ] Save persists notes and closes (existing behavior)
- [ ] Close without saving warns of unsaved changes if dirty (existing
      behavior — verify no regression)
- [ ] Esc key closes dialog (existing behavior — verify no regression)
- [ ] Click on a player with no ADP (e.g. Aaron Rodgers) → metadata
      shows `Proj X · Bye Y` only, no ADP segment, no broken separator
- [ ] Manually add a player via the toolbar AddPlayer dialog with no
      outlook / no metadata. Click that player. Outlook panel shows
      "No outlook available." placeholder. Metadata strip is absent.
      Notes panel works normally.
- [ ] At narrow window width (drag browser to <700px), panels stack
      vertically. Outlook on top, notes below.
- [ ] No console errors

## Out of Scope

- Surfacing `risk` and `upside` anywhere. Captured in data, hidden in UI.
- Showing metadata on the player row itself. Operator preference: keep
  the war room visually tight.
- Editing outlook from the UI. Outlook is seed data, read-only.
- Showing the dialog in Draft Mode in a different way. Same dialog
  works in both modes (existing behavior preserved).
- Keyboard navigation within the dialog beyond Esc-to-close.
- Tablet/mobile drafting workflow. Drafting is desktop-only.

## Files Touched

(Repeated for clarity)

- `frontend/src/components/PlayerDetailDialog.jsx` — new
- `frontend/src/components/PlayerDetailDialog.css` — new
- `frontend/src/components/NotesDialog.jsx` — delete
- `frontend/src/components/NotesDialog.css` — delete
- `frontend/src/components/WarRoom.jsx` — import + render update
- `frontend/src/App.jsx` — if NotesDialog state lives here, rename
  state and pass full player object

## Constraints Reminder

- File size limit: 500 lines per file. `PlayerDetailDialog.jsx` ~100
  lines, comfortable margin.
- Atomic commit after feature complete.
- Single `feat:` commit message: e.g. `feat: PlayerDetailDialog —
  outlook + notes split-panel`
- No backend changes, no test count changes, no deploy data steps.

## Deploy

Pure frontend change. No backend logic, no schema, no S3 touch.

```bash
ssh ubuntu@98.94.138.178
cd ff-draft-room && ./scripts/deploy.sh
```

The `deploy.sh` script handles `git pull`, vite build, and nginx
restart. No re-seed, no environment variables, no S3 operations.

After deploy: click any player on `ff.jurigregg.com` and walk the
manual checklist above.

## Open Questions for PRP

1. **Where does NotesDialog state currently live?** App.jsx or
   WarRoom.jsx? PRP should verify and update only what's needed.
2. **Is there an existing `var(--text-muted)` or similar in the CSS?**
   If yes, use it. If not, define one in App.css as part of this PRP
   for the metadata strip and placeholder text.
3. **Does the existing NotesDialog have a dirty-state check on close?**
   If yes, that behavior carries forward (unchanged). If no, this PRP
   doesn't add one — out of scope.

## Follow-ups (out of scope for this PRP)

- **Init-22**: read-only demo site at `ffdemo.jurigregg.com` (the demo
  site we keep parking). The richer player detail dialog from this PRP
  will be visible there too once the demo is built — a nice side
  benefit.
- Future surfacing of `risk` / `upside` if operator changes mind
- Future editing of outlook (very unlikely — outlook is FF Boys'
  analyst content, not user content)
- Future click-to-expand metadata on rows if operator changes mind
  about per-row density
