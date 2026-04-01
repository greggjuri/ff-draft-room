# PRP-06: Profile Management

**Created**: 2026-03-31
**Initial**: `initials/06-init-profile-management.md`
**Status**: Ready

---

## Overview

### Problem Statement
The War Room only supports a single `default.json` profile. Users cannot save snapshots of their rankings, load previous versions, or reset to a known baseline. There is no way to compare approaches (e.g., "zero RB" vs "hero RB" boards).

### Proposed Solution
Add Save As, Load, Reset, and Set as Default operations. Named profiles are stored as individual JSON files in `data/rankings/`. A user-defined seed baseline (`seed.json`) allows resetting to a known state. Five new backend endpoints + four new frontend dialogs.

### Success Criteria
- [ ] Save As: dialog saves named profile, header shows new name
- [ ] Save As: saved profile appears in Load dialog
- [ ] Load: dialog lists all named profiles, empty state if none
- [ ] Load: selecting a profile reloads all 4 columns
- [ ] Load: warns before loading if unsaved changes exist
- [ ] Reset: confirm dialog, restores from `seed.json` or CSV fallback
- [ ] Set as Default: confirm dialog, writes `seed.json`
- [ ] Set as Default: subsequent Reset uses `seed.json`
- [ ] Profile name displayed in header, updates after Save As / Load
- [ ] All 4 new dialogs use native `<dialog>` with useEffect pattern
- [ ] `pytest tests/` → all tests pass (35 existing + 14 new)
- [ ] `ruff check backend/ tests/` → zero errors
- [ ] All files under 500 lines

---

## Context

### Related Documentation
- `docs/DECISIONS.md` — ADR-002 (JSON persistence), ADR-006 (React frontend)
- `docs/PLANNING.md` — Data model, API design
- `CLAUDE.md` — API routes, design system

### Dependencies
- **Required**: PRP-04 (backend) ✅, PRP-05 (frontend) ✅
- **Optional**: None

### Files to Create
```
frontend/src/components/SaveAsDialog.jsx
frontend/src/components/LoadDialog.jsx
frontend/src/components/ResetConfirmDialog.jsx
frontend/src/components/SetDefaultConfirmDialog.jsx
tests/test_profile_management.py
```

### Files to Modify
```
backend/routers/rankings.py       # 5 new endpoints + 2 Pydantic models
backend/utils/rankings.py         # New utility functions for profile ops
frontend/src/api/rankings.js      # 5 new API functions
frontend/src/App.jsx              # New state + handlers
frontend/src/components/WarRoom.jsx    # Header toolbar buttons
frontend/src/components/WarRoom.css    # New button styles
```

---

## Technical Specification

### Storage Model

```
data/rankings/
  default.json       ← active profile (always present)
  seed.json          ← custom reset baseline (optional)
  {name}.json        ← named profile snapshots
```

- `default.json` is the active working copy, loaded on startup
- `seed.json` is set by user via Set as Default — used by Reset
- Named profiles are independent snapshots created via Save As

### New Backend Utility Functions (`backend/utils/rankings.py`)

```python
RESERVED_NAMES: set[str] = {"default", "seed"}

def list_profiles(rankings_dir: Path | None = None) -> list[str]:
    """Return sorted list of profile names (excludes default.json and seed.json)."""

def save_profile_as(profile: dict, name: str, rankings_dir: Path | None = None) -> dict:
    """Save profile under a named file. Returns {saved, name, filename}."""

def load_profile(name: str, rankings_dir: Path | None = None) -> dict:
    """Load a named profile from disk. Raises FileNotFoundError if missing."""

def save_seed(profile: dict, rankings_dir: Path | None = None) -> bool:
    """Save profile as seed.json baseline. Returns success bool."""

def load_seed_or_csv(df: pd.DataFrame, rankings_dir: Path | None = None) -> dict:
    """Load seed.json if exists, otherwise seed from CSV data."""
```

### New Pydantic Models (`backend/routers/rankings.py`)

```python
class SaveAsRequest(BaseModel):
    name: str

class LoadRequest(BaseModel):
    name: str
```

### New API Endpoints

| Method | Path | Request Body | Response | Errors |
|--------|------|-------------|----------|--------|
| GET | `/api/rankings/profiles` | — | `list[str]` | — |
| POST | `/api/rankings/save-as` | `SaveAsRequest` | `{saved, name, filename}` | 400 invalid name |
| POST | `/api/rankings/load` | `LoadRequest` | Full profile dict | 404 not found, 400 reserved |
| POST | `/api/rankings/set-default` | — | `{saved: true}` | 500 on disk error |
| POST | `/api/rankings/reset` | — | Full profile dict | 500 if no data |

### New Frontend State (`App.jsx`)

```js
const [profileName, setProfileName] = useState('2026 Draft')
const [saveAsDialog, setSaveAsDialog] = useState(false)
const [loadDialog, setLoadDialog] = useState(false)
const [resetDialog, setResetDialog] = useState(false)
const [setDefaultDialog, setDefaultDialog] = useState(false)
```

### New API Functions (`rankings.js`)

```js
export const getProfiles = () => request(`${BASE}/profiles`)
export const saveAs = (name) => request(`${BASE}/save-as`, { method: 'POST', ... })
export const loadProfile = (name) => request(`${BASE}/load`, { method: 'POST', ... })
export const resetRankings = () => request(`${BASE}/reset`, { method: 'POST' })
export const setDefaultSeed = () => request(`${BASE}/set-default`, { method: 'POST' })
```

---

## Implementation Steps

### Step 1: Backend Utility Functions
**Files**: `backend/utils/rankings.py`

Add to existing file:
1. `RESERVED_NAMES` constant
2. `list_profiles()` — glob `*.json`, exclude reserved, extract display names
3. `save_profile_as()` — sanitize name, write file, return metadata
4. `load_profile()` — read named JSON, raise `FileNotFoundError` if missing
5. `save_seed()` — write `seed.json`
6. `load_seed_or_csv()` — try `seed.json`, fall back to `seed_rankings(df)`

Name sanitization: strip whitespace, replace spaces with underscores, reject `/`, `\`, `..`.

**Validation**:
```bash
ruff check backend/utils/rankings.py
```
- [ ] No lint errors, file under 500 lines

---

### Step 2: Backend Unit Tests
**Files**: `tests/test_profile_management.py`

14 tests using `tmp_path`:
- `test_get_profiles_empty` — no files → `[]`
- `test_get_profiles_lists_files` — named profiles listed
- `test_get_profiles_excludes_reserved` — `default.json`, `seed.json` excluded
- `test_save_as_creates_file` — file written
- `test_save_as_sanitizes_name` — spaces → underscores
- `test_save_as_rejects_empty_name` — raises ValueError
- `test_save_as_rejects_path_traversal` — `"../evil"` rejected
- `test_load_profile_loads_file` — returns parsed profile
- `test_load_profile_copies_to_default` — `default.json` updated
- `test_load_profile_404_if_missing` — raises FileNotFoundError
- `test_load_rejects_reserved_names` — `"default"`, `"seed"` rejected
- `test_set_default_writes_seed_json` — `seed.json` created
- `test_reset_uses_seed_json_if_exists` — returns seed content
- `test_reset_falls_back_to_csv` — no seed → CSV seed

**Validation**:
```bash
pytest tests/test_profile_management.py -v
```
- [ ] All 14 tests pass

---

### Step 3: Backend Router Endpoints
**Files**: `backend/routers/rankings.py`

Add 5 new endpoints (must be registered BEFORE `/{position}` catch-all routes):
1. `GET /profiles` — call `list_profiles()`
2. `POST /save-as` — validate, call `save_profile_as()`, update in-memory
3. `POST /load` — validate not reserved, call `load_profile()`, copy to default, update in-memory
4. `POST /set-default` — call `save_seed()`
5. `POST /reset` — call `load_seed_or_csv()`, save to default, update in-memory

**IMPORTANT**: These routes must appear before `/{position}` to avoid FastAPI matching `profiles`, `save-as`, `load`, etc. as position path params.

Add Pydantic models: `SaveAsRequest`, `LoadRequest`.

**Validation**:
```bash
ruff check backend/routers/rankings.py
uvicorn backend.main:app --reload  # curl test each endpoint
```
- [ ] No lint errors, file under 500 lines
- [ ] All 5 endpoints respond correctly

---

### Step 4: Frontend API Layer
**Files**: `frontend/src/api/rankings.js`

Add 5 new functions:
- `getProfiles()`
- `saveAs(name)`
- `loadProfile(name)`
- `resetRankings()`
- `setDefaultSeed()`

**Validation**:
- [ ] File exports all functions

---

### Step 5: Frontend Dialogs
**Files**: 4 new dialog components

**`SaveAsDialog.jsx`**:
- Name input, auto-focused
- Inline validation (empty name)
- API error display (from backend)
- Save / Cancel buttons

**`LoadDialog.jsx`**:
- Fetches profile list on open
- Renders list with [Load] buttons
- Empty state: "No profiles saved yet."
- Dirty warning before loading
- Close button

**`ResetConfirmDialog.jsx`**:
- Confirm message explaining seed.json vs CSV fallback
- "This cannot be undone."
- Reset (danger) / Cancel buttons

**`SetDefaultConfirmDialog.jsx`**:
- Confirm message
- Set as Default / Cancel buttons

All use `useEffect` with `isOpen` prop for `showModal()`/`close()`.

**Validation**:
```bash
cd frontend && npx vite build
```
- [ ] Builds without errors

---

### Step 6: Frontend Integration — App.jsx + WarRoom
**Files**: `frontend/src/App.jsx`, `frontend/src/components/WarRoom.jsx`, `WarRoom.css`

**App.jsx**:
- Add `profileName` state, initialized from loaded profile's `name` field
- Add dialog open/close states for all 4 new dialogs
- Add handlers: `handleSaveAs`, `handleLoad`, `handleReset`, `handleSetDefault`
- `handleLoad` and `handleReset` must reload all 4 positions after profile change

**WarRoom.jsx**:
- Add 4 buttons to header toolbar: SAVE AS, LOAD, RESET, ★ SET DEFAULT
- Show `profileName` in header between title and unsaved indicator
- Render 4 new dialogs conditionally

**WarRoom.css**:
- `.toolbar-btn` — secondary button style (muted border)
- `.toolbar-btn-danger` — red border, red hover
- `.profile-name` — muted text styling

**Validation**:
```bash
cd frontend && npx vite build
```
- [ ] Builds without errors
- [ ] All buttons visible in header

---

### Step 7: Final Integration Check
**Commands**:
```bash
pytest tests/ --cov=backend --cov-report=term-missing
ruff check backend/ tests/
cd frontend && npx vite build
# Manual: start both servers, test all flows
```

**Validation**:
- [ ] All tests pass (35 existing + 14 new = 49+)
- [ ] Zero lint errors
- [ ] Frontend builds
- [ ] Full manual test of all profile operations
- [ ] All files under 500 lines
- [ ] Commit and push

---

## Testing Requirements

### Backend Unit Tests (`tests/test_profile_management.py`)
```
test_get_profiles_empty               — no files → []
test_get_profiles_lists_files         — returns names
test_get_profiles_excludes_reserved   — default/seed excluded
test_save_as_creates_file             — file written
test_save_as_sanitizes_name           — spaces → underscores
test_save_as_rejects_empty_name       — raises ValueError
test_save_as_rejects_path_traversal   — rejects ../
test_load_profile_loads_file          — returns profile
test_load_profile_copies_to_default   — default.json updated
test_load_profile_404_if_missing      — FileNotFoundError
test_load_rejects_reserved_names      — default/seed → ValueError
test_set_default_writes_seed_json     — seed.json created
test_reset_uses_seed_json_if_exists   — returns seed content
test_reset_falls_back_to_csv          — CSV fallback works
```

### Frontend Manual Tests
```
Save As:
  - Click SAVE AS → dialog opens, input focused
  - Enter name, Save → header shows new name, dirty cleared
  - Empty name → inline error
  - Profile file appears in data/rankings/

Load:
  - Click LOAD → dialog lists saved profiles
  - No profiles → "No profiles saved yet."
  - Click Load on a profile → columns reload with that data
  - Load while dirty → warning shown

Reset:
  - Click RESET → confirm dialog
  - Reset with seed.json → restores baseline
  - Reset without seed.json → re-seeds from CSV
  - Cancel → no change

Set as Default:
  - Click ★ SET DEFAULT → confirm dialog
  - Confirm → seed.json written
  - Subsequent Reset → uses seed.json
```

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Click SAVE AS | Dialog opens, input focused | ☐ |
| 2 | Enter "Mock Draft 1", Save | Header shows "Mock Draft 1", file created | ☐ |
| 3 | Click LOAD | Dialog shows "Mock Draft 1" | ☐ |
| 4 | Make changes, click LOAD | Warning about unsaved changes | ☐ |
| 5 | Load "Mock Draft 1" | Columns reload with saved data | ☐ |
| 6 | Click ★ SET DEFAULT | Confirm dialog | ☐ |
| 7 | Confirm Set Default | seed.json created in data/rankings/ | ☐ |
| 8 | Make changes, click RESET | Confirm dialog | ☐ |
| 9 | Confirm Reset | Rankings restored to seed.json baseline | ☐ |
| 10 | Delete seed.json manually, RESET | Re-seeds from CSV data | ☐ |
| 11 | `pytest tests/ -v` | All tests pass | ☐ |
| 12 | `ruff check backend/ tests/` | Zero errors | ☐ |

---

## Error Handling

| Error | Cause | Behavior |
|-------|-------|----------|
| Empty profile name | User submits blank | Inline error in dialog |
| Path traversal in name | `../` or `\` chars | 400: "Invalid profile name" |
| Reserved name (default/seed) | User tries to load reserved | 400: blocked |
| Profile file not found | File deleted externally | 404: "Profile not found" |
| Disk write failure | Permissions/space | 500: "Save failed" |
| No seed + no CSV data | Both missing on reset | 500: "Reset failed" |
| Load while dirty | Unsaved changes exist | Confirm dialog before proceeding |

---

## Open Questions

None — all resolved in the init spec.

---

## Rollback Plan

1. Revert backend changes: `git revert <commit>`
2. Remove new test file: `tests/test_profile_management.py`
3. Remove new frontend components: `SaveAsDialog.jsx`, `LoadDialog.jsx`, `ResetConfirmDialog.jsx`, `SetDefaultConfirmDialog.jsx`
4. Named profile JSON files in `data/rankings/` are harmless — can leave or delete

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Every endpoint, dialog, and validation rule specified |
| Feasibility | 10 | Standard CRUD operations on JSON files, no exotic requirements |
| Completeness | 9 | All endpoints, tests, and UI specified. Minor: no delete-profile yet (explicitly out of scope) |
| Alignment | 10 | Consistent with ADR-002 (JSON files), ADR-006 (React) |
| **Average** | **9.75** | |

---

## Notes

- **Route ordering**: The 5 new routes (`/profiles`, `/save-as`, `/load`, `/set-default`, `/reset`) MUST be registered before `/{position}` to avoid FastAPI matching them as position params. This is critical.
- **File size**: `rankings.py` (router) is currently 196 lines. Adding ~80 lines for 5 endpoints keeps it under 300 — well within limit. `rankings.py` (utils) is 266 lines, adding ~60 lines keeps it under 330.
- **Name sanitization**: Strip, replace spaces with underscores, reject `/`, `\`, `..`. Display name stored in profile's `"name"` field, filename is sanitized version.
- **Load copies to default**: When loading a named profile, it becomes the active `default.json`. This ensures the next startup loads the last-used profile.
