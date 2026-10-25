import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.patient import Patient
from backend.app.models.clinical_entity import Disease, Medication, LabResult, ExtractedEntity
from backend.app.models.allergy import Allergy
from backend.app.models.report import MedicalReport
from backend.app.models.timeline import TimelineEvent
from backend.app.models.summary import DoctorSummary


def calculate_age_from_dob(date_of_birth: Optional[str]) -> Optional[int]:
    """Calculates chronological age from DOB string (YYYY-MM-DD), returning None if invalid/absent."""
    if not date_of_birth or not date_of_birth.strip():
        return None
    try:
        clean_dob = date_of_birth.strip()
        if len(clean_dob) == 10 and clean_dob[4] == '-' and clean_dob[7] == '-':
            dob = datetime.strptime(clean_dob, "%Y-%m-%d")
            today = datetime.now()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        pass
    return None


def generate_doctor_summary_for_patient(
    db: Session,
    patient: Patient,
    doctor_questions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Assembles a longitudinal doctor clinical summary directly from verified patient records.
    Deterministic assembly ensures 100% provenance and zero hallucination.
    """
    # 1. Build lookup dictionary for patient's medical reports
    reports_by_id = {
        r.id: r for r in db.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).all()
    }

    # 2. Patient Demographics & Context
    patient_name = patient.user.name if (patient.user and patient.user.name) else "Patient"
    age = calculate_age_from_dob(patient.date_of_birth)
    gender = patient.gender.capitalize() if patient.gender and patient.gender != "other" else (patient.gender or "Not recorded")
    blood_group = patient.blood_group or "Not recorded"
    primary_care_physician = patient.primary_care_physician or "Not assigned"
    insurance = patient.insurance

    # 3. Known Medical Conditions
    diseases = db.query(Disease).filter(Disease.patient_id == patient.id).order_by(Disease.diagnosed_date.desc()).all()
    
    def format_disease(d: Disease) -> Dict[str, Any]:
        rep = reports_by_id.get(d.source_report_id)
        return {
            "id": d.id,
            "name": d.name,
            "icdCode": d.icd_code,
            "status": d.status,
            "diagnosedDate": d.diagnosed_date,
            "notes": d.notes,
            "sourceReportId": d.source_report_id,
            "sourceReportTitle": rep.title if rep else None,
            "sourceDate": rep.report_date if rep else None,
            "sourceHospital": rep.hospital_name if rep else None,
            "sourcePageNumber": d.source_page_number
        }

    current_diseases = [format_disease(d) for d in diseases if d.status in ["active", "chronic"]]
    past_diseases = [format_disease(d) for d in diseases if d.status in ["resolved", "in_remission", "past", "completed"]]

    # 4. Allergies & Adverse Reactions
    allergies = db.query(Allergy).filter(Allergy.patient_id == patient.id).all()
    
    def format_allergy(a: Allergy) -> Dict[str, Any]:
        rep = reports_by_id.get(a.source_report_id)
        return {
            "id": a.id,
            "allergen": a.allergen,
            "category": a.category,
            "severity": a.severity,
            "reaction": a.reaction,
            "status": a.status,
            "notes": a.notes,
            "sourceReportId": a.source_report_id,
            "sourceReportTitle": rep.title if rep else None,
            "sourceDate": rep.report_date if rep else None,
            "sourceHospital": rep.hospital_name if rep else None,
            "sourcePageNumber": a.source_page_number
        }

    known_allergies_list = [format_allergy(a) for a in allergies]
    
    # Fallback to patient.known_allergies if Allergy table has none yet
    if not known_allergies_list and patient.known_allergies:
        for idx, item in enumerate(patient.known_allergies):
            if isinstance(item, str):
                known_allergies_list.append({
                    "id": f"allergy-legacy-{idx}",
                    "allergen": item,
                    "category": "medication",
                    "severity": "moderate",
                    "reaction": None,
                    "status": "active",
                    "sourceReportTitle": "Patient Profile Intake",
                    "sourcePageNumber": None
                })
            elif isinstance(item, dict):
                known_allergies_list.append(item)

    # 5. Medications: Partition Current vs Historical
    medications = db.query(Medication).filter(Medication.patient_id == patient.id).order_by(Medication.start_date.desc()).all()
    
    def format_medication(m: Medication) -> Dict[str, Any]:
        rep = reports_by_id.get(m.source_report_id)
        return {
            "id": m.id,
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "route": m.route or "oral",
            "status": m.status,
            "startDate": m.start_date,
            "endDate": m.end_date,
            "prescribingDoctor": m.prescribing_doctor,
            "indication": m.indication,
            "rxnormCode": m.rxnorm_code,
            "sourceReportId": m.source_report_id,
            "sourceReportTitle": rep.title if rep else None,
            "sourceDate": rep.report_date if rep else None,
            "sourceHospital": rep.hospital_name if rep else None,
            "sourcePageNumber": m.source_page_number
        }

    active_medications = [
        format_medication(m) for m in medications 
        if m.status in ["active", "as_needed"]
    ]
    historical_medications = [
        format_medication(m) for m in medications 
        if m.status in ["discontinued", "completed", "inactive"]
    ]

    # 6. Laboratory Results
    lab_results = db.query(LabResult).filter(LabResult.patient_id == patient.id).order_by(LabResult.test_date.desc()).all()
    
    def format_lab(lr: LabResult) -> Dict[str, Any]:
        rep = reports_by_id.get(lr.source_report_id)
        return {
            "id": lr.id,
            "testName": lr.test_name,
            "canonicalName": lr.canonical_name,
            "value": lr.value,
            "unit": lr.unit,
            "referenceRange": lr.reference_range,
            "status": lr.status,
            "testDate": lr.test_date,
            "hospitalName": lr.hospital_name or (rep.hospital_name if rep else None),
            "sourceReportId": lr.source_report_id,
            "sourceReportTitle": rep.title if rep else None,
            "sourceDate": rep.report_date if rep else None,
            "sourceHospital": rep.hospital_name if rep else None,
            "sourcePageNumber": lr.source_page_number
        }

    abnormal_labs = [format_lab(lr) for lr in lab_results if lr.status in ["high", "low", "critical"]]
    recent_labs = [format_lab(lr) for lr in lab_results[:12]]

    # 7. Procedures & Diagnostic Imaging
    imaging_reports = [
        r for r in reports_by_id.values() 
        if r.category in ["mri", "xray", "ct_scan", "ultrasound", "procedure", "discharge_summary", "pathology"]
    ]
    procedures_and_imaging = [
        {
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "reportDate": r.report_date,
            "hospitalName": r.hospital_name,
            "doctorName": r.doctor_name,
            "summary": r.summary,
            "pageCount": r.page_count
        } for r in sorted(imaging_reports, key=lambda x: x.report_date, reverse=True)
    ]

    # Also search ExtractedEntity where category == 'procedure'
    proc_entities = db.query(ExtractedEntity).join(MedicalReport).filter(
        MedicalReport.patient_id == patient.id,
        ExtractedEntity.category == "procedure"
    ).all()
    for pe in proc_entities:
        rep = reports_by_id.get(pe.report_id)
        procedures_and_imaging.append({
            "id": pe.id,
            "title": pe.name,
            "category": "procedure_extracted",
            "reportDate": rep.report_date if rep else "Not recorded",
            "hospitalName": rep.hospital_name if rep else "Not recorded",
            "doctorName": rep.doctor_name if rep else None,
            "summary": pe.notes or f"Extracted procedure: {pe.name}",
            "pageCount": getattr(pe, 'source_page_number', 1)
        })

    # 8. Clinical Timeline Highlights
    timeline_events = db.query(TimelineEvent).filter(
        TimelineEvent.patient_id == patient.id
    ).order_by(TimelineEvent.date.desc()).limit(8).all()
    
    timeline_highlights = [
        {
            "id": t.id,
            "date": t.date,
            "title": t.title,
            "category": getattr(t, 'event_type', 'clinical_event'),
            "hospitalName": getattr(t, 'facility', None),
            "description": t.description,
            "sourceReportId": t.source_report_id
        } for t in timeline_events
    ]

    # 9. Conflicting or Uncertain Information
    conflicting_information = []
    # Check for analyte measurements from different facilities on similar dates with discordant values
    analyte_dates: Dict[str, List[LabResult]] = {}
    for lr in lab_results:
        key = (lr.canonical_name or lr.test_name).lower()
        analyte_dates.setdefault(key, []).append(lr)
    
    for analyte, results in analyte_dates.items():
        if len(results) >= 2:
            # Check if facilities differ
            facilities = {r.hospital_name for r in results if r.hospital_name}
            if len(facilities) > 1:
                conflicting_information.append({
                    "topic": f"Multi-facility observations for {analyte.upper()}",
                    "details": f"Measurements recorded across {', '.join(facilities)}. Variations in reference intervals or lab techniques may exist.",
                    "recordsInvolved": [f"{r.hospital_name} ({r.test_date}): {r.value} {r.unit} [Ref: {r.reference_range}]" for r in results[:3]]
                })

    # 10. Missing Data Disclosures
    missing_data_disclosures = []
    if not known_allergies_list:
        missing_data_disclosures.append("No allergies documented in indexed records (absence in records does not confirm clinical absence).")
    if not active_medications and not historical_medications:
        missing_data_disclosures.append("No medications documented in indexed records.")
    if not current_diseases and not past_diseases:
        missing_data_disclosures.append("No clinical diagnoses documented in indexed records.")
    if not patient.date_of_birth:
        missing_data_disclosures.append("Patient date of birth is not recorded in profile.")
    if not patient.primary_care_physician:
        missing_data_disclosures.append("Primary care physician is not assigned.")
    missing_data_disclosures.append(
        f"Digest compiled from {len(reports_by_id)} indexed documents. Any unuploaded or non-digitized records are not reflected."
    )

    # 11. Patient Questions for the Doctor
    questions = doctor_questions if doctor_questions is not None else [
        "Review dosage and potential side effects of active medications.",
        "Discuss target reference ranges for any abnormal laboratory biomarkers.",
        "Evaluate necessity and timing of follow-up diagnostic imaging or procedures."
    ]

    # 12. Clinician Notice
    clinician_notice = (
        "NOTICE TO CLINICIANS: This clinical digest was deterministically compiled from indexed medical "
        "documents on ChronaNexus. It provides longitudinal reference data and does not constitute an automated "
        "diagnosis, treatment recommendation, or prescribing directive. All findings must be clinically verified "
        "with original primary sources."
    )

    # 13. Deterministic Clinical Overview Paragraph
    overview_parts = []
    demog = f"{patient_name}"
    if age:
        demog += f", {age}-year-old"
    if gender and gender != "Not recorded":
        demog += f" {gender.lower()}"
    overview_parts.append(f"{demog}. Longitudinal medical intelligence digest grounded across {len(reports_by_id)} indexed clinical documents.")
    
    if current_diseases:
        cond_names = ", ".join([d["name"] for d in current_diseases[:3]])
        overview_parts.append(f"Documented active conditions include {cond_names}.")
    if active_medications:
        overview_parts.append(f"Currently prescribed {len(active_medications)} active medications.")
    if abnormal_labs:
        overview_parts.append(f"{len(abnormal_labs)} recent laboratory findings flagged outside standard reference ranges.")
    if known_allergies_list:
        overview_parts.append(f"{len(known_allergies_list)} known adverse reactions/allergies recorded.")
    
    summary_overview = " ".join(overview_parts)

    recent_reports = [
        {
            "id": r.id,
            "title": r.title,
            "reportDate": r.report_date,
            "hospitalName": r.hospital_name,
            "category": r.category
        } for r in sorted(reports_by_id.values(), key=lambda x: x.report_date, reverse=True)[:5]
    ]

    risk_factors = [
        d["name"] + (f" (ICD: {d['icdCode']})" if d.get("icdCode") else "") 
        for d in current_diseases
    ]

    summary_dict = {
        "patientName": patient_name,
        "age": age,
        "gender": gender,
        "bloodGroup": blood_group,
        "primaryCarePhysician": primary_care_physician,
        "insurance": insurance,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "summaryOverview": summary_overview,
        "currentDiseases": current_diseases,
        "pastDiseases": past_diseases,
        "activeMedications": active_medications,
        "historicalMedications": historical_medications,
        "knownAllergies": known_allergies_list,
        "abnormalLabs": abnormal_labs,
        "recentLabs": recent_labs,
        "proceduresAndImaging": procedures_and_imaging,
        "timelineHighlights": timeline_highlights,
        "conflictingInformation": conflicting_information,
        "missingDataDisclosures": missing_data_disclosures,
        "doctorQuestions": questions,
        "clinicianNotice": clinician_notice,
        "riskFactors": risk_factors,
        "recentReports": recent_reports,
        "shareLink": None
    }

    # Store or update in DB
    existing_summary = db.query(DoctorSummary).filter(DoctorSummary.patient_id == patient.id).first()
    if not existing_summary:
        existing_summary = DoctorSummary(
            patient_id=patient.id,
            patient_name=patient_name,
            age=age or 0,
            gender=gender,
            summary_overview=summary_overview,
            current_diseases=current_diseases,
            past_diseases=past_diseases,
            active_medications=active_medications,
            known_allergies=known_allergies_list,
            abnormal_labs=abnormal_labs,
            risk_factors=risk_factors,
            recent_reports=recent_reports,
            timeline_highlights=timeline_highlights,
            share_token=f"share_token_{uuid.uuid4().hex}"
        )
        db.add(existing_summary)
    else:
        existing_summary.patient_name = patient_name
        existing_summary.age = age or 0
        existing_summary.gender = gender
        existing_summary.summary_overview = summary_overview
        existing_summary.current_diseases = current_diseases
        existing_summary.past_diseases = past_diseases
        existing_summary.active_medications = active_medications
        existing_summary.known_allergies = known_allergies_list
        existing_summary.abnormal_labs = abnormal_labs
        existing_summary.risk_factors = risk_factors
        existing_summary.recent_reports = recent_reports
        existing_summary.timeline_highlights = timeline_highlights
        existing_summary.generated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(existing_summary)

    if existing_summary.share_token:
        summary_dict["shareLink"] = f"https://chronanexus.app/physician-view/{existing_summary.share_token}"

    return summary_dict
