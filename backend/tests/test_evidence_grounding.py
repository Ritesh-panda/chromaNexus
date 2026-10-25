"""
Phase 6: Evidence-Grounded Assistant & Citation Verification Test Suite.
Verifies all 17 mandatory failure modes, attribution accuracy, contradiction surfacing,
negation preservation, patient isolation, and Phase 5 regression safety.
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import LabResult
from backend.app.models.clinical_entity import Disease, Medication
from backend.app.clinical.verification.models import (
    ClaimType,
    ClaimVerificationStatus,
    ClinicalClaim,
    EvidenceGroundingResult
)
from backend.app.clinical.verification.claim_extractor import ClaimExtractor
from backend.app.clinical.verification.evidence_verifier import EvidenceVerifier
from backend.app.clinical.verification.answer_corrector import AnswerCorrector
from backend.app.clinical.verification.citation_validator import CitationValidator
from backend.app.clinical.verification.pipeline import EvidenceGroundingPipeline
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider
from backend.app.ai.retrieval import InMemoryVectorStore, DocumentChunk
from backend.app.schemas.chat import MessageResponse, CitationSchema


@pytest.fixture
def isolated_verification_db():
    """Provides an isolated SQLite database populated with multi-facility synthetic records."""
    temp_dir = tempfile.mkdtemp(prefix="p6_eval_")
    db_path = os.path.join(temp_dir, "eval.db")
    test_db_url = f"sqlite:///{db_path.replace(os.sep, '/')}"

    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Patient A
    u_a = User(id="usr_eval_alex", name="Alex Vance", email="alex@test.com", hashed_password="pwd")
    pat_a = Patient(id="pat_eval_alex", user_id=u_a.id)

    # Patient B (Isolation check)
    u_b = User(id="usr_eval_bob", name="Bob Smith", email="bob@test.com", hashed_password="pwd")
    pat_b = Patient(id="pat_eval_bob", user_id=u_b.id)

    db.add_all([u_a, pat_a, u_b, pat_b])
    db.commit()

    # Reports for Patient A
    rep_cmp = MedicalReport(
        id="rep_cmp_01",
        patient_id=pat_a.id,
        title="Comprehensive Metabolic Panel",
        report_date="2026-05-15",
        category="laboratory",
        hospital_name="Metro General",
        file_name="cmp.pdf",
        status="parsed"
    )
    rep_lipid = MedicalReport(
        id="rep_lipid_02",
        patient_id=pat_a.id,
        title="Lipid Profile & Glucose Screening",
        report_date="2026-10-12",
        category="laboratory",
        hospital_name="City Health Lab",
        file_name="lipid.pdf",
        status="parsed"
    )
    rep_conflict = MedicalReport(
        id="rep_conflict_03",
        patient_id=pat_a.id,
        title="Urgent Care Metabolic Panel",
        report_date="2026-10-12",
        category="laboratory",
        hospital_name="Metro General",
        file_name="uc.pdf",
        status="parsed"
    )
    rep_mri = MedicalReport(
        id="rep_mri_04",
        patient_id=pat_a.id,
        title="Right Knee MRI",
        report_date="2026-08-20",
        category="radiology",
        hospital_name="Advanced Imaging",
        file_name="mri.pdf",
        status="parsed"
    )

    # Report for Patient B
    rep_bob = MedicalReport(
        id="rep_bob_99",
        patient_id=pat_b.id,
        title="Bob Hematology Report",
        report_date="2026-09-01",
        category="laboratory",
        hospital_name="County Hospital",
        file_name="bob.pdf",
        status="parsed"
    )
    db.add_all([rep_cmp, rep_lipid, rep_conflict, rep_mri, rep_bob])
    db.commit()

    # Lab Results
    labs = [
        # Patient A: Potassium in CMP
        LabResult(
            id="lab_pot_cmp",
            patient_id=pat_a.id,
            test_name="Potassium, Serum",
            canonical_name="Potassium, Serum",
            loinc_code="2823-3",
            value="4.1",
            unit="mEq/L",
            reference_range="3.5 - 5.1",
            status="normal",
            test_date="2026-05-15",
            source_report_id=rep_cmp.id,
            hospital_name="Metro General"
        ),
        # Patient A: Potassium in City Health Lab
        LabResult(
            id="lab_pot_city",
            patient_id=pat_a.id,
            test_name="Potassium",
            canonical_name="Potassium, Serum",
            loinc_code="2823-3",
            value="5.2",
            unit="mEq/L",
            reference_range="3.5 - 5.1",
            status="high",
            test_date="2026-10-12",
            source_report_id=rep_lipid.id,
            hospital_name="City Health Lab"
        ),
        # Patient A: Conflicting Potassium from Metro General on same date
        LabResult(
            id="lab_pot_metro",
            patient_id=pat_a.id,
            test_name="Potassium",
            canonical_name="Potassium, Serum",
            loinc_code="2823-3",
            value="4.8",
            unit="mEq/L",
            reference_range="3.5 - 5.1",
            status="normal",
            test_date="2026-10-12",
            source_report_id=rep_conflict.id,
            hospital_name="Metro General"
        ),
        # Patient A: Glucose in CMP
        LabResult(
            id="lab_glu_cmp",
            patient_id=pat_a.id,
            test_name="Glucose",
            canonical_name="Glucose, Fasting Blood",
            loinc_code="1558-6",
            value="95",
            unit="mg/dL",
            reference_range="70 - 99",
            status="normal",
            test_date="2026-05-15",
            source_report_id=rep_cmp.id,
            hospital_name="Metro General"
        ),
        # Patient B: High Hemoglobin (Must remain isolated!)
        LabResult(
            id="lab_bob_hgb",
            patient_id=pat_b.id,
            test_name="Hemoglobin",
            canonical_name="Hemoglobin",
            loinc_code="718-7",
            value="14.2",
            unit="g/dL",
            reference_range="13.5 - 17.5",
            status="normal",
            test_date="2026-09-01",
            source_report_id=rep_bob.id,
            hospital_name="County Hospital"
        )
    ]
    db.add_all(labs)

    # Diagnoses for Patient A
    db.add(Disease(
        id="diag_dm2",
        patient_id=pat_a.id,
        name="Type 2 Diabetes Mellitus",
        icd_code="E11.9",
        status="active",
        diagnosed_date="2022-03-10"
    ))

    # Medications for Patient A
    db.add(Medication(
        id="med_metformin",
        patient_id=pat_a.id,
        name="Metformin",
        dosage="500 mg",
        frequency="twice daily",
        start_date="2022-03-10",
        status="active"
    ))
    db.commit()

    yield {
        "db": db,
        "pat_a": pat_a,
        "pat_b": pat_b,
        "rep_cmp": rep_cmp,
        "rep_lipid": rep_lipid,
        "rep_conflict": rep_conflict,
        "rep_mri": rep_mri
    }
    db.close()


# ==============================================================================
# Scenario 1: Correct numerical value and correct citation
# ==============================================================================
def test_01_correct_numerical_value_and_correct_citation(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your Potassium was 5.2 mEq/L on 2026-10-12 at City Health Lab."
    citations = [{
        "reportId": "rep_lipid_02",
        "reportTitle": "Lipid Profile & Glucose Screening",
        "date": "2026-10-12",
        "facility": "City Health Lab",
        "excerpt": "Potassium: 5.2 mEq/L (2026-10-12) - City Health Lab"
    }]

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert res.all_supported is True
    assert "5.2 mEq/L" in res.verified_answer
    assert len(res.citations) == 1
    assert res.citations[0]["reportId"] == "rep_lipid_02"


# ==============================================================================
# Scenario 2: Correct analyte with wrong value
# ==============================================================================
def test_02_correct_analyte_with_wrong_value(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your Potassium was 6.8 mEq/L on 2026-10-12 at City Health Lab."
    citations = [{
        "reportId": "rep_lipid_02",
        "reportTitle": "Lipid Profile & Glucose Screening",
        "date": "2026-10-12",
        "facility": "City Health Lab",
        "excerpt": "Potassium: 5.2 mEq/L (2026-10-12) - City Health Lab"
    }]

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert res.all_supported is False
    # Wrong value 6.8 is either corrected to 5.2 or qualified as unverified
    assert "6.8" not in res.verified_answer or "5.2" in res.verified_answer


# ==============================================================================
# Scenario 3: Correct value attributed to the wrong report
# ==============================================================================
def test_03_correct_value_attributed_to_wrong_report(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    # Candidate claims potassium 4.1 was from Lipid Profile, but it was in Comprehensive Metabolic Panel
    candidate = "In the Lipid Profile & Glucose Screening, your Potassium was 4.1 mEq/L on 2026-05-15."
    citations = [{
        "reportId": "rep_cmp_01",
        "reportTitle": "Comprehensive Metabolic Panel",
        "date": "2026-05-15",
        "facility": "Metro General",
        "excerpt": "Potassium, Serum: 4.1 mEq/L (2026-05-15) - Metro General"
    }]

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    # Attribution corrected to true source report title
    assert "Comprehensive Metabolic Panel" in res.verified_answer
    assert any(c["reportId"] == "rep_cmp_01" for c in res.citations)


# ==============================================================================
# Scenario 4: Wrong date or facility
# ==============================================================================
def test_04_wrong_date_or_facility(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your Glucose was 95 mg/dL on 2026-01-01 at Mayo Clinic."
    citations = [{
        "reportId": "rep_cmp_01",
        "reportTitle": "Comprehensive Metabolic Panel",
        "date": "2026-05-15",
        "facility": "Metro General",
        "excerpt": "Glucose: 95 mg/dL"
    }]

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert res.all_supported is False
    assert "No clinical documentation" in res.verified_answer or "Metro General" in res.verified_answer


# ==============================================================================
# Scenario 5: Wrong unit
# ==============================================================================
def test_05_wrong_unit(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your Potassium was 5.2 mg/dL on 2026-10-12."
    citations = [{
        "reportId": "rep_lipid_02",
        "reportTitle": "Lipid Profile & Glucose Screening",
        "date": "2026-10-12",
        "facility": "City Health Lab",
        "excerpt": "Potassium: 5.2 mEq/L"
    }]

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert res.all_supported is False
    assert "No clinical documentation" in res.verified_answer or "mEq/L" in res.verified_answer


# ==============================================================================
# Scenario 6: Same number appearing in an unrelated clinical context
# ==============================================================================
def test_06_same_number_appearing_in_unrelated_clinical_context(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your Potassium was 500 mEq/L."
    # 500 appears in medication context (Metformin 500 mg), NOT potassium!
    citations = [{
        "reportId": "rep_med_01",
        "reportTitle": "Medication Reconciliation",
        "date": "2026-05-15",
        "facility": "Metro General",
        "excerpt": "Metformin 500 mg oral tablet twice daily"
    }]

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert res.all_supported is False
    assert len(res.citations) == 0
    assert "No clinical documentation" in res.verified_answer


# ==============================================================================
# Scenario 7: Unsupported diagnosis in an otherwise supported answer
# ==============================================================================
def test_07_unsupported_diagnosis_in_otherwise_supported_answer(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your Potassium was 5.2 mEq/L on 2026-10-12, and you have chronic kidney disease."
    citations = [{
        "reportId": "rep_lipid_02",
        "reportTitle": "Lipid Profile & Glucose Screening",
        "date": "2026-10-12",
        "facility": "City Health Lab",
        "excerpt": "Potassium: 5.2 mEq/L"
    }]

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert "5.2" in res.verified_answer
    assert "No clinical documentation of chronic kidney disease" in res.verified_answer


# ==============================================================================
# Scenario 8: Unsupported positive claim mixed with a missing-data statement
# ==============================================================================
def test_08_unsupported_positive_claim_mixed_with_missing_data_statement(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your records do not contain any information about uric acid, and you were diagnosed with severe hypertension."
    citations = []

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert "do not contain" in res.verified_answer.lower() or "no clinical documentation" in res.verified_answer.lower()
    # Positive claim about severe hypertension must not bypass verification!
    assert "No clinical documentation of" in res.verified_answer


# ==============================================================================
# Scenario 9: Answer with no citations containing an unsupported medical claim
# ==============================================================================
def test_09_answer_with_no_citations_containing_unsupported_claim(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "You have acute renal failure and should immediately discontinue all medications."
    citations = []

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert res.all_supported is False
    assert len(res.citations) == 0
    assert "No clinical documentation" in res.verified_answer or "No verified clinical records" in res.verified_answer


# ==============================================================================
# Scenario 10: Contradictory evidence from multiple reports
# ==============================================================================
def test_10_contradictory_evidence_from_multiple_reports(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your records show conflicting Potassium results across facilities."
    citations = [
        {"reportId": "rep_lipid_02", "reportTitle": "Lipid Profile", "date": "2026-10-12", "facility": "City Health Lab", "excerpt": "Potassium: 5.2 mEq/L"},
        {"reportId": "rep_conflict_03", "reportTitle": "Urgent Care Panel", "date": "2026-10-12", "facility": "Metro General", "excerpt": "Potassium: 4.8 mEq/L"}
    ]

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert "conflicting" in res.verified_answer.lower()


# ==============================================================================
# Scenario 11: Narrative negation and negative findings
# ==============================================================================
def test_11_narrative_negation_and_negative_findings(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    citations = [{
        "reportId": "rep_mri_04",
        "reportTitle": "Right Knee MRI",
        "date": "2026-08-20",
        "facility": "Advanced Imaging",
        "excerpt": "Right Knee MRI: Findings demonstrate mild medial meniscus degeneration without tear. Cruciate ligaments intact."
    }]

    # 11a: Correct negative claim
    correct_candidate = "Your Right Knee MRI showed mild degeneration without tear and intact ligaments."
    res_correct = pipeline.verify_answer(correct_candidate, citations, patient_id=pat.id)
    assert res_correct.all_supported is True
    assert len(res_correct.citations) == 1

    # 11b: Contradicted positive claim (Polarity inversion)
    inverted_candidate = "Your Right Knee MRI showed a medial meniscus tear."
    res_inverted = pipeline.verify_answer(inverted_candidate, citations, patient_id=pat.id)
    assert res_inverted.all_supported is False
    assert "No clinical documentation" in res_inverted.verified_answer


# ==============================================================================
# Scenario 12: Partial answer where one claim is supported and another is not
# ==============================================================================
def test_12_partial_answer_one_claim_supported_one_unsupported(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your Glucose was 95 mg/dL on 2026-05-15. You were also diagnosed with liver cirrhosis."
    citations = [{
        "reportId": "rep_cmp_01",
        "reportTitle": "Comprehensive Metabolic Panel",
        "date": "2026-05-15",
        "facility": "Metro General",
        "excerpt": "Glucose: 95 mg/dL"
    }]

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert "95 mg/dL" in res.verified_answer
    assert "No clinical documentation of liver cirrhosis" in res.verified_answer


# ==============================================================================
# Scenario 13: Correct abstention when evidence is absent
# ==============================================================================
def test_13_correct_abstention_when_evidence_is_absent(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    candidate = "Your Troponin was 0.04 ng/mL."
    citations = []

    res = pipeline.verify_answer(candidate, citations, patient_id=pat.id)
    assert res.is_abstained is True
    assert len(res.citations) == 0
    assert "No clinical documentation matching your request" in res.verified_answer


# ==============================================================================
# Scenario 14: Patient-isolation enforcement during retrieval and verification
# ==============================================================================
def test_14_patient_isolation_enforcement(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat_a = isolated_verification_db["pat_a"]
    pat_b = isolated_verification_db["pat_b"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    # Bob has Hemoglobin 14.2 g/dL. Alex does NOT have Hemoglobin in records.
    # Attempt to ground Bob's lab value under Alex's identity:
    candidate = "Your Hemoglobin was 14.2 g/dL on 2026-09-01."
    citations = [{
        "reportId": "rep_bob_99",
        "reportTitle": "Bob Hematology Report",
        "date": "2026-09-01",
        "facility": "County Hospital",
        "excerpt": "Hemoglobin: 14.2 g/dL"
    }]

    # Executing as Alex Vance
    res_alex = pipeline.verify_answer(candidate, citations, patient_id=pat_a.id)
    assert res_alex.all_supported is False
    assert len(res_alex.citations) == 0  # Bob's report citation must be purged for Alex!
    assert "No clinical documentation" in res_alex.verified_answer

    # Executing as Bob Smith
    res_bob = pipeline.verify_answer(candidate, citations, patient_id=pat_b.id)
    assert res_bob.all_supported is True
    assert len(res_bob.citations) == 1
    assert res_bob.citations[0]["reportId"] == "rep_bob_99"


# ==============================================================================
# Scenario 15: Citation provenance for structured clinical trends
# ==============================================================================
def test_15_citation_provenance_for_structured_clinical_trends(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]
    pipeline = EvidenceGroundingPipeline(db_session=db)

    from backend.app.clinical.structured_query.detector import StructuredQueryDetector
    from backend.app.clinical.structured_query.engine import StructuredClinicalQueryEngine

    detector = StructuredQueryDetector()
    engine = StructuredClinicalQueryEngine(db)

    intent = detector.detect("How has my potassium changed over the last six months?")
    trend_res = engine.execute_query(intent, pat.id)

    grounded = pipeline.verify_structured_trend_response(trend_res, patient_id=pat.id)
    assert grounded.all_supported is True
    assert len(grounded.citations) >= 2
    for c in grounded.citations:
        assert "reportId" in c
        assert "date" in c
        assert "excerpt" in c


# ==============================================================================
# Scenario 16: Regression of existing Phase 5 numerical answers
# ==============================================================================
def test_16_regression_of_existing_phase_5_numerical_answers(isolated_verification_db):
    db = isolated_verification_db["db"]
    pat = isolated_verification_db["pat_a"]

    # Remove conflicting same-day reading so longitudinal trend is purely 4.1 -> 5.2
    db.query(LabResult).filter(LabResult.id == "lab_pot_metro").delete()
    db.commit()

    # Wrap isolated db into RAGPipeline
    rag_pipe = RAGPipeline(
        retriever=InMemoryVectorStore(),
        llm=MockDeterministicLLMProvider(),
        db_session=db
    )

    resp = rag_pipe.query("How has my potassium changed over the last six months?", patient_id=pat.id)
    assert resp.reasoning_type == "fact"
    assert resp.structured_trend is not None
    assert resp.structured_trend["trend_direction"] == "increasing"
    assert "5.2" in resp.answer
    assert "4.1" in resp.answer
    assert len(resp.citations) >= 2


# ==============================================================================
# Scenario 17: HTTP response and frontend citation rendering schema
# ==============================================================================
def test_17_http_response_and_frontend_citation_rendering():
    # Validates that CitationSchema and MessageResponse support enriched provenance
    cit = CitationSchema(
        reportId="rep_cmp_01",
        reportTitle="Comprehensive Metabolic Panel",
        excerpt="Potassium, Serum: 4.1 mEq/L (2026-05-15) - Metro General",
        date="2026-05-15",
        confidenceScore=0.98,
        pageNumber=1,
        facility="Metro General",
        analyte="Potassium, Serum",
        value="4.1",
        unit="mEq/L"
    )

    msg = MessageResponse(
        id="msg_001",
        sender="ai",
        text="Your Potassium, Serum was 4.1 mEq/L on 2026-05-15 at Metro General.",
        timestamp="10:30 AM",
        reasoningType="fact",
        citations=[cit]
    )

    dumped = msg.model_dump()
    assert dumped["sender"] == "ai"
    assert dumped["reasoningType"] == "fact"
    assert len(dumped["citations"]) == 1
    assert dumped["citations"][0]["facility"] == "Metro General"
    assert dumped["citations"][0]["value"] == "4.1"
