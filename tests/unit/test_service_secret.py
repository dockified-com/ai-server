import pytest
from fastapi import HTTPException

from app.security.service_secret import require_service_secret


def test_accepts_matching_secret():
    # should not raise
    require_service_secret(authorization="Bearer svc-secret", expected="svc-secret")


def test_rejects_missing_header():
    with pytest.raises(HTTPException) as exc:
        require_service_secret(authorization=None, expected="svc-secret")
    assert exc.value.status_code == 401


def test_rejects_wrong_secret():
    with pytest.raises(HTTPException) as exc:
        require_service_secret(authorization="Bearer nope", expected="svc-secret")
    assert exc.value.status_code == 401