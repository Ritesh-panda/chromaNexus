import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure project root is in sys.path so 'backend.app...' imports always resolve
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.models import (
    User, Patient, MedicalReport, ExtractedEntity, Disease, Medication, LabResult, TimelineEvent, ChatConversation, ChatMessage, DoctorSummary
)
from backend.app.services.seed_data import seed_initial_data
from backend.app.routers import (
    auth_router,
    users_router,
    patients_router,
    reports_router,
    documents_router,
    timeline_router,
    chat_router,
    summaries_router,
    search_router,
    audit_router,
    fhir_router,
    purge_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    # Retrieve engine and session_factory from app.state if overridden for testing
    current_engine = getattr(app.state, "engine", engine)
    current_session_factory = getattr(app.state, "session_factory", SessionLocal)

    is_test_env = bool(
        os.environ.get("PYTEST_CURRENT_TEST") or
        os.environ.get("CHRONANEXUS_TEST_ENV")
    )
    # If running in test mode and app.state has not provided an explicit isolated test engine,
    # skip table creation and seeding on the default production engine to prevent unintended mutation.
    if is_test_env and not hasattr(app.state, "engine"):
        yield
        return

    # Initialize database tables
    Base.metadata.create_all(bind=current_engine)
    
    # Auto-seed initial demo patient profile (Alex Vance)
    db = current_session_factory()
    try:
        seed_initial_data(db)
        
        # Initialize persistent ChromaDB vector store and sync pre-existing chunks non-destructively
        try:
            from backend.app.ai.retrieval import get_vector_store, ChromaDBVectorStore
            v_store = get_vector_store(db_session=db)
            if isinstance(v_store, ChromaDBVectorStore):
                v_store.sync_from_db(db)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"ChromaDB startup sync notice: {e}")
    finally:
        db.close()
    
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Privacy-First Longitudinal Medical Intelligence Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api/v1
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(patients_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(timeline_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(summaries_router, prefix=settings.API_V1_STR)
app.include_router(search_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(fhir_router, prefix=settings.API_V1_STR)
app.include_router(purge_router, prefix=settings.API_V1_STR)


@app.get("/health")
@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    """Liveness probe: verifies process is alive and accepting connections."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get("/ready")
@app.get(f"{settings.API_V1_STR}/ready")
def readiness_check():
    """
    Readiness probe: validates all underlying infrastructure dependencies
    (Database, Vector Store, Storage Root, Inference Provider).
    Returns HTTP 200 when ready to serve patient traffic, HTTP 503 if critical dependencies are down.
    """
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    import time
    import os

    components = {}
    is_ready = True

    # 1. Database check
    db_start = time.time()
    try:
        session_factory = getattr(app.state, "session_factory", SessionLocal)
        db = session_factory()
        try:
            db.execute(text("SELECT 1"))
            components["database"] = {
                "status": "connected",
                "latency_ms": round((time.time() - db_start) * 1000, 2)
            }
        finally:
            db.close()
    except Exception as e:
        is_ready = False
        components["database"] = {
            "status": "unreachable",
            "error": str(e)
        }

    # 2. Vector Store check
    try:
        from backend.app.ai.retrieval import get_vector_store
        v_store = get_vector_store()
        v_ok = v_store.health_check()
        components["vector_store"] = {
            "backend": settings.VECTOR_STORE_BACKEND,
            "status": "operational" if v_ok else "degraded"
        }
    except Exception as e:
        components["vector_store"] = {
            "backend": settings.VECTOR_STORE_BACKEND,
            "status": "error",
            "error": str(e)
        }

    # 3. Storage directory check
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        probe_file = os.path.join(settings.UPLOAD_DIR, ".readiness_probe")
        with open(probe_file, "w") as f:
            f.write("probe")
        os.remove(probe_file)
        components["storage"] = {
            "path": settings.UPLOAD_DIR,
            "status": "writable"
        }
    except Exception as e:
        components["storage"] = {
            "path": settings.UPLOAD_DIR,
            "status": "read_only_or_missing",
            "error": str(e)
        }

    # 4. LLM provider status
    try:
        from backend.app.ai.llm import get_llm_provider
        llm = get_llm_provider()
        llm_ok = llm.health_check()
        components["inference_provider"] = {
            "provider": llm.provider_name,
            "status": "available" if llm_ok else "offline_or_mock"
        }
    except Exception as e:
        components["inference_provider"] = {
            "status": "unconfigured",
            "error": str(e)
        }

    payload = {
        "status": "ready" if is_ready else "not_ready",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "components": components
    }

    if not is_ready:
        return JSONResponse(status_code=503, content=payload)
    return payload


@app.get("/")
def root():
    return {
        "message": "Welcome to ChronaNexus API",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "version": settings.VERSION
    }

