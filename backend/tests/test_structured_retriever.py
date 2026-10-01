import pytest
from backend.app.ai.rag.structured_retriever import StructuredRetriever, StructuredClinicalResult
from backend.app.models.patient import Patient


def test_structured_retriever_labs(db_session):
    patient = db_session.query(Patient).first()
    assert patient is not None

    retriever = StructuredRetriever(db_session)
    labs = retriever.retrieve_labs(patient_id=patient.id, query_keywords=["cholesterol"])

    assert len(labs) > 0
    assert all(isinstance(r, StructuredClinicalResult) for r in labs)
    assert any("242" in r.content or "198" in r.content for r in labs)
    assert labs[0].source_type == "lab_result"


def test_structured_retriever_medications(db_session):
    patient = db_session.query(Patient).first()
    retriever = StructuredRetriever(db_session)
    meds = retriever.retrieve_medications(patient_id=patient.id, query_keywords=["metformin"])

    assert len(meds) > 0
    assert any("500mg" in m.content for m in meds)
    assert meds[0].source_type == "medication"


def test_structured_retriever_diagnoses_and_timeline(db_session):
    patient = db_session.query(Patient).first()
    retriever = StructuredRetriever(db_session)

    diagnoses = retriever.retrieve_diagnoses(patient_id=patient.id)
    assert len(diagnoses) >= 3
    assert any("Diabetes" in d.title for d in diagnoses)

    timeline = retriever.retrieve_timeline(patient_id=patient.id)
    assert len(timeline) >= 5
    assert timeline[0].source_type == "timeline_event"
