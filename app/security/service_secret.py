import hmac

from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_service_secret(
    authorization: str | None,
    expected: str,
) -> None:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing service secret")
    presented = authorization.split(" ", 1)[1]
    if not hmac.compare_digest(presented, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid service secret")


async def service_secret_guard(authorization: str | None = Header(default=None)) -> None:
    require_service_secret(authorization, get_settings().ai_service_secret)