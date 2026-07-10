"""PRACTICE_HELP — socratic help on quiz/code; never full solutions."""

from __future__ import annotations

from typing import Any

from app.graphs.tutor_session.llm import run_node_llm
from app.graphs.tutor_session.prompts import (
    PRACTICE_HELP_SYSTEM,
    PRACTICE_HELP_TOOLS_HINT,
    build_practice_help_user_message,
)
from app.graphs.tutor_session.state import TutorState


async def practice_help_node(state: TutorState) -> dict[str, Any]:
    system = PRACTICE_HELP_SYSTEM + PRACTICE_HELP_TOOLS_HINT
    user_message = build_practice_help_user_message(dict(state))
    text, tool_results = await run_node_llm(
        system_prompt=system,
        user_message=user_message,
        state=dict(state),
        allowed_tools={
            "check_progress",
            "get_block_context",
            "get_last_submission",
        },
        max_tokens=640,
    )

    messages = list(state.get("messages") or [])
    if text:
        messages.append({"role": "assistant", "content": text})

    prior_tools = list(state.get("tool_results") or [])
    return {
        "assistant_text": text or "",
        "messages": messages,
        "tool_results": prior_tools + tool_results,
        "route": "practice_help",
    }
