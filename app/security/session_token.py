from __future__ import annotations

import datetime as _dt
import uuid

import jwt


class SessionTokenError(Exception):
    """Raised when a session token cannot be minted or verified."""


def mint_session_token(
    agent: str,
    server_context: dict,
    signing_secret: str,
    ttl_seconds: int,
) -> str:
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    payload = {
        "agent": agent,
        "server_context": server_context,
        "iat": now,
        "exp": now + _dt.timedelta(seconds=ttl_seconds),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, signing_secret, algorithm="HS256")


def verify_session_token(token: str, signing_secret: str) -> dict:
    try:
        return jwt.decode(
            token,
            signing_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "agent"]},
        )
    except jwt.PyJWTError as exc:
        raise SessionTokenError(str(exc)) from exc


from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_session_claims(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing session token")
    token = authorization.split(" ", 1)[1]
    try:
        return verify_session_token(token, get_settings().session_signing_secret)
    except SessionTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc