# PRP-08: Global Player Search

**Created**: 2026-03-31
**Initial**: `initials/08-init-search.md`
**Status**: Ready

---

## Overview

### Problem Statement
With 160 players across 4 columns, finding a specific player requires scrolling through multiple tier groups. There's no way to quickly locate a player by name or team.

### Proposed Solution
Add a global search bar to the War Room header. Typing filters all 4 positions in memory (no API calls). Matches appear in a dropdown overlay grouped by position. Clicking a result scrolls to the player's row and briefly highlights it. Works in both War Room and Draft Mode.

**Pure frontend feature** — no backend changes.

### Success Criteria
- [ ] Search box visible in header (both modes)
- [ ] Typing filters all 4 positions — no API calls
- [ ] Dropdown shows matches grouped by position (max 5 per position)
- [ ] Matching text bolded in result name
- [ ] Draft Mode: result rows show colored status dots
- [ ] War Room: result rows show plain muted circles
- [ ] Click result → scroll to player, highlight with blue outline 1.5s
- [ ] Escape clears search and closes dropdown
- [ ] Click outside closes dropdown
- [ ] × button clears query
- [ ] Empty query → no dropdown
- [ ] No matches → `"No players found"`
- [ ] Backend tests unaffected (49 passing)
- [ ] Frontend builds with zero errors

---

## Context

### Dependencies
- **Required**: PRP-05 (frontend) ✅, PRP-07 (draft mode) ✅
- **Optional**: None

### Files to Create
```
frontend/src/components/SearchBar.jsx
frontend/src/components/SearchBar.css
```

### Files to Modify
```
frontend/src/App.jsx                   # searchQuery state, searchResults memo, handleSelectResult
frontend/src/components/WarRoom.jsx    # Render <SearchBar> in header
frontend/src/components/PlayerRow.jsx  # Add data-player-id attribute
frontend/src/components/PlayerRow.css  # search-highlight style
```

### Files Untouched
```
backend/        — no changes
tests/          — no changes
```

---

## Technical Specification

### State (`App.jsx`)
```js
const [searchQuery, setSearchQuery] = useState('')

const searchResults = useMemo(() => {
  if (!searchQuery.trim()) return []
  const q = searchQuery.toLowerCase()
  const results = []
  for (const position of ['QB', 'RB', 'WR', 'TE']) {
    const matches = rankings[position].filter(p =>
      p.name.toLowerCase().includes(q) ||
      p.team.toLowerCase().includes(q)
    ).slice(0, 5)
    if (matches.length > 0) results.push({ position, players: matches })
  }
  return results
}, [searchQuery, rankings])
```

### Scroll + Highlight (`handleSelectResult`)
```js
const handleSelectResult = (position, rank) => {
  setSearchQuery('')
  const el = document.querySelector(`[data-player-id="${position}-${rank}"]`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('search-highlight')
    setTimeout(() => el.classList.remove('search-highlight'), 1500)
  }
}
```

### SearchBar Component Props
```js
SearchBar({ query, onChange, results, onSelectResult, isDraft, getDraftStatus })
```

Internal state: `isOpen` — controlled by focus/blur and outside click listener.

### PlayerRow Data Attribute
```jsx
<div className="player-row" data-player-id={`${position}-${player.position_rank}`}>
```

---

## Implementation Steps

### Step 1: SearchBar Component
**Files**: `frontend/src/components/SearchBar.jsx`, `SearchBar.css`

1. Input with search icon prefix, clear × button
2. Dropdown: position headers, result rows with dot/rank/name/team
3. Name highlighting: split on query match, wrap in `<strong>`
4. Outside click detection via `useEffect` + `mousedown` listener
5. Escape key clears and closes
6. All CSS from init spec

**Validation**: `npx vite build` — no errors

---

### Step 2: App.jsx — Search State + Memo
**Files**: `frontend/src/App.jsx`

1. Add `searchQuery` state
2. Add `searchResults` useMemo
3. Add `handleSelectResult` function
4. Pass to `<WarRoom>`: `searchQuery`, `onSearchChange`, `searchResults`, `onSelectResult`

**Validation**: No build errors

---

### Step 3: WarRoom — Render SearchBar in Header
**Files**: `frontend/src/components/WarRoom.jsx`

Insert `<SearchBar>` between mode toggle and profile name.
Pass `isDraft` and `getDraftStatus` for dot rendering in results.

**Validation**: Search box visible in header

---

### Step 4: PlayerRow — Data Attribute + Highlight CSS
**Files**: `frontend/src/components/PlayerRow.jsx`, `PlayerRow.css`

1. Add `data-player-id={`${position}-${player.position_rank}`}` to both war room and draft row divs
2. Add `.search-highlight .player-name-btn` outline CSS

**Validation**: Build succeeds, `data-player-id` attributes in DOM

---

### Step 5: Final Integration Check
**Commands**:
```bash
cd frontend && npx vite build
pytest tests/ -q
ruff check backend/ tests/
```

- [ ] Frontend builds (0 errors)
- [ ] Backend tests pass (49 passing)
- [ ] Lint clean
- [ ] Commit and push

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Type "allen" in search | Dropdown shows Josh Allen (QB) + any RB/WR matches | ☐ |
| 2 | Verify max 5 per position | No position shows more than 5 results | ☐ |
| 3 | Verify bold text | "Allen" portion bolded in results | ☐ |
| 4 | Click Josh Allen result | Dropdown closes, scrolls to QB rank, blue outline flash | ☐ |
| 5 | Type "BUF" | Shows all Buffalo players across positions | ☐ |
| 6 | Press Escape | Search clears, dropdown closes | ☐ |
| 7 | Type, click × | Query cleared, dropdown closes | ☐ |
| 8 | Type "zzzzz" | "No players found" message | ☐ |
| 9 | Click outside dropdown | Dropdown closes, query stays | ☐ |
| 10 | Switch to Draft Mode | Search still works, dots show status | ☐ |
| 11 | `npx vite build` | Zero errors | ☐ |
| 12 | `pytest tests/ -q` | 49 passed, 1 skipped | ☐ |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Empty query | No dropdown shown |
| No matches | Dropdown: "No players found" |
| Player deleted after search | scrollIntoView no-op (element gone) |

---

## Open Questions

None.

---

## Rollback Plan

1. Remove `SearchBar.jsx` and `SearchBar.css`
2. Revert changes to App.jsx, WarRoom.jsx, PlayerRow.jsx/css
3. No backend changes to revert

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Every UI element, CSS rule, and interaction specified |
| Feasibility | 10 | In-memory filter, DOM scrollIntoView — standard React patterns |
| Completeness | 10 | Component, styles, state, dropdown, highlight all covered |
| Alignment | 10 | No backend changes, fully consistent with architecture |
| **Average** | **10** | |
