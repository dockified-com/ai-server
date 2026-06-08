from fastapi import FastAPI

from app.transport.router import v1


def create_app() -> FastAPI:
    app = FastAPI(title="AI Server")
    app.include_router(v1)
    return app


app = create_app()
