"""Node system prompts for tutor_session (LG-1: open_name + pre_assess).

Aligned with app.agents.definitions so behavior matches legacy single-shot agents.
"""

from __future__ import annotations

from typing import Any

# Reuse canonical prompt text from the agent definitions package.
from app.agents.definitions import PRE_ASSESS_SYSTEM_PROMPT, TUTOR_OPEN_SYSTEM_PROMPT

OPEN_NAME_SYSTEM = TUTOR_OPEN_SYSTEM_PROMPT
PRE_ASSESS_SYSTEM = PRE_ASSESS_SYSTEM_PROMPT

# Tool-use addendum (graph nodes allow tools; legacy reason path does not).
OPEN_NAME_TOOLS_HINT = (
    "\n\nYou may call the save_profile tool when the student clearly states a preferred name. "
    "Do not invent a name. After saving (or if no name yet), reply warmly to the student."
)

PRE_ASSESS_TOOLS_HINT = (
    "\n\nYou may call the save_profile tool with assessed_level "
    "(beginner|intermediate|advanced) only after the student confirms a proposed level. "
    "Do not save a level before confirmation."
)


def build_open_name_user_message(state: dict[str, Any]) -> str:
    profile = state.get("profile") or {}
    task = state.get("task") or {}
    mint = state.get("mint") or {}
    sc = mint.get("server_context") or {}

    course = (
        state.get("course_title")
        or sc.get("courseTitle")
        or sc.get("course_title")
        or "this course"
    )
    name = (
        profile.get("preferred_name")
        or profile.get("preferredName")
        or sc.get("preferredName")
        or sc.get("preferred_name")
    )
    lesson = sc.get("lessonTitle") or sc.get("lesson_title") or task.get("lesson_title") or ""
    user_turn = _latest_user_text(state)

    if name:
        base = (
            f"Course: {course}. Lesson: {lesson}. "
            f"Student preferred name already known: {name}. "
            "Greet them by name and invite them to continue when ready. Do not teach yet."
        )
    else:
        base = (
            f"Course: {course}. Lesson: {lesson}. "
            "Open the session: greet briefly, mention the course, and ask what name they want you to use. "
            "Do not teach concepts yet."
        )
    if user_turn:
        base += f"\n\nStudent message: {user_turn}"
    return base


def build_pre_assess_user_message(state: dict[str, Any]) -> str:
    profile = state.get("profile") or {}
    task = state.get("task") or {}
    mint = state.get("mint") or {}
    sc = mint.get("server_context") or {}

    name = (
        profile.get("preferred_name")
        or profile.get("preferredName")
        or sc.get("preferredName")
        or "student"
    )
    topics = (
        sc.get("topics")
        or sc.get("lesson_objectives")
        or task.get("topics")
        or []
    )
    topics_s = ", ".join(topics) if isinstance(topics, list) else str(topics)
    prior = state.get("messages") or sc.get("recentTurns") or sc.get("recent_turns") or []
    prior_s = _format_prior(prior)
    user_turn = _latest_user_text(state)

    return (
        f"Student name: {name}.\n"
        f"Course topics to probe: {topics_s or 'general programming for this course'}.\n"
        f"Prior turns:\n{prior_s or '(none)'}\n\n"
        f"Student message: {user_turn or '(session just started — ask first pre-assessment question)'}\n"
        "Continue the pre-assessment. After enough signal, propose beginner|intermediate|advanced "
        "and ask for confirmation."
    )


def _latest_user_text(state: dict[str, Any]) -> str:
    messages = state.get("messages") or []
    for msg in reversed(messages):
        if not isinstance(msg, dict):
            continue
        role = (msg.get("role") or msg.get("type") or "").lower()
        if role in ("user", "human"):
            return str(msg.get("content") or msg.get("text") or "")
    return ""


def _format_prior(prior: list) -> str:
    lines: list[str] = []
    for t in prior[-6:]:
        if not isinstance(t, dict):
            continue
        role = t.get("role", "?")
        text = t.get("content") or t.get("text") or t.get("assistantText") or t.get("userInput") or ""
        if text:
            lines.append(f"- {role}: {text}")
    return "\n".join(lines)
