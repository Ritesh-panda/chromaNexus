from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
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


class ResultFusion:
    """
    Fuses structured relational data and unstructured vector chunks into a prioritized context.
    Removes exact duplicates, balances representation, and enforces length budgets.
    """

    def __init__(self, max_items: int = 10):
        self.max_items = max_items

    def fuse(
        self,
        structured_results: List[StructuredClinicalResult],
        vector_results: List[SearchResult],
        primary_intent: str = "GENERAL_DOCUMENT_QUERY"
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

        # 2. Convert vector search chunks
        for item in vector_results:
            chunk = item.chunk
            meta = chunk.metadata
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

        # 3. For MIXED_CLINICAL / overview queries, enforce balanced representation
        if primary_intent == "MIXED_CLINICAL":
            budget = max(self.max_items, 12)
            by_type: Dict[str, List[FusedElement]] = {}
            for elem in fused:
                by_type.setdefault(elem.source_type, []).append(elem)

            for t in by_type:
                by_type[t].sort(key=lambda x: x.score, reverse=True)

            balanced: List[FusedElement] = []
            # Take top items from each key category
            type_quotas = {
                "structured_disease": 3,
                "structured_medication": 3,
                "structured_lab_result": 4,
                "structured_timeline_event": 2,
                "report_chunk": 2
            }
            for stype, quota in type_quotas.items():
                balanced.extend(by_type.get(stype, [])[:quota])

            # Fill remaining budget if needed
            already_ids = {e.id for e in balanced}
            remaining = [e for e in fused if e.id not in already_ids]
            remaining.sort(key=lambda x: x.score, reverse=True)
            balanced.extend(remaining[:max(0, budget - len(balanced))])
            return balanced

        # 4. Standard sort by score descending
        fused.sort(key=lambda x: x.score, reverse=True)
        return fused[:self.max_items]
