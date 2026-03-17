from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router

__all__ = ["documents_router", "auth_router"]
