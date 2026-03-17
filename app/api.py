from fastapi import FastAPI

from app.routers import auth_router, documents_router
from app.utils.logger import logger


def create_app() -> FastAPI:
    app = FastAPI(title="Medicoder API")

    @app.on_event("startup")
    def on_startup() -> None:
        logger.info("Application startup complete.")

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(documents_router)
    return app


app = create_app()
