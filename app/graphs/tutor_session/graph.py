"""Compile tutor_session StateGraph: ENTRY → ROUTER → session nodes.

LG-1: open_name | pre_assess
LG-4: teach | practice_help
Checkpointer: MemorySaver keyed by thread_id (enrollment:{id}).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.graphs.tutor_session.nodes.entry import entry_node
from app.graphs.tutor_session.nodes.open_name import open_name_node
from app.graphs.tutor_session.nodes.practice_help import practice_help_node
from app.graphs.tutor_session.nodes.pre_assess import pre_assess_node
from app.graphs.tutor_session.nodes.router import route_after_router, router_node
from app.graphs.tutor_session.nodes.teach import teach_node
from app.graphs.tutor_session.state import TutorState

_checkpointer = MemorySaver()


def compile_tutor_session_graph(*, checkpointer: Any | None = None):
    """Build and compile the tutor session graph (LG-1 + LG-4)."""
    builder = StateGraph(TutorState)

    builder.add_node("entry", entry_node)
    builder.add_node("router", router_node)
    builder.add_node("open_name", open_name_node)
    builder.add_node("pre_assess", pre_assess_node)
    builder.add_node("teach", teach_node)
    builder.add_node("practice_help", practice_help_node)

    builder.add_edge(START, "entry")
    builder.add_edge("entry", "router")
    builder.add_conditional_edges(
        "router",
        route_after_router,
        {
            "open_name": "open_name",
            "pre_assess": "pre_assess",
            "teach": "teach",
            "practice_help": "practice_help",
        },
    )
    builder.add_edge("open_name", END)
    builder.add_edge("pre_assess", END)
    builder.add_edge("teach", END)
    builder.add_edge("practice_help", END)

    return builder.compile(
        checkpointer=checkpointer if checkpointer is not None else _checkpointer
    )


@lru_cache
def get_tutor_session_graph():
    """Process-wide compiled graph with MemorySaver."""
    return compile_tutor_session_graph()


def thread_id_for_claims(claims: dict) -> str:
    """thread_id = enrollment:{id} from claims or server_context."""
    if claims.get("thread_id"):
        return str(claims["thread_id"])
    sc = claims.get("server_context") or {}
    task = sc.get("task") if isinstance(sc.get("task"), dict) else {}
    eid = (
        task.get("enrollment_id")
        or task.get("enrollmentId")
        or sc.get("enrollmentId")
        or sc.get("enrollment_id")
    )
    if eid:
        return f"enrollment:{eid}"
    sub = str(claims.get("sub") or "")
    if sub.startswith("enrollment:"):
        return sub
    return f"session:{claims.get('jti', 'anon')}"
