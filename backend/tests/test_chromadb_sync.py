import pytest
import chromadb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models.document_chunk import DocumentChunkModel
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.embeddings import LocalLightweightEmbeddingProvider
from backend.app.ai.retrieval import ChromaDBVectorStore


@pytest.fixture
def isolated_db(tmp_path):
    db_file = tmp_path / "test_isolated.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def embedding_provider():
    return LocalLightweightEmbeddingProvider(dim=384)


def test_sync_sql5_chroma0(isolated_db, tmp_path, embedding_provider):
    """SQL has 5 chunks; Chroma has 0: synchronize and expect 5."""
    chroma_dir = str(tmp_path / "chroma_0")
    for i in range(1, 6):
        isolated_db.add(DocumentChunkModel(
            chunk_id=f"chk_00{i}",
            document_id=f"doc_00{i}",
            patient_id="patient_alpha",
            chunk_index=i,
            page_number=1,
            content=f"Clinical observation chunk content number {i} regarding hypertension.",
            embedding=embedding_provider.embed_text(f"Clinical observation chunk {i}"),
            chunk_metadata={"source": "test", "category": "cardiology"}
        ))
    isolated_db.commit()

    vstore = ChromaDBVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_sync_5_0",
        embedding_provider=embedding_provider
    )
    assert vstore.collection.count() == 0

    res = vstore.sync_from_db(isolated_db)
    assert res == 5
    assert vstore.collection.count() == 5


def test_sync_sql5_chroma2_reconciles_missing(isolated_db, tmp_path, embedding_provider):
    """SQL has 5 chunks; Chroma has 2: synchronize and expect 5."""
    chroma_dir = str(tmp_path / "chroma_2")
    vstore = ChromaDBVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_sync_5_2",
        embedding_provider=embedding_provider
    )
    # Pre-populate Chroma with 2 chunks
    initial_chunks = [
        DocumentChunk(
            chunk_id="chk_001",
            document_id="doc_001",
            page_number=1,
            chunk_index=0,
            text="Initial chunk 1 content.",
            metadata={"patient_id": "patient_alpha"}
        ),
        DocumentChunk(
            chunk_id="chk_002",
            document_id="doc_002",
            page_number=1,
            chunk_index=1,
            text="Initial chunk 2 content.",
            metadata={"patient_id": "patient_alpha"}
        )
    ]
    vstore.add_documents(initial_chunks)
    assert vstore.collection.count() == 2

    # Add 5 chunks to SQL (chk_001 through chk_005)
    for i in range(1, 6):
        isolated_db.add(DocumentChunkModel(
            chunk_id=f"chk_00{i}",
            document_id=f"doc_00{i}",
            patient_id="patient_alpha",
            chunk_index=i,
            page_number=1,
            content=f"Clinical chunk content {i}.",
            embedding=embedding_provider.embed_text(f"Clinical chunk {i}"),
            chunk_metadata={"section": "labs"}
        ))
    isolated_db.commit()

    res = vstore.sync_from_db(isolated_db)
    assert res == 5
    assert vstore.collection.count() == 5

    # Verify all 5 IDs exist in Chroma
    all_chroma_ids = set(vstore.collection.get(include=[])["ids"])
    assert all_chroma_ids == {"chk_001", "chk_002", "chk_003", "chk_004", "chk_005"}


def test_sync_sql5_chroma5_no_duplicates(isolated_db, tmp_path, embedding_provider):
    """SQL has 5 chunks; Chroma already has 5: synchronize and expect no duplicates."""
    chroma_dir = str(tmp_path / "chroma_5")
    vstore = ChromaDBVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_sync_5_5",
        embedding_provider=embedding_provider
    )
    for i in range(1, 6):
        isolated_db.add(DocumentChunkModel(
            chunk_id=f"chk_00{i}",
            document_id=f"doc_00{i}",
            patient_id="patient_alpha",
            chunk_index=i,
            page_number=1,
            content=f"Clinical observation chunk {i}.",
            embedding=embedding_provider.embed_text(f"Clinical observation {i}"),
            chunk_metadata={"section": "progress_notes"}
        ))
    isolated_db.commit()

    # Pre-sync to fill Chroma with all 5
    first_res = vstore.sync_from_db(isolated_db)
    assert first_res == 5
    assert vstore.collection.count() == 5

    # Synchronize again when collection already has all 5
    second_res = vstore.sync_from_db(isolated_db)
    assert second_res == 5
    assert vstore.collection.count() == 5


def test_sync_idempotence_stability(isolated_db, tmp_path, embedding_provider):
    """Run synchronization twice and verify the count remains stable."""
    chroma_dir = str(tmp_path / "chroma_idempotent")
    vstore = ChromaDBVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_idempotent",
        embedding_provider=embedding_provider
    )
    for i in range(1, 6):
        isolated_db.add(DocumentChunkModel(
            chunk_id=f"chk_idem_{i}",
            document_id=f"doc_idem_{i}",
            patient_id="patient_beta",
            chunk_index=i,
            page_number=1,
            content=f"Idempotence verification text chunk {i}.",
            embedding=embedding_provider.embed_text(f"Idempotence {i}"),
            chunk_metadata={"test": "idempotent"}
        ))
    isolated_db.commit()

    count_1 = vstore.sync_from_db(isolated_db)
    count_2 = vstore.sync_from_db(isolated_db)
    count_3 = vstore.sync_from_db(isolated_db)

    assert count_1 == 5
    assert count_2 == 5
    assert count_3 == 5
    assert vstore.collection.count() == 5


def test_sync_multi_patient_metadata_isolation(isolated_db, tmp_path, embedding_provider):
    """Include chunks belonging to two synthetic patients and verify metadata isolation."""
    chroma_dir = str(tmp_path / "chroma_patients")
    vstore = ChromaDBVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_multi_patient",
        embedding_provider=embedding_provider
    )
    # Patient A chunks (3)
    for i in range(1, 4):
        isolated_db.add(DocumentChunkModel(
            chunk_id=f"chk_patA_{i}",
            document_id=f"doc_patA_{i}",
            patient_id="synthetic_patient_A",
            chunk_index=i,
            page_number=1,
            content=f"Patient A oncology lab report detail {i}.",
            embedding=embedding_provider.embed_text(f"Patient A report {i}"),
            chunk_metadata={"patient_id": "synthetic_patient_A", "department": "oncology"}
        ))
    # Patient B chunks (2)
    for j in range(1, 3):
        isolated_db.add(DocumentChunkModel(
            chunk_id=f"chk_patB_{j}",
            document_id=f"doc_patB_{j}",
            patient_id="synthetic_patient_B",
            chunk_index=j,
            page_number=1,
            content=f"Patient B cardiology assessment detail {j}.",
            embedding=embedding_provider.embed_text(f"Patient B assessment {j}"),
            chunk_metadata={"patient_id": "synthetic_patient_B", "department": "cardiology"}
        ))
    isolated_db.commit()

    res = vstore.sync_from_db(isolated_db)
    assert res == 5
    assert vstore.collection.count() == 5

    # Verify patient A chunks isolation
    patient_a_chunks = vstore.get_patient_chunks("synthetic_patient_A")
    assert len(patient_a_chunks) == 3
    for c in patient_a_chunks:
        assert c.metadata.get("patient_id") == "synthetic_patient_A"
        assert c.chunk_id.startswith("chk_patA_")

    # Verify patient B chunks isolation
    patient_b_chunks = vstore.get_patient_chunks("synthetic_patient_B")
    assert len(patient_b_chunks) == 2
    for c in patient_b_chunks:
        assert c.metadata.get("patient_id") == "synthetic_patient_B"
        assert c.chunk_id.startswith("chk_patB_")

    # Verify similarity search patient isolation
    search_a = vstore.similarity_search("oncology", top_k=5, filter_metadata={"patient_id": "synthetic_patient_A"})
    for s in search_a:
        assert s.chunk.metadata.get("patient_id") == "synthetic_patient_A"


def test_sync_retry_after_failed_indexing(isolated_db, tmp_path, embedding_provider, monkeypatch):
    """Simulate a failed indexing operation and verify that a later retry repairs missing entries."""
    chroma_dir = str(tmp_path / "chroma_retry")
    vstore = ChromaDBVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_retry_repairs",
        embedding_provider=embedding_provider
    )
    # Pre-populate Chroma with 2 chunks
    vstore.add_documents([
        DocumentChunk(chunk_id="chk_rep_1", document_id="doc_1", page_number=1, chunk_index=0, text="Chunk 1", metadata={"patient_id": "pat_1"}),
        DocumentChunk(chunk_id="chk_rep_2", document_id="doc_2", page_number=1, chunk_index=1, text="Chunk 2", metadata={"patient_id": "pat_1"})
    ])
    assert vstore.collection.count() == 2

    # Add 5 chunks to SQL
    for i in range(1, 6):
        isolated_db.add(DocumentChunkModel(
            chunk_id=f"chk_rep_{i}",
            document_id=f"doc_{i}",
            patient_id="pat_1",
            chunk_index=i,
            page_number=1,
            content=f"Report content {i}",
            embedding=embedding_provider.embed_text(f"Report {i}"),
            chunk_metadata={"seq": i}
        ))
    isolated_db.commit()

    # Simulate indexing failure on the first sync attempt
    call_count = {"count": 0}
    original_add = vstore.add_documents
    def failing_add(*args, **kwargs):
        call_count["count"] += 1
        raise RuntimeError("Simulated storage failure during chunk insertion!")

    monkeypatch.setattr(vstore, "add_documents", failing_add)

    # First attempt: sync encounters simulated failure and logs error, returns current count (2)
    sync_attempt_1 = vstore.sync_from_db(isolated_db)
    assert sync_attempt_1 == 2
    assert vstore.collection.count() == 2
    assert call_count["count"] == 1

    # Restore normal add_documents operation for retry
    monkeypatch.setattr(vstore, "add_documents", original_add)

    # Retry sync: successfully reconciles missing 3 chunks
    sync_attempt_2 = vstore.sync_from_db(isolated_db)
    assert sync_attempt_2 == 5
    assert vstore.collection.count() == 5

    # Verify all 5 chunks are now present
    existing_ids = set(vstore.collection.get(include=[])["ids"])
    assert existing_ids == {f"chk_rep_{i}" for i in range(1, 6)}


def test_sync_persistence_and_searchable_after_restart(isolated_db, tmp_path, embedding_provider):
    """Restart the test application and verify the indexed chunks remain searchable."""
    chroma_dir = str(tmp_path / "chroma_persistence")
    for i in range(1, 6):
        isolated_db.add(DocumentChunkModel(
            chunk_id=f"chk_persist_{i}",
            document_id=f"doc_persist_{i}",
            patient_id="pat_restart",
            chunk_index=i,
            page_number=1,
            content=f"Patient restart test record {i} documenting systolic blood pressure 135 mmHg.",
            embedding=embedding_provider.embed_text(f"Patient restart test record {i}"),
            chunk_metadata={"test": "persistence"}
        ))
    isolated_db.commit()

    # Application Session 1: initialize and sync
    vstore_1 = ChromaDBVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_persistence",
        embedding_provider=embedding_provider
    )
    synced = vstore_1.sync_from_db(isolated_db)
    assert synced == 5
    assert vstore_1.collection.count() == 5

    # Simulate restart: clear system cache and re-open from same disk path
    chromadb.api.client.SharedSystemClient.clear_system_cache()
    del vstore_1

    # Application Session 2: re-instantiate persistent vector store
    vstore_2 = ChromaDBVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_persistence",
        embedding_provider=embedding_provider
    )
    assert vstore_2.collection.count() == 5

    # Verify chunks remain searchable
    results = vstore_2.similarity_search("systolic blood pressure", top_k=3)
    assert len(results) > 0
    assert "blood pressure" in results[0].chunk.text
    assert results[0].chunk.metadata.get("patient_id") == "pat_restart"
