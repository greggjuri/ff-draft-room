# PRP-009: AWS Deployment

**Created**: 2026-04-14
**Initial**: `initials/09-init-aws-deploy.md`
**Status**: Complete

---

## Overview

### Problem Statement
FF Draft Room is feature-complete for War Room, Draft Mode, and Search. It runs
only on the local MacBook. On draft day, accessing the app from a phone or tablet
requires the MacBook to be running and reachable — impractical in most draft
environments.

### Proposed Solution
Deploy to the existing EC2 t3.micro instance at `ff.jurigregg.com`. Serve the
React build as static files via nginx. Reverse-proxy `/api/*` to uvicorn managed
by systemd. Migrate rankings data from local filesystem to S3 via a storage
abstraction layer. Protect all routes with Cognito JWT authentication (reusing
the existing automation-platform User Pool). Infrastructure defined in CDK.

### Success Criteria
- [ ] `StorageBackend` abstraction with `LocalStorage` and `S3Storage` implementations
- [ ] All 49 existing tests pass unchanged against `LocalStorage`
- [ ] New `test_storage.py` tests cover both backends (S3 via moto mocks)
- [ ] Cognito JWT middleware rejects unauthenticated requests with 401
- [ ] Frontend login page renders with correct design tokens
- [ ] Auth token attached to all API `fetch()` calls
- [ ] CDK stack creates S3 bucket + IAM role + instance profile
- [ ] `deploy.sh` builds frontend, installs backend, restarts services
- [ ] Health check passes at `https://ff.jurigregg.com/health`
- [ ] Full War Room + Draft Mode + Search functional at `https://ff.jurigregg.com`
- [ ] All tests pass: `pytest tests/ -q`
- [ ] Lint clean: `ruff check backend/ tests/`
- [ ] Frontend builds: `cd frontend && npx vite build`

---

## Context

### Related Documentation
- `docs/PLANNING.md` — Architecture overview, data model
- `docs/DECISIONS.md` — ADR-002 (JSON persistence), ADR-003 (CSV data source), ADR-006 (FastAPI + React)
- `initials/09-init-aws-deploy.md` — ADR-007 (EC2 + nginx + S3), ADR-008 (S3 Storage Backend)

### Dependencies
- **Required**: All Phase 1b features complete (PRP 04–08)
- **External**: EC2 instance running, Cognito User Pool exists, DNS configured, certbot SSL active

### Placeholder Values
| Placeholder | Value |
|---|---|
| `<EC2_INSTANCE_ID>` | `i-04c64860b83289813` |
| `<COGNITO_USER_POOL_ID>` | `us-east-1_znsMeTGDS` |
| `<COGNITO_CLIENT_ID>` | `2hl97stgnf1g3vbhol28v8fg5e` |
| `<COGNITO_REGION>` | `us-east-1` |
| `<S3_BUCKET>` | `ff-draft-room-data` |

### Files to Modify/Create
```
# NEW — Backend
backend/utils/storage.py                  # StorageBackend abstraction
backend/middleware/__init__.py            # Package init
backend/middleware/auth.py                # Cognito JWT verification

# NEW — CDK
cdk/app.py                               # CDK app entry point
cdk/ff_deploy_stack.py                    # S3 + IAM stack
cdk/requirements.txt                     # CDK dependencies
cdk/cdk.json                             # CDK config with EC2 instance ID

# NEW — Frontend auth
frontend/src/auth/cognito.js             # CognitoUserPool setup + helpers
frontend/src/auth/AuthContext.jsx         # React auth context provider
frontend/src/components/LoginPage.jsx     # Login form
frontend/src/components/LoginPage.css     # Login styles

# NEW — Deployment
scripts/deploy.sh                         # EC2 deploy script
scripts/cdk-bootstrap.sh                  # One-time CDK deploy
scripts/nginx.conf.template              # nginx site config
scripts/ff-draft-room.service            # systemd unit file
env.production.example                   # Template for EC2 .env.production
frontend/.env.production                 # Vite Cognito env vars

# NEW — Tests
tests/test_storage.py                    # LocalStorage + S3Storage (moto) tests

# MODIFIED
backend/utils/rankings.py                # Replace Path I/O → StorageBackend
backend/main.py                          # Init storage singleton, CORS update
backend/routers/rankings.py              # Inject storage, apply auth dependency
frontend/src/App.jsx                     # Wrap in AuthContext
frontend/src/api/rankings.js             # Add Authorization header
frontend/package.json                    # Add amazon-cognito-identity-js
requirements.txt                         # Add boto3, python-jose, httpx
.gitignore                               # Add .env.production, cdk-outputs.json
tests/conftest.py                        # Add storage fixture

# DOC UPDATES
docs/DECISIONS.md                        # Add ADR-007, ADR-008
docs/PLANNING.md                         # Update architecture, constraints
docs/TASK.md                             # Update status
```

---

## Technical Specification

### Storage Abstraction (`backend/utils/storage.py`)

Abstract base class with five methods: `read`, `write`, `delete`, `exists`, `list_keys`.
Two implementations:

```python
class StorageBackend(ABC):
    def read(self, key: str) -> dict[str, Any] | None: ...
    def write(self, key: str, data: dict[str, Any]) -> None: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
    def list_keys(self, prefix: str = "") -> list[str]: ...

class LocalStorage(StorageBackend):
    # Wraps current Path-based file I/O. Used in dev + tests.

class S3Storage(StorageBackend):
    # boto3 s3 client. Auth via IAM instance role. Used in prod.

def get_storage() -> StorageBackend:
    # Factory. STORAGE_BACKEND env var selects implementation.
```

### Rankings Utility Refactor (`backend/utils/rankings.py`)

All functions that currently accept `rankings_dir: Path | None` gain a
`storage: StorageBackend | None` parameter instead. Internal `Path` file
operations replaced with `storage.read()` / `storage.write()` / etc.

Key mapping: `default.json` → key `"default.json"`, `seed.json` → key
`"seed.json"`, `{name}.json` → key `"{name}.json"`.

Default behavior preserved: if `storage` is `None`, instantiate
`LocalStorage(RANKINGS_DIR)` for backward compatibility.

### Auth Middleware (`backend/middleware/auth.py`)

- Fetches Cognito JWKS once, caches in module-level variable
- Verifies RS256 JWT on every request via `python-jose`
- Applied as router-level dependency on all rankings routes
- `/health` endpoint remains unauthenticated

### Frontend Auth (`frontend/src/auth/`)

- `cognito.js`: Initializes `CognitoUserPool` from `amazon-cognito-identity-js`,
  exports `login(email, password)`, `logout()`, `getToken()`, `getCurrentUser()`
- `AuthContext.jsx`: React context providing `{ user, token, login, logout, loading }`.
  On mount, checks for existing session via `getCurrentUser()`.
- `App.jsx`: Wraps in `<AuthProvider>`. If not authenticated, render `<LoginPage>`.
  If authenticated, render existing app tree.

### API Auth Headers (`frontend/src/api/rankings.js`)

The `request()` helper gains an `Authorization: Bearer <token>` header on
every call via `getToken()` imported from `cognito.js`.

### CORS Update (`backend/main.py`)

Add `https://ff.jurigregg.com` to `allow_origins` alongside the existing
`http://localhost:5173`.

---

## Implementation Steps

### Step 1: Storage Abstraction
**Files**: `backend/utils/storage.py`, `tests/test_storage.py`, `tests/conftest.py`

Create `StorageBackend` ABC with `LocalStorage` and `S3Storage` implementations
as specified in the init spec. Add `storage` fixture to `conftest.py`.
Write `test_storage.py` with tests for:
- `LocalStorage`: read/write/delete/exists/list_keys (happy path + missing key)
- `S3Storage`: all methods mocked with `moto`
- `get_storage()`: env var switching

**Validation**:
```bash
pytest tests/test_storage.py -v
ruff check backend/utils/storage.py
```
- [ ] All storage tests pass
- [ ] No lint errors

---

### Step 2: Refactor Rankings to Use StorageBackend
**Files**: `backend/utils/rankings.py`, `tests/test_rankings.py`, `tests/test_profile_management.py`

Replace all `rankings_dir: Path | None` parameters with
`storage: StorageBackend | None`. Replace `Path` file I/O with storage method
calls. Default `storage=None` instantiates `LocalStorage(RANKINGS_DIR)` for
backward compat.

Update all test files to pass `LocalStorage(tmp_path / "rankings")` fixture.
The `conftest.py` fixture handles this — test logic should not change.

**Validation**:
```bash
pytest tests/test_rankings.py tests/test_profile_management.py -v
```
- [ ] All 41 existing rankings tests pass
- [ ] No test logic changes required

---

### Step 3: Wire Storage into Router and App
**Files**: `backend/main.py`, `backend/routers/rankings.py`

In `main.py`:
- Import `get_storage` and create singleton: `app.state.storage = get_storage()`
- Add `https://ff.jurigregg.com` to CORS origins

In `routers/rankings.py`:
- Access storage via `request.app.state.storage` or pass through to utility
  functions. Update `get_profile()` and all write endpoints to use storage.

**Validation**:
```bash
uvicorn backend.main:app --reload
curl http://localhost:8000/health
curl http://localhost:8000/api/rankings
```
- [ ] Backend starts
- [ ] All endpoints respond correctly

---

### Step 4: Cognito JWT Auth Middleware
**Files**: `backend/middleware/__init__.py`, `backend/middleware/auth.py`,
`backend/routers/rankings.py`, `requirements.txt`

Create `auth.py` with `require_auth` dependency as specified in init spec.
Add `python-jose[cryptography]` and `httpx` to `requirements.txt`.
Apply `Depends(require_auth)` at router level in `rankings.py`.
`/health` stays unprotected (it's on `app`, not the router).

**Validation**:
```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
curl http://localhost:8000/health           # 200
curl http://localhost:8000/api/rankings     # 401
```
- [ ] Health returns 200 without token
- [ ] Rankings returns 401 without token

---

### Step 5: Frontend Auth Integration
**Files**: `frontend/src/auth/cognito.js`, `frontend/src/auth/AuthContext.jsx`,
`frontend/src/components/LoginPage.jsx`, `frontend/src/components/LoginPage.css`,
`frontend/src/App.jsx`, `frontend/src/api/rankings.js`,
`frontend/package.json`, `frontend/.env.production`

1. `npm install amazon-cognito-identity-js`
2. Create `cognito.js` — pool setup, login/logout/getToken helpers
3. Create `AuthContext.jsx` — React context with session check on mount
4. Create `LoginPage.jsx` + `.css` — email/password form, design tokens
   matching War Room (dark navy, Honolulu Blue, monospace)
5. Update `App.jsx` — wrap in `<AuthProvider>`, conditional rendering
6. Update `api/rankings.js` — add `Authorization: Bearer` header to
   all requests via `getToken()` import
7. Create `frontend/.env.production` with Vite Cognito env vars
8. Create `frontend/.env.local` (gitignored) with same vars for local dev

**Validation**:
```bash
cd frontend && npm run build
```
- [ ] Build succeeds with no errors
- [ ] Login page renders at localhost:5173 (backend auth blocks API until login)

---

### Step 6: CDK Stack
**Files**: `cdk/app.py`, `cdk/ff_deploy_stack.py`, `cdk/requirements.txt`, `cdk/cdk.json`

Create CDK app per init spec:
- S3 bucket `ff-draft-room-data` with versioning, public access blocked,
  90-day noncurrent version lifecycle
- IAM role with S3 access scoped to bucket
- Instance profile wrapping the role
- Outputs: `BucketName`, `InstanceProfileArn`

`cdk.json` context includes `ec2InstanceId: i-04c64860b83289813`.

**Validation**:
```bash
cd cdk && pip install -r requirements.txt
python -c "from ff_deploy_stack import FfDeployStack; print('Import OK')"
```
- [ ] Stack module imports without error

---

### Step 7: Deployment Scripts
**Files**: `scripts/deploy.sh`, `scripts/cdk-bootstrap.sh`,
`scripts/nginx.conf.template`, `scripts/ff-draft-room.service`,
`env.production.example`

Create all deployment artifacts per init spec:
- `deploy.sh` — git pull, pip install, npm build, rsync dist, systemctl restart
- `cdk-bootstrap.sh` — CDK deploy + IAM profile attach to EC2
- `nginx.conf.template` — HTTPS, static files, API proxy, SPA fallback
- `ff-draft-room.service` — systemd unit, reads `.env.production`
- `env.production.example` — template with placeholder comments

Note: `uvicorn` invocation in the systemd service uses `backend.main:app`
(dotted import) since the working directory is the repo root, not `backend/`.

**Validation**:
```bash
bash -n scripts/deploy.sh
bash -n scripts/cdk-bootstrap.sh
```
- [ ] Scripts parse without syntax errors
- [ ] All placeholder values substituted correctly

---

### Step 8: Update .gitignore and Dependencies
**Files**: `.gitignore`, `requirements.txt`

Add to `.gitignore`:
```
.env.production
cdk/cdk-outputs.json
cdk/cdk.out/
frontend/.env.local
```

Add to `requirements.txt`:
```
boto3>=1.28.0
python-jose[cryptography]>=3.3.0
httpx>=0.27.0
```

Create `requirements-dev.txt`:
```
moto[s3]>=4.0.0
```

**Validation**:
```bash
pip install -r requirements.txt
```
- [ ] All dependencies install cleanly

---

### Step 9: Documentation Updates
**Files**: `docs/DECISIONS.md`, `docs/PLANNING.md`, `docs/TASK.md`

- Add ADR-007 (EC2 + nginx + S3 deployment) and ADR-008 (S3 Storage Backend)
  to `DECISIONS.md`
- Update `PLANNING.md` architecture diagram to show nginx → static + API proxy,
  S3 storage, and Cognito auth. Update constraints to note deployment option.
- Update `TASK.md` to mark 09 as complete

---

### Step 10: Final Integration Check
**Commands**:
```bash
pytest tests/ --cov=backend --cov-report=term-missing
ruff check backend/ tests/
cd frontend && npx vite build
```

**Validation**:
- [ ] All tests pass (49 existing + new storage tests)
- [ ] Coverage ≥ 80% for `backend/utils/`
- [ ] Zero lint errors
- [ ] Frontend builds cleanly
- [ ] No debug output or `print()` left in code

---

## Testing Requirements

### Unit Tests — `tests/test_storage.py` (NEW)
```
test_local_write_and_read             — round-trip write then read
test_local_read_missing_key           — returns None for nonexistent key
test_local_delete                     — deletes existing key
test_local_delete_missing             — no error on missing key
test_local_exists_true                — key exists after write
test_local_exists_false               — key does not exist before write
test_local_list_keys                  — lists all keys
test_local_list_keys_with_prefix      — filters by prefix
test_s3_write_and_read                — moto mock round-trip
test_s3_read_missing_key              — returns None
test_s3_delete                        — deletes object
test_s3_exists                        — head_object check
test_s3_list_keys                     — list_objects_v2
test_get_storage_default              — returns LocalStorage
test_get_storage_s3_env               — returns S3Storage when env set
```

### Existing Tests — Zero Changes to Logic
All 49 tests pass via `LocalStorage(tmp_path)` fixture injection.

### Manual Browser Tests
- [ ] Login page renders with dark navy + Honolulu Blue design
- [ ] Login with Cognito credentials → redirects to War Room
- [ ] Invalid credentials → error message on login page
- [ ] All War Room operations work post-login
- [ ] Draft Mode toggle works
- [ ] Search works
- [ ] Page refresh maintains session (Cognito tokens in localStorage)

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `pytest tests/ -q` | All tests pass (49 + ~15 new) | ☐ |
| 2 | `ruff check backend/ tests/` | Zero errors | ☐ |
| 3 | `cd frontend && npx vite build` | Build succeeds | ☐ |
| 4 | Start backend: `uvicorn backend.main:app --reload` | Starts at :8000 | ☐ |
| 5 | `curl http://localhost:8000/health` | `{"status":"ok"}` | ☐ |
| 6 | `curl http://localhost:8000/api/rankings` | 401 Unauthorized | ☐ |
| 7 | Start frontend: `cd frontend && npm run dev` | Starts at :5173 | ☐ |
| 8 | Open localhost:5173 | Login page renders | ☐ |
| 9 | Login with Cognito credentials | War Room loads | ☐ |
| 10 | Reorder player + Save | Save succeeds | ☐ |
| 11 | `./scripts/cdk-bootstrap.sh i-04c64860b83289813` | Stack deploys, profile attached | ☐ |
| 12 | SSH to EC2, run `./scripts/deploy.sh` | Deploy completes, health check passes | ☐ |
| 13 | `curl https://ff.jurigregg.com/health` | `{"status":"ok"}` | ☐ |
| 14 | Open `https://ff.jurigregg.com` in browser | Login → War Room works | ☐ |
| 15 | Save rankings, verify in S3: `aws s3 ls s3://ff-draft-room-data/rankings/` | Files present | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| 401 Unauthorized | Missing/invalid/expired JWT | FastAPI returns 401, frontend redirects to login |
| JWKS fetch failure | Network issue on first request | `httpx.get` raises → 500, logged. JWKS cached after first success |
| S3 NoSuchKey | Reading non-existent profile | `S3Storage.read()` returns `None` (same as `LocalStorage`) |
| S3 access denied | IAM role misconfigured | boto3 raises `ClientError` → 500, logged |
| Cognito login failure | Wrong credentials | `amazon-cognito-identity-js` callback error → shown on login form |
| `STORAGE_BACKEND` invalid | Typo in env var | `get_storage()` defaults to local |
| Missing `S3_BUCKET` env var | `.env.production` not configured | `KeyError` on startup → fast fail with clear error |
| Missing Cognito env vars | `.env.production` not configured | `KeyError` on import → fast fail with clear error |

---

## Open Questions

None — all questions resolved in the init spec:
- EC2 instance identified
- Cognito pool reused from automation-platform
- SSL and DNS assumed pre-configured
- No CI/CD — manual deploy via `deploy.sh`

---

## Rollback Plan

### Code rollback
```bash
git revert <commit>
pytest tests/ -q          # verify tests pass
uvicorn backend.main:app --reload  # verify app starts
```

### Infrastructure rollback
```bash
cd cdk
CDK_ACCOUNT=<account> cdk destroy FfDeployStack
# S3 bucket must be emptied first if it contains data
```

### EC2 rollback
```bash
sudo systemctl stop ff-draft-room
sudo systemctl disable ff-draft-room
sudo rm /etc/systemd/system/ff-draft-room.service
sudo rm /etc/nginx/sites-enabled/ff-draft-room
sudo rm /etc/nginx/sites-available/ff-draft-room
sudo systemctl reload nginx
```

Local development continues to work unchanged — `STORAGE_BACKEND` defaults
to `local`, auth middleware is only active when Cognito env vars are set.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 9 | Init spec is exhaustive — exact file contents, deployment sequence, placeholder values provided |
| Feasibility | 9 | Standard patterns: S3 storage abstraction, Cognito JWT, nginx reverse proxy. All pieces proven in automation-platform |
| Completeness | 9 | All files, tests, deployment scripts, and env configs specified. Only gap: no automated integration test for auth flow (manual browser test covers it) |
| Alignment | 8 | ADR-007 and ADR-008 explicitly enable this. ADR-002 (JSON persistence) preserved — S3 stores the same JSON files. Slight tension with PLANNING.md "local only" constraint, but this ADR supersedes that for production |
| **Average** | **8.75** | Ready for execution |

---

## Notes

### Execution Phases
This PRP is executed in phases, not all on the dev machine:
- **Phase 1** (Steps 1–10): All code, tests, and build validation on Debian dev machine
- **Phase 2** (CDK): Run `cdk-bootstrap.sh` from Debian to create AWS resources
- **Phase 3** (EC2 setup): SSH to EC2, clone repo, create `.env.production`
- **Phase 4** (Deploy): Run `deploy.sh` on EC2
- **Phase 5** (Verify): Browser testing at `https://ff.jurigregg.com`

### Import Note for systemd
The systemd service runs `uvicorn backend.main:app` from the repo root directory.
This means `backend/main.py`'s `sys.path.insert(0, str(Path(__file__).parent))`
correctly adds `backend/` to the path, and all `from utils.*` imports resolve.

### Local Dev Unchanged
Developers (i.e., you, the single user) continue to run `uvicorn backend.main:app
--reload` and `npm run dev` exactly as before. No env vars required — storage
defaults to local, and auth middleware is only activated when Cognito env vars
are present. To enable auth locally for testing, create `frontend/.env.local`
with the Cognito vars and set the backend Cognito env vars.

### Auth Middleware Toggle
When `COGNITO_USER_POOL_ID` is not set in the environment, the auth middleware
should be skipped so that local development works without Cognito. Check for
this in `main.py` when applying the router dependency.
