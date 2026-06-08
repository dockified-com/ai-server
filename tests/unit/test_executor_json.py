import app.runtime.executor as executor
from app.agents.registry import get_agent


class _FakeContent:
    def __init__(self, text):
        self.text = text


class _FakeResp:
    def __init__(self, text):
        self.content = [_FakeContent(text)]


async def test_run_json_returns_text(monkeypatch):
    async def fake_create(**kwargs):
        assert kwargs["model"] == "claude-haiku-4-5-20251001"
        assert kwargs["system"]  # agent system prompt passed through
        return _FakeResp('{"verdict": "passed"}')

    monkeypatch.setattr(executor.anthropic_client.messages, "create", fake_create)
    out = await executor.run_json(get_agent("code-eval"), user_message="check this")
    assert out == '{"verdict": "passed"}'