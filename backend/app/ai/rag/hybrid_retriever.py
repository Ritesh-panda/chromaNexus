import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import VectorStore, InMemoryVectorStore, get_vector_store
from backend.app.ai.rag.bm25_retriever import BM25KeywordRetriever
from backend.app.ai.rag.classifier import QueryClassifier, ClassificationResult, QueryIntent
from backend.app.ai.rag.structured_retriever import StructuredRetriever, StructuredClinicalResult
from backend.app.ai.rag.fusion import ResultFusion, FusedElement
from backend.app.ai.rag.reranker import ClinicalReranker


logger = logging.getLogger(__name__)


class HybridRetrievalResult(BaseModel):
    intent: QueryIntent
    classification: ClassificationResult
    elements: List[FusedElement]
    structured_count: int = 0
    vector_count: int = 0
    bm25_count: int = 0


class HybridRetriever:
    """
    Production Hybrid Retriever for ChronaNexus.
    Combines deterministic structured SQL retrieval + semantic vector search (PostgreSQL/pgvector/In-Memory)
    with intent classification, result fusion, and reranking.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        db_session: Optional[Session] = None,
        classifier: Optional[QueryClassifier] = None,
        fusion: Optional[ResultFusion] = None,
        reranker: Optional[ClinicalReranker] = None,
        bm25_retriever: Optional[BM25KeywordRetriever] = None
    ):
        self.vector_store = vector_store or get_vector_store(db_session=db_session)
        self.db = db_session
        self.classifier = classifier or QueryClassifier()
        self.fusion = fusion or ResultFusion(max_items=8)
        self.reranker = reranker or ClinicalReranker()
        self.bm25_retriever = bm25_retriever or BM25KeywordRetriever()

    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Convenience method to index chunks into both vector store and BM25 retriever."""
        if hasattr(self.vector_store, "add_documents"):
            self.vector_store.add_documents(chunks)
        if self.bm25_retriever:
            self.bm25_retriever.index_chunks(chunks)

    def retrieve(
        self,
        query: str,
        patient_id: str,
        top_k: int = 6,
        search_query: Optional[str] = None,
        override_intent: Optional[QueryIntent] = None,
        override_keywords: Optional[List[str]] = None
    ) -> HybridRetrievalResult:
        if not patient_id or not str(patient_id).strip():
            logger.warning("HybridRetriever.retrieve invoked without a valid patient_id; failing closed with empty results.")
            classification = self.classifier.classify(query or "")
            return HybridRetrievalResult(elements=[], classifications=classification)

        eff_query = search_query or query

        # 1. Classify query intent
        classification = self.classifier.classify(eff_query)
        primary_intent = override_intent or classification.primary_intent
        matched_keywords = list(set((override_keywords or []) + classification.keywords_matched))

        structured_results: List[StructuredClinicalResult] = []
        vector_results = []

        # 2. Structured Retrieval Branch (if DB session available)
        if self.db and patient_id:
            s_retriever = StructuredRetriever(self.db)

            # Filter keywords specifically for lab and medication names
            # Broad overview keywords must not filter out all labs or medications
            overview_filter_words = {"health", "status", "summary", "overview", "report", "reports", "records", "current", "recent", "doing", "give", "tell", "level", "levels", "reading", "readings", "value", "values", "lab", "labs", "test", "tests"}
            lab_kws = [k for k in matched_keywords if k.lower() in QueryClassifier.LAB_KEYWORDS and k.lower() not in overview_filter_words]
            med_kws = [k for k in matched_keywords if k.lower() in QueryClassifier.MEDICATION_KEYWORDS and k.lower() not in overview_filter_words]

            if primary_intent in [QueryIntent.LAB_HISTORY, QueryIntent.MIXED_CLINICAL]:
                structured_results.extend(s_retriever.retrieve_labs(patient_id, lab_kws if lab_kws else None, limit=6))

            if primary_intent in [QueryIntent.MEDICATION_HISTORY, QueryIntent.MIXED_CLINICAL]:
                structured_results.extend(s_retriever.retrieve_medications(patient_id, med_kws if med_kws else None, limit=6))
                structured_results.extend(s_retriever.retrieve_allergies(patient_id, query_keywords=matched_keywords, query_text=eff_query, limit=5))

            # Also check allergy safety if query asks about allergies or drug safety explicitly
            allergy_triggers = {"allergy", "allergies", "allergic", "reaction", "safe", "take", "prescribed", "amoxicillin", "penicillin", "bactrim"}
            if any(w in eff_query.lower() for w in allergy_triggers) and primary_intent not in [QueryIntent.MEDICATION_HISTORY, QueryIntent.MIXED_CLINICAL]:
                structured_results.extend(s_retriever.retrieve_allergies(patient_id, query_keywords=matched_keywords, query_text=eff_query, limit=5))

            if primary_intent in [QueryIntent.DIAGNOSIS_HISTORY, QueryIntent.MIXED_CLINICAL]:

                structured_results.extend(s_retriever.retrieve_diagnoses(patient_id, limit=6))

            if primary_intent in [QueryIntent.TIMELINE, QueryIntent.MIXED_CLINICAL]:
                structured_results.extend(s_retriever.retrieve_timeline(patient_id, limit=6))

            if primary_intent == QueryIntent.REPORT_CONTENT:
                # Include relevant structured diagnoses or timeline events to enrich report context
                structured_results.extend(s_retriever.retrieve_diagnoses(patient_id, limit=3))
                structured_results.extend(s_retriever.retrieve_timeline(patient_id, limit=3))

            # Fallback for GENERAL_DOCUMENT_QUERY: pull all structured data so the LLM always
            # has patient context (covers "am I healthy?", unrecognized, or very short queries)
            if primary_intent == QueryIntent.GENERAL_DOCUMENT_QUERY and len(structured_results) == 0:
                structured_results.extend(s_retriever.retrieve_diagnoses(patient_id, limit=5))
                structured_results.extend(s_retriever.retrieve_medications(patient_id, limit=5))
                structured_results.extend(s_retriever.retrieve_labs(patient_id, limit=5))

        # 3. Semantic Vector Retrieval Branch
        # Always run vector search for report content, mixed queries, or general document queries
        should_run_vector = (
            classification.is_hybrid_required or
            primary_intent in [
                QueryIntent.REPORT_CONTENT,
                QueryIntent.PROCEDURE_HISTORY,
                QueryIntent.GENERAL_DOCUMENT_QUERY,
                QueryIntent.MIXED_CLINICAL,
                QueryIntent.LAB_HISTORY,
                QueryIntent.MEDICATION_HISTORY
            ] or
            len(structured_results) == 0  # Fallback if structured found nothing
        )

        if should_run_vector:
            filter_meta = {"patient_id": patient_id} if patient_id else None
            vector_results = self.vector_store.similarity_search(
                query=eff_query,
                top_k=top_k,
                filter_metadata=filter_meta
            )

        # 3b. BM25 Lexical Keyword Search Branch
        bm25_results = []
        if self.bm25_retriever:
            # Sync chunks from database into BM25 if not already indexed
            if self.bm25_retriever._bm25 is None and self.db and patient_id:
                try:
                    from backend.app.models.document_chunk import DocumentChunkModel
                    db_chunks = self.db.query(DocumentChunkModel).filter(
                        DocumentChunkModel.patient_id == patient_id
                    ).all()
                    if db_chunks:
                        chunks_to_index = []
                        for c in db_chunks:
                            meta = dict(c.chunk_metadata) if isinstance(c.chunk_metadata, dict) else {}
                            # Authoritatively enforce patient_id from the database column
                            meta["patient_id"] = str(c.patient_id)
                            meta.setdefault("document_id", c.document_id)
                            meta.setdefault("page_number", c.page_number)
                            chunks_to_index.append(
                                DocumentChunk(
                                    chunk_id=c.chunk_id,
                                    document_id=c.document_id,
                                    page_number=c.page_number,
                                    chunk_index=c.chunk_index,
                                    text=c.content,
                                    metadata=meta
                                )
                            )
                        self.bm25_retriever.index_chunks(chunks_to_index)
                except Exception as e:
                    logger.warning("Failed to hydrate BM25 index from SQL DocumentChunkModel for patient %s: %s", patient_id, str(e), exc_info=True)

            # Sync from ChromaDBVectorStore if present
            if self.bm25_retriever._bm25 is None and hasattr(self.vector_store, "get_patient_chunks") and patient_id:
                try:
                    c_chunks = self.vector_store.get_patient_chunks(patient_id)
                    if c_chunks:
                        for chunk in c_chunks:
                            if not chunk.metadata:
                                chunk.metadata = {}
                            chunk.metadata["patient_id"] = str(patient_id)
                        self.bm25_retriever.index_chunks(c_chunks)
                except Exception as e:
                    logger.warning("Failed to hydrate BM25 index from ChromaDBVectorStore for patient %s: %s", patient_id, str(e), exc_info=True)

            # Sync from InMemoryVectorStore if present
            if self.bm25_retriever._bm25 is None and hasattr(self.vector_store, "_documents"):
                try:
                    mem_docs = list(self.vector_store._documents.values())
                    if patient_id:
                        mem_docs = [d for d in mem_docs if (d.metadata or {}).get("patient_id") == patient_id]
                    if mem_docs:
                        self.bm25_retriever.index_chunks(mem_docs)
                except Exception as e:
                    logger.warning("Failed to hydrate BM25 index from InMemoryVectorStore for patient %s: %s", patient_id, str(e), exc_info=True)

            bm25_filter = {"patient_id": patient_id} if patient_id else None
            bm25_results = self.bm25_retriever.search(
                query=eff_query,
                top_k=top_k,
                filter_metadata=bm25_filter
            )

        # 4. Result Fusion & Reciprocal Rank Fusion (RRF)
        fused = self.fusion.fuse(
            structured_results=structured_results,
            vector_results=vector_results,
            primary_intent=primary_intent.value,
            bm25_results=bm25_results if bm25_results else None
        )

        # 5. Intent-aware Reranking
        reranked = self.reranker.rerank(
            elements=fused,
            query=eff_query,
            primary_intent=primary_intent
        )

        return HybridRetrievalResult(
            intent=primary_intent,
            classification=classification,
            elements=reranked,
            structured_count=len(structured_results),
            vector_count=len(vector_results),
            bm25_count=len(bm25_results) if bm25_results else 0
        )
