"""Integration tests for POST /v1/tutor/stream."""

from __future__ import annotations

from app.security.session_token import mint_session_token


def _token(agent: str, server_context: dict, **extra_claims_ignored):
    return mint_session_token(
        agent, server_context, signing_secret="sign-secret", ttl_seconds=300
    )


async def test_tutor_stream_requires_session_token(client):
    resp = await client.post("/v1/tutor/stream", json={"client_context": {}})
    assert resp.status_code == 401


async def test_tutor_stream_rejects_wrong_agent(client):
    token = _token("socratic", {"problem_prompt": "p"})
    resp = await client.post(
        "/v1/tutor/stream",
        json={"client_context": {}},
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "tutor_session" in resp.text


async def test_tutor_stream_sse_tokens_and_done(client, monkeypatch):
    from app.graphs.tutor_session.nodes import open_name as open_name_mod

    async def fake_llm(**kwargs):
        return "Hello from graph!", []

    monkeypatch.setattr(open_name_mod, "run_node_llm", fake_llm)

    token = _token(
        "tutor_session",
        {
            "courseTitle": "Intro Python",
            "task": {"tutorStage": "onboarding", "enrollmentId": "enr-stream-1"},
        },
    )
    resp = await client.post(
        "/v1/tutor/stream",
        json={"client_context": {}},
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.text
    assert "Hello from graph!" in body
    assert "event: token" in body
    assert "event: done" in body
    assert "event: error" not in body


async def test_tutor_stream_pre_assess_stage(client, monkeypatch):
    from app.graphs.tutor_session.nodes import pre_assess as pre_assess_mod

    async def fake_llm(**kwargs):
        return "Question 1: What is a loop?", []

    monkeypatch.setattr(pre_assess_mod, "run_node_llm", fake_llm)

    token = _token(
        "tutor_session",
        {
            "preferredName": "Alex",
            "task": {"tutorStage": "pre_assess", "enrollmentId": "enr-stream-2"},
        },
    )
    resp = await client.post(
        "/v1/tutor/stream",
        json={"client_context": {"message": "let's start"}},
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    # Tokens may be chunked across SSE events — reassemble data lines
    joined = "".join(
        line.split(":", 1)[1].lstrip()
        for line in resp.text.replace("\r\n", "\n").splitlines()
        if line.startswith("data:")
    )
    assert "What is a loop?" in joined
    assert "event: done" in resp.text


async def test_reason_still_registered(client):
    """Keep /v1/reason working (smoke: 401 without token, route exists)."""
    resp = await client.post("/v1/reason", json={"client_context": {}})
    assert resp.status_code == 401


async def test_mint_accepts_tutor_session_agent(client):
    resp = await client.post(
        "/v1/session",
        json={
            "agent": "tutor_session",
            "server_context": {
                "courseTitle": "X",
                "task": {"tutorStage": "onboarding"},
            },
        },
        headers={"authorization": "Bearer svc-secret"},
    )
    assert resp.status_code == 200
    assert "session_token" in resp.json()
