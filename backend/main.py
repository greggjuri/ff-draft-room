"""FF Draft Room API — FastAPI entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import rankings

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
