"""HTTP client for Next internal tool APIs (service-secret auth)."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings

DEFAULT_TIMEOUT = 15.0


def next_base_url() -> str:
    """Prefer NEXT_INTERNAL_URL, else NEXT_APP_URL, else local Next default."""
    settings = get_settings()
    return (
        (settings.next_internal_url or "").rstrip("/")
        or (settings.next_app_url or "").rstrip("/")
        or "http://127.0.0.1:3000"
    )


def _auth_headers() -> dict[str, str]:
    secret = get_settings().ai_service_secret
    return {
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def next_request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Call Next with AI_SERVICE_SECRET. path is absolute path e.g. /api/internal/..."""
    url = f"{next_base_url()}{path if path.startswith('/') else '/' + path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(
            method.upper(),
            url,
            headers=_auth_headers(),
            json=json_body,
        )
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {"raw": resp.text}
        if not isinstance(data, dict):
            data = {"data": data}
        if resp.is_error:
            return {
                "ok": False,
                "status": resp.status_code,
                "error": data.get("error") or data.get("message") or resp.reason_phrase,
                "body": data,
            }
        return {"ok": True, "status": resp.status_code, **data}
