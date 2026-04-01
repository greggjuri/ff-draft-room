# 08-init-search.md — Global Player Search

## Feature Summary
Add a global search bar to the War Room header. Typing filters all 4 position
columns simultaneously, showing matches in a dropdown overlay grouped by position.
Clicking a result scrolls to that player's row in their column and highlights it
briefly. Works identically in War Room and Draft Mode. Pure frontend — no backend
changes required.

## Status
- [x] Open questions resolved
- [x] Ready for PRP generation

---

## Requirements

### 1. Search Box Placement

In the War Room header, between the mode toggle and the profile name:
```
🏈 WAR ROOM  [WAR ROOM|DRAFT]  [🔍 Search players...]  2026 Draft  ● UNSAVED  [SAVE]...
```

- `<input type="text">` with search icon prefix
- Placeholder: `"Search players..."`
- Width: ~220px fixed
- Clears on Escape key
- Shows dropdown when value is non-empty and matches exist

### 2. Search Logic

Performed entirely in React against the already-loaded `rankings` state.
No API calls.

```js
// In App.jsx or a useMemo hook
const searchResults = useMemo(() => {
  if (!searchQuery.trim()) return []
  const q = searchQuery.toLowerCase()
  const results = []
  for (const position of ['QB', 'RB', 'WR', 'TE']) {
    const matches = rankings[position].filter(p =>
      p.name.toLowerCase().includes(q) ||
      p.team.toLowerCase().includes(q)
    )
    if (matches.length > 0) {
      results.push({ position, players: matches })
    }
  }
  return results
}, [searchQuery, rankings])
```

Matches on player name OR team abbreviation (case-insensitive).
Results grouped by position in order: QB → RB → WR → TE.
Max 5 results per position in the dropdown (prevents overwhelming output).

### 3. Dropdown Overlay

Appears directly below the search input, absolutely positioned.
Stays on top of everything (high z-index).
Columns remain fully visible and interactive behind it.

```
┌─────────────────────────────┐
│ 🔍 allen                  × │
├─────────────────────────────┤
│  QB                         │
│  ● 1  Josh Allen    BUF     │
│                             │
│  RB                         │
│  ● 14  Kendre Miller  NO    │
└─────────────────────────────┘
```

**Dropdown structure:**
- Position group header: `QB`, `RB`, `WR`, `TE` — muted, small caps
- Each result row: status dot (draft mode) or plain circle (war room) · rank · name · team
- Hover state: highlight row
- Click: scroll to player, close dropdown
- Max height: 320px with scroll if overflow
- Closes when: result clicked, Escape pressed, click outside, search cleared

### 4. Scroll to Player

When a search result is clicked:

1. Close dropdown, clear search input
2. Identify the target player's column (`position`) and rank
3. Use a `data-player-id` attribute on each `PlayerRow` for targeting:
   ```jsx
   <div
     className="player-row"
     data-player-id={`${position}-${player.position_rank}`}
   >
   ```
4. Scroll to the element:
   ```js
   const el = document.querySelector(
     `[data-player-id="${position}-${rank}"]`
   )
   el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
   ```
5. Briefly highlight the row — add `.search-highlight` class, remove after 1.5s:
   ```js
   el?.classList.add('search-highlight')
   setTimeout(() => el?.classList.remove('search-highlight'), 1500)
   ```

**Highlight CSS:**
```css
.player-row.search-highlight .player-name-btn {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
  transition: outline 0.3s ease;
}
```

### 5. State

```js
// App.jsx
const [searchQuery, setSearchQuery] = useState('')
```

Passed to `<WarRoom>` → `<SearchBar>` component.
`searchResults` derived via `useMemo`.

### 6. New Component: `SearchBar.jsx`

```
frontend/src/components/SearchBar.jsx
frontend/src/components/SearchBar.css
```

Props:
```js
SearchBar({
  query,           // string
  onChange,        // (value) => void
  results,         // [{ position, players }]
  onSelectResult,  // (position, rank) => void
  isDraft,         // bool — controls dot vs plain circle in results
  getDraftStatus,  // (position, rank) => status string
})
```

Internal state:
- `isOpen` — true when results exist and input is focused/active
- Closes on outside click via `useEffect` + `mousedown` listener on `document`

**Keyboard support:**
- Escape → clears query, closes dropdown
- (Arrow key navigation is out of scope for this init)

### 7. Search Result Row

Each result in the dropdown:
```
[dot/circle]  [rank]  [name]  [team]
```

- In **Draft Mode**: show colored status dot matching current draft status
- In **War Room**: show a plain muted circle (no status meaning)
- `rank` in muted text
- `name` in primary text — matching portion bolded via string split:
  ```js
  // e.g. query="allen", name="Josh Allen"
  // renders: "Josh " + <strong>Allen</strong>
  ```
- `team` in muted text, right-aligned

### 8. CSS

**Search input** (`SearchBar.css`):
```css
.search-container {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-primary);
  font-family: var(--font);
  font-size: 11px;
  padding: 4px 8px 4px 28px; /* room for icon */
  width: 220px;
  outline: none;
}
.search-input:focus {
  border-color: var(--accent);
}

.search-icon {
  position: absolute;
  left: 8px;
  color: var(--text-muted);
  font-size: 11px;
  pointer-events: none;
}

.search-clear {
  position: absolute;
  right: 6px;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 11px;
  background: none;
  border: none;
  padding: 0;
}
.search-clear:hover { color: var(--text-primary); }
```

**Dropdown** (`SearchBar.css`):
```css
.search-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  width: 300px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 4px;
  z-index: 1000;
  max-height: 320px;
  overflow-y: auto;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}

.search-position-header {
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--text-muted);
  padding: 8px 12px 4px;
  text-transform: uppercase;
}

.search-result-row {
  display: grid;
  grid-template-columns: 16px 28px 1fr 36px;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  cursor: pointer;
}
.search-result-row:hover { background: var(--bg-primary); }

.search-result-rank  { color: var(--text-muted); font-size: 10px; }
.search-result-name  { font-size: 11px; color: var(--text-primary); }
.search-result-name strong { color: var(--accent); }
.search-result-team  { color: var(--text-muted); font-size: 10px; text-align: right; }

.search-no-results {
  padding: 12px;
  color: var(--text-muted);
  font-size: 11px;
  text-align: center;
}
```

---

## Success Criteria

1. Search box visible in header in both War Room and Draft Mode
2. Typing filters against all 4 positions in memory — no API calls
3. Dropdown appears below search box with matches grouped by position
4. Max 5 results per position shown in dropdown
5. Matching text portion is bolded in result name
6. In Draft Mode: result rows show colored status dots
7. In War Room: result rows show plain muted circles
8. Clicking a result: dropdown closes, page scrolls smoothly to player row
9. Target player row briefly highlighted with Honolulu Blue outline
10. Escape clears search and closes dropdown
11. Clicking outside dropdown closes it
12. × button in search box clears query
13. Empty query → no dropdown shown
14. No matches → dropdown shows `"No players found"`
15. Backend tests unaffected (49 passing)
16. Frontend builds with zero errors

---

## No Backend Changes

Pure frontend feature. Search operates on `rankings` state already in memory.
No new API endpoints. No changes to backend files or tests.

---

## Component Changes Summary

| File | Change |
|------|--------|
| `frontend/src/components/SearchBar.jsx` | New component |
| `frontend/src/components/SearchBar.css` | New styles |
| `frontend/src/App.jsx` | `searchQuery` state, `searchResults` memo, `handleSelectResult` |
| `frontend/src/components/WarRoom.jsx` | Add `<SearchBar>` to header |
| `frontend/src/components/WarRoom.css` | Header layout adjustment |
| `frontend/src/components/PlayerRow.jsx` | Add `data-player-id` attribute |

---

## Open Questions

*All resolved.*

1. ~~Where does search appear?~~ → Header, both modes
2. ~~Where do results show?~~ → Dropdown overlay, columns stay visible
3. ~~What does clicking a result do?~~ → Scroll to player in column + highlight
4. ~~One box or per-column?~~ → One global box

---

## Out of Scope

- Keyboard arrow navigation in dropdown
- Filter-in-place (hiding non-matches in columns)
- Search within a single column only
- Saved search history
