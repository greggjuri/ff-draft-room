# FF Draft Room - Architecture Decisions

## ADR-001: Streamlit as UI Framework

**Date**: 2026-03-22
**Status**: Superseded by ADR-006

### Decision
Use Streamlit for the UI layer.

### Superseded Because
Streamlit cannot support the dense, interactive war room layout required.
See ADR-006.

---

## ADR-002: JSON Files for Rankings Persistence

**Date**: 2026-03-22
**Status**: Accepted — extended by ADR-008

### Decision
Use JSON files for all ranking profiles.

### Rationale
- Human-readable, no setup, portable, easy to back up
- Profiles are small (< 200 players, ~50KB max)

### Consequences
- Zero setup, works out of the box locally
- No query capability — load entire profile into memory (acceptable)
- Extended by ADR-008 to support S3 as the production storage backend
  while preserving local JSON behaviour for development

---

## ADR-003: FantasyPros CSV as Sole Data Source

**Date**: 2026-03-22
**Status**: Accepted

### Decision
Use exclusively FantasyPros half-PPR season leaders CSV exports.
No approximations, no fallbacks, no hardcoded data.

### Rationale
- 24 CSV files already collected (4 positions × 6 years)
- Verified authoritative source
- Fully offline at runtime

---

## ADR-004: VOR Replacement Level Thresholds

**Date**: 2026-03-22
**Status**: Accepted

### Decision
Default replacement levels for 10-team half-PPR:
- QB: Rank 13 · RB: Rank 25 · WR: Rank 35 · TE: Rank 13

Configurable per ranking profile.

---

## ADR-005: Rankings-Only App — No History Browser

**Date**: 2026-03-30
**Status**: Accepted

### Decision
Drop History and Analysis pages. Historical CSV data seeds the initial
rankings baseline only. No user-facing history view.

### Rationale
App is a draft preparation tool, not a stats browser.
Tighter scope = faster path to a usable tool.

---

## ADR-006: Retire Streamlit — Migrate to FastAPI + React

**Date**: 2026-03-30
**Status**: Accepted

### Context
The War Room was fully implemented in Streamlit (commit dede688, 43 tests
passing). During UI polish, Streamlit's fundamental rendering model
repeatedly blocked desired UI behaviour:

- Background colors cannot be applied to sections containing widgets —
  Streamlit strips custom HTML div wrappers around interactive elements
- CSS selectors targeting Streamlit's internal DOM structure are fragile
  and break across versions
- `nth-child` / `nth-of-type` selectors cannot reliably target tier groups
  because Streamlit inserts unpredictable wrapper elements
- MutationObserver JavaScript injection was required just to attempt basic
  alternating row colors — and still failed
- The war room is a dense, interactive, pixel-precise layout that Streamlit
  was never designed to support

Streamlit is the right tool for data dashboards with charts and tables.
It is the wrong tool for a custom interactive board UI.

### Decision
Retire Streamlit entirely. Migrate to:
- **Backend**: FastAPI — REST API serving rankings data
- **Frontend**: Vite + React — full UI ownership, full CSS control

### What Is Kept
- `backend/utils/data_loader.py` — ported unchanged, all tests pass
- `backend/utils/rankings.py` — ported unchanged, all tests pass
- `backend/utils/constants.py` — ported unchanged
- All 43 unit tests — carry over to `tests/`
- `data/players/` CSV files — unchanged
- `data/rankings/default.json` — unchanged

### What Is Scrapped
- `app/main.py` and all Streamlit pages
- `.streamlit/config.toml`
- All CSS injection and JavaScript workarounds

### Alternatives Considered
| Option | Verdict |
|--------|---------|
| Keep Streamlit, accept limitations | Rejected — too many layout blockers |
| Streamlit + custom component | Rejected — high complexity, still limited |
| Flask + vanilla HTML/JS | Rejected — FastAPI is more modern, better DX |
| Reflex | Rejected — less mature, smaller community |
| FastAPI + React (Vite) | **Selected** |

### Consequences
**Positive:**
- Full CSS control — any layout, any color, any interaction
- Real drag-and-drop possible in future
- Clean separation of concerns: Python handles data, React handles UI
- Existing Python utility layer is fully preserved and tested

**Negative:**
- Two processes to run (backend + frontend dev server)
- JavaScript required for frontend — new language in the stack
- More initial setup than Streamlit

---

## ADR-007: Deploy to AWS via EC2 + nginx + systemd

**Date**: 2026-04-14
**Status**: Accepted

### Context
App is feature-complete for War Room and Draft Mode. Publishing to AWS
enables access from any device — specifically mobile on draft day —
without needing a running MacBook.

### Decision
Deploy to existing EC2 t3.micro instance behind nginx. Serve Vite `dist/`
as static files. Reverse-proxy `/api/*` to uvicorn on port 8000. Manage
the uvicorn process with systemd. Use Cognito for authentication.
All infrastructure defined in CDK.

### Rationale
- EC2 already running 24/7 — no new infrastructure cost
- nginx + systemd is simple, debuggable, proven pattern
- No containerisation overhead for a single-user personal tool
- CDK ensures everything is reproducible — no manual console steps

### Alternatives Considered
| Option | Verdict |
|--------|---------|
| ECS Fargate | Rejected — over-engineered for single-user tool |
| App Runner | Rejected — unnecessary abstraction, EC2 already exists |
| Elastic Beanstalk | Rejected — more managed than needed |
| EC2 + nginx + systemd | **Selected** |

### Consequences
- Deployments are `git pull` + `./scripts/deploy.sh` on the EC2
- CDK manages S3 bucket and IAM role only — not the EC2 instance itself
- SSL via certbot, already configured on this EC2
- Single-user only — no multi-user support in this architecture (see Phase 3)

---

## ADR-008: S3 Storage Backend with StorageBackend Abstraction

**Date**: 2026-04-14
**Status**: Accepted

### Context
Rankings JSON files live on the local filesystem in development. In a
deployed EC2 environment, files on disk are lost if the instance is
rebuilt, and local file state creates friction during deployments. A
storage abstraction is needed that allows local dev to continue using
the filesystem while production reads/writes from S3.

### Decision
Introduce a `StorageBackend` ABC in `backend/utils/storage.py` with two
implementations: `LocalStorage` (preserves all existing filesystem
behaviour) and `S3Storage` (boto3, EC2 IAM instance role auth). A
`get_storage()` factory selects the implementation via the
`STORAGE_BACKEND` environment variable at startup.

### Rationale
- All 49 existing tests continue to pass against `LocalStorage` unchanged
- S3 data survives EC2 rebuilds, reboots, and redeployments
- IAM instance role is the correct AWS-native credential pattern — no
  credentials in code, env files, or the repository
- The access pattern (load once on page load, write on explicit user save)
  is ideal for S3 — latency is imperceptible
- `moto` allows full S3Storage test coverage without real AWS calls

### Alternatives Considered
| Option | Verdict |
|--------|---------|
| Keep files on EC2, manual backups | Rejected — fragile, not automated |
| EFS mounted filesystem | Rejected — over-engineered for small JSON blobs |
| DynamoDB | Rejected — ADR-002 established JSON as the data format |
| S3 with StorageBackend abstraction | **Selected** |

### Consequences
- `boto3`, `python-jose[cryptography]`, `httpx` added to `requirements.txt`
- `moto[s3]` added to `requirements-dev.txt`
- `rankings.py` functions receive a `storage: StorageBackend` parameter
- All existing tests refactored to pass `LocalStorage(tmp_path)` fixture —
  no logic changes
- S3 bucket structure mirrors local: `rankings/default.json`,
  `rankings/seed.json`, `rankings/{name}.json`
- `StorageBackend` is designed to support future user-scoped keys
  (`rankings/{user_id}/default.json`) if multi-user is ever added

---

## ADR-009: Draggable Tier Boundaries

**Date**: 2026-04-15
**Status**: Accepted

### Context
Tier boundaries are fixed at seeding time. Moving a player between tiers
requires repeatedly pressing ▲▼ until they cross the boundary — slow and
tedious when prepping multiple positions before a draft.

ADR-001 (Streamlit era) stated "no drag-and-drop" but that concerned
full player reordering via drag in Streamlit, which is now irrelevant
since the project migrated to React (ADR-006). Tier boundary dragging
is a distinct, narrower affordance: a single vertical axis, snapping to
discrete rows, affecting only two adjacent tiers.

### Decision
Add draggable separator lines between adjacent tier groups in War Room
mode. Dragging down moves the first player of the lower tier into the
upper tier. Dragging up moves the last player of the upper tier into the
lower tier. Movement snaps one player at a time.

### Rationale
- Tier boundaries are the most frequently adjusted aspect of rankings
- One-player-at-a-time snapping keeps the operation atomic and reversible
- Only the `tier` field changes — `position_rank` is untouched
- Touch support is critical for mobile draft-day use

### Constraints
- Drag-and-drop for player reordering remains out of scope (▲▼ buttons stay)
- Tier boundary drag is limited to War Room mode only (hidden in Draft Mode)
- Empty tiers are prevented — separator stops when a tier has one player

### Consequences
- New `set_player_tier()` utility function + `PUT /{position}/{rank}/tier` endpoint
- New `TierSeparator` React component with mouse and touch support
- No data model changes — `tier` field already exists on every player

---

## Template for New Decisions

```markdown
## ADR-XXX: Title

**Date**: YYYY-MM-DD
**Status**: Proposed/Accepted/Deprecated/Superseded

### Context
### Decision
### Rationale
### Alternatives Considered
### Consequences
```

## Key Principles

1. **No approximations**: All player data from verified CSV exports
2. **Two environments**: local dev (LocalStorage, no auth) / production (S3, Cognito JWT)
3. **Rankings-only UI**: Historical data is seed infrastructure, not a feature
4. **Graceful degradation**: Missing files warn the user, never crash
5. **Full UI control**: React owns the frontend — no CSS framework fighting
6. **Automate everything**: CDK, deploy scripts, systemd — no manual console steps
7. **No credentials in code**: IAM roles and public Cognito IDs only
