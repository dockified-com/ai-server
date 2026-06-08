import app.transport.reason_routes as reason_routes
from app.security.session_token import mint_session_token


def _token(agent, server_context):
    return mint_session_token(agent, server_context, signing_secret="sign-secret", ttl_seconds=300)


async def test_reason_requires_session_token(client):
    resp = await client.post("/v1/reason", json={"client_context": {}})
    assert resp.status_code == 401


async def test_reason_streams_tokens(client, monkeypatch):
    async def fake_stream(agent, user_message):
        for t in ["Hel", "lo"]:
            yield t

    monkeypatch.setattr(reason_routes, "run_stream", fake_stream)
    token = _token("socratic", {"problem_prompt": "p"})
    resp = await client.post(
        "/v1/reason",
        json={"client_context": {"student_code": "x", "stdout": "", "stderr": "", "attempt_count": 1}},
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.text
    assert "Hel" in body and "lo" in body
    assert "token" in body  # event name present
