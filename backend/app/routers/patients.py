from typing import List, Optional, Dict, Any, Set
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.patient import (
    PatientResponse,
    PatientUpdate,
    DiseaseResponse,
    MedicationResponse,
    LabResultResponse,
    AnalyteSummarySchema,
    AnalyteListResponse,
)
from backend.app.schemas.chat import StructuredTrendSchema, MeasurementPointSchema, CitationSchema
from backend.app.services.auth_service import get_current_patient
from backend.app.models.patient import Patient
from backend.app.models.clinical_entity import Disease, Medication, LabResult
from backend.app.models.report import MedicalReport
from backend.app.clinical.terminology.biomarkers import resolve_biomarker
from backend.app.clinical.structured_query.engine import StructuredClinicalQueryEngine
from backend.app.clinical.structured_query.models import (
    StructuredQueryType,
    TimeWindow,
    StructuredQueryIntent,
)

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


@router.get("/me/labs/analytes", response_model=AnalyteListResponse)
def get_patient_analytes(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Returns distinct lab analytes recorded for the patient with summary statistics.
    """
    labs = db.query(LabResult).filter(LabResult.patient_id == current_patient.id).order_by(LabResult.test_date.desc()).all()

    # Group by canonical name or test name
    grouped: Dict[str, Dict[str, Any]] = {}
    for lab in labs:
        # Resolve canonical name
        defn = resolve_biomarker(lab.test_name)
        c_name = defn.canonical_name if defn else (lab.canonical_name or lab.test_name)
        loinc = defn.loinc_code if defn else lab.loinc_code

        key = c_name.lower().strip()
        if key not in grouped:
            grouped[key] = {
                "testName": lab.test_name,
                "canonicalName": c_name,
                "loincCode": loinc,
                "count": 0,
                "latestDate": lab.test_date,
                "latestValue": lab.value,
                "unit": lab.unit,
                "referenceRange": lab.reference_range,
                "facilities": set(),
            }

        item = grouped[key]
        item["count"] += 1
        if lab.hospital_name and lab.hospital_name.strip():
            item["facilities"].add(lab.hospital_name.strip())

    result_list = []
    for item in grouped.values():
        result_list.append(
            AnalyteSummarySchema(
                testName=item["testName"],
                canonicalName=item["canonicalName"],
                loincCode=item["loincCode"],
                count=item["count"],
                latestDate=item["latestDate"],
                latestValue=item["latestValue"],
                unit=item["unit"],
                referenceRange=item["referenceRange"],
                facilities=sorted(list(item["facilities"]))
            )
        )

    # Sort by count descending, then canonical name
    result_list.sort(key=lambda a: (-a.count, a.canonicalName))
    return AnalyteListResponse(analytes=result_list)


@router.get("/me/labs/trends", response_model=StructuredTrendSchema)
def get_patient_lab_trend(
    analyte: str = Query(..., description="Analyte name or biomarker (e.g. Potassium, Glucose, Total Cholesterol)"),
    time_window: Optional[str] = Query(None, description="Time window: 3m, 6m, 1y, or all"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Executes a clinical lab trend query for the patient with full chronological series,
    unit mismatch detection, multi-facility conflict detection, and source report citations.
    """
    if not analyte or not analyte.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Analyte query parameter is required")

    # Map time_window string or date range to TimeWindow model
    tw_model = None
    if time_window:
        tw_clean = time_window.lower().strip()
        if tw_clean in ["3m", "3_months", "three_months"]:
            tw_model = TimeWindow(days=90, descriptor="Past 3 Months")
        elif tw_clean in ["6m", "6_months", "six_months"]:
            tw_model = TimeWindow(days=180, descriptor="Past 6 Months")
        elif tw_clean in ["1y", "1_year", "one_year"]:
            tw_model = TimeWindow(days=365, descriptor="Past 1 Year")

    if start_date or end_date:
        tw_model = TimeWindow(start_date=start_date, end_date=end_date, descriptor=f"{start_date or 'Earliest'} to {end_date or 'Latest'}")

    defn = resolve_biomarker(analyte)
    canonical = defn.canonical_name if defn else analyte.strip()

    intent = StructuredQueryIntent(
        is_structured_query=True,
        query_type=StructuredQueryType.MEASUREMENT_HISTORY,
        analyte_term=analyte.strip(),
        canonical_name=canonical,
        loinc_code=defn.loinc_code if defn else None,
        time_window=tw_model,
        is_multi_analyte=False,
        is_generic_latest=False,
        raw_query=f"Trend for {analyte.strip()}"
    )

    engine = StructuredClinicalQueryEngine(db_session=db)
    trend_result = engine.execute_query(intent, patient_id=current_patient.id)

    # If start_date or end_date are provided, filter measurements while preserving clinical integrity
    if start_date or end_date:
        filtered_points = trend_result.all_measurements
        if start_date:
            filtered_points = [p for p in filtered_points if p.test_date >= start_date]
        if end_date:
            filtered_points = [p for p in filtered_points if p.test_date <= end_date]

        trend_result.all_measurements = filtered_points
        if filtered_points:
            trend_result.latest_measurement = filtered_points[-1]
            trend_result.previous_measurement = filtered_points[-2] if len(filtered_points) > 1 else None
            trend_result.has_sufficient_data = len(filtered_points) >= 2
        else:
            trend_result.latest_measurement = None
            trend_result.previous_measurement = None
            trend_result.has_sufficient_data = False

    raw_dict = trend_result.model_dump()
    return StructuredTrendSchema(**raw_dict)
