import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.report import ReportResponse
from backend.app.services.auth_service import get_current_patient
from backend.app.services.storage_service import storage_service
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import ExtractedEntity
from backend.app.routers.reports import format_report_response
from backend.app.ai.ingestion import (
    ingestion_registry,
    document_orchestrator,
    IngestionStatus,
    IngestionStage
)

router = APIRouter(prefix="/documents", tags=["Document Vault"])

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


def run_background_ingestion(
    document_id: str,
    file_bytes: bytes,
    file_name: str,
    patient_id: str,
    report_date: str,
    hospital_name: str
):
    """Background task worker for full document ingestion pipeline."""
    document_orchestrator.process_document(
        document_id=document_id,
        file_bytes=file_bytes,
        file_name=file_name,
        patient_id=patient_id,
        report_date=report_date,
        hospital_name=hospital_name
    )


@router.post("/upload", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form("blood_report"),
    hospital_name: str = Form("General Hospital"),
    doctor_name: str = Form(None),
    report_date: str = Form(None),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format '{ext}'. Only PDF documents are supported."
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    await file.seek(0)

    # Save to storage service
    file_id, storage_path, file_size = await storage_service.save_file(file)
    date_str = report_date or datetime.now().strftime("%Y-%m-%d")

    # Create Report record in Vault
    report = MedicalReport(
        patient_id=current_patient.id,
        title=os.path.splitext(file.filename)[0].replace("_", " ").title(),
        file_name=file.filename,
        file_size=file_size,
        file_type=file.content_type or "application/pdf",
        category=category,
        hospital_name=hospital_name,
        doctor_name=doctor_name,
        report_date=date_str,
        confidence_score=0.98,
        storage_path=storage_path,
        status="processing",
        summary=f"Processing {file.filename} through Document Intelligence Pipeline...",
        raw_text=""
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Initialize Ingestion Status Tracker
    ingestion_registry.set_status(
        document_id=report.id,
        stage=IngestionStage.RECEIVED,
        progress=5,
        message="Document uploaded. Queued for ingestion and entity extraction."
    )

    # Dispatch Asynchronous Background Ingestion Task
    background_tasks.add_task(
        run_background_ingestion,
        document_id=report.id,
        file_bytes=file_bytes,
        file_name=file.filename,
        patient_id=current_patient.id,
        report_date=date_str,
        hospital_name=hospital_name
    )

    return format_report_response(report)


@router.get("/{document_id}/status", response_model=IngestionStatus)
def get_document_ingestion_status(
    document_id: str,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Returns live ingestion status, stage, progress percentage, and extracted counts.
    """
    report = db.query(MedicalReport).filter(
        MedicalReport.id == document_id,
        MedicalReport.patient_id == current_patient.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return ingestion_registry.get_status(document_id)


@router.get("", response_model=list[ReportResponse])
def get_documents(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    reports = db.query(MedicalReport).filter(MedicalReport.patient_id == current_patient.id).order_by(MedicalReport.report_date.desc()).all()
    return [format_report_response(r) for r in reports]


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    report = db.query(MedicalReport).filter(
        MedicalReport.id == document_id,
        MedicalReport.patient_id == current_patient.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not report.storage_path or not os.path.exists(report.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File content not found on server storage")

    return FileResponse(
        path=report.storage_path,
        filename=report.file_name,
        media_type=report.file_type
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    report = db.query(MedicalReport).filter(
        MedicalReport.id == document_id,
        MedicalReport.patient_id == current_patient.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if report.storage_path:
        storage_service.delete_file(report.storage_path)

    db.delete(report)
    db.commit()
    return {"message": "Document removed from vault", "id": document_id}
