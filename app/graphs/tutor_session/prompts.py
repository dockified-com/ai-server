"""Node system prompts for tutor_session (LG-1 open/pre_assess + LG-4 teach/practice).

Aligned with app.agents.definitions where possible.
"""

from __future__ import annotations

from typing import Any

# Reuse canonical prompt text from the agent definitions package.
from app.agents.definitions import (
    PRE_ASSESS_SYSTEM_PROMPT,
    SOCRATIC_SYSTEM_PROMPT,
    TUTOR_OPEN_SYSTEM_PROMPT,
)

OPEN_NAME_SYSTEM = TUTOR_OPEN_SYSTEM_PROMPT
PRE_ASSESS_SYSTEM = PRE_ASSESS_SYSTEM_PROMPT

TEACH_SYSTEM = """You are a programming course tutor explaining the current lesson block.
Goals:
1) Call get_block_context (or use provided block summary) so you teach the real content.
2) Explain clearly for the student's assessed level (beginner / intermediate / advanced).
3) Keep explanations concise (short paragraphs or bullets). End with a check question.
4) NEVER reveal full solution code for coding exercises. For code blocks, explain concepts and
   what success looks like without writing the complete answer.
5) Do not unlock lessons yourself — only teach."""

PRACTICE_HELP_SYSTEM = SOCRATIC_SYSTEM_PROMPT + """

You are in PRACTICE_HELP mode (quiz or code lab).
Use get_last_submission and get_block_context when helpful.
ABSOLUTE: never paste a full working solution. Hints and questions only."""

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

TEACH_TOOLS_HINT = (
    "\n\nTools: get_block_context (load block content), check_progress (current block/stage). "
    "Prefer calling get_block_context before teaching if content is not already in the message."
)

PRACTICE_HELP_TOOLS_HINT = (
    "\n\nTools: check_progress, get_block_context, get_last_submission. "
    "Use get_last_submission when the student is stuck on a failed run. "
    "Never output full solution code."
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


def build_teach_user_message(state: dict[str, Any]) -> str:
    profile = state.get("profile") or {}
    task = state.get("task") or {}
    mint = state.get("mint") or {}
    sc = mint.get("server_context") or {}
    name = (
        profile.get("preferred_name")
        or profile.get("preferredName")
        or "student"
    )
    level = profile.get("assessed_level") or profile.get("assessedLevel") or "unknown"
    block_id = (
        task.get("current_block_id")
        or task.get("currentBlockId")
        or sc.get("currentBlockId")
        or ""
    )
    course = state.get("course_title") or sc.get("courseTitle") or "this course"
    user_turn = _latest_user_text(state)
    return (
        f"Student: {name} (level: {level}). Course: {course}.\n"
        f"current_block_id: {block_id or '(use get_block_context / check_progress)'}.\n"
        f"Student message: {user_turn or '(please explain the current block)'}\n"
        "Teach this block. Call get_block_context if needed. No full solutions."
    )


def build_practice_help_user_message(state: dict[str, Any]) -> str:
    profile = state.get("profile") or {}
    task = state.get("task") or {}
    mint = state.get("mint") or {}
    sc = mint.get("server_context") or {}
    name = (
        profile.get("preferred_name")
        or profile.get("preferredName")
        or "student"
    )
    block_id = (
        task.get("current_block_id")
        or task.get("currentBlockId")
        or sc.get("currentBlockId")
        or ""
    )
    verdict = task.get("last_verdict") or task.get("lastCodeVerdict") or sc.get("lastCodeVerdict")
    attempt = task.get("attempt_count") or sc.get("attempt_count") or ""
    user_turn = _latest_user_text(state)
    return (
        f"Student: {name}.\n"
        f"current_block_id: {block_id or '(unknown)'}.\n"
        f"last_verdict: {verdict or 'unknown'}. attempt_count: {attempt or 'unknown'}.\n"
        f"Student message: {user_turn or '(student needs help on this exercise)'}\n"
        "Give a Socratic hint only. Use get_last_submission if useful. No full solution code."
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
