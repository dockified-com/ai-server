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


async def test_reason_tutor_open_streams_without_crash(client, monkeypatch):
    captured: dict = {}

    async def fake_stream(agent, user_message):
        captured["user_message"] = user_message
        yield "Hi "

        yield "there"

    monkeypatch.setattr(reason_routes, "run_stream", fake_stream)
    token = _token("tutor_open", {"courseTitle": "Intro Python", "lessonTitle": "Start"})
    resp = await client.post(
        "/v1/reason",
        json={"client_context": {}},
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "Hi " in resp.text
    assert "event: done" in resp.text
    assert "Intro Python" in captured["user_message"]
    # No signed result for tutor_open
    assert "event: result" not in resp.text


async def test_reason_pre_assess_streams_without_crash(client, monkeypatch):
    captured: dict = {}

    async def fake_stream(agent, user_message):
        captured["user_message"] = user_message
        yield "Question one?"

    monkeypatch.setattr(reason_routes, "run_stream", fake_stream)
    token = _token(
        "pre_assess",
        {"preferredName": "Sam", "topics": ["variables"]},
    )
    resp = await client.post(
        "/v1/reason",
        json={"client_context": {"message": "ready"}},
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "Question one?" in resp.text
    assert "event: done" in resp.text
    assert "Sam" in captured["user_message"]
    assert "variables" in captured["user_message"]
    assert "event: result" not in resp.text


async def test_reason_final_clarify_streams_without_crash(client, monkeypatch):
    captured: dict = {}

    async def fake_stream(agent, user_message):
        captured["user_message"] = user_message
        yield "It means reverse the characters."

    monkeypatch.setattr(reason_routes, "run_stream", fake_stream)
    token = _token(
        "final_clarify",
        {"challenge_prompt": "Reverse a string"},
    )
    resp = await client.post(
        "/v1/reason",
        json={"client_context": {"question": "What does reverse mean?"}},
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "Reverse a string" in captured["user_message"]
    assert "What does reverse mean?" in captured["user_message"]
    assert "event: done" in resp.text
    assert "event: result" not in resp.text
    assert "event: error" not in resp.text


async def test_reason_tts_completes_without_model_or_crash(client, monkeypatch):
    called = {"stream": False}

    async def fake_stream(agent, user_message):
        called["stream"] = True
        yield "should-not-run"

    monkeypatch.setattr(reason_routes, "run_stream", fake_stream)
    token = _token("tts", {})
    resp = await client.post(
        "/v1/reason",
        json={"client_context": {}},
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert called["stream"] is False
    assert "event: done" in resp.text
    assert "event: error" not in resp.text
    assert "should-not-run" not in resp.text
