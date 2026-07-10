"""get_last_submission tool — last code run for PRACTICE_HELP."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from google.genai import types

from app.graphs.tutor_session.tools.http_client import next_request

GET_LAST_SUBMISSION_DECLARATION = types.FunctionDeclaration(
    name="get_last_submission",
    description=(
        "Load the student's most recent code submission for a block "
        "(code, stdout, stderr, verdict, attempt number). Use for socratic help only."
    ),
    parameters={
        "type": "object",
        "properties": {
            "block_id": {
                "type": "string",
                "description": "Code block UUID. Defaults to current_block_id when omitted.",
            },
        },
        "required": [],
    },
)


async def get_last_submission(
    enrollment_id: str,
    block_id: str | None = None,
) -> dict[str, Any]:
    """GET /api/internal/enrollments/:id/submissions/latest?blockId="""
    if not enrollment_id:
        return {"ok": False, "error": "missing enrollment_id"}
    bid = (block_id or "").strip()
    if not bid:
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
            return {"ok": False, "error": "no block_id"}
    path = (
        f"/api/internal/enrollments/{quote(enrollment_id)}/submissions/latest"
        f"?blockId={quote(bid)}"
    )
    return await next_request("GET", path)
