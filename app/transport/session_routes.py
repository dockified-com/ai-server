from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agents.registry import UnknownAgentError, get_agent
from app.config import get_settings
from app.security.service_secret import service_secret_guard
from app.security.session_token import mint_session_token

router = APIRouter()


class SessionRequest(BaseModel):
    agent: str
    server_context: dict = {}


class SessionResponse(BaseModel):
    session_token: str
    expires_in: int


@router.post("/session", response_model=SessionResponse, dependencies=[Depends(service_secret_guard)])
async def session_endpoint(body: SessionRequest) -> SessionResponse:
    try:
        get_agent(body.agent)  # validate the agent exists
    except UnknownAgentError:
        raise HTTPException(400, f"unknown agent: {body.agent}")
    settings = get_settings()
    ttl = settings.session_token_ttl_seconds
    token = mint_session_token(
        agent=body.agent,
        server_context=body.server_context,
        signing_secret=settings.session_signing_secret,
        ttl_seconds=ttl,
    )
    return SessionResponse(session_token=token, expires_in=ttl)