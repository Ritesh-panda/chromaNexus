import re
from typing import List
from backend.app.ai.rag.fusion import FusedElement
from backend.app.ai.rag.classifier import QueryIntent


def _extract_iso_date(date_str: str) -> str:
    if not date_str:
        return "0000-00-00"
    match = re.search(r"\b(19\d\d|20\d\d)(?:-(\d{2}))?(?:-(\d{2}))?\b", str(date_str))
    if match:
        year = match.group(1)
        month = match.group(2) or "01"
        day = match.group(3) or "01"
        return f"{year}-{month}-{day}"
    return "0000-00-00"


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

        is_extremum = any(term in lower_query for term in ["highest", "peak", "maximum", "max", "lowest", "minimum", "min"])
        is_explicit_recency = any(term in lower_query for term in ["latest", "recent", "current", "currently", "last", "newest", "new", "today"])
        is_trend_or_history = any(term in lower_query for term in ["trend", "trajectory", "history", "all", "over time", "progress", "first", "timeline"])

        parsed_dates = {elem.id: _extract_iso_date(elem.date) for elem in elements}
        valid_dates = [d for d in parsed_dates.values() if d != "0000-00-00"]
        max_date = max(valid_dates) if valid_dates else "0000-00-00"

        reranked_tuples = []

        for elem in elements:
            score = elem.score
            content_lower = elem.content.lower()
            elem_date = parsed_dates.get(elem.id, "0000-00-00")

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

            # 3. Extremum vs. Recency adjustments
            if is_extremum:
                # For highest/peak queries, boost abnormal/high status
                if any(term in lower_query for term in ["highest", "peak", "max"]):
                    if "high" in content_lower or "critical" in content_lower:
                        score += 0.10
                elif any(term in lower_query for term in ["lowest", "min"]):
                    if "low" in content_lower:
                        score += 0.10
            elif not is_trend_or_history:
                if is_explicit_recency:
                    if elem_date == max_date and max_date != "0000-00-00":
                        score += 0.12
                    elif elem_date[:4] == max_date[:4] and max_date != "0000-00-00":
                        score += 0.06
                else:
                    # General inquiry (e.g. "What is my cholesterol?"):
                    # Give moderate recency bonus so latest status is preferred over older readings
                    if elem_date == max_date and max_date != "0000-00-00":
                        score += 0.08
                    elif elem_date[:4] == max_date[:4] and max_date != "0000-00-00":
                        score += 0.04

            elem_copy = elem.model_copy()
            ranking_score = round(score, 3)
            elem_copy.score = min(1.0, ranking_score)
            reranked_tuples.append((ranking_score, elem_date, elem_copy))

        # Sort by updated ranking score descending, with date as secondary tie-breaker
        reranked_tuples.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [item[2] for item in reranked_tuples]
