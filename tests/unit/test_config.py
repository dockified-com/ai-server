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
