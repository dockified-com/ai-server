"""PRE_ASSESS — short level probe; may call save_profile(level)."""

from __future__ import annotations

from typing import Any

from app.graphs.tutor_session.llm import run_node_llm
from app.graphs.tutor_session.prompts import (
    PRE_ASSESS_SYSTEM,
    PRE_ASSESS_TOOLS_HINT,
    build_pre_assess_user_message,
)
from app.graphs.tutor_session.state import TutorState


async def pre_assess_node(state: TutorState) -> dict[str, Any]:
    system = PRE_ASSESS_SYSTEM + PRE_ASSESS_TOOLS_HINT
    user_message = build_pre_assess_user_message(dict(state))
    text, tool_results = await run_node_llm(
        system_prompt=system,
        user_message=user_message,
        state=dict(state),
        allowed_tools={"save_profile"},
    )

    messages = list(state.get("messages") or [])
    if text:
        messages.append({"role": "assistant", "content": text})

    profile = dict(state.get("profile") or {})
    for tr in tool_results:
        if tr.get("tool") != "save_profile":
            continue
        args = tr.get("args") or {}
        result = tr.get("result") or {}
        if result.get("ok") is False:
            continue
        name = args.get("preferred_name") or args.get("preferredName")
        level = args.get("assessed_level") or args.get("assessedLevel")
        if name:
            profile["preferred_name"] = name
            profile["preferredName"] = name
        if level:
            profile["assessed_level"] = level
            profile["assessedLevel"] = level

    prior_tools = list(state.get("tool_results") or [])
    return {
        "assistant_text": text or "",
        "messages": messages,
        "profile": profile,
        "tool_results": prior_tools + tool_results,
        "route": "pre_assess",
    }
