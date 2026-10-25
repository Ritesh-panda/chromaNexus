"""
Adversarial Clinical Citation Grounding Remediation Benchmark
============================================================
Comprehensive test suite asserting exact clinical fact verification:
1. Correct value, wrong full date (same month/year, different day).
2. Correct value, wrong known facility.
3. Correct value, wrong unlisted/unknown facility.
4. Correct value, missing required unit (bare number rejected).
5. Correct value, incompatible unit.
6. Similar numbers appearing in unrelated analytes.
7. Medication dosage (10 mg) colliding with a laboratory value (10 mg/dL).
8. Multiple reports with same value on different dates/facilities.
9. One supported and one unsupported claim in the same answer.
10. Ambiguous source metadata abstention.
"""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.retrieval import InMemoryVectorStore
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider


@pytest.fixture
def pipeline():
    store = InMemoryVectorStore()
    llm = MockDeterministicLLMProvider()
    return RAGPipeline(retriever=store, llm=llm)


@pytest.fixture
def adversarial_citations():
    return [
        {
            "reportId": "rep-cmp-01",
            "reportTitle": "Comprehensive Metabolic Panel",
            "date": "2026-10-12",
            "facility": "Metro Health",
            "excerpt": (
                "Comprehensive Metabolic Panel (2026-10-12) - Metro Health\n"
                "Potassium: 5.8 mEq/L [HIGH] (Ref: 3.5-5.0)\n"
                "Sodium: 140 mEq/L (Ref: 135-145)"
            ),
            "confidenceScore": 0.98
        },
        {
            "reportId": "rep-cbc-01",
            "reportTitle": "Complete Blood Count",
            "date": "2026-10-12",
            "facility": "Metro Health",
            "excerpt": (
                "Complete Blood Count (2026-10-12) - Metro Health\n"
                "WBC: 5.8 x10^3/uL (Ref: 4.0-11.0)\n"
                "Hemoglobin: 14.2 g/dL"
            ),
            "confidenceScore": 0.95
        },
        {
            "reportId": "rep-glu-01",
            "reportTitle": "Outpatient Fasting Glucose",
            "date": "2026-09-01",
            "facility": "Metro Health",
            "excerpt": (
                "Outpatient Fasting Glucose (2026-09-01) - Metro Health\n"
                "Fasting Plasma Glucose: 105 mg/dL (Ref: 70-99)"
            ),
            "confidenceScore": 0.95
        },
        {
            "reportId": "rep-glu-02",
            "reportTitle": "Follow-up Fasting Glucose",
            "date": "2026-09-15",
            "facility": "Valley Lab",
            "excerpt": (
                "Follow-up Fasting Glucose (2026-09-15) - Valley Lab\n"
                "Fasting Plasma Glucose: 105 mg/dL (Ref: 70-99)"
            ),
            "confidenceScore": 0.95
        },
        {
            "reportId": "rep-rx-01",
            "reportTitle": "Prescription Record",
            "date": "2026-08-15",
            "facility": "Metro Health",
            "excerpt": "Prescription: Lisinopril 10 mg oral daily. Refills: 3.",
            "confidenceScore": 0.90
        }
    ]


def test_01_correct_value_wrong_full_date(pipeline, adversarial_citations):
    """1. Evidence date 2026-10-12; answer date 2026-10-13 must be rejected."""
    answer = "Your potassium was 5.8 mEq/L on 2026-10-13 at Metro Health."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, adversarial_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert len(rep_ids) == 0, f"Expected 0 citations due to full date mismatch, got {rep_ids}"


def test_02_correct_value_wrong_known_facility(pipeline, adversarial_citations):
    """2. Evidence facility Metro Health; answer claims Memorial Hospital."""
    answer = "Your potassium was 5.8 mEq/L on 2026-10-12 at Memorial Hospital."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, adversarial_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert len(rep_ids) == 0, f"Expected 0 citations due to known facility mismatch, got {rep_ids}"


def test_03_correct_value_wrong_unlisted_facility(pipeline, adversarial_citations):
    """3. Evidence facility Metro Health; answer claims unlisted St. Jude Hospital."""
    answer = "Your potassium was 5.8 mEq/L on 2026-10-12 at St. Jude Hospital."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, adversarial_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert len(rep_ids) == 0, f"Expected 0 citations due to unlisted facility mismatch, got {rep_ids}"


def test_04_correct_value_missing_required_unit(pipeline, adversarial_citations):
    """4. Evidence has 5.8 mEq/L; answer gives bare number 5.8 without unit."""
    answer = "Your potassium was 5.8 on 2026-10-12 at Metro Health."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, adversarial_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert len(rep_ids) == 0, f"Bare number 5.8 without unit must not be verified: {rep_ids}"


def test_05_correct_value_incompatible_unit(pipeline, adversarial_citations):
    """5. Evidence has 5.8 mEq/L; answer gives 5.8 mg/dL."""
    answer = "Your potassium was 5.8 mg/dL on 2026-10-12 at Metro Health."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, adversarial_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert len(rep_ids) == 0, f"Incompatible unit mg/dL must not receive mEq/L citation: {rep_ids}"


def test_06_similar_numbers_unrelated_analytes(pipeline, adversarial_citations):
    """6. Evidence has WBC 5.8 and Potassium 5.8; claim asserts Sodium 5.8."""
    answer = "Your sodium level was 5.8 mEq/L on 2026-10-12."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, adversarial_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert len(rep_ids) == 0, f"Sodium 5.8 must not match potassium 5.8: {rep_ids}"


def test_07_medication_dosage_colliding_with_lab_value(pipeline, adversarial_citations):
    """7. Lisinopril 10 mg must never ground a claim of glucose 10 mg/dL."""
    answer = "Your fasting blood glucose was 10 mg/dL."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, adversarial_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert len(rep_ids) == 0, f"10 mg Lisinopril must not ground glucose 10 mg/dL: {rep_ids}"


def test_08_multiple_reports_same_value_different_dates_facilities(pipeline, adversarial_citations):
    """8. Multiple reports with same value: cite only the report matching date & facility."""
    # Claim 1: 2026-09-01 at Metro Health -> should only cite rep-glu-01
    ans1 = "Your fasting glucose was 105 mg/dL on 2026-09-01 at Metro Health."
    _, g1 = pipeline._reconcile_and_ground_answer(ans1, adversarial_citations)
    assert [c["reportId"] for c in g1] == ["rep-glu-01"], f"Expected rep-glu-01, got {[c['reportId'] for c in g1]}"

    # Claim 2: 2026-09-15 at Valley Lab -> should only cite rep-glu-02
    ans2 = "Your fasting glucose was 105 mg/dL on 2026-09-15 at Valley Lab."
    _, g2 = pipeline._reconcile_and_ground_answer(ans2, adversarial_citations)
    assert [c["reportId"] for c in g2] == ["rep-glu-02"], f"Expected rep-glu-02, got {[c['reportId'] for c in g2]}"


def test_09_mixed_supported_and_unsupported_claim(pipeline, adversarial_citations):
    """9. Mixed answer: Supported claim cited, ungrounded diagnostic conclusion flagged."""
    answer = (
        "Your potassium level was 5.8 mEq/L at Metro Health on 2026-10-12. "
        "You were diagnosed with acute biventricular endocarditis."
    )
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, adversarial_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert rep_ids == ["rep-cmp-01"], f"Expected only CMP citation, got {rep_ids}"
    assert "endocarditis" in reconciled_ans
    assert "No clinical documentation" in reconciled_ans, f"Expected documentation warning in: {reconciled_ans}"


def test_10_ambiguous_source_metadata_abstention(pipeline):
    """10. Ambiguous source metadata: If source facility cannot be verified, abstain from citing."""
    citations = [
        {
            "reportId": "rep-ambig-01",
            "reportTitle": "Laboratory Report",
            "date": "2026-10-12",
            "facility": "Unknown Clinic",
            "excerpt": "Laboratory Report (2026-10-12) - Unknown Clinic\nPotassium: 5.8 mEq/L",
            "confidenceScore": 0.85
        }
    ]
    # Sentence asserts St. Jude Hospital, but record is from Unknown Clinic
    answer = "Your potassium was 5.8 mEq/L at St. Jude Hospital on 2026-10-12."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, citations)
    assert len(grounded) == 0, f"Ambiguous/mismatched facility must receive 0 citations: {grounded}"
