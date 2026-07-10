from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.providers.gemini_provider import synthesize_speech
from app.security.session_token import require_session_claims

router = APIRouter()


class SpeakRequest(BaseModel):
    text: str


@router.post("/speak")
async def speak_endpoint(
    body: SpeakRequest,
    claims: dict = Depends(require_session_claims),
) -> Response:
    # Buffer full WAV. Streaming empty/partial bodies broke browser playback
    # (Next blob() got 0 bytes even when Gemini succeeded in-process).
    chunks: list[bytes] = []
    async for chunk in synthesize_speech(body.text):
        if chunk:
            chunks.append(chunk)
    audio = b"".join(chunks)
    if not audio:
        raise HTTPException(status_code=502, detail="TTS produced no audio")
    media = "audio/wav" if audio[:4] == b"RIFF" else "audio/mpeg"
    return Response(
        content=audio,
        media_type=media,
        headers={"Cache-Control": "no-store", "Content-Length": str(len(audio))},
    )
