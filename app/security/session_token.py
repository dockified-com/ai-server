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