"""save_profile tool — PATCH Next enrollment profile (M1 write)."""

from __future__ import annotations

from typing import Any

from google.genai import types

from app.graphs.tutor_session.tools.http_client import next_request

SAVE_PROFILE_DECLARATION = types.FunctionDeclaration(
    name="save_profile",
    description=(
        "Save the student's preferred name and/or assessed level on their enrollment. "
        "Call only when the student has clearly provided a name or confirmed a level."
    ),
    parameters={
        "type": "object",
        "properties": {
            "preferred_name": {
                "type": "string",
                "description": "Student's preferred name to use in tutoring.",
            },
            "assessed_level": {
                "type": "string",
                "description": "Confirmed level: beginner, intermediate, or advanced.",
                "enum": ["beginner", "intermediate", "advanced"],
            },
        },
    },
)


async def save_profile(
    enrollment_id: str,
    *,
    preferred_name: str | None = None,
    assessed_level: str | None = None,
) -> dict[str, Any]:
    """PATCH /api/internal/enrollments/:id/profile"""
    if not enrollment_id:
        return {"ok": False, "error": "missing enrollment_id"}
    body: dict[str, Any] = {}
    # Next internal API uses camelCase (LG2 contract).
    if preferred_name is not None:
        body["preferredName"] = preferred_name
    if assessed_level is not None:
        body["assessedLevel"] = assessed_level
    if not body:
        return {"ok": False, "error": "no fields to update"}
    return await next_request(
        "PATCH",
        f"/api/internal/enrollments/{enrollment_id}/profile",
        json_body=body,
    )
