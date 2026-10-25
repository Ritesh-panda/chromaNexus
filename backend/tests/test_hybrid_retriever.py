import pytest
from backend.app.ai.rag.hybrid_retriever import HybridRetriever, HybridRetrievalResult
from backend.app.ai.retrieval import InMemoryVectorStore
from backend.app.ai.chunker import DocumentChunk
from backend.app.models.patient import Patient


def test_hybrid_retriever_multi_branch(db_session):
    patient = db_session.query(Patient).first()
    assert patient is not None

    vector_store = InMemoryVectorStore()
    vector_store.add_documents([
        DocumentChunk(
            chunk_id="chk_mri_01",
            document_id="rep_003",
            page_number=1,
            chunk_index=0,
            text="3.0T MRI Right Knee: Grade II signal alteration of posterior horn medial meniscus.",
            metadata={"title": "MRI Right Knee Joint", "patient_id": patient.id, "date": "2022-08-10"}
        )
    ])

    retriever = HybridRetriever(vector_store=vector_store, db_session=db_session)

    # 1. Test pure structured branch
    res_lab = retriever.retrieve("What was my cholesterol level?", patient_id=patient.id)
    assert isinstance(res_lab, HybridRetrievalResult)
    assert res_lab.structured_count > 0
    assert len(res_lab.elements) > 0

    # 2. Test semantic vector branch
    res_mri = retriever.retrieve("What did my knee MRI scan show?", patient_id=patient.id)
    assert res_mri.vector_count > 0
    assert any("MRI" in elem.title or "meniscus" in elem.content.lower() for elem in res_mri.elements)

    # 3. Test mixed query
    res_mixed = retriever.retrieve("How did my HbA1c change after I started taking Metformin?", patient_id=patient.id)
    assert len(res_mixed.elements) > 0


import uuid
import logging
from backend.app.models.user import User
from backend.app.models.report import MedicalReport
from backend.app.models.document_chunk import DocumentChunkModel


def test_bm25_hydration_missing_metadata_propagates_authoritative_patient_id(db_session):
    """
    Requirement 2: When hydrating chunks from SQL, explicitly propagate authoritative
    DocumentChunkModel.patient_id into each chunk's metadata, even when chunk_metadata
    is None or missing patient_id.
    """
    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    patient_id = f"pat_{uuid.uuid4().hex[:8]}"
    report_id = f"rep_{uuid.uuid4().hex[:8]}"
    chunk_id = f"chk_test_{uuid.uuid4().hex[:8]}"

    u = User(id=user_id, name="BM25 Meta User", email=f"{user_id}@test.com", hashed_password="pwd")
    p = Patient(id=patient_id, user_id=user_id)
    r = MedicalReport(
        id=report_id,
        patient_id=patient_id,
        title="Endocrine Panel",
        file_name="endocrine.pdf",
        hospital_name="St. Jude",
        report_date="2026-10-15"
    )
    c = DocumentChunkModel(
        id=chunk_id,
        document_id=report_id,
        patient_id=patient_id,
        chunk_id=chunk_id,
        chunk_index=0,
        page_number=1,
        content="Free T4 thyroxine level was 1.15 ng/dL with normal reference range 0.8-1.8 ng/dL.",
        chunk_metadata=None
    )
    db_session.add_all([u, p, r, c])
    db_session.commit()

    retriever = HybridRetriever(vector_store=InMemoryVectorStore(), db_session=db_session)
    res = retriever.retrieve("What was my Free T4 thyroxine level?", patient_id=patient_id)

    indexed_chunks = retriever.bm25_retriever._chunks
    matching = [ch for ch in indexed_chunks if ch.chunk_id == chunk_id]
    assert len(matching) == 1
    assert matching[0].metadata.get("patient_id") == patient_id

    assert len(res.elements) > 0
    assert any("thyroxine" in elem.content.lower() or "1.15" in elem.content for elem in res.elements)


def test_bm25_patient_isolation(db_session):
    """
    Requirement 2: Ensure BM25 lexical keyword retrieval strictly enforces patient isolation.
    Chunks from Patient A must never be retrieved for Patient B even when sharing identical keywords.
    """
    u_a = User(id=f"usr_a_{uuid.uuid4().hex[:6]}", name="Pat A User", email=f"a_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pwd")
    u_b = User(id=f"usr_b_{uuid.uuid4().hex[:6]}", name="Pat B User", email=f"b_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pwd")
    pat_a = Patient(id=f"pat_a_{uuid.uuid4().hex[:6]}", user_id=u_a.id)
    pat_b = Patient(id=f"pat_b_{uuid.uuid4().hex[:6]}", user_id=u_b.id)

    rep_a = MedicalReport(id=f"rep_a_{uuid.uuid4().hex[:6]}", patient_id=pat_a.id, title="Cardiology Rep A", file_name="a.pdf", hospital_name="Hospital A", report_date="2026-10-10")
    rep_b = MedicalReport(id=f"rep_b_{uuid.uuid4().hex[:6]}", patient_id=pat_b.id, title="Cardiology Rep B", file_name="b.pdf", hospital_name="Hospital B", report_date="2026-10-11")

    chk_a = DocumentChunkModel(
        id=f"chk_a_{uuid.uuid4().hex[:6]}",
        document_id=rep_a.id,
        patient_id=pat_a.id,
        chunk_id=f"chk_a_{uuid.uuid4().hex[:6]}",
        chunk_index=0,
        page_number=1,
        content="Cardiac biomarker high_sensitivity_troponin_xyz was 0.01 ng/mL for Patient Alpha.",
        chunk_metadata={"patient_id": pat_a.id}
    )
    chk_b = DocumentChunkModel(
        id=f"chk_b_{uuid.uuid4().hex[:6]}",
        document_id=rep_b.id,
        patient_id=pat_b.id,
        chunk_id=f"chk_b_{uuid.uuid4().hex[:6]}",
        chunk_index=0,
        page_number=1,
        content="Cardiac biomarker high_sensitivity_troponin_xyz was 0.98 ng/mL for Patient Beta.",
        chunk_metadata={"patient_id": pat_b.id}
    )
    db_session.add_all([u_a, u_b, pat_a, pat_b, rep_a, rep_b, chk_a, chk_b])
    db_session.commit()

    retriever = HybridRetriever(vector_store=InMemoryVectorStore(), db_session=db_session)

    res_a = retriever.retrieve("What was my high_sensitivity_troponin_xyz?", patient_id=pat_a.id)
    all_content_a = " ".join(elem.content for elem in res_a.elements)
    assert "0.01" in all_content_a or "Patient Alpha" in all_content_a
    assert "0.98" not in all_content_a
    assert "Patient Beta" not in all_content_a

    retriever_b = HybridRetriever(vector_store=InMemoryVectorStore(), db_session=db_session)
    res_b = retriever_b.retrieve("What was my high_sensitivity_troponin_xyz?", patient_id=pat_b.id)
    all_content_b = " ".join(elem.content for elem in res_b.elements)
    assert "0.98" in all_content_b or "Patient Beta" in all_content_b
    assert "0.01" not in all_content_b
    assert "Patient Alpha" not in all_content_b


def test_bm25_empty_index_safe_retrieval(db_session):
    """
    Requirement 2: Ensure BM25 keyword search handles empty indexes and non-existent patients safely
    without exceptions, returning a valid, empty HybridRetrievalResult.
    """
    empty_patient_id = f"pat_empty_{uuid.uuid4().hex[:8]}"
    retriever = HybridRetriever(vector_store=InMemoryVectorStore(), db_session=db_session)

    res = retriever.retrieve("What was my creatinine level?", patient_id=empty_patient_id)
    assert isinstance(res, HybridRetrievalResult)
    assert len(res.elements) == 0
    assert res.bm25_count == 0
    assert res.vector_count == 0
    assert res.structured_count == 0


def test_bm25_hydration_exception_handling_and_recovery(db_session, monkeypatch, caplog):
    """
    Requirement 2: Replace silent exception swallowing in BM25 hydration with appropriate logging
    and safe failure behavior. On failure, retrieval continues safely. On subsequent recovery/retry,
    hydration succeeds.
    """
    user_id = f"usr_err_{uuid.uuid4().hex[:8]}"
    patient_id = f"pat_err_{uuid.uuid4().hex[:8]}"
    report_id = f"rep_err_{uuid.uuid4().hex[:8]}"
    chunk_id = f"chk_err_{uuid.uuid4().hex[:8]}"

    u = User(id=user_id, name="Error Recovery User", email=f"{user_id}@test.com", hashed_password="pwd")
    p = Patient(id=patient_id, user_id=user_id)
    r = MedicalReport(
        id=report_id,
        patient_id=patient_id,
        title="Recovery Report",
        file_name="recovery.pdf",
        hospital_name="City Hospital",
        report_date="2026-10-12"
    )
    c = DocumentChunkModel(
        id=chunk_id,
        document_id=report_id,
        patient_id=patient_id,
        chunk_id=chunk_id,
        chunk_index=0,
        page_number=1,
        content="Patient has elevated serum ferritin level of 850 ng/mL.",
        chunk_metadata={"patient_id": patient_id}
    )
    db_session.add_all([u, p, r, c])
    db_session.commit()

    retriever = HybridRetriever(vector_store=InMemoryVectorStore(), db_session=db_session)

    orig_query = db_session.query

    def failing_query(model):
        if model is DocumentChunkModel:
            raise RuntimeError("Simulated transient database connection error")
        return orig_query(model)

    monkeypatch.setattr(db_session, "query", failing_query)

    with caplog.at_level(logging.WARNING):
        res_error = retriever.retrieve("What was my serum ferritin?", patient_id=patient_id)
        assert isinstance(res_error, HybridRetrievalResult)

    warning_logged = any("Failed to hydrate BM25 index from SQL DocumentChunkModel" in record.message for record in caplog.records)
    assert warning_logged, "Expected warning log was not emitted during BM25 hydration failure"

    monkeypatch.undo()
    res_recovered = retriever.retrieve("What was my serum ferritin?", patient_id=patient_id)
    assert isinstance(res_recovered, HybridRetrievalResult)
    assert len(res_recovered.elements) > 0
    assert any("850" in elem.content or "ferritin" in elem.content.lower() for elem in res_recovered.elements)
