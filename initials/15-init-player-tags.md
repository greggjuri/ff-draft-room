# 15-init-player-tags.md — Player Tag Icons

**Date**: 2026-04-15
**Phase**: 1d — Polish
**Scope**: Backend + Frontend
**New tests**: Yes — tag utility function
**New ADR**: None

---

## Context

Players currently support free-text `notes`. This spec adds a single
structured `tag` field — a short string key that maps to a visual icon
displayed inside the player name box. Tags give instant visual signals
during draft prep and on draft day without opening the notes dialog.

The implementation mirrors the existing `notes` pattern exactly:
a new field on the player dict, a new utility function, and a new
`PUT /{position}/{rank}/tag` endpoint.

---

## Tag Set

| Key | Display | Rendering | Meaning |
|-----|---------|-----------|---------|
| `heart` | ❤ | Red heart emoji | Love — priority target |
| `fire` | 🔥 | Fire emoji | Breakout — hot hand this year |
| `gem` | 💎 | Gem emoji | Sleeper — late round value |
| `warning` | ⚠ | Warning emoji | Risky — injury history or unclear situation |
| `cross` | ✚ | `✚` in CSS red `#E03030` | Hurt — currently injured or limited |
| `skull` | ☠ | Skull emoji | Avoid — don't trust, stay away |
| `flag` | 🚩 | Flag emoji | Red flag — off-field concern or scheme fit |

The red cross (`cross`) is rendered as a styled HTML `<span>` with the `✚`
character in `color: #E03030` rather than an emoji — this ensures consistent
appearance across all OS/browser combinations where emoji rendering varies.
All other tags use their native emoji character which renders consistently
in modern browsers.

**Tag keys are short lowercase strings** stored in the JSON — never the
emoji character itself. This keeps the data clean and rendering logic in
the frontend.

---

## Data Model

### Player dict — new field

```json
{
  "position_rank": 1,
  "name": "Patrick Mahomes",
  "team": "KC",
  "position": "QB",
  "tier": 1,
  "notes": "",
  "tag": ""
}
```

`tag` is an empty string `""` when no tag is set. Valid values:
`""`, `"heart"`, `"fire"`, `"gem"`, `"warning"`, `"cross"`, `"skull"`, `"flag"`.

---

## Backend

### Data migration — seeding and existing profiles

The `seed_rankings()` function builds new player dicts. Add `"tag": ""`
to the new player template in `add_player()` and `seed_rankings()`.

Existing profiles in `default.json` / `seed.json` / named profiles will
not have a `tag` field. The backend must handle missing `tag` gracefully —
wherever player dicts are read, treat missing `tag` as `""`. The safest
place is in `get_position_players()` or at the API response layer:

```python
# Ensure tag field present on all returned players
for p in players:
    p.setdefault("tag", "")
```

This means no migration script is needed — old profiles just get `tag: ""`
defaulted on read.

### New utility function (`backend/utils/rankings.py`)

```python
VALID_TAGS: frozenset[str] = frozenset(
    {"", "heart", "fire", "gem", "warning", "cross", "skull", "flag"}
)

def set_player_tag(
    profile: dict, position: str, position_rank: int, tag: str
) -> dict:
    """Set or clear the tag on a player.

    Returns a new profile dict — does not mutate input.
    Raises ValueError if tag is not in VALID_TAGS.
    Raises ValueError if player not found.
    """
    if tag not in VALID_TAGS:
        raise ValueError(f"Invalid tag: {tag!r}")

    new_profile = copy.deepcopy(profile)
    for p in new_profile["players"]:
        if p["position"] == position and p["position_rank"] == position_rank:
            p["tag"] = tag
            return new_profile

    raise ValueError(f"Player not found: {position} rank {position_rank}")
```

### New API endpoint (`backend/routers/rankings.py`)

```python
class TagRequest(BaseModel):
    tag: str

@router.put("/{position}/{rank}/tag")
def update_tag(
    request: Request, position: str, rank: int, body: TagRequest
) -> dict:
    """Set or clear the tag on a player."""
```

- `_validate_position(position)` — 404 if not a known position
- Find player — 404 if rank not found
- Call `set_player_tag()` — 400 on `ValueError` (invalid tag)
- `_set_profile(updated)`
- Return updated player dict (same pattern as `update_notes`)

**Route registration**: `/{position}/{rank}/tag` is a sub-route of
`/{position}/{rank}` — same level as the existing `/notes` and `/tier`
endpoints. No ordering concern.

---

## Frontend

### `frontend/src/api/rankings.js` — new function

```js
export const setPlayerTag = (position, rank, tag) =>
  request(`${BASE}/${position}/${rank}/tag`, {
    method: 'PUT',
    body: JSON.stringify({ tag }),
  })
```

### Tag picker component — `frontend/src/components/TagPicker.jsx`

A small floating panel that appears anchored to a player name box on
right-click (or long-press on mobile).

**Props:**
```jsx
<TagPicker
  activeTag={player.tag}     // current tag key or ""
  position={{ x, y }}        // anchor coordinates from contextmenu event
  onSelect={fn}              // (tagKey) => void — called with "" to clear
  onClose={fn}               // () => void
/>
```

**Layout:**
```
┌──────────────────────────────────────────┐
│  ❤   🔥   💎   ⚠   ✚   ☠   🚩           │
└──────────────────────────────────────────┘
```

Single row of 7 icon buttons. Active tag gets a highlighted border
(`2px solid var(--accent)`). Inactive tags have transparent border.

**Positioning:** anchored below the right-click point with a small offset.
Clamps to viewport so it never overflows off the bottom or right edge:
```js
const x = Math.min(event.clientX, window.innerWidth - 200)
const y = Math.min(event.clientY + 8, window.innerHeight - 60)
```

**Dismissal:** closes on outside click (mousedown listener on document),
Escape key, or after a selection is made.

**Tag definitions array** (drives the picker render):
```js
const TAGS = [
  { key: 'heart',   label: '❤',  title: 'Love'     },
  { key: 'fire',    label: '🔥', title: 'Breakout'  },
  { key: 'gem',     label: '💎', title: 'Sleeper'   },
  { key: 'warning', label: '⚠', title: 'Risky'     },
  { key: 'cross',   label: '✚',  title: 'Hurt',  className: 'tag-cross' },
  { key: 'skull',   label: '☠', title: 'Avoid'     },
  { key: 'flag',    label: '🚩', title: 'Red flag'  },
]
```

The `tag-cross` class applies `color: #E03030` to render the `✚` in red.

**Select / toggle logic:**
```js
function handleSelect(key) {
  const newTag = key === activeTag ? '' : key  // toggle off if same
  onSelect(newTag)
  onClose()
}
```

### `frontend/src/components/TagPicker.css`

```css
.tag-picker {
  position: fixed;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 8px;
  display: flex;
  gap: 4px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.tag-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  border: 2px solid transparent;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  transition: background 0.1s;
}

.tag-btn:hover {
  background: var(--bg-tertiary);
}

.tag-btn.active {
  border-color: var(--accent);
  background: var(--bg-tertiary);
}

.tag-cross {
  color: #E03030;
  font-size: 16px;
}
```

### `frontend/src/components/PlayerRow.jsx`

#### Right-click handler

```jsx
function handleContextMenu(e) {
  e.preventDefault()
  onTagOpen(player, position, { x: e.clientX, y: e.clientY })
}
```

Add `onContextMenu={handleContextMenu}` to the name button in the war
room return AND the name span in the draft return.

New prop: `onTagOpen` — passed from `TierGroup` → `PositionColumn` →
`WarRoom` → `App`.

#### Tag icon in name box

Left of the name text, inside the name button:

```jsx
{player.tag && (
  <span className={`player-tag tag-${player.tag}`}>
    {TAG_ICONS[player.tag]}
  </span>
)}
<span className="player-name-text">{nameLabel}</span>
{logoEl}
```

`TAG_ICONS` map (defined once at the top of the file or in a shared util):
```js
const TAG_ICONS = {
  heart:   '❤',
  fire:    '🔥',
  gem:     '💎',
  warning: '⚠',
  cross:   '✚',
  skull:   '☠',
  flag:    '🚩',
}
```

#### Tag icon CSS (`PlayerRow.css`)

```css
.player-tag {
  font-size: 13px;
  flex-shrink: 0;
  line-height: 1;
}

.player-tag.tag-cross {
  color: #E03030;
  font-size: 14px;
}
```

The `<span className="player-name-text">` already has `flex: 1; min-width: 0;
overflow: hidden; text-overflow: ellipsis;` — it will compress correctly
when the tag icon occupies space on the left.

### `frontend/src/App.jsx`

#### State

```js
const [tagPicker, setTagPicker] = useState(null)
// { player, position, coords: {x, y} } or null
```

#### Handlers

```js
function handleTagOpen(player, position, coords) {
  setTagPicker({ player, position, coords })
}

async function handleTagSelect(tag) {
  if (!tagPicker) return
  const { player, position } = tagPicker
  setTagPicker(null)
  await setPlayerTag(position, player.position_rank, tag)
  await reloadPosition(position)  // reload just that position's data
}

function handleTagClose() {
  setTagPicker(null)
}
```

#### Render

```jsx
{tagPicker && (
  <TagPicker
    activeTag={tagPicker.player.tag ?? ''}
    position={tagPicker.coords}
    onSelect={handleTagSelect}
    onClose={handleTagClose}
  />
)}
```

Rendered at the App level so it floats above all columns regardless of
which column triggered it.

### Prop threading

`onTagOpen` threads from App → WarRoom → PositionColumn → TierGroup →
PlayerRow. This is the same depth as `onNotesOpen` — follow the same
pattern. `WarRoom.jsx` and the intermediate components simply accept and
pass the prop through.

---

## Draft Mode

The tag picker works identically in Draft Mode. Right-click on a player
name span opens the picker. Tags are visible on all players regardless
of draft status — a tagged player with `status-mine` shows the tag icon
on the green background, same as war room.

The tag picker is **not** hidden in Draft Mode. Being able to tag a player
as `✚` (hurt) during a live draft is useful.

---

## Files to Change

```
# Backend
backend/utils/rankings.py          # VALID_TAGS + set_player_tag() + .setdefault("tag","")
backend/routers/rankings.py        # TagRequest model + PUT /{position}/{rank}/tag

# Frontend (new)
frontend/src/components/TagPicker.jsx
frontend/src/components/TagPicker.css

# Frontend (modified)
frontend/src/api/rankings.js       # setPlayerTag()
frontend/src/components/PlayerRow.jsx  # tag icon display + onContextMenu
frontend/src/components/PlayerRow.css  # .player-tag styles
frontend/src/App.jsx               # tagPicker state + handlers + TagPicker render
frontend/src/components/WarRoom.jsx    # pass onTagOpen through
frontend/src/components/PositionColumn.jsx  # pass onTagOpen through
frontend/src/components/TierGroup.jsx       # pass onTagOpen through

# Tests
tests/test_rankings.py             # set_player_tag tests
```

---

## New Tests (`tests/test_rankings.py`)

```
test_set_player_tag_sets_tag        — tag field updated on correct player
test_set_player_tag_clears_tag      — tag="" clears the field
test_set_player_tag_invalid_tag     — ValueError for unknown tag key
test_set_player_tag_not_found       — ValueError for nonexistent player
test_set_player_tag_no_mutation     — original profile dict unchanged
test_get_position_players_defaults_tag  — missing tag field defaults to ""
```

6 new tests. All use the existing `sample_profile` fixture.

---

## Acceptance Criteria

- [ ] Right-clicking a player name box opens the tag picker
- [ ] Picker shows 7 icons in a single row, anchored near the click point
- [ ] `✚` (cross) renders in red `#E03030`, not as emoji
- [ ] Clicking an icon tags the player — icon appears left of name text in name box
- [ ] Clicking the active icon again clears the tag
- [ ] Clicking a different icon replaces the tag
- [ ] Picker closes on outside click, Escape, and after selection
- [ ] Tags persist to JSON via save (same as notes — unsaved indicator appears)
- [ ] Tags survive page reload
- [ ] Tags visible in both War Room and Draft Mode
- [ ] Long player names still truncate with ellipsis (tag icon + logo both fit)
- [ ] Picker clamps to viewport — never overflows right or bottom edge
- [ ] `pytest tests/ -q` — 76 existing + 6 new = 82 passing
- [ ] `ruff check backend/ tests/` — zero errors
- [ ] `npx vite build` — 0 errors

---

## Non-Goals

- Multiple tags per player — single tag only (by design)
- Custom user-defined tags — fixed set only
- Tag filtering / filtering the board by tag — future consideration
- Tag display in search results dropdown — future consideration
- Any changes to the notes dialog
