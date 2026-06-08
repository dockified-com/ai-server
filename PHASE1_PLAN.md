# Phase 1 Plan — AI Server Foundation

> **Scope:** Scaffold, config, three security primitives, and an app skeleton with `/v1/healthz`. No backend porting, no providers, no DB. This is a standalone, executable extract of Phase 1 from `docs/superpowers/plans/2026-06-08-ai-service-extraction.md` — an implementer never needs to cross-reference the master doc.

**Source spec:** `docs/superpowers/specs/2026-06-08-ai-service-extraction-design.md`

---

## Dependency graph & execution order

```
Task 1: Scaffold + config        (pyproject.toml, .env.example, app/config.py)
   │                                MUST run first — everything imports app.config
   ├────────────┬──────────────┐
   ▼            ▼              ▼
Task 2        Task 3        Task 4        ← PARALLEL BATCH (fully independent)
session_token service_secret result_signing
   └────────────┴──────────────┘
                  ▼
Task 5: App skeleton + /v1/healthz   (conftest.py, main.py, router.py)
                                 MUST run last — conftest imports app.main
```

**Execution annotation:**
- **Task 1** — solo, serial. Run first. Everything imports `app.config`.
- **Tasks 2 / 3 / 4** — PARALLEL BATCH. Dispatch as 3 concurrent subagents (model: `minimax-m2.5`). Each creates one isolated security module + its unit test. Task 3 imports `app.config` (already written by Task 1) but has no dependency on Tasks 2 or 4.
- **Task 5** — solo, serial. Run last. Its `conftest.py` imports the full app, so the app must be assembled after the security modules exist.

**Per task:** strict TDD — write failing test → run to confirm failure → implement → run to confirm pass → **commit** (one commit per task).

---

## Conventions (read before starting)

- **Tests:** `cd ai_server && pytest tests/path::test_name -v`. `asyncio_mode=auto` (no `@pytest.mark.asyncio` needed). Integration tests use `httpx.ASGITransport` against `app` (mirror `backend/tests/conftest.py`).
- **Env in tests:** set required env vars via `os.environ.setdefault(...)` in `conftest.py` BEFORE importing `app.main`.
- **Provider calls in tests:** never hit real APIs — monkeypatch the provider adapter functions.
- **Commits:** one per task (after tests pass).
- **Ruff:** line-length 100, target py312.

---

## Task 1: Scaffold `ai_server` package + config

**Files:**
- Create: `ai_server/pyproject.toml`
- Create: `ai_server/.env.example`
- Create: `ai_server/app/__init__.py` (empty)
- Create: `ai_server/app/config.py`
- Create: `ai_server/tests/__init__.py` (empty), `ai_server/tests/unit/__init__.py` (empty)
- Test: `ai_server/tests/unit/test_config.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "ai-server"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.118",
  "uvicorn[standard]>=0.32",
  "pydantic>=2.10",
  "pydantic-settings>=2.7",
  "sse-starlette>=2.1",
  "httpx>=0.28",
  "pyjwt[crypto]>=2.10",
  "anthropic>=0.50",
  "openai>=1.60",
  "google-genai>=0.3",
]

[project.optional-dependencies]
dev = ["pytest>=8.4", "pytest-asyncio>=0.25", "ruff>=0.9", "mypy>=1.14"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 2: Write `.env.example`**

```
AI_SERVICE_SECRET=change-me-shared-static-secret
SESSION_SIGNING_SECRET=change-me-jwt-signing-secret
SESSION_TOKEN_TTL_SECONDS=300
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

- [ ] **Step 3: Write the failing test** — `ai_server/tests/unit/test_config.py`

```python
import os

os.environ.setdefault("AI_SERVICE_SECRET", "svc-secret")
os.environ.setdefault("SESSION_SIGNING_SECRET", "sign-secret")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("GEMINI_API_KEY", "gem-test")

from app.config import get_settings


def test_settings_load_from_env():
    s = get_settings()
    assert s.ai_service_secret == "svc-secret"
    assert s.session_signing_secret == "sign-secret"
    assert s.session_token_ttl_seconds == 300  # default
    assert s.anthropic_api_key == "sk-ant-test"
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd ai_server && pytest tests/unit/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.config'`

- [ ] **Step 5: Write `app/config.py`**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    ai_service_secret: str
    session_signing_secret: str
    session_token_ttl_seconds: int = 300

    anthropic_api_key: str
    openai_api_key: str
    gemini_api_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd ai_server && pytest tests/unit/test_config.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add ai_server/pyproject.toml ai_server/.env.example ai_server/app/__init__.py ai_server/app/config.py ai_server/tests/
git commit -m "feat(ai-server): scaffold package and config"
```

---

## Task 2: Session-token mint + verify  *(PARALLEL BATCH)*

**Files:**
- Create: `ai_server/app/security/__init__.py` (empty)
- Create: `ai_server/app/security/session_token.py`
- Test: `ai_server/tests/unit/test_session_token.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai_server && pytest tests/unit/test_session_token.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `app/security/session_token.py`**

```python
from __future__ import annotations

import datetime as _dt
import uuid

import jwt


class SessionTokenError(Exception):
    """Raised when a session token cannot be minted or verified."""


def mint_session_token(
    agent: str,
    server_context: dict,
    signing_secret: str,
    ttl_seconds: int,
) -> str:
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    payload = {
        "agent": agent,
        "server_context": server_context,
        "iat": now,
        "exp": now + _dt.timedelta(seconds=ttl_seconds),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, signing_secret, algorithm="HS256")


def verify_session_token(token: str, signing_secret: str) -> dict:
    try:
        return jwt.decode(
            token,
            signing_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "agent"]},
        )
    except jwt.PyJWTError as exc:
        raise SessionTokenError(str(exc)) from exc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai_server && pytest tests/unit/test_session_token.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add ai_server/app/security/__init__.py ai_server/app/security/session_token.py ai_server/tests/unit/test_session_token.py
git commit -m "feat(ai-server): session token mint and verify"
```

---

## Task 3: Service-secret dependency  *(PARALLEL BATCH)*

**Files:**
- Create: `ai_server/app/security/service_secret.py`
- Test: `ai_server/tests/unit/test_service_secret.py`

> **Parallel-batch note:** this task creates `app/security/service_secret.py`. The `app/security/__init__.py` empty file is also created by Task 2 — if running in parallel, whichever subagent lands first creates it; the file is empty so there is no conflict. To be safe, this task may also `git add` `ai_server/app/security/__init__.py` only if it does not already exist.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai_server && pytest tests/unit/test_service_secret.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `app/security/service_secret.py`**

```python
import hmac

from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_service_secret(
    authorization: str | None,
    expected: str,
) -> None:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing service secret")
    presented = authorization.split(" ", 1)[1]
    if not hmac.compare_digest(presented, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid service secret")


async def service_secret_guard(authorization: str | None = Header(default=None)) -> None:
    require_service_secret(authorization, get_settings().ai_service_secret)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai_server && pytest tests/unit/test_service_secret.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add ai_server/app/security/service_secret.py ai_server/tests/unit/test_service_secret.py
git commit -m "feat(ai-server): service-secret guard with constant-time compare"
```

---

## Task 4: Signed result events (sign + verify)  *(PARALLEL BATCH)*

**Files:**
- Create: `ai_server/app/security/result_signing.py`
- Test: `ai_server/tests/unit/test_result_signing.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai_server && pytest tests/unit/test_result_signing.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `app/security/result_signing.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai_server && pytest tests/unit/test_result_signing.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add ai_server/app/security/result_signing.py ai_server/tests/unit/test_result_signing.py
git commit -m "feat(ai-server): signed result events for stream persistence"
```

---

## Task 5: App skeleton + `/healthz`

**Files:**
- Create: `ai_server/app/transport/__init__.py` (empty)
- Create: `ai_server/app/transport/router.py`
- Create: `ai_server/app/main.py`
- Create: `ai_server/tests/conftest.py`
- Create: `ai_server/tests/integration/__init__.py` (empty)
- Test: `ai_server/tests/integration/test_healthz.py`

- [ ] **Step 1: Write `tests/conftest.py`**

```python
import os

os.environ.setdefault("AI_SERVICE_SECRET", "svc-secret")
os.environ.setdefault("SESSION_SIGNING_SECRET", "sign-secret")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("GEMINI_API_KEY", "gem-test")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 2: Write the failing test** — `tests/integration/test_healthz.py`

```python
async def test_healthz(client):
    resp = await client.get("/v1/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd ai_server && pytest tests/integration/test_healthz.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 4: Write `app/transport/router.py`**

```python
from fastapi import APIRouter

v1 = APIRouter(prefix="/v1")


@v1.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
```

- [ ] **Step 5: Write `app/main.py`**

```python
from fastapi import FastAPI

from app.transport.router import v1


def create_app() -> FastAPI:
    app = FastAPI(title="AI Server")
    app.include_router(v1)
    return app


app = create_app()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd ai_server && pytest tests/integration/test_healthz.py -v`
Expected: PASS

- [ ] **Step 7: Run the full Phase 1 suite**

Run: `cd ai_server && pytest -v`
Expected: all pass (config + 3 security modules + healthz).

- [ ] **Step 8: Commit**

```bash
git add ai_server/app/main.py ai_server/app/transport/ ai_server/tests/conftest.py ai_server/tests/integration/
git commit -m "feat(ai-server): app skeleton with /v1/healthz"
```

---

## Phase 1 Exit Criteria

- [ ] `cd ai_server && pytest -v` — all tests pass.
- [ ] Package imports cleanly: `app.config`, `app.security.{session_token,service_secret,result_signing}`, `app.main`.
- [ ] No DB, no Clerk, no provider calls in Phase 1 code.
- [ ] One commit per task (5 commits total).
