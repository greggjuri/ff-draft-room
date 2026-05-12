# 18 — Untrack Rankings JSONs + Stale Docs Cleanup

## Goal

Stop tracking `data/rankings/*.json` in git. These files are regenerable
runtime state (local dev: written by the app; production: lives in S3
only), not source. Tracking them creates a second source of truth that
drifts. While in the same change, fix a stale `README.md` section that
still describes the FantasyPros CSV format.

Pure repo hygiene — no code changes, no deploy needed.

## Context

- `data/rankings/default.json` and `data/rankings/seed.json` are both
  tracked in the repo (confirmed during PRP-017 execution).
- In **local dev**, the app writes to these files via `LocalStorage` —
  every save during development would show as a `M` in `git status`,
  inviting accidental commits of dev state.
- In **production**, the systemd service runs with `STORAGE_BACKEND=s3`,
  so these on-disk files are inert. Production reads/writes
  `s3://ff-draft-room-data/rankings/`.
- `CLAUDE.md` already documents `data/rankings/` as "local dev only" —
  the tracking is inconsistent with the stated convention.
- `README.md` "CSV Format" section still describes FantasyPros columns
  (`#, Player, Pos, Team, GP, [week columns], AVG, TTL`) — stale after
  PRP-017 / ADR-010.

## Design

### 1. Untrack `data/rankings/*.json`

```bash
git rm --cached data/rankings/default.json
git rm --cached data/rankings/seed.json   # if present in repo
```

`--cached` removes from git tracking only; local files stay on disk.
Local dev state is preserved.

### 2. Add to `.gitignore`

Add at the top of the existing `.gitignore`, or in a dedicated section
if one fits the file's structure:

```
# Rankings runtime state — never tracked
# Local dev writes to these; production uses S3
data/rankings/*.json
```

Wildcard rather than naming files explicitly — covers any named profile
the user might Save As locally (`Mock_Draft_1.json` etc.) without
needing a future `.gitignore` update.

### 3. Update `README.md` — CSV Format section

**Current** (stale):
```markdown
## CSV Format

FantasyPros half-PPR season leaders exports. Export from:
`fantasypros.com → Fantasy Football → Leaders → [Position] → Half PPR → Export CSV`

Expected columns: `#, Player, Pos, Team, GP, [week columns], AVG, TTL`
```

**New**:
```markdown
## CSV Format

Fantasy Footballers Podcast expert consensus rankings (ADR-010).
One CSV per position under `data/players/`, named:

```
2026 {POSITION} Draft Rankings - Fantasy Footballers Podcast.csv
```

Expected columns: `Name, Team, Rank, Andy, Jason, Mike` —
loader uses `Name`, `Team`, `Rank` and ignores the per-host columns.
```

### 4. (Optional, defer if it adds friction) — `README.md` project structure

The "Project Structure" block in `README.md` describes
`data/players/` as "FantasyPros CSV exports (seed data)". Should now
read "Fantasy Footballers CSV exports (seed data)". Same change in
`CLAUDE.md`'s structure block.

**Decision: include both.** Two trivial edits, same logical change.

## Verification

After the change:

```bash
# No rankings JSONs tracked
git ls-files data/rankings/
# Expected output: empty

# Files still on disk locally
ls data/rankings/
# Expected: default.json (and seed.json if you have it)

# .gitignore covers them
git status
# Expected: no rankings/*.json in any section

# Local dev still works
uvicorn backend.main:app --reload &
curl http://localhost:8000/api/rankings
# Expected: 200 with full profile (reads from existing local default.json)
```

## Out of Scope

- Removing legacy `data/players/{POS}_{YEAR}.csv` files (24 FantasyPros
  CSVs) — deferred until post-first-draft per ADR-010
- Cleaning up unused constants in `backend/utils/constants.py` —
  already done in PRP-017
- Production deploy — none needed (S3 is unaffected; on-disk EC2 files
  remain inert)

## Files Touched

- `.gitignore` — add `data/rankings/*.json` rule
- `data/rankings/default.json` — untrack via `git rm --cached`
- `data/rankings/seed.json` — untrack via `git rm --cached` (if tracked)
- `README.md` — update CSV Format section + project structure block
- `CLAUDE.md` — update project structure block

## Commit

```bash
git add .gitignore README.md CLAUDE.md
git commit -m "chore: untrack data/rankings JSONs + refresh stale FantasyPros docs"
git push origin main
```

Single atomic commit. No PRP needed for a change this small — pass the
init spec to Code directly, or apply the diff by hand.
