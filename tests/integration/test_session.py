from app.security.session_token import verify_session_token


async def test_session_requires_service_secret(client):
    resp = await client.post("/v1/session", json={"agent": "ask", "server_context": {}})
    assert resp.status_code == 401


async def test_session_mints_token(client):
    resp = await client.post(
        "/v1/session",
        json={"agent": "ask", "server_context": {"chunks": ["c1"]}},
        headers={"authorization": "Bearer svc-secret"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["expires_in"] == 300
    claims = verify_session_token(body["session_token"], signing_secret="sign-secret")
    assert claims["agent"] == "ask"
    assert claims["server_context"] == {"chunks": ["c1"]}


async def test_session_rejects_unknown_agent(client):
    resp = await client.post(
        "/v1/session",
        json={"agent": "nope", "server_context": {}},
        headers={"authorization": "Bearer svc-secret"},
    )
    assert resp.status_code == 400