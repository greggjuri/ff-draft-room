# PRP-023: Context Menu Submenus — Hover → Click

**Created**: 2026-06-01
**Initial**: `initials/23-init-context-menu-click-to-open.md`
**Status**: Draft

---

## Overview

### Problem Statement
The PRP-020 ContextMenu opens its `Tags ▸` and `Edit ▸` submenus on
mouse hover (desktop) via `@media (pointer: fine) { .cm-item:hover >
.cm-submenu { display: block } }`. In real use the operator reports
that submenus close mid-traverse: as the cursor crosses the gap
between the parent item and the submenu, it leaves both bounding
boxes for an instant and the hover rule snaps the submenu shut. The
problem is acute for `Edit ▸ Delete`, which is one missed click away
from a re-attempt loop.

### Proposed Solution
Pure frontend interaction fix. Replace hover-to-open with
click-to-open. Pleasant surprise on inspection: the click-toggle
plumbing already exists — `openSub` state at `ContextMenu.jsx:18`,
`toggleSub` handler at line 41, and the `.cm-item.open > .cm-submenu`
CSS rule. The only thing creating the hover behaviour is the
`@media (pointer: fine)` block at `ContextMenu.css:43-45`. Removing
it (and collapsing the `(pointer: coarse)` wrapper to a single
state-driven rule) makes click-to-open work on both desktop and
touch with one code path.

Three small enhancements ride along, all inside the same two files:

1. **Rename** `openSub` → `openSubmenu` for clarity (init's preferred
   name; the state is exposed enough in the JSX that the longer name
   reads better).
2. **Rotate the parent arrow** `▸` → `▾` when its submenu is open —
   one ternary in the className, signals state changes are responsive.
3. **Convert parent `<div>`s to `<button>`s** for free a11y wins
   (Enter / Space activate, correct ARIA role, native focus ring).
   No keyboard navigation work — `<button>` gives us the
   activation-key handling for free without committing to arrow-key
   submenu nav (still deferred per init §"Out of Scope").

### Success Criteria
- [ ] Clicking `Tags ▸` opens the Tags submenu; clicking it again
  closes the same submenu (toggle).
- [ ] Clicking `Edit ▸` while Tags is open closes Tags and opens
  Edit (mutual exclusion).
- [ ] Submenu stays open during slow mouse traversal across the gap
  to a child item — no intermittent close.
- [ ] Clicking a tag row toggles the tag and closes the entire menu
  (existing behaviour preserved).
- [ ] Clicking `Edit ▸ Delete` opens the existing
  `DeleteConfirmDialog` and closes the entire menu (existing
  behaviour preserved).
- [ ] Esc closes the entire menu (existing behaviour preserved).
- [ ] Outside-click closes the entire menu (existing behaviour
  preserved).
- [ ] Arrow rotates from `▸` to `▾` when the parent's submenu is open.
- [ ] No `@media (pointer: …)` blocks remain in `ContextMenu.css`.
- [ ] `pytest tests/ -q` passes (target: **98**, no delta — no
  backend / no tests touched).
- [ ] `ruff check backend/ tests/` clean (baseline preserved).
- [ ] `uvicorn backend.main:app --reload` starts (sanity).
- [ ] `cd frontend && npx vite build` clean.

---

## Context

### Related Documentation
- `docs/PLANNING.md` — Architecture, React component layout
- `docs/DECISIONS.md` — ADR-006 (FastAPI + React, full CSS control);
  no new ADR — interaction-model fix, not architectural.
- `prps/20-prp-add-delete-ux-overhaul.md` — Created the ContextMenu
  with the hover/click branched behaviour being fixed here
- `initials/23-init-context-menu-click-to-open.md` — Full spec

### ADR Alignment
No ADR conflict. Single-user / JSON / React stack unchanged. The
`@media (pointer: ...)` branching from PRP-020 was a "best of both
worlds" attempt that turned out worse-than-both in practice; click-
to-open collapses to one code path.

### Dependencies
- **Required**: PRP-020 (`ContextMenu.jsx` exists). Verified.
- **Optional**: none.

### Open Question Resolutions (Init §"Open Questions for PRP")

| Init Question | Resolution |
|---|---|
| **Q1**: Where does outside-click-to-close live? | **Inside `ContextMenu.jsx`** at lines 20-31 — `document.mousedown` listener checks `!ref.current.contains(e.target)`. Cleanup at lines 27-30 removes the listener on unmount. `openSub` state is local to the component, so it dies with the unmount automatically. No additional reset wiring needed. |
| **Q2**: Where does the Esc handler live? | **Same `useEffect`** at line 24 (`document.keydown` for `Escape` → `onClose()`). Cleanup at line 29 removes it. Same automatic state cleanup. |
| **Q3**: Are parents `<div>` or `<button>`? | **`<div>`** — `ContextMenu.jsx:48-51` and `:67-70`. PRP converts them to `<button type="button">` for free a11y wins (Enter/Space activation, correct ARIA role, focus-ring). No keyboard arrow-key navigation added (still deferred per init §"Out of Scope"). |
| **Q4**: Include arrow rotation polish? | **Yes** — one ternary in className. Negligible cost, real responsiveness signal. The arrow is already there; rotating it on open completes the affordance. |

### Files to Modify / Create / Delete
```
frontend/src/components/ContextMenu.jsx   # MODIFY — rename openSub→openSubmenu;
                                          #          <div> → <button>; arrow rotation
frontend/src/components/ContextMenu.css   # MODIFY — drop @media (pointer: fine)
                                          #          and the @media (pointer: coarse)
                                          #          wrapper; collapse to one rule;
                                          #          reset <button> default styling
initials/23-init-context-menu-click-to-open.md   # untracked; include in commit
```

### Scope Expansion vs. Init
None. Init lists `ContextMenu.{jsx,css}` — same two files modified
here. The three rider enhancements (rename, arrow rotation, button
conversion) all live inside those two files and were explicitly
discussed in the init's Open Questions (Q3 for buttons, Q4 for arrow).

### Files NOT Modified (intentional)
```
backend/**                                          # No backend work
frontend/src/api/rankings.js                        # No API change
frontend/src/App.jsx                                # Same ContextMenu
                                                    #  props/wiring
frontend/src/components/PlayerRow.jsx               # Right-click trigger
                                                    #  unchanged
frontend/src/components/DeleteConfirmDialog.jsx     # Same flow
data/players/**                                     # Read-only seed
```

---

## Technical Specification

### `ContextMenu.jsx` — New version

```jsx
import { useEffect, useRef, useState } from 'react'
import './ContextMenu.css'

const TAGS = [
  { key: 'heart',   icon: '❤',  label: 'Love'     },
  { key: 'fire',    icon: '🔥', label: 'Breakout' },
  { key: 'gem',     icon: '💎', label: 'Sleeper'  },
  { key: 'warning', icon: '⚠',  label: 'Risky'    },
  { key: 'cross',   icon: '✚',  label: 'Hurt'     },
  { key: 'skull',   icon: '☠',  label: 'Avoid'    },
  { key: 'flag',    icon: '🚩', label: 'Red flag' },
]

export default function ContextMenu({
  activeTag, position, onTagSelect, onDelete, onClose,
}) {
  const ref = useRef(null)
  const [openSubmenu, setOpenSubmenu] = useState(null)  // null | 'tags' | 'edit'

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) onClose()
    }
    function handleKey(e) { if (e.key === 'Escape') onClose() }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [onClose])

  const x = Math.min(position.x, window.innerWidth - 260)
  const y = Math.min(position.y + 8, window.innerHeight - 80)

  const handleTagClick = (key) => {
    const newTag = key === activeTag ? '' : key
    onTagSelect(newTag)
  }

  const toggleSubmenu = (k) => (e) => {
    e.stopPropagation()
    setOpenSubmenu(prev => prev === k ? null : k)
  }

  const renderParent = (key, label) => {
    const isOpen = openSubmenu === key
    return (
      <button
        type="button"
        className={`cm-item ${isOpen ? 'open' : ''}`}
        onClick={toggleSubmenu(key)}
      >
        <span>{label}</span>
        <span className="cm-arrow">{isOpen ? '▾' : '▸'}</span>
        {/* submenu rendered as a sibling div, positioned absolutely */}
      </button>
    )
  }

  return (
    <div ref={ref} className="context-menu" style={{ left: x, top: y }}>
      <div className={`cm-item-wrapper ${openSubmenu === 'tags' ? 'open' : ''}`}>
        {renderParent('tags', 'Tags')}
        <div className="cm-submenu cm-submenu-tags">
          {TAGS.map(t => (
            <button
              key={t.key}
              type="button"
              className={`cm-tag-row ${activeTag === t.key ? 'active' : ''}`}
              onClick={(e) => { e.stopPropagation(); handleTagClick(t.key) }}
            >
              <span className={`cm-tag-icon tag-${t.key}`}>{t.icon}</span>
              <span className="cm-tag-label">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className={`cm-item-wrapper ${openSubmenu === 'edit' ? 'open' : ''}`}>
        {renderParent('edit', 'Edit')}
        <div className="cm-submenu cm-submenu-edit">
          <button
            type="button"
            className="cm-edit-row cm-delete"
            onClick={(e) => { e.stopPropagation(); onDelete() }}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Key change from current**:
- `<div className="cm-item">` parents → `<button type="button" className="cm-item">`.
- Each parent is now wrapped in a `<div className="cm-item-wrapper">`
  that owns the `.open` class for CSS. Reason: `.cm-submenu` is
  positioned `absolute` relative to its parent and renders as a
  sibling of the `<button>`. A `<button>` cannot contain block-level
  children like an absolutely-positioned div without invalid HTML
  semantics, so the wrapper holds both the button and the submenu.
  The CSS rule `.cm-item-wrapper.open > .cm-submenu` selects on the
  wrapper's `.open` class — which `renderParent` synchronises with the
  button's `.open` class via the same `isOpen` boolean.
- `openSub` → `openSubmenu` (rename for clarity).
- `toggleSub` → `toggleSubmenu` (matches the state name).
- Arrow shows `▾` when its submenu is open, `▸` otherwise.
- `<button type="button">` everywhere prevents any future inadvertent
  form-submit behaviour and gives the parent items Enter / Space
  activation for free.

**What stays the same**:
- Component props (`activeTag`, `position`, `onTagSelect`, `onDelete`,
  `onClose`).
- `useEffect` for outside-click + Esc — verbatim.
- `handleTagClick` toggle semantics — verbatim.
- `e.stopPropagation()` on parent clicks (stops the click from
  bubbling to the document `mousedown` listener that would close
  the menu — though strictly that listener runs on `mousedown` not
  `click`, so the stop is belt-and-suspenders. Keep it.).
- The 7 tag rows + their icons / labels / colors / active highlight.
- The Delete row red colour.
- Position clamping (`Math.min(...)`) for viewport edges.

### `ContextMenu.css` — New version

```css
.context-menu {
  position: fixed;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px;
  min-width: 140px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  font-family: var(--font);
  font-size: 12px;
}

.cm-item-wrapper {
  position: relative;     /* anchor for absolutely-positioned submenu */
}

.cm-item {
  /* Reset native <button> styling first */
  appearance: none;
  background: transparent;
  border: none;
  font-family: var(--font);
  font-size: 12px;
  /* Existing layout */
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 6px 10px;
  cursor: pointer;
  border-radius: 4px;
  color: var(--text-primary);
  text-align: left;
}
.cm-item:hover { background: rgba(255, 255, 255, 0.06); }
.cm-item.open  { background: rgba(255, 255, 255, 0.06); }
.cm-item:focus-visible { outline: 1px solid var(--accent); outline-offset: -1px; }

.cm-arrow { color: var(--text-muted); font-size: 10px; }

.cm-submenu {
  position: absolute;
  left: 100%;
  top: -4px;
  margin-left: 4px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px;
  min-width: 160px;
  display: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

/* Single rule, click-driven via React state. No media queries. */
.cm-item-wrapper.open > .cm-submenu { display: block; }

.cm-tag-row, .cm-edit-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 6px 8px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-family: var(--font);
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  border-radius: 4px;
}
.cm-tag-row:hover, .cm-edit-row:hover { background: rgba(255, 255, 255, 0.06); }
.cm-tag-row.active { background: rgba(0, 118, 182, 0.18); }

.cm-tag-icon { font-size: 18px; line-height: 1; width: 20px; text-align: center; }
.cm-tag-icon.tag-heart   { color: #E03030; }
.cm-tag-icon.tag-warning { color: #F0B429; }
.cm-tag-icon.tag-skull   { color: #E0E0E0; }
.cm-tag-icon.tag-cross   { color: #E03030; }

.cm-delete { color: var(--danger); }
.cm-delete:hover { background: rgba(192, 57, 43, 0.15); color: var(--danger); }
```

**Changes from current CSS**:
- New `.cm-item-wrapper` rule (1 line: `position: relative`) so the
  absolutely-positioned `.cm-submenu` anchors to it instead of the
  button.
- `.cm-item` rule gains four native-button reset properties
  (`appearance`, `background`, `border`, `font-family`) and a
  `width: 100%` + `text-align: left` to match the previous `<div>`
  rendering byte-for-byte. The original layout properties
  (display/padding/cursor/border-radius/color) are preserved.
- New `.cm-item.open { background: ... }` rule so the parent stays
  highlighted while its submenu is open (visual feedback for
  "this is the active parent").
- New `.cm-item:focus-visible` rule for keyboard / accessibility
  focus indication.
- **Removed**: both `@media (pointer: fine)` and `@media (pointer:
  coarse)` blocks.
- **Replaced** with one rule: `.cm-item-wrapper.open > .cm-submenu
  { display: block }`.

### Design tokens
Nothing new. Reuses existing `var(--bg-secondary)`, `var(--border)`,
`var(--accent)`, `var(--text-muted)`, `var(--danger)`, `var(--font)`.

---

## Implementation Steps

### Step 1 — Update `ContextMenu.jsx`
**Files**: `frontend/src/components/ContextMenu.jsx`

Replace the file body with the new version per the spec. Key
diff-points to verify after edit:
- `openSubmenu` (renamed from `openSub`)
- `toggleSubmenu` (renamed from `toggleSub`)
- Both parents wrapped in `<div className="cm-item-wrapper ...open?...">`
- Both parents are `<button type="button" className="cm-item ...open?...">`
- Arrow shows `▾` when `isOpen`, `▸` otherwise
- All tag-row + Delete-row `<button>`s gain `type="button"` (currently
  missing — same issue, free safety)

**Validation**:
```bash
grep -n "openSub\b\|toggleSub\b" frontend/src/components/ContextMenu.jsx
# expected: zero matches (renamed everywhere)

grep -n "@media\|hover.*display: block" frontend/src/components/ContextMenu.css
# this step shouldn't have touched CSS yet — Step 2 does
```

- [ ] Zero matches for old names
- [ ] `<button type="button"` appears on all four button instances
  (2 parents + tag-row template + delete row)

---

### Step 2 — Update `ContextMenu.css`
**Files**: `frontend/src/components/ContextMenu.css`

Replace the file body with the new version per the spec.

**Validation**:
```bash
grep -n "@media (pointer:" frontend/src/components/ContextMenu.css
# expected: zero matches

grep -n "cm-item-wrapper" frontend/src/components/ContextMenu.css
# expected: at least two matches (the wrapper rule + the submenu open rule)
```

- [ ] No `@media (pointer:` blocks remain
- [ ] `.cm-item-wrapper` rule exists with `position: relative`
- [ ] `.cm-item-wrapper.open > .cm-submenu { display: block }` is the
  sole open-state rule

---

### Step 3 — Full build + sanity
**Validation**:
```bash
source .venv/bin/activate
pytest tests/ -q
ruff check backend/ tests/
cd frontend && npx vite build
```
- [ ] 98 tests pass, 1 skipped (baseline, no change expected)
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

Open `http://localhost:5173`, right-click a player, and walk the
manual checklist (Testing Requirements below). If browser is not
available, say so explicitly — do not claim success.

---

### Step 5 — Commit + push
```bash
git add frontend/src/components/ContextMenu.jsx \
        frontend/src/components/ContextMenu.css \
        initials/23-init-context-menu-click-to-open.md

git commit -m "fix: context menu submenus open on click instead of hover"
git push origin main
```

> Per CLAUDE.md commit conventions, this is `fix:` not `feat:` — the
> hover behaviour was a usability bug.

---

## Testing Requirements

### Unit Tests (`backend/utils/`)
- **None**. No backend code is changed.

### API Tests (curl, local)
- **None**. No API surface change.

### Manual Browser Tests (post-deploy checklist)

Core behavior:
- [ ] Right-click any player → context menu opens with Tags / Edit
  parents and `▸` arrows
- [ ] Click `Tags ▸` → submenu opens, arrow rotates to `▾`, 7 tags
  visible
- [ ] Click `Tags` again → submenu closes, arrow rotates back to `▸`
- [ ] Click `Tags` (opens), then click `Edit` → Tags closes, Edit opens
  (mutual exclusion)
- [ ] Click any tag → tag toggles on the player, entire menu closes
- [ ] Click `Edit ▸ Delete` → `DeleteConfirmDialog` opens, context
  menu closes
- [ ] Esc closes the entire menu (works with submenu open too)
- [ ] Click outside menu closes the entire menu (works with submenu
  open too)

The bug being fixed:
- [ ] **Open Tags submenu, deliberately move mouse along the gap
  between parent and submenu. Submenu does NOT close.** (Today
  it does close — the regression test.)
- [ ] **Open Edit submenu, click Delete reliably on first try.**
  (Today this is unreliable.)

Cross-mode regression:
- [ ] Same behavior in War Room mode
- [ ] Same behavior in Draft Mode (PRP-022 wired Draft-mode
  right-click — verify no regression)

Visual / a11y:
- [ ] Parent arrow rotates `▸` → `▾` when its submenu opens
- [ ] Parent stays subtly highlighted while its submenu is open
- [ ] Tab key focuses the parent buttons (`:focus-visible` ring
  visible — accent-blue outline)
- [ ] Enter / Space on a focused parent toggles its submenu
  (free from `<button>` semantics — not formally an a11y feature
  but a nice side effect)
- [ ] No console errors

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | 98 passed, 1 skipped (baseline) | ☐ |
| 2 | `ruff check backend/ tests/` | Clean | ☐ |
| 3 | `cd frontend && npx vite build` | Build clean | ☐ |
| 4 | `grep -n "@media (pointer:" frontend/src/components/ContextMenu.css` | Zero matches | ☐ |
| 5 | `grep -n "openSub\b\|toggleSub\b" frontend/src/components/ContextMenu.jsx` | Zero matches (renamed) | ☐ |
| 6 | Browser: right-click player → click `Tags` | Submenu opens, `▸` → `▾` | ☐ |
| 7 | Browser: click `Tags` again | Submenu closes, `▾` → `▸` | ☐ |
| 8 | Browser: open `Tags`, then click `Edit` | Tags closes, Edit opens | ☐ |
| 9 | Browser: open `Tags`, slow-traverse mouse to a tag | Submenu stays open (bug fix) | ☐ |
| 10 | Browser: click a tag | Tag toggles, menu closes | ☐ |
| 11 | Browser: open `Edit` → click Delete | DeleteConfirmDialog opens, menu closes | ☐ |
| 12 | Browser: Esc with submenu open | Entire menu closes | ☐ |
| 13 | Browser: outside-click with submenu open | Entire menu closes | ☐ |
| 14 | Browser: Draft Mode → right-click → same flow | Identical behavior to War Room | ☐ |
| 15 | Browser: keyboard Tab to parent → Space | Submenu toggles | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| Parent click bubbles to document listener and closes menu | `stopPropagation` missing on parent button | `toggleSubmenu(...)` calls `e.stopPropagation()` first — preserved from current code |
| Submenu opens then closes immediately | If we forgot `stopPropagation` on inner buttons | Tag-row and Delete-row buttons keep their existing `e.stopPropagation()` calls |
| Both submenus open simultaneously | If state allowed it | `setOpenSubmenu(prev => prev === k ? null : k)` plus the `isOpen = openSubmenu === key` check on each wrapper guarantees mutual exclusion |
| Button picks up form-submit behaviour | If a future ancestor adds a `<form>` | `type="button"` on every `<button>` prevents accidental submits |
| Submenu off-screen | Right-click near viewport edge | Existing `Math.min(position.x, window.innerWidth - 260)` and y-clamp preserved |

---

## Open Questions

All four init Open Questions resolved against live code (see Context →
"Open Question Resolutions"). No outstanding blockers.

---

## Rollback Plan

1. `git revert <commit-sha>` on `main`
2. `git push origin main`
3. **Local**: Vite HMR picks up the revert — ContextMenu returns to
   the PRP-020 hover behavior immediately.
4. **Production**: on EC2 run `./scripts/deploy.sh` (it runs
   `git pull origin main` itself).
5. **S3 / on-disk JSON cleanup**: none — pure interaction-model change,
   no schema or data touched.

Rollback is trivial and risk-free. Any tag/delete actions taken while
the click-to-open version was live persist normally; only the
*mechanism* for opening submenus reverts.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Both files rewritten with full content. All four init Open Questions resolved with file:line citations. The `<button>` wrapping subtlety (can't nest absolutely-positioned div in button cleanly) flagged and addressed via the `.cm-item-wrapper` div. |
| Feasibility | 10 | Two-file frontend change. `openSubmenu` state + `toggleSubmenu` handler + `.open` class plumbing already exist in PRP-020's code — this PRP mostly just deletes the hover branch and renames for clarity. No new dependencies. |
| Completeness | 10 | All affected behaviour identified: arrow rotation, button conversion, wrapper div for submenu anchoring, focus-visible ring, parent-stays-highlighted when open. Manual test plan includes specific regression tests for the bug being fixed plus a Draft-Mode cross-check (PRP-022 territory). |
| Alignment | 10 | No ADR conflict. Single-user / JSON / React stack respected. The `@media (pointer: ...)` cleanup reduces code paths — net simpler architecture. Init's commit prefix (`fix:` not `feat:`) honored. |
| **Average** | **10.0** | Ready for execution. |

---

## Notes

### Why a wrapper `<div>` around each parent button + submenu
The current code does `<div className="cm-item">…<div className="cm-submenu">…</div></div>`, with the submenu positioned absolutely relative to the parent `.cm-item` (which has `position: relative`). When the parent becomes a `<button>`, nesting the submenu inside it is technically invalid HTML — `<button>` content model disallows block-level descendants. Browsers render it but accessibility tools and some screen readers misbehave.

The wrapper pattern (`<div className="cm-item-wrapper">…<button>…</button><div className="cm-submenu">…</div></div>`) makes the button a leaf, sits the submenu as a sibling, and anchors the submenu to the wrapper instead. The `.open` class lives on the wrapper, but `renderParent` sets the same `isOpen` value on both the wrapper's class and the button's class so styling stays consistent.

### Why include button conversion and arrow rotation in the same PRP
Init's Q3 (button vs div) and Q4 (arrow rotation) both live entirely
inside the two files being edited. Bundling them avoids a second
churn cycle through these components for changes that take 3 lines
combined. Both are independently revertible if either misbehaves.

### Why no keyboard navigation work
Init §"Out of Scope" explicitly defers arrow-key submenu navigation.
The `<button>` conversion gives us Enter / Space activation for free
(no PRP work, just browser default behaviour) but doesn't commit to
arrow-key nav or focus-roving — a richer keyboard model is its own
PRP if it ever becomes a priority.

### File-size considerations
- `ContextMenu.jsx`: 84 → ~95 lines (the `renderParent` helper +
  wrapper divs add a handful of lines).
- `ContextMenu.css`: 78 → ~85 lines (button-reset properties +
  wrapper rule + focus-visible rule, minus the two media query
  blocks).

Both well under the 500-line limit.
