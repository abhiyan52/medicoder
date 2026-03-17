from fastapi import FastAPI

from app.database import Base, engine
from app.routers import documents_router


def create_app() -> FastAPI:
    app = FastAPI(title="Medicoder API")

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(documents_router)
    return app


app = create_app()
