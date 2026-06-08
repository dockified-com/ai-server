from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agents.registry import UnknownAgentError, get_agent
from app.runtime.executor import run_json
from app.security.service_secret import service_secret_guard

router = APIRouter()


class RunRequest(BaseModel):
    agent: str
    user_message: str


class RunResponse(BaseModel):
    text: str


@router.post("/run", response_model=RunResponse, dependencies=[Depends(service_secret_guard)])
async def run_endpoint(body: RunRequest) -> RunResponse:
    try:
        agent = get_agent(body.agent)
    except UnknownAgentError:
        raise HTTPException(400, f"unknown agent: {body.agent}")
    if agent.mode != "json":
        raise HTTPException(400, f"agent {body.agent} is not a json agent")
    text = await run_json(agent, body.user_message)
    return RunResponse(text=text)
