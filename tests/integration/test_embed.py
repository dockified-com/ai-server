import app.transport.embed_routes as embed_routes


async def test_embed_requires_service_secret(client):
    resp = await client.post("/v1/embed", json={"texts": ["hi"]})
    assert resp.status_code == 401


async def test_embed_batch(client, monkeypatch):
    async def fake_embed(texts):
        return [[0.1, 0.2] for _ in texts]

    monkeypatch.setattr(embed_routes, "embed_texts", fake_embed)
    resp = await client.post(
        "/v1/embed",
        json={"texts": ["a", "b"]},
        headers={"authorization": "Bearer svc-secret"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"vectors": [[0.1, 0.2], [0.1, 0.2]]}