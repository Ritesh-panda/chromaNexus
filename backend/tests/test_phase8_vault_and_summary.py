import pytest
import uuid
from datetime import datetime, timezone, timedelta
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import Disease, Medication, LabResult, ExtractedEntity
from backend.app.models.allergy import Allergy
from backend.app.models.timeline import TimelineEvent
from backend.app.services.summary_service import generate_doctor_summary_for_patient, calculate_age_from_dob


# --- Vault Tests ---

def test_vault_search_and_filtering(client, db_session):
    """
    Verifies that GET /api/v1/reports supports filtering by category, hospital, status, and search.
    """
    # 1. Filter by category
    res_cat = client.get("/api/v1/reports?category=blood_report")
    assert res_cat.status_code == 200
    reports = res_cat.json()
    assert len(reports) > 0
    for r in reports:
        assert r["category"] == "blood_report"

    # 2. Filter by hospital
    res_hosp = client.get("/api/v1/reports?hospital=St.+Jude")
    assert res_hosp.status_code == 200
    for r in res_hosp.json():
        assert "st. jude" in r["hospitalName"].lower()

    # 3. Filter by status
    res_status = client.get("/api/v1/reports?status=completed")
    assert res_status.status_code == 200
    for r in res_status.json():
        assert r["status"] == "completed"

    # 4. Search query
    res_search = client.get("/api/v1/reports?search=glucose")
    assert res_search.status_code == 200
    for r in res_search.json():
        match = (
            "glucose" in r["title"].lower() or
            "glucose" in (r.get("summary") or "").lower() or
            "glucose" in r["hospitalName"].lower()
        )
        assert match


def test_vault_sorting_clinical_vs_upload_date(client, db_session):
    """
    Verifies sorting by clinical date vs upload date, distinguishing the two.
    """
    # Sort by clinical date descending
    res_clin_desc = client.get("/api/v1/reports?sort_by=clinical_date&sort_order=desc")
    assert res_clin_desc.status_code == 200
    dates_desc = [r["reportDate"] for r in res_clin_desc.json()]
    for i in range(len(dates_desc) - 1):
        assert dates_desc[i] >= dates_desc[i + 1]

    # Sort by clinical date ascending
    res_clin_asc = client.get("/api/v1/reports?sort_by=clinical_date&sort_order=asc")
    assert res_clin_asc.status_code == 200
    dates_asc = [r["reportDate"] for r in res_clin_asc.json()]
    for i in range(len(dates_asc) - 1):
        assert dates_asc[i] <= dates_asc[i + 1]

    # Sort by upload date descending
    res_up_desc = client.get("/api/v1/reports?sort_by=upload_date&sort_order=desc")
    assert res_up_desc.status_code == 200
    up_dates = [r["uploadDate"] for r in res_up_desc.json() if r.get("uploadDate")]
    for i in range(len(up_dates) - 1):
        assert up_dates[i] >= up_dates[i + 1]


def test_vault_document_metadata_and_linked_records(client, db_session):
    """
    Verifies that reports contain complete metadata (checksum, pageCount, uploadDate vs reportDate)
    and that GET /reports/{id} returns linked graph records with source page numbers.
    """
    res = client.get("/api/v1/reports")
    assert res.status_code == 200
    reports = res.json()
    assert len(reports) > 0
    first_report = reports[0]

    # Metadata checks
    assert "id" in first_report
    assert "checksum" in first_report
    assert "pageCount" in first_report
    assert "uploadDate" in first_report
    assert "reportDate" in first_report
    assert first_report["reportDate"] is not None

    # Inspect single report with linked entities
    res_single = client.get(f"/api/v1/reports/{first_report['id']}")
    assert res_single.status_code == 200
    detail = res_single.json()
    assert detail["id"] == first_report["id"]
    assert "linkedEntities" in detail
    assert isinstance(detail["linkedEntities"], dict)
    assert "labResults" in detail["linkedEntities"]
    assert "medications" in detail["linkedEntities"]
    assert "diseases" in detail["linkedEntities"]


def test_vault_empty_and_failed_document_handling(client, db_session):
    """
    Verifies graceful handling of empty query results and failed document extraction status.
    """
    # 1. No matching query returns empty list
    res_empty = client.get("/api/v1/reports?search=nonexistent_query_xyz_999")
    assert res_empty.status_code == 200
    assert res_empty.json() == []

    # 2. Document with failed status
    patient = db_session.query(Patient).first()
    failed_doc = MedicalReport(
        patient_id=patient.id,
        title="Corrupted Lab Scan",
        file_name="corrupted.pdf",
        file_size=1024,
        category="blood_report",
        hospital_name="City Clinic",
        report_date="2024-05-01",
        status="failed",
        summary="Document extraction failed due to corrupted PDF stream."
    )
    db_session.add(failed_doc)
    db_session.commit()

    res_failed = client.get("/api/v1/reports?status=failed")
    assert res_failed.status_code == 200
    failed_list = res_failed.json()
    assert any(r["id"] == failed_doc.id for r in failed_list)
    assert any(r["status"] == "failed" for r in failed_list)


def test_vault_distinct_facilities_endpoint(client, db_session):
    """
    Verifies that GET /api/v1/reports/facilities returns distinct hospital names.
    """
    res = client.get("/api/v1/reports/facilities")
    assert res.status_code == 200
    facilities = res.json()
    assert isinstance(facilities, list)
    assert len(facilities) > 0
    assert "St. Jude Hospital" in facilities or "City Health Clinic" in facilities or any("hospital" in f.lower() for f in facilities)


def test_vault_patient_isolation(client, db_session):
    """
    Verifies that Patient A cannot view or search Patient B's vault reports.
    """
    # Create Patient B
    user_b = User(id="user-isolation-vault", email="vault_b@test.com", hashed_password="pw", name="Bob Isolated")
    db_session.add(user_b)
    patient_b = Patient(id="patient-isolation-vault", user_id=user_b.id)
    db_session.add(patient_b)

    report_b = MedicalReport(
        id="report-secret-b",
        patient_id=patient_b.id,
        title="Patient B Confidential Oncology Report",
        file_name="oncology_b.pdf",
        category="oncology",
        hospital_name="Secret Hospital",
        report_date="2024-06-01"
    )
    db_session.add(report_b)
    db_session.commit()

    # Client is authenticated as Patient A (default demo patient)
    res_list = client.get("/api/v1/reports")
    assert res_list.status_code == 200
    report_ids = [r["id"] for r in res_list.json()]
    assert "report-secret-b" not in report_ids

    res_direct = client.get(f"/api/v1/reports/{report_b.id}")
    assert res_direct.status_code == 404


# --- Doctor-Ready Clinical Summary Tests ---

def test_calculate_age_from_dob():
    """
    Verifies age calculation from DOB.
    """
    assert calculate_age_from_dob(None) is None
    assert calculate_age_from_dob("") is None
    assert calculate_age_from_dob("invalid-date") is None
    # 2000-01-01 should be >= 24
    age = calculate_age_from_dob("2000-01-01")
    assert age is not None
    assert age >= 24


def test_doctor_summary_patient_overview_and_demographics(client, db_session):
    """
    Verifies patient overview, DOB-derived age, gender, blood group, and clinician disclaimer.
    """
    patient = db_session.query(Patient).first()
    patient.date_of_birth = "1988-04-12"
    patient.blood_group = "O+"
    db_session.commit()

    res = client.get("/api/v1/summaries/latest")
    assert res.status_code == 200
    data = res.json()

    assert data["patientName"] is not None
    assert data["age"] is not None
    assert data["age"] >= 35
    assert data["bloodGroup"] == "O+"
    assert "clinicianNotice" in data
    assert "NOTICE TO CLINICIANS" in data["clinicianNotice"]


def test_doctor_summary_conditions_and_provenance(client, db_session):
    """
    Verifies active vs past diagnoses separation, with ICD codes and source report provenance.
    """
    patient = db_session.query(Patient).first()
    
    # Add an active and a resolved condition with source report
    rep = db_session.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).first()
    
    active_cond = Disease(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        name="Chronic Glaucoma Phase 8",
        icd_code="H40.1",
        status="active",
        diagnosed_date="2022-03-15",
        source_report_id=rep.id,
        source_page_number=1
    )
    resolved_cond = Disease(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        name="Acute Bronchitis Phase 8",
        icd_code="J20.9",
        status="resolved",
        diagnosed_date="2021-11-10",
        source_report_id=rep.id,
        source_page_number=2
    )
    db_session.add(active_cond)
    db_session.add(resolved_cond)
    db_session.commit()

    res = client.get("/api/v1/summaries/latest")
    assert res.status_code == 200
    data = res.json()

    current = [d["name"] for d in data["currentDiseases"]]
    past = [d["name"] for d in data["pastDiseases"]]

    assert "Chronic Glaucoma Phase 8" in current
    assert "Acute Bronchitis Phase 8" in past

    # Check provenance
    target = next(d for d in data["currentDiseases"] if d["id"] == active_cond.id)
    assert target["sourceReportId"] == rep.id
    assert target["sourcePageNumber"] == 1
    assert target["sourceReportTitle"] is not None


def test_doctor_summary_allergies_from_model(client, db_session):
    """
    Verifies inclusion of Allergy records with severity, reaction, and source provenance,
    and checks missing data disclosures if absent.
    """
    patient = db_session.query(Patient).first()
    
    allergy = Allergy(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        allergen="Penicillin G",
        category="medication",
        severity="severe",
        reaction="Anaphylaxis, Urticaria",
        status="active",
        source_page_number=1
    )
    db_session.add(allergy)
    db_session.commit()

    res = client.get("/api/v1/summaries/latest")
    assert res.status_code == 200
    data = res.json()

    allergies = data["knownAllergies"]
    assert len(allergies) > 0
    penicillin = next((a for a in allergies if isinstance(a, dict) and "Penicillin" in a.get("allergen", "")), None)
    assert penicillin is not None
    assert penicillin["severity"] == "severe"
    assert "Anaphylaxis" in penicillin["reaction"]


def test_doctor_summary_current_vs_historical_medications(client, db_session):
    """
    Verifies that active prescriptions and historical/discontinued medications are distinctly partitioned.
    Historical medications MUST NOT be presented as active.
    """
    patient = db_session.query(Patient).first()

    active_med = Medication(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        name="Metformin HCl",
        dosage="500 mg",
        frequency="Twice daily",
        status="active",
        start_date="2022-04-01"
    )
    hist_med = Medication(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        name="Amoxicillin",
        dosage="250 mg",
        frequency="Every 8 hours",
        status="discontinued",
        start_date="2021-11-10",
        end_date="2021-11-20"
    )
    db_session.add(active_med)
    db_session.add(hist_med)
    db_session.commit()

    res = client.get("/api/v1/summaries/latest")
    assert res.status_code == 200
    data = res.json()

    active_names = [m["name"] for m in data["activeMedications"]]
    hist_names = [m["name"] for m in data.get("historicalMedications", [])]

    assert "Metformin HCl" in active_names
    assert "Amoxicillin" not in active_names
    assert "Amoxicillin" in hist_names


def test_doctor_summary_lab_results_and_abnormals(client, db_session):
    """
    Verifies abnormal lab values are flagged with reference ranges and source hospital.
    """
    patient = db_session.query(Patient).first()

    lab_high = LabResult(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        test_name="HbA1c",
        value="8.4",
        unit="%",
        reference_range="4.0 - 5.6",
        status="high",
        test_date="2024-03-15",
        hospital_name="St. Jude Hospital"
    )
    db_session.add(lab_high)
    db_session.commit()

    res = client.get("/api/v1/summaries/latest")
    assert res.status_code == 200
    data = res.json()

    abnormal_names = [l["testName"] for l in data["abnormalLabs"]]
    assert "HbA1c" in abnormal_names
    hba1c = next(l for l in data["abnormalLabs"] if l["testName"] == "HbA1c")
    assert hba1c["value"] == "8.4"
    assert hba1c["unit"] == "%"
    assert hba1c["referenceRange"] == "4.0 - 5.6"
    assert hba1c["status"] == "high"


def test_doctor_summary_conflicting_information_surfaced(client, db_session):
    """
    Verifies that multi-facility measurements on the same biomarker are surfaced as conflicting information.
    """
    patient = db_session.query(Patient).first()

    # Two tests for Glucose from different hospitals
    lab1 = LabResult(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        test_name="Fasting Glucose",
        canonical_name="fasting glucose",
        value="110",
        unit="mg/dL",
        reference_range="70 - 99",
        status="high",
        test_date="2024-03-10",
        hospital_name="Hospital Alpha"
    )
    lab2 = LabResult(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        test_name="Fasting Glucose",
        canonical_name="fasting glucose",
        value="125",
        unit="mg/dL",
        reference_range="70 - 99",
        status="high",
        test_date="2024-03-12",
        hospital_name="Hospital Beta"
    )
    db_session.add(lab1)
    db_session.add(lab2)
    db_session.commit()

    res = client.get("/api/v1/summaries/latest")
    assert res.status_code == 200
    data = res.json()

    conflicts = data.get("conflictingInformation", [])
    assert len(conflicts) > 0
    assert any("FASTING GLUCOSE" in c["topic"] for c in conflicts)


def test_doctor_summary_patient_isolation(client, db_session):
    """
    Verifies that a patient's summary does NOT include another patient's medical records.
    """
    # Create Patient B
    user_b = User(id="user-isolation-sum", email="sum_b@test.com", hashed_password="pw", name="Charlie Isolated")
    db_session.add(user_b)
    patient_b = Patient(id="patient-isolation-sum", user_id=user_b.id)
    db_session.add(patient_b)

    # Patient B's unique disease
    disease_b = Disease(
        id=str(uuid.uuid4()),
        patient_id=patient_b.id,
        name="Isolated Lupus Erythematosus",
        status="active",
        diagnosed_date="2023-01-01"
    )
    db_session.add(disease_b)
    db_session.commit()

    # Fetch summary for current patient (Patient A)
    res = client.get("/api/v1/summaries/latest")
    assert res.status_code == 200
    data = res.json()

    active_diseases = [d["name"] for d in data["currentDiseases"]]
    assert "Isolated Lupus Erythematosus" not in active_diseases


def test_doctor_summary_questions_update(client, db_session):
    """
    Verifies that PUT /api/v1/summaries/questions updates patient's questions for the doctor.
    """
    new_questions = [
        "Can I reduce the dosage of Metformin if my HbA1c is below 7.0?",
        "When should I schedule my next annual dilated eye exam?"
    ]
    res = client.put("/api/v1/summaries/questions", json={"questions": new_questions})
    assert res.status_code == 200
    data = res.json()
    assert data["doctorQuestions"] == new_questions
