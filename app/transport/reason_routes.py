import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agents.registry import get_agent
from app.config import get_settings
from app.runtime.executor import run_stream
from app.runtime.reasoning import build_user_message
from app.security.result_signing import sign_result
from app.security.session_token import require_session_claims

router = APIRouter()

LEVEL_ORDER = {"poor": 0, "fair": 1, "good": 2, "excellent": 3}
PASS_THRESHOLD = 2


class ReasonRequest(BaseModel):
    client_context: dict = {}


def _build_result(agent_name: str, accumulated: str, client_context: dict) -> dict | None:
    if agent_name == "understanding-check":
        first_line = accumulated.strip().splitlines()[0] if accumulated.strip() else "{}"
        try:
            parsed = json.loads(first_line)
        except json.JSONDecodeError:
            parsed = {}
        level = parsed.get("level", "poor")
        level = level if level in LEVEL_ORDER else "poor"
        return {
            "level": level,
            "passed": LEVEL_ORDER[level] >= PASS_THRESHOLD,
            "feedback": parsed.get("feedback", accumulated),
            "missing_points": parsed.get("missing_points", []),
        }
    if agent_name == "ask":
        return {
            "question": client_context.get("question", ""),
            "answer": accumulated,
        }
    return None


@router.post("/reason")
async def reason_endpoint(
    body: ReasonRequest,
    claims: dict = Depends(require_session_claims),
) -> EventSourceResponse:
    agent_name = claims["agent"]
    server_context = claims.get("server_context", {})
    agent = get_agent(agent_name)
    user_message = build_user_message(agent_name, server_context, body.client_context)

    async def _events() -> AsyncGenerator[dict, None]:
        accumulated = ""
        try:
            async for chunk in run_stream(agent, user_message):
                accumulated += chunk
                yield {"event": "token", "data": chunk}
            result = _build_result(agent_name, accumulated, body.client_context)
            if result is not None:
                signed = sign_result(result, get_settings().session_signing_secret)
                yield {"event": "result", "data": signed}
            yield {"event": "done", "data": ""}
        except Exception:
            yield {"event": "error", "data": "AI temporarily unavailable"}

    return EventSourceResponse(_events())
