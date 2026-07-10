"""get_block_context tool — student-safe block content for TEACH node."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from google.genai import types

from app.graphs.tutor_session.tools.http_client import next_request

GET_BLOCK_CONTEXT_DECLARATION = types.FunctionDeclaration(
    name="get_block_context",
    description=(
        "Load the current lesson block content the student is on "
        "(markdown, quiz prompt, code instructions). Never returns hidden tests or solutions."
    ),
    parameters={
        "type": "object",
        "properties": {
            "block_id": {
                "type": "string",
                "description": "Block UUID. If omitted, use the student's current_block_id from progress.",
            },
        },
    },
)


async def get_block_context(
    enrollment_id: str,
    block_id: str | None = None,
) -> dict[str, Any]:
    """GET /api/internal/blocks/:id/tutor-context?enrollmentId="""
    if not enrollment_id:
        return {"ok": False, "error": "missing enrollment_id"}
    bid = (block_id or "").strip()
    if not bid:
        # Resolve current block from progress
        progress = await next_request(
            "GET",
            f"/api/internal/enrollments/{enrollment_id}/progress",
        )
        if not progress.get("ok", True) and progress.get("error"):
            return progress
        bid = str(
            progress.get("currentBlockId")
            or progress.get("current_block_id")
            or ""
        )
        if not bid:
            return {"ok": False, "error": "no current_block_id; pass block_id"}
    path = (
        f"/api/internal/blocks/{quote(bid)}/tutor-context"
        f"?enrollmentId={quote(enrollment_id)}"
    )
    return await next_request("GET", path)
