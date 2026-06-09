from collections.abc import AsyncGenerator

from google import genai
from google.genai import types

from app.config import get_settings

gemini_client = genai.Client(api_key=get_settings().gemini_api_key)

TTS_MODEL = "gemini-2.5-flash-preview-tts"
TEXT_MODEL = "gemini-2.5-flash-lite"
EMBED_MODEL = "text-embedding-004"


async def generate_text(system_prompt: str, user_message: str, max_tokens: int, model: str = TEXT_MODEL) -> str:
    resp = await gemini_client.aio.models.generate_content(
        model=model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
        ),
    )
    return resp.text or ""


async def stream_text(system_prompt: str, user_message: str, max_tokens: int, model: str = TEXT_MODEL) -> AsyncGenerator[str, None]:
    async for chunk in await gemini_client.aio.models.generate_content_stream(
        model=model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
        ),
    ):
        if chunk.text:
            yield chunk.text


async def embed_texts(texts: list[str]) -> list[list[float]]:
    result = []
    for text in texts:
        resp = await gemini_client.aio.models.embed_content(
            model=EMBED_MODEL,
            contents=text,
        )
        result.append(resp.embeddings[0].values)
    return result


async def synthesize_speech(text: str) -> AsyncGenerator[bytes, None]:
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
