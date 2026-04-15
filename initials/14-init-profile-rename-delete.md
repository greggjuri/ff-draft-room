# 14-init-profile-rename-delete.md — Profile Rename and Delete

**Date**: 2026-04-15
**Phase**: 1d — Polish
**Scope**: Backend + Frontend
**New tests**: Yes — rename and delete backend utility functions
**New ADR**: None

---

## Context

The Load dialog lists all named profiles with a single `[Load]` button per row.
There is no way to rename a profile after saving or to delete one that is no
longer needed. This spec adds both operations as inline actions in the existing
Load dialog — keeping all profile management in one place.

---

## UI Design

### Load dialog — enhanced row

Each profile row gains two additional action buttons to the right of `[Load]`:

```
┌─────────────────────────────────────────────────────────┐
│  Mock Draft 1          [Load]  [Rename]  [Delete]        │
│  Pre-FA Rankings       [Load]  [Rename]  [Delete]        │
│  Final Board           [Load]  [Rename]  [Delete]        │
└─────────────────────────────────────────────────────────┘
```

### Rename flow

Clicking `[Rename]` on a row switches that row into an inline edit state:

```
┌─────────────────────────────────────────────────────────┐
│  [ Mock Draft 1        ▏]          [Save]  [Cancel]      │
│  Pre-FA Rankings       [Load]  [Rename]  [Delete]        │
└─────────────────────────────────────────────────────────┘
```

- The input is pre-filled with the current name and focused
- `[Save]` submits the rename — calls the API, refreshes the list
- `[Cancel]` reverts to the normal row
- Only one row can be in rename mode at a time — clicking `[Rename]` on
  another row cancels the previous edit
- Validation: same rules as Save As (non-empty, no path traversal, not a
  reserved name) — inline error shown below the input on failure
- If the renamed profile is currently active, the profile name in the header
  updates to the new name

### Delete flow

Clicking `[Delete]` shows a confirmation state inline on the same row —
no separate modal needed:

```
┌─────────────────────────────────────────────────────────┐
│  Delete "Mock Draft 1"?     [Confirm]  [Cancel]          │
│  Pre-FA Rankings       [Load]  [Rename]  [Delete]        │
└─────────────────────────────────────────────────────────┘
```

- `[Confirm]` calls the API, removes the profile, refreshes the list
- `[Cancel]` reverts to the normal row
- If the deleted profile is currently active (i.e. `activeProfile ===
  profileName`), the active profile name in the header reverts to `"default"`
  and a full data reload is triggered to ensure state is consistent

### Active profile indicator

Add a subtle active indicator so the user knows which profile is loaded.
A small `●` dot or `(active)` label next to the name:

```
│  Mock Draft 1  ●       [Load]  [Rename]  [Delete]        │
```

CSS: `color: var(--accent)` (`#0076B6`), font-size 10px.

---

## Backend

### New utility functions (`backend/utils/rankings.py`)

#### `rename_profile(old_name, new_name, storage)`

```python
def rename_profile(
    old_name: str,
    new_name: str,
    storage: StorageBackend | None = None,
) -> dict:
    """Rename a saved profile.

    Reads old file, writes under new sanitized name, deletes old file.
    Returns {"renamed": True, "old_name": old_name, "new_name": new_name}.
    Raises ValueError on invalid new_name or reserved names.
    Raises FileNotFoundError if old profile does not exist.
    """
```

Logic:
1. `_sanitize_name(new_name)` — raises `ValueError` on invalid
2. Load old profile from storage (`{sanitized_old}.json`)
3. Update `profile["name"]` to `new_name.strip()`
4. Write to `{sanitized_new}.json`
5. Delete `{sanitized_old}.json`
6. Return result dict

#### `delete_profile(name, storage)`

```python
def delete_profile(
    name: str,
    storage: StorageBackend | None = None,
) -> dict:
    """Delete a saved profile.

    Raises ValueError if name is reserved.
    Raises FileNotFoundError if profile does not exist.
    Returns {"deleted": True, "name": name}.
    """
```

Logic:
1. Validate `name.lower() not in RESERVED_NAMES` — raises `ValueError`
2. Delete `{sanitized_name}.json` from storage
3. Return result dict

---

### New API endpoints (`backend/routers/rankings.py`)

```
POST /api/rankings/rename
Body: { "name": str, "new_name": str }

DELETE /api/rankings/profile/{name}
```

**`POST /api/rankings/rename`**
- Calls `rename_profile(body.name, body.new_name, storage)`
- 400 on `ValueError` (invalid name, reserved name)
- 404 on `FileNotFoundError`
- 200 `{"renamed": true, "old_name": ..., "new_name": ...}` on success

**`DELETE /api/rankings/profile/{name}`**
- Calls `delete_profile(name, storage)`
- 400 on `ValueError` (reserved name)
- 404 on `FileNotFoundError`
- 200 `{"deleted": true, "name": name}` on success

**Route registration**: both new routes must be registered before
`/{position}` in the router. `DELETE /api/rankings/profile/{name}` uses
a `/profile/` prefix specifically to avoid any ambiguity with
`GET /api/rankings/{position}`.

---

## Frontend

### `frontend/src/api/rankings.js` — new functions

```js
export const renameProfile = (name, newName) =>
  request(`${BASE}/rename`, {
    method: 'POST',
    body: JSON.stringify({ name, new_name: newName }),
  })

export const deleteProfile = (name) =>
  request(`${BASE}/profile/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
```

---

### `frontend/src/components/LoadDialog.jsx` — enhanced

New internal state:
```js
const [renamingProfile, setRenamingProfile] = useState(null)  // name being renamed
const [renameValue, setRenameValue]         = useState('')
const [renameError, setRenameError]         = useState('')
const [deletingProfile, setDeletingProfile] = useState(null)  // name awaiting confirm
```

Row rendering logic (three mutually exclusive states per row):

```
1. deletingProfile === profile  →  confirm state
2. renamingProfile === profile  →  rename input state
3. default                      →  normal row
```

Starting a rename cancels any pending delete, and vice versa.

#### Rename submission handler
```js
async function handleRename(oldName) {
  setRenameError('')
  try {
    await renameProfile(oldName, renameValue)
    if (activeProfile === oldName) onProfileRenamed(renameValue)
    setRenamingProfile(null)
    await refreshProfiles()  // reload the list
  } catch (err) {
    setRenameError(err.message ?? 'Rename failed')
  }
}
```

#### Delete confirmation handler
```js
async function handleDeleteConfirm(name) {
  try {
    await deleteProfile(name)
    if (activeProfile === name) onProfileDeleted()
    setDeletingProfile(null)
    await refreshProfiles()
  } catch (err) {
    // show inline error on the row or a toast
  }
}
```

---

### `frontend/src/App.jsx` — new callbacks

Two new callbacks passed down through `WarRoom` → `LoadDialog`:

```js
// Called when the active profile is renamed from LoadDialog
function handleProfileRenamed(newName) {
  setActiveProfile(newName)
}

// Called when the active profile is deleted from LoadDialog
function handleProfileDeleted() {
  setActiveProfile('default')
  loadData()  // reload rankings from backend (now serves default.json)
}
```

`activeProfile` state is already present in `App.jsx` (used to show the
profile name in the header). These two handlers close the loop between
LoadDialog actions and the header state.

---

## New Tests (`tests/test_profile_management.py`)

Add to the existing test file:

```
test_rename_profile_renames_file      — old file gone, new file present
test_rename_profile_updates_name_field — profile["name"] updated to new name
test_rename_profile_rejects_reserved  — ValueError for "default"/"seed" new name
test_rename_profile_404_if_missing    — FileNotFoundError for nonexistent profile
test_delete_profile_removes_file      — file no longer exists after delete
test_delete_profile_rejects_reserved  — ValueError for "default"/"seed"
test_delete_profile_404_if_missing    — FileNotFoundError for nonexistent profile
```

All tests use `tmp_path` + `LocalStorage` fixture — no real filesystem writes.

---

## Files to Change

```
# Backend
backend/utils/rankings.py              # rename_profile() + delete_profile()
backend/routers/rankings.py            # POST /rename + DELETE /profile/{name}

# Frontend
frontend/src/api/rankings.js           # renameProfile() + deleteProfile()
frontend/src/components/LoadDialog.jsx # inline rename + delete UI
frontend/src/components/LoadDialog.css # new button and state styles (if separate file)

# Tests
tests/test_profile_management.py       # 7 new tests
```

No new components. No new files outside the above.

---

## Acceptance Criteria

- [ ] Load dialog shows `[Rename]` and `[Delete]` buttons on every profile row
- [ ] Currently active profile has a visible `●` indicator
- [ ] Clicking `[Rename]` switches that row to an inline input pre-filled with the current name
- [ ] Rename `[Save]` submits, refreshes list, updates header if active profile was renamed
- [ ] Rename `[Cancel]` reverts the row without making any changes
- [ ] Rename shows inline error for empty name, reserved name, or API failure
- [ ] Clicking `[Delete]` switches that row to inline confirm state
- [ ] Delete `[Confirm]` deletes profile, removes from list
- [ ] Delete `[Cancel]` reverts without changes
- [ ] Deleting the active profile resets header to `"default"` and reloads data
- [ ] Only one row can be in rename or delete state at a time
- [ ] `pytest tests/ -q` — all tests pass (69 existing + 7 new = 76 total)
- [ ] `ruff check backend/ tests/` — zero errors
- [ ] `npx vite build` — 0 errors

---

## Non-Goals

- Duplicate / copy a profile — future
- Profile metadata (date created, notes) — future
- Reordering profiles in the list — future
- Rename/delete of `default` or `seed` — explicitly blocked
