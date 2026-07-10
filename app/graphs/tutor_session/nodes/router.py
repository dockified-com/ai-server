"""ROUTER — map task.tutor_stage + user intent → session node."""

from __future__ import annotations

from typing import Any

from app.graphs.tutor_session.state import TutorState

_VALID_ROUTES = frozenset(
    {"open_name", "pre_assess", "teach", "practice_help"},
)

_STAGE_TO_ROUTE: dict[str, str] = {
    "onboarding": "open_name",
    "open_name": "open_name",
    "open": "open_name",
    "name": "open_name",
    "pre_assess": "pre_assess",
    "pre-assess": "pre_assess",
    "preassess": "pre_assess",
    "ready": "teach",
    "active": "teach",
    "in_lesson": "teach",
    "final_eval": "teach",  # FINAL_MODE node later; teach with tight policy interim
    "completed": "teach",
}


def _latest_user_text(state: TutorState) -> str:
    messages = state.get("messages") or []
    for msg in reversed(messages):
        if not isinstance(msg, dict):
            continue
        role = (msg.get("role") or "").lower()
        if role in ("user", "human"):
            return str(msg.get("content") or msg.get("text") or "").lower()
    return ""


def _wants_practice_help(user_text: str, task: dict[str, Any]) -> bool:
    """Heuristic: stuck on code / asks for help → practice_help when active."""
    if not user_text:
        # Failed last run with no text still routes to practice if verdict failed
        verdict = str(
            task.get("last_verdict")
            or task.get("lastCodeVerdict")
            or ""
        ).lower()
        return verdict in ("failed", "runtime_error", "compile_error", "error")

    help_markers = (
        "help",
        "stuck",
        "hint",
        "error",
        "fail",
        "doesn't work",
        "does not work",
        "not working",
        "why",
        "fix",
        "bug",
        "hint please",
        "what am i missing",
    )
    return any(m in user_text for m in help_markers)


def router_node(state: TutorState) -> dict[str, Any]:
    task = state.get("task") or {}
    stage_raw = task.get("tutor_stage") or task.get("tutorStage") or "onboarding"
    stage = str(stage_raw).strip().lower()
    route = _STAGE_TO_ROUTE.get(stage, "open_name")

    # LG-4: when in lesson (active/ready), prefer practice_help if student is stuck
    if route == "teach" and stage in ("active", "ready", "in_lesson"):
        user_text = _latest_user_text(state)
        if _wants_practice_help(user_text, dict(task)):
            route = "practice_help"

    return {"route": route}


def route_after_router(state: TutorState) -> str:
    """Conditional edge target for LangGraph."""
    route = (state.get("route") or "open_name").strip().lower()
    if route in _VALID_ROUTES:
        return route
    return "open_name"
