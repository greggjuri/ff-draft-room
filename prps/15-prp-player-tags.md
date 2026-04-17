# PRP-015: Player Tag Icons

**Created**: 2026-04-17
**Initial**: `initials/15-init-player-tags.md`
**Status**: Complete

---

## Overview

### Problem Statement
Players support free-text notes, but opening the notes dialog is needed
to see any signal. There's no way to get instant visual indicators during
draft prep or on draft day.

### Proposed Solution
Add a structured `tag` field to each player — a short key mapping to a
visual icon (heart, fire, gem, warning, cross, skull, flag). Tags display
as icons left of the player name inside the name box. Right-click opens a
floating picker panel to set/clear tags. Works in both War Room and Draft Mode.

### Success Criteria
- [ ] Right-click player name → tag picker opens near click point
- [ ] 7 icons in a single row; `cross` renders in CSS red, not emoji
- [ ] Click icon → tags the player, icon appears left of name text
- [ ] Click active icon → clears the tag
- [ ] Picker closes on outside click, Escape, and after selection
- [ ] Tags persist via save, survive reload
- [ ] Tags visible in both War Room and Draft Mode
- [ ] Long names truncate with ellipsis (tag icon + logo both fit)
- [ ] Picker clamps to viewport
- [ ] Existing profiles without `tag` field default to `""` on read
- [ ] `pytest tests/ -q` — 76 existing + 6 new = 82 passing
- [ ] `ruff check backend/ tests/` — zero errors
- [ ] `cd frontend && npx vite build` — no errors
- [ ] No file exceeds 500 lines

---

## Context

### Related Documentation
- `initials/15-init-player-tags.md` — Full spec with tag set, data model, component design
- Mirrors `notes` pattern: new field, utility function, `PUT /{position}/{rank}/tag`

### Dependencies
- **Required**: PRP-012 (team logos — current PlayerRow shape with name text + logo)

### Files to Create/Modify
```
# NEW
frontend/src/components/TagPicker.jsx      # Floating tag picker panel
frontend/src/components/TagPicker.css      # Picker styles

# MODIFIED — Backend
backend/utils/rankings.py                  # VALID_TAGS, set_player_tag(), setdefault in get_position_players
backend/routers/rankings.py                # TagRequest + PUT /{position}/{rank}/tag

# MODIFIED — Frontend
frontend/src/api/rankings.js               # setPlayerTag()
frontend/src/components/PlayerRow.jsx      # Tag icon display + onContextMenu
frontend/src/components/PlayerRow.css      # .player-tag styles
frontend/src/components/TierGroup.jsx      # Pass onTagOpen through
frontend/src/components/PositionColumn.jsx # Pass onTagOpen through
frontend/src/components/WarRoom.jsx        # Pass onTagOpen through
frontend/src/App.jsx                       # tagPicker state + handlers + render

# MODIFIED — Tests
tests/test_rankings.py                     # 6 new tests
```

---

## Technical Specification

### Tag Set
| Key | Display | Meaning |
|-----|---------|---------|
| `heart` | ❤ | Priority target |
| `fire` | 🔥 | Breakout candidate |
| `gem` | 💎 | Late round sleeper |
| `warning` | ⚠ | Risky — injury/situation |
| `cross` | ✚ (CSS red) | Currently injured |
| `skull` | ☠ | Avoid |
| `flag` | 🚩 | Red flag — off-field concern |

### Backend — `set_player_tag()` in `backend/utils/rankings.py`

```python
VALID_TAGS: frozenset[str] = frozenset(
    {"", "heart", "fire", "gem", "warning", "cross", "skull", "flag"}
)

def set_player_tag(profile, position, position_rank, tag) -> dict:
```

Same pattern as `set_player_tier`: deepcopy, find player, update field,
return new profile. Validates tag is in `VALID_TAGS`.

### Backend — `get_position_players()` default

Add `p.setdefault("tag", "")` in `get_position_players()` so existing
profiles without the field work without migration.

### Backend — seed and add_player

Add `"tag": ""` to player dicts in `seed_rankings()` and `add_player()`.

### API — `PUT /api/rankings/{position}/{rank}/tag`

`TagRequest(tag: str)`. Validates position, rank, calls `set_player_tag`.
Returns updated player dict (same as `update_notes`).

### Frontend — `TagPicker.jsx`

Fixed-position floating panel, 7 icon buttons in a row. Active tag gets
accent border. Toggle logic: click same tag → clear, click different → set.
Closes on outside click, Escape, selection.

### Frontend — `PlayerRow.jsx`

- Tag icon rendered left of name text inside the name box
- `onContextMenu` handler opens tag picker via `onTagOpen` prop
- `TAG_ICONS` map at top of file for key → display character

### Prop Threading

`onTagOpen` threads: App → WarRoom → PositionColumn → TierGroup → PlayerRow.
Same pattern as `onNotesOpen`.

---

## Implementation Steps

### Step 1: Backend — `set_player_tag()` + defaults + tests
**Files**: `backend/utils/rankings.py`, `tests/test_rankings.py`

1. Add `VALID_TAGS` frozenset
2. Add `set_player_tag()` function
3. Add `p.setdefault("tag", "")` in `get_position_players()`
4. Add `"tag": ""` to player dicts in `seed_rankings()` and `add_player()`
5. Add 6 tests

**Validation:**
```bash
pytest tests/test_rankings.py -v
ruff check backend/utils/rankings.py
```
- [ ] All tests pass
- [ ] No lint errors

---

### Step 2: Backend — API endpoint
**Files**: `backend/routers/rankings.py`

Add `TagRequest` model and `PUT /{position}/{rank}/tag` endpoint.

**Validation:**
```bash
ruff check backend/routers/rankings.py
pytest tests/ -q
```
- [ ] Lint clean
- [ ] All tests pass

---

### Step 3: Frontend — API function
**Files**: `frontend/src/api/rankings.js`

Add `setPlayerTag(position, rank, tag)`.

---

### Step 4: Frontend — TagPicker component
**Files**: `frontend/src/components/TagPicker.jsx`, `frontend/src/components/TagPicker.css`

Floating picker panel with 7 icon buttons, outside-click dismissal,
viewport clamping.

---

### Step 5: Frontend — PlayerRow tag icon + context menu
**Files**: `frontend/src/components/PlayerRow.jsx`, `frontend/src/components/PlayerRow.css`

1. Add `TAG_ICONS` map
2. Render tag icon left of name text in both returns
3. Add `onContextMenu` handler calling `onTagOpen`
4. Accept `onTagOpen` prop
5. Add `.player-tag` CSS

---

### Step 6: Frontend — Wire through components + App
**Files**: `frontend/src/components/TierGroup.jsx`,
`frontend/src/components/PositionColumn.jsx`,
`frontend/src/components/WarRoom.jsx`,
`frontend/src/App.jsx`

1. Thread `onTagOpen` through TierGroup → PositionColumn → WarRoom → App
2. App: `tagPicker` state, `handleTagOpen`, `handleTagSelect`, `handleTagClose`
3. App: import `setPlayerTag`, render `<TagPicker>` when open
4. App: after tag select, reload position data to get updated player

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds

---

### Step 7: Final integration check
```bash
pytest tests/ --cov=backend
ruff check backend/ tests/
cd frontend && npx vite build
```
- [ ] 82 tests pass
- [ ] Lint clean
- [ ] Frontend builds
- [ ] No file over 500 lines

---

## Testing Requirements

### Unit Tests — `tests/test_rankings.py` (additions)
```
test_set_player_tag_sets_tag            — tag updated on correct player
test_set_player_tag_clears_tag          — tag="" clears the field
test_set_player_tag_invalid_tag         — ValueError for unknown key
test_set_player_tag_not_found           — ValueError for nonexistent player
test_set_player_tag_no_mutation         — original profile unchanged
test_get_position_players_defaults_tag  — missing tag field defaults to ""
```

### Manual Browser Tests
- [ ] Right-click player name → picker appears near cursor
- [ ] Picker shows 7 icons, ✚ in red
- [ ] Click heart → ❤ appears left of name in name box
- [ ] Click heart again → cleared
- [ ] Click fire → replaces heart with 🔥
- [ ] Outside click / Escape closes picker
- [ ] Tag visible in Draft Mode on green/purple backgrounds
- [ ] Long name with tag + logo → name truncates, all three fit
- [ ] Save → reload → tag persists
- [ ] Unsaved indicator after tagging

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | 82 tests pass | ☐ |
| 2 | `ruff check backend/ tests/` | Zero errors | ☐ |
| 3 | `cd frontend && npx vite build` | Build succeeds | ☐ |
| 4 | Start dev servers | Both start | ☐ |
| 5 | Right-click a QB player | Picker appears | ☐ |
| 6 | Click ❤ | Heart icon in name box, unsaved indicator | ☐ |
| 7 | Right-click same player, click ❤ | Tag cleared | ☐ |
| 8 | Right-click, click 🔥 | Fire icon replaces | ☐ |
| 9 | Save → reload page | Tag persists | ☐ |
| 10 | Switch to Draft Mode | Tag visible | ☐ |
| 11 | Right-click in Draft Mode | Picker works | ☐ |
| 12 | Picker near bottom of screen | Clamps to viewport | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| 400 invalid tag | Unknown tag key | HTTPException, should not happen from picker |
| 404 player not found | Race condition | Error banner |
| Missing `tag` field on old profiles | Pre-PRP-015 data | `setdefault("tag", "")` in `get_position_players` |

---

## Open Questions

None.

---

## Rollback Plan

```bash
git revert <commit>
pytest tests/ -q
cd frontend && npx vite build
```

Additive feature — new function, new endpoint, new component. Revert is clean.
Old profiles without `tag` field continue to work (the `setdefault` is
only needed while this feature exists).

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Exact tag set, data model, component design, CSS all specified |
| Feasibility | 10 | Standard context menu + floating panel + one field update |
| Completeness | 10 | All files, 6 tests, backward compat for old profiles |
| Alignment | 10 | Mirrors existing notes pattern, no ADR impact |
| **Average** | **10** | Ready for execution |

---

## Notes

### Prop Threading Depth
`onTagOpen` threads 4 levels deep (App → WarRoom → PositionColumn →
TierGroup → PlayerRow). This matches `onNotesOpen` exactly. Follow the
same pattern — accept and pass through at each level.

### File Size Check
- `backend/utils/rankings.py`: ~447 lines → ~470 after (under 500)
- `backend/routers/rankings.py`: ~354 lines → ~380 after (under 500)
- `frontend/src/components/PlayerRow.jsx`: ~97 lines → ~120 after
- `frontend/src/App.jsx`: ~328 lines → ~360 after
- `tests/test_rankings.py`: ~372 lines → ~420 after
All safe.
