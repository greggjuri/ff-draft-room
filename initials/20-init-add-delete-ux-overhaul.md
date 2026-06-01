# 20 — Add/Delete UX Overhaul

## Goal

Three coordinated UI changes that share the theme "add and delete
players, done right":

1. **Toolbar gains an `+ ADD PLAYER` button.** Replaces the per-tier
   `+ {POSITION} · Tier N` strips that sit at the bottom of every tier
   group. With 8 tiers across 4 columns, that's 32 repeated UI elements
   eating real estate for an action used rarely.
2. **AddPlayer dialog expands from 2 fields to ~10.** With PRP-019's
   richer player schema (tier, bye_week, adp, projected_points, risk,
   upside, outlook) now in place, manually-added players should be able
   to populate all of them. The expanded dialog asks for each.
3. **Delete moves into a restructured context menu.** The always-visible
   `×` button on every player row is removed. The existing single-row
   icon strip context menu (7 tags on one row) is split into two
   submenus: **Tags ▸** (the existing 7) and **Edit ▸** (currently just
   Delete, room to grow). Hover-to-open on desktop, click-to-open on
   touch.

## Context

- PRP-019 expanded the player record to 13 fields. The seed path emits
  all 13; `add_player()` accepts all 13 as kwargs with `None`/`""`
  defaults. The frontend dialog currently only collects 2 (name, team)
  and the new fields stay empty until manually edited. This PRP closes
  that gap.
- Operator confirms manual add is still needed (unsigned WRs landing on
  rosters late summer); delete is rarer but real (preseason injuries
  ending careers). Both stay in the app, just relocated to be less
  visually noisy.
- The current toolbar lives in the sticky header: `SAVE · SAVE AS ·
  LOAD · RESET · ★ SET DEFAULT`. The `+ ADD PLAYER` button slots in
  *before* SAVE, separated by a visual divider — Add is a data-entry
  action; the rest manage profile state.
- The existing context menu is a horizontal icon strip with 7 tag
  icons. Each tag click toggles the tag on/off. This stays — the new
  submenu structure preserves that behavior, just nests it one level
  deeper.

## Design

### 1. Toolbar — new `+ ADD PLAYER` button

**Position**: leftmost button in the toolbar group, before `SAVE`.

**Visual separator**: a thin vertical rule between `+ ADD PLAYER` and
`SAVE` to group "data entry" vs "profile management."

```
[+ ADD PLAYER]  |  SAVE  SAVE AS  LOAD  RESET  ★ SET DEFAULT
```

**Color**: use the existing Honolulu Blue `#0076B6` accent for the
button border / text, same as `SAVE`. Don't introduce a new color —
the divider is what signals "different group of actions."

**Behavior**: opens the new AddPlayer dialog (see §2). No contextual
auto-fill — position and tier are user-entered dropdowns/inputs in the
dialog, not pre-filled from a button click.

**Visibility**: shown in War Room mode only, hidden in Draft Mode (same
rule that hides SAVE / SAVE AS / etc.).

### 2. AddPlayer dialog — expanded

**Layout**: two-column grid for short fields, full-width `outlook`
textarea at the bottom. Required fields marked with `*`, optional
fields shown without asterisk. All optional fields can be left blank
and submit to the backend as `None`/`""`.

```
┌─ Add Player ──────────────────────────────────────────────┐
│                                                            │
│  Name *           [_____________________]                  │
│  Team *           [____]    Position *  [QB ▼]             │
│  Tier *           [___]     Bye Week    [___]              │
│  ADP              [_____]   Projected   [_____]            │
│  Risk             [___]     Upside      [___]              │
│                                                            │
│  Outlook                                                   │
│  [_______________________________________________________] │
│  [_______________________________________________________] │
│  [_______________________________________________________] │
│                                                            │
│                                          [Cancel] [Add]    │
└────────────────────────────────────────────────────────────┘
```

**Field details**:

| Field | Required | Type | Validation |
|---|---|---|---|
| Name | ✓ | text | non-empty |
| Team | ✓ | text | non-empty (FA is fine, just type "FA") |
| Position | ✓ | select (QB/RB/WR/TE) | must be one of POSITIONS |
| Tier | ✓ | number | int ≥ 1 |
| Bye Week | optional | number | int 5-14 OR empty |
| ADP | optional | text | any string (lax — accept "3.05", "19.11", etc.) |
| Projected Points | optional | number | float OR empty |
| Risk | optional | number | float 0-10 OR empty |
| Upside | optional | number | float 0-10 OR empty |
| Outlook | optional | textarea | any string (multi-line OK) |

**Empty handling**: blank optional fields send `null` (numerics) or
`""` (strings) to the backend. The current `add_player()` signature
from PRP-019 already accepts these as defaults — no backend logic
change needed for empty handling, just for accepting the values when
present (see §5).

**Submit**: dialog validates required fields locally (non-empty
name/team, valid position, integer tier ≥ 1). On success, calls
`POST /api/rankings/{position}/add` with the new request body shape.
On failure, shows inline error.

**Position field placement**: the original dialog inferred position
from which "+ QB · Tier 3" button was clicked. With the contextual
button gone, position becomes an explicit dropdown. Default to QB
unless we have a better heuristic (we don't — the user could be adding
any position).

### 3. Remove per-tier `+ {POSITION} · Tier N` strips

Delete from `TierGroup.jsx`. The strip currently renders at the bottom
of every tier group with text like `+ QB · Tier 3`. After this PRP, it
doesn't render at all — the toolbar `+ ADD PLAYER` is the only add
path.

**Net visual gain**: 32 strips × roughly one row height each ≈ a real
estate win across the war room. Tier groups become visually tighter.

### 4. Remove `×` delete button from every player row

Delete from `PlayerRow.jsx`. The `×` button currently sits at the
right edge of every player name box. After this PRP, no inline delete
affordance — right-click context menu only.

**The existing `DeleteConfirmDialog` stays.** The context menu Delete
action invokes the same dialog, preserving the "are you sure?" step.

### 5. Restructure context menu — Tags ▸ / Edit ▸

**Current state**: right-click a player → horizontal icon strip with 7
tag icons. Clicking an icon toggles that tag on the player.

**New state**: right-click a player → small menu with two items:

```
┌──────────────┐
│  Tags     ▸  │
│  Edit     ▸  │
└──────────────┘
```

**Hovering `Tags ▸` (desktop) or tapping `Tags ▸` (touch) opens a
submenu** showing the 7 existing tags, each as `icon + label` on its
own row:

```
┌──────────────┐ ┌─────────────────┐
│  Tags     ▸  ├─│  ❤  Love        │
│  Edit     ▸  │ │  🔥 Breakout    │
└──────────────┘ │  💎 Sleeper     │
                 │  ⚠  Risky       │
                 │  ✚  Handcuff    │
                 │  ☠  Avoid       │
                 │  🚩 Red Flag    │
                 └─────────────────┘
```

Tag click behavior preserved: toggle on/off (clicking an already-set
tag removes it; clicking a different tag replaces the current one,
since a player can only have one tag at a time — confirm this is the
current behavior in the codebase).

**Hovering / tapping `Edit ▸` opens a submenu**, currently with one
item:

```
┌──────────────┐ ┌─────────────────┐
│  Tags     ▸  │ │  Delete         │ ← red text
│  Edit     ▸  ├─└─────────────────┘
└──────────────┘
```

**Delete row styling**: red text (`#D32F2F` or whatever red the
existing `ResetConfirmDialog`'s confirm button uses — match the
convention). No icon. Click → existing `DeleteConfirmDialog` →
existing delete flow.

**Edit submenu is intentionally sparse.** Room to grow (future:
"Rename", "Move to tier...", "Set notes..."). One item is fine for
now.

### 6. Hover-vs-click submenu behavior

CSS-only switching via `@media (pointer: fine)` (mouse) and `@media
(pointer: coarse)` (touch).

```css
/* Desktop: submenu opens on hover */
@media (pointer: fine) {
  .context-menu-item:hover > .submenu { display: block; }
}

/* Touch: submenu opens on click via JS toggle */
@media (pointer: coarse) {
  .context-menu-item > .submenu { display: none; }
  .context-menu-item.open > .submenu { display: block; }
}
```

JS handles the click case: tapping a parent item adds `.open` to it,
which trumps the hover rule. Tapping outside closes everything.

**Keyboard navigation** (arrow keys, Enter): explicitly deferred. The
app is single-user, mouse-driven, no current keyboard affordances.

## Frontend Architecture

### Components touched

```
WarRoom.jsx                     # Toolbar — add new button
WarRoom.css                     # Toolbar — divider, spacing
AddPlayerDialog.jsx             # Major expansion: 2 → 10 fields
AddPlayerDialog.css             # Grid layout
TierGroup.jsx                   # Remove "+ tier" strip
TierGroup.css                   # Remove .add-strip rules
PlayerRow.jsx                   # Remove × button
PlayerRow.css                   # Remove .delete-btn rules
ContextMenu.jsx (or wherever)   # Major restructure: strip → submenus
ContextMenu.css                 # Submenu positioning, hover/click rules
api/rankings.js                 # addPlayer() — new request body
```

(Component file names approximate — verify against actual codebase
during execution.)

### Backend changes — router request body

The `POST /api/rankings/{position}/add` request body grows from
`{ name, team }` to:

```python
class AddPlayerBody(BaseModel):
    name: str
    team: str
    tier: int
    bye_week: int | None = None
    adp: str = ""
    projected_points: float | None = None
    risk: float | None = None
    upside: float | None = None
    outlook: str = ""
```

`position` stays a path parameter (`/api/rankings/{position}/add`),
**not** a body field. The router signature already extracts it from
the path — keep that pattern.

The router handler then calls `add_player()` with the existing
positional args (`profile, name, team, position, tier`) plus the new
fields as kwargs.

**Backwards compatibility note**: this is a breaking change to the
request body, but the only caller is our own frontend, which is being
updated in lockstep. No external API consumers exist.

### `api/rankings.js` — `addPlayer()`

```javascript
export async function addPlayer(position, body) {
  // body = { name, team, tier, bye_week?, adp?, projected_points?, risk?, upside?, outlook? }
  return await authFetch(`/api/rankings/${position}/add`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
```

Frontend constructs the body from dialog state. Empty inputs become
`null` (numerics) or `""` (strings) before send. Position is passed as
the URL segment.

## Tests

### Backend
- `tests/test_rankings.py`: existing `add_player` tests pass unchanged
  (the new kwargs are optional with defaults). One new test:

  ```python
  def test_add_player_full_kwargs():
      """Caller supplying all 6 optional kwargs round-trips correctly."""
      profile = _sample_profile()
      result = add_player(
          profile, "Test", "FA", "QB", tier=3,
          bye_week=9, adp="12.05", projected_points=250.0,
          risk=4.5, upside=8.0, outlook="Some blurb.",
      )
      new_player = next(p for p in result["players"] if p["name"] == "Test")
      assert new_player["bye_week"] == 9
      assert new_player["adp"] == "12.05"
      assert new_player["projected_points"] == 250.0
      assert new_player["risk"] == 4.5
      assert new_player["upside"] == 8.0
      assert new_player["outlook"] == "Some blurb."
  ```

- Router test for the expanded `AddPlayerBody` schema: rejects missing
  required fields, accepts request with only required fields, accepts
  request with all fields.

### Frontend
- No automated frontend tests exist; manual browser test only.

### Manual browser test checklist (post-deploy)
- [ ] Toolbar shows `+ ADD PLAYER` before `SAVE` with visual divider
- [ ] Tier groups no longer have `+ {POSITION} · Tier N` strips
- [ ] Player rows no longer have `×` button
- [ ] Right-click on a player shows new context menu with Tags / Edit
- [ ] Tags submenu opens on hover (desktop) / click (touch)
- [ ] Tags submenu shows all 7 tags with icon + label
- [ ] Clicking a tag toggles it on the player (existing behavior preserved)
- [ ] Edit submenu opens on hover/click
- [ ] Edit > Delete shows red text
- [ ] Edit > Delete → opens DeleteConfirmDialog (existing) → confirms → player gone
- [ ] `+ ADD PLAYER` opens expanded dialog with all 10 fields
- [ ] Dialog validates required fields; rejects empty name/team/position/tier
- [ ] Dialog accepts blank optional fields; new player has null/empty values
- [ ] Dialog with all fields filled: new player has all values correctly
- [ ] Added player appears at the bottom of the specified tier

## Out of Scope

- Keyboard navigation in context menus (arrow keys, Enter). Deferred
  indefinitely; single-user mouse/touch app.
- Adding more items to the Edit submenu beyond Delete. Future PRPs
  (Rename, Move to tier, etc.) plug in here easily.
- Demo site (init-21).
- Any change to the existing tag set, tag toggle behavior, or
  DeleteConfirmDialog.
- Mobile-specific layout tuning beyond making the context menu work on
  touch. The war room layout itself stays as-is for this PRP.

## Files Touched

**Frontend (estimated)**:
- `frontend/src/components/WarRoom.jsx`
- `frontend/src/components/WarRoom.css`
- `frontend/src/components/AddPlayerDialog.jsx`
- `frontend/src/components/AddPlayerDialog.css`
- `frontend/src/components/TierGroup.jsx`
- `frontend/src/components/TierGroup.css`
- `frontend/src/components/PlayerRow.jsx`
- `frontend/src/components/PlayerRow.css`
- `frontend/src/components/ContextMenu.jsx` (or actual filename)
- `frontend/src/components/ContextMenu.css`
- `frontend/src/api/rankings.js`

**Backend**:
- `backend/routers/rankings.py` — expanded `AddPlayerBody` schema, pass
  new fields through to `add_player()`

**Tests**:
- `tests/test_rankings.py` — one new test for full-kwargs add
- `tests/<router_tests>.py` — if router-level tests exist for the add
  endpoint, update request body fixtures

## Constraints Reminder

- File size limit: 500 lines per file. `AddPlayerDialog.jsx` will grow
  noticeably — if it pushes past 400 lines, consider splitting the
  field-rendering helpers into a separate file.
- Atomic commit after feature complete.
- `from __future__ import annotations` already in affected backend files.
- Python 3.9 / Node 18+ compatibility.

## Open Questions for PRP

1. **Tag toggle semantics**: confirm in code — does clicking an
   *already-set* tag remove it, or do nothing? Init assumes "removes
   it" per operator confirmation. PRP should verify against current
   implementation and align.
2. **Touch event handling for context menu**: draft-time use is
   desktop-only per operator, so the iOS long-press case is not a
   correctness requirement. The CSS `@media (pointer: coarse)` rule
   stays in the spec (cheap, future-proofs for tablet warroom
   *viewing*) but PRP need not verify or fix iOS behavior. Confirm
   only that the desktop `oncontextmenu` path works as today.
3. **Color for Delete text**: match existing destructive-action red
   (find it in `ResetConfirmDialog` or `DeleteConfirmDialog` CSS) vs
   pick a new one. PRP should pick the existing convention.
4. **Optional field rendering of `null` values in the war room**: out
   of scope here (UI for the new fields isn't being built in this PRP)
   but worth noting that null `bye_week`/`adp`/etc. on a manually-added
   player will appear blank wherever those fields surface in future UI
   work. Future PRPs handle that gracefully.

## Follow-ups (out of scope for this PRP)

- init-21: read-only demo site at `ffdemo.jurigregg.com`
- Future UI to actually *display* the new fields (bye_week, adp, etc.)
  in the war room rows or expanded player detail views
- Possible Edit submenu additions: Rename, Move to tier, Set notes
- Keyboard navigation for context menus, if ever desired
