from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.report import ReportResponse, ReportCreate, ReportUpdate, ExtractedEntitySchema
from backend.app.services.auth_service import get_current_patient
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import ExtractedEntity, Disease, Medication, LabResult
from backend.app.models.allergy import Allergy
from backend.app.services.audit_service import log_audit_event

router = APIRouter(prefix="/reports", tags=["Reports"])


def format_report_response(report: MedicalReport, linked_entities: Optional[Dict[str, Any]] = None) -> ReportResponse:
    entities = [
        ExtractedEntitySchema(
            category=e.category,
            name=e.name,
            confidence=e.confidence,
            value=e.value,
            unit=e.unit,
            notes=e.notes,
            sourcePageNumber=getattr(e, 'source_page_number', None)
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
        checksum=getattr(report, 'checksum', None),
        contentChecksum=getattr(report, 'content_checksum', None),
        pageCount=getattr(report, 'page_count', 1),
        extractedEntities=entities,
        linkedEntities=linked_entities
    )


@router.get("/facilities", response_model=List[str])
def get_report_facilities(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    rows = db.query(MedicalReport.hospital_name).filter(
        MedicalReport.patient_id == current_patient.id,
        MedicalReport.hospital_name.isnot(None)
    ).distinct().all()
    facilities = sorted(list({r[0] for r in rows if r[0]}))
    return facilities


@router.get("", response_model=List[ReportResponse])
def get_reports(
    category: Optional[str] = Query(None),
    hospital: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("clinical_date", description="'clinical_date' or 'upload_date'"),
    sort_order: Optional[str] = Query("desc", description="'asc' or 'desc'"),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    query = db.query(MedicalReport).filter(MedicalReport.patient_id == current_patient.id)
    if category and category != "all":
        query = query.filter(MedicalReport.category == category)
    if hospital and hospital != "all":
        query = query.filter(MedicalReport.hospital_name.ilike(f"%{hospital}%"))
    if status and status != "all":
        query = query.filter(MedicalReport.status == status)
    if start_date:
        query = query.filter(MedicalReport.report_date >= start_date)
    if end_date:
        query = query.filter(MedicalReport.report_date <= end_date)
    if search:
        query = query.filter(
            (MedicalReport.title.ilike(f"%{search}%")) |
            (MedicalReport.hospital_name.ilike(f"%{search}%")) |
            (MedicalReport.summary.ilike(f"%{search}%")) |
            (MedicalReport.file_name.ilike(f"%{search}%"))
        )
    
    # Sorting: distinguish clinical_date from upload_date
    if sort_by == "upload_date":
        order_col = MedicalReport.upload_date.asc() if sort_order.lower() == "asc" else MedicalReport.upload_date.desc()
    else:
        order_col = MedicalReport.report_date.asc() if sort_order.lower() == "asc" else MedicalReport.report_date.desc()
    
    reports = query.order_by(order_col).all()
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
        foreign = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
        if foreign:
            log_audit_event(
                db=db,
                action="IDOR_BLOCKED",
                outcome="DENIED",
                patient_id=current_patient.id,
                resource_type="medical_report",
                resource_id=report_id,
                details={"reason": "Attempted cross-patient report access"}
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical report not found")
    
    log_audit_event(
        db=db,
        action="REPORT_INSPECT",
        outcome="SUCCESS",
        patient_id=current_patient.id,
        resource_type="medical_report",
        resource_id=report_id,
        details={"title": report.title, "hospital": report.hospital_name}
    )

    # Fetch linked structured entities created or associated with this report
    labs = db.query(LabResult).filter(
        LabResult.patient_id == current_patient.id,
        LabResult.source_report_id == report_id
    ).all()
    meds = db.query(Medication).filter(
        Medication.patient_id == current_patient.id,
        Medication.source_report_id == report_id
    ).all()
    diseases = db.query(Disease).filter(
        Disease.patient_id == current_patient.id,
        Disease.source_report_id == report_id
    ).all()
    allergies = db.query(Allergy).filter(
        Allergy.patient_id == current_patient.id,
        Allergy.source_report_id == report_id
    ).all()

    linked = {
        "labResults": [
            {
                "id": lr.id,
                "testName": lr.test_name,
                "value": lr.value,
                "unit": lr.unit,
                "referenceRange": lr.reference_range,
                "status": lr.status,
                "testDate": lr.test_date,
                "sourcePageNumber": lr.source_page_number
            } for lr in labs
        ],
        "medications": [
            {
                "id": m.id,
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "status": m.status,
                "startDate": m.start_date,
                "endDate": m.end_date,
                "sourcePageNumber": m.source_page_number
            } for m in meds
        ],
        "diseases": [
            {
                "id": d.id,
                "name": d.name,
                "icdCode": d.icd_code,
                "status": d.status,
                "diagnosedDate": d.diagnosed_date,
                "sourcePageNumber": d.source_page_number
            } for d in diseases
        ],
        "allergies": [
            {
                "id": a.id,
                "allergen": a.allergen,
                "category": a.category,
                "severity": a.severity,
                "reaction": a.reaction,
                "status": a.status,
                "sourcePageNumber": a.source_page_number
            } for a in allergies
        ]
    }

    return format_report_response(report, linked_entities=linked)


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
