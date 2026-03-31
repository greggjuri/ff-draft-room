# 05-init-react-frontend.md — React War Room UI

## Feature Summary
Build the full War Room UI in Vite + React, consuming the FastAPI backend at
localhost:8000. Four side-by-side position columns (QB | RB | WR | TE), each
with tier groups, ▲▼ reordering, notes dialog, add player, and delete confirm.
Full CSS control — no framework. Monospace font, dark navy + Honolulu Blue design.

After this init: `npm run dev` at localhost:5173 shows a fully functional War Room.

## Status
- [x] Open questions resolved
- [x] Ready for PRP generation

---

## Requirements

### 1. Project Scaffold

```
frontend/
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── App.css               ← global styles + design tokens
    ├── api/
    │   └── rankings.js       ← all fetch() calls, one place
    └── components/
        ├── WarRoom.jsx
        ├── WarRoom.css
        ├── PositionColumn.jsx
        ├── PositionColumn.css
        ├── TierGroup.jsx
        ├── TierGroup.css
        ├── PlayerRow.jsx
        ├── PlayerRow.css
        ├── NotesDialog.jsx
        ├── AddPlayerDialog.jsx
        └── DeleteConfirmDialog.jsx
```

### 2. Dependencies (`package.json`)

```json
{
  "name": "ff-draft-room",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0"
  }
}
```

### 3. Vite Config (`vite.config.js`)

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

All `/api/*` requests proxy to FastAPI. No CORS issues in dev.

### 4. Design System (`src/App.css`)

CSS custom properties, applied globally:

```css
:root {
  --bg-primary:    #0D1B2A;
  --bg-secondary:  #132338;
  --bg-tier-odd:   #132338;
  --bg-tier-even:  #0A1628;
  --accent:        #0076B6;
  --accent-hover:  #005A8E;
  --border:        #1E3A5F;
  --text-primary:  #E8E8E8;
  --text-muted:    #6A8CAA;
  --player-bg:     #1A3A5C;
  --player-hover:  #0076B6;
  --danger:        #C0392B;
  --success:       #00C805;
  --font:          'Courier New', Courier, monospace;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font);
  font-size: 12px;
}
```

### 5. API Layer (`src/api/rankings.js`)

All fetch calls in one file. No fetch calls in components.

```js
const BASE = '/api/rankings'

export const getPositionPlayers = (position) =>
  fetch(`${BASE}/${position}`).then(r => r.json())

export const reorderPlayers = (position, rank_a, rank_b) =>
  fetch(`${BASE}/${position}/reorder`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rank_a, rank_b })
  }).then(r => r.json())

export const addPlayer = (position, name, team, tier) =>
  fetch(`${BASE}/${position}/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, team, tier })
  }).then(r => r.json())

export const deletePlayer = (position, rank) =>
  fetch(`${BASE}/${position}/${rank}`, { method: 'DELETE' })
    .then(r => r.json())

export const updateNotes = (position, rank, notes) =>
  fetch(`${BASE}/${position}/${rank}/notes`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes })
  }).then(r => r.json())

export const saveRankings = () =>
  fetch(`${BASE}/save`, { method: 'POST' }).then(r => r.json())
```

### 6. State Management

No Redux, no Zustand — plain React state is sufficient.

**`App.jsx`** holds top-level state:
```jsx
const [rankings, setRankings] = useState({
  QB: [], RB: [], WR: [], TE: []
})
const [dirty, setDirty] = useState(false)
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)
```

On mount: fetch all 4 positions in parallel:
```js
useEffect(() => {
  Promise.all(
    ['QB','RB','WR','TE'].map(pos =>
      getPositionPlayers(pos).then(players => [pos, players])
    )
  ).then(results => {
    setRankings(Object.fromEntries(results))
    setLoading(false)
  })
}, [])
```

State update pattern after any mutation:
```js
// After reorder/add/delete — API returns updated position list
const handleReorder = async (position, rank_a, rank_b) => {
  const updated = await reorderPlayers(position, rank_a, rank_b)
  setRankings(prev => ({ ...prev, [position]: updated }))
  setDirty(true)
}
```

### 7. Component Breakdown

**`App.jsx`**
- Holds all state
- Renders `<WarRoom>` passing state + handlers as props
- Handles save: calls `saveRankings()`, sets `dirty = false`

**`WarRoom.jsx`**
- Layout: header row + 4-column grid
- Header: `🏈 WAR ROOM` title, unsaved indicator, SAVE button
- Grid: `display: grid; grid-template-columns: repeat(4, 1fr); gap: 32px`
- Renders `<PositionColumn>` for each position
- Renders whichever dialog is currently open (notes / add / delete)

**`PositionColumn.jsx`**
- Props: `position`, `players`, `onReorder`, `onAdd`, `onDelete`, `onNotesOpen`, `onAddOpen`
- Column header: position name + player count
- Groups players by tier: `players.reduce((groups, p) => ...)`
- Renders `<TierGroup>` for each tier

**`TierGroup.jsx`**
- Props: `position`, `tierNum`, `players`, `isFirst`, `isLast` (for ▲▼ disable logic), all handlers
- Tier header: `— TIER {n} —` with alternating background
  - Odd tier: `var(--bg-tier-odd)`
  - Even tier: `var(--bg-tier-even)`
- Players list
- Add button at bottom: `+ {position} · Tier {n}`

**`PlayerRow.jsx`**
- Props: `player`, `position`, `isFirst`, `isLast`, `onMoveUp`, `onMoveDown`, `onNameClick`, `onDeleteClick`
- Layout: `display: grid; grid-template-columns: 24px 24px 28px 1fr 40px 24px`
- Columns: `▲` | `▼` | rank | name button | team | `×`
- Name button: `background: var(--player-bg)`, hover `var(--player-hover)`
- `📝` appended to name if `player.notes !== ""`
- `▲` disabled (opacity + pointer-events) if `isFirst`
- `▼` disabled if `isLast`

**`NotesDialog.jsx`**
- Props: `player`, `position`, `onSave`, `onClose`
- Native HTML `<dialog>` element — real modal, no z-index hacks
- `dialog.showModal()` / `dialog.close()` via `useRef`
- Textarea pre-filled with `player.notes`
- Save / Close buttons

**`AddPlayerDialog.jsx`**
- Props: `position`, `tier`, `onAdd`, `onClose`
- Native `<dialog>`
- Inputs: Name (text), Team (text, maxLength=4)
- Validation: name required, team required, shown inline
- Error from API (duplicate) shown inline

**`DeleteConfirmDialog.jsx`**
- Props: `player`, `position`, `onConfirm`, `onClose`
- Native `<dialog>`
- `"Remove {name} ({team}) from {position} rankings?"`
- `"This cannot be undone."`
- Delete (red) / Cancel buttons

### 8. Layout Details

**War Room header** (`WarRoom.css`):
```css
.war-room-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}

.war-room-title {
  font-size: 24px;
  font-weight: bold;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.unsaved-indicator {
  color: var(--accent);
  font-size: 12px;
  letter-spacing: 1px;
}

.save-button {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
  padding: 6px 20px;
  font-family: var(--font);
  font-size: 12px;
  letter-spacing: 2px;
  cursor: pointer;
}

.save-button:hover {
  background: var(--accent);
  color: white;
}
```

**Position columns grid**:
```css
.war-room-columns {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
  padding: 0 24px 24px;
}
```

**Column divider** — use border-right on first 3 columns:
```css
.position-column:not(:last-child) {
  border-right: 1px solid var(--border);
  padding-right: 32px;
}
```

**Tier header**:
```css
.tier-header {
  font-size: 10px;
  letter-spacing: 3px;
  color: var(--text-muted);
  padding: 4px 8px;
  margin: 8px 0 4px;
  border-radius: 3px;
}
.tier-odd  { background: var(--bg-tier-odd); }
.tier-even { background: var(--bg-tier-even); }
```

**Player row**:
```css
.player-row {
  display: grid;
  grid-template-columns: 24px 24px 24px 1fr 36px 24px;
  align-items: center;
  gap: 4px;
  margin-bottom: 3px;
}

.player-name-btn {
  background: var(--player-bg);
  border: none;
  color: var(--text-primary);
  font-family: var(--font);
  font-size: 11px;
  padding: 3px 8px;
  text-align: left;
  cursor: pointer;
  border-radius: 3px;
  width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.player-name-btn:hover { background: var(--player-hover); }

.control-btn {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  font-size: 10px;
  width: 24px;
  height: 24px;
  cursor: pointer;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.control-btn:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.control-btn:disabled { opacity: 0.25; cursor: default; }

.delete-btn {
  color: var(--text-muted);
  border-color: transparent;
  background: transparent;
}
.delete-btn:hover:not(:disabled) { color: var(--danger); border-color: var(--danger); }

.player-team {
  color: var(--text-muted);
  font-size: 10px;
  text-align: center;
}

.player-rank {
  color: var(--text-muted);
  font-size: 10px;
  text-align: right;
}
```

**Dialog** (shared base):
```css
dialog {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: var(--font);
  padding: 24px;
  min-width: 320px;
}
dialog::backdrop {
  background: rgba(0, 0, 0, 0.6);
}
```

**Add button** (bottom of tier):
```css
.add-tier-btn {
  width: 100%;
  background: transparent;
  border: 1px dashed var(--border);
  color: var(--text-muted);
  font-family: var(--font);
  font-size: 10px;
  padding: 4px;
  margin-top: 4px;
  cursor: pointer;
  border-radius: 3px;
  letter-spacing: 1px;
}
.add-tier-btn:hover { border-color: var(--accent); color: var(--accent); }
```

---

## Success Criteria

1. `npm install` completes without errors
2. `npm run dev` starts at localhost:5173
3. With backend running: War Room loads, 4 columns visible
4. QB 30 / RB 50 / WR 50 / TE 30 players shown
5. Players grouped under tier headers — odd/even tiers visually distinct
6. Column dividers visible between positions
7. ▲▼ buttons reorder players — ranks update immediately
8. Moving across tier boundary updates player's tier number
9. ▲ disabled on rank 1; ▼ disabled on last rank
10. Click player name → notes dialog opens, notes pre-filled
11. Save notes → `📝` appears in name, unsaved indicator shown
12. `[+ QB · Tier 1]` → add dialog, validation works, duplicate rejected
13. `[×]` → confirm dialog, cancel works, delete removes player
14. `● Unsaved` indicator appears after any change
15. SAVE button → POST /api/rankings/save, indicator clears
16. Page reload → rankings preserved (loaded fresh from backend)
17. Backend not running → graceful error message shown
18. `ruff check backend/ tests/` still passes (no backend regressions)

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Backend not running | Loading spinner → error banner: `"Cannot connect to backend at localhost:8000"` |
| API call fails | Toast/banner with error message, state not updated |
| Add duplicate name | Inline error in add dialog: `"Already in {position} rankings"` |
| Add empty name/team | Inline error: `"Name and team are required"` |
| Network timeout | Retry not automatic — show error, user retries manually |

---

## Open Questions

*All resolved.*

1. ~~CSS framework?~~ → Plain CSS, custom properties only
2. ~~State management?~~ → React useState, no external library
3. ~~Dialog implementation?~~ → Native HTML `<dialog>` — real modal, no z-index fights
4. ~~API proxy?~~ → Vite proxy config, no CORS config needed in dev
5. ~~Component CSS?~~ → Co-located `.css` file per component

---

## Out of Scope for This Init

- K and D/ST columns — `06-init-k-dst.md`
- Multiple named profiles — `07-init-rankings-profiles.md`
- Export to CSV — Phase 1c
- Drag-and-drop reordering — future
- Live Draft — Phase 2
- Production build / deployment — local only
