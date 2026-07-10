"""TEACH — explain current block; tools: get_block_context, check_progress."""

from __future__ import annotations

from typing import Any

from app.graphs.tutor_session.llm import run_node_llm
from app.graphs.tutor_session.prompts import (
    TEACH_SYSTEM,
    TEACH_TOOLS_HINT,
    build_teach_user_message,
)
from app.graphs.tutor_session.state import TutorState


async def teach_node(state: TutorState) -> dict[str, Any]:
    system = TEACH_SYSTEM + TEACH_TOOLS_HINT
    user_message = build_teach_user_message(dict(state))
    text, tool_results = await run_node_llm(
        system_prompt=system,
        user_message=user_message,
        state=dict(state),
        allowed_tools={"get_block_context", "check_progress"},
        max_tokens=768,
    )

    messages = list(state.get("messages") or [])
    if text:
        messages.append({"role": "assistant", "content": text})

    task = dict(state.get("task") or {})
    for tr in tool_results:
        if tr.get("tool") != "check_progress":
            continue
        result = tr.get("result") or {}
        if result.get("error") and not result.get("ok", True):
            continue
        for camel, snake in (
            ("tutorStage", "tutor_stage"),
            ("currentBlockId", "current_block_id"),
            ("currentLessonId", "current_lesson_id"),
            ("lastCodeVerdict", "last_verdict"),
        ):
            if result.get(camel) is not None:
                task[camel] = result[camel]
                task[snake] = result[camel]

    prior_tools = list(state.get("tool_results") or [])
    return {
        "assistant_text": text or "",
        "messages": messages,
        "task": task,
        "tool_results": prior_tools + tool_results,
        "route": "teach",
    }
