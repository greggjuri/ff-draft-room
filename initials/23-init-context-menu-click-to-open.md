# 23 — Context Menu Submenus: Hover → Click

## Goal

Replace the current hover-to-open behavior on the context menu's Tags
and Edit submenus with click-to-open. The hover model is fragile in
real use — moving the mouse across the small gap between a parent
item and its submenu can cause the submenu to close before the user
reaches the item they want. This is especially painful for Delete,
which requires extra precision and is the consequence of a missed
click trail.

Pure frontend interaction fix. No backend, no API, no schema. About
30-50 lines of state and event-handling changes.

## Context

- PRP-020 created the current context menu with Tags ▸ / Edit ▸
  submenus using a `@media (pointer: fine)` hover rule for desktop
  and `@media (pointer: coarse)` click rule for touch. The hover path
  was the chosen "elegant" desktop behavior at the time.
- In practice the hover behavior is unreliable: the operator reports
  that submenus frequently close mid-traverse, requiring multiple
  attempts to pick a tag or (especially) reach Delete.
- This is a well-known issue with web-based hover submenus — the
  user's mouse can momentarily exit the parent's bounding box while
  crossing the gap to the submenu, which closes the submenu before
  the user reaches the intended item.
- Click-to-open eliminates this entirely. It also unifies desktop and
  touch into a single code path, collapsing the `@media (pointer: ...)`
  branching from PRP-020.

## Design

### The new interaction model

**Parent items (Tags, Edit)** are clickable. Clicking a parent opens
its submenu. Clicking the *same* parent again closes it (toggle).
Clicking the *other* parent closes the current submenu and opens the
new one (mutual exclusion).

**Submenu items (the 7 tags, or Delete)** are clickable. Clicking an
item performs its action (toggle tag, or open DeleteConfirmDialog)
*and* closes the entire context menu — same behavior as today.

**Closing the menu**:
- Click outside the context menu (existing behavior, already wired)
- Press Esc (existing behavior, already wired)
- Click any action item (existing behavior — tag toggle or Delete)

### Why click-to-open and not click-to-toggle

The init's question discussed two patterns:
- **Click-to-toggle**: same item click opens and closes its own submenu
- **Click-to-open with implicit close**: clicks elsewhere close the submenu

We're using **click-to-toggle for parents** + **mutually exclusive
submenus** + **all other clicks close everything**. This is the
standard desktop-app pattern and it's intuitive: the parent acts as
its own toggle, but clicking elsewhere (other parent, action item,
outside) cleans up.

### State model

The context menu component currently has no concept of which submenu
is open — it's CSS-driven via hover. After this PRP it needs explicit
state:

```jsx
const [openSubmenu, setOpenSubmenu] = useState(null)
// Values: null, 'tags', or 'edit'
```

**Transitions**:
- Click Tags parent: `setOpenSubmenu(openSubmenu === 'tags' ? null : 'tags')`
- Click Edit parent: `setOpenSubmenu(openSubmenu === 'edit' ? null : 'edit')`
- Click any tag in Tags submenu: invoke tag toggle, then close *entire* menu (existing path)
- Click Delete in Edit submenu: open DeleteConfirmDialog, then close *entire* menu (existing path)
- Esc or outside-click: close *entire* menu (existing path); `openSubmenu` resets implicitly when the menu unmounts

### CSS changes

**Remove**:
```css
@media (pointer: fine) {
  .cm-item:hover > .cm-submenu { display: block; }
}
@media (pointer: coarse) {
  .cm-item > .cm-submenu { display: none; }
  .cm-item.open > .cm-submenu { display: block; }
}
```

**Replace with**:
```css
.cm-submenu { display: none; }
.cm-item.open > .cm-submenu { display: block; }
```

Submenu visibility is now driven purely by the React state via the
`.open` class, applied conditionally based on `openSubmenu` value.
No more media query branching.

### Visual affordance — the `▸` arrows

Today the Tags and Edit parents already render with a `▸` arrow on
the right edge (per PRP-020). That arrow already communicates "this
opens something." After click-to-open, the arrow continues to mean
exactly that. **Optional small enhancement**: rotate the arrow 90°
(or change to `▾`) when the submenu is open, signaling state. This
is purely visual polish — not required for correctness, but it's the
kind of small detail that makes click-to-open feel responsive.

PRP can include this OR defer to a follow-up; my recommendation is
include it since we're already touching the components and the cost
is one line of conditional className.

### What does NOT change

- The 7 tags themselves, their icons, their labels, their colors,
  their toggle semantics
- The Delete row (red text, opens DeleteConfirmDialog)
- The right-click trigger on the player row
- Esc-to-close behavior
- Outside-click-to-close behavior
- The visual structure of the context menu (two parent items, two
  submenus, position, dimensions, fonts)
- Tag toggling behavior or DeleteConfirmDialog flow

Only the *opening mechanism* for submenus changes.

## Files Touched

- `frontend/src/components/ContextMenu.jsx` — add `openSubmenu` state,
  wire `onClick` on parent items, drop hover dependence
- `frontend/src/components/ContextMenu.css` — remove the two
  `@media (pointer: ...)` blocks, simplify to a single state-driven
  rule

Likely 30-50 LOC total across both files.

## Tests

### Backend
None. No backend touched.

### Frontend
No automated frontend tests exist. Manual browser walkthrough only.

### Manual browser test checklist

- [ ] Right-click any player → context menu opens with Tags / Edit parents
- [ ] Click Tags parent → submenu opens, 7 tags visible
- [ ] Click Tags parent again → submenu closes
- [ ] Click Tags parent (opens), then move mouse slowly across to a tag
      and click it → tag toggles successfully (the bug we're fixing)
- [ ] Click Tags parent (opens), then click Edit parent → Tags closes,
      Edit opens (mutual exclusion)
- [ ] Click Edit parent → Delete row visible
- [ ] Click Delete → DeleteConfirmDialog opens, context menu closes
- [ ] Click outside menu while submenu is open → both close
- [ ] Esc while submenu is open → both close
- [ ] No "intermittent close" behavior — submenus stay open until
      explicitly closed by user action
- [ ] Same behavior in both War Room and Draft Mode
- [ ] Optional: arrow rotation when submenu open (`▸` → `▾`)
- [ ] No console errors

### Specifically test the bug we're fixing
- [ ] Open Tags submenu, move mouse along the gap between parent and
      submenu deliberately. Submenu should NOT close. (Today it does
      close; after this PRP it should not.)
- [ ] Open Edit submenu, click Delete row reliably on first try.
      (Today this is unreliable due to the hover fragility.)

## Out of Scope

- Adding more items to the Edit submenu (Rename, Move to tier — still
  parked, will plug in trivially after this PRP)
- Keyboard navigation (arrow keys, Enter to confirm) — still deferred
- Touch-specific testing — drafting is desktop-only per CLAUDE.md
- Changes to the tag icons, colors, or labels
- Animation / transition on submenu open/close
- Changes to the right-click trigger or menu positioning logic

## Files NOT Touched

- `frontend/src/components/PlayerRow.jsx` — right-click handler unchanged
- `frontend/src/components/TagPicker.*` — already deleted in PRP-020
- `frontend/src/components/DeleteConfirmDialog.*` — unchanged
- Any other component or CSS

## Deploy

Pure frontend change. Standard:

```bash
ssh ubuntu@98.94.138.178
cd ff-draft-room && ./scripts/deploy.sh
```

No re-seed, no S3 work, no environment variables, no data migration.

## Constraints Reminder

- File size limit: 500 lines (ContextMenu.jsx well under)
- Atomic commit, single `fix:` (this is a bug fix, not a feature)
- `fix: context menu submenus open on click instead of hover`
- No backend changes, no test count changes

## Open Questions for PRP

1. **Where does outside-click-to-close live currently?** ContextMenu
   itself, or up in a parent component? PRP should verify and ensure
   the existing handler also clears `openSubmenu` state (it should
   automatically when the menu unmounts, but worth confirming the
   unmount path).

2. **Esc handler — where does it live?** Same question. Likely
   already correct since the menu fully unmounts, but verify.

3. **Are the Tags and Edit parents currently `<button>` or `<div>`
   elements?** If they're `<div>`s for styling reasons, the PRP needs
   to add `role="button"` and keyboard handling, or just convert to
   `<button>`. If already `<button>`, no a11y churn needed.

4. **Arrow rotation polish (`▸` → `▾`)** — include in this PRP or
   defer? My init recommendation: include, since we're touching the
   render anyway. PRP can defer if it adds complexity I'm not seeing.

## Follow-ups (out of scope for this PRP)

- The "spring cleaning" doc/cleanup work that's parked
- init-24 (demo site, if it ever gets prioritized)
- Phase 2 live-draft features (round/pick tracker, best available,
  scarcity alerts, roster needs)
- Future Edit submenu additions (Rename, Move to tier, etc.)
