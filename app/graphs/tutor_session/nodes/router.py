"""ROUTER — map task.tutor_stage → open_name | pre_assess (default open_name)."""

from __future__ import annotations

from typing import Any

from app.graphs.tutor_session.state import TutorState

# LG-1 only wires open_name and pre_assess. Later stages default to open_name
# until TEACH/READY nodes land (LG-3+).
_STAGE_TO_ROUTE: dict[str, str] = {
    "onboarding": "open_name",
    "open_name": "open_name",
    "open": "open_name",
    "name": "open_name",
    "pre_assess": "pre_assess",
    "pre-assess": "pre_assess",
    "preassess": "pre_assess",
}


def router_node(state: TutorState) -> dict[str, Any]:
    task = state.get("task") or {}
    stage_raw = task.get("tutor_stage") or task.get("tutorStage") or "onboarding"
    stage = str(stage_raw).strip().lower()
    route = _STAGE_TO_ROUTE.get(stage, "open_name")
    return {"route": route}


def route_after_router(state: TutorState) -> str:
    """Conditional edge target for LangGraph."""
    route = (state.get("route") or "open_name").strip().lower()
    if route in ("open_name", "pre_assess"):
        return route
    return "open_name"
