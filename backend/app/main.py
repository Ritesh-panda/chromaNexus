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
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed initial demo patient profile (Alex Vance)
    db = SessionLocal()
    try:
        seed_initial_data(db)
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


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get("/")
def root():
    return {
        "message": "Welcome to ChronaNexus API",
        "docs": "/docs",
        "health": "/health",
        "version": settings.VERSION
    }
