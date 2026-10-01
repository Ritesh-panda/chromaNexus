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
