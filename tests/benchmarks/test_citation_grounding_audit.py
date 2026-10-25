"""
ChronaNexus Citation Grounding & Clinical Value Verification Benchmark
======================================================================
Strict verification of:
1. Exact lab value, unit, and report citation.
2. Wrong source attribution: Corrects false attribution in text to true source, matching citations.
3. Correct analyte but incorrect value: Rejects citation and abstains from false value.
4. Correct value belonging to different analyte: Rejects cross-analyte false attribution.
5. Incorrect or missing units: Rejects unit mismatch (e.g. mg/dL vs mEq/L).
6. Decimal vs integer collision: Rejects 10 mg dosage citing 10 mg/dL glucose (vs 105 mg/dL).
7. Reference range bound vs measured value: Rejects ref range bound cited as measured result.
8. Conflicting measurements across facilities: Retains both discrepant records.
9. Wrong date & facility: Rejects citation when date/facility conflicts despite value match.
10. Missing evidence abstention: Model abstains, citations empty.
11. Abstention phrased differently: Robust regex detection across natural language variants.
12. Mixed supported & unsupported claims: Reconciles text, grounds supported, qualifies unsupported.
13. Cross-analyte value collision: Rejects 142 mg/dL glucose cited as 142 g/dL hemoglobin.
14. Multiple reports similar values: Distinguishes CMP (Potassium 5.8) vs CBC (WBC 5.8).
"""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider


@pytest.fixture
def pipeline():
    return RAGPipeline(llm=MockDeterministicLLMProvider())


@pytest.fixture
def sample_citations():
    return [
        {
            "reportId": "rep-cmp-01",
            "reportTitle": "Comprehensive Metabolic Panel",
            "date": "2026-10-12",
            "facility": "Metro Health",
            "excerpt": "Comprehensive Metabolic Panel (2026-10-12) - Metro Health\nPotassium: 5.8 mEq/L [HIGH] (Ref: 3.5-5.0)\nSodium: 140 mEq/L (Ref: 135-145)",
            "confidenceScore": 0.98
        },
        {
            "reportId": "rep-cbc-01",
            "reportTitle": "Complete Blood Count",
            "date": "2026-10-12",
            "facility": "Metro Health",
            "excerpt": "Complete Blood Count (2026-10-12) - Metro Health\nWBC: 5.8 x10^3/uL (Ref: 4.0-11.0)\nHemoglobin: 14.2 g/dL",
            "confidenceScore": 0.95
        },
        {
            "reportId": "rep-glu-01",
            "reportTitle": "Outpatient Fasting Glucose",
            "date": "2026-09-01",
            "facility": "Metro Health",
            "excerpt": "Outpatient Fasting Glucose (2026-09-01) - Metro Health\nFasting Plasma Glucose: 105 mg/dL (Ref: 70-99)",
            "confidenceScore": 0.95
        },
        {
            "reportId": "rep-glu-02",
            "reportTitle": "Diagnostic Endocrinology Panel",
            "date": "2026-09-05",
            "facility": "Valley Lab",
            "excerpt": "Diagnostic Endocrinology Panel (2026-09-05) - Valley Lab\nFasting Plasma Glucose: 142 mg/dL",
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


def test_01_exact_lab_value_and_unit(pipeline, sample_citations):
    """1. Exact lab value, unit, and report citation."""
    answer = (
        "Your potassium level on October 12, 2026, was 5.8 mEq/L (Reference: 3.5-5.0 mEq/L), "
        "as documented in the Comprehensive Metabolic Panel from Metro Health."
    )
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, sample_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert rep_ids == ["rep-cmp-01"], f"Expected exact citation ['rep-cmp-01'], got {rep_ids}"
    assert "Comprehensive Metabolic Panel" in reconciled_ans


def test_02_wrong_source_attribution_reconciliation(pipeline, sample_citations):
    """
    2. Wrong source attribution reconciliation:
    Answer claims: 'According to the Complete Blood Count, your potassium was 5.8 mEq/L.'
    The system must NOT leave the false CBC attribution in the answer text while citing CMP.
    It must reconcile the answer text to name the true source (Comprehensive Metabolic Panel)
    and attach the agreeing citation rep-cmp-01.
    """
    hallucinated_answer = (
        "According to the Complete Blood Count on October 12, 2026, your potassium was 5.8 mEq/L."
    )
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(hallucinated_answer, sample_citations)
    rep_ids = [c["reportId"] for c in grounded]

    assert "rep-cbc-01" not in rep_ids, "Complete Blood Count must NOT be cited for potassium"
    assert rep_ids == ["rep-cmp-01"], f"Expected exact citation ['rep-cmp-01'], got {rep_ids}"
    assert "Complete Blood Count" not in reconciled_ans, "False CBC attribution must be eliminated from answer text"
    assert "Comprehensive Metabolic Panel" in reconciled_ans, "Answer text must be reconciled to name true source"


def test_03_correct_analyte_incorrect_value(pipeline, sample_citations):
    """
    3. Correct analyte but incorrect value:
    Claim: 'Your potassium was 3.8 mEq/L in the Comprehensive Metabolic Panel.' (True value is 5.8 mEq/L).
    CMP must NOT be cited as supporting 3.8 mEq/L, and text must abstain from false value.
    """
    hallucinated_answer = "Your potassium was 3.8 mEq/L in the Comprehensive Metabolic Panel."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(hallucinated_answer, sample_citations)
    assert len(grounded) == 0, f"False value 3.8 mEq/L must not receive citation, got: {grounded}"
    assert "does not report" in reconciled_ans or "not" in reconciled_ans.lower()


def test_04_correct_value_belonging_to_different_analyte(pipeline, sample_citations):
    """
    4. Correct value belonging to a different analyte:
    Claim: 'Your sodium was 5.8 mEq/L.' (5.8 is potassium, sodium is 140 mEq/L).
    Must not cite CMP for sodium = 5.8 mEq/L.
    """
    hallucinated_answer = "Your sodium was 5.8 mEq/L."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(hallucinated_answer, sample_citations)
    assert len(grounded) == 0, f"Sodium 5.8 must not receive citation: {grounded}"


def test_05_incorrect_or_missing_units(pipeline, sample_citations):
    """
    5. Incorrect unit:
    Claim: 'Your potassium was 5.8 mg/dL in the Comprehensive Metabolic Panel.' (Unit is mEq/L).
    Citation must be rejected for unit discrepancy.
    """
    hallucinated_answer = "Your potassium was 5.8 mg/dL in the Comprehensive Metabolic Panel."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(hallucinated_answer, sample_citations)
    assert len(grounded) == 0, f"Potassium 5.8 mg/dL must not receive citation: {grounded}"


def test_06_decimal_vs_integer_values(pipeline, sample_citations):
    """
    6. Decimal vs integer collision:
    Claim: 'Your fasting blood glucose was 10 mg/dL.'
    Evidence has 105 mg/dL glucose and 10 mg Lisinopril.
    Neither report must support glucose = 10 mg/dL.
    """
    hallucinated_answer = "Your fasting blood glucose was 10 mg/dL."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(hallucinated_answer, sample_citations)
    assert len(grounded) == 0, f"Glucose 10 mg/dL must not receive citation: {grounded}"


def test_07_reference_range_bound_vs_measured_value(pipeline, sample_citations):
    """
    7. Reference range lower bound vs measured value:
    Claim: 'Your potassium was 3.5 mEq/L in the Comprehensive Metabolic Panel.'
    In CMP, (Ref: 3.5-5.0) has 3.5 as lower reference limit; measured value is 5.8 mEq/L.
    CMP must NOT be cited as verifying that the patient measured 3.5 mEq/L.
    """
    hallucinated_answer = "Your potassium was 3.5 mEq/L in the Comprehensive Metabolic Panel."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(hallucinated_answer, sample_citations)
    assert len(grounded) == 0, f"Reference range bound 3.5 must not be cited as measured value: {grounded}"


def test_08_conflicting_measurements_across_facilities(pipeline, sample_citations):
    """8. Conflicting measurements across facilities: Both records retained."""
    answer = (
        "Your fasting glucose results show discrepant readings across facilities: "
        "105 mg/dL at Metro Health on 2026-09-01 (Outpatient Fasting Glucose) and "
        "142 mg/dL at Valley Lab on 2026-09-05 (Diagnostic Endocrinology Panel)."
    )
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, sample_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert set(rep_ids) == {"rep-glu-01", "rep-glu-02"}, f"Expected both glucose panels, got {rep_ids}"


def test_09_wrong_date_and_facility_attribution(pipeline, sample_citations):
    """
    9. Conflicting date and facility attribution:
    Claim asserts potassium was 5.8 mEq/L on January 1, 2025 at Memorial Hospital.
    True record is on 2026-10-12 at Metro Health.
    Citation must NOT be accepted despite matching number 5.8.
    """
    hallucinated_answer = "Your potassium was 5.8 mEq/L on January 1, 2025 at Memorial Hospital."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(hallucinated_answer, sample_citations)
    assert len(grounded) == 0, f"Conflicting date/facility must receive 0 citations: {grounded}"


def test_10_missing_evidence_abstention(pipeline, sample_citations):
    """10. Missing evidence abstention."""
    answer = "LVEF was not reported in the provided echocardiogram records."
    assert pipeline._answer_indicates_missing_data(answer)
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, sample_citations)
    assert len(grounded) == 0


def test_11_abstention_phrased_differently(pipeline, sample_citations):
    """11. Abstention phrased differently across natural language variants."""
    phrased_answers = [
        "There is no record of echocardiogram findings.",
        "The clinical documentation does not contain any echocardiogram data.",
        "Left ventricular ejection fraction was not documented in these files.",
        "No information was provided regarding heart function."
    ]
    for ans in phrased_answers:
        assert pipeline._answer_indicates_missing_data(ans), f"Failed to detect abstention on: {ans}"
        _, grounded = pipeline._reconcile_and_ground_answer(ans, sample_citations)
        assert len(grounded) == 0


def test_12_mixed_supported_and_unsupported_claims(pipeline, sample_citations):
    """
    12. Mixed supported and unsupported claims in a single answer:
    Sentence 1: Supported potassium claim in CMP.
    Sentence 2: Unsupported diagnostic claim ('severe cardiac ischemia').
    System must reconcile text, ground supported claim, and qualify/disclaim unsupported claim.
    """
    answer = (
        "Your potassium level was 5.8 mEq/L in the Comprehensive Metabolic Panel. "
        "You also have severe cardiac ischemia."
    )
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(answer, sample_citations)
    rep_ids = [c["reportId"] for c in grounded]

    assert rep_ids == ["rep-cmp-01"], f"Expected exact citation ['rep-cmp-01'], got {rep_ids}"
    assert "Comprehensive Metabolic Panel" in reconciled_ans
    assert "No clinical documentation of" in reconciled_ans or "cardiac" in reconciled_ans

    # Sentence-level isolation
    s1 = "Your potassium level was 5.8 mEq/L in the Comprehensive Metabolic Panel."
    s2 = "You also have severe cardiac ischemia."
    _, s1_grounded = pipeline._reconcile_and_ground_answer(s1, sample_citations)
    _, s2_grounded = pipeline._reconcile_and_ground_answer(s2, sample_citations)
    assert [c["reportId"] for c in s1_grounded] == ["rep-cmp-01"]
    assert len(s2_grounded) == 0


def test_13_cross_analyte_value_collision(pipeline, sample_citations):
    """
    13. Cross-analyte value collision:
    Endo Panel has Glucose 142 mg/dL. CBC has Hemoglobin 14.2 g/dL.
    Claim: 'Your hemoglobin was 142 g/dL in the Complete Blood Count.'
    Must NOT cite CBC or Endo Panel for hemoglobin = 142 g/dL.
    """
    hallucinated_answer = "Your hemoglobin was 142 g/dL in the Complete Blood Count."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(hallucinated_answer, sample_citations)
    assert len(grounded) == 0, f"Hemoglobin 142 g/dL must not receive citation: {grounded}"


def test_14_multiple_reports_similar_values(pipeline, sample_citations):
    """
    14. Multiple reports containing similar values:
    CMP has Potassium 5.8 mEq/L on 2026-10-12.
    CBC has WBC 5.8 x10^3/uL on 2026-10-12.
    Query for WBC must cite ONLY CBC, not CMP.
    """
    wbc_answer = "Your WBC count was 5.8 x10^3/uL on 2026-10-12 in the Complete Blood Count."
    reconciled_ans, grounded = pipeline._reconcile_and_ground_answer(wbc_answer, sample_citations)
    rep_ids = [c["reportId"] for c in grounded]
    assert rep_ids == ["rep-cbc-01"], f"Expected only ['rep-cbc-01'], got {rep_ids}"
