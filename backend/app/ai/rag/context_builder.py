from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field
from backend.app.ai.retrieval import SearchResult
from backend.app.ai.rag.fusion import FusedElement


class Citation(BaseModel):
    report_id: str = Field(alias="reportId")
    report_title: str = Field(alias="reportTitle")
    date: str
    excerpt: str
    confidence_score: float = Field(default=0.95, alias="confidenceScore")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


class RAGContext(BaseModel):
    formatted_context: str
    citations: List[Dict[str, Any]]
    total_sources: int


class RAGContextBuilder:
    """
    Constructs structured LLM context and auditable citations from:
    - Pure vector SearchResults
    - Fused hybrid elements (Structured DB labs/meds/diagnoses + Vector report chunks)
    """

    def __init__(self, max_context_chars: int = 4000):
        self.max_context_chars = max_context_chars

    def build_context(
        self,
        items: Union[List[SearchResult], List[FusedElement]]
    ) -> RAGContext:
        if not items:
            return RAGContext(
                formatted_context="No relevant patient medical records found matching this query.",
                citations=[],
                total_sources=0
            )

        context_blocks: List[str] = []
        citations: List[Dict[str, Any]] = []
        current_len = 0
        seen_citations = set()

        for idx, item in enumerate(items, start=1):
            if isinstance(item, FusedElement):
                # Hybrid Fused Element formatting
                source_tag = item.source_type.upper().replace("_", " ")
                header = f"[{source_tag} #{idx} | {item.title} | Date: {item.date}]"
                block = f"{header}\n{item.content}\n"

                doc_id = item.report_id or item.id
                report_title = item.title
                date = item.date
                score = item.score
                excerpt = item.content[:200] + "..." if len(item.content) > 200 else item.content

            else:
                # Vector SearchResult formatting
                chunk = item.chunk
                meta = chunk.metadata
                doc_id = meta.get("document_id", chunk.document_id)
                report_title = meta.get("title", meta.get("report_title", f"Report #{doc_id}"))
                date = meta.get("date", meta.get("report_date", "Undated"))
                hospital = meta.get("hospital_name", "")
                page = chunk.page_number
                score = round(item.score, 2)

                source_header = f"[REPORT EXCERPT #{idx} | {report_title} ({date}) | Page {page}"
                if hospital:
                    source_header += f" | {hospital}"
                source_header += "]"

                block = f"{source_header}\n{chunk.text}\n"
                excerpt = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text

            if current_len + len(block) > self.max_context_chars and idx > 1:
                break

            context_blocks.append(block)
            current_len += len(block)

            # Build Citation
            cit_key = f"{doc_id}_{date}"
            if cit_key not in seen_citations:
                seen_citations.add(cit_key)
                citations.append({
                    "reportId": str(doc_id),
                    "reportTitle": str(report_title),
                    "date": str(date),
                    "excerpt": excerpt,
                    "confidenceScore": float(max(0.85, score))
                })

        formatted = "\n\n".join(context_blocks)

        return RAGContext(
            formatted_context=formatted,
            citations=citations,
            total_sources=len(context_blocks)
        )
