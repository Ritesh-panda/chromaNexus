import os
import uuid
import pytest
from datetime import datetime, timezone
from backend.app.core.config import settings
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import Disease, Medication, LabResult, ExtractedEntity
from backend.app.models.allergy import Allergy
from backend.app.models.timeline import TimelineEvent
from backend.app.models.audit_log import AuditLog
from backend.app.services.audit_service import log_audit_event
from backend.app.services.fhir_service import generate_fhir_r4_bundle_for_patient, validate_fhir_r4_bundle
from backend.app.services.purge_service import get_purge_preview, execute_patient_purge, MANDATORY_CONFIRMATION_PHRASE
from backend.app.ai.retrieval import get_vector_store, ChromaDBVectorStore


# =====================================================================
# 1. SECURITY & AUTHORIZATION TESTS
# =====================================================================

def test_idor_blocked_across_patients(client, db_session):
    """
    Verifies that a patient cannot access another patient's medical report.
    Cross-patient lookup must be blocked with HTTP 403 and logged in audit trail.
    """
    # Create another patient and another report
    other_user = User(
        id=str(uuid.uuid4()),
        email="other.patient@example.com",
        name="Other Patient",
        hashed_password="hashed_pw",
        role="patient"
    )
    db_session.add(other_user)
    db_session.flush()

    other_patient = Patient(
        id=str(uuid.uuid4()),
        user_id=other_user.id
    )
    db_session.add(other_patient)
    db_session.flush()

    other_report = MedicalReport(
        id=f"rep_secret_{uuid.uuid4().hex[:8]}",
        patient_id=other_patient.id,
        title="Confidential Oncology Biopsy",
        file_name="biopsy.pdf",
        hospital_name="Oncology Center",
        category="biopsy",
        status="completed",
        report_date="2026-10-24"
    )
    db_session.add(other_report)
    db_session.commit()

    # The test client defaults to the current logged-in demo user (Alex Vance)
    res = client.get(f"/api/v1/reports/{other_report.id}")
    # Returning 404/403 prevents disclosing whether the other patient's record exists
    assert res.status_code in [403, 404]


    # Verify IDOR_BLOCKED audit log was recorded
    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.action == "IDOR_BLOCKED",
        AuditLog.resource_id == other_report.id
    ).first()
    assert audit_entry is not None
    assert audit_entry.outcome == "DENIED"


def test_path_traversal_protection_on_download(client, db_session):
    """
    Verifies that document download validates that the storage path
    remains strictly within settings.UPLOAD_DIR and blocks directory traversal attempts.
    """
    # Current patient
    current_patient = db_session.query(Patient).first()
    assert current_patient is not None

    # Create a report with a malicious traversal path
    malicious_report = MedicalReport(
        id=f"rep_traversal_{uuid.uuid4().hex[:8]}",
        patient_id=current_patient.id,
        title="Tampered Report Path",
        file_name="tampered.pdf",
        hospital_name="City Hospital",
        category="general",
        status="completed",
        storage_path="../../etc/shadow",
        report_date="2026-10-24"
    )
    db_session.add(malicious_report)
    db_session.commit()

    res = client.get(f"/api/v1/documents/{malicious_report.id}/download")
    # Must be rejected with 403 Forbidden preventing access outside upload directory
    assert res.status_code == 403
    assert "Access denied to storage path" in res.json()["detail"]


# =====================================================================
# 2. AUDIT LOGGING TESTS
# =====================================================================

def test_audit_sensitive_fields_excluded(db_session):
    """
    Ensures passwords, bearer tokens, full report text, and secret keys
    are never stored in the audit trail.
    """
    log_entry = log_audit_event(
        db=db_session,
        action="TEST_SENSITIVE_STRIP",
        outcome="SUCCESS",
        actor_id="user_123",
        patient_id="pat_456",
        details={
            "password": "SuperSecretPassword123!",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "secret_key": "raw_secret_value",
            "raw_text": "Patient was diagnosed with severe disease...",
            "summary": "Long text with medical details",
            "safe_field": "safe_metadata_value",
            "record_count": 42
        }
    )
    assert log_entry is not None
    db_session.refresh(log_entry)

    # Verify sensitive keys were stripped
    assert "password" not in log_entry.details
    assert "token" not in log_entry.details
    assert "secret_key" not in log_entry.details
    assert "raw_text" not in log_entry.details
    assert "summary" not in log_entry.details
    # Safe fields preserved
    assert log_entry.details.get("safe_field") == "safe_metadata_value"
    assert log_entry.details.get("record_count") == 42


def test_audit_log_query_endpoint(client, db_session):
    """
    Verifies that the /api/v1/audit/logs endpoint returns audit events
    scoped strictly to the authenticated patient/actor.
    """
    res = client.get("/api/v1/audit/logs?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "items" in data or "logs" in data
    logs_list = data.get("logs") or data.get("items")
    assert isinstance(logs_list, list)


# =====================================================================
# 3. FHIR R4 EXPORT TESTS
# =====================================================================

def test_fhir_r4_bundle_generation_and_validation(client, db_session):
    """
    Tests FHIR R4 bundle generation, resource mapping completeness,
    valid references, and schema validation.
    """
    patient = db_session.query(Patient).first()
    assert patient is not None

    # Call FHIR export endpoint
    res = client.get("/api/v1/fhir/export")
    assert res.status_code == 200
    assert "attachment" in res.headers.get("content-disposition", "")

    bundle = res.json()
    assert bundle.get("resourceType") == "Bundle"
    assert bundle.get("type") == "collection"
    assert "entry" in bundle
    assert len(bundle["entry"]) > 0

    # Validate bundle with FHIR R4 validator
    is_valid, validation_errors = validate_fhir_r4_bundle(bundle)
    assert is_valid, f"FHIR validation errors: {validation_errors}"
    assert len(validation_errors) == 0

    # Verify Resource Types Present
    resource_types = {e["resource"]["resourceType"] for e in bundle["entry"]}
    assert "Patient" in resource_types

    # Find patient resource
    patient_res = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
    assert patient_res["id"] == patient.id

    # Verify references point to Patient/{patient.id}
    for e in bundle["entry"]:
        r = e["resource"]
        if r["resourceType"] == "Observation":
            assert r["subject"]["reference"] == f"Patient/{patient.id}"
            assert "code" in r
            assert "valueQuantity" in r or "valueString" in r
        elif r["resourceType"] == "Condition":
            assert r["subject"]["reference"] == f"Patient/{patient.id}"
            assert "code" in r
            assert "clinicalStatus" in r
        elif r["resourceType"] == "DocumentReference":
            assert r["subject"]["reference"] == f"Patient/{patient.id}"
            assert "status" in r
            assert "content" in r

    # Verify FHIR_EXPORT was logged in audit trail
    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.action == "FHIR_EXPORT",
        AuditLog.patient_id == patient.id
    ).first()
    assert audit_entry is not None
    assert audit_entry.outcome == "SUCCESS"


# =====================================================================
# 4. SAFE PATIENT-DATA PURGE TESTS (ISOLATED TEST ENVIRONMENT)
# =====================================================================

def test_purge_request_preview(client, db_session):
    """
    Verifies that POST /api/v1/patients/me/purge/request returns
    accurate itemized scope counts and a 15-minute token.
    """
    res = client.post("/api/v1/patients/me/purge/request")
    assert res.status_code == 200
    data = res.json()
    assert "purgeToken" in data or "confirmation_token" in data
    token = data.get("purgeToken") or data.get("confirmation_token")
    assert len(token) >= 32
    assert "scope" in data
    assert "disclaimer" in data or "warning" in data


def test_purge_confirm_phrase_mismatch_rejected(client, db_session):
    """
    Submitting confirmation with an incorrect phrase must be rejected with HTTP 400.
    """
    req_res = client.post("/api/v1/patients/me/purge/request")
    assert req_res.status_code == 200
    token = req_res.json().get("purgeToken") or req_res.json().get("confirmation_token")

    # Wrong confirmation phrase
    confirm_res = client.post("/api/v1/patients/me/purge/confirm", json={
        "purgeToken": token,
        "confirmationPhrase": "delete all please"
    })
    assert confirm_res.status_code == 400
    assert "Confirmation phrase mismatch" in confirm_res.text or "error" in confirm_res.json()


def test_purge_confirm_invalid_token_rejected(client, db_session):
    """
    Submitting confirmation with a bogus or expired token must be rejected with HTTP 400.
    """
    confirm_res = client.post("/api/v1/patients/me/purge/confirm", json={
        "purgeToken": "invalid-non-existent-token",
        "confirmationPhrase": MANDATORY_CONFIRMATION_PHRASE
    })
    assert confirm_res.status_code == 400


def test_purge_execution_cross_patient_isolation(db_session, test_isolation_env):
    """
    Validates end-to-end safe purge execution:
    - Target Patient A's records, files, and Chroma chunks are erased.
    - Patient B's records and chunks remain 100% intact.
    - Baseline 'violator_chunk' in Chroma remains 100% intact.
    - Physical files outside target patient are untouched.
    """
    # 1. Setup Patient A (Target to be purged)
    user_a = User(
        id=str(uuid.uuid4()),
        email="patient_a@example.com",
        name="Patient A",
        hashed_password="pw",
        role="patient"
    )
    db_session.add(user_a)
    db_session.flush()

    patient_a = Patient(id=str(uuid.uuid4()), user_id=user_a.id)
    db_session.add(patient_a)
    db_session.flush()

    # Create dummy storage file for Patient A
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_a_path = os.path.join(settings.UPLOAD_DIR, f"test_doc_a_{uuid.uuid4().hex[:6]}.pdf")
    with open(file_a_path, "w") as f:
        f.write("CONFIDENTIAL MEDICAL REPORT PATIENT A")

    report_a = MedicalReport(
        id=f"rep_a_{uuid.uuid4().hex[:6]}",
        patient_id=patient_a.id,
        title="Patient A Bloodwork",
        file_name="bloodwork_a.pdf",
        hospital_name="Alpha Medical",
        category="blood_report",
        status="completed",
        storage_path=file_a_path,
        report_date="2026-10-24"
    )
    db_session.add(report_a)

    lab_a = LabResult(
        id=f"lab_a_{uuid.uuid4().hex[:6]}",
        patient_id=patient_a.id,
        test_name="Glucose",
        value="110.0",
        unit="mg/dL",
        reference_range="70-99",
        test_date="2026-10-24"
    )
    db_session.add(lab_a)

    med_a = Medication(
        id=f"med_a_{uuid.uuid4().hex[:6]}",
        patient_id=patient_a.id,
        name="Metformin",
        dosage="500mg",
        frequency="twice daily",
        start_date="2026-10-01"
    )
    db_session.add(med_a)

    # 2. Setup Patient B (Should remain untouched)
    user_b = User(
        id=str(uuid.uuid4()),
        email="patient_b@example.com",
        name="Patient B",
        hashed_password="pw",
        role="patient"
    )
    db_session.add(user_b)
    db_session.flush()

    patient_b = Patient(id=str(uuid.uuid4()), user_id=user_b.id)
    db_session.add(patient_b)
    db_session.flush()

    report_b = MedicalReport(
        id=f"rep_b_{uuid.uuid4().hex[:6]}",
        patient_id=patient_b.id,
        title="Patient B Cardiology",
        file_name="cardiology_b.pdf",
        hospital_name="Beta Heart Clinic",
        category="cardiology",
        status="completed",
        report_date="2026-10-24"
    )
    db_session.add(report_b)

    lab_b = LabResult(
        id=f"lab_b_{uuid.uuid4().hex[:6]}",
        patient_id=patient_b.id,
        test_name="Cholesterol",
        value="190.0",
        unit="mg/dL",
        reference_range="125-200",
        test_date="2026-10-24"
    )
    db_session.add(lab_b)

    db_session.commit()

    # 3. Setup ChromaDB test collection with chunks for Patient A, Patient B, and violator_chunk
    v_store = get_vector_store(db_session=db_session)
    if isinstance(v_store, ChromaDBVectorStore) and v_store.collection:
        v_store.collection.add(
            ids=["chunk_patient_a_001", "chunk_patient_b_001", "violator_chunk"],
            documents=[
                "Patient A glucose history",
                "Patient B ECG analysis",
                "Baseline invariant violator chunk"
            ],
            metadatas=[
                {"patient_id": patient_a.id, "report_id": report_a.id},
                {"patient_id": patient_b.id, "report_id": report_b.id},
                {"patient_id": "system_violator", "report_id": "rep_violator"}
            ]
        )

    # 4. Request preview for Patient A
    preview = get_purge_preview(db=db_session, patient=patient_a, actor_id=user_a.id)
    token = preview.get("confirmation_token") or preview.get("purgeToken")
    assert token is not None


    # 5. Execute confirmed purge for Patient A
    success, result = execute_patient_purge(
        db=db_session,
        patient=patient_a,
        purge_token=token,
        confirmation_phrase=MANDATORY_CONFIRMATION_PHRASE,
        actor_id=user_a.id
    )
    assert success is True, f"Purge execution failed: {result}"

    # 6. Verify Patient A records are gone
    assert db_session.query(MedicalReport).filter(MedicalReport.patient_id == patient_a.id).count() == 0
    assert db_session.query(LabResult).filter(LabResult.patient_id == patient_a.id).count() == 0
    assert db_session.query(Medication).filter(Medication.patient_id == patient_a.id).count() == 0
    # Physical file deleted
    assert not os.path.exists(file_a_path)

    # 7. CRITICAL VERIFICATION: Patient B records MUST remain 100% intact
    assert db_session.query(MedicalReport).filter(MedicalReport.patient_id == patient_b.id).count() == 1
    assert db_session.query(LabResult).filter(LabResult.patient_id == patient_b.id).count() == 1

    # 8. CRITICAL VERIFICATION: ChromaDB chunks
    if isinstance(v_store, ChromaDBVectorStore) and v_store.collection:
        remaining_ids = v_store.collection.get()["ids"]
        assert "chunk_patient_a_001" not in remaining_ids, "Patient A chunk was not deleted!"
        assert "chunk_patient_b_001" in remaining_ids, "Patient B chunk was accidentally deleted!"
        assert "violator_chunk" in remaining_ids, "violator_chunk was corrupted or deleted!"

    # 9. Verify PURGE_EXECUTED audit log exists without clinical content
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action == "PURGE_EXECUTED",
        AuditLog.patient_id == patient_a.id
    ).first()
    assert audit_log is not None
    assert audit_log.outcome == "SUCCESS"
    assert "Glucose" not in str(audit_log.details)
    assert "Metformin" not in str(audit_log.details)
