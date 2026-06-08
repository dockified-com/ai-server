import app.transport.run_routes as run_routes


async def test_run_requires_service_secret(client):
    resp = await client.post("/v1/run", json={"agent": "code-eval", "user_message": "x"})
    assert resp.status_code == 401


async def test_run_unknown_agent(client):
    resp = await client.post(
        "/v1/run",
        json={"agent": "nope", "user_message": "x"},
        headers={"authorization": "Bearer svc-secret"},
    )
    assert resp.status_code == 400


async def test_run_returns_text(client, monkeypatch):
    async def fake_run_json(agent, user_message):
        return '{"verdict": "passed"}'

    monkeypatch.setattr(run_routes, "run_json", fake_run_json)
    resp = await client.post(
        "/v1/run",
        json={"agent": "code-eval", "user_message": "check"},
        headers={"authorization": "Bearer svc-secret"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"text": '{"verdict": "passed"}'}
