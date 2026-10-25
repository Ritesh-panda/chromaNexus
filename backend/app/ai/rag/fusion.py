from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import SearchResult
from backend.app.ai.rag.structured_retriever import StructuredClinicalResult


class FusedElement(BaseModel):
    id: str
    source_type: str  # 'structured_lab' | 'structured_medication' | 'structured_diagnosis' | 'timeline_event' | 'report_chunk'
    title: str
    date: str
    content: str
    report_id: Optional[str] = None
    score: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)


def reciprocal_rank_fusion(
    vector_results: List[SearchResult],
    bm25_results: List[SearchResult],
    rrf_k: int = 60,
    weight_vector: float = 1.0,
    weight_bm25: float = 1.0
) -> List[SearchResult]:
    """
    Computes standard Reciprocal Rank Fusion (RRF) over vector and BM25 lexical rankings.
    Formula: RRF(d) = sum_m ( weight_m / (rrf_k + rank_m(d)) )
    Normalized to range [0.0, 1.0].
    """
    rrf_scores: Dict[str, float] = {}
    chunks_by_id: Dict[str, DocumentChunk] = {}

    # 1. Accumulate dense vector ranks
    for rank, item in enumerate(vector_results, start=1):
        c_id = item.chunk.chunk_id or f"chk_{item.chunk.document_id}_{item.chunk.chunk_index}"
        chunks_by_id[c_id] = item.chunk
        rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (weight_vector / (rrf_k + rank))

    # 2. Accumulate lexical BM25 ranks
    for rank, item in enumerate(bm25_results, start=1):
        c_id = item.chunk.chunk_id or f"chk_{item.chunk.document_id}_{item.chunk.chunk_index}"
        chunks_by_id[c_id] = item.chunk
        rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (weight_bm25 / (rrf_k + rank))

    if not rrf_scores:
        return []

    max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0

    # Sort descending by fused RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda kv: kv[1], reverse=True)
    fused: List[SearchResult] = []

    for c_id, raw_rrf in sorted_items:
        norm_score = raw_rrf / max_rrf if max_rrf > 0 else 0.5
        fused.append(SearchResult(
            chunk=chunks_by_id[c_id],
            score=round(norm_score, 4)
        ))

    return fused


class ResultFusion:
    """
    Phase 4 Hybrid Result Fusion for ChronaNexus.
    Combines structured relational clinical data with Reciprocal Rank Fusion (RRF) of
    dense vector chunks and BM25 keyword chunks. Enforces representation budgets.
    """

    def __init__(self, max_items: int = 10, rrf_k: int = 60):
        self.max_items = max_items
        self.rrf_k = rrf_k

    def fuse(
        self,
        structured_results: List[StructuredClinicalResult],
        vector_results: List[SearchResult],
        primary_intent: str = "GENERAL_DOCUMENT_QUERY",
        bm25_results: Optional[List[SearchResult]] = None
    ) -> List[FusedElement]:
        fused: List[FusedElement] = []
        seen_keys = set()

        # 1. Convert structured results
        for item in structured_results:
            key = f"{item.source_type}_{item.source_id}"
            if key not in seen_keys:
                seen_keys.add(key)
                fused.append(FusedElement(
                    id=item.source_id,
                    source_type=f"structured_{item.source_type}",
                    title=item.title,
                    date=item.date,
                    content=item.content,
                    report_id=item.report_id,
                    score=item.relevance_score,
                    metadata=item.metadata
                ))

        # 2. Compute chunk rankings: apply Reciprocal Rank Fusion if BM25 results available
        if bm25_results is not None:
            effective_chunks = reciprocal_rank_fusion(
                vector_results=vector_results,
                bm25_results=bm25_results,
                rrf_k=self.rrf_k
            )
        else:
            effective_chunks = vector_results

        # 3. Convert document chunks into FusedElements
        for item in effective_chunks:
            chunk = item.chunk
            meta = chunk.metadata or {}
            key = f"chunk_{chunk.chunk_id}"
            if key not in seen_keys:
                seen_keys.add(key)
                title = meta.get("title", meta.get("report_title", f"Report #{chunk.document_id}"))
                date = meta.get("date", meta.get("report_date", "Undated"))

                fused.append(FusedElement(
                    id=chunk.chunk_id,
                    source_type="report_chunk",
                    title=f"Excerpt: {title} (p.{chunk.page_number})",
                    date=str(date),
                    content=chunk.text,
                    report_id=chunk.document_id,
                    score=round(item.score, 3),
                    metadata={
                        **meta,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index
                    }
                ))

        # 4. For MIXED_CLINICAL / overview queries, enforce balanced representation
        if primary_intent == "MIXED_CLINICAL":
            budget = max(self.max_items, 12)
            by_type: Dict[str, List[FusedElement]] = {}
            for elem in fused:
                by_type.setdefault(elem.source_type, []).append(elem)

            for t in by_type:
                by_type[t].sort(key=lambda x: x.score, reverse=True)

            balanced: List[FusedElement] = []
            type_quotas = {
                "structured_disease": 3,
                "structured_medication": 3,
                "structured_lab_result": 4,
                "structured_timeline_event": 2,
                "report_chunk": 3
            }
            for stype, quota in type_quotas.items():
                balanced.extend(by_type.get(stype, [])[:quota])

            # Fill remaining budget
            already_ids = {e.id for e in balanced}
            remaining = [e for e in fused if e.id not in already_ids]
            remaining.sort(key=lambda x: x.score, reverse=True)
            balanced.extend(remaining[:max(0, budget - len(balanced))])
            return balanced

        # 5. Standard sort by score descending, with date descending as secondary tie-breaker
        fused.sort(key=lambda x: (round(x.score, 2), str(x.date or "")), reverse=True)
        return fused[:self.max_items]
