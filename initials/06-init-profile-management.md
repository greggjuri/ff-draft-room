# 06-init-profile-management.md — Profile Management

## Feature Summary
Add Save As, Load, Reset, and Set as Default to the War Room header toolbar.
Profiles are named JSON files in `data/rankings/`. Reset restores from a user-defined
seed baseline (`seed.json`) if one exists, otherwise falls back to CSV data.
Load shows a modal listing all saved profiles.

## Status
- [x] Open questions resolved
- [x] Ready for PRP generation

---

## Requirements

### 1. Storage Model

```
data/rankings/
  default.json       ← active profile (always present)
  seed.json          ← custom reset baseline (optional, set by user)
  {name}.json        ← any named profiles created via Save As
```

- `seed.json` is never shown in the Load profile picker
- `default.json` is the active working profile — always loaded on startup
- Named profiles are independent snapshots — loading one copies it into `default.json`

### 2. Backend Changes (`backend/routers/rankings.py`)

**New endpoints:**

```
GET  /api/rankings/profiles
```
Returns list of saved profile names (excludes `default.json` and `seed.json`):
```json
["Mock Draft 1", "Pre-FA Rankings", "Final Board"]
```
Sorted alphabetically. Empty list `[]` if none exist.

```
POST /api/rankings/save-as
Body: { "name": str }
```
- Validates: name not empty, no path traversal characters (`/`, `\`, `..`)
- Sanitizes: strip whitespace, replace spaces with underscores for filename
- Saves current in-memory profile to `data/rankings/{sanitized_name}.json`
- Updates profile `"name"` field to the provided name
- Switches active profile to this new one (updates `_profile` in memory)
- Returns `{"saved": true, "name": "Mock Draft 1", "filename": "Mock_Draft_1.json"}`
- 400 if name is empty or invalid

```
POST /api/rankings/load
Body: { "name": str }
```
- Loads `data/rankings/{name}.json` into memory as active profile
- Copies loaded profile to `data/rankings/default.json`
- Returns full loaded profile
- 404 if file not found
- 400 if name is `"default"` or `"seed"` (reserved names)

```
POST /api/rankings/set-default
```
- Saves current in-memory profile to `data/rankings/seed.json`
- This becomes the baseline for future resets
- Returns `{"saved": true}`

```
POST /api/rankings/reset
```
- If `data/rankings/seed.json` exists: load it as the active profile,
  copy to `default.json`, return it
- If not: re-seed from CSV data (existing seed logic), save to `default.json`, return it
- Always returns full profile after reset
- Never fails silently — 500 if both seed.json missing and CSV data unavailable

**Note**: The existing `POST /api/rankings/seed` endpoint remains unchanged
(nuclear CSV re-seed, used internally and for testing).

### 3. Frontend Changes

#### 3a. Header Toolbar (`WarRoom.jsx`, `WarRoom.css`)

Current header: `🏈 WAR ROOM` | `● UNSAVED` | `[SAVE]`

New header: `🏈 WAR ROOM` | `● UNSAVED` | `[SAVE] [SAVE AS] [LOAD] [RESET] [SET AS DEFAULT]`

Button styling:
- `[SAVE]` — primary style (bordered in accent color, existing style)
- `[SAVE AS]`, `[LOAD]` — secondary style (muted border, less prominent)
- `[RESET]` — danger style (muted red border `#8B2020`, red on hover)
- `[SET AS DEFAULT]` — secondary style with a ★ icon prefix

Profile name display: show current profile name in muted text between title and unsaved indicator:
```
🏈 WAR ROOM   Mock Draft 1   ● UNSAVED   [SAVE] [SAVE AS] [LOAD] [RESET] [★ SET DEFAULT]
```

#### 3b. Save As Dialog (`SaveAsDialog.jsx`)

Native `<dialog>`:
```
Save Rankings As

Profile name: [________________________]

             [Save]  [Cancel]
```
- Text input, auto-focused on open
- Inline validation: empty name → `"Profile name is required"`
- On Save: POST /api/rankings/save-as → close dialog, update profile name in header, clear dirty
- On Cancel: close, no change

#### 3c. Load Dialog (`LoadDialog.jsx`)

Native `<dialog>`:
```
Load Profile

  Mock Draft 1          [Load]
  Pre-FA Rankings       [Load]
  Final Board           [Load]

  No profiles saved yet.   ← shown if list empty

             [Close]
```
- On open: GET /api/rankings/profiles → render list
- Each profile: name + `[Load]` button
- On Load click: confirm if dirty (`"Unsaved changes will be lost. Continue?"`)
  then POST /api/rankings/load → reload all 4 positions, close dialog, clear dirty
- Loading state: show spinner while fetching list
- On Close: dismiss, no change

#### 3d. Reset Confirm Dialog (`ResetConfirmDialog.jsx`)

Native `<dialog>`:
```
Reset Rankings

Reset to your saved default baseline?
If no baseline is set, rankings will be
re-seeded from 2025 CSV data.

This cannot be undone.

        [Reset]   [Cancel]
```
- `[Reset]` styled in danger red
- On Reset: POST /api/rankings/reset → reload all 4 positions, close, clear dirty
- On Cancel: close, no change

#### 3e. Set Default Confirm Dialog (`SetDefaultConfirmDialog.jsx`)

Native `<dialog>`:
```
Set as Default Baseline

Save current rankings as the baseline
for future resets?

        [Set as Default]   [Cancel]
```
- On confirm: POST /api/rankings/set-default → close, show brief success toast
- On Cancel: close, no change

#### 3f. State Updates (`App.jsx`)

New state:
```js
const [profileName, setProfileName] = useState('2026 Draft')
const [profiles, setProfiles] = useState([])
```

New handlers:
```js
const handleSaveAs = async (name) => { ... }   // POST save-as, update profileName
const handleLoad = async (name) => { ... }      // POST load, reload all positions
const handleReset = async () => { ... }         // POST reset, reload all positions
const handleSetDefault = async () => { ... }    // POST set-default
const fetchProfiles = async () => { ... }       // GET profiles, called when Load opens
```

#### 3g. API Layer (`src/api/rankings.js`)

Add:
```js
export const getProfiles = () =>
  fetch('/api/rankings/profiles').then(r => r.json())

export const saveAs = (name) =>
  fetch('/api/rankings/save-as', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  }).then(r => r.json())

export const loadProfile = (name) =>
  fetch('/api/rankings/load', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  }).then(r => r.json())

export const resetRankings = () =>
  fetch('/api/rankings/reset', { method: 'POST' }).then(r => r.json())

export const setDefaultSeed = () =>
  fetch('/api/rankings/set-default', { method: 'POST' }).then(r => r.json())
```

---

## Success Criteria

1. **Save As**: dialog opens, name input validates, saves to named file, header shows new name
2. **Save As**: saved profile appears in Load dialog on next open
3. **Load**: dialog lists all named profiles, empty state shown if none
4. **Load**: selecting a profile reloads all 4 columns with that profile's data
5. **Load**: warns before loading if there are unsaved changes
6. **Reset**: confirm dialog shown before reset
7. **Reset**: if `seed.json` exists → restores to it; if not → re-seeds from CSV
8. **Set as Default**: confirm dialog shown, `seed.json` written after confirm
9. **Set as Default**: subsequent Reset uses `seed.json` not CSV data
10. **Profile name**: displayed in header, updates after Save As and Load
11. All 4 new dialogs use native `<dialog>` with proper useEffect open/close pattern
12. `pytest tests/ -v` → all 35 tests still pass
13. `ruff check backend/ tests/` → zero errors

---

## Backend Test Requirements (`tests/test_profile_management.py`)

New test file:

- `test_get_profiles_empty`: no named profiles → returns `[]`
- `test_get_profiles_lists_files`: named profiles present → returns their names
- `test_get_profiles_excludes_reserved`: `default.json` and `seed.json` not listed
- `test_save_as_creates_file`: file written to `data/rankings/{name}.json`
- `test_save_as_sanitizes_name`: spaces → underscores in filename
- `test_save_as_rejects_empty_name`: 400 response
- `test_save_as_rejects_path_traversal`: `"../evil"` → 400 response
- `test_load_profile_loads_file`: loads named profile into memory
- `test_load_profile_copies_to_default`: `default.json` updated after load
- `test_load_profile_404_if_missing`: 404 for nonexistent profile
- `test_load_rejects_reserved_names`: `"default"` and `"seed"` → 400
- `test_set_default_writes_seed_json`: `seed.json` created with current profile
- `test_reset_uses_seed_json_if_exists`: reset returns seed.json content
- `test_reset_falls_back_to_csv`: no seed.json → re-seeds from CSV

All tests use `tmp_path` fixture — no writes to real `data/rankings/`.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Save As — empty name | Inline error: `"Profile name is required"` |
| Save As — invalid chars | Inline error: `"Invalid profile name"` |
| Load — profile file missing | Toast: `"Profile not found"` |
| Load — dirty state | Confirm: `"Unsaved changes will be lost. Continue?"` |
| Reset — no seed, no CSV | 500 → toast: `"Reset failed: no data available"` |
| Any API call fails | Toast error message, state unchanged |

---

## Open Questions

*All resolved.*

1. ~~Where are profiles stored?~~ → `data/rankings/{name}.json`
2. ~~What does Reset restore to?~~ → `seed.json` if set, CSV data if not
3. ~~Load UI?~~ → Modal with list of named profiles, `[Load]` per item
4. ~~Reserved filenames?~~ → `default` and `seed` blocked from Save As and Load

---

## Out of Scope for This Init

- Rename or delete saved profiles — future
- Profile metadata (date created, notes) — future
- K and D/ST columns — `07-init-k-dst.md`
- Export to CSV — Phase 1c
