import pytest

from app.security.result_signing import sign_result, verify_result, ResultSignatureError


def test_sign_and_verify_roundtrip():
    blob = sign_result({"passed": True, "level": "good"}, signing_secret="s")
    payload = verify_result(blob, signing_secret="s")
    assert payload == {"passed": True, "level": "good"}


def test_verify_rejects_tampered_payload():
    blob = sign_result({"passed": False}, signing_secret="s")
    with pytest.raises(ResultSignatureError):
        verify_result(blob, signing_secret="wrong")