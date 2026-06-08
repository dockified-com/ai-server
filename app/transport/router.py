from fastapi import APIRouter

from app.transport.embed_routes import router as embed_router

v1 = APIRouter(prefix="/v1")


@v1.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


v1.include_router(embed_router)
