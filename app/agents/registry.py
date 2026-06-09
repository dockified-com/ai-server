from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.agents import definitions as d


class UnknownAgentError(Exception):
    """Raised when an agent name is not in the registry."""


@dataclass(frozen=True)
class AgentDef:
    name: str
    model: str
    system_prompt: str
    mode: Literal["stream", "json"]
    max_tokens: int


AGENTS: dict[str, AgentDef] = {
    "socratic": AgentDef("socratic", "gemini-2.5-flash-lite", d.SOCRATIC_SYSTEM_PROMPT, "stream", 512),
    "understanding-check": AgentDef(
        "understanding-check", "gemini-2.5-flash-lite", d.UNDERSTANDING_CHECK_SYSTEM_PROMPT, "stream", 512
    ),
    "ask": AgentDef("ask", "gemini-2.5-flash-lite", d.ASK_ANYTHING_SYSTEM_PROMPT, "stream", 1024),
    "code-eval": AgentDef("code-eval", "gemini-2.5-flash-lite", d.CODE_EVAL_SYSTEM_PROMPT, "json", 64),
    "agent-edit": AgentDef("agent-edit", "gemini-2.5-flash-lite", d.AGENT_EDIT_SYSTEM_PROMPT, "json", 4096),
    "outline": AgentDef("outline", "gemini-2.5-flash-lite", d.OUTLINE_SYSTEM_PROMPT, "json", 4096),
    "generate-blocks": AgentDef(
        "generate-blocks", "gemini-2.5-flash-lite", d.LESSON_BLOCKS_SYSTEM_PROMPT, "json", 8192
    ),
}


def get_agent(name: str) -> AgentDef:
    try:
        return AGENTS[name]
    except KeyError as exc:
        raise UnknownAgentError(name) from exc