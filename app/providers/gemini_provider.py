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


def _pcm_s16le_to_wav(
    pcm: bytes,
    *,
    sample_rate: int = 24_000,
    channels: int = 1,
) -> bytes:
    """Wrap raw little-endian 16-bit PCM in a WAV container for browser <audio>."""
    import struct

    byte_rate = sample_rate * channels * 2
    block_align = channels * 2
    data_size = len(pcm)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,  # PCM fmt chunk size
        1,  # audio format = PCM
        channels,
        sample_rate,
        byte_rate,
        block_align,
        16,  # bits per sample
        b"data",
        data_size,
    )
    return header + pcm


def _normalize_audio_bytes(data: bytes | str) -> bytes:
    if isinstance(data, str):
        import base64

        return base64.b64decode(data)
    return data


async def synthesize_speech(text: str) -> AsyncGenerator[bytes, None]:
    """Yield a single browser-playable audio blob (WAV).

    Gemini TTS returns raw PCM (s16le), not MPEG. Labeling it audio/mpeg left
    the Next.js client with a silent <audio> element (decode/play failure).
    """
    stream = await gemini_client.aio.models.generate_content_stream(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(response_modalities=["AUDIO"]),
    )
    pcm_chunks: list[bytes] = []
    mime = ""
    async for chunk in stream:
        candidates = getattr(chunk, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if content is None:
                continue
            for part in getattr(content, "parts", None) or []:
                inline = getattr(part, "inline_data", None)
                if not inline:
                    continue
                data = getattr(inline, "data", None)
                if not data:
                    continue
                raw = _normalize_audio_bytes(data)
                mime = (getattr(inline, "mime_type", None) or mime or "").lower()
                pcm_chunks.append(raw)

    if not pcm_chunks:
        return

    audio = b"".join(pcm_chunks)
    # Already a container format — pass through
    if audio[:4] == b"RIFF" or audio[:3] == b"ID3" or (
        len(audio) > 2 and audio[0] == 0xFF and (audio[1] & 0xE0) == 0xE0
    ):
        yield audio
        return

    # Raw PCM / L16 from Gemini TTS → WAV for browser playback
    if "wav" in mime:
        yield audio
        return
    yield _pcm_s16le_to_wav(audio)

