from backend.app.routers.auth import router as auth_router
from backend.app.routers.users import router as users_router
from backend.app.routers.patients import router as patients_router
from backend.app.routers.reports import router as reports_router
from backend.app.routers.documents import router as documents_router
from backend.app.routers.timeline import router as timeline_router
from backend.app.routers.chat import router as chat_router
from backend.app.routers.summaries import router as summaries_router
from backend.app.routers.search import router as search_router

__all__ = [
    "auth_router",
    "users_router",
    "patients_router",
    "reports_router",
    "documents_router",
    "timeline_router",
    "chat_router",
    "summaries_router",
    "search_router"
]
