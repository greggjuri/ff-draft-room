# PRP-020: Add/Delete UX Overhaul

**Created**: 2026-05-31
**Initial**: `initials/20-init-add-delete-ux-overhaul.md`
**Status**: Draft

---

## Overview

### Problem Statement
Three friction points in the War Room UI all relate to the
add/delete-player flow:

1. **32 per-tier `+ {POSITION} · Tier N` buttons** (8 tiers × 4 columns)
   eat real estate for an action used a handful of times per draft prep.
2. **The AddPlayer dialog only collects 2 fields** (name, team) even
   though PRP-019 expanded the player record to 13 fields. Manually-added
   players have empty `bye_week`/`adp`/`projected_points`/`risk`/`upside`/
   `outlook` until somebody hand-edits the JSON — there is no UI path to
   populate them at insert time.
3. **An always-visible `×` delete button on every player row** turns a
   destructive, infrequently-used action into the visually loudest
   control on the row, and is one stray click away from data loss.

### Proposed Solution
Three coordinated UI changes plus a backend body-schema extension:

1. **Toolbar gets a single `+ ADD PLAYER` button**, leftmost, separated
   by a thin vertical rule from the profile-management group
   (SAVE / SAVE AS / LOAD / RESET / ★ SET DEFAULT). Hidden in Draft Mode.
2. **Delete the per-tier add strips** from `TierGroup.jsx` and the
   per-row `×` delete button from `PlayerRow.jsx`.
3. **Expand `AddPlayerDialog.jsx` from 2 → 10 fields**, with a Position
   dropdown (was inferred from the per-tier button), required Tier
   input, and 6 new optional inputs that map 1:1 to PRP-019's player
   fields. Blank optional inputs → `null`/`""` on the wire — the
   backend `add_player()` kwargs already default to those.
4. **Restructure the right-click context menu**. Today it's a
   horizontal 7-icon tag strip (`TagPicker.jsx`). After this PRP it's a
   small two-item parent menu (`Tags ▸` / `Edit ▸`) with submenus:
   - **Tags ▸** — vertical list of the 7 existing tags as `icon + label`
     rows; tag-toggle behaviour preserved.
   - **Edit ▸** — single Delete row (red text, matches existing
     `var(--danger)`); invokes the existing `DeleteConfirmDialog`.
   - Hover-to-open on desktop (`@media (pointer: fine)`), click-to-open
     on touch (`@media (pointer: coarse)`).

Backend: `AddPlayerRequest` Pydantic model gains 6 optional fields with
matching types/defaults; router passes them through as kwargs to the
already-extended `add_player()` from PRP-019. URL path still carries
position.

### Success Criteria
- [ ] Toolbar in War Room mode shows `+ ADD PLAYER` leftmost, followed
  by a vertical divider, then the existing 5 buttons unchanged. Hidden
  in Draft Mode.
- [ ] `TierGroup.jsx` renders no `+ {POSITION} · Tier N` buttons.
- [ ] `PlayerRow.jsx` renders no `×` button (War Room or Draft).
- [ ] Right-click on a player row opens a 2-item menu (Tags / Edit);
  hover (desktop) or click (touch) opens the appropriate submenu.
- [ ] Tags submenu: 7 vertical rows (icon + label); clicking toggles
  the same way as today (clicking active tag clears; clicking another
  replaces).
- [ ] Edit submenu: 1 Delete row in red (`var(--danger)`); click opens
  the existing `DeleteConfirmDialog` → confirms → player removed.
- [ ] AddPlayerDialog opens from the toolbar button with 10 fields
  (Name*, Team*, Position*, Tier*, Bye Week, ADP, Projected, Risk,
  Upside, Outlook); required fields validated client-side; optional
  blank fields submit as `null`/`""`.
- [ ] `POST /api/rankings/{position}/add` accepts the expanded body
  and the new fields are persisted on the resulting player record
  exactly as supplied (verified by curl with `tier=9, bye_week=8,
  adp="12.05", ...`).
- [ ] `pytest tests/ -q` passes (target: **98** = 97 baseline + 1 new
  `test_add_player_full_kwargs`).
- [ ] `ruff check backend/ tests/` clean.
- [ ] `uvicorn backend.main:app --reload` starts.
- [ ] `cd frontend && npx vite build` clean.

---

## Context

### Related Documentation
- `docs/PLANNING.md` — Architecture, data model, API design
- `docs/DECISIONS.md` — ADR-002 (JSON), ADR-006 (FastAPI + React),
  ADR-008 (StorageBackend), ADR-010 (Fantasy Footballers seed). No
  contradiction with any ADR.
- `prps/19-prp-fantasy-footballers-tiered-import.md` — Previous PRP;
  `add_player()` already accepts the six new fields as kwargs.
- `initials/20-init-add-delete-ux-overhaul.md` — Full spec.

### ADR Alignment
None of the three changes invent new architecture. They all sit inside
the React layer + one backend Pydantic-model extension. Single-user
JSON-persistence model unchanged.

### Dependencies
- **Required**: PRP-019 (`add_player()` kwargs). Verified present at
  `backend/utils/rankings.py:178-209`.
- **Optional**: none.

### Files to Modify / Create
```
backend/routers/rankings.py             # MODIFY — expand AddPlayerRequest;
                                        #          pass new kwargs to add_player()
tests/test_rankings.py                  # MODIFY — add test_add_player_full_kwargs

frontend/src/api/rankings.js            # MODIFY — addPlayer(position, body)
frontend/src/App.jsx                    # MODIFY — addDialog state shape,
                                        #          handleAdd signature, rename
                                        #          tagPicker → contextMenu
frontend/src/components/WarRoom.jsx     # MODIFY — toolbar + ADD PLAYER button;
                                        #          AddPlayerDialog props drop
                                        #          position/tier
frontend/src/components/WarRoom.css     # MODIFY — divider + add-player button styles
frontend/src/components/AddPlayerDialog.jsx  # REWRITE — 2 → 10 fields
frontend/src/components/AddPlayerDialog.css  # CREATE — grid layout
frontend/src/components/TierGroup.jsx   # MODIFY — delete add-tier-btn JSX,
                                        #          drop onAddOpen prop
frontend/src/components/TierGroup.css   # MODIFY — delete .add-tier-btn rules
frontend/src/components/PositionColumn.jsx   # MODIFY — drop onAddOpen passthrough
frontend/src/components/PlayerRow.jsx   # MODIFY — delete .delete-btn JSX,
                                        #          drop onDeleteClick prop;
                                        #          rename onTagOpen → onContextMenuOpen
frontend/src/components/PlayerRow.css   # MODIFY — delete .delete-btn rules;
                                        #          adjust grid (5 cols → 4 cols)
frontend/src/components/ContextMenu.jsx # CREATE — parent 2-item menu with
                                        #          Tags ▸ / Edit ▸ submenus
frontend/src/components/ContextMenu.css # CREATE — popover + submenu rules
frontend/src/components/TagPicker.jsx   # DELETE — replaced by ContextMenu
frontend/src/components/TagPicker.css   # DELETE
initials/20-init-add-delete-ux-overhaul.md   # untracked; include in commit
```

### Scope Expansion vs. Init

Init's "Files Touched" anticipates the major edits. Three small extras
or differences worth surfacing:

1. **`frontend/src/components/PositionColumn.jsx`** (added). It passes
   `onAddOpen` from WarRoom down to TierGroup. Once TierGroup stops
   accepting that prop, the passthrough is a stale parameter. **Default
   chosen**: include — clean prop graph, no dead args. **Opt-out**: leave
   the passthrough; React tolerates ignored props but the lint config
   would flag it under stricter settings.

2. **`frontend/src/App.jsx`** (added — init listed it implicitly via
   the `api/rankings.js` signature change). The `handleAdd` signature
   change and `tagPicker` → `contextMenu` state rename both live here.
   **Default chosen**: include — required, not optional.

3. **`TagPicker.jsx` / `TagPicker.css` deleted, `ContextMenu.jsx` /
   `ContextMenu.css` created** (init said "ContextMenu.jsx (or actual
   filename)" — the actual filename is `TagPicker.jsx`). **Default
   chosen**: create new `ContextMenu.*` + delete `TagPicker.*` rather
   than rename in place. Reason: the new component's responsibility is
   genuinely different (a 2-item parent menu that *renders* the tag
   submenu), and the tag-list constant + submenu rendering naturally
   live inside ContextMenu. Keeping the `TagPicker` filename around
   would mislead future readers. **Opt-out**: rename `TagPicker.jsx` →
   `ContextMenu.jsx` and edit in place — saves one create + one delete
   but conflates the rename with the restructure in `git log`.

### Files NOT Modified (intentional)
```
backend/utils/rankings.py        # add_player() already extended in PRP-019 —
                                 #  no further backend logic change needed
backend/utils/data_loader.py     # Untouched
backend/middleware/auth.py       # Auth surface unchanged
frontend/src/components/DeleteConfirmDialog.{jsx,css}  # Existing dialog reused
frontend/src/components/NotesDialog.jsx                # Untouched
frontend/src/components/SearchBar.{jsx,css}            # Untouched
frontend/src/components/RosterPanel.{jsx,css}          # Untouched
data/players/2026_{POS}.csv                            # Seed data — read-only
```

---

## Technical Specification

### Backend — Pydantic Model + Router Handler

**`backend/routers/rankings.py`** — extend `AddPlayerRequest` and
update the handler:

```python
from pydantic import BaseModel, Field

class AddPlayerRequest(BaseModel):
    name: str
    team: str
    tier: int = Field(ge=1)
    bye_week: int | None = None
    adp: str = ""
    projected_points: float | None = None
    risk: float | None = None
    upside: float | None = None
    outlook: str = ""


@router.post("/{position}/add")
def add(
    request: Request, position: str, body: AddPlayerRequest
) -> list[dict]:
    """Add a new player at the end of the specified tier."""
    _validate_position(position)

    if not body.name.strip() or not body.team.strip():
        raise HTTPException(
            status_code=400, detail="Name and team are required"
        )

    # Duplicate check (case-insensitive)
    profile = get_profile(request)
    existing = get_position_players(profile, position)
    if any(p["name"].lower() == body.name.strip().lower() for p in existing):
        raise HTTPException(
            status_code=400,
            detail=f"{body.name.strip()} already exists in {position}",
        )

    updated = add_player(
        profile,
        body.name.strip(),
        body.team.strip().upper(),
        position,
        body.tier,
        bye_week=body.bye_week,
        adp=body.adp.strip(),
        projected_points=body.projected_points,
        risk=body.risk,
        upside=body.upside,
        outlook=body.outlook,
    )
    _set_profile(updated)
    return get_position_players(updated, position)
```

Notes:
- `tier: int = Field(ge=1)` rejects 0 / negative client-side via 422.
- `name.strip()` / `team.strip().upper()` / `adp.strip()` preserved /
  applied symmetrically. `outlook` is *not* stripped (multi-line, leading
  whitespace can be intentional inside a paragraph).
- No new endpoints. No path changes. Existing 14 endpoints stand.

### Backend — Test Migration

**`tests/test_rankings.py`** — append one test (no deletions, no edits
to existing add_player tests; they pass unchanged because the new
kwargs default to `None`/`""`):

```python
def test_add_player_full_kwargs(sample_profile):
    """Caller supplying all 6 optional kwargs round-trips correctly."""
    result = add_player(
        sample_profile, "Test", "FA", "QB", tier=3,
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
    # Sanity on positional args:
    assert new_player["tier"] == 3
    assert new_player["team"] == "FA"
    assert new_player["position"] == "QB"
```

No router-level tests exist in the repo (verified: no `TestClient` /
`httpx` imports across `tests/`). The router code path is covered by
the manual curl smoke test in Step 7 below.

### Frontend — `api/rankings.js`

Change `addPlayer` signature from positional to body-object:

```javascript
export const addPlayer = (position, body) =>
  request(`${BASE}/${position}/add`, {
    method: 'POST',
    body: JSON.stringify(body),
  })

// body shape (constructed by AddPlayerDialog):
// {
//   name, team, tier,             // required
//   bye_week,                     // int | null
//   adp,                          // string ("" when blank)
//   projected_points,             // float | null
//   risk, upside,                 // float | null
//   outlook,                      // string ("" when blank)
// }
```

### Frontend — `App.jsx`

Two changes:

1. `handleAdd` signature drops the individual args, takes `(position, body)`:
   ```javascript
   const handleAdd = async (position, body) => {
     const updated = await addPlayer(position, body)
     setRankings(prev => ({ ...prev, [position]: updated }))
     setDirty(true)
     setAddDialog(null)
   }
   ```

2. `addDialog` state goes from `{ position, tier }` to plain `true`/`null`
   (toolbar button doesn't carry contextual position/tier):
   ```javascript
   const [addDialog, setAddDialog] = useState(null)   // null | true
   // ...
   onAddOpen={() => setAddDialog(true)}
   ```

3. Rename `tagPicker` state and `handleTagOpen` to `contextMenu` /
   `handleContextMenuOpen` for clarity. The render conditional uses
   `<ContextMenu>` instead of `<TagPicker>`. `handleTagSelect` keeps its
   body — the new ContextMenu still calls it for tag-row clicks.

### Frontend — `WarRoom.jsx` + `WarRoom.css`

**Toolbar** — add `+ ADD PLAYER` as the first button, with a divider:

```jsx
<div className="toolbar">
  <button className="toolbar-btn toolbar-btn-add" onClick={onAddOpen}>
    + ADD PLAYER
  </button>
  <div className="toolbar-divider" />
  <button className="save-button" onClick={onSave}>SAVE</button>
  <button className="toolbar-btn" onClick={onSaveAsOpen}>SAVE AS</button>
  <button className="toolbar-btn" onClick={onLoadOpen}>LOAD</button>
  <button className="toolbar-btn toolbar-btn-danger" onClick={onResetOpen}>RESET</button>
  <button className="toolbar-btn" onClick={onSetDefaultOpen}>★ SET DEFAULT</button>
</div>
```

**AddPlayerDialog render** — drop `position` / `tier` props:

```jsx
{addDialog && (
  <AddPlayerDialog
    isOpen={true}
    onAdd={handleAdd}
    onClose={onAddClose}
  />
)}
```

**CSS** — append in `WarRoom.css`:

```css
.toolbar-btn-add {
  border-color: var(--accent);
  color: var(--accent);
}
.toolbar-btn-add:hover {
  background: var(--accent);
  color: white;
}

.toolbar-divider {
  width: 1px;
  background: var(--border);
  align-self: stretch;
  margin: 2px 4px;
}
```

### Frontend — `AddPlayerDialog.{jsx,css}` (rewrite)

Component owns its 10 field states plus a `position` state (default
`'QB'`). Required validation client-side: non-empty `name`, `team`,
`position` ∈ POSITIONS, `tier >= 1`. Optional numeric fields parse to
`Number` only if non-empty; otherwise send `null`. Optional string
fields send `""`.

```jsx
import { useRef, useEffect, useState } from 'react'
import './AddPlayerDialog.css'

const POSITIONS = ['QB', 'RB', 'WR', 'TE']

const INITIAL = {
  name: '', team: '', position: 'QB', tier: '1',
  bye_week: '', adp: '',
  projected_points: '', risk: '', upside: '',
  outlook: '',
}

export default function AddPlayerDialog({ isOpen, onAdd, onClose }) {
  const dialogRef = useRef(null)
  const [f, setF] = useState(INITIAL)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      setF(INITIAL); setError('')
      dialogRef.current?.showModal()
    } else {
      dialogRef.current?.close()
    }
  }, [isOpen])

  const set = (k) => (e) => setF(prev => ({ ...prev, [k]: e.target.value }))

  const handleAdd = async () => {
    const name = f.name.trim()
    const team = f.team.trim().toUpperCase()
    const position = f.position
    const tier = parseInt(f.tier, 10)
    if (!name || !team) { setError('Name and team are required'); return }
    if (!POSITIONS.includes(position)) { setError('Pick a position'); return }
    if (!Number.isInteger(tier) || tier < 1) { setError('Tier must be ≥ 1'); return }

    const parseFloatOrNull = (s) => s.trim() === '' ? null : Number(s)
    const body = {
      name, team, tier,
      bye_week: f.bye_week.trim() === '' ? null : parseInt(f.bye_week, 10),
      adp: f.adp.trim(),
      projected_points: parseFloatOrNull(f.projected_points),
      risk: parseFloatOrNull(f.risk),
      upside: parseFloatOrNull(f.upside),
      outlook: f.outlook,
    }
    // NaN check for any numeric input that the user typed garbage into
    for (const k of ['bye_week', 'projected_points', 'risk', 'upside']) {
      if (body[k] !== null && Number.isNaN(body[k])) {
        setError(`${k} must be a number`); return
      }
    }

    try { await onAdd(position, body) }
    catch (err) { setError(err.message) }
  }

  return (
    <dialog ref={dialogRef} onClose={onClose} className="add-player-dialog">
      <div className="dialog-header">Add Player</div>
      {error && <div className="dialog-error">{error}</div>}

      <div className="add-grid">
        <label className="full">
          <span>Name *</span>
          <input className="dialog-input" value={f.name} onChange={set('name')} />
        </label>

        <label>
          <span>Team *</span>
          <input className="dialog-input" value={f.team} maxLength={4} onChange={set('team')} />
        </label>
        <label>
          <span>Position *</span>
          <select className="dialog-input" value={f.position} onChange={set('position')}>
            {POSITIONS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </label>

        <label>
          <span>Tier *</span>
          <input className="dialog-input" type="number" min="1" value={f.tier} onChange={set('tier')} />
        </label>
        <label>
          <span>Bye Week</span>
          <input className="dialog-input" type="number" min="1" max="18" value={f.bye_week} onChange={set('bye_week')} />
        </label>

        <label>
          <span>ADP</span>
          <input className="dialog-input" value={f.adp} placeholder="e.g. 3.05" onChange={set('adp')} />
        </label>
        <label>
          <span>Projected Points</span>
          <input className="dialog-input" type="number" step="0.1" value={f.projected_points} onChange={set('projected_points')} />
        </label>

        <label>
          <span>Risk</span>
          <input className="dialog-input" type="number" step="0.1" min="0" max="10" value={f.risk} onChange={set('risk')} />
        </label>
        <label>
          <span>Upside</span>
          <input className="dialog-input" type="number" step="0.1" min="0" max="10" value={f.upside} onChange={set('upside')} />
        </label>

        <label className="full">
          <span>Outlook</span>
          <textarea className="dialog-input add-outlook" rows="4" value={f.outlook} onChange={set('outlook')} />
        </label>
      </div>

      <div className="dialog-buttons">
        <button className="btn-primary" onClick={handleAdd}>Add</button>
        <button className="btn-cancel" onClick={onClose}>Cancel</button>
      </div>
    </dialog>
  )
}
```

CSS (new file):

```css
.add-player-dialog { min-width: 480px; }

.add-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 12px;
  margin: 10px 0 14px;
}
.add-grid label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
  color: var(--text-muted);
}
.add-grid label.full { grid-column: 1 / -1; }
.add-grid .dialog-input { width: 100%; box-sizing: border-box; }
.add-outlook { resize: vertical; min-height: 80px; font-family: var(--font); }
```

### Frontend — `TierGroup.{jsx,css}`

Delete the `<button className="add-tier-btn">` block and the
`onAddOpen` prop. The component no longer needs `tierNum` for an add
button purpose, but it does still need it for the tier header — leave
that prop alone.

```jsx
// Drop these from the prop list:  onAddOpen
// Delete this JSX block:
// {!isDraft && (<button className="add-tier-btn" …>+ {position} · Tier {tierNum}</button>)}
```

CSS: delete the `.add-tier-btn` and `.add-tier-btn:hover` rules.

### Frontend — `PositionColumn.jsx`

Drop the `onAddOpen` prop from the component signature and from where
it's passed to `<TierGroup>`. No other change.

### Frontend — `PlayerRow.{jsx,css}`

Delete the `<button className="control-btn delete-btn">×</button>`
JSX in the War-Room branch. Drop `onDeleteClick` from the props.
Rename `onTagOpen` prop to `onContextMenuOpen` (the same function, just
clearer name now that it opens a multi-item menu).

`handleContextMenu` body unchanged — still captures `e.clientX/Y` and
calls the prop with `(player, position, { x, y })`.

CSS: delete `.delete-btn` and `.delete-btn:hover` rules. Update the
grid template:

```css
/* before */
.player-row { grid-template-columns: 24px 24px 24px 1fr 24px; }
/* after */
.player-row { grid-template-columns: 24px 24px 24px 1fr; }
```

(The draft-row grid is already 3-column and isn't affected.)

### Frontend — `ContextMenu.{jsx,css}` (new)

Two-item parent menu with submenu opening on hover (mouse) or click
(touch). Owns the TAGS constant and tag toggle behaviour.

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
  const [openSub, setOpenSub] = useState(null)  // null | 'tags' | 'edit' (touch)

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

  const toggleSub = (k) => (e) => {
    // For touch: tapping the parent row opens the submenu.
    // For mouse: hover handles it via CSS; this click is a no-op-ish.
    e.stopPropagation()
    setOpenSub(prev => prev === k ? null : k)
  }

  return (
    <div ref={ref} className="context-menu" style={{ left: x, top: y }}>
      <div
        className={`cm-item ${openSub === 'tags' ? 'open' : ''}`}
        onClick={toggleSub('tags')}
      >
        <span>Tags</span><span className="cm-arrow">▸</span>
        <div className="cm-submenu cm-submenu-tags">
          {TAGS.map(t => (
            <button
              key={t.key}
              className={`cm-tag-row ${activeTag === t.key ? 'active' : ''}`}
              onClick={(e) => { e.stopPropagation(); handleTagClick(t.key) }}
            >
              <span className={`cm-tag-icon tag-${t.key}`}>{t.icon}</span>
              <span className="cm-tag-label">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div
        className={`cm-item ${openSub === 'edit' ? 'open' : ''}`}
        onClick={toggleSub('edit')}
      >
        <span>Edit</span><span className="cm-arrow">▸</span>
        <div className="cm-submenu cm-submenu-edit">
          <button
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

CSS (new file):

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

.cm-item {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  cursor: pointer;
  border-radius: 4px;
  color: var(--text-primary);
}
.cm-item:hover { background: rgba(255, 255, 255, 0.06); }

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

/* Desktop: hover opens submenu */
@media (pointer: fine) {
  .cm-item:hover > .cm-submenu { display: block; }
}

/* Touch: open via JS class only */
@media (pointer: coarse) {
  .cm-item.open > .cm-submenu { display: block; }
}

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

### Open Question Resolutions

| Question | Resolution |
|---|---|
| Tag toggle semantics | Verified at `TagPicker.jsx:36-37`: `key === activeTag ? '' : key` — clicking active tag clears it; clicking another replaces. Behaviour preserved in ContextMenu's `handleTagClick`. |
| Touch / iOS long-press | Per init, desktop-only correctness requirement. `@media (pointer: coarse)` CSS rule kept for future tablet viewing; no manual touch test required. |
| Delete row color | `var(--danger)` (`#C0392B`) — defined in `App.css:13`, already used by `.btn-danger`, `.toolbar-btn-danger:hover`, `.delete-btn:hover`. Matches existing convention. |
| Null fields in UI | Per init out-of-scope. UI doesn't render `bye_week`/`adp`/etc. yet, so null values are persisted invisibly until a future PRP surfaces them. |

### Identity Preservation — Verified Against Live Code

These were spot-checked before this PRP to make sure no UI identity
silently changes:

- **Tag labels** in the ContextMenu `TAGS` constant match
  `TagPicker.jsx:5-11` exactly: `Love / Breakout / Sleeper / Risky /
  Hurt / Avoid / Red flag`. (Note: the init mock said "Handcuff" for
  the cross/✚ tag; the live code labels it "Hurt" — live code wins.
  Tag rename is out of scope.)
- **Tag icon colors** in ContextMenu.css (`heart #E03030`, `warning
  #F0B429`, `skull #E0E0E0`, `cross #E03030`) match `TagPicker.css:36-39`
  byte-for-byte. Visual identity preserved.

### Design Tokens (reaffirmed)
- Background secondary: `var(--bg-secondary)`
- Accent (Honolulu Blue): `var(--accent)` (`#0076B6`)
- Danger red: `var(--danger)` (`#C0392B`)
- Border: `var(--border)`
- Text muted: `var(--text-muted)`
- Tag icon colors: heart/cross `#E03030`, warning `#F0B429`, skull `#E0E0E0`

---

## Implementation Steps

### Step 1 — Backend: expand `AddPlayerRequest` + handler
**Files**: `backend/routers/rankings.py`

Edit per spec above. Two distinct edits:

1. Import `Field` from pydantic (it isn't currently imported):
   ```python
   from pydantic import BaseModel, Field
   ```
2. Replace `AddPlayerRequest` class body with the 9-field version.
3. Replace the `add_player(...)` call in the `add` handler to pass the
   new fields as kwargs.

**Validation**:
```bash
ruff check backend/routers/rankings.py
python -c "import sys; sys.path.insert(0, 'backend'); from routers.rankings import AddPlayerRequest; \
  b = AddPlayerRequest(name='T', team='F', tier=3, bye_week=8, adp='1.05', \
                       projected_points=100.0, risk=5.0, upside=5.0, outlook='x'); \
  print(b.model_dump())"
```
- [ ] Ruff clean
- [ ] Pydantic accepts the full body
- [ ] Pydantic rejects `tier=0` (try `AddPlayerRequest(name='T', team='F', tier=0)` — should ValidationError)

---

### Step 2 — Backend: add `test_add_player_full_kwargs`
**Files**: `tests/test_rankings.py`

Append the test from the Technical Specification near the other
`test_add_player_*` tests.

**Validation**:
```bash
source .venv/bin/activate
pytest tests/test_rankings.py -v -k add_player
```
- [ ] All `test_add_player_*` tests pass (5 existing + 1 new)

---

### Step 3 — Frontend: ContextMenu + delete TagPicker
**Files**:
- Create `frontend/src/components/ContextMenu.jsx`
- Create `frontend/src/components/ContextMenu.css`
- Delete `frontend/src/components/TagPicker.jsx`
- Delete `frontend/src/components/TagPicker.css`

Implement per spec. Done first so that Step 5's App.jsx rewrite can
import a real component — no stub-then-replace dance.

**Validation**:
```bash
grep -rn "TagPicker" frontend/src/
# expected: matches only in App.jsx (still imports the now-deleted file;
# fixed in Step 5)
```
- [ ] `ContextMenu.jsx` + `ContextMenu.css` exist
- [ ] `TagPicker.jsx` + `TagPicker.css` deleted
- [ ] Only remaining `TagPicker` reference is in `App.jsx` (cleaned up in Step 5)

> **Build deferred** — Steps 3 through 9 each leave the tree in an
> intermediate state where Vite would error (deleted import here,
> renamed prop there). One full `npx vite build` runs at Step 10 once
> all the pieces are in place. For per-step iteration, lean on the dev
> server's HMR if it's running.

---

### Step 4 — Frontend: `api/rankings.js` — `addPlayer(position, body)`
**Files**: `frontend/src/api/rankings.js`

Replace the existing `addPlayer` export with the new signature.

**Validation**:
```bash
grep -n "addPlayer" frontend/src/api/rankings.js
# expected: one export matching the new (position, body) signature
```
- [ ] Signature is `addPlayer = (position, body) => …`

---

### Step 5 — Frontend: `App.jsx` — handleAdd + state renames
**Files**: `frontend/src/App.jsx`

Three edits:

1. `handleAdd(position, body)` per spec.
2. `addDialog` state: keep `useState(null)` but the value becomes
   `true` (open) or `null` (closed); `onAddOpen={() => setAddDialog(true)}`.
3. Rename `tagPicker` → `contextMenu` (state + setter + callbacks). The
   import `import TagPicker from './components/TagPicker'` becomes
   `import ContextMenu from './components/ContextMenu'`. The render
   conditional becomes:
   ```jsx
   {contextMenu && (
     <ContextMenu
       activeTag={contextMenu.player.tag ?? ''}
       position={contextMenu.coords}
       onTagSelect={handleTagSelect}
       onDelete={() => {
         const { player, position } = contextMenu
         setContextMenu(null)
         setDeleteDialog({ player, position })
       }}
       onClose={() => setContextMenu(null)}
     />
   )}
   ```
4. Pass `onContextMenuOpen={handleContextMenuOpen}` down to WarRoom
   (which forwards to PositionColumn → TierGroup → PlayerRow).
   `handleContextMenuOpen` body is the same as the old `handleTagOpen`.

**Validation**:
```bash
grep -rn "TagPicker\|tagPicker\|handleTagOpen" frontend/src/App.jsx
# expected: zero matches
```
- [ ] All TagPicker / tagPicker references in App.jsx replaced

---

### Step 6 — Frontend: WarRoom — toolbar + dialog props
**Files**: `frontend/src/components/WarRoom.jsx`, `frontend/src/components/WarRoom.css`

1. Add `+ ADD PLAYER` button + divider before `SAVE` in the toolbar.
2. Drop `position` and `tier` props on `<AddPlayerDialog>`.
3. Append `.toolbar-btn-add` and `.toolbar-divider` CSS rules.

**Validation**:
```bash
grep -n "toolbar-btn-add\|toolbar-divider" frontend/src/components/WarRoom.jsx frontend/src/components/WarRoom.css
```
- [ ] Button rendered in JSX; CSS rules appended

---

### Step 7 — Frontend: TierGroup + PositionColumn — drop add button
**Files**: `frontend/src/components/TierGroup.jsx`,
`frontend/src/components/TierGroup.css`,
`frontend/src/components/PositionColumn.jsx`

1. `TierGroup.jsx`: delete the `<button className="add-tier-btn">…</button>` block and the `onAddOpen` prop reference.
2. `TierGroup.css`: delete `.add-tier-btn` and `.add-tier-btn:hover` rules.
3. `PositionColumn.jsx`: stop accepting / passing `onAddOpen`.

**Validation**:
```bash
grep -rn "add-tier-btn\|onAddOpen" frontend/src/components/TierGroup.* frontend/src/components/PositionColumn.*
# expected: zero matches
```
- [ ] No traces of the per-tier add path in TierGroup or PositionColumn

---

### Step 8 — Frontend: PlayerRow — drop `×`, rename prop
**Files**: `frontend/src/components/PlayerRow.jsx`,
`frontend/src/components/PlayerRow.css`

1. `PlayerRow.jsx`: delete the `<button className="control-btn delete-btn">×</button>` block. Drop `onDeleteClick` from props. Rename `onTagOpen` → `onContextMenuOpen` in the prop list and inside `handleContextMenu`.
2. `PlayerRow.css`: delete `.delete-btn` + `.delete-btn:hover` rules. Change `.player-row` `grid-template-columns` from `24px 24px 24px 1fr 24px` to `24px 24px 24px 1fr`.

Also update all upstream prop-passers in the chain so the rename
propagates: `TierGroup.jsx` (passes `onTagOpen` → rename to
`onContextMenuOpen`), `PositionColumn.jsx` (same), and the WarRoom
`<PositionColumn>` render (same).

**Validation**:
```bash
grep -rn "onTagOpen\|delete-btn\|onDeleteClick" frontend/src/
# expected: zero matches
```
- [ ] No traces of removed identifiers anywhere in `frontend/src/`

---

### Step 9 — Frontend: AddPlayerDialog rewrite
**Files**:
- `frontend/src/components/AddPlayerDialog.jsx` (rewrite)
- `frontend/src/components/AddPlayerDialog.css` (create)

Implement per spec. ~110 lines JSX, ~25 lines CSS — both well under 500.

**Validation**:
```bash
wc -l frontend/src/components/AddPlayerDialog.jsx frontend/src/components/AddPlayerDialog.css
```
- [ ] Both files < 500 lines (target: ~130 / ~25)

---

### Step 10 — Full validation
First production build of the run — verifies the whole tree compiles
together after Steps 3–9.

**Validation**:
```bash
source .venv/bin/activate
pytest tests/ -q
ruff check backend/ tests/
cd frontend && npx vite build
```
- [ ] 98 tests pass, 1 skipped (was 97; +1 for `test_add_player_full_kwargs`)
- [ ] Ruff clean
- [ ] Vite build clean

---

### Step 11 — Local smoke + curl
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload &
sleep 2

# Required-only body
curl -s -X POST http://localhost:8000/api/rankings/QB/add \
  -H "Content-Type: application/json" \
  -d '{"name":"Smoke Test 1","team":"FA","tier":9}' | python -m json.tool | tail -20

# Full body
curl -s -X POST http://localhost:8000/api/rankings/RB/add \
  -H "Content-Type: application/json" \
  -d '{"name":"Smoke Test 2","team":"NYJ","tier":9,
       "bye_week":8,"adp":"12.05","projected_points":250.0,
       "risk":4.5,"upside":8.0,"outlook":"Sample blurb."}' | python -m json.tool | tail -20

# Tier validation (expect 422)
curl -s -w "\nHTTP %{http_code}\n" -X POST http://localhost:8000/api/rankings/QB/add \
  -H "Content-Type: application/json" \
  -d '{"name":"Bad Tier","team":"FA","tier":0}'

# Cleanup — undo the test inserts
# (Smoke Test 1 and 2 are at the bottom of their new tiers; find their ranks)
curl -s http://localhost:8000/api/rankings/QB | python -c "
import json,sys
qb=json.load(sys.stdin)
print('Smoke Test 1 rank:', next(p['position_rank'] for p in qb if p['name']=='Smoke Test 1'))
"

pkill -f "uvicorn backend.main"
```
- [ ] Required-only body returns 200; new player has `bye_week: null`,
  `adp: ""`, etc.
- [ ] Full body returns 200; new player has every field set correctly
- [ ] `tier=0` returns HTTP 422 with Pydantic validation detail

---

### Step 12 — Manual browser test
```bash
# Terminal 1
source .venv/bin/activate && uvicorn backend.main:app --reload

# Terminal 2
cd frontend && npm run dev
```
Open `http://localhost:5173`. Walk the init's checklist (see Testing
Requirements below). If browser isn't available, say so explicitly —
do not claim success.

---

### Step 13 — Commit + push
```bash
git add backend/routers/rankings.py \
        tests/test_rankings.py \
        frontend/src/api/rankings.js \
        frontend/src/App.jsx \
        frontend/src/components/WarRoom.jsx \
        frontend/src/components/WarRoom.css \
        frontend/src/components/AddPlayerDialog.jsx \
        frontend/src/components/AddPlayerDialog.css \
        frontend/src/components/TierGroup.jsx \
        frontend/src/components/TierGroup.css \
        frontend/src/components/PositionColumn.jsx \
        frontend/src/components/PlayerRow.jsx \
        frontend/src/components/PlayerRow.css \
        frontend/src/components/ContextMenu.jsx \
        frontend/src/components/ContextMenu.css \
        initials/20-init-add-delete-ux-overhaul.md
git rm frontend/src/components/TagPicker.jsx frontend/src/components/TagPicker.css

git commit -m "feat: add/delete UX overhaul — toolbar add button, expanded dialog, context-menu delete"
git push origin main
```

---

## Testing Requirements

### Unit Tests (`backend/utils/`)
- `tests/test_rankings.py::test_add_player_full_kwargs` — verifies
  round-trip of all 6 optional kwargs via `add_player()`. The five
  existing `test_add_player_*` tests pass unchanged.

### API Tests (curl, local)
See Step 11 above. Three scenarios:
1. Required-only body → 200 with `null`/`""` for optional fields
2. Full body → 200 with all fields populated
3. `tier=0` → 422 from Pydantic

### Manual Browser Tests (post-deploy checklist)
Per init §"Manual browser test checklist":
- [ ] Toolbar shows `+ ADD PLAYER` before `SAVE` with vertical divider
- [ ] Tier groups: no `+ {POSITION} · Tier N` strips
- [ ] Player rows: no `×` button (War Room or Draft)
- [ ] Right-click on player → 2-item menu (Tags / Edit)
- [ ] Tags submenu opens on hover (desktop)
- [ ] Tags submenu shows 7 vertical rows: `icon + label`
- [ ] Clicking a tag toggles it (active tag click clears; different
  tag click replaces)
- [ ] Edit submenu opens on hover
- [ ] Edit > Delete row is red (`var(--danger)`)
- [ ] Edit > Delete → opens existing DeleteConfirmDialog → confirms →
  player removed
- [ ] `+ ADD PLAYER` opens dialog with 10 fields
- [ ] Dialog blocks save when name / team / position / tier invalid
- [ ] Dialog with only required fields filled: player added; verify
  via `curl http://localhost:8000/api/rankings/<POS>` that the new
  player has `bye_week: null`, `adp: ""`, `projected_points: null`,
  `risk: null`, `upside: null`, `outlook: ""`
- [ ] Dialog with all fields filled: player added with all values
  (verify via curl as above; all 6 optional fields populated)
- [ ] Added player appears at end of chosen tier
- [ ] Right-click on player in Draft Mode still opens context menu
  (existing behavior — `onContextMenu` works in both modes; verify no
  regression)
- [ ] No console errors

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | 98 passed, 1 skipped | ☐ |
| 2 | `ruff check backend/ tests/` | Clean | ☐ |
| 3 | `cd frontend && npx vite build` | Build clean | ☐ |
| 4 | `uvicorn backend.main:app --reload` | Starts, no errors | ☐ |
| 5 | `curl /health` | 200 OK | ☐ |
| 6 | curl required-only add | 200, player with null optionals | ☐ |
| 7 | curl full-body add | 200, player with all fields | ☐ |
| 8 | curl `tier=0` add | 422 validation error | ☐ |
| 9 | Browser: toolbar has `+ ADD PLAYER` + divider | Visible left of SAVE | ☐ |
| 10 | Browser: tier groups have no add strip | No `+ QB · Tier N` strips | ☐ |
| 11 | Browser: player rows have no × | No delete button visible | ☐ |
| 12 | Browser: right-click player → 2-item menu | Tags / Edit visible | ☐ |
| 13 | Browser: hover Tags ▸ | Submenu opens, 7 rows | ☐ |
| 14 | Browser: click a tag in submenu | Tag toggles on the player | ☐ |
| 15 | Browser: hover Edit ▸ → click Delete | DeleteConfirmDialog appears | ☐ |
| 16 | Browser: confirm Delete | Player removed | ☐ |
| 17 | Browser: + ADD PLAYER → fill all 10 fields → Add | Player added with all values | ☐ |
| 18 | Browser: + ADD PLAYER → blank optionals → Add. Then `curl -s http://localhost:8000/api/rankings/QB \| python -c "import json,sys; p=next(x for x in json.load(sys.stdin) if x['name']=='<new>'); print(p)"` | `bye_week: null, adp: "", projected_points: null, risk: null, upside: null, outlook: ""` | ☐ |
| 19 | Browser: + ADD PLAYER → tier=0 → Add | Inline error shown | ☐ |
| 20 | Browser: Draft Mode toggle still works | No regression | ☐ |
| 21 | Browser: SAVE clears unsaved indicator | Existing behavior intact | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| 422 Pydantic | Missing required body field; `tier < 1`; wrong type for a numeric field | FastAPI auto-422; frontend dialog catches via `onAdd` rejection and surfaces inline via `setError(err.message)` |
| 400 duplicate name | Same name already exists in that position | Router raises `HTTPException(400)`; dialog shows inline error |
| 400 empty name/team | Body has empty string after strip | Router raises `HTTPException(400)`; dialog already validates client-side, this is the belt-and-suspenders backstop |
| 404 invalid position in path | Bad URL like `/api/rankings/QQ/add` | Router `_validate_position()` raises 404; dialog dropdown prevents this for normal flow |
| Frontend NaN on numeric input | User types text into a number field | Dialog's `Number.isNaN` check sets inline error and blocks submit |
| ContextMenu off-screen | Right-click near viewport edge | `Math.min(position.x, window.innerWidth - 260)` + analogous y; same pattern as existing `TagPicker` |

---

## Open Questions

All resolved (see Technical Specification → Open Question Resolutions).

No outstanding blockers.

---

## Rollback Plan

1. `git revert <commit-sha>` on `main`
2. `git push origin main`
3. **Local**:
   - Backend `--reload` picks up the reverted `AddPlayerRequest`
     immediately. Any in-memory profile already mutated by full-body
     adds keeps the new fields (they're additive) until next reload.
   - Frontend dev server (Vite HMR) picks up the revert and reverts the
     dialog + toolbar + context menu. `TagPicker.jsx` reappears.
4. **Production** (if deployed): on EC2 `git pull && ./scripts/deploy.sh`.
5. **S3 / on-disk JSON cleanup**: none required. Any player records
   inserted via the new full body have the 6 new fields populated;
   the reverted UI doesn't render them but doesn't break on them
   either (PRP-019 already established additive-fields-as-safe). No
   destructive cleanup needed.

Rollback is safe — no schema migration, no destructive operations.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Exact file paths, complete JSX/CSS spec, every prop rename traced through the render chain, all four init Open Questions resolved against the current codebase. |
| Feasibility | 10 | All work sits inside React + one Pydantic model edit. PRP-019 already wired `add_player()` for kwargs — backend is a 10-line change. No new framework, no infra, no router URL change. |
| Completeness | 10 | All affected components identified including the implicit ones (PositionColumn passthrough, App.jsx state rename). TagPicker → ContextMenu transition handled as create/delete to keep `git log` clean. Test target adjusted: 98 (=97+1). |
| Alignment | 10 | No ADR conflict. Single-user, JSON, no DB, no Streamlit, no external runtime APIs. ADR-006 React stack respected; ADR-010 player-record shape extended in PRP-019 is now matched in the UI. |
| **Average** | **10.0** | Ready for execution. |

---

## Notes

### File-size considerations
- `AddPlayerDialog.jsx` grows from 58 → ~130 lines. Well under the
  500-line limit; no split planned.
- `ContextMenu.jsx` lands at ~90 lines (was 58 lines as `TagPicker.jsx`).
- `WarRoom.jsx` adds ~5 lines (new button + divider); still well under
  limit.

### Why a single atomic commit
This is one coherent UX overhaul. Splitting it would leave intermediate
commits with broken UI (e.g. the toolbar button added before the
per-tier strip is removed produces *two* add affordances). One commit,
one revert button. Same pattern as PRP-019.

### What about Draft Mode?
Draft Mode already hides the toolbar entirely (the `!isDraft && (...)`
guard around the toolbar JSX). The new `+ ADD PLAYER` button lives
inside that same conditional, so it's automatically hidden in Draft —
no extra wiring needed. Per-row `×` button removal also applies to the
Draft-mode rendering path, but the draft branch in `PlayerRow.jsx`
never rendered `delete-btn` in the first place (it returns earlier with
its own grid). Verified at `PlayerRow.jsx:64-80`.

### Why `position` becomes a body-free path parameter
Router signature `add(request, position, body)` already takes
`position` from the URL. Adding it to the body too would duplicate
state and invite drift. The dialog passes `position` as the first
argument to `onAdd`, App.jsx forwards it to `addPlayer(position,
body)`, and `body` carries only the 9 non-position fields. Symmetric
with the existing `reorderPlayers(position, …)`, `deletePlayer(position, rank)`, etc.
