from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.patient import (
    PatientResponse,
    PatientUpdate,
    DiseaseResponse,
    MedicationResponse,
    LabResultResponse,
)
from backend.app.services.auth_service import get_current_patient
from backend.app.models.patient import Patient
from backend.app.models.clinical_entity import Disease, Medication, LabResult

router = APIRouter(prefix="/patients", tags=["Patients"])


def format_disease_response(d: Disease) -> DiseaseResponse:
    return DiseaseResponse(
        id=d.id,
        name=d.name,
        icdCode=d.icd_code,
        status=d.status or "active",
        diagnosedDate=d.diagnosed_date,
        resolvedDate=d.resolved_date,
        treatingDoctor=d.treating_doctor,
        sourceReportId=d.source_report_id,
        notes=d.notes
    )


def format_medication_response(m: Medication) -> MedicationResponse:
    return MedicationResponse(
        id=m.id,
        name=m.name,
        dosage=m.dosage,
        frequency=m.frequency,
        route=m.route or "oral",
        startDate=m.start_date,
        endDate=m.end_date,
        status=m.status or "active",
        prescribingDoctor=m.prescribing_doctor,
        indication=m.indication,
        sourceReportId=m.source_report_id
    )


def format_lab_result_response(l: LabResult) -> LabResultResponse:
    return LabResultResponse(
        id=l.id,
        testName=l.test_name,
        category=l.category or "metabolic",
        value=l.value,
        unit=l.unit,
        referenceRange=l.reference_range,
        status=l.status or "normal",
        testDate=l.test_date,
        sourceReportId=l.source_report_id,
        hospitalName=l.hospital_name
    )


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


@router.get("/me/diagnoses", response_model=List[DiseaseResponse])
def get_patient_diagnoses(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    diseases = db.query(Disease).filter(Disease.patient_id == current_patient.id).order_by(Disease.diagnosed_date.desc()).all()
    return [format_disease_response(d) for d in diseases]


@router.get("/me/medications", response_model=List[MedicationResponse])
def get_patient_medications(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    meds = db.query(Medication).filter(Medication.patient_id == current_patient.id).order_by(Medication.start_date.desc()).all()
    return [format_medication_response(m) for m in meds]


@router.get("/me/labs", response_model=List[LabResultResponse])
def get_patient_labs(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    labs = db.query(LabResult).filter(LabResult.patient_id == current_patient.id).order_by(LabResult.test_date.desc()).all()
    return [format_lab_result_response(l) for l in labs]
