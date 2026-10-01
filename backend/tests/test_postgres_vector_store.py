import pytest
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import PostgresVectorStore, get_vector_store
from backend.app.ai.embeddings import LocalLightweightEmbeddingProvider


def test_postgres_vector_store_crud(db_session):
    emb_provider = LocalLightweightEmbeddingProvider(dim=64)
    store = PostgresVectorStore(db_session=db_session, embedding_provider=emb_provider)

    assert store.health_check() is True

    chunks = [
        DocumentChunk(
            chunk_id="pg_chk_01",
            document_id="rep_002",
            page_number=1,
            chunk_index=0,
            text="Lipid Profile: Total Cholesterol was 242 mg/dL on June 12, 2021.",
            metadata={"title": "Lipid Profile", "patient_id": "pat_001"}
        ),
        DocumentChunk(
            chunk_id="pg_chk_02",
            document_id="rep_003",
            page_number=1,
            chunk_index=0,
            text="3.0T MRI Right Knee Joint: Grade II signal alteration in posterior horn of medial meniscus.",
            metadata={"title": "MRI Right Knee", "patient_id": "pat_001"}
        )
    ]

    # Add chunks
    store.add_documents(chunks)

    # Search
    results = store.similarity_search("cholesterol level", top_k=1, filter_metadata={"patient_id": "pat_001"})
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "pg_chk_01"
    assert "242 mg/dL" in results[0].chunk.text

    # Delete
    deleted = store.delete_document("rep_002")
    assert deleted >= 1


def test_get_vector_store_factory(db_session):
    in_mem = get_vector_store("in_memory")
    assert in_mem.__class__.__name__ == "InMemoryVectorStore"

    pg_store = get_vector_store("postgres", db_session=db_session)
    assert isinstance(pg_store, PostgresVectorStore)
