"""POST /v1/tutor/stream — LangGraph tutor_session SSE (token/done/error).

Auth: session JWT (same as /v1/reason).
Agent: mint agent must be `tutor_session` (registered for mint validation).

Does not use product DB; tools inside the graph call Next with AI_SERVICE_SECRET.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.graphs.tutor_session.graph import get_tutor_session_graph, thread_id_for_claims
from app.security.session_token import require_session_claims

router = APIRouter()

# Graph agent name. Registered in app.agents.registry so POST /v1/session mint
# still validates agent names. /v1/tutor/stream accepts only this agent
# (legacy one-shot agents stay on /v1/reason).
TUTOR_SESSION_AGENT = "tutor_session"


class TutorStreamRequest(BaseModel):
    client_context: dict = {}


def _user_message_from_client(client_context: dict) -> str:
    return str(
        client_context.get("message")
        or client_context.get("user_message")
        or client_context.get("text")
        or ""
    )


def _chunk_text(text: str, size: int = 24) -> list[str]:
    """Split assistant_text into small SSE token chunks (stream UX without mid-LLM callback)."""
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


@router.post("/tutor/stream")
async def tutor_stream_endpoint(
    body: TutorStreamRequest,
    claims: dict = Depends(require_session_claims),
) -> EventSourceResponse:
    agent_name = claims.get("agent")
    if agent_name != TUTOR_SESSION_AGENT:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"agent must be {TUTOR_SESSION_AGENT} for /v1/tutor/stream (got {agent_name!r})",
        )

    server_context = claims.get("server_context") or {}
    thread_id = thread_id_for_claims(claims)
    user_text = _user_message_from_client(body.client_context)

    messages: list[dict[str, Any]] = []
    if user_text:
        messages.append({"role": "user", "content": user_text})

    input_state: dict[str, Any] = {
        "mint": {
            "agent": agent_name,
            "server_context": server_context,
            "thread_id": thread_id,
            "sub": claims.get("sub"),
            "jti": claims.get("jti"),
        },
        "messages": messages,
        "tool_results": [],
        "assistant_text": "",
    }

    config = {"configurable": {"thread_id": thread_id}}
    graph = get_tutor_session_graph()

    async def _events() -> AsyncGenerator[dict, None]:
        try:
            result = await graph.ainvoke(input_state, config=config)
            text = (result or {}).get("assistant_text") or ""
            for chunk in _chunk_text(text):
                yield {"event": "token", "data": chunk}
            yield {"event": "done", "data": ""}
        except Exception:
            yield {"event": "error", "data": "AI temporarily unavailable"}

    return EventSourceResponse(_events())
