from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
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
) -> StreamingResponse:
    return StreamingResponse(synthesize_speech(body.text), media_type="audio/mpeg")
