# 07-init-draft-mode.md — Draft Mode

## Feature Summary
Add a Draft Mode toggle to the War Room header. Draft Mode shows the same
4-column layout with no reorder/delete/add controls. Each player name box
has a clickable status dot that cycles through undrafted → mine → other →
undrafted. Mine = green background, other = muted purple background.
Draft state is in-memory only — toggling back to War Room resets it.

This is a pure frontend feature. No backend changes required.

## Status
- [x] Open questions resolved
- [x] Ready for PRP generation

---

## Requirements

### 1. Mode Toggle

**Header** — add toggle button between title and profile name:
```
🏈 WAR ROOM   [WAR ROOM | DRAFT]   Mock Draft 1   ● UNSAVED   [SAVE] ...
```

Toggle button styles:
- `WAR ROOM` active: Honolulu Blue accent border, blue text
- `DRAFT` active: green accent border, green text
- Inactive side: muted, no border

When switching **War Room → Draft**:
- Draft state initializes: all players `status: "undrafted"`
- War Room controls hidden (▲▼, ×, add buttons, save toolbar)

When switching **Draft → War Room**:
- Draft state wiped entirely (reset to all undrafted)
- War Room controls restored
- Confirm if any players have been marked: `"Exit draft mode? All pick markings will be lost."`

### 2. Draft State

Stored in React state only — never sent to backend:

```js
// In App.jsx
const [mode, setMode] = useState('warroom') // 'warroom' | 'draft'
const [draftState, setDraftState] = useState({})
// Shape: { "QB-1": "mine", "RB-3": "other", "WR-7": "mine" }
// Key format: "{position}-{position_rank}"
// Values: "undrafted" | "mine" | "other"
// Missing key = "undrafted" (default)
```

### 3. Player Status Dot

A small clickable circle rendered on the left side of each player name box.

**Dot states:**
```
● undrafted  →  dim grey dot  (#3A4A5A)
● mine       →  bright green  (#00C805)
● other      →  soft purple   (#9B59B6)
```

**Click behavior** — cycles through states:
```
undrafted → mine → other → undrafted → ...
```

**Dot placement** — inside the player name button, left edge:
```
[● Josh Allen          BUF]
```

Name button layout in draft mode:
```
[dot] [name text........................] [team]
```

The dot is a `<span>` inside the name button, `onClick` with `stopPropagation`.
Left-clicking the dot cycles the status. Left-clicking the name text does nothing
in draft mode (notes dialog disabled).

### 4. Player Name Box Colors in Draft Mode

Override the tier-based alternating colors when a draft status is set:

```css
/* Undrafted — keep existing tier colors (no override) */

/* Mine — dark green */
.player-name-btn.status-mine {
  background: #1B4332 !important;
  color: #E8E8E8;
  opacity: 1;
}

/* Other — dark purple */
.player-name-btn.status-other {
  background: #2D1B4E !important;
  color: #B8A8D0;
  opacity: 0.85;
}

/* Undrafted in draft mode — slightly dimmed to make drafted players pop */
.draft-mode .player-name-btn.status-undrafted {
  opacity: 0.7;
}
/* But once any player is drafted, undrafted ones dim further */
.draft-mode.has-picks .player-name-btn.status-undrafted {
  opacity: 0.55;
}
```

Add `draft-mode` class to the war room root div when in draft mode.
Add `has-picks` class once at least one player is marked mine or other.

### 5. Draft Mode Layout Differences

When `mode === 'draft'`:

**Hidden completely:**
- ▲ and ▼ buttons (entire columns in player row grid)
- × delete button
- `[+ Position · Tier N]` add buttons
- Save toolbar (SAVE, SAVE AS, LOAD, RESET, SET DEFAULT buttons)
- Unsaved indicator

**Shown:**
- Mode toggle button
- Profile name (read-only display)
- All 4 position columns with tier groups
- Player name boxes with status dots
- Team labels
- Rank numbers
- Tier headers

**Player row grid in draft mode:**
```css
/* War room mode: 24px 24px 24px 1fr 36px 24px */
/* Draft mode:    12px  24px  1fr  36px        */
/* (dot) (rank) (name) (team) */
```

Simplest implementation: pass `isDraft` prop to `PlayerRow`, conditionally
render controls.

### 6. Component Changes

**`App.jsx`**:
```js
const [mode, setMode] = useState('warroom')
const [draftState, setDraftState] = useState({})

const getDraftStatus = (position, rank) =>
  draftState[`${position}-${rank}`] || 'undrafted'

const cycleDraftStatus = (position, rank) => {
  const key = `${position}-${rank}`
  const current = draftState[key] || 'undrafted'
  const next = { undrafted: 'mine', mine: 'other', other: 'undrafted' }[current]
  setDraftState(prev => ({ ...prev, [key]: next }))
}

const enterDraftMode = () => {
  setMode('draft')
  setDraftState({})
}

const exitDraftMode = () => {
  const hasPicks = Object.values(draftState).some(s => s !== 'undrafted')
  if (hasPicks) {
    // show confirm dialog
  } else {
    setMode('warroom')
    setDraftState({})
  }
}
```

**`WarRoom.jsx`**:
- Receives `mode`, `onEnterDraft`, `onExitDraft` props
- Renders mode toggle in header
- Passes `isDraft` down to `PositionColumn` → `TierGroup` → `PlayerRow`
- Renders `ExitDraftConfirmDialog` when needed

**`PositionColumn.jsx`**:
- Receives `isDraft`, passes to `TierGroup`

**`TierGroup.jsx`**:
- Receives `isDraft`
- Hides add button when `isDraft`
- Passes `isDraft` to `PlayerRow`

**`PlayerRow.jsx`**:
- Receives `isDraft`, `draftStatus`, `onStatusClick`
- When `isDraft`:
  - Hide ▲, ▼, × buttons
  - Show status dot in name box
  - Notes click disabled (no-op)
- Status dot: `<span className={`draft-dot status-${draftStatus}`} onClick={...} />`

**`ExitDraftConfirmDialog.jsx`** (new):
```
Exit Draft Mode?

All pick markings will be lost.

      [Exit]   [Stay in Draft]
```
Native `<dialog>`, same pattern as other confirm dialogs.

### 7. CSS

**Mode toggle button** (`WarRoom.css`):
```css
.mode-toggle {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 4px;
  overflow: hidden;
  font-size: 11px;
  letter-spacing: 1px;
}

.mode-toggle-btn {
  padding: 4px 12px;
  background: transparent;
  border: none;
  font-family: var(--font);
  cursor: pointer;
  color: var(--text-muted);
}

.mode-toggle-btn.active-warroom {
  background: transparent;
  border-right: 1px solid var(--border);
  color: var(--accent);
}

.mode-toggle-btn.active-draft {
  background: transparent;
  color: #00C805;
}
```

**Status dot** (`PlayerRow.css`):
```css
.draft-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
  flex-shrink: 0;
  cursor: pointer;
  transition: background 0.15s;
}

.draft-dot.status-undrafted { background: #3A4A5A; }
.draft-dot.status-mine      { background: #00C805; }
.draft-dot.status-other     { background: #9B59B6; }
```

**Name box in draft mode** (`PlayerRow.css`):
```css
.player-name-btn.status-mine  { background: #1B4332 !important; }
.player-name-btn.status-other { background: #2D1B4E !important; }

.draft-mode .player-name-btn.status-undrafted { opacity: 0.7; }
.draft-mode.has-picks .player-name-btn.status-undrafted { opacity: 0.55; }
```

---

## Success Criteria

1. Mode toggle visible in header — `WAR ROOM | DRAFT` button
2. Clicking DRAFT → enters draft mode, all controls hidden
3. All 4 columns visible in draft mode with tier groups intact
4. Each player name box shows a grey dot on left edge
5. Click dot → cycles undrafted → mine → other → undrafted
6. Mine → green background on name box, green dot
7. Other → purple background on name box, purple dot
8. Undrafted players dim slightly once any pick is made
9. Clicking WAR ROOM with picks → confirm dialog appears
10. Confirm exit → draft state wiped, War Room controls restored
11. No picks → exits draft mode immediately, no confirm
12. Toggling back and forth resets draft state each time
13. Notes dialog does not open in draft mode
14. `ruff check backend/ tests/` still passes (no backend regressions)
15. Frontend builds with zero errors

---

## No Backend Changes

This feature is entirely frontend state. No new API endpoints, no changes to
`data/rankings/`, no changes to backend files.

Backend tests (49 passing) must remain unaffected.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Exit draft with picks | Confirm dialog before wiping state |
| Exit draft with no picks | Immediate exit, no dialog |
| Notes click in draft mode | No-op (disabled) |

---

## Open Questions

*All resolved.*

1. ~~How to switch modes?~~ → Toggle button in header
2. ~~Does draft state persist?~~ → In-memory only, resets on exit
3. ~~How to mark players?~~ → Clickable dot/badge on name box
4. ~~Round/pick tracking?~~ → No, color coding only

---

## Out of Scope for This Init

- Undo last pick
- Filter to show only available players
- Export draft results
- Round/pick counter
- K and D/ST columns
- Live Draft Phase 2 features
