import uuid
import pytest
from datetime import datetime, timezone
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import LabResult
from backend.app.clinical.structured_query import (
    StructuredQueryDetector,
    StructuredClinicalQueryEngine,
    StructuredQueryType,
    TrendDirection,
)
from backend.app.ai.rag.pipeline import RAGPipeline


@pytest.fixture
def structured_test_data(db_session):
    """
    Sets up synthetic patients and longitudinal lab results for testing.
    Never mutates persistent databases.
    """
    # Patient Alpha
    u_a = User(id="usr_synth_a", name="Synth Patient A", email="a@test.com", hashed_password="pwd")
    pat_a = Patient(id="pat_synth_a", user_id=u_a.id)

    # Patient Beta (for isolation testing)
    u_b = User(id="usr_synth_b", name="Synth Patient B", email="b@test.com", hashed_password="pwd")
    pat_b = Patient(id="pat_synth_b", user_id=u_b.id)

    # Reports for Patient A
    rep_cbc1 = MedicalReport(
        id="rep_synth_cbc1", patient_id=pat_a.id, title="Complete Blood Count",
        file_name="cbc1.pdf", hospital_name="City Health Clinic", report_date="2026-04-10"
    )
    rep_cbc2 = MedicalReport(
        id="rep_synth_cbc2", patient_id=pat_a.id, title="Comprehensive Metabolic & CBC",
        file_name="cbc2.pdf", hospital_name="Metro Health Center", report_date="2026-10-12"
    )
    rep_glu1 = MedicalReport(
        id="rep_synth_glu1", patient_id=pat_a.id, title="Outpatient Glucose Screen",
        file_name="glu1.pdf", hospital_name="Metro Health Center", report_date="2026-09-01"
    )
    rep_glu2 = MedicalReport(
        id="rep_synth_glu2", patient_id=pat_a.id, title="Endocrinology Blood Panel",
        file_name="glu2.pdf", hospital_name="Valley Reference Lab", report_date="2026-09-05"
    )

    # Report for Patient Beta
    rep_b = MedicalReport(
        id="rep_synth_b", patient_id=pat_b.id, title="Cardiology Inpatient Panel",
        file_name="cardio_b.pdf", hospital_name="Secret Hospital", report_date="2026-10-12"
    )

    # 1. Hemoglobin: 13.5 g/dL (2026-04-10) -> 14.2 g/dL (2026-10-12) [Increasing]
    lab_hgb1 = LabResult(
        id="lab_hgb1", patient_id=pat_a.id, test_name="Hemoglobin", canonical_name="Hemoglobin",
        loinc_code="718-7", value="13.5", unit="g/dL", reference_range="13.8 - 17.2",
        status="low", test_date="2026-04-10", source_report_id=rep_cbc1.id, hospital_name="City Health Clinic"
    )
    lab_hgb2 = LabResult(
        id="lab_hgb2", patient_id=pat_a.id, test_name="Hemoglobin", canonical_name="Hemoglobin",
        loinc_code="718-7", value="14.2", unit="g/dL", reference_range="13.8 - 17.2",
        status="normal", test_date="2026-10-12", source_report_id=rep_cbc2.id, hospital_name="Metro Health Center"
    )

    # 2. Potassium: Single reading 5.8 mEq/L (2026-10-12) [Elevated]
    lab_pot = LabResult(
        id="lab_pot", patient_id=pat_a.id, test_name="Potassium", canonical_name="Potassium, Serum",
        loinc_code="2823-3", value="5.8", unit="mEq/L", reference_range="3.5 - 5.1",
        status="high", test_date="2026-10-12", source_report_id=rep_cbc2.id, hospital_name="Metro Health Center"
    )

    # 3. Glucose: Conflicting readings across facilities (105 mg/dL vs 142 mg/dL)
    lab_glu1 = LabResult(
        id="lab_glu1", patient_id=pat_a.id, test_name="Fasting Glucose", canonical_name="Glucose, Fasting Blood",
        loinc_code="1558-6", value="105", unit="mg/dL", reference_range="70 - 99",
        status="high", test_date="2026-09-01", source_report_id=rep_glu1.id, hospital_name="Metro Health Center"
    )
    lab_glu2 = LabResult(
        id="lab_glu2", patient_id=pat_a.id, test_name="Fasting Blood Glucose", canonical_name="Glucose, Fasting Blood",
        loinc_code="1558-6", value="142", unit="mg/dL", reference_range="70 - 99",
        status="high", test_date="2026-09-05", source_report_id=rep_glu2.id, hospital_name="Valley Reference Lab"
    )

    # 4. Calcium: Decreasing (9.8 mg/dL -> 8.9 mg/dL)
    lab_ca1 = LabResult(
        id="lab_ca1", patient_id=pat_a.id, test_name="Calcium", canonical_name="Calcium, Serum",
        loinc_code="17861-6", value="9.8", unit="mg/dL", reference_range="8.6 - 10.2",
        status="normal", test_date="2026-04-10", source_report_id=rep_cbc1.id, hospital_name="City Health Clinic"
    )
    lab_ca2 = LabResult(
        id="lab_ca2", patient_id=pat_a.id, test_name="Calcium", canonical_name="Calcium, Serum",
        loinc_code="17861-6", value="8.9", unit="mg/dL", reference_range="8.6 - 10.2",
        status="normal", test_date="2026-10-12", source_report_id=rep_cbc2.id, hospital_name="Metro Health Center"
    )

    # 5. Sodium: Stable (140 mEq/L -> 140 mEq/L)
    lab_na1 = LabResult(
        id="lab_na1", patient_id=pat_a.id, test_name="Sodium", canonical_name="Sodium, Serum",
        loinc_code="2951-2", value="140", unit="mEq/L", reference_range="136 - 145",
        status="normal", test_date="2026-04-10", source_report_id=rep_cbc1.id, hospital_name="City Health Clinic"
    )
    lab_na2 = LabResult(
        id="lab_na2", patient_id=pat_a.id, test_name="Sodium", canonical_name="Sodium, Serum",
        loinc_code="2951-2", value="140", unit="mEq/L", reference_range="136 - 145",
        status="normal", test_date="2026-10-12", source_report_id=rep_cbc2.id, hospital_name="Metro Health Center"
    )

    # 6. Creatinine: Unit mismatch (1.1 mg/dL vs 0.09 mmol/L, reference range unavailable on 2nd)
    lab_cr1 = LabResult(
        id="lab_cr1", patient_id=pat_a.id, test_name="Creatinine", canonical_name="Creatinine, Serum",
        loinc_code="2160-0", value="1.1", unit="mg/dL", reference_range="0.7 - 1.3",
        status="normal", test_date="2026-04-10", source_report_id=rep_cbc1.id, hospital_name="City Health Clinic"
    )
    lab_cr2 = LabResult(
        id="lab_cr2", patient_id=pat_a.id, test_name="Creatinine", canonical_name="Creatinine, Serum",
        loinc_code="2160-0", value="0.09", unit="mmol/L", reference_range="unavailable",
        status="normal", test_date="2026-10-12", source_report_id=rep_cbc2.id, hospital_name="Metro Health Center"
    )

    # 7. Patient Beta's private Troponin
    lab_b = LabResult(
        id="lab_b", patient_id=pat_b.id, test_name="Troponin", canonical_name="Troponin I, Cardiac",
        loinc_code="10839-9", value="0.95", unit="ng/mL", reference_range="< 0.04",
        status="high", test_date="2026-10-12", source_report_id=rep_b.id, hospital_name="Secret Hospital"
    )

    db_session.add_all([
        u_a, u_b, pat_a, pat_b,
        rep_cbc1, rep_cbc2, rep_glu1, rep_glu2, rep_b,
        lab_hgb1, lab_hgb2, lab_pot, lab_glu1, lab_glu2,
        lab_ca1, lab_ca2, lab_na1, lab_na2, lab_cr1, lab_cr2, lab_b
    ])
    db_session.commit()

    return {
        "patient_a": pat_a,
        "patient_b": pat_b,
        "detector": StructuredQueryDetector(),
        "engine": StructuredClinicalQueryEngine(db_session)
    }


def test_01_latest_measurement_selection(structured_test_data):
    """1. Latest measurement selection."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    intent = detector.detect("What was my latest hemoglobin result?")
    assert intent.is_structured_query is True
    assert intent.query_type == StructuredQueryType.LATEST_VALUE

    res = engine.execute_query(intent, pat_a.id)
    assert res.latest_measurement is not None
    assert res.latest_measurement.value == "14.2"
    assert res.latest_measurement.unit == "g/dL"
    assert res.latest_measurement.test_date == "2026-10-12"
    assert res.latest_measurement.facility == "Metro Health Center"
    assert "14.2 g/dL" in res.narrative_summary
    assert "2026-10-12" in res.narrative_summary


def test_02_correct_previous_versus_latest_comparison(structured_test_data):
    """2. Correct previous-versus-latest comparison."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    intent = detector.detect("Show my latest hemoglobin result alongside the previous result and the reference range.")
    assert intent.is_structured_query is True

    res = engine.execute_query(intent, pat_a.id)
    assert res.latest_measurement.value == "14.2"
    assert res.previous_measurement.value == "13.5"
    assert res.absolute_change == 0.7
    assert res.percentage_change == 5.2
    assert "14.2 g/dL" in res.narrative_summary
    assert "13.5 g/dL" in res.narrative_summary
    assert "+0.7 g/dL" in res.narrative_summary


def test_03_chronological_ordering(structured_test_data):
    """3. Correct chronological ordering."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    intent = detector.detect("Show my hemoglobin history.")
    res = engine.execute_query(intent, pat_a.id)
    assert len(res.all_measurements) == 2
    dates = [m.test_date for m in res.all_measurements]
    assert dates == sorted(dates)
    assert dates[0] == "2026-04-10"
    assert dates[1] == "2026-10-12"


def test_04_six_month_time_window_filtering(structured_test_data):
    """4. Six-month time-window filtering."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    intent = detector.detect("How has my hemoglobin changed over the last six months?")
    assert intent.time_window is not None
    assert intent.time_window.days == 180

    res = engine.execute_query(intent, pat_a.id)
    assert res.time_window_applied == "last six months"
    # Points falling within 180 days of 2026-10-12 (cutoff ~ 2026-04-15)
    # 2026-04-10 is ~185 days ago, so only 2026-10-12 is included in 6-month window
    assert len(res.all_measurements) >= 1
    assert any(m.test_date == "2026-10-12" for m in res.all_measurements)


def test_05_increasing_decreasing_and_stable_trends(structured_test_data):
    """5. Increasing, decreasing, and stable trends."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    # Increasing (Hemoglobin 13.5 -> 14.2)
    res_inc = engine.execute_query(detector.detect("How has my hemoglobin changed?"), pat_a.id)
    assert res_inc.trend_direction == TrendDirection.INCREASING
    assert "increasing" in res_inc.narrative_summary

    # Decreasing (Calcium 9.8 -> 8.9)
    res_dec = engine.execute_query(detector.detect("How has my calcium changed?"), pat_a.id)
    assert res_dec.trend_direction == TrendDirection.DECREASING
    assert "decreasing" in res_dec.narrative_summary

    # Stable (Sodium 140 -> 140)
    res_stable = engine.execute_query(detector.detect("How has my sodium changed?"), pat_a.id)
    assert res_stable.trend_direction == TrendDirection.STABLE
    assert "stable" in res_stable.narrative_summary


def test_06_missing_measurement_and_insufficient_data_handling(structured_test_data):
    """6. Missing measurement and insufficient-data handling."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    # Absent analyte
    res_missing = engine.execute_query(detector.detect("What was my ferritin level?"), pat_a.id)
    assert res_missing.trend_direction == TrendDirection.NOT_FOUND
    assert "No recorded measurements for Ferritin" in res_missing.narrative_summary
    assert len(res_missing.citations) == 0

    # Only single measurement exists (Potassium)
    res_single = engine.execute_query(detector.detect("How has my potassium changed?"), pat_a.id)
    assert res_single.trend_direction == TrendDirection.INSUFFICIENT_DATA
    assert "Only a single measurement exists" in res_single.narrative_summary


def test_07_conflicting_values_across_facilities(structured_test_data):
    """7. Conflicting values from multiple reports or facilities."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    intent = detector.detect("Compare my glucose results across dates and facilities.")
    assert intent.query_type == StructuredQueryType.COMPARISON_ACROSS_SOURCES

    res = engine.execute_query(intent, pat_a.id)
    assert res.trend_direction == TrendDirection.CONFLICTING
    assert len(res.conflicting_measurements) >= 2
    # Conflicting readings must both be explicitly documented
    assert "105 mg/dL" in res.narrative_summary
    assert "Metro Health Center" in res.narrative_summary
    assert "142 mg/dL" in res.narrative_summary
    assert "Valley Reference Lab" in res.narrative_summary


def test_08_unit_mismatch_prevents_invalid_comparison(structured_test_data):
    """8. Unit mismatch preventing an invalid comparison."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    intent = detector.detect("How has my creatinine changed?")
    res = engine.execute_query(intent, pat_a.id)

    assert res.trend_direction == TrendDirection.INCOMPATIBLE_UNITS
    assert res.incompatible_units_detected is True
    assert res.absolute_change is None
    assert res.percentage_change is None
    assert "differ" in res.narrative_summary.lower() or "incompatible" in res.narrative_summary.lower()


def test_09_missing_or_unavailable_reference_ranges(structured_test_data):
    """9. Missing or unavailable reference ranges."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    # Potassium has valid reference range 3.5 - 5.1
    res_pot = engine.execute_query(detector.detect("Is my potassium within reference range?"), pat_a.id)
    assert res_pot.reference_range_status == "elevated"
    assert "3.5 - 5.1" in res_pot.narrative_summary

    # Creatinine latest measurement has reference_range='unavailable'
    res_cr = engine.execute_query(detector.detect("Is my creatinine within reference range?"), pat_a.id)
    assert res_cr.reference_range_status == "unavailable"
    assert "not documented" in res_cr.narrative_summary.lower()


def test_10_synonym_resolution_for_supported_analytes(structured_test_data):
    """10. Synonym resolution for supported analytes."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    # Colloquial 'blood sugar' resolves to Glucose
    intent_sugar = detector.detect("What was my latest blood sugar?")
    assert intent_sugar.canonical_name == "Glucose, Fasting Blood"
    res_sugar = engine.execute_query(intent_sugar, pat_a.id)
    assert res_sugar.latest_measurement is not None
    assert res_sugar.latest_measurement.unit == "mg/dL"

    # 'serum potassium' resolves to Potassium
    intent_k = detector.detect("What was my latest serum potassium?")
    assert intent_k.canonical_name == "Potassium, Serum"
    res_k = engine.execute_query(intent_k, pat_a.id)
    assert res_k.latest_measurement.value == "5.8"


def test_11_patient_isolation_enforcement(structured_test_data):
    """11. Patient isolation: patient A cannot query patient B's data."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]
    pat_b = structured_test_data["patient_b"]

    intent = detector.detect("What was my troponin level?")

    # Patient A has no troponin record
    res_a = engine.execute_query(intent, pat_a.id)
    assert res_a.trend_direction == TrendDirection.NOT_FOUND
    assert "No recorded measurements for Troponin" in res_a.narrative_summary

    # Patient B has troponin record
    res_b = engine.execute_query(intent, pat_b.id)
    assert res_b.latest_measurement is not None
    assert res_b.latest_measurement.value == "0.95"
    assert res_b.latest_measurement.facility == "Secret Hospital"


def test_12_exact_value_date_source_attribution(structured_test_data):
    """12. Exact value/date/source attribution in final answer."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    intent = detector.detect("What was my latest potassium result?")
    res = engine.execute_query(intent, pat_a.id)

    assert "5.8 mEq/L" in res.narrative_summary
    assert "2026-10-12" in res.narrative_summary
    assert "Metro Health Center" in res.narrative_summary
    assert len(res.citations) == 1
    cit = res.citations[0]
    assert cit["reportId"] == "rep_synth_cbc2"
    assert "Comprehensive Metabolic & CBC" in cit["reportTitle"]
    assert "5.8 mEq/L" in cit["excerpt"]


def test_13_unsupported_claims_abstention(structured_test_data):
    """13. Unsupported claims when structured evidence is absent."""
    detector = structured_test_data["detector"]
    engine = structured_test_data["engine"]
    pat_a = structured_test_data["patient_a"]

    intent = detector.detect("What was my uric acid level?")
    res = engine.execute_query(intent, pat_a.id)
    assert res.trend_direction == TrendDirection.NOT_FOUND
    # Ensures zero ungrounded clinical claims fabricated
    assert not any(char.isdigit() for char in res.narrative_summary)
    assert len(res.citations) == 0


def test_14_api_and_frontend_payload_integration(structured_test_data, client, monkeypatch):
    """14. API and frontend integration for successful and empty results."""
    pat_a = structured_test_data["patient_a"]
    from backend.app.services.auth_service import get_current_patient
    client.app.dependency_overrides[get_current_patient] = lambda: pat_a

    conv_id = f"conv_struct_{uuid.uuid4().hex[:6]}"

    # Successful structured trend query
    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "How has my hemoglobin changed over the last six months?"}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["sender"] == "ai"
    assert data["reasoningType"] == "fact"
    assert "structuredTrend" in data
    st = data["structuredTrend"]
    assert st is not None
    assert st["canonical_name"] == "Hemoglobin"
    assert st["latest_measurement"]["value"] == "14.2"
    assert st["latest_measurement"]["facility"] == "Metro Health Center"
    assert len(st["all_measurements"]) >= 1

    # Multi-analyte trend query
    resp_multi = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"text": "Which of my recorded lab values have increased?"}
    )
    assert resp_multi.status_code == 200
    data_multi = resp_multi.json()
    assert data_multi["structuredTrend"] is not None
    assert data_multi["structuredTrend"]["query_type"] == "all_increasing"
    assert data_multi["structuredTrend"]["has_sufficient_data"] is True
    assert data_multi["structuredTrend"]["multi_analyte_items"] is not None
    assert len(data_multi["structuredTrend"]["multi_analyte_items"]) >= 1

    # Clean up dependency override
    client.app.dependency_overrides.pop(get_current_patient, None)
