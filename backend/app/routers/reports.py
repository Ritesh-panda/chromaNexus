from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.report import ReportResponse, ReportCreate, ReportUpdate, ExtractedEntitySchema
from backend.app.services.auth_service import get_current_patient
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import ExtractedEntity

router = APIRouter(prefix="/reports", tags=["Reports"])


def format_report_response(report: MedicalReport) -> ReportResponse:
    entities = [
        ExtractedEntitySchema(
            category=e.category,
            name=e.name,
            confidence=e.confidence,
            value=e.value,
            unit=e.unit,
            notes=e.notes
        ) for e in report.extracted_entities
    ]
    return ReportResponse(
        id=report.id,
        title=report.title,
        fileName=report.file_name,
        fileSize=report.file_size or 0,
        fileType=report.file_type or "application/pdf",
        category=report.category,
        hospitalName=report.hospital_name,
        doctorName=report.doctor_name,
        reportDate=report.report_date,
        uploadDate=report.upload_date.isoformat() if report.upload_date else datetime.now().isoformat(),
        status=report.status or "completed",
        confidenceScore=report.confidence_score or 0.98,
        rawText=report.raw_text,
        summary=report.summary,
        fileUrl=report.file_url,
        extractedEntities=entities
    )


@router.get("", response_model=List[ReportResponse])
def get_reports(
    category: Optional[str] = Query(None),
    hospital: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    query = db.query(MedicalReport).filter(MedicalReport.patient_id == current_patient.id)
    if category and category != "all":
        query = query.filter(MedicalReport.category == category)
    if hospital and hospital != "all":
        query = query.filter(MedicalReport.hospital_name.ilike(f"%{hospital}%"))
    if search:
        query = query.filter(
            (MedicalReport.title.ilike(f"%{search}%")) |
            (MedicalReport.hospital_name.ilike(f"%{search}%")) |
            (MedicalReport.summary.ilike(f"%{search}%"))
        )
    
    reports = query.order_by(MedicalReport.report_date.desc()).all()
    return [format_report_response(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.patient_id == current_patient.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical report not found")
    return format_report_response(report)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    report_in: ReportCreate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    report_date = report_in.reportDate or datetime.now().strftime("%Y-%m-%d")
    report = MedicalReport(
        patient_id=current_patient.id,
        title=report_in.title,
        file_name=f"{report_in.title.lower().replace(' ', '_')}.pdf",
        category=report_in.category,
        hospital_name=report_in.hospitalName,
        doctor_name=report_in.doctorName,
        report_date=report_date,
        summary=f"Processed {report_in.category} from {report_in.hospitalName}."
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return format_report_response(report)


@router.put("/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: str,
    report_update: ReportUpdate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.patient_id == current_patient.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical report not found")

    if report_update.title is not None:
        report.title = report_update.title
    if report_update.category is not None:
        report.category = report_update.category
    if report_update.hospitalName is not None:
        report.hospital_name = report_update.hospitalName
    if report_update.doctorName is not None:
        report.doctor_name = report_update.doctorName
    if report_update.summary is not None:
        report.summary = report_update.summary
    if report_update.status is not None:
        report.status = report_update.status

    db.commit()
    db.refresh(report)
    return format_report_response(report)


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
def delete_report(
    report_id: str,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.patient_id == current_patient.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical report not found")

    db.delete(report)
    db.commit()
    return {"message": "Report deleted successfully", "id": report_id}
