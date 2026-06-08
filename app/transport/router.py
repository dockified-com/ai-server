from fastapi import APIRouter

from app.transport.embed_routes import router as embed_router
from app.transport.reason_routes import router as reason_router
from app.transport.run_routes import router as run_router
from app.transport.speak_routes import router as speak_router
from app.transport.session_routes import router as session_router

v1 = APIRouter(prefix="/v1")


@v1.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


v1.include_router(embed_router)
v1.include_router(run_router)
v1.include_router(session_router)
v1.include_router(reason_router)
v1.include_router(speak_router)
