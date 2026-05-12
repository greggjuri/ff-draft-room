# PRP-018: Untrack Rankings JSONs + Stale Docs Cleanup

**Created**: 2026-05-12
**Initial**: `initials/18-init-untrack-rankings-and-doc-cleanup.md`
**Status**: Draft

---

## Overview

### Problem Statement
Two repo-hygiene issues from the PRP-017 cutover:

1. **Tracked rankings runtime state.** `data/rankings/default.json` and
   `data/rankings/seed.json` are both tracked in git. They are
   regenerable runtime state: in local dev the app writes them via
   `LocalStorage` every time the user saves; in production the systemd
   service runs `STORAGE_BACKEND=s3` and these on-disk files are inert.
   Tracking them creates a second source of truth that drifts and
   produced surprise `M` / `D` entries during PRP-017's smoke test
   (resolved with `git restore`, but the root issue persists).
2. **Stale FantasyPros references** in `README.md` and `CLAUDE.md` —
   ADR-010 retired the FantasyPros source, but the docs still describe
   the old CSV format and seed pipeline.

### Proposed Solution
A single atomic `chore:` commit:
- `git rm --cached` the two tracked rankings JSONs (files stay on disk
  locally; production S3 unaffected)
- Add `data/rankings/*.json` to `.gitignore` under a dedicated section
- Rewrite the "CSV Format" section in `README.md` to describe the
  Fantasy Footballers format
- Update the project-structure blocks in both `README.md` and
  `CLAUDE.md` to drop "FantasyPros" wording
- Sweep the remaining stale FantasyPros references in the same two
  files (init doesn't enumerate them, but leaving them stale defeats
  the cleanup goal — see Scope Expansion)

No code, no tests, no deploy.

### Success Criteria
- [ ] `git ls-files data/rankings/` returns empty
- [ ] `data/rankings/default.json` still exists on disk locally
- [ ] `git status` does not show `data/rankings/*.json` in any section
  after a fresh `uvicorn` run that mutates the profile
- [ ] No occurrence of "FantasyPros" remains in `README.md` or
  `CLAUDE.md` *except* the not-affiliated-with disclaimer (README line
  ~177), which is a legal attribution and stays
- [ ] `uvicorn backend.main:app --reload` + `GET /api/rankings` still
  returns the existing profile (reads from on-disk `default.json` —
  untouched)
- [ ] Single atomic commit on `main`

---

## Context

### Related Documentation
- `initials/18-init-untrack-rankings-and-doc-cleanup.md` — full spec
- `docs/DECISIONS.md` — ADR-010 (Fantasy Footballers as seed source),
  ADR-008 (StorageBackend / S3 for production)

### Dependencies
- **Required**: PRP-017 / ADR-010 complete (done as of commit `a1c33c3`)

### Files to Modify
```
.gitignore                                    # ADD: rankings/*.json rule
README.md                                     # MODIFY: CSV Format + struct + setup
CLAUDE.md                                     # MODIFY: intro + struct block
data/rankings/default.json                    # UNTRACK (git rm --cached, file stays)
data/rankings/seed.json                       # UNTRACK (git rm --cached, file stays)
```

### Files NOT Modified (intentional)
```
backend/**                                    # no code changes
tests/**                                      # no test changes
data/rankings/{default,seed}.json (on disk)   # local content untouched
S3 bucket contents                            # production unaffected
docs/**                                       # PLANNING/TASK/DECISIONS already current
```

### Confirmed Current State
```
$ git ls-files data/rankings/
data/rankings/default.json
data/rankings/seed.json

$ ls data/rankings/
default.json  seed.json

$ grep -n FantasyPros .gitignore
(no matches)
```

---

## Technical Specification

### `.gitignore` — insert new section

The existing file uses commented section headers (`# Node`, `# Python`,
`# Production env`, etc.). Add a new section near the top (after the
`# Python` block, before `# Production env`):

```
# Rankings runtime state — never tracked
# Local dev writes to these; production uses S3
data/rankings/*.json
```

Wildcard catches named profiles created via Save As (`Mock_Draft_1.json`,
etc.) without future maintenance.

### `git rm --cached` — surgical untrack

```bash
git rm --cached data/rankings/default.json data/rankings/seed.json
```

`--cached` removes from the index only; working-tree files are
preserved. After the commit, `git status` should be clean (the
.gitignore rule prevents the now-untracked files from re-appearing as
untracked).

### `README.md` — Three sections to update

**§ Player Data** (line ~49):

Before:
```markdown
All player data sourced from [FantasyPros](https://www.fantasypros.com) half-PPR season leaders exports.
```
After:
```markdown
All player data sourced from [Fantasy Footballers Podcast](https://www.thefantasyfootballers.com)
2026 expert consensus rankings (ADR-010).
```

**§ Setup / `data/players/` instructions** (lines ~76–77):

Before:
```markdown
# Add your FantasyPros CSV exports to data/players/:
# QB_2025.csv, RB_2025.csv, WR_2025.csv, TE_2025.csv
```
After:
```markdown
# Add your Fantasy Footballers Podcast CSVs to data/players/:
# 2026 QB Draft Rankings - Fantasy Footballers Podcast.csv
# 2026 RB Draft Rankings - Fantasy Footballers Podcast.csv
# 2026 WR Draft Rankings - Fantasy Footballers Podcast.csv
# 2026 TE Draft Rankings - Fantasy Footballers Podcast.csv
```

**§ CSV Format** (lines ~123–128):

Before:
```markdown
## CSV Format

FantasyPros half-PPR season leaders exports. Export from:
`fantasypros.com → Fantasy Football → Leaders → [Position] → Half PPR → Export CSV`

Expected columns: `#, Player, Pos, Team, GP, [week columns], AVG, TTL`
```
After:
```markdown
## CSV Format

Fantasy Footballers Podcast 2026 expert consensus rankings (ADR-010).
One CSV per position under `data/players/`, named:

    2026 {POSITION} Draft Rankings - Fantasy Footballers Podcast.csv

Expected columns: `Name, Team, Rank, Andy, Jason, Mike` — the loader
uses `Name`, `Team`, `Rank` and ignores the per-host columns. Empty
`Team` cells are preserved as empty strings for free agents.
```

> Note on indentation: the original code-block-style filename example
> in the init uses triple-backtick fenced code blocks. Within an
> already-fenced "After:" example in this PRP, nesting that as a
> 4-space indented block keeps the markdown unambiguous.

**§ Project Structure** (line ~167):

Before:
```markdown
│   ├── players/             # FantasyPros CSV exports (seed data)
```
After:
```markdown
│   ├── players/             # Fantasy Footballers CSV exports (seed data)
```

**§ Disclaimer** (line ~177) — **unchanged**. "Not affiliated with
Yahoo, FantasyPros, or the NFL" is a legal attribution disclaiming
prior data-source affiliation, not a stale spec reference. Leave it.

### `CLAUDE.md` — Two edits

**§ Intro / "What This Is"** (line ~11):

Before:
```markdown
Historical FantasyPros data seeds the initial rankings baseline — it is
infrastructure, not UI.
```
After:
```markdown
Fantasy Footballers Podcast 2026 expert consensus rankings (ADR-010)
seed the initial rankings baseline — it is infrastructure, not UI.
```

**§ Project Structure** (line ~119):

Before:
```markdown
│   ├── players/                 # FantasyPros CSVs (read-only seed data)
│   └── rankings/                # JSON profiles — local dev only
```
After:
```markdown
│   ├── players/                 # Fantasy Footballers CSVs (read-only seed data)
│   └── rankings/                # JSON profiles — local dev only (gitignored)
```

The `(gitignored)` addition makes the new ignore rule discoverable
from the structure block, which is the first place anyone looks.

---

## Scope Expansion vs. Init

The init explicitly lists three doc edits (CSV Format, README structure,
CLAUDE.md structure). This PRP also includes:
- `README.md` § Player Data line (top-of-file source attribution)
- `README.md` § Setup CSV-file instructions
- `CLAUDE.md` § "What This Is" intro paragraph

**Why**: all five touch the same two files; partial cleanup leaves
stale FantasyPros references that contradict ADR-010 in the most-read
parts of the README and the project's CLAUDE.md preamble. The init's
intent ("fix … stale documentation") covers this; the init author
just didn't enumerate every site.

If you want to keep this PRP scoped exactly to the init's enumerated
edits, drop the two README "Player Data" and "Setup" edits and the
CLAUDE.md intro edit. **Default chosen: include all five.**

---

## Implementation Steps

### Step 1 — Update `.gitignore`
**Files**: `.gitignore`

Insert a new commented section near the top of the file (after the
`# Python` block, before `# Production env`):

```
# Rankings runtime state — never tracked
# Local dev writes to these; production uses S3
data/rankings/*.json
```

**Validation**:
```bash
grep -A 2 "Rankings runtime state" .gitignore
```
- [ ] Section present
- [ ] Rule `data/rankings/*.json` appears

---

### Step 2 — Untrack rankings JSONs
**Commands**:
```bash
git rm --cached data/rankings/default.json data/rankings/seed.json
```

This stages the untrack as a deletion in the index but leaves both
files on disk. Confirm:

```bash
ls data/rankings/
# expected: default.json  seed.json  (still present)

git status
# expected:
#   deleted: data/rankings/default.json
#   deleted: data/rankings/seed.json
#   modified: .gitignore
```

- [ ] Both files still on disk
- [ ] Both show as `deleted:` in `git status` staging
- [ ] No untracked entries for `data/rankings/`

---

### Step 3 — Update `README.md`
**Files**: `README.md`

Apply all four edits per the Technical Specification:
- Player Data attribution line (~49)
- Setup CSV-file instructions (~76–77)
- CSV Format section (~123–128)
- Project Structure block (~167)

**Validation**:
```bash
grep -n FantasyPros README.md
# expected: only one match — the disclaimer line near the bottom
```
- [ ] Only the disclaimer mention of FantasyPros remains
- [ ] CSV Format describes Fantasy Footballers format with full filename
- [ ] Setup block lists the four new CSV filenames

---

### Step 4 — Update `CLAUDE.md`
**Files**: `CLAUDE.md`

Apply both edits per the Technical Specification:
- Intro line (~11)
- Project Structure block (~119)

**Validation**:
```bash
grep -n FantasyPros CLAUDE.md
# expected: zero matches
```
- [ ] No remaining FantasyPros references
- [ ] Structure block notes rankings/ is gitignored

---

### Step 5 — Sanity check the app still works
The app reads `default.json` from `data/rankings/` on first request.
That file is now untracked but still on disk — load behavior is
unchanged.

```bash
source .venv/bin/activate
uvicorn backend.main:app --port 8001 > /tmp/uvicorn.log 2>&1 &
sleep 2
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8001/health
curl -s http://localhost:8001/api/rankings | python -c "import sys, json; d=json.load(sys.stdin); print('profile name:', d['name']); print('players:', len(d['players']))"
pkill -f "uvicorn backend.main"
```

- [ ] `/health` → 200
- [ ] `/api/rankings` returns the existing profile
- [ ] No `data/rankings/*.json` appears in `git status` after the call
  (if any save happens, it should be silently ignored by the new rule)

---

### Step 6 — Commit + push
```bash
git add .gitignore README.md CLAUDE.md
# data/rankings/* deletions are already staged from Step 2
git status   # final pre-commit review

git commit -m "chore: untrack data/rankings JSONs + refresh stale FantasyPros docs"
git push origin main
```

- [ ] Commit shows: 3 modified (.gitignore, README.md, CLAUDE.md) + 2
  deleted from index (default.json, seed.json)
- [ ] `git ls-files data/rankings/` returns empty after the push
- [ ] `ls data/rankings/` still shows the local files

---

## Testing Requirements

### Automated
None. No code or tests changed. Existing `pytest tests/ -q` (82 passing)
remains the safety net for the broader codebase — if you want belt-and-
suspenders, run it before commit.

### Manual
Covered by Step 5's `curl` smoke test. The app must still load the
existing on-disk profile because the file itself is unchanged — only
its git-tracking status changed.

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `git ls-files data/rankings/` | (empty) | ☐ |
| 2 | `ls data/rankings/` | `default.json  seed.json` still present | ☐ |
| 3 | `grep -n FantasyPros README.md` | One match (disclaimer line only) | ☐ |
| 4 | `grep -n FantasyPros CLAUDE.md` | Zero matches | ☐ |
| 5 | `grep -A 1 "Rankings runtime state" .gitignore` | Rule present | ☐ |
| 6 | `uvicorn backend.main:app --port 8001`; `curl /health` | 200 | ☐ |
| 7 | `curl /api/rankings` | Returns existing profile from on-disk file | ☐ |
| 8 | Modify rankings via UI / save endpoint; `git status` | `default.json` change does NOT appear | ☐ |
| 9 | `git log -1 --stat` | Single commit, 5 files changed (3 mod, 2 del) | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| `git rm --cached` reports `pathspec did not match` for `seed.json` | seed.json removed between PRP authoring and execution | Run with `default.json` only; note in commit body |
| Wildcard `data/rankings/*.json` matches future named profile uses | Intentional — covers Save-As outputs too | None — by design |
| Someone clones the repo fresh | `data/rankings/` directory exists but is empty | App auto-seeds from CSV on first `/api/rankings` call — existing behavior, no change |

---

## Open Questions

None outstanding. The init's only ambiguity ("optional: include both
project-structure blocks") is resolved as "include all five doc edits"
in Scope Expansion above.

---

## Rollback Plan

The change is entirely git-tracked metadata + doc text. To revert:

```bash
git revert <commit-sha>
git push origin main
```

After revert:
- `data/rankings/default.json` and `seed.json` re-appear as tracked
  files at their pre-PRP-018 contents (which match the on-disk
  contents, modulo any local saves after the commit).
- `.gitignore` loses the rankings rule.
- README/CLAUDE doc text returns to the stale FantasyPros wording.

If a local save *between* commit and revert produced divergent content
in `default.json`, the revert will create a working-tree change.
Resolve with `git checkout HEAD -- data/rankings/default.json` to
match repo state, or accept the local change.

Production is unaffected — no deploy step in this PRP, S3 state never
referenced.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Exact strings to find/replace, exact files, exact commands. |
| Feasibility | 10 | All operations are stock git + text edits. No environment, framework, or runtime concerns. |
| Completeness | 9 | Five doc edits + 2 untracks + 1 .gitignore rule + 1 smoke test. Init listed three of the doc edits; the other two are flagged in Scope Expansion with an opt-out. |
| Alignment | 10 | Directly implements ADR-010's "Documentation has been updated" consequence and CLAUDE.md's stated "JSON profiles — local dev only" convention. |
| **Average** | **9.75** | Ready for execution. |

---

## Notes

### Init's "no PRP needed" guidance
The init says: "No PRP needed for a change this small — pass the init
spec to Code directly, or apply the diff by hand." This PRP exists
because `/generate-prp` was invoked anyway. It is intentionally lean
(no unit tests section, no Streamlit-template artifacts) — most of its
weight is the explicit before/after diffs, which double as
copy-pasteable instructions.

If the user prefers to skip the PRP altogether and execute the init
directly, that path is equally valid; this PRP is a structured
reference rather than a gate.

### Why include the extra doc edits
Cleanup PRPs are most useful when a future reader can `grep FantasyPros
README.md CLAUDE.md` and see one expected hit (the disclaimer) instead
of five-with-no-obvious-reason. Partial cleanup invites a second
follow-up PR for the same files, which is more friction than one
slightly-wider commit.
