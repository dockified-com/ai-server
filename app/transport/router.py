from fastapi import APIRouter

v1 = APIRouter(prefix="/v1")


@v1.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
