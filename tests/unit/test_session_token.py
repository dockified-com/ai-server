import time

import pytest

from app.security.session_token import mint_session_token, verify_session_token, SessionTokenError


def test_mint_and_verify_roundtrip():
    token = mint_session_token(
        agent="ask",
        server_context={"chunks": ["a", "b"]},
        signing_secret="sign-secret",
        ttl_seconds=300,
    )
    claims = verify_session_token(token, signing_secret="sign-secret")
    assert claims["agent"] == "ask"
    assert claims["server_context"] == {"chunks": ["a", "b"]}
    assert "jti" in claims


def test_verify_rejects_wrong_secret():
    token = mint_session_token("ask", {}, signing_secret="right", ttl_seconds=300)
    with pytest.raises(SessionTokenError):
        verify_session_token(token, signing_secret="wrong")


def test_verify_rejects_expired():
    token = mint_session_token("ask", {}, signing_secret="s", ttl_seconds=-1)
    with pytest.raises(SessionTokenError):
        verify_session_token(token, signing_secret="s")