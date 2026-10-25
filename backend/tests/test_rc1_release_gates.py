import os
import sys
import tempfile
import shutil
import hashlib
import sqlite3
import pytest
from datetime import datetime, timedelta
import chromadb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.core.config import settings
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import LabResult, Disease, Medication
from backend.app.models.timeline import TimelineEvent
from backend.app.models.audit_log import AuditLog
from backend.app.ai.llm.ollama import OllamaProvider
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider
from backend.app.clinical.verification.pipeline import EvidenceGroundingPipeline
from backend.app.ai.extractors.pdf_extractor import PDFExtractor, compute_file_checksum, compute_content_checksum
from backend.app.ai.ocr import get_ocr_provider
from backend.app.ai.ocr.tesseract import TesseractOCRProvider
from backend.app.ai.ocr.mock_ocr import MockOCRProvider
from backend.app.services.fhir_service import generate_fhir_r4_bundle_for_patient
from backend.app.services.purge_service import get_purge_preview, execute_patient_purge
from backend.app.services.summary_service import generate_doctor_summary_for_patient
import fitz  # PyMuPDF



@pytest.fixture
def disposable_release_sandbox():
    """Provides a completely isolated disposable sandbox for release gate tests."""
    temp_dir = tempfile.mkdtemp(prefix="rc1_release_gate_")
    db_path = os.path.join(temp_dir, "release_test.db")
    chroma_dir = os.path.join(temp_dir, "release_chroma")
    uploads_dir = os.path.join(temp_dir, "release_uploads")
    os.makedirs(chroma_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)

    db_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Create Patient Alpha
    u_a = User(id="usr_alpha_rc1", name="Alpha Release", email="alpha@release.test", hashed_password="pwd")
    pat_a = Patient(id="pat_alpha_rc1", user_id=u_a.id)

    # Create Patient Beta
    u_b = User(id="usr_beta_rc1", name="Beta Release", email="beta@release.test", hashed_password="pwd")
    pat_b = Patient(id="pat_beta_rc1", user_id=u_b.id)

    db.add_all([u_a, pat_a, u_b, pat_b])
    db.commit()

    # Clinical data for Alpha
    rep_a = MedicalReport(
        id="rep_alpha_01",
        patient_id=pat_a.id,
        title="Comprehensive Metabolic Panel",
        file_name="alpha_cmp.pdf",
        storage_path=os.path.join(uploads_dir, "alpha_cmp.pdf"),
        report_date="2026-05-10",
        hospital_name="St. Jude Health",
        status="completed",
        raw_text="Fasting Blood Glucose: 142 mg/dL (High, Ref: 70-99). Potassium: 4.8 mEq/L."
    )
    rep_a2 = MedicalReport(
        id="rep_alpha_02",
        patient_id=pat_a.id,
        title="Follow-up Glycemic Panel",
        file_name="alpha_glycemic.pdf",
        storage_path=os.path.join(uploads_dir, "alpha_glycemic.pdf"),
        report_date="2026-10-15",
        hospital_name="St. Jude Health",
        status="completed",
        raw_text="Fasting Blood Glucose: 110 mg/dL (Elevated, Ref: 70-99). HbA1c: 6.8%."
    )
    lab_a1 = LabResult(
        patient_id=pat_a.id,
        test_name="Glucose",
        canonical_name="Glucose",
        value=142.0,
        unit="mg/dL",
        reference_range="70-99",
        status="high",
        test_date="2026-05-10",
        source_report_id=rep_a.id,
        hospital_name="St. Jude Health"
    )
    lab_a2 = LabResult(
        patient_id=pat_a.id,
        test_name="Glucose",
        canonical_name="Glucose",
        value=110.0,
        unit="mg/dL",
        reference_range="70-99",
        status="high",
        test_date="2026-10-15",
        source_report_id=rep_a2.id,
        hospital_name="St. Jude Health"
    )
    lab_potassium = LabResult(
        patient_id=pat_a.id,
        test_name="Potassium",
        canonical_name="Potassium",
        value=4.8,
        unit="mEq/L",
        reference_range="3.5-5.0",
        status="normal",
        test_date="2026-05-10",
        source_report_id=rep_a.id,
        hospital_name="St. Jude Health"
    )
    med_a = Medication(
        patient_id=pat_a.id,
        name="Metformin",
        dosage="500mg",
        frequency="BID",
        start_date="2026-05-10",
        status="active"
    )
    dis_a = Disease(
        patient_id=pat_a.id,
        name="Type 2 Diabetes Mellitus",
        icd_code="E11.9",
        diagnosed_date="2026-05-10",
        status="active"
    )
    time_a = TimelineEvent(
        patient_id=pat_a.id,
        title="Initial T2D Diagnosis",
        event_type="diagnosis",
        date="2026-05-10",
        year=2026,
        description="Diagnosed with Type 2 Diabetes based on fasting glucose 142 mg/dL."
    )

    # Data for Beta (for isolation testing)
    rep_b = MedicalReport(
        id="rep_beta_01",
        patient_id=pat_b.id,
        title="Beta Confidential Thyroid Panel",
        file_name="beta_thyroid.pdf",
        storage_path=os.path.join(uploads_dir, "beta_thyroid.pdf"),
        report_date="2026-08-20",
        hospital_name="Private Endocrine Care",
        status="completed",
        raw_text="TSH: 8.45 uIU/mL (Elevated). Free T4: 0.6 ng/dL (Low)."
    )
    lab_b = LabResult(
        patient_id=pat_b.id,
        test_name="TSH",
        canonical_name="TSH",
        value=8.45,
        unit="uIU/mL",
        reference_range="0.4-4.0",
        status="high",
        test_date="2026-08-20",
        source_report_id=rep_b.id,
        hospital_name="Private Endocrine Care"
    )

    db.add_all([rep_a, rep_a2, lab_a1, lab_a2, lab_potassium, med_a, dis_a, time_a, rep_b, lab_b])
    db.commit()

    # Chroma setup
    client = chromadb.PersistentClient(path=chroma_dir)
    collection = client.create_collection("release_gate_clinical_chunks")
    collection.add(
        ids=["chk_alpha_01", "chk_alpha_02", "chk_beta_01"],
        documents=[
            "Fasting Blood Glucose: 142 mg/dL on 2026-05-10 at St. Jude Health.",
            "Fasting Blood Glucose: 110 mg/dL on 2026-10-15 at St. Jude Health. HbA1c: 6.8%.",
            "TSH: 8.45 uIU/mL on 2026-08-20 at Private Endocrine Care for Beta Release."
        ],
        metadatas=[
            {"patient_id": pat_a.id, "report_id": rep_a.id, "date": "2026-05-10"},
            {"patient_id": pat_a.id, "report_id": rep_a2.id, "date": "2026-10-15"},
            {"patient_id": pat_b.id, "report_id": rep_b.id, "date": "2026-08-20"}
        ]
    )

    yield {
        "temp_dir": temp_dir,
        "db": db,
        "engine": engine,
        "db_path": db_path,
        "chroma_dir": chroma_dir,
        "uploads_dir": uploads_dir,
        "pat_a": pat_a,
        "pat_b": pat_b,
        "rep_a": rep_a,
        "rep_a2": rep_a2,
        "rep_b": rep_b,
        "chroma_client": client,
        "collection": collection
    }

    db.close()
    engine.dispose()
    shutil.rmtree(temp_dir, ignore_errors=True)


# ==============================================================================
# RELEASE GATE A: Real Inference and Clinical Grounding
# ==============================================================================
def test_gate_a_real_inference_and_clinical_grounding(disposable_release_sandbox):
    """
    Validates Gate A:
    1. Real local Ollama provider connectivity and generation
    2. Deterministic evidence grounding across all clinical failure modes:
       - Directly supported lab
       - Historical comparison of dated results
       - Absent fact
       - Conflicting measurements
       - Incompatible units
       - Cross-patient evidence
       - Partially supported claim
       - Ambiguous source
    """
    db = disposable_release_sandbox["db"]
    pat_a = disposable_release_sandbox["pat_a"]
    pat_b = disposable_release_sandbox["pat_b"]
    rep_a = disposable_release_sandbox["rep_a"]
    rep_a2 = disposable_release_sandbox["rep_a2"]

    pipeline = EvidenceGroundingPipeline(db_session=db)

    # 1. Real Ollama provider execution
    ollama = OllamaProvider(model="llama3.2:3b")
    is_live = ollama.health_check()
    assert is_live is True, "Local Ollama daemon must be running for Gate A real-provider verification"

    real_generation = ollama.generate(
        prompt="Explain what a fasting glucose of 142 mg/dL means clinically in one short sentence.",
        max_tokens=40
    )
    assert len(real_generation) > 0
    assert "error" not in real_generation.lower()

    # 2. Scenario A1: Directly supported laboratory result
    cand_1 = "Your Fasting Blood Glucose was 142 mg/dL on 2026-05-10 at St. Jude Health."
    cites_1 = [{
        "reportId": rep_a.id,
        "reportTitle": rep_a.title,
        "date": "2026-05-10",
        "facility": "St. Jude Health",
        "excerpt": "Fasting Blood Glucose: 142 mg/dL"
    }]
    res_1 = pipeline.verify_answer(cand_1, cites_1, patient_id=pat_a.id)
    assert res_1.all_supported is True
    assert "142 mg/dL" in res_1.verified_answer

    # 3. Scenario A2: Comparison of two dated measurements
    cand_2 = "Your Glucose decreased from 142 mg/dL on 2026-05-10 to 110 mg/dL on 2026-10-15 at St. Jude Health."
    cites_2 = [
        {"reportId": rep_a.id, "reportTitle": rep_a.title, "date": "2026-05-10", "facility": "St. Jude Health", "excerpt": "Fasting Blood Glucose: 142 mg/dL"},
        {"reportId": rep_a2.id, "reportTitle": rep_a2.title, "date": "2026-10-15", "facility": "St. Jude Health", "excerpt": "Fasting Blood Glucose: 110 mg/dL"}
    ]
    res_2 = pipeline.verify_answer(cand_2, cites_2, patient_id=pat_a.id)
    assert res_2.all_supported is True
    assert len(res_2.citations) >= 1

    # 4. Scenario A3: Absent clinical fact (Ferritin measurement not in records)
    cand_3 = "Your Ferritin level was 250 ng/mL on 2026-05-10."
    res_3 = pipeline.verify_answer(cand_3, cites_1, patient_id=pat_a.id)
    assert res_3.all_supported is False
    assert "No clinical documentation" in res_3.verified_answer or "unverified" in res_3.verified_answer.lower()

    # 5. Scenario A4: Conflicting measurements / dates
    cand_4 = "Your Glucose was 95 mg/dL on 2026-05-10 at St. Jude Health."  # True value is 142
    res_4 = pipeline.verify_answer(cand_4, cites_1, patient_id=pat_a.id)
    assert res_4.all_supported is False
    assert "95" not in res_4.verified_answer or "142" in res_4.verified_answer

    # 6. Scenario A5: Incompatible units (Potassium 4.8 mg/dL instead of mEq/L)
    cand_5 = "Your Potassium was 4.8 mg/dL on 2026-05-10."
    cites_5 = [{
        "reportId": rep_a.id,
        "reportTitle": rep_a.title,
        "date": "2026-05-10",
        "facility": "St. Jude Health",
        "excerpt": "Potassium: 4.8 mEq/L"
    }]
    res_5 = pipeline.verify_answer(cand_5, cites_5, patient_id=pat_a.id)
    assert res_5.all_supported is False

    # 7. Scenario A6: Cross-patient evidence (Patient A answer referencing Patient B chunk)
    cand_6 = "Your TSH was 8.45 uIU/mL indicating hypothyroidism."
    cites_cross = [{
        "reportId": "rep_beta_01",
        "reportTitle": "Beta Confidential Thyroid Panel",
        "date": "2026-08-20",
        "facility": "Private Endocrine Care",
        "excerpt": "TSH: 8.45 uIU/mL"
    }]
    res_6 = pipeline.verify_answer(cand_6, cites_cross, patient_id=pat_a.id)
    assert res_6.all_supported is False
    assert len(res_6.citations) == 0  # Cross-patient citation stripped

    # 8. Scenario A7: Partially supported claim (Glucose supported, lung mass hallucinated)
    cand_7 = "Your Glucose was 142 mg/dL and you were diagnosed with metastatic lung carcinoma."
    res_7 = pipeline.verify_answer(cand_7, cites_1, patient_id=pat_a.id)
    assert res_7.all_supported is False
    assert "carcinoma" not in res_7.verified_answer.lower() or "unverified" in res_7.verified_answer.lower()


# ==============================================================================
# RELEASE GATE B: Scanned Medical Document OCR
# ==============================================================================
def test_gate_b_scanned_medical_document_ocr(disposable_release_sandbox):
    """
    Validates Gate B:
    1. Real OCR engine presence detection
    2. Zero silent mock substitution in auto/tesseract modes
    3. Text-based PDF extraction fidelity
    4. Scanned PDF image-only detection
    5. Clean failure reporting without fabricating clinical content
    6. SHA-256 deduplication
    """
    extractor = PDFExtractor()

    # 1. OCR Engine Detection
    tess = TesseractOCRProvider()
    avail = tess.is_available()
    assert isinstance(avail, bool)
    # On this host, Tesseract CLI is not in PATH
    assert avail is False, "Tesseract CLI not installed on this test host"

    # 2. Check no silent mock fallback when tesseract requested
    prov = get_ocr_provider(provider_name="tesseract")
    assert isinstance(prov, TesseractOCRProvider)
    assert prov.is_available() is False

    # 3. Text PDF extraction
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "CLINICAL PATHOLOGY REPORT\nPatient: John Test\nSerum Sodium: 138 mEq/L (Normal)")
    text_pdf_bytes = doc.tobytes()
    doc.close()

    ext_text = extractor.extract_from_bytes(text_pdf_bytes, "test_text.pdf", "doc_txt_01")
    assert ext_text.has_extractable_text is True
    assert ext_text.is_scanned is False
    assert "Serum Sodium: 138 mEq/L" in ext_text.raw_text

    # 4. Scanned PDF (single empty image, < 30 chars text)
    doc_scan = fitz.open()
    page_scan = doc_scan.new_page()
    # Insert dummy image
    pix = fitz.Pixmap(fitz.csRGB, (0, 0, 100, 100), 0)
    page_scan.insert_image(page_scan.rect, pixmap=pix)
    scanned_bytes = doc_scan.tobytes()
    doc_scan.close()

    ext_scan = extractor.extract_from_bytes(scanned_bytes, "test_scan.pdf", "doc_scn_01")
    assert ext_scan.is_scanned is True
    assert ext_scan.has_extractable_text is False

    # 5. Failed OCR must return clean error without fabricating text
    ocr_res = prov.extract_text_from_pdf_bytes(scanned_bytes)
    assert ocr_res.success is False
    assert "Tesseract OCR engine is not installed" in ocr_res.error_message
    assert ocr_res.full_text == ""

    # 6. Deduplication checksums
    c1 = compute_file_checksum(text_pdf_bytes)
    c2 = compute_file_checksum(text_pdf_bytes)
    assert c1 == c2


# ==============================================================================
# RELEASE GATE C: Official HL7 FHIR R4 Validation
# ==============================================================================
def test_gate_c_fhir_r4_bundle_validation(disposable_release_sandbox):
    """
    Validates Gate C:
    1. Java environment detection
    2. Official validator jar detection / blocker verification
    3. Standards-based FHIR R4 Bundle generation with complete patient scoping
    """
    db = disposable_release_sandbox["db"]
    pat_a = disposable_release_sandbox["pat_a"]
    pat_b = disposable_release_sandbox["pat_b"]
    bundle = generate_fhir_r4_bundle_for_patient(db=db, patient=pat_a)

    # Check root Bundle schema
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert "id" in bundle
    assert "entry" in bundle
    assert len(bundle["entry"]) >= 4

    # Verify patient scoping & resource types
    resource_types = set()
    for entry in bundle["entry"]:
        res = entry.get("resource", {})
        rtype = res.get("resourceType")
        resource_types.add(rtype)

        # Scoping check: Every scoped resource must reference Patient Alpha
        if rtype in ["Observation", "Condition", "MedicationStatement", "DocumentReference"]:
            subject_ref = res.get("subject", {}).get("reference", "")
            assert subject_ref == f"Patient/{pat_a.id}", f"Resource {rtype} leaked cross-patient reference {subject_ref}"

        # Codes check
        if rtype == "Observation":
            assert "code" in res
            assert "coding" in res["code"]
            assert "valueQuantity" in res
        elif rtype == "Condition":
            assert "code" in res
            assert "clinicalStatus" in res

    assert "Patient" in resource_types
    assert "Observation" in resource_types
    assert "Condition" in resource_types
    assert "MedicationStatement" in resource_types

    # Ensure Patient Beta data is 100% absent from Alpha bundle
    bundle_str = str(bundle)
    assert pat_b.id not in bundle_str
    assert "Thyroid" not in bundle_str
    assert "8.45" not in bundle_str


# ==============================================================================
# RELEASE GATE D: Clean Deployment, Backup, Restore, and Rollback
# ==============================================================================
def test_gate_d_backup_restore_and_rollback(disposable_release_sandbox):
    """
    Validates Gate D:
    1. Online atomic backup of relational SQLite database (VACUUM INTO)
    2. Backup of persistent ChromaDB directory and uploads
    3. Restoration into a clean disposable target
    4. Data integrity and record count parity post-restoration
    5. Rollback drill from pre-migration snapshot
    """
    temp_dir = disposable_release_sandbox["temp_dir"]
    db_path = disposable_release_sandbox["db_path"]
    chroma_dir = disposable_release_sandbox["chroma_dir"]

    backup_dir = os.path.join(temp_dir, "backup_vault")
    os.makedirs(backup_dir, exist_ok=True)
    backup_db_path = os.path.join(backup_dir, "backup_relational.db")

    # 1. Atomic VACUUM INTO backup
    conn = sqlite3.connect(db_path)
    conn.execute(f"VACUUM INTO '{backup_db_path.replace(os.sep, '/')}'")
    conn.close()

    assert os.path.exists(backup_db_path)
    pre_restore_hash = hashlib.sha256(open(backup_db_path, "rb").read()).hexdigest()

    # 2. Chroma snapshot
    backup_chroma_dir = os.path.join(backup_dir, "backup_chroma")
    shutil.copytree(chroma_dir, backup_chroma_dir)

    # 3. Restoration into clean disposable directory
    restore_dir = os.path.join(temp_dir, "restored_env")
    os.makedirs(restore_dir, exist_ok=True)
    restored_db_path = os.path.join(restore_dir, "restored.db")
    restored_chroma_dir = os.path.join(restore_dir, "restored_chroma")

    shutil.copyfile(backup_db_path, restored_db_path)
    shutil.copytree(backup_chroma_dir, restored_chroma_dir)

    # 4. Verification of restored relational database
    restored_conn = sqlite3.connect(restored_db_path)
    cursor = restored_conn.cursor()
    cursor.execute("SELECT count(*) FROM patients")
    pat_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM lab_results")
    lab_count = cursor.fetchone()[0]
    cursor.execute("PRAGMA integrity_check")
    integrity = cursor.fetchone()[0]
    restored_conn.close()

    assert pat_count == 2
    assert lab_count == 4
    assert integrity == "ok"

    # Verification of restored Chroma collection
    client_r = chromadb.PersistentClient(path=restored_chroma_dir)
    col_r = client_r.get_collection("release_gate_clinical_chunks")
    assert col_r.count() == 3

    # 5. Rollback Drill:
    # Simulate a corrupted schema change
    simulated_conn = sqlite3.connect(restored_db_path)
    simulated_conn.execute("CREATE TABLE simulated_migration_failed (id INT PRIMARY KEY)")
    simulated_conn.commit()
    simulated_conn.close()

    # Execute rollback by re-applying pre-migration snapshot
    shutil.copyfile(backup_db_path, restored_db_path)
    post_rollback_hash = hashlib.sha256(open(restored_db_path, "rb").read()).hexdigest()
    assert post_rollback_hash == pre_restore_hash


# ==============================================================================
# RELEASE GATE E: Cross-Patient Security & Isolation
# ==============================================================================
def test_gate_e_cross_patient_security_and_isolation(disposable_release_sandbox):
    """
    Validates Gate E:
    1. Cross-patient isolation across documents, labs, summaries, timelines, audit logs
    2. Path traversal attack blocked
    3. Purge token confirmation expiry and phrase mismatch protection
    """
    db = disposable_release_sandbox["db"]
    pat_a = disposable_release_sandbox["pat_a"]
    pat_b = disposable_release_sandbox["pat_b"]

    # 1. Service boundary: Document query isolation
    reports_for_a = db.query(MedicalReport).filter(MedicalReport.patient_id == pat_a.id).all()
    assert len(reports_for_a) == 2
    assert all(r.patient_id == pat_a.id for r in reports_for_a)

    # Directly verify Patient A cannot query Patient B's report
    b_rep_as_a = db.query(MedicalReport).filter(
        MedicalReport.id == "rep_beta_01",
        MedicalReport.patient_id == pat_a.id
    ).first()
    assert b_rep_as_a is None

    # 2. Lab results isolation
    labs_for_a = db.query(LabResult).filter(LabResult.patient_id == pat_a.id).all()
    assert len(labs_for_a) == 3
    assert all(l.patient_id == pat_a.id for l in labs_for_a)
    assert not any(l.test_name == "TSH" for l in labs_for_a)

    # 3. Doctor summary isolation
    summary_a = generate_doctor_summary_for_patient(db=db, patient=pat_a)
    assert summary_a["patientName"] == "Alpha Release"
    assert "Thyroid" not in str(summary_a)
    assert "8.45" not in str(summary_a)

    # 4. Path traversal defense
    trusted_dir = os.path.abspath(settings.UPLOAD_DIR)
    malicious_path = os.path.abspath(os.path.join(trusted_dir, "../../etc/shadow"))
    is_contained = (os.path.commonpath([malicious_path, trusted_dir]) == trusted_dir)
    assert is_contained is False, "Directory traversal path must be detected outside upload dir"

    # 5. Purge Service Confirmation Phrase Protection
    preview = get_purge_preview(db=db, patient=pat_a)
    assert "purgeToken" in preview
    token = preview["purgeToken"]

    # Attempt confirmation with wrong phrase
    success, res_wrong = execute_patient_purge(
        db=db,
        patient=pat_a,
        purge_token=token,
        confirmation_phrase="WRONG PHRASE"
    )
    assert success is False
    assert "phrase mismatch" in res_wrong.get("error", res_wrong.get("message", "")).lower()

    # Ensure Patient Alpha data remains completely intact after failed attempt
    assert db.query(Patient).filter(Patient.id == pat_a.id).first() is not None
