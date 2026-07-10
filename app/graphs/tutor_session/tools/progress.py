"""check_progress tool — GET Next enrollment progress (M3 read)."""

from __future__ import annotations

from typing import Any

from google.genai import types

from app.graphs.tutor_session.tools.http_client import next_request

CHECK_PROGRESS_DECLARATION = types.FunctionDeclaration(
    name="check_progress",
    description=(
        "Read the student's current tutor stage, preferred name, level, "
        "current lesson/block, and lesson lock summary from the product server."
    ),
    parameters={
        "type": "object",
        "properties": {},
    },
)


async def check_progress(enrollment_id: str) -> dict[str, Any]:
    """GET /api/internal/enrollments/:id/progress"""
    if not enrollment_id:
        return {"ok": False, "error": "missing enrollment_id"}
    return await next_request(
        "GET",
        f"/api/internal/enrollments/{enrollment_id}/progress",
    )
