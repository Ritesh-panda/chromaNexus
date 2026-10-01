from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.patient import PatientResponse, PatientUpdate
from backend.app.services.auth_service import get_current_patient
from backend.app.models.patient import Patient

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/me", response_model=PatientResponse)
def get_patient_profile(current_patient: Patient = Depends(get_current_patient)):
    return PatientResponse(
        id=current_patient.id,
        userId=current_patient.user_id,
        dateOfBirth=current_patient.date_of_birth or "1988-04-12",
        gender=current_patient.gender or "male",
        bloodGroup=current_patient.blood_group or "O+",
        heightCm=current_patient.height_cm or 178.0,
        weightKg=current_patient.weight_kg or 82.0,
        primaryCarePhysician=current_patient.primary_care_physician or "Dr. Sarah Jenkins, MD",
        emergencyContact=current_patient.emergency_contact or {},
        insurance=current_patient.insurance or {},
        knownAllergies=current_patient.known_allergies or []
    )


@router.put("/me", response_model=PatientResponse)
def update_patient_profile(
    patient_update: PatientUpdate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    if patient_update.dateOfBirth is not None:
        current_patient.date_of_birth = patient_update.dateOfBirth
    if patient_update.gender is not None:
        current_patient.gender = patient_update.gender
    if patient_update.bloodGroup is not None:
        current_patient.blood_group = patient_update.bloodGroup
    if patient_update.heightCm is not None:
        current_patient.height_cm = patient_update.heightCm
    if patient_update.weightKg is not None:
        current_patient.weight_kg = patient_update.weightKg
    if patient_update.primaryCarePhysician is not None:
        current_patient.primary_care_physician = patient_update.primaryCarePhysician
    if patient_update.emergencyContact is not None:
        current_patient.emergency_contact = patient_update.emergencyContact
    if patient_update.insurance is not None:
        current_patient.insurance = patient_update.insurance
    if patient_update.knownAllergies is not None:
        current_patient.known_allergies = patient_update.knownAllergies

    db.commit()
    db.refresh(current_patient)

    return PatientResponse(
        id=current_patient.id,
        userId=current_patient.user_id,
        dateOfBirth=current_patient.date_of_birth or "1988-04-12",
        gender=current_patient.gender or "male",
        bloodGroup=current_patient.blood_group or "O+",
        heightCm=current_patient.height_cm or 178.0,
        weightKg=current_patient.weight_kg or 82.0,
        primaryCarePhysician=current_patient.primary_care_physician or "Dr. Sarah Jenkins, MD",
        emergencyContact=current_patient.emergency_contact or {},
        insurance=current_patient.insurance or {},
        knownAllergies=current_patient.known_allergies or []
    )
