import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.transport.router import v1


def _cors_origins() -> list[str]:
    """Browser calls /v1/reason and /v1/speak directly after Next mints a JWT.
    Comma-separated CORS_ORIGINS or ALLOWED_ORIGINS; defaults include local Next.
    """
    raw = os.getenv("CORS_ORIGINS") or os.getenv("ALLOWED_ORIGINS") or ""
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins:
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    return origins


def create_app() -> FastAPI:
    app = FastAPI(title="AI Server")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )
    app.include_router(v1)
    return app


app = create_app()
