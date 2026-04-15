"""FF Draft Room API — FastAPI entry point."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so internal imports resolve
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from routers import rankings  # noqa: E402
from utils.storage import get_storage  # noqa: E402

app = FastAPI(title="FF Draft Room API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ff.jurigregg.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage singleton — LocalStorage in dev, S3Storage in prod
app.state.storage = get_storage()

# Auth — only enforce when Cognito is configured (production)
_router_deps = []
if os.environ.get("COGNITO_USER_POOL_ID"):
    from middleware.auth import require_auth  # noqa: E402

    _router_deps.append(Depends(require_auth))

app.include_router(
    rankings.router, prefix="/api", dependencies=_router_deps
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
