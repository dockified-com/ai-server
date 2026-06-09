from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.transport.router import v1


def create_app() -> FastAPI:
    app = FastAPI(title="AI Server")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(v1)
    return app


app = create_app()
