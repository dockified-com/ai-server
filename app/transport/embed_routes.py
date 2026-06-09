from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.providers.gemini_provider import embed_texts
from app.security.service_secret import service_secret_guard

router = APIRouter()


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    vectors: list[list[float]]


@router.post("/embed", response_model=EmbedResponse, dependencies=[Depends(service_secret_guard)])
async def embed_endpoint(body: EmbedRequest) -> EmbedResponse:
    vectors = await embed_texts(body.texts)
    return EmbedResponse(vectors=vectors)