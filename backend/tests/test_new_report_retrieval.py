import pytest
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.models.clinical_entity import LabResult
from backend.app.models.report import MedicalReport
from backend.app.models.document_chunk import DocumentChunkModel
from backend.app.ai.retrieval import PostgresVectorStore
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider


def test_newly_uploaded_report_retrieved_as_top_priority(db_session):
    """
    Test Priority 1: When a new relevant medical report is ingested,
    queries for latest status or general queries must prioritize the newly uploaded report
    over older historical records, while correctly updating citations.
    """
    patient = db_session.query(Patient).first()
    assert patient is not None, "Patient profile must exist in test database"

    # 1. Ensure baseline 2021 lab exists for Alex Vance so we test multi-encounter trajectory
    baseline_2021 = db_session.query(LabResult).filter(
        LabResult.patient_id == patient.id,
        LabResult.source_report_id == "rep_002"
    ).first()
    if not baseline_2021:
        baseline_2021 = LabResult(
            id="lab_baseline_2021_chol",
            patient_id=patient.id,
            test_name="Total Cholesterol",
            category="lipid_panel",
            value="242",
            unit="mg/dL",
            reference_range="<200",
            status="high",
            test_date="2021-06-12",
            source_report_id="rep_002",
            hospital_name="Quest Diagnostics"
        )
        db_session.add(baseline_2021)
        db_session.commit()

    # 2. Ingest synthetic newly uploaded report dated 2026-10-10
    new_report = MedicalReport(
        id="rep_synthetic_oct_2026",
        patient_id=patient.id,
        title="Follow-Up Comprehensive Lipid Panel",
        file_name="lipid_panel_oct_2026.pdf",
        file_size=20480,
        file_type="application/pdf",
        category="blood_report",
        hospital_name="St. Jude Advanced Diagnostics",
        report_date="2026-10-10",
        confidence_score=0.99,
        status="completed",
        summary="Routine follow-up lipid profile showing optimal response to statin therapy.",
        raw_text="Comprehensive Lipid Profile: Total Cholesterol: 168 mg/dL (Normal). HDL: 54 mg/dL. LDL: 94 mg/dL. Triglycerides: 120 mg/dL."
    )
    db_session.add(new_report)

    new_lab = LabResult(
        id="lab_synthetic_oct_2026",
        patient_id=patient.id,
        test_name="Total Cholesterol",
        value="168",
        unit="mg/dL",
        reference_range="<200",
        status="normal",
        test_date="2026-10-10",
        source_report_id="rep_synthetic_oct_2026",
        hospital_name="St. Jude Advanced Diagnostics"
    )
    db_session.add(new_lab)

    # Also add vector chunk to simulate document chunk indexing
    vector_store = PostgresVectorStore(db_session=db_session)
    new_chunk = DocumentChunkModel(
        document_id="rep_synthetic_oct_2026",
        patient_id=patient.id,
        chunk_id="chk_synthetic_oct_2026",
        chunk_index=0,
        page_number=1,
        content="St. Jude Advanced Diagnostics: Total Cholesterol: 168 mg/dL on October 10, 2026. Statin therapy effective.",
        embedding=[0.05] * 384,
        chunk_metadata={
            "patient_id": patient.id,
            "title": "Follow-Up Comprehensive Lipid Panel",
            "date": "2026-10-10",
            "hospital_name": "St. Jude Advanced Diagnostics"
        }
    )
    db_session.add(new_chunk)
    db_session.commit()

    # 3. Query through Hybrid RAG pipeline
    hybrid_retriever = HybridRetriever(vector_store=vector_store, db_session=db_session)
    pipeline = RAGPipeline(
        retriever=hybrid_retriever,
        llm=MockDeterministicLLMProvider(),
        db_session=db_session
    )

    response = pipeline.query("What is my latest cholesterol level?", patient_id=patient.id)

    # 4. Verify the newly uploaded report is retrieved as the #1 priority citation
    assert response.sources_used > 0
    assert len(response.citations) > 0
    top_citation = response.citations[0]
    assert top_citation["reportId"] == "rep_synthetic_oct_2026", f"Expected rep_synthetic_oct_2026 at top citation, got {top_citation['reportId']}"
    assert top_citation["date"] == "2026-10-10"
    assert "168" in response.answer or "168" in top_citation["excerpt"]


def test_extremum_query_preserves_clinical_relevance_over_recency(db_session):
    """
    Test that asking for an extremum (e.g. 'highest cholesterol') correctly returns
    the highest clinical reading (242 mg/dL from 2021) and does NOT blindly favor
    recency over medical query relevance.
    """
    patient = db_session.query(Patient).first()
    assert patient is not None

    vector_store = PostgresVectorStore(db_session=db_session)
    hybrid_retriever = HybridRetriever(vector_store=vector_store, db_session=db_session)
    pipeline = RAGPipeline(
        retriever=hybrid_retriever,
        llm=MockDeterministicLLMProvider(),
        db_session=db_session
    )

    response = pipeline.query("When was my highest recorded cholesterol reading?", patient_id=patient.id)

    assert response.sources_used > 0
    assert len(response.citations) > 0
    # The 2021 report (rep_002 with 242 mg/dL) must be cited for the peak value
    citation_ids = [c["reportId"] for c in response.citations]
    assert "rep_002" in citation_ids, "Highest query must include rep_002 (2021 peak of 242 mg/dL)"
    assert "242 mg/dL" in response.answer


def test_patient_isolation_on_uploaded_reports(db_session):
    """
    Test strict patient data isolation: a report uploaded by Patient B must never
    be retrieved, cited, or leaked in queries executed by Patient A.
    """
    patient_a = db_session.query(Patient).filter(Patient.id == "pat_alex_vance_001").first()
    if not patient_a:
        patient_a = db_session.query(Patient).first()

    # Create Patient B
    user_b = User(
        id="usr_patient_b_isolated",
        email="patient_b_isolated@example.com",
        hashed_password="pw",
        name="Isolated Patient B"
    )
    db_session.add(user_b)
    patient_b = Patient(
        id="pat_patient_b_isolated",
        user_id=user_b.id,
        blood_group="B+"
    )
    db_session.add(patient_b)

    # Ingest report strictly belonging to Patient B
    report_b = MedicalReport(
        id="rep_patient_b_secret",
        patient_id=patient_b.id,
        title="Patient B Confidential Metabolic Panel",
        file_name="patient_b_panel.pdf",
        file_size=12000,
        file_type="application/pdf",
        category="blood_report",
        hospital_name="Private Clinic B",
        report_date="2026-10-14",
        status="completed"
    )
    db_session.add(report_b)

    lab_b = LabResult(
        id="lab_patient_b_secret",
        patient_id=patient_b.id,
        test_name="Total Cholesterol",
        value="135",
        unit="mg/dL",
        reference_range="<200",
        status="normal",
        test_date="2026-10-14",
        source_report_id="rep_patient_b_secret",
        hospital_name="Private Clinic B"
    )
    db_session.add(lab_b)

    chunk_b = DocumentChunkModel(
        document_id="rep_patient_b_secret",
        patient_id=patient_b.id,
        chunk_id="chk_patient_b_secret",
        chunk_index=0,
        page_number=1,
        content="Private Clinic B: Patient B Total Cholesterol 135 mg/dL on October 14, 2026.",
        embedding=[0.05] * 384,
        chunk_metadata={
            "patient_id": patient_b.id,
            "title": "Patient B Confidential Metabolic Panel",
            "date": "2026-10-14"
        }
    )
    db_session.add(chunk_b)
    db_session.commit()

    # Query as Patient A
    vector_store = PostgresVectorStore(db_session=db_session)
    hybrid_retriever = HybridRetriever(vector_store=vector_store, db_session=db_session)
    pipeline = RAGPipeline(
        retriever=hybrid_retriever,
        llm=MockDeterministicLLMProvider(),
        db_session=db_session
    )

    response_a = pipeline.query("What is my latest cholesterol level?", patient_id=patient_a.id)

    # Patient A must NEVER see Patient B's report
    citations_a = [c["reportId"] for c in response_a.citations]
    assert "rep_patient_b_secret" not in citations_a, "CRITICAL: Patient B report leaked to Patient A!"
    assert "135 mg/dL" not in response_a.answer, "CRITICAL: Patient B lab value leaked in Patient A answer!"

    # Query as Patient B
    response_b = pipeline.query("What is my latest cholesterol level?", patient_id=patient_b.id)
    citations_b = [c["reportId"] for c in response_b.citations]
    assert "rep_patient_b_secret" in citations_b, "Patient B should retrieve their own uploaded report"
