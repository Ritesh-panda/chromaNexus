from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.ai.retrieval import VectorStore, InMemoryVectorStore
from backend.app.ai.rag.classifier import QueryClassifier, ClassificationResult, QueryIntent
from backend.app.ai.rag.structured_retriever import StructuredRetriever, StructuredClinicalResult
from backend.app.ai.rag.fusion import ResultFusion, FusedElement
from backend.app.ai.rag.reranker import ClinicalReranker


class HybridRetrievalResult(BaseModel):
    intent: QueryIntent
    classification: ClassificationResult
    elements: List[FusedElement]
    structured_count: int = 0
    vector_count: int = 0


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
        reranker: Optional[ClinicalReranker] = None
    ):
        self.vector_store = vector_store or InMemoryVectorStore()
        self.db = db_session
        self.classifier = classifier or QueryClassifier()
        self.fusion = fusion or ResultFusion(max_items=8)
        self.reranker = reranker or ClinicalReranker()

    def retrieve(
        self,
        query: str,
        patient_id: str,
        top_k: int = 6
    ) -> HybridRetrievalResult:
        # 1. Classify query intent
        classification = self.classifier.classify(query)
        primary_intent = classification.primary_intent
        matched_keywords = classification.keywords_matched

        structured_results: List[StructuredClinicalResult] = []
        vector_results = []

        # 2. Structured Retrieval Branch (if DB session available)
        if self.db and patient_id:
            s_retriever = StructuredRetriever(self.db)

            if primary_intent in [QueryIntent.LAB_HISTORY, QueryIntent.MIXED_CLINICAL]:
                structured_results.extend(s_retriever.retrieve_labs(patient_id, matched_keywords, limit=6))

            if primary_intent in [QueryIntent.MEDICATION_HISTORY, QueryIntent.MIXED_CLINICAL]:
                structured_results.extend(s_retriever.retrieve_medications(patient_id, matched_keywords, limit=6))

            if primary_intent in [QueryIntent.DIAGNOSIS_HISTORY, QueryIntent.MIXED_CLINICAL]:
                structured_results.extend(s_retriever.retrieve_diagnoses(patient_id, limit=6))

            if primary_intent in [QueryIntent.TIMELINE, QueryIntent.MIXED_CLINICAL]:
                structured_results.extend(s_retriever.retrieve_timeline(patient_id, limit=6))

        # 3. Semantic Vector Retrieval Branch
        # Always run vector search for report content, mixed queries, or general document queries
        should_run_vector = (
            classification.is_hybrid_required or
            primary_intent in [
                QueryIntent.REPORT_CONTENT,
                QueryIntent.PROCEDURE_HISTORY,
                QueryIntent.GENERAL_DOCUMENT_QUERY,
                QueryIntent.MIXED_CLINICAL
            ] or
            len(structured_results) == 0  # Fallback if structured found nothing
        )

        if should_run_vector:
            filter_meta = {"patient_id": patient_id} if patient_id else None
            vector_results = self.vector_store.similarity_search(
                query=query,
                top_k=top_k,
                filter_metadata=filter_meta
            )

        # 4. Result Fusion & Deduplication
        fused = self.fusion.fuse(
            structured_results=structured_results,
            vector_results=vector_results,
            primary_intent=primary_intent.value
        )

        # 5. Intent-aware Reranking
        reranked = self.reranker.rerank(
            elements=fused,
            query=query,
            primary_intent=primary_intent
        )

        return HybridRetrievalResult(
            intent=primary_intent,
            classification=classification,
            elements=reranked,
            structured_count=len(structured_results),
            vector_count=len(vector_results)
        )
