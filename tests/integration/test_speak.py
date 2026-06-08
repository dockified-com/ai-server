import app.transport.speak_routes as speak_routes
from app.security.session_token import mint_session_token


async def test_speak_requires_session_token(client):
    resp = await client.post("/v1/speak", json={"text": "hello"})
    assert resp.status_code == 401


async def test_speak_streams_audio(client, monkeypatch):
    async def fake_tts(text):
        yield b"\x00\x01"
        yield b"\x02\x03"

    monkeypatch.setattr(speak_routes, "synthesize_speech", fake_tts)
    token = mint_session_token("ask", {}, signing_secret="sign-secret", ttl_seconds=300)
    resp = await client.post(
        "/v1/speak",
        json={"text": "hello"},
        headers={"authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.content == b"\x00\x01\x02\x03"
