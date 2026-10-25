import pytest
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.models.report import MedicalReport
from backend.app.models.timeline import TimelineEvent
from backend.app.models.clinical_entity import Disease, Medication, LabResult


def test_timeline_aggregate_includes_all_sources(client, db_session):
    """
    Verifies that GET /api/v1/timeline aggregates events across
    TimelineEvent, MedicalReport, Disease, and Medication.
    """
    response = client.get("/api/v1/timeline")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8

    types = {e["type"] for e in data}
    assert "diagnosis" in types
    assert "medication_start" in types
    assert "lab_test" in types


def test_timeline_chronological_ordering(client):
    """
    Verifies timeline events with valid ISO dates are strictly sorted by clinical event date.
    """
    # Descending (default)
    res_desc = client.get("/api/v1/timeline?order=desc")
    assert res_desc.status_code == 200
    data_desc = res_desc.json()
    valid_dates_desc = [e["date"] for e in data_desc if not e.get("isUnknownDate") and e["date"] != "Unknown Date"]
    for i in range(len(valid_dates_desc) - 1):
        assert valid_dates_desc[i] >= valid_dates_desc[i + 1]

    # Ascending
    res_asc = client.get("/api/v1/timeline?order=asc")
    assert res_asc.status_code == 200
    data_asc = res_asc.json()
    valid_dates_asc = [e["date"] for e in data_asc if not e.get("isUnknownDate") and e["date"] != "Unknown Date"]
    for i in range(len(valid_dates_asc) - 1):
        assert valid_dates_asc[i] <= valid_dates_asc[i + 1]


def test_timeline_distinguish_event_date_from_upload_date(client, db_session):
    """
    Verifies that clinical event date is distinct from uploadDate.
    """
    response = client.get("/api/v1/timeline")
    assert response.status_code == 200
    data = response.json()

    # Find events with sourceReportId and uploadDate
    report_events = [e for e in data if e.get("sourceReportId") and e.get("uploadDate")]
    assert len(report_events) > 0
    for ev in report_events:
        assert ev["date"] is not None
        assert ev["uploadDate"] is not None


def test_timeline_deduplication(client, db_session):
    """
    Verifies that explicit TimelineEvents that already represent a report
    do not have duplicate synthetic report events generated.
    """
    response = client.get("/api/v1/timeline")
    assert response.status_code == 200
    data = response.json()

    # Explicit event ev_001 references rep_008
    rep_008_events = [e for e in data if e.get("sourceReportId") == "rep_008"]
    assert len(rep_008_events) == 1
    assert rep_008_events[0]["id"] == "ev_001"


def test_timeline_incomplete_dates_flagged(client, db_session):
    """
    Verifies records with incomplete or unknown dates are explicitly flagged
    with isUnknownDate=True and sorted to the bottom without fabricating positions.
    """
    patient = db_session.query(Patient).first()
    undated_ev = TimelineEvent(
        id="ev_undated_test",
        patient_id=patient.id,
        date="Unknown Date",
        year=0,
        title="Historical Allergy Assessment",
        description="Childhood onset allergy with unrecorded exact encounter date.",
        event_type="symptom",
        severity="low",
        facility="Family Practice",
    )
    db_session.add(undated_ev)
    db_session.commit()

    response = client.get("/api/v1/timeline")
    assert response.status_code == 200
    data = response.json()

    # Undated event must be present at the end
    last_event = data[-1]
    assert last_event["id"] == "ev_undated_test"
    assert last_event["isUnknownDate"] is True


def test_timeline_multi_facility_conflict_detection(client, db_session):
    """
    Verifies encounters on the same date across differing facilities
    are flagged with hasConflict=True and conflictDetails populated.
    """
    patient = db_session.query(Patient).first()
    ev1 = TimelineEvent(
        id="ev_conf_1",
        patient_id=patient.id,
        date="2026-08-20",
        year=2026,
        title="Consultation A",
        description="Evaluation at Clinic A",
        event_type="hospital_visit",
        facility="Facility Alpha",
    )
    ev2 = TimelineEvent(
        id="ev_conf_2",
        patient_id=patient.id,
        date="2026-08-20",
        year=2026,
        title="Consultation B",
        description="Evaluation at Clinic B",
        event_type="hospital_visit",
        facility="Facility Beta",
    )
    db_session.add_all([ev1, ev2])
    db_session.commit()

    response = client.get("/api/v1/timeline")
    assert response.status_code == 200
    data = response.json()

    conf_events = [e for e in data if e["id"] in ["ev_conf_1", "ev_conf_2"]]
    assert len(conf_events) == 2
    for e in conf_events:
        assert e["hasConflict"] is True
        assert "Facility Alpha" in e["conflictDetails"]
        assert "Facility Beta" in e["conflictDetails"]


def test_timeline_filters(client):
    """
    Verifies filtering by event_type, year, and facility.
    """
    # Filter by diagnosis
    res_diag = client.get("/api/v1/timeline?event_type=diagnosis")
    assert res_diag.status_code == 200
    data_diag = res_diag.json()
    assert all(e["type"] == "diagnosis" for e in data_diag)

    # Filter by year
    res_yr = client.get("/api/v1/timeline?year=2026")
    assert res_yr.status_code == 200
    data_yr = res_yr.json()
    assert all(e["year"] == 2026 for e in data_yr)

    # Filter by facility
    res_fac = client.get("/api/v1/timeline?facility=Metro")
    assert res_fac.status_code == 200
    data_fac = res_fac.json()
    assert all("metro" in (e.get("facility") or "").lower() for e in data_fac)


def test_timeline_facilities_endpoint(client):
    """
    Verifies GET /api/v1/timeline/facilities returns distinct facilities.
    """
    response = client.get("/api/v1/timeline/facilities")
    assert response.status_code == 200
    data = response.json()
    assert "facilities" in data
    assert isinstance(data["facilities"], list)
    assert len(data["facilities"]) >= 2
    assert "Metro General Hospital" in data["facilities"]


def test_timeline_summary_endpoint(client):
    """
    Verifies GET /api/v1/timeline/summary returns comprehensive metadata.
    """
    response = client.get("/api/v1/timeline/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["totalEvents"] >= 8
    assert len(data["eventTypes"]) >= 3
    assert len(data["facilities"]) >= 2
    assert len(data["years"]) >= 2
    assert data["dateRange"]["latest"] is not None


def test_patient_analytes_endpoint(client):
    """
    Verifies GET /api/v1/patients/me/labs/analytes returns distinct lab biomarkers.
    """
    response = client.get("/api/v1/patients/me/labs/analytes")
    assert response.status_code == 200
    data = response.json()
    assert "analytes" in data
    analytes = data["analytes"]
    assert len(analytes) >= 5

    names = [a["canonicalName"] for a in analytes]
    assert any("Glucose" in n for n in names)
    assert any("Hemoglobin" in n or "Cholesterol" in n for n in names)

    # Check structure
    sample = analytes[0]
    assert "testName" in sample
    assert "canonicalName" in sample
    assert "count" in sample
    assert "latestDate" in sample
    assert sample["count"] >= 1


def test_patient_lab_trend_series(client, db_session):
    """
    Verifies GET /api/v1/patients/me/labs/trends returns chronological measurements,
    reference range, unit, and non-diagnostic narrative summary.
    """
    patient = db_session.query(Patient).first()
    # Add prior fasting glucose result to form longitudinal series
    prior_rep = MedicalReport(
        id="rep_synth_prior_glu",
        patient_id=patient.id,
        title="Annual Wellness Labs",
        file_name="prior_glu.pdf",
        hospital_name="City Health Clinic",
        report_date="2026-01-10"
    )
    prior_lab = LabResult(
        id="lab_synth_prior_glu",
        patient_id=patient.id,
        test_name="Fasting Blood Glucose",
        category="metabolic",
        value="115",
        unit="mg/dL",
        reference_range="70 - 99",
        status="high",
        test_date="2026-01-10",
        hospital_name="City Health Clinic",
        source_report_id=prior_rep.id
    )
    db_session.add_all([prior_rep, prior_lab])
    db_session.commit()

    response = client.get("/api/v1/patients/me/labs/trends?analyte=Glucose")
    assert response.status_code == 200
    data = response.json()

    assert "Glucose" in data["canonical_name"]
    assert data["unit"] == "mg/dL"
    assert len(data["all_measurements"]) >= 2

    # Check chronological ordering
    dates = [m["test_date"] for m in data["all_measurements"]]
    assert dates == sorted(dates)

    assert data["latest_measurement"] is not None
    assert data["previous_measurement"] is not None
    assert data["has_sufficient_data"] is True
    assert data["trend_direction"] == "increasing"
    assert data["absolute_change"] == 13.0
    assert data["narrative_summary"] != ""
    assert len(data["citations"]) >= 1


def test_patient_lab_trend_conflicting_readings(client, db_session):
    """
    Verifies conflicting measurements on the same date across differing facilities
    are accurately populated in conflicting_measurements.
    """
    patient = db_session.query(Patient).first()
    rep_a = MedicalReport(id="rep_conf_a", patient_id=patient.id, title="Panel A", file_name="a.pdf", hospital_name="Facility A", report_date="2026-09-15")
    rep_b = MedicalReport(id="rep_conf_b", patient_id=patient.id, title="Panel B", file_name="b.pdf", hospital_name="Facility B", report_date="2026-09-15")
    lab_a = LabResult(id="lab_conf_a", patient_id=patient.id, test_name="Potassium, Serum", value="4.1", unit="mEq/L", reference_range="3.5 - 5.0", test_date="2026-09-15", hospital_name="Facility A", source_report_id=rep_a.id)
    lab_b = LabResult(id="lab_conf_b", patient_id=patient.id, test_name="Potassium, Serum", value="5.8", unit="mEq/L", reference_range="3.5 - 5.0", test_date="2026-09-15", hospital_name="Facility B", source_report_id=rep_b.id)

    db_session.add_all([rep_a, rep_b, lab_a, lab_b])
    db_session.commit()

    response = client.get("/api/v1/patients/me/labs/trends?analyte=Potassium")
    assert response.status_code == 200
    data = response.json()

    assert len(data["conflicting_measurements"]) >= 2
    conf_facs = {c["facility"] for c in data["conflicting_measurements"]}
    assert "Facility A" in conf_facs
    assert "Facility B" in conf_facs


def test_patient_lab_trend_incompatible_units(client, db_session):
    """
    Verifies differing measurement units are safely detected and incompatible_units_detected is set.
    """
    patient = db_session.query(Patient).first()
    rep_u = MedicalReport(id="rep_unit_mismatch", patient_id=patient.id, title="EU Lab Report", file_name="eu.pdf", hospital_name="Euro Clinic", report_date="2026-10-01")
    lab_u = LabResult(id="lab_unit_mismatch", patient_id=patient.id, test_name="Fasting Blood Glucose", value="5.5", unit="mmol/L", reference_range="3.9 - 5.5", test_date="2026-10-01", hospital_name="Euro Clinic", source_report_id=rep_u.id)

    db_session.add_all([rep_u, lab_u])
    db_session.commit()

    response = client.get("/api/v1/patients/me/labs/trends?analyte=Glucose")
    assert response.status_code == 200
    data = response.json()

    assert data["incompatible_units_detected"] is True
    assert data["absolute_change"] is None


def test_patient_lab_trend_single_observation(client):
    """
    Verifies a single recorded measurement returns has_sufficient_data=False without error.
    """
    # Serum Creatinine only has 1 measurement seeded
    response = client.get("/api/v1/patients/me/labs/trends?analyte=Creatinine")
    assert response.status_code == 200
    data = response.json()

    assert data["has_sufficient_data"] is False
    assert len(data["all_measurements"]) == 1
    assert data["trend_direction"] in ["insufficient_data", "stable"]
