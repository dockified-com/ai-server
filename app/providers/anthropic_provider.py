from anthropic import AsyncAnthropic

from app.config import get_settings

anthropic_client = AsyncAnthropic(api_key=get_settings().anthropic_api_key)
