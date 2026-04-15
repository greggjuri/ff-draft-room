# 09-init-aws-deploy.md — AWS Deployment

## Overview

Deploy FF Draft Room to AWS so it is accessible from any device at
`ff.jurigregg.com`. The app runs on the existing EC2 t3.micro instance.
Rankings data migrates from local JSON files to S3. Auth uses the existing
Cognito User Pool from the automation-platform project.

Infrastructure is defined entirely in CDK — no manual console steps.

---

## Placeholders

These values are provided at PRP execution time and substituted wherever
they appear throughout the generated code and config files:

| Placeholder | Description |
|---|---|
| `<EC2_INSTANCE_ID>` | EC2 instance ID, e.g. `i-XXXXXXXXXXXXXXXXX` |
| `<COGNITO_USER_POOL_ID>` | Cognito User Pool ID, e.g. `us-east-1_XXXXXXXXX` |
| `<COGNITO_CLIENT_ID>` | Cognito App Client ID, e.g. `XXXXXXXXXXXXXXXXXXXXXXXXXX` |
| `<COGNITO_REGION>` | AWS region, e.g. `us-east-1` |
| `<S3_BUCKET>` | Always `ff-draft-room-data` (hardcoded in CDK stack) |

---

## Architecture Decision Records

### ADR-007: Publish to AWS via EC2 + nginx + S3

**Date**: 2026-04-14
**Status**: Accepted

#### Context
App is feature-complete for War Room and Draft Mode. Publishing enables
access from mobile devices on draft day without running a MacBook.

#### Decision
Deploy to existing EC2 t3.micro behind nginx. Serve Vite `dist/` as static
files. Reverse-proxy `/api/*` to uvicorn on port 8000. Manage process with
systemd. Use existing Cognito User Pool for auth.

#### Rationale
- EC2 already running 24/7, no new infrastructure cost
- nginx + systemd is simple, debuggable, proven pattern
- No containerisation needed for a single-user personal tool

#### Alternatives Considered
| Option | Verdict |
|--------|---------|
| ECS Fargate | Rejected — over-engineered for single-user tool |
| App Runner | Rejected — unnecessary abstraction given EC2 already exists |
| EC2 + nginx + systemd | **Selected** |

#### Consequences
- Deployments are a `git pull` + build + systemctl restart
- CDK manages only the S3 bucket and IAM role, not the EC2 itself
- SSL via certbot (already configured on this EC2)

---

### ADR-008: S3 Storage Backend for Rankings Data

**Date**: 2026-04-14
**Status**: Accepted

#### Context
Rankings JSON files currently live on the local filesystem. In a deployed
environment, files on EC2 are ephemeral and not portable. A storage
abstraction allows local dev to continue using the filesystem while
production reads/writes from S3.

#### Decision
Introduce a `StorageBackend` abstraction in `backend/utils/storage.py`.
`STORAGE_BACKEND` env var selects the implementation at startup.
`LocalStorage` preserves all existing behaviour. `S3Storage` uses boto3.
EC2 authenticates to S3 via IAM instance role — no credentials in code or
environment files.

#### Rationale
- All 49 existing tests continue to pass against `LocalStorage` unchanged
- S3 data survives EC2 rebuilds and deployments
- IAM instance role is the correct AWS-native credential pattern
- Access pattern (load once, save on explicit user action) is ideal for S3

#### Alternatives Considered
| Option | Verdict |
|--------|---------|
| Keep files on EC2, back up manually | Rejected — fragile |
| EFS mounted filesystem | Rejected — over-engineered for small JSON blobs |
| DynamoDB | Rejected — ADR-002 established JSON as persistence format |
| S3 with storage abstraction | **Selected** |

#### Consequences
- `boto3` added to `requirements.txt`
- Rankings util functions receive a `storage` parameter (dependency injection)
- Existing function signatures unchanged for tests
- Local dev default remains `STORAGE_BACKEND=local`

---

## What Gets Built

### 1. CDK Stack (`cdk/`)

New file `cdk/ff_deploy_stack.py`. Deployed as its own CDK app separate
from any automation-platform stacks.

**Resources**:

```
S3 Bucket: ff-draft-room-data
  - Versioning: enabled
  - Public access: fully blocked
  - Lifecycle: noncurrent version expiry after 90 days

IAM Role: ff-draft-room-ec2-role
  - Trust policy: EC2 service principal
  - Inline policy: s3:GetObject, s3:PutObject, s3:DeleteObject,
    s3:ListBucket scoped to ff-draft-room-data/*

IAM Instance Profile: ff-draft-room-instance-profile
  - Wraps the role above
  - Attached to existing EC2 instance (by instance ID, passed as CDK
    context variable)
```

**CDK app entry** (`cdk/app.py`):
```python
import aws_cdk as cdk
import os
from ff_deploy_stack import FfDeployStack

app = cdk.App()
FfDeployStack(app, "FfDeployStack", env=cdk.Environment(
    account=os.environ["CDK_ACCOUNT"],
    region=os.environ.get("CDK_REGION", "us-east-1"),
))
app.synth()
```

**CDK context** (`cdk/cdk.json`):
```json
{
  "app": "python app.py",
  "context": {
    "ec2InstanceId": "<EC2_INSTANCE_ID>"
  }
}
```

**CDK outputs** (printed after `cdk deploy`):
- `BucketName` — S3 bucket name
- `InstanceProfileArn` — used in `cdk-bootstrap.sh` to attach to EC2

**CDK requirements** (`cdk/requirements.txt`):
```
aws-cdk-lib>=2.0.0
constructs>=10.0.0
```

---

### 2. Storage Abstraction (`backend/utils/storage.py`)

New file. All file I/O for rankings data routes through this module.

```python
from __future__ import annotations
import json, os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

class StorageBackend(ABC):
    @abstractmethod
    def read(self, key: str) -> dict[str, Any] | None: ...
    @abstractmethod
    def write(self, key: str, data: dict[str, Any]) -> None: ...
    @abstractmethod
    def delete(self, key: str) -> None: ...
    @abstractmethod
    def exists(self, key: str) -> bool: ...
    @abstractmethod
    def list_keys(self, prefix: str = "") -> list[str]: ...

class LocalStorage(StorageBackend):
    """Current filesystem behaviour. Used in local dev and all tests."""
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        base_dir.mkdir(parents=True, exist_ok=True)

    def read(self, key: str) -> dict[str, Any] | None:
        path = self.base_dir / key
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def write(self, key: str, data: dict[str, Any]) -> None:
        (self.base_dir / key).write_text(json.dumps(data, indent=2))

    def delete(self, key: str) -> None:
        path = self.base_dir / key
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return (self.base_dir / key).exists()

    def list_keys(self, prefix: str = "") -> list[str]:
        return [p.name for p in self.base_dir.glob(f"{prefix}*.json")]

class S3Storage(StorageBackend):
    """Production S3 backend. Auth via EC2 IAM instance role."""
    def __init__(self, bucket: str, prefix: str = "rankings/"):
        import boto3
        self.client = boto3.client("s3")
        self.bucket = bucket
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def read(self, key: str) -> dict[str, Any] | None:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=self._key(key))
            return json.loads(obj["Body"].read())
        except self.client.exceptions.NoSuchKey:
            return None

    def write(self, key: str, data: dict[str, Any]) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key(key),
            Body=json.dumps(data, indent=2),
            ContentType="application/json",
        )

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=self._key(key))

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._key(key))
            return True
        except Exception:
            return False

    def list_keys(self, prefix: str = "") -> list[str]:
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=f"{self.prefix}{prefix}",
        )
        full_prefix = self.prefix
        return [
            obj["Key"].removeprefix(full_prefix)
            for obj in response.get("Contents", [])
        ]

def get_storage() -> StorageBackend:
    """Factory. Reads STORAGE_BACKEND env var. Default: local."""
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend == "s3":
        bucket = os.environ["S3_BUCKET"]
        return S3Storage(bucket)
    base_dir = Path(os.getenv("RANKINGS_DIR", "data/rankings"))
    return LocalStorage(base_dir)
```

---

### 3. Rankings Utility Updates (`backend/utils/rankings.py`)

All direct `Path` file read/write calls replaced with `StorageBackend` calls.
The storage instance is passed as a parameter to each function (dependency
injection — testable, no global state).

**Signature changes** (all functions gain `storage: StorageBackend` param):
```python
def load_or_seed(storage: StorageBackend, ...) -> dict
def save_profile(storage: StorageBackend, profile: dict) -> None
def list_profiles(storage: StorageBackend) -> list[str]
def save_as(storage: StorageBackend, name: str, profile: dict) -> None
def load_profile(storage: StorageBackend, name: str) -> dict
def reset_profile(storage: StorageBackend, ...) -> dict
def set_default(storage: StorageBackend, profile: dict) -> None
```

**Key mapping** (what was a `Path` filename is now a storage `key`):
```
default.json → "default.json"
seed.json    → "seed.json"
{name}.json  → "{name}.json"
```

**In `backend/main.py`**: create storage singleton at startup:
```python
from utils.storage import get_storage
storage = get_storage()
app.state.storage = storage
```

**In `backend/routers/rankings.py`**: access via `request.app.state.storage`.

**Tests**: all 49 existing tests use `LocalStorage(tmp_path)` passed directly
— zero changes to test logic. Add `conftest.py` fixture:
```python
@pytest.fixture
def storage(tmp_path):
    return LocalStorage(tmp_path / "rankings")
```

---

### 4. Cognito JWT Auth Middleware (`backend/middleware/auth.py`)

New file. All API endpoints require a valid Cognito JWT — this is a
private personal tool, no public access.

```python
from __future__ import annotations
import os, httpx
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

REGION = os.environ["COGNITO_REGION"]
USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]
JWKS_URL = (
    f"https://cognito-idp.{REGION}.amazonaws.com"
    f"/{USER_POOL_ID}/.well-known/jwks.json"
)

_jwks_cache: dict | None = None

def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        _jwks_cache = httpx.get(JWKS_URL).json()
    return _jwks_cache

bearer = HTTPBearer()

def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
) -> dict:
    token = credentials.credentials
    try:
        jwks = _get_jwks()
        header = jwt.get_unverified_header(token)
        key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except (JWTError, StopIteration) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
```

**Dependency applied in `routers/rankings.py`** — all routes (GET and write):
```python
from middleware.auth import require_auth

router = APIRouter(dependencies=[Depends(require_auth)])
```

**New dependencies** in `requirements.txt`:
```
python-jose[cryptography]
httpx
```

---

### 5. nginx Configuration

Template stored at `scripts/nginx.conf.template` in the repo.
Deploy script copies to `/etc/nginx/sites-available/ff-draft-room` and
symlinks to `sites-enabled/` on first deploy.

```nginx
server {
    listen 80;
    server_name ff.jurigregg.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name ff.jurigregg.com;

    ssl_certificate     /etc/letsencrypt/live/ff.jurigregg.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ff.jurigregg.com/privkey.pem;

    root /var/www/ff-draft-room/dist;
    index index.html;

    # React SPA — all non-API routes serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API to uvicorn
    location /api/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    # Health check (unauthed, used by deploy script)
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

### 6. systemd Service Unit

File: `scripts/ff-draft-room.service` (checked into repo)

```ini
[Unit]
Description=FF Draft Room FastAPI Backend
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/ff-draft-room
EnvironmentFile=/home/ec2-user/ff-draft-room/.env.production
ExecStart=/home/ec2-user/ff-draft-room/.venv/bin/uvicorn \
    backend.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Deploy script installs to `/etc/systemd/system/` on first deploy.

---

### 7. Production Environment File

`.env.production` lives on the EC2 instance at `/home/ec2-user/ff-draft-room/`.
It is **not** in the repo (add to `.gitignore`).

Template checked in as `env.production.example`:
```bash
# Storage
STORAGE_BACKEND=s3
S3_BUCKET=ff-draft-room-data

# Cognito — reuse automation-platform User Pool
COGNITO_USER_POOL_ID=<COGNITO_USER_POOL_ID>
COGNITO_REGION=<COGNITO_REGION>

# App
RANKINGS_DIR=data/rankings   # only used when STORAGE_BACKEND=local
```

Local dev `.env` (already gitignored):
```bash
STORAGE_BACKEND=local
RANKINGS_DIR=data/rankings
```

---

### 8. Frontend Auth Integration

Mirrors the automation-platform frontend Cognito pattern.

**New dependency** (`frontend/package.json`):
```
amazon-cognito-identity-js
```

**New files**:
```
frontend/src/
├── auth/
│   ├── cognito.js        # CognitoUserPool setup + login/logout/getToken helpers
│   └── AuthContext.jsx   # React context: { user, token, login, logout }
└── components/
    └── LoginPage.jsx / .css
```

**`frontend/.env.production`** (checked into repo — not secrets):
```
VITE_COGNITO_USER_POOL_ID=<COGNITO_USER_POOL_ID>
VITE_COGNITO_CLIENT_ID=<COGNITO_CLIENT_ID>
VITE_COGNITO_REGION=<COGNITO_REGION>
```

**`frontend/.env.local`** (gitignored, local dev only):
```
VITE_COGNITO_USER_POOL_ID=<COGNITO_USER_POOL_ID>
VITE_COGNITO_CLIENT_ID=<COGNITO_CLIENT_ID>
VITE_COGNITO_REGION=<COGNITO_REGION>
```

**`App.jsx` change**: wrap entire app in `AuthContext`. If no valid session,
render `<LoginPage />`. If authenticated, render existing `<WarRoom />` as
today. Token attached to all `fetch()` calls in `api/rankings.js` as
`Authorization: Bearer <token>`.

**`api/rankings.js` change**: all `fetch()` calls gain an auth header helper:
```js
const authHeaders = () => ({
  "Content-Type": "application/json",
  "Authorization": `Bearer ${getToken()}`,
});
```

**LoginPage**: email + password form. Design tokens consistent with War Room
(dark navy `#0D1B2A`, Honolulu Blue `#0076B6`, monospace font). No
registration UI — account already exists in the User Pool.

---

### 9. Deploy Script (`scripts/deploy.sh`)

Checked into repo. Run on EC2 after `git pull`.

```bash
#!/bin/bash
set -euo pipefail

REPO_DIR="/home/ec2-user/ff-draft-room"
DIST_DIR="/var/www/ff-draft-room/dist"
NGINX_CONF="/etc/nginx/sites-available/ff-draft-room"
NGINX_ENABLED="/etc/nginx/sites-enabled/ff-draft-room"
SERVICE_FILE="/etc/systemd/system/ff-draft-room.service"

echo "==> Pulling latest code"
cd "$REPO_DIR"
git pull origin main

echo "==> Installing Python dependencies"
.venv/bin/pip install -r requirements.txt --quiet

echo "==> Building frontend"
cd frontend
npm ci --silent
# Vite reads frontend/.env.production automatically during build
npm run build
cd ..

echo "==> Copying frontend build"
sudo mkdir -p "$DIST_DIR"
sudo rsync -a --delete frontend/dist/ "$DIST_DIR/"

echo "==> Installing systemd service (first deploy only)"
if [ ! -f "$SERVICE_FILE" ]; then
    sudo cp scripts/ff-draft-room.service "$SERVICE_FILE"
    sudo systemctl daemon-reload
    sudo systemctl enable ff-draft-room
fi

echo "==> Installing nginx config (first deploy only)"
if [ ! -f "$NGINX_CONF" ]; then
    sudo cp scripts/nginx.conf.template "$NGINX_CONF"
    sudo ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
    sudo nginx -t && sudo systemctl reload nginx
fi

echo "==> Restarting backend"
sudo systemctl restart ff-draft-room

echo "==> Waiting for backend to start"
sleep 3
curl -sf http://127.0.0.1:8000/health && echo "Backend healthy" \
    || echo "WARNING: health check failed"

echo "==> Deploy complete"
```

---

### 10. CDK Bootstrap Script (`scripts/cdk-bootstrap.sh`)

Run once from Debian machine. Checked into repo.

```bash
#!/bin/bash
# Run once from Debian machine (where AWS CLI + CDK are configured)
# Usage: ./scripts/cdk-bootstrap.sh <EC2_INSTANCE_ID>
set -euo pipefail

INSTANCE_ID=${1:?"Usage: $0 <EC2_INSTANCE_ID>"}
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "==> Account: $ACCOUNT  Region: $REGION  Instance: $INSTANCE_ID"

cd cdk
pip install -r requirements.txt --quiet

echo "==> Bootstrapping CDK environment"
cdk bootstrap "aws://$ACCOUNT/$REGION"

echo "==> Deploying FfDeployStack"
CDK_ACCOUNT=$ACCOUNT CDK_REGION=$REGION \
cdk deploy FfDeployStack \
    --context ec2InstanceId="$INSTANCE_ID" \
    --outputs-file cdk-outputs.json \
    --require-approval never

echo ""
echo "==> Stack deployed. Outputs:"
cat cdk-outputs.json

PROFILE_ARN=$(python3 -c \
    "import json; d=json.load(open('cdk-outputs.json')); \
     print(d['FfDeployStack']['InstanceProfileArn'])")

echo ""
echo "==> Attaching IAM instance profile to EC2"
aws ec2 associate-iam-instance-profile \
    --instance-id "$INSTANCE_ID" \
    --iam-instance-profile Arn="$PROFILE_ARN"

echo ""
echo "==> Done. EC2 can now access S3 bucket ff-draft-room-data."
echo "    Next: SSH into EC2, clone repo, create .env.production, run deploy.sh"
```

---

## File Changes Summary

### New Files
```
backend/
  middleware/
    __init__.py
    auth.py                    # Cognito JWT verification
  utils/
    storage.py                 # StorageBackend abstraction

cdk/
  app.py                       # CDK app entry point
  ff_deploy_stack.py           # S3 bucket + IAM role + instance profile
  requirements.txt
  cdk.json                     # Includes ec2InstanceId context

frontend/src/
  auth/
    cognito.js                 # CognitoUserPool + login/logout/getToken
    AuthContext.jsx             # React context provider
  components/
    LoginPage.jsx
    LoginPage.css

scripts/
  deploy.sh                    # EC2 deploy script
  cdk-bootstrap.sh             # One-time CDK deploy from Debian
  nginx.conf.template          # nginx config template
  ff-draft-room.service        # systemd unit file

env.production.example         # Template for EC2 .env.production
frontend/.env.production       # Cognito identifiers (not secrets, in repo)
```

### Modified Files
```
backend/utils/rankings.py      # Replace Path I/O with StorageBackend calls
backend/main.py                # Initialise storage singleton at startup
backend/routers/rankings.py    # Inject storage; apply require_auth to all routes
frontend/src/App.jsx           # Wrap in AuthContext; render LoginPage if unauthed
frontend/src/api/rankings.js   # Add Authorization header to all fetch() calls
requirements.txt               # Add boto3, python-jose[cryptography], httpx
.gitignore                     # Add .env.production, cdk/cdk-outputs.json
docs/DECISIONS.md              # Add ADR-007, ADR-008
docs/PLANNING.md               # Update architecture diagram, constraints
docs/TASK.md                   # Mark 09 complete, update backlog
```

### Unchanged
```
backend/utils/data_loader.py   # No storage changes (CSV is read-only seed)
backend/utils/constants.py     # Unchanged
tests/                         # All 49 tests pass — LocalStorage preserves behaviour
frontend/src/components/       # All War Room and Draft Mode components unchanged
```

---

## Testing Additions

### `tests/test_storage.py` (new)
- `LocalStorage` — read/write/delete/exists/list_keys, happy path and missing keys
- `S3Storage` — all methods mocked with `moto`
- `get_storage()` factory — env var switching between local and s3

### `tests/test_rankings.py` updates
- All existing tests refactored to pass `LocalStorage(tmp_path)` fixture
- No logic changes — storage parameter is the only diff

### `tests/conftest.py` addition
```python
@pytest.fixture
def storage(tmp_path):
    from utils.storage import LocalStorage
    return LocalStorage(tmp_path / "rankings")
```

### New dev dependency (`requirements-dev.txt`):
```
moto[s3]>=4.0.0
```

---

## Execution Sequence

Claude Code executes in this exact order. Each phase depends on the
previous completing successfully.

### Phase 1 — Write and test all code (Debian machine)

1. Write all new and modified files per spec above, substituting all
   `<PLACEHOLDER>` values provided at execution time
2. `pytest tests/ --cov=backend` — all 49+ tests passing, zero regressions
3. `ruff check backend/ tests/` — zero errors
4. Commit: `feat: add S3 storage backend, Cognito auth, AWS deploy tooling`
5. `git push origin main`

### Phase 2 — CDK infrastructure (Debian machine)

6. `cd cdk && pip install -r requirements.txt`
7. Run CDK bootstrap — creates S3 bucket and IAM instance profile,
   then attaches the profile to the EC2 automatically:
   ```bash
   ./scripts/cdk-bootstrap.sh <EC2_INSTANCE_ID>
   ```
8. Confirm `cdk/cdk-outputs.json` contains:
   - `BucketName`: `ff-draft-room-data`
   - `InstanceProfileArn`: non-empty ARN

### Phase 3 — EC2 first-time setup (SSH from Debian)

9. SSH into EC2:
   ```bash
   ssh ec2-user@ff.jurigregg.com
   ```
10. Clone repo and set up Python environment:
    ```bash
    git clone https://github.com/greggjuri/ff-draft-room
    cd ff-draft-room
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    ```
11. Create `.env.production` from template and fill in Cognito values:
    ```bash
    cp env.production.example .env.production
    nano .env.production
    # Set COGNITO_USER_POOL_ID and COGNITO_REGION
    ```
    Note: `VITE_COGNITO_CLIENT_ID` is baked into the frontend build from
    `frontend/.env.production` — it does not go in `.env.production`.

### Phase 4 — Deploy (on EC2)

12. Run deploy script:
    ```bash
    chmod +x scripts/deploy.sh
    ./scripts/deploy.sh
    ```

### Phase 5 — Verify

13. Health check through nginx:
    ```bash
    curl https://ff.jurigregg.com/health
    # Expected: {"status":"ok"}
    ```
14. Open `https://ff.jurigregg.com` in browser:
    - [ ] LoginPage renders with correct design tokens
    - [ ] Login with Cognito credentials succeeds
    - [ ] War Room loads with existing rankings
    - [ ] Reorder a player and Save → confirm write lands in S3:
          `aws s3 ls s3://ff-draft-room-data/rankings/`
    - [ ] Draft Mode toggle works
    - [ ] Search works

---

## Out of Scope

- SSL certificate provisioning — certbot already configured on this EC2
- DNS record for `ff.jurigregg.com` — assumed already pointed at EC2 IP
- Cognito User Pool creation — reusing existing automation-platform pool
- Cognito user creation — account already exists
- CI/CD pipeline — deploy is manual `git pull` + `./scripts/deploy.sh`
- Multi-user support — single user only (ADR-007); revisit in future phase
