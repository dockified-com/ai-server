async def test_healthz(client):
    resp = await client.get("/v1/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
