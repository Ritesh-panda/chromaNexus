from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.summary import DoctorSummaryResponse, DoctorQuestionsUpdate
from backend.app.services.auth_service import get_current_patient
from backend.app.services.summary_service import generate_doctor_summary_for_patient
from backend.app.models.patient import Patient
from backend.app.models.summary import DoctorSummary
from backend.app.services.audit_service import log_audit_event

router = APIRouter(prefix="/summaries", tags=["Doctor Summary Engine"])


@router.post("/generate", response_model=DoctorSummaryResponse)
def generate_summary(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    summary_data = generate_doctor_summary_for_patient(db, current_patient)
    log_audit_event(
        db=db,
        action="SUMMARY_GENERATED",
        outcome="SUCCESS",
        patient_id=current_patient.id,
        resource_type="doctor_summary",
        details={"conditions_count": len(summary_data.get("currentDiseases", [])), "meds_count": len(summary_data.get("activeMedications", []))}
    )
    return DoctorSummaryResponse(**summary_data)


@router.get("/latest", response_model=DoctorSummaryResponse)
def get_latest_summary(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    summary_data = generate_doctor_summary_for_patient(db, current_patient)
    log_audit_event(
        db=db,
        action="SUMMARY_ACCESSED",
        outcome="SUCCESS",
        patient_id=current_patient.id,
        resource_type="doctor_summary"
    )
    return DoctorSummaryResponse(**summary_data)


@router.put("/questions", response_model=DoctorSummaryResponse)
@router.post("/questions", response_model=DoctorSummaryResponse)
def update_doctor_questions(
    questions_in: DoctorQuestionsUpdate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Allows patient to update their questions/notes for the doctor's appointment."""
    summary_data = generate_doctor_summary_for_patient(
        db, 
        current_patient, 
        doctor_questions=questions_in.questions
    )
    return DoctorSummaryResponse(**summary_data)


@router.get("/share/{share_token}", response_model=DoctorSummaryResponse)
def get_shared_summary(share_token: str, db: Session = Depends(get_db)):
    summary = db.query(DoctorSummary).filter(DoctorSummary.share_token == share_token).first()
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physician share link expired or not found")
    
    patient = db.query(Patient).filter(Patient.id == summary.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated patient record not found")
    
    summary_data = generate_doctor_summary_for_patient(db, patient)
    return DoctorSummaryResponse(**summary_data)
