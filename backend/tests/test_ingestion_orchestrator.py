import pytest
from backend.app.ai.ingestion.orchestrator import DocumentIngestionOrchestrator
from backend.app.ai.ingestion.ingestion_status import ingestion_registry, IngestionStage
from backend.app.ai.retrieval import InMemoryVectorStore
from backend.app.ai.embeddings import LocalLightweightEmbeddingProvider
from backend.app.models.patient import Patient
from backend.app.models.user import User


def test_ingestion_orchestrator_success(db_session):
    # Setup test patient
    user = User(id="usr_test_orch", email="orch@example.com", hashed_password="pw", name="Orch User")
    db_session.add(user)
    patient = Patient(id="pat_test_orch", user_id="usr_test_orch", blood_group="A+")
    db_session.add(patient)
    db_session.commit()

    vector_store = InMemoryVectorStore()
    embedding_provider = LocalLightweightEmbeddingProvider()

    orchestrator = DocumentIngestionOrchestrator(
        embedding_provider=embedding_provider,
        vector_store=vector_store
    )

    doc_text = (
        "Comprehensive Metabolic Panel\n"
        "Patient: Orchestrator Patient\n"
        "Date: 2024-05-10\n"
        "Fasting Blood Glucose: 110 mg/dL\n"
        "Diagnosis: Pre-diabetes\n"
        "Prescription: Metformin 250mg once daily\n"
    )

    doc_id = "doc_orch_001"
    success = orchestrator.process_document(
        document_id=doc_id,
        file_bytes=doc_text.encode("utf-8"),
        file_name="lab_results.txt",
        patient_id="pat_test_orch",
        db=db_session,
        report_date="2024-05-10",
        hospital_name="Test Ingestion Health"
    )

    assert success is True

    # Verify status registry updated to COMPLETED
    status = ingestion_registry.get_status(doc_id)
    assert status is not None
    assert status.status == IngestionStage.COMPLETED
    assert status.progress_percent == 100
    assert status.indexed_chunks_count > 0


def test_ingestion_orchestrator_scanned_fallback(db_session):
    user = db_session.query(User).filter_by(id="usr_test_orch").first()
    if not user:
        user = User(id="usr_test_orch", email="orch@example.com", hashed_password="pw", name="Orch User")
        db_session.add(user)
    patient = db_session.query(Patient).filter_by(id="pat_test_orch").first()
    if not patient:
        patient = Patient(id="pat_test_orch", user_id="usr_test_orch", blood_group="A+")
        db_session.add(patient)
    db_session.commit()

    orchestrator = DocumentIngestionOrchestrator(
        embedding_provider=LocalLightweightEmbeddingProvider(),
        vector_store=InMemoryVectorStore()
    )

    # Scanned PDF binary simulator
    scanned_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    doc_id = "doc_orch_scanned_002"

    success = orchestrator.process_document(
        document_id=doc_id,
        file_bytes=scanned_bytes,
        file_name="scanned_scan.pdf",
        patient_id="pat_test_orch",
        db=db_session
    )

    assert success is True
    status = ingestion_registry.get_status(doc_id)
    assert status is not None
    assert status.status == IngestionStage.COMPLETED
