from openai import AsyncOpenAI

from app.config import get_settings

openai_client = AsyncOpenAI(api_key=get_settings().openai_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    resp = await openai_client.embeddings.create(
        input=texts,
        model="text-embedding-3-small",
    )
    return [item.embedding for item in resp.data]
