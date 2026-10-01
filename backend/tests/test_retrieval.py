import pytest
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import VectorStore, InMemoryVectorStore, SearchResult
from backend.app.ai.embeddings import LocalLightweightEmbeddingProvider


def test_vector_store_interface_and_crud():
    emb = LocalLightweightEmbeddingProvider(dim=64)
    store = InMemoryVectorStore(embedding_provider=emb)
    assert isinstance(store, VectorStore)
    assert store.health_check() is True

    # Prepare chunks
    chunks = [
        DocumentChunk(
            chunk_id="chk_01",
            document_id="doc_rep_002",
            page_number=1,
            chunk_index=0,
            text="Lipid Profile: Total Cholesterol 242 mg/dL (High). Fasting glucose 104 mg/dL.",
            metadata={"category": "blood_report", "patient_id": "pat_001"}
        ),
        DocumentChunk(
            chunk_id="chk_02",
            document_id="doc_rep_003",
            page_number=1,
            chunk_index=0,
            text="3.0T MRI Right Knee Joint: Grade II degenerative signal of posterior horn of medial meniscus.",
            metadata={"category": "mri", "patient_id": "pat_001"}
        ),
        DocumentChunk(
            chunk_id="chk_03",
            document_id="doc_rep_004",
            page_number=1,
            chunk_index=0,
            text="Clinical Encounter: Essential hypertension diagnosed. Prescribed Lisinopril 10mg QD.",
            metadata={"category": "prescription", "patient_id": "pat_002"}
        )
    ]

    store.add_documents(chunks)

    # Search for cholesterol
    results = store.similarity_search("What was my cholesterol level?", top_k=2)
    assert len(results) > 0
    assert isinstance(results[0], SearchResult)
    assert results[0].chunk.document_id == "doc_rep_002"

    # Search with patient metadata filter
    pat1_results = store.similarity_search(
        "hypertension prescription",
        top_k=5,
        filter_metadata={"patient_id": "pat_001"}
    )
    # pat_002 doc should NOT appear in filtered results
    assert all(r.chunk.metadata["patient_id"] == "pat_001" for r in pat1_results)

    # Delete document
    deleted = store.delete_document("doc_rep_002")
    assert deleted == 1
    
    # Query again, doc_rep_002 should not be in store
    after_del = store.similarity_search("cholesterol", top_k=5)
    assert all(r.chunk.document_id != "doc_rep_002" for r in after_del)
