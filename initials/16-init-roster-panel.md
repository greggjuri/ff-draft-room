# 16-init-roster-panel.md — My Roster Panel

## Goal

Add a **My Roster** drawer panel to Draft Mode that displays players the user
has marked `mine`, grouped by position, in a fixed bottom-anchored overlay.

Pure frontend feature — zero backend changes.

---

## Behaviour

### Visibility
- Panel is **only present in Draft Mode** — completely absent in War Room.
- A fixed **handle bar** is always visible at the bottom of the viewport
  while in Draft Mode, even when the panel is collapsed.
- Handle bar shows: `MY ROSTER` label (left) + pick count summary
  `QB 0 · RB 0 · WR 0 · TE 0` (right, updates live).
- Clicking the handle bar toggles the panel open/closed.
- **Default state**: collapsed on draft entry.

### Panel Content
Four position sections always rendered, even when empty:

```
┌─────────────────────────────────────────────────┐
│  QB · 1                                  [close] │
│  ──────────────────────────────────────────────  │
│  ♥  Josh Allen         BUF  [logo]               │
│                                                  │
│  RB · 2                                          │
│  ──────────────────────────────────────────────  │
│  🔥  Saquon Barkley    PHI  [logo]               │
│      De'Von Achane     MIA  [logo]               │
│                                                  │
│  WR · 0                                          │
│  ──────────────────────────────────────────────  │
│  — empty —                                       │
│                                                  │
│  TE · 0                                          │
│  ──────────────────────────────────────────────  │
│  — empty —                                       │
└─────────────────────────────────────────────────┘
  MY ROSTER                    QB 1 · RB 2 · WR 0 · TE 0
```

### Per-Player Row (inside panel)
- Tag icon (if any) — leftmost, same icon as PlayerRow
- Player name
- Team abbreviation (muted)
- Team logo (ESPN CDN, same src pattern as PlayerRow, 18px, opacity 72%)
- Players listed in the order they were marked `mine` (chronological pick order)

### Section headers
- Position label + pick count: `RB · 2`
- Position accent color on the label (QB gold / RB green / WR blue / TE orange)
  — matches existing column header accent colors
- `— empty —` placeholder row when section has zero picks (muted, italic)

### State lifecycle
- Roster panel state is **in-memory only** — never sent to backend.
- Wiped when the user exits Draft Mode (same as existing draft status wipe).
- Reactive: updates immediately when any player's status dot is clicked.

---

## Data Flow

The panel reads from two existing state sources already present in `WarRoom.jsx`:

1. **`rankings`** — the full player list (already loaded from backend on mount).
   Used to resolve player name, team, tag from a `(position, rank)` key.

2. **`draftStatuses`** — existing `Map` or object keyed by `{position}-{rank}`
   → `'undrafted' | 'mine' | 'other'`.

The panel filters `draftStatuses` for entries with value `'mine'`,
looks up the matching player from `rankings`, and groups by position.

**No new state required** — RosterPanel is a pure derived-display component.

---

## Components

### New: `RosterPanel.jsx` + `RosterPanel.css`

Props:
```javascript
RosterPanel({
  rankings,        // { QB: [...], RB: [...], WR: [...], TE: [...] }
  draftStatuses,   // { 'QB-1': 'mine', 'RB-3': 'other', ... }
  isOpen,          // boolean — controlled by WarRoom
  onToggle,        // () => void — called when handle bar clicked
})
```

Internal logic:
```javascript
// Derive my picks per position
const myPicks = POSITIONS.reduce((acc, pos) => {
  acc[pos] = (rankings[pos] ?? [])
    .filter(p => draftStatuses[`${pos}-${p.position_rank}`] === 'mine');
  return acc;
}, {});
```

### Modified: `WarRoom.jsx`

Add:
```javascript
const [rosterPanelOpen, setRosterPanelOpen] = useState(false);
```

Reset on draft exit (alongside existing status wipe):
```javascript
setRosterPanelOpen(false);
```

Render `<RosterPanel>` conditionally inside the draft mode block,
below the main columns layout and above nothing — it is fixed-position
so it does not affect document flow.

---

## Design Spec

### Handle bar
```css
position: fixed;
bottom: 0;
left: 0;
right: 0;
height: 36px;
background: #0D1B2A;
border-top: 1px solid #1E3A5F;
display: flex;
align-items: center;
justify-content: space-between;
padding: 0 16px;
cursor: pointer;
z-index: 200;
font-family: monospace;
font-size: 11px;
letter-spacing: 0.08em;
```

Handle bar hover: border-top color shifts to `#0076B6`.

### Panel drawer
```css
position: fixed;
bottom: 36px;   /* sits above the handle bar */
left: 0;
right: 0;
max-height: 40vh;
overflow-y: auto;
background: #0D1B2A;
border-top: 2px solid #0076B6;
z-index: 199;
padding: 12px 16px;
```

Slide animation: `transform: translateY(100%)` when closed →
`transform: translateY(0)` when open.
Transition: `transform 200ms ease`.

### Section header
```css
font-size: 11px;
letter-spacing: 0.1em;
font-weight: bold;
text-transform: uppercase;
margin: 8px 0 4px;
border-bottom: 1px solid #1E3A5F;
padding-bottom: 4px;
```
Position accent color applied to the label text (same CSS variables
already defined for column headers).

### Player row in panel
```css
display: flex;
align-items: center;
gap: 6px;
padding: 3px 0;
font-size: 12px;
font-family: monospace;
```
Team abbreviation: `color: #5A8AB0; font-size: 10px;`
Tag icon: same `<span>` rendering as `PlayerRow.jsx`.
Team logo: same ESPN CDN `<img>` pattern as `PlayerRow.jsx` — reuse exactly.

### Empty placeholder
```css
color: #3A5A7A;
font-style: italic;
font-size: 11px;
padding: 2px 0;
```

### Column padding in draft mode
When the panel is open, add `padding-bottom: calc(40vh + 36px)` to the
main columns container so content below the fold isn't permanently hidden
under the drawer. When collapsed, `padding-bottom: 36px` (handle bar height
only) so the last players aren't clipped.

---

## Files Changed

| File | Change |
|---|---|
| `frontend/src/components/RosterPanel.jsx` | **New** — panel component |
| `frontend/src/components/RosterPanel.css` | **New** — panel styles |
| `frontend/src/components/WarRoom.jsx` | Add `rosterPanelOpen` state + mount `<RosterPanel>` + reset on exit |
| `frontend/src/components/WarRoom.css` | Add `padding-bottom` rule for draft mode panel offset |

No backend changes. No new API routes. No test changes.

---

## Edge Cases

| Case | Behaviour |
|---|---|
| Player marked `mine` then re-clicked to `other` | Disappears from panel immediately |
| All 4 positions empty | Panel shows 4 empty sections with `— empty —` |
| Many picks (8+) | `max-height: 40vh` + `overflow-y: auto` handles scroll |
| Draft exited with picks | Panel wiped alongside `draftStatuses` reset |
| War Room mode | `<RosterPanel>` not rendered; no handle bar visible |

---

## Out of Scope

- Round or pick number tracking — separate future feature
- Snake draft pick countdown — separate future feature
- Reordering picks inside the panel — War Room handles ranking, not panel
- `other` picks shown — panel is "my team" only
- Backend persistence of draft state — explicitly excluded (ADR, draft state is ephemeral)

---

## Acceptance Criteria

1. Handle bar is visible at viewport bottom whenever Draft Mode is active.
2. Handle bar pick summary (`QB 0 · RB 2 · …`) updates in real time as dots are clicked.
3. Clicking handle bar toggles panel open/closed with slide animation.
4. Panel shows all 4 position sections regardless of pick count.
5. Empty sections show `— empty —` placeholder.
6. Player rows show tag icon (if set), name, team abbreviation, team logo.
7. Players appear in the panel the moment their dot is clicked to `mine`.
8. Players disappear from the panel when their dot cycles away from `mine`.
9. Panel and handle bar are absent in War Room mode.
10. Draft exit wipes panel state and collapses it.
11. Main column content is not hidden under the panel when it is open.
12. Design matches existing system: navy background, monospace, position accent colors.
