from __future__ import annotations

import jwt


class ResultSignatureError(Exception):
    """Raised when a signed result event fails verification."""


def sign_result(payload: dict, signing_secret: str) -> str:
    # Wrap under a claim so the whole dict is signed as one unit.
    return jwt.encode({"result": payload}, signing_secret, algorithm="HS256")


def verify_result(token: str, signing_secret: str) -> dict:
    try:
        decoded = jwt.decode(token, signing_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise ResultSignatureError(str(exc)) from exc
    return decoded["result"]