import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.providers.gemini_provider import synthesize_speech
from app.security.session_token import require_session_claims

router = APIRouter()
logger = logging.getLogger(__name__)


class SpeakRequest(BaseModel):
    text: str


@router.post("/speak")
async def speak_endpoint(
    body: SpeakRequest,
    claims: dict = Depends(require_session_claims),
) -> Response:
    # Buffer full WAV. Streaming empty/partial bodies broke browser playback.
    try:
        chunks: list[bytes] = []
        async for chunk in synthesize_speech(body.text):
            if chunk:
                chunks.append(chunk)
        audio = b"".join(chunks)
    except Exception as exc:  # noqa: BLE001 — map provider errors to clear HTTP
        msg = str(exc)
        logger.exception("TTS synthesize failed: %s", msg)
        if (
            "429" in msg
            or "RESOURCE_EXHAUSTED" in msg
            or "quota" in msg.lower()
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini TTS quota exceeded (free tier ~10 requests/day for "
                    "gemini-2.5-flash-tts). Wait and retry, enable billing, or "
                    "use browser speech fallback on the client."
                ),
            ) from exc
        raise HTTPException(
            status_code=502,
            detail=f"TTS provider error: {msg[:280]}",
        ) from exc

    if not audio:
        raise HTTPException(status_code=502, detail="TTS produced no audio")
    media = "audio/wav" if audio[:4] == b"RIFF" else "audio/mpeg"
    return Response(
        content=audio,
        media_type=media,
        headers={"Cache-Control": "no-store", "Content-Length": str(len(audio))},
    )
