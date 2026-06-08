import pytest

from app.agents.registry import get_agent, AgentDef, UnknownAgentError


def test_known_agent_has_fields():
    a = get_agent("socratic")
    assert isinstance(a, AgentDef)
    assert a.mode == "stream"
    assert a.model.startswith("claude")
    assert a.system_prompt


def test_run_agent_is_json_mode():
    assert get_agent("outline").mode == "json"
    assert get_agent("code-eval").mode == "json"


def test_unknown_agent_raises():
    with pytest.raises(UnknownAgentError):
        get_agent("does-not-exist")