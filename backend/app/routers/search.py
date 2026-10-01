from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.search import GlobalSearchResponse
from backend.app.services.auth_service import get_current_patient
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import Disease, Medication
from backend.app.models.timeline import TimelineEvent

router = APIRouter(prefix="/search", tags=["Global Intelligence Search"])


@router.get("", response_model=GlobalSearchResponse)
def global_search(
    q: str = Query(..., min_length=1),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    search_term = f"%{q.lower()}%"

    reports = db.query(MedicalReport).filter(
        MedicalReport.patient_id == current_patient.id,
        (MedicalReport.title.ilike(search_term)) |
        (MedicalReport.hospital_name.ilike(search_term)) |
        (MedicalReport.summary.ilike(search_term))
    ).limit(5).all()

    diseases = db.query(Disease).filter(
        Disease.patient_id == current_patient.id,
        (Disease.name.ilike(search_term)) |
        (Disease.notes.ilike(search_term))
    ).limit(5).all()

    timeline_events = db.query(TimelineEvent).filter(
        TimelineEvent.patient_id == current_patient.id,
        (TimelineEvent.title.ilike(search_term)) |
        (TimelineEvent.description.ilike(search_term))
    ).limit(5).all()

    medications = db.query(Medication).filter(
        Medication.patient_id == current_patient.id,
        (Medication.name.ilike(search_term)) |
        (Medication.indication.ilike(search_term))
    ).limit(5).all()

    matched_reports = [{"id": r.id, "title": r.title, "hospitalName": r.hospital_name, "reportDate": r.report_date} for r in reports]
    matched_diseases = [{"id": d.id, "name": d.name, "diagnosedDate": d.diagnosed_date, "status": d.status} for d in diseases]
    matched_events = [{"id": e.id, "title": e.title, "date": e.date, "type": e.event_type} for e in timeline_events]
    matched_meds = [{"id": m.id, "name": m.name, "dosage": m.dosage, "status": m.status} for m in medications]

    total_matches = len(matched_reports) + len(matched_diseases) + len(matched_events) + len(matched_meds)

    return GlobalSearchResponse(
        query=q,
        totalMatches=total_matches,
        reports=matched_reports,
        diseases=matched_diseases,
        timelineEvents=matched_events,
        medications=matched_meds
    )
