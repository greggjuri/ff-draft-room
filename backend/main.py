"""FF Draft Room API — FastAPI entry point."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend/ is on sys.path so internal imports resolve
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from routers import rankings  # noqa: E402

app = FastAPI(title="FF Draft Room API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rankings.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
