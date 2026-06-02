# 22 — PlayerDetailDialog in Draft Mode

## Goal

Let the PlayerDetailDialog open in Draft Mode, not just in War Room
mode. During a live draft, the ability to glance at a player's outlook
and bye week is more valuable than during pre-draft prep — you're
actively deciding between two or three players with a pick clock
ticking. The data and the dialog already exist; this PRP wires the
click handler on the Draft Mode branch of PlayerRow.jsx so it actually
opens.

## Context

- PRP-021 created PlayerDetailDialog and wired the click handler on
  the **War Room** branch of `PlayerRow.jsx`. The **Draft Mode** branch
  was left alone — that branch has different rendering (status dot,
  different colored backgrounds for `mine`/`other` picks) and at the
  time of PRP-021 was out of scope.
- Per Code's PRP-021 Step 16 note: `PlayerRow.jsx:73` (Draft Mode
  branch) has no `onClick` on the player name `<span>`. Clicking a
  player in Draft Mode does nothing.
- The fix is small in code terms (~one wired-up handler), but there
  are real interaction questions to resolve because Draft Mode has
  existing click behavior on the player row — the **status dot cycle**
  (undrafted → mine → other → undrafted) per the existing memory.
- Mid-draft usage pattern: pick clock running, comparing 2-3 players,
  want to see outlook + bye week for each. The dialog should open
  fast and dismiss fast (Esc).

## Design

### The interaction model

In Draft Mode, the player row currently has:
- **Status dot on the left** — click to cycle status
- **Player name area** — no click handler (the regression we're fixing)
- **Reorder buttons (▲▼)** — already hidden in Draft Mode per existing behavior
- **× delete button** — gone since PRP-020

After this PRP:
- **Status dot on the left** — click to cycle status (unchanged)
- **Player name** — click to open PlayerDetailDialog (new)
- **Right-click anywhere on the row** — context menu (Tags / Edit) opens
  (already works in both modes per PRP-020)

The two click targets are spatially distinct (dot is on the far left,
name fills the rest of the row). No collision risk if implemented
correctly.

### What stays the same in Draft Mode

- **Drafted status colors**: `mine` players still have the dark green
  background, `other` players still have the vivid purple background.
  Click-to-open-dialog does not change visual treatment of the row.
- **Notes saving**: if you save notes from within the dialog during a
  draft, those notes persist to S3 just like in War Room mode. Notes
  are user-owned data; draft mode doesn't make them ephemeral. This is
  the same behavior the dialog already exhibits in War Room mode.
- **The dialog itself**: no mode-aware behavior inside PlayerDetailDialog.
  Same component, same props, same rendering. The dialog doesn't even
  know what mode the app is in.

### The actual code change

In `PlayerRow.jsx`, the Draft Mode branch (around line 73 per Code's
PRP-021 note) currently renders something like:

```jsx
<span className="player-name">{player.name}</span>
```

Becomes:

```jsx
<span
  className="player-name"
  onClick={() => onNameClick(position, player)}
>
  {player.name}
</span>
```

The `onNameClick` prop is the same one already wired in the War Room
branch. The parent (`TierGroup` → `WarRoom` → `App`) already has the
handler — it sets the `notesDialog` state which renders the dialog.

That's the whole change. ~3 lines of JSX, ~0 lines of new logic.

### Question to resolve at PRP time

**Cursor style for the name span in Draft Mode.** The War Room branch
likely already has `cursor: pointer` on the player name (because it
opens the dialog). The Draft Mode branch may not. After this PRP,
both should have it. PRP should verify the CSS rule's selector covers
both branches, or add a new rule if not.

## Out of Scope

- **Disabling the dialog or making it read-only in Draft Mode.** The
  full functionality stays available, including notes editing/saving.
  Arguments either way, but the simpler answer is "the dialog works
  the same in both modes" — fewer code paths, less to test, no
  unexpected behavior differences.
- **A "compact" dialog variant for Draft Mode.** The full dialog is
  fine. If real-world draft use suggests the dialog is too large or
  takes too long to dismiss, that's a separate UX iteration.
- **Auto-close on draft action.** When you click a status dot to mark
  a player drafted, the dialog (if open for that player) does not
  auto-close. The two interactions are independent. If real-world use
  suggests this is annoying, easy follow-up.
- **Keyboard shortcuts to open the dialog** (e.g. hover + spacebar).
  Out of scope; Draft Mode remains mouse-driven.
- **Mode-aware visual treatment of the dialog itself** (e.g. dimmer
  background during a draft to reduce eye strain). Out of scope.

## Files Touched

- `frontend/src/components/PlayerRow.jsx` — wire `onClick` on the
  Draft Mode branch's player name span
- `frontend/src/components/PlayerRow.css` — verify (and add if
  missing) `cursor: pointer` on `.player-name` for the Draft Mode
  branch

Likely 5-10 lines of change total across both files.

## Tests

### Backend
- None. No backend code touched.

### Frontend
- No automated frontend tests exist.

### Manual browser test checklist

- [ ] Enter Draft Mode (toggle in header)
- [ ] Click any player's name → PlayerDetailDialog opens
- [ ] Dialog shows the same content as in War Room mode
  (header / metadata strip / outlook / notes textarea)
- [ ] Click the status dot of the same row → dialog does NOT open
  (status cycles instead — existing behavior preserved, no collision)
- [ ] Right-click anywhere on the row → context menu opens
  (Tags / Edit — existing PRP-020 behavior preserved)
- [ ] In the open dialog, type notes, click Save → notes persist;
  return to Draft Mode, click player again → notes pre-populated
  (proving save worked across the dialog open/close cycle)
- [ ] Esc key closes dialog (existing behavior)
- [ ] Click a player marked as `mine` (green) → dialog opens normally;
  background of the row is still green
- [ ] Click a player marked as `other` (purple) → dialog opens
  normally; background still purple
- [ ] Switch from Draft Mode to War Room while dialog is open → dialog
  remains open (it's a modal, mode toggle is in the header behind it).
  This is fine — close the dialog, mode swap takes effect normally.

## Constraints Reminder

- File size limit: 500 lines (PlayerRow.jsx well under)
- Atomic commit
- Single `feat:` commit message
- No backend changes, no test count changes, no deploy data steps

## Deploy

```bash
ssh ubuntu@98.94.138.178
cd ff-draft-room && ./scripts/deploy.sh
```

Standard. No re-seed, no S3 work, no env var changes.

## Open Questions for PRP

1. **Line number for the Draft Mode branch in PlayerRow.jsx.** Code's
   PRP-021 note cited line 73. PRP-022 should re-verify since the
   exact line may have shifted with PRP-021's WarRoom.jsx changes
   (it shouldn't have, since PRP-021 didn't touch PlayerRow.jsx, but
   verify).
2. **Is `cursor: pointer` already on `.player-name`, or branch-scoped?**
   If branch-scoped to War Room only, this PRP needs to extend the
   selector. If it's on the base class, no CSS work needed beyond
   verification.
3. **Click target overlap with status dot.** Visual inspection in the
   live app should confirm there's no visible overlap between the dot's
   click area and the name span. If the row is small enough that they
   abut, may need a small gap or pointer-events tweak. Code should
   verify during PRP review and surface if it's an issue.
4. **Is `onNameClick` already passed as a prop to `PlayerRow` in
   Draft Mode**, or does the parent conditionally omit it for the
   Draft branch? PRP should verify the prop chain.

## Follow-ups (out of scope for this PRP)

- **Init-23 (demo site).** Still queued. Will inherit PlayerDetailDialog
  with the Draft-Mode click handler — the demo site can use the dialog
  in read-only mode regardless.
- **Auto-close dialog on status dot click**, if real draft use shows it's
  needed.
- **Compact dialog variant** for during-draft use, if the full dialog
  proves too heavy mid-pick.
- **Hover-to-preview** instead of click-to-open, if click feels too
  committed. Cheaper interaction, but harder to scan multiple players
  fluidly. Worth considering only if real use surfaces the need.
