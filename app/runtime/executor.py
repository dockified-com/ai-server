from __future__ import annotations

from collections.abc import AsyncGenerator

from app.agents.registry import AgentDef
from app.providers.anthropic_provider import anthropic_client


async def run_json(agent: AgentDef, user_message: str) -> str:
    resp = await anthropic_client.messages.create(
        model=agent.model,
        max_tokens=agent.max_tokens,
        system=agent.system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return resp.content[0].text


async def run_stream(agent: AgentDef, user_message: str) -> AsyncGenerator[str, None]:
    async with anthropic_client.messages.stream(
        model=agent.model,
        max_tokens=agent.max_tokens,
        system=agent.system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for chunk in stream.text_stream:
            yield chunk