from backend.app.routers.auth import router as auth_router
from backend.app.routers.users import router as users_router
from backend.app.routers.patients import router as patients_router
from backend.app.routers.reports import router as reports_router
from backend.app.routers.documents import router as documents_router
from backend.app.routers.timeline import router as timeline_router
from backend.app.routers.chat import router as chat_router
from backend.app.routers.summaries import router as summaries_router
from backend.app.routers.search import router as search_router
from backend.app.routers.audit import router as audit_router
from backend.app.routers.fhir import router as fhir_router
from backend.app.routers.purge import router as purge_router
from backend.app.routers.graph import router as graph_router
from backend.app.routers.settings_router import router as settings_router
from backend.app.routers.hospitals import router as hospitals_router
from backend.app.routers.alerts import router as alerts_router
from backend.app.routers.tts import router as tts_router

__all__ = [
    "auth_router",
    "users_router",
    "patients_router",
    "reports_router",
    "documents_router",
    "timeline_router",
    "chat_router",
    "summaries_router",
    "search_router",
    "audit_router",
    "fhir_router",
    "purge_router",
    "graph_router",
    "settings_router",
    "hospitals_router",
    "alerts_router",
    "tts_router",
]
