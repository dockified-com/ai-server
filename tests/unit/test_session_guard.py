import pytest
from fastapi import HTTPException

from app.security.session_token import mint_session_token, require_session_claims


def test_require_session_claims_ok():
    token = mint_session_token("ask", {"x": 1}, signing_secret="sign-secret", ttl_seconds=300)
    claims = require_session_claims(authorization=f"Bearer {token}")
    assert claims["agent"] == "ask"


def test_require_session_claims_missing():
    with pytest.raises(HTTPException) as exc:
        require_session_claims(authorization=None)
    assert exc.value.status_code == 401


def test_require_session_claims_bad_token():
    with pytest.raises(HTTPException) as exc:
        require_session_claims(authorization="Bearer garbage")
    assert exc.value.status_code == 401