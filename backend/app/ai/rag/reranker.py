import re
from typing import List
from backend.app.ai.rag.fusion import FusedElement
from backend.app.ai.rag.classifier import QueryIntent


class ClinicalReranker:
    """
    Lightweight clinical reranker.
    Adjusts ranking scores based on query intent alignment, term overlap, and temporal recency.
    Can be replaced or extended with a neural Cross-Encoder model.
    """

    def rerank(
        self,
        elements: List[FusedElement],
        query: str,
        primary_intent: QueryIntent
    ) -> List[FusedElement]:
        if not elements:
            return []

        lower_query = query.lower()
        query_words = set(re.findall(r"\b[a-z0-9]+\b", lower_query))

        reranked: List[FusedElement] = []

        for elem in elements:
            score = elem.score
            content_lower = elem.content.lower()

            # 1. Boost for intent alignment
            if primary_intent == QueryIntent.LAB_HISTORY and "lab" in elem.source_type:
                score += 0.15
            elif primary_intent == QueryIntent.MEDICATION_HISTORY and "medication" in elem.source_type:
                score += 0.15
            elif primary_intent == QueryIntent.DIAGNOSIS_HISTORY and "diagnosis" in elem.source_type:
                score += 0.15
            elif primary_intent == QueryIntent.TIMELINE and "timeline" in elem.source_type:
                score += 0.15
            elif primary_intent == QueryIntent.REPORT_CONTENT and elem.source_type == "report_chunk":
                score += 0.15

            # 2. Boost for specific query keyword overlap
            for w in query_words:
                if len(w) > 3 and w in content_lower:
                    score += 0.05

            # 3. Recency bonus if asking for latest/recent/current
            if any(term in lower_query for term in ["latest", "recent", "current", "highest", "last"]):
                if "2026" in elem.date or "2025" in elem.date:
                    score += 0.08

            elem_copy = elem.model_copy()
            elem_copy.score = min(1.0, round(score, 3))
            reranked.append(elem_copy)

        # Sort by updated score descending
        reranked.sort(key=lambda x: x.score, reverse=True)
        return reranked
