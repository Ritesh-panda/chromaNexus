import os
import hashlib
import pytest
from sqlalchemy import create_engine, text
from backend.app.core.database import PROTECTED_DB_PATHS, get_db, SessionLocal
from backend.app.ai.retrieval import ChromaDBVectorStore
from backend.app.ai.chunker import DocumentChunk
import chromadb


def compute_sha256(path: str) -> str:
    if not os.path.exists(path):
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


ROOT_DB_PATH = r"C:\chromaNexus\chronanexus.db"
BACKEND_DB_PATH = r"C:\chromaNexus\backend\chronanexus.db"
CHROMA_PERSIST_DIR = r"C:\chromaNexus\data\chroma_db"


def test_protected_sqlite_mutation_blocked_by_engine_listener():
    """
    Verifies that any attempted write statement (INSERT, UPDATE, DELETE, CREATE, DROP)
    targeting either protected database raises RuntimeError during test runs.
    """
    for db_path in [ROOT_DB_PATH, BACKEND_DB_PATH]:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        with pytest.raises(RuntimeError, match="CRITICAL TEST ISOLATION FAILURE"):
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO chat_messages (id, text) VALUES ('violator', 'test');"))

        with pytest.raises(RuntimeError, match="CRITICAL TEST ISOLATION FAILURE"):
            with engine.connect() as conn:
                conn.execute(text("CREATE TABLE test_violation (id INT);"))


def test_protected_chromadb_mutation_blocked_by_retrieval_guard():
    """
    Verifies that attempting to add or delete documents from the protected
    persistent ChromaDB store raises RuntimeError during test runs.
    """
    v_store = ChromaDBVectorStore(
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name="chronanexus_clinical_chunks"
    )
    test_chunk = DocumentChunk(
        chunk_id="violator_chunk",
        document_id="doc_violator",
        page_number=1,
        chunk_index=0,
        text="Violating chunk text",
        metadata={"patient_id": "test"}
    )
    with pytest.raises(RuntimeError, match="CRITICAL TEST ISOLATION FAILURE"):
        v_store.add_documents([test_chunk])

    with pytest.raises(RuntimeError, match="CRITICAL TEST ISOLATION FAILURE"):
        v_store.delete_document("violator_chunk")


def test_http_requests_preserve_protected_databases_and_chroma(client):
    """
    Verifies that issuing chat conversations and messages through the FastAPI
    TestClient operates strictly on isolated temporary storage and does not
    modify the protected SQLite databases or persistent ChromaDB collection.
    """
    # 1. Record before state
    root_hash_before = compute_sha256(ROOT_DB_PATH)
    backend_hash_before = compute_sha256(BACKEND_DB_PATH)

    client_chroma = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    coll = client_chroma.get_collection("chronanexus_clinical_chunks")
    chroma_count_before = coll.count()

    # 2. Issue HTTP requests via TestClient
    resp_get = client.get("/api/v1/chat/conversations")
    assert resp_get.status_code == 200

    resp_post = client.post(
        "/api/v1/chat/conversations/th_1/messages",
        json={"text": "When was my highest cholesterol reading?"}
    )
    assert resp_post.status_code == 200
    data = resp_post.json()
    assert data["sender"] == "ai"

    # 3. Record after state and assert bit-for-bit invariance
    root_hash_after = compute_sha256(ROOT_DB_PATH)
    backend_hash_after = compute_sha256(BACKEND_DB_PATH)
    chroma_count_after = coll.count()

    assert root_hash_before == root_hash_after, (
        f"Defect: Root database changed during HTTP test! Before: {root_hash_before}, After: {root_hash_after}"
    )
    assert backend_hash_before == backend_hash_after, (
        f"Defect: Backend database changed during HTTP test! Before: {backend_hash_before}, After: {backend_hash_after}"
    )
    assert chroma_count_before == chroma_count_after, (
        f"Defect: ChromaDB persistent count changed during HTTP test! Before: {chroma_count_before}, After: {chroma_count_after}"
    )
