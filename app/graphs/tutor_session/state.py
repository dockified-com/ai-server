"""TutorState — three memories (M1 profile, M2 messages, M3 task) + runtime fields."""

from __future__ import annotations

from typing import Any, TypedDict


class TutorState(TypedDict, total=False):
    # M2 — dialogue / episodic
    messages: list[dict[str, Any]]

    # M1 — profile (preferred_name, assessed_level, locale)
    profile: dict[str, Any]

    # M3 — task (enrollment_id, course_id, tutor_stage, current lesson/block, …)
    task: dict[str, Any]

    # Runtime — JWT claims / server_context snapshot from mint
    mint: dict[str, Any]

    # Router decision: open_name | pre_assess | …
    route: str

    # Accumulated tool call results this turn
    tool_results: list[dict[str, Any]]

    # Final assistant utterance for SSE
    assistant_text: str

    # Course metadata from mint (not durable M1/M3)
    course_title: str
