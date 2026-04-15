"""Cognito JWT authentication middleware."""

from __future__ import annotations

import os

import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

REGION = os.environ.get("COGNITO_REGION", "")
USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
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
    """Validate Cognito JWT. Returns decoded payload."""
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
    except (JWTError, StopIteration, KeyError) as exc:
        raise HTTPException(
            status_code=401, detail="Invalid token"
        ) from exc
