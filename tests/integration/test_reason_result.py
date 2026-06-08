import app.transport.reason_routes as reason_routes
from app.security.result_signing import verify_result
from app.security.session_token import mint_session_token


async def test_understanding_emits_signed_result(client, monkeypatch):
    async def fake_stream(agent, user_message):
        # Model returns a JSON first line then prose (mirrors current backend behavior)
        yield '{"level": "good", "feedback": "Nice", "missing_points": []}'

    monkeypatch.setattr(reason_routes, "run_stream", fake_stream)
    token = mint_session_token(
        "understanding-check", {"rubric": "r"}, signing_secret="sign-secret", ttl_seconds=300
    )
    resp = await client.post(
        "/v1/reason",
        json={"client_context": {"response": "answer", "attempt_number": 1}},
        headers={"authorization": f"Bearer {token}"},
    )
    text = resp.text
    signed = None
    for line in text.splitlines():
        if line.startswith("data: ") and "." in line:  # JWT has dots
            candidate = line[len("data: "):].strip()
            try:
                payload = verify_result(candidate, signing_secret="sign-secret")
            except Exception:
                continue
            signed = payload
    assert signed is not None
    assert signed["passed"] is True
    assert signed["level"] == "good"


async def test_ask_emits_signed_qa_result(client, monkeypatch):
    async def fake_stream(agent, user_message):
        for t in ["Recursion ", "is..."]:
            yield t

    monkeypatch.setattr(reason_routes, "run_stream", fake_stream)
    token = mint_session_token(
        "ask", {"chunks": ["c1"]}, signing_secret="sign-secret", ttl_seconds=300
    )
    resp = await client.post(
        "/v1/reason",
        json={"client_context": {"question": "what is recursion?"}},
        headers={"authorization": f"Bearer {token}"},
    )
    signed = None
    for line in resp.text.splitlines():
        if line.startswith("data: ") and "." in line:
            candidate = line[len("data: "):].strip()
            try:
                signed = verify_result(candidate, signing_secret="sign-secret")
            except Exception:
                continue
    assert signed is not None
    assert signed["question"] == "what is recursion?"
    assert signed["answer"] == "Recursion is..."
