from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.summary import DoctorSummaryResponse
from backend.app.services.auth_service import get_current_patient
from backend.app.services.summary_service import generate_doctor_summary_for_patient
from backend.app.models.patient import Patient
from backend.app.models.summary import DoctorSummary

router = APIRouter(prefix="/summaries", tags=["Doctor Summary Engine"])


def format_summary_response(summary: DoctorSummary) -> DoctorSummaryResponse:
    return DoctorSummaryResponse(
        patientName=summary.patient_name,
        age=summary.age or 38,
        gender=summary.gender or "Male (38M)",
        generatedAt=summary.generated_at.isoformat() if summary.generated_at else "",
        summaryOverview=summary.summary_overview,
        currentDiseases=summary.current_diseases or [],
        pastDiseases=summary.past_diseases or [],
        activeMedications=summary.active_medications or [],
        knownAllergies=summary.known_allergies or [],
        abnormalLabs=summary.abnormal_labs or [],
        riskFactors=summary.risk_factors or [],
        recentReports=summary.recent_reports or [],
        timelineHighlights=summary.timeline_highlights or [],
        shareLink=f"https://chronanexus.app/physician-view/{summary.share_token}" if summary.share_token else None
    )


@router.post("/generate", response_model=DoctorSummaryResponse)
def generate_summary(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    summary = generate_doctor_summary_for_patient(db, current_patient)
    return format_summary_response(summary)


@router.get("/latest", response_model=DoctorSummaryResponse)
def get_latest_summary(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    summary = db.query(DoctorSummary).filter(DoctorSummary.patient_id == current_patient.id).order_by(DoctorSummary.generated_at.desc()).first()
    if not summary:
        summary = generate_doctor_summary_for_patient(db, current_patient)
    return format_summary_response(summary)


@router.get("/share/{share_token}", response_model=DoctorSummaryResponse)
def get_shared_summary(share_token: str, db: Session = Depends(get_db)):
    summary = db.query(DoctorSummary).filter(DoctorSummary.share_token == share_token).first()
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physician share link expired or not found")
    return format_summary_response(summary)
