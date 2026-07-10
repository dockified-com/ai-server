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


# V1 tutoring registry — generation agents intentionally omitted for pilot deploys.
AGENTS: dict[str, AgentDef] = {
    # LangGraph multi-turn session (POST /v1/tutor/stream). Mint validates this name.
    "tutor_session": AgentDef(
        "tutor_session", "gemini-2.5-flash-lite", d.TUTOR_OPEN_SYSTEM_PROMPT, "stream", 1024
    ),
    "tutor_open": AgentDef(
        "tutor_open", "gemini-2.5-flash-lite", d.TUTOR_OPEN_SYSTEM_PROMPT, "stream", 512
    ),
    "pre_assess": AgentDef(
        "pre_assess", "gemini-2.5-flash-lite", d.PRE_ASSESS_SYSTEM_PROMPT, "stream", 512
    ),
    "socratic": AgentDef("socratic", "gemini-2.5-flash-lite", d.SOCRATIC_SYSTEM_PROMPT, "stream", 512),
    "understanding-check": AgentDef(
        "understanding-check", "gemini-2.5-flash-lite", d.UNDERSTANDING_CHECK_SYSTEM_PROMPT, "stream", 512
    ),
    "ask": AgentDef("ask", "gemini-2.5-flash-lite", d.ASK_ANYTHING_SYSTEM_PROMPT, "stream", 1024),
    "final_clarify": AgentDef(
        "final_clarify", "gemini-2.5-flash-lite", d.FINAL_CLARIFY_SYSTEM_PROMPT, "stream", 256
    ),
    "code-eval": AgentDef("code-eval", "gemini-2.5-flash-lite", d.CODE_EVAL_SYSTEM_PROMPT, "json", 64),
    # TTS is spoken via /v1/speak; keep name for session mint compatibility from Next.
    "tts": AgentDef("tts", "gemini-2.5-flash-lite", "You are a TTS session placeholder.", "stream", 64),
}


def get_agent(name: str) -> AgentDef:
    try:
        return AGENTS[name]
    except KeyError as exc:
        raise UnknownAgentError(name) from exc
