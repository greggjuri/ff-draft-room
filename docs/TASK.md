# FF Draft Room - Task Tracker

## Current Sprint: Phase 1d — Polish

### In Progress
_None_

---

## Backlog

### Phase 1d — Polish
_Empty — all items complete or dropped_

### Phase 2 — Live Draft (future)
- [ ] Full draft board with round/pick tracking
- [ ] Best available board
- [ ] My roster view, needs tracker, scarcity alerts

---

## Recently Completed

- [x] `23-init-context-menu-click-to-open.md` — Context menu submenus open on click
  - Fixed the PRP-020 hover-fragility bug where the cursor crossing
    the gap from a parent item to its submenu caused the submenu to
    snap shut. Especially painful for Edit ▸ Delete.
  - Pleasant finding: PRP-020 already wired `openSub` state,
    `toggleSub` handler, and the `.open` class — the hover behaviour
    was 100% CSS-driven via `@media (pointer: fine)`. Removing one
    CSS block + unwrapping the touch wrapper collapsed everything to
    one state-driven rule.
  - Rider enhancements (same two files): `openSub` → `openSubmenu`
    rename; arrow rotation `▸` → `▾` when open; `<div>` parents → 
    `<button type="button">` for free Enter/Space activation + correct
    ARIA role + `:focus-visible` ring. Each parent + its submenu now
    sit in a `.cm-item-wrapper` div (because `<button>` can't validly
    contain absolutely-positioned descendants).
  - Pure frontend: no backend, no API, no tests touched (98 passing
    baseline preserved).
  - Single atomic commit (`aa2c741`).
  - Follow-ups: keyboard arrow-key submenu navigation (still deferred);
    eventual Edit submenu additions (Rename, Move to tier).
  - **Pre-existing cleanup parked**: 24 legacy `{POS}_{YEAR}.csv`
    deletions sit unstaged in the working tree (per ADR-010's
    "separate cleanup change after first live draft" plan). Operator
    should commit those separately when ready.

- [x] `22-init-player-detail-in-draft-mode.md` — PlayerDetailDialog in Draft Mode
  - Wired the click handler PRP-021 left disconnected on the Draft
    Mode branch of `PlayerRow.jsx`. Clicking a player name in Draft
    Mode now opens the dialog — most valuable mid-pick when comparing
    two or three players with the clock running.
  - Two surgical edits: `PlayerRow.jsx:73` adds `onClick={onNameClick}`
    on the Draft name span (matches the War Room branch byte-for-byte);
    `TierGroup.jsx:29` drops the `!isDraft &&` short-circuit so the
    callback actually invokes `onNotesOpen`.
  - Status dot still cycles (distinct CSS grid cell, no collision);
    right-click context menu (PRP-020) still works; notes save round-
    trips identically to War Room mode.
  - Pure frontend: no backend, no API, no tests touched (98 passing
    baseline preserved).
  - Single atomic commit (`a94d589`).
  - Follow-ups: optional auto-close-on-status-dot-click and compact
    dialog variant — defer until real draft use surfaces the need.

- [x] `21-init-player-detail-dialog.md` — PlayerDetailDialog (outlook + notes split panel)
  - Replaced NotesDialog (single-textarea modal) with a two-panel
    PlayerDetailDialog. Surfaces the per-player data that PRP-019 has
    been storing since the tiered ingest landed.
  - Left panel: metadata strip (`Proj X · ADP Y · Bye N`, with each
    segment omitted when null/empty) + full outlook prose, scrolls
    within bounds.
  - Right panel: existing notes textarea + Save/Close, behaviour
    verbatim (no dirty-state warning — wasn't one before, didn't add
    one).
  - Header now reads `📋 {name} · {position} · {team}` (position pill
    added between name and team).
  - Narrow viewports (<700px) stack the panels vertically.
  - `risk` / `upside` intentionally remain hidden in the UI per
    operator preference; war room rows stay tight.
  - Pure frontend change: no backend, no API, no tests touched
    (98 passing baseline preserved).
  - Single atomic commit (`eea7f08`).
  - Follow-ups: future surfacing of risk/upside if operator changes
    mind; future demo site (init-22 backlog).

- [x] `20-init-add-delete-ux-overhaul.md` — Add/Delete UX overhaul
  - Toolbar gains a single `+ ADD PLAYER` button (leftmost, divider
    before SAVE); 32 per-tier `+ {POSITION} · Tier N` strips removed.
  - AddPlayerDialog expanded 2 → 10 fields (Name, Team, Position
    dropdown, Tier, plus optional bye_week / adp / projected_points /
    risk / upside / outlook). Blank optionals submit as null / "".
  - Right-click context menu restructured: TagPicker.jsx (7-icon
    horizontal strip) → ContextMenu.jsx (2-item parent menu with
    Tags ▸ / Edit ▸ submenus). Submenus open on hover (desktop) or
    click (touch via `@media (pointer: coarse)`).
  - Always-visible `×` delete button on every player row removed;
    delete now lives under Edit ▸ Delete (red, `var(--danger)`),
    invoking the existing `DeleteConfirmDialog`.
  - Backend: `AddPlayerRequest` gains 6 optional fields + `Field(ge=1)`
    on tier (422 for tier=0); handler passes the new fields as kwargs
    to `add_player()` (already extended in PRP-019).
  - 98 tests passing (+1 `test_add_player_full_kwargs` for full
    kwargs round-trip). Manual browser verification deferred to
    operator post-deploy.
  - Single atomic commit (`2bff86c`).
  - Follow-ups: future Edit-submenu additions (Rename, Move to tier,
    Set notes); future UI to actually surface the new fields in the
    war room rows.

- [x] `19-init-fantasy-footballers-tiered-import.md` — Fantasy Footballers tiered 2026 seed
  - New `2026_{POS}.csv` filename pattern + 13-column tiered format
    (was 6-column rank-only). Old `2026 {POS} Draft Rankings - …Podcast.csv`
    files removed.
  - Six new per-player fields persisted on every seeded record:
    `bye_week` (int|None), `adp` (str), `projected_points` (float),
    `risk` (float), `upside` (float), `outlook` (str). Tier sourced
    directly from CSV — `_assign_tier()` / `TIER_BREAKPOINTS` deleted.
  - `add_player()` extended with the same six fields as keyword-only
    optional kwargs (None / "" defaults) so seeded and manually-added
    records share the 13-field shape. Router callsite and AddPlayer
    dialog unchanged; richer manual entry deferred to PRP-020.
  - ADP read with `dtype=str` to preserve trailing zeros ("3.10" not 3.1).
    bye_week stored as nullable Int64 → int / None in JSON.
  - 97 tests passing (was 82): +15 in test_data_loader, +9 in
    test_rankings, _sample_df helper in test_profile_management updated.
  - Single atomic commit (`db7273d`). Production deploy: pull, deploy,
    then click Reset in the toolbar (or `POST /api/rankings/seed`) to
    force a fresh re-seed from the new CSVs.
  - Follow-ups: PRP-020 (AddPlayer dialog + endpoint body schema to
    surface new fields); optional ADR-011 note for the schema expansion
    (ADR-010 already anticipates this).

- [x] `18-init-untrack-rankings-and-doc-cleanup.md` — Repo hygiene
  - `git rm --cached` `data/rankings/{default,seed}.json`; rule
    activated in `.gitignore` (was commented out)
  - README.md: rewrote CSV Format + player-data attribution + setup
    block for Fantasy Footballers format; updated structure block
  - CLAUDE.md: updated intro paragraph + structure block (marks
    rankings/ as gitignored)
  - Smoke test confirmed: `POST /api/rankings/save` mutates disk file
    but git status stays clean
  - Single atomic commit (`766ead1`), no deploy needed

- [x] `17-init-fantasy-footballers-import.md` — Fantasy Footballers 2026 seed
  - Replaced FantasyPros half-PPR season-stats CSVs with Fantasy Footballers
    Podcast 2026 expert rankings (one CSV per position, rank-only)
  - `data_loader.py` rewrite: strict loader, FileNotFoundError on missing
    file, FA empty-team preserved, legacy `{POS}_{YEAR}.csv` ignored
  - `seed_rankings()` simplified: sort by rank ascending; year filter and
    `total_pts` ordering removed
  - `load_all_players` → `load_player_data` rename (3 router callsites)
  - Pruned dead constants: `YEARS`, `CSV_COLUMN_MAP`, `SCHEMA_COLUMNS`,
    `EXPECTED_COUNTS`
  - 82 tests passing (net delta 0; +1 in test_data_loader, −1 in test_rankings)
  - Tiered release follow-up: Fantasy Footballers ships tiered files in
    ~1.5 weeks → separate init; tier assignment continues to use
    `_assign_tier()` heuristic until then
  - Production deploy: `POST /api/rankings/seed` on EC2 to force fresh
    rebuild from new CSVs (see PRP-017 Step 10 for seed.json caveat)
  - Follow-ups: ADR-010 to supersede ADR-003; separate cleanup PR to
    `git rm --cached` `data/rankings/{default,seed}.json` and gitignore them

- [x] `16-init-roster-panel.md` — My Roster panel in Draft Mode
  - Fixed bottom drawer with handle bar showing live pick counts
  - 4 position sections with accent colors, tag icons, team logos
  - Slide animation, padding-bottom for content clearance
  - Pure frontend — no backend changes

- [x] `15-init-player-tags.md` — Player tag icons
  - 7 tags: heart, fire, gem, warning, cross, skull, flag
  - Right-click tag picker with toggle/clear, viewport clamping
  - Tag icon rendered left of name text in name box
  - set_player_tag() backend utility + PUT /{position}/{rank}/tag
  - Backward compat: missing tag field defaults to "" on read
  - 6 new tests (82 total passing)

- [x] `14-init-profile-rename-delete.md` — Profile rename and delete
  - Inline rename input + delete confirm in Load dialog
  - Active profile indicator (● dot)
  - rename_profile() + delete_profile() backend utilities
  - POST /rename + DELETE /profile/{name} endpoints
  - 7 new tests (76 total passing)

- [x] `11-init-visual-polish.md` — Position-specific column accent colors
  - QB gold, RB green, WR blue, TE orange — header border + tier left-border
  - depth · N sub-label on column headers
  - Background texture attempted and rolled back — clean navy reads better

- [x] `12-init-team-logos.md` — NFL team logos on player name boxes
  - ESPN CDN, right-aligned inside name box, 18px, opacity 72%
  - JAC→jax normalization, silent fallback for FA/unknown

- [x] `13-init-team-gradients.md` — Team color gradients on player name boxes
  - Flat tier color left → team tint (22%) right, kicks in at 45%
  - Applies in War Room and Draft Mode (tints draft status colors too)

- [x] `10-init-tier-drag.md` — Draggable Tier Boundaries
  - `set_player_tier()` backend utility + `PUT /{position}/{rank}/tier` endpoint
  - `TierSeparator` component with mouse + touch drag support
  - Empty tier guard prevents dragging below 1 player
  - Adjacency validation (±1 only) on backend
  - 5 new unit tests (69 total passing)
  - ADR-009 (Draggable Tier Boundaries)

- [x] `09-init-aws-deploy.md` — AWS Deployment
  - S3 StorageBackend abstraction (LocalStorage + S3Storage)
  - Cognito JWT auth middleware (conditional — prod only)
  - Frontend auth: LoginPage + AuthContext + token headers
  - CDK stack: S3 bucket + IAM role + instance profile
  - Deploy scripts: deploy.sh, cdk-bootstrap.sh, nginx, systemd
  - 15 new storage tests (64 total passing)
  - ADR-007 (EC2 + nginx), ADR-008 (S3 Storage Backend)

- [x] `08-init-search.md` — Global Player Search
  - Commit: `f7d3743`
  - SearchBar component with dropdown overlay, in-memory filtering
  - Scroll-to-player with 1.5s highlight on result click
  - Works in both War Room and Draft Mode

- [x] `07-init-draft-mode.md` — Draft Mode
  - Commit: `7992c01`
  - WAR ROOM | DRAFT toggle in header
  - Status dot per player: undrafted → mine → other cycling
  - Controls hidden in draft mode, exit confirm dialog
  - Pure frontend — no backend changes

- [x] `06-init-profile-management.md` — Profile Management
  - Commits: `a190560`, `83922b4`, `5dc8df4`
  - Save As, Load, Reset, Set as Default
  - 5 new backend endpoints, 4 new frontend dialogs
  - 14 new tests (49 total passing)

- [x] `05-init-react-frontend.md` — React War Room Frontend
  - Commit: `89a7c20`
  - 7 components: WarRoom, PositionColumn, TierGroup, PlayerRow,
    NotesDialog, AddPlayerDialog, DeleteConfirmDialog
  - Full CSS control with design tokens, native HTML `<dialog>`
  - Vite proxy to FastAPI backend

- [x] `04-init-fastapi-backend.md` — FastAPI Backend
  - Commits: `5017f03`, `770efd6`, `363a3df`, `12e4f2f`
  - 8 API endpoints for rankings CRUD + profile management
  - Ported utils from app/ to backend/, removed Streamlit deps
  - All tests updated to import from backend/

- [x] `03-init-war-room-core.md` — War Room in Streamlit
  - Commit: `dede688`
  - Retired due to Streamlit UI limitations (ADR-006)

- [x] `01-init-project-setup.md` — Project scaffold, data loader
  - Commit: `6a5f313`

---

## Dropped / Descoped

- ~~Streamlit UI~~ — **Retired** (2026-03-30)
  - Replaced by FastAPI + React (ADR-006)

- ~~`02-init-history-browser.md`~~ — **Dropped** (2026-03-30)
  - App is rankings-only. Historical data is seed infrastructure.

- ~~K and D/ST columns~~ — **Dropped** (2026-04-14)
  - Not needed — handled separately during drafts

- ~~Export rankings to CSV~~ — **Dropped** (2026-04-17)
  - Not needed

---

## Architecture Decisions

### Import Convention (Backend)
All backend Python imports are relative to `backend/`:
```python
# CORRECT
from utils.constants import POSITIONS
from utils.rankings import load_or_seed
from utils.storage import get_storage

# WRONG
from backend.utils.constants import POSITIONS
```

### Profile Storage Model
```
default.json       ← active profile (always present)
seed.json          ← custom reset baseline (optional)
{name}.json        ← named profiles created via Save As
```
In local dev: files in `data/rankings/`
In production: S3 objects under `rankings/` prefix

---

## Notes

### Running the Stack
```bash
# Backend
source .venv/bin/activate
uvicorn backend.main:app --reload   # → localhost:8000

# Frontend
cd frontend && npm run dev          # → localhost:5173
```

### Production Deploy
```bash
# On EC2
git pull origin main
./scripts/deploy.sh
```

### Tests
```bash
pytest tests/ --cov=backend         # 76 passing
ruff check backend/ tests/          # zero errors
```

### CSV File Naming
```
data/players/QB_2020.csv  through  QB_2025.csv
data/players/RB_2020.csv  through  RB_2025.csv
data/players/WR_2020.csv  through  WR_2025.csv
data/players/TE_2020.csv  through  TE_2025.csv
```

### League Defaults
- 10 teams, half-PPR, standard roster
- Positions: QB, RB, WR, TE

---

*Last updated: 2026-06-01 (PRP-023 context menu click-to-open submenus)*
