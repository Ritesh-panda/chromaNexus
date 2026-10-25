import os
import pytest
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.embeddings import BGEEmbeddingProvider, LocalLightweightEmbeddingProvider
from backend.app.ai.retrieval import ChromaDBVectorStore, SearchResult
from backend.app.ai.rag.bm25_retriever import BM25KeywordRetriever, clinical_bm25_tokenize
from backend.app.ai.rag.fusion import ResultFusion, reciprocal_rank_fusion
from backend.app.ai.rag.hybrid_retriever import HybridRetriever
from backend.app.ai.rag.query_resolver import ConversationQueryResolver


def test_bge_semantic_similarity_synonyms():
    """Verify that BGE produces semantic similarity for clinical synonyms where hash vectorizer fails."""
    provider = BGEEmbeddingProvider()
    assert provider.dimension() == 384

    v_query = provider.embed_text("What treatments are documented for my high blood pressure?")
    v_doc1 = provider.embed_text("Patient diagnosed with Essential Hypertension. Prescribed Lisinopril 10mg once daily.")
    v_doc2 = provider.embed_text("Routine screening colonoscopy showed normal colonic mucosa without polyps.")

    sim_synonym = sum(q * d for q, d in zip(v_query, v_doc1))
    sim_unrelated = sum(q * d for q, d in zip(v_query, v_doc2))

    # BGE semantic cosine similarity for medical synonyms must be substantially higher than unrelated text
    assert sim_synonym > 0.65
    assert sim_synonym > sim_unrelated + 0.20


def test_chromadb_vector_store_disposable(tmp_path):
    """Verify ChromaDB operates in-process with a disposable directory and patient isolation."""
    persist_dir = str(tmp_path / "chroma_test_store")
    v_store = ChromaDBVectorStore(persist_directory=persist_dir)

    c1 = DocumentChunk(
        chunk_id="chk_alpha_1",
        document_id="doc_alpha_1",
        page_number=1,
        chunk_index=0,
        text="Serum Potassium was measured at 4.8 mEq/L (Normal 3.5 - 5.1).",
        metadata={"patient_id": "pat_alpha", "report_type": "lab_report"}
    )
    c2 = DocumentChunk(
        chunk_id="chk_beta_1",
        document_id="doc_beta_1",
        page_number=1,
        chunk_index=0,
        text="Serum Potassium was measured at 6.2 mEq/L Critical High.",
        metadata={"patient_id": "pat_beta", "report_type": "lab_report"}
    )

    v_store.add_documents([c1, c2])

    # Search with patient_id filter
    res_alpha = v_store.similarity_search("potassium level", top_k=5, filter_metadata={"patient_id": "pat_alpha"})
    assert len(res_alpha) == 1
    assert res_alpha[0].chunk.chunk_id == "chk_alpha_1"
    assert "4.8" in res_alpha[0].chunk.text

    # Verify zero leakage from Patient Beta
    assert all(r.chunk.metadata.get("patient_id") == "pat_alpha" for r in res_alpha)


def test_bm25_retriever_exact_keyword_and_dosage():
    """Verify BM25 keyword matching for exact drugs, dosages, and numbers."""
    bm25 = BM25KeywordRetriever()

    c1 = DocumentChunk(
        chunk_id="chk_med_1",
        document_id="doc_1",
        page_number=1,
        chunk_index=0,
        text="Discharge plan: Prescribed Azithromycin 250mg Z-Pak 5-day course for acute asthmatic bronchitis.",
        metadata={"patient_id": "pat_alpha"}
    )
    c2 = DocumentChunk(
        chunk_id="chk_med_2",
        document_id="doc_2",
        page_number=1,
        chunk_index=0,
        text="Maintenance therapy: Metformin 500mg BID and Lisinopril 10mg QD.",
        metadata={"patient_id": "pat_alpha"}
    )
    c3 = DocumentChunk(
        chunk_id="chk_med_beta",
        document_id="doc_3",
        page_number=1,
        chunk_index=0,
        text="Prescribed Azithromycin 500mg IV for inpatient pneumonia.",
        metadata={"patient_id": "pat_beta"}
    )

    bm25.index_chunks([c1, c2, c3])

    # Search for Azithromycin under patient alpha filter
    results = bm25.search("acute bronchitis antibiotic Azithromycin", top_k=2, filter_metadata={"patient_id": "pat_alpha"})
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "chk_med_1"
    assert results[0].score > 0.0


def test_reciprocal_rank_fusion_math():
    """Verify standard RRF (k=60) mathematically prioritizes chunks supported across both modalities."""
    c_shared = DocumentChunk(chunk_id="chk_shared", document_id="doc_1", page_number=1, chunk_index=0, text="Shared chunk text")
    c_vector_only = DocumentChunk(chunk_id="chk_vec", document_id="doc_2", page_number=1, chunk_index=0, text="Vector only text")
    c_bm25_only = DocumentChunk(chunk_id="chk_bm25", document_id="doc_3", page_number=1, chunk_index=0, text="BM25 only text")

    # Vector results: shared is rank 1, vec is rank 2
    vec_results = [
        SearchResult(chunk=c_shared, score=0.92),
        SearchResult(chunk=c_vector_only, score=0.85)
    ]
    # BM25 results: shared is rank 1, bm25 is rank 2
    bm25_results = [
        SearchResult(chunk=c_shared, score=0.95),
        SearchResult(chunk=c_bm25_only, score=0.78)
    ]

    fused = reciprocal_rank_fusion(vec_results, bm25_results, rrf_k=60)
    assert len(fused) == 3

    # Shared chunk appears in both rankings at rank 1, so its RRF score must be highest (normalized to 1.0)
    assert fused[0].chunk.chunk_id == "chk_shared"
    assert fused[0].score == 1.0


def test_query_resolver_pulmonary_taxonomy():
    """Verify that DEF-03 fix resolves pulmonary/asthma follow-up questions correctly."""
    resolver = ConversationQueryResolver()

    turn1_history = [
        {"sender": "user", "text": "What pulmonary conditions have been diagnosed in my records?"},
        {"sender": "ai", "text": "You have a documented diagnosis of Moderate Persistent Asthma from St. Jude Pulmonary Center."}
    ]

    turn2_query = "What inhaler dose was prescribed for that condition?"
    resolved = resolver.resolve(turn2_query, conversation_history=turn1_history)

    assert resolved.active_topic in ["asthma", "pulmonary"]
    assert "inhaler" in resolved.resolved_query.lower() or "fluticasone" in resolved.resolved_query.lower() or "asthma" in resolved.resolved_query.lower()
