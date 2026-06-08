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
