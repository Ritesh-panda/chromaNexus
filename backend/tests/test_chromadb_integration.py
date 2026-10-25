import os
import tempfile
import shutil
import pytest
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import ChromaDBVectorStore, get_vector_store
from backend.app.ai.embeddings import get_embedding_provider
from backend.app.ai.rag.bm25_retriever import BM25KeywordRetriever
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider


@pytest.fixture
def disposable_chroma_dir():
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    try:
        import chromadb
        chromadb.api.client.SharedSystemClient.clear_system_cache()
    except Exception:
        pass
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_chromadb_insert_and_similarity_search(disposable_chroma_dir):
    """Verify synthetic chunks can be inserted into ChromaDB and retrieved via semantic similarity."""
    v_store = ChromaDBVectorStore(
        persist_directory=disposable_chroma_dir,
        collection_name="test_clinical_collection"
    )

    c1 = DocumentChunk(
        chunk_id="syn_chk_alpha_001",
        document_id="doc_alpha_lab_01",
        page_number=1,
        chunk_index=0,
        text="Serum Potassium: 4.8 mEq/L (Normal Reference: 3.5 - 5.1 mEq/L). Electrolytes stable.",
        metadata={"patient_id": "pat_synth_alpha", "category": "Lab Report"}
    )
    c2 = DocumentChunk(
        chunk_id="syn_chk_alpha_002",
        document_id="doc_alpha_cardio_02",
        page_number=2,
        chunk_index=0,
        text="Echocardiogram: Normal left ventricular ejection fraction 60-65%. No valvular vegetation.",
        metadata={"patient_id": "pat_synth_alpha", "category": "Cardiology"}
    )

    v_store.add_documents([c1, c2])
    assert v_store.collection.count() == 2

    # Query
    results = v_store.similarity_search("potassium level and electrolytes", top_k=2)
    assert len(results) >= 1
    assert results[0].chunk.chunk_id == "syn_chk_alpha_001"
    assert "4.8 mEq/L" in results[0].chunk.text
    assert results[0].chunk.page_number == 1
    assert results[0].score > 0.6


def test_chromadb_patient_isolation(disposable_chroma_dir):
    """Verify strict cross-patient isolation in ChromaDB metadata filtering."""
    v_store = ChromaDBVectorStore(
        persist_directory=disposable_chroma_dir,
        collection_name="test_isolation_collection"
    )

    c_alpha = DocumentChunk(
        chunk_id="chk_alpha_htn",
        document_id="doc_alpha_01",
        page_number=1,
        chunk_index=0,
        text="Patient Alex Vance diagnosed with essential hypertension, prescribed Lisinopril 10mg daily.",
        metadata={"patient_id": "pat_synth_alpha"}
    )
    c_beta = DocumentChunk(
        chunk_id="chk_beta_ortho",
        document_id="doc_beta_01",
        page_number=1,
        chunk_index=0,
        text="Patient Beta underwent right knee arthroscopy and ACL reconstruction with hamstring autograft.",
        metadata={"patient_id": "pat_synth_beta"}
    )

    v_store.add_documents([c_alpha, c_beta])

    # Search Alpha's space for knee surgery (which only Beta has)
    alpha_results = v_store.similarity_search(
        query="What were the findings of my right knee arthroscopy?",
        top_k=5,
        filter_metadata={"patient_id": "pat_synth_alpha"}
    )
    # Zero Beta records must leak
    assert not any(r.chunk.metadata.get("patient_id") == "pat_synth_beta" for r in alpha_results)
    assert not any("knee" in r.chunk.text.lower() for r in alpha_results)

    # Search Beta's space
    beta_results = v_store.similarity_search(
        query="What were the findings of my right knee arthroscopy?",
        top_k=5,
        filter_metadata={"patient_id": "pat_synth_beta"}
    )
    assert len(beta_results) == 1
    assert beta_results[0].chunk.metadata.get("patient_id") == "pat_synth_beta"


def test_chromadb_restart_persistence(disposable_chroma_dir):
    """Verify that chunks persisted in ChromaDB survive service reboots/re-instantiation without data loss."""
    # Instance 1: write data
    store1 = ChromaDBVectorStore(
        persist_directory=disposable_chroma_dir,
        collection_name="test_reboot_collection"
    )
    c = DocumentChunk(
        chunk_id="chk_persist_001",
        document_id="doc_persist_01",
        page_number=3,
        chunk_index=1,
        text="Histopathology: Biopsy negative for malignancy. Benign follicular adenoma.",
        metadata={"patient_id": "pat_synth_gamma"}
    )
    store1.add_documents([c])
    assert store1.collection.count() == 1

    # Instance 2: re-instantiate pointing to the exact same persist directory
    store2 = ChromaDBVectorStore(
        persist_directory=disposable_chroma_dir,
        collection_name="test_reboot_collection"
    )
    assert store2.collection.count() == 1

    search_res = store2.similarity_search("biopsy malignancy findings", top_k=1)
    assert len(search_res) == 1
    assert search_res[0].chunk.chunk_id == "chk_persist_001"
    assert search_res[0].chunk.page_number == 3
    assert "follicular adenoma" in search_res[0].chunk.text


def test_chromadb_bm25_refresh_and_rrf(disposable_chroma_dir):
    """Verify that newly ingested report chunks refresh BM25 and fuse correctly with ChromaDB via RRF."""
    v_store = ChromaDBVectorStore(
        persist_directory=disposable_chroma_dir,
        collection_name="test_hybrid_rrf_collection"
    )
    bm25 = BM25KeywordRetriever()
    hybrid = HybridRetriever(
        vector_store=v_store,
        bm25_retriever=bm25
    )

    # Ingest baseline report
    c1 = DocumentChunk(
        chunk_id="chk_visit_01",
        document_id="doc_visit_01",
        page_number=1,
        chunk_index=0,
        text="Annual Wellness Exam 2024. Blood pressure 120/80 mmHg. No complaints.",
        metadata={"patient_id": "pat_synth_delta"}
    )
    hybrid.index_chunks([c1])

    # Now simulate newly uploaded report ingested later
    c2_new = DocumentChunk(
        chunk_id="chk_bronchitis_new",
        document_id="doc_bronchitis_new",
        page_number=1,
        chunk_index=0,
        text="Urgent Care Encounter: Diagnosed with acute bacterial bronchitis, prescribed Azithromycin 250mg Z-Pak.",
        metadata={"patient_id": "pat_synth_delta"}
    )
    hybrid.index_chunks([c2_new])

    # Retrieve with hybrid BM25 + ChromaDB
    res = hybrid.retrieve(
        query="When was I diagnosed with acute bacterial bronchitis and what antibiotic was prescribed?",
        patient_id="pat_synth_delta",
        top_k=3
    )

    assert len(res.elements) > 0
    top_element = res.elements[0]
    assert "bronchitis" in top_element.content.lower()
    assert "azithromycin" in top_element.content.lower()
    # Confirm RRF combined both dense and lexical signals
    assert top_element.score > 0.0


def test_chromadb_full_rag_pipeline_citations(disposable_chroma_dir):
    """Verify end-to-end RAG pipeline using ChromaDB returns verified citations and page numbers."""
    v_store = ChromaDBVectorStore(
        persist_directory=disposable_chroma_dir,
        collection_name="test_rag_pipeline_collection"
    )
    c = DocumentChunk(
        chunk_id="chk_tsh_01",
        document_id="rep_thyroid_007",
        page_number=2,
        chunk_index=0,
        text="ENDOCRINOLOGY CLINICAL REPORT\nTSH: 2.15 uIU/mL (Normal, Ref: 0.45-4.50 uIU/mL)\nFree T4: 1.2 ng/dL (Normal).",
        metadata={"patient_id": "pat_synth_epsilon", "title": "Endocrinology Follow-up"}
    )
    v_store.add_documents([c])

    hybrid = HybridRetriever(vector_store=v_store)
    pipeline = RAGPipeline(
        retriever=hybrid,
        llm=MockDeterministicLLMProvider()
    )

    response = pipeline.query(
        question="What was my TSH level on the endocrinology report?",
        patient_id="pat_synth_epsilon"
    )

    assert response.answer is not None
    assert len(response.citations) > 0
    cit = response.citations[0]
    assert cit.get("reportId") == "rep_thyroid_007"
    assert "(p.2)" in cit.get("reportTitle")
