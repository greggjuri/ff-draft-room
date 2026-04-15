# PRP-014: Profile Rename and Delete

**Created**: 2026-04-15
**Initial**: `initials/14-init-profile-rename-delete.md`
**Status**: Complete

---

## Overview

### Problem Statement
Profiles can be created via Save As and loaded, but there is no way to
rename or delete them. Unused profiles accumulate, and typos in profile
names are permanent.

### Proposed Solution
Add `[Rename]` and `[Delete]` inline actions to each row in the existing
Load dialog. Rename switches to an inline input. Delete shows an inline
confirmation. New backend utility functions and endpoints support both
operations. 7 new tests cover the backend logic.

### Success Criteria
- [ ] Load dialog shows `[Rename]` and `[Delete]` on every profile row
- [ ] Active profile has a visible `●` indicator
- [ ] Rename: inline input pre-filled, `[Save]` + `[Cancel]`
- [ ] Rename updates header if active profile was renamed
- [ ] Rename validates (non-empty, no reserved names, no path traversal)
- [ ] Delete: inline confirm, removes profile from list
- [ ] Deleting active profile resets header to "default" and reloads data
- [ ] Only one row in rename/delete state at a time
- [ ] All tests pass: 69 existing + 7 new = 76
- [ ] `ruff check backend/ tests/` — zero errors
- [ ] `cd frontend && npx vite build` — no errors

---

## Context

### Related Documentation
- `docs/DECISIONS.md` — ADR-002 (JSON persistence), ADR-008 (StorageBackend)
- `initials/14-init-profile-rename-delete.md` — Full spec

### Dependencies
- **Required**: PRP-006 (profile management — Load dialog, `list_profiles`, `_sanitize_name`)

### Files to Create/Modify
```
# MODIFIED — Backend
backend/utils/rankings.py              # rename_profile() + delete_profile()
backend/routers/rankings.py            # POST /rename + DELETE /profile/{name}

# MODIFIED — Frontend
frontend/src/api/rankings.js           # renameProfile() + deleteProfile()
frontend/src/components/LoadDialog.jsx  # inline rename/delete UI
frontend/src/components/WarRoom.jsx     # pass new props to LoadDialog
frontend/src/App.jsx                    # handleProfileRenamed + handleProfileDeleted

# MODIFIED — Tests
tests/test_profile_management.py        # 7 new tests
```

---

## Technical Specification

### Backend Utility — `rename_profile()` in `backend/utils/rankings.py`

```python
def rename_profile(
    old_name: str, new_name: str, storage: StorageBackend | None = None
) -> dict:
```

1. Sanitize `new_name` via `_sanitize_name()` — raises `ValueError`
2. Load old profile from storage
3. Update `profile["name"]` to `new_name.strip()`
4. Write to `{sanitized_new}.json`
5. Delete `{sanitized_old}.json`
6. Return `{"renamed": True, "old_name": ..., "new_name": ...}`

### Backend Utility — `delete_profile()` in `backend/utils/rankings.py`

```python
def delete_profile(
    name: str, storage: StorageBackend | None = None
) -> dict:
```

1. Validate name not reserved
2. Check profile exists
3. Delete from storage
4. Return `{"deleted": True, "name": name}`

### API Endpoints

```
POST   /api/rankings/rename            { "name": str, "new_name": str }
DELETE /api/rankings/profile/{name}
```

Both registered before `/{position}` in the router. The delete endpoint
uses a `/profile/` prefix to avoid ambiguity with `GET /{position}`.

### Frontend — `LoadDialog.jsx` Enhanced

New internal state: `renamingProfile`, `renameValue`, `renameError`,
`deletingProfile`. Three mutually exclusive row states: normal, renaming,
deleting. Starting one cancels the other.

New props: `activeProfile` (to show `●` indicator and detect active
profile operations), `onProfileRenamed(newName)`, `onProfileDeleted()`.

### Frontend — `App.jsx` Callbacks

```js
handleProfileRenamed(newName)  → setProfileName(newName)
handleProfileDeleted()         → setProfileName('2026 Draft'), reloadAllPositions
```

The state variable is `profileName` (not `activeProfile`) — follow the
existing naming in App.jsx.

---

## Implementation Steps

### Step 1: Backend — `rename_profile()` + `delete_profile()` + tests
**Files**: `backend/utils/rankings.py`, `tests/test_profile_management.py`

Add both utility functions. Add 7 tests:
- `test_rename_profile_renames_file`
- `test_rename_profile_updates_name_field`
- `test_rename_profile_rejects_reserved`
- `test_rename_profile_404_if_missing`
- `test_delete_profile_removes_file`
- `test_delete_profile_rejects_reserved`
- `test_delete_profile_404_if_missing`

**Validation:**
```bash
pytest tests/test_profile_management.py -v
ruff check backend/utils/rankings.py tests/test_profile_management.py
```
- [ ] All tests pass
- [ ] No lint errors

---

### Step 2: Backend — API endpoints
**Files**: `backend/routers/rankings.py`

Add `RenameRequest` model, `POST /rename` and `DELETE /profile/{name}`
endpoints. Register before `/{position}`.

**Validation:**
```bash
ruff check backend/routers/rankings.py
pytest tests/ -q
```
- [ ] Lint clean
- [ ] All tests pass

---

### Step 3: Frontend — API functions
**Files**: `frontend/src/api/rankings.js`

Add `renameProfile(name, newName)` and `deleteProfile(name)`.

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds

---

### Step 4: Frontend — Enhanced LoadDialog
**Files**: `frontend/src/components/LoadDialog.jsx`

1. Add rename/delete state management
2. Three row states: normal (Load/Rename/Delete buttons), renaming
   (input + Save/Cancel), deleting (confirm text + Confirm/Cancel)
3. Active profile indicator (`●`)
4. Inline error for rename validation failures
5. Refresh profile list after rename/delete

New props: `activeProfile`, `onProfileRenamed`, `onProfileDeleted`.

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds

---

### Step 5: Frontend — Wire through WarRoom and App
**Files**: `frontend/src/components/WarRoom.jsx`, `frontend/src/App.jsx`

1. `App.jsx`: add `handleProfileRenamed` and `handleProfileDeleted`
   callbacks, import `renameProfile`/`deleteProfile` (not needed in App
   — LoadDialog calls API directly), pass `profileName` and callbacks
   through `WarRoom` to `LoadDialog`
2. `WarRoom.jsx`: accept and pass new props to `LoadDialog`

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds
- [ ] Manual: rename a profile, verify list refreshes and header updates
- [ ] Manual: delete a profile, verify removal
- [ ] Manual: delete active profile, verify header resets

---

### Step 6: Documentation
**Files**: `docs/TASK.md`

Update TASK.md to mark 14 complete.

---

### Step 7: Final Integration Check
```bash
pytest tests/ --cov=backend --cov-report=term-missing
ruff check backend/ tests/
cd frontend && npx vite build
```
- [ ] All tests pass (76 total)
- [ ] Coverage >= 80% for `backend/utils/`
- [ ] Zero lint errors
- [ ] Frontend builds cleanly
- [ ] No file exceeds 500 lines

---

## Testing Requirements

### Unit Tests — `tests/test_profile_management.py` (additions)
```
test_rename_profile_renames_file       — old key gone, new key present
test_rename_profile_updates_name_field — profile["name"] == new_name
test_rename_profile_rejects_reserved   — ValueError for "default"/"seed"
test_rename_profile_404_if_missing     — FileNotFoundError
test_delete_profile_removes_file       — key no longer exists
test_delete_profile_rejects_reserved   — ValueError for "default"/"seed"
test_delete_profile_404_if_missing     — FileNotFoundError
```

### Manual Browser Tests
- [ ] Load dialog shows Rename + Delete buttons on each row
- [ ] Active profile shows `●` indicator
- [ ] Rename: click → input appears pre-filled → edit → Save → list refreshes
- [ ] Rename: Cancel reverts without changes
- [ ] Rename: empty name shows inline error
- [ ] Rename: reserved name shows inline error
- [ ] Delete: click → "Delete X?" confirm → Confirm → profile removed
- [ ] Delete: Cancel reverts
- [ ] Delete active profile → header resets, data reloads
- [ ] Only one row in rename/delete state at a time

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | 76 tests pass | ☐ |
| 2 | `ruff check backend/ tests/` | Zero errors | ☐ |
| 3 | `cd frontend && npx vite build` | Build succeeds | ☐ |
| 4 | Start dev servers | Both start | ☐ |
| 5 | Save As "Test Rename" | Profile created | ☐ |
| 6 | Open Load dialog | "Test Rename" shown with Rename/Delete | ☐ |
| 7 | Click Rename → type "Renamed" → Save | List shows "Renamed", old gone | ☐ |
| 8 | Rename active profile | Header updates to new name | ☐ |
| 9 | Save As "To Delete" | Profile created | ☐ |
| 10 | Click Delete → Confirm | "To Delete" removed from list | ☐ |
| 11 | Load "Renamed", then delete it | Header resets, data reloads | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| 400 invalid name | Empty, reserved, path traversal | Inline error in rename input |
| 404 not found | Profile deleted externally | Inline error, refresh list |
| Network error | Connection lost | Error banner |

---

## Open Questions

None — the init spec covers all flows, validation rules, and edge cases.

---

## Rollback Plan

```bash
git revert <commit>
pytest tests/ -q
cd frontend && npx vite build
```

Backend functions are additive. LoadDialog changes are self-contained.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Init spec has exact UI wireframes, utility signatures, validation rules |
| Feasibility | 10 | Standard CRUD — rename is read+write+delete, delete is delete |
| Completeness | 10 | All files, 7 test cases, edge cases (active profile rename/delete) |
| Alignment | 10 | Extends existing profile management, uses StorageBackend, same patterns |
| **Average** | **10** | Ready for execution |

---

## Notes

### Route Registration Order
`DELETE /api/rankings/profile/{name}` uses a `/profile/` prefix — this
avoids the `/{position}` catch-all. `POST /api/rankings/rename` is a
named route like `/save-as` — also safe. Both must be registered before
the `/{position}` route in the router file.

### File Size Check
- `backend/utils/rankings.py`: ~390 lines → ~430 after (under 500)
- `backend/routers/rankings.py`: ~320 lines → ~360 after (under 500)
- `frontend/src/components/LoadDialog.jsx`: 58 lines → ~140 after (well under 500)
- `tests/test_profile_management.py`: ~70 lines → ~120 after (well under 500)
