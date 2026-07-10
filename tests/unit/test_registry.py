import pytest

from app.agents.registry import get_agent, AgentDef, UnknownAgentError


def test_known_agent_has_fields():
    a = get_agent("socratic")
    assert isinstance(a, AgentDef)
    assert a.mode == "stream"
    assert a.system_prompt


def test_tutoring_open_agents_registered():
    assert get_agent("tutor_open").mode == "stream"
    assert get_agent("pre_assess").mode == "stream"
    assert get_agent("final_clarify").mode == "stream"
    # Mint-compatible placeholder for /v1/speak
    assert get_agent("tts").mode == "stream"


def test_run_agent_is_json_mode():
    assert get_agent("code-eval").mode == "json"


def test_generation_agents_removed_from_v1_registry():
    with pytest.raises(UnknownAgentError):
        get_agent("outline")


def test_unknown_agent_raises():
    with pytest.raises(UnknownAgentError):
        get_agent("does-not-exist")
