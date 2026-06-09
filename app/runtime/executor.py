from __future__ import annotations

from collections.abc import AsyncGenerator

from app.agents.registry import AgentDef
from app.providers.gemini_provider import generate_text, stream_text


async def run_json(agent: AgentDef, user_message: str) -> str:
    return await generate_text(agent.system_prompt, user_message, agent.max_tokens, agent.model)


async def run_stream(agent: AgentDef, user_message: str) -> AsyncGenerator[str, None]:
    async for chunk in stream_text(agent.system_prompt, user_message, agent.max_tokens, agent.model):
        yield chunk
