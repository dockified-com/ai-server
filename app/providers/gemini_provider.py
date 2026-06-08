from collections.abc import AsyncGenerator

from google import genai
from google.genai import types

from app.config import get_settings

gemini_client = genai.Client(api_key=get_settings().gemini_api_key)

TTS_MODEL = "gemini-2.5-flash-preview-tts"


async def synthesize_speech(text: str) -> AsyncGenerator[bytes, None]:
    """Stream TTS audio bytes for `text`. All google-genai SDK specifics live
    here so only this function changes if the SDK signature differs."""
    stream = await gemini_client.aio.models.generate_content_stream(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(response_modalities=["AUDIO"]),
    )
    async for chunk in stream:
        candidates = getattr(chunk, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if content is None:
                continue
            for part in getattr(content, "parts", None) or []:
                inline = getattr(part, "inline_data", None)
                data = getattr(inline, "data", None) if inline else None
                if data:
                    yield data
