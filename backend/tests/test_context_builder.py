import pytest
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import SearchResult
from backend.app.ai.rag.context_builder import RAGContextBuilder, RAGContext


def test_context_builder_empty_results():
    builder = RAGContextBuilder()
    context = builder.build_context([])
    assert isinstance(context, RAGContext)
    assert context.total_sources == 0
    assert len(context.citations) == 0
    assert "No relevant patient medical records found" in context.formatted_context


def test_context_builder_preserves_citations_and_metadata():
    builder = RAGContextBuilder()
    search_results = [
        SearchResult(
            chunk=DocumentChunk(
                chunk_id="chk_01",
                document_id="rep_002",
                page_number=1,
                chunk_index=0,
                text="Lipid Profile: Total Cholesterol 242 mg/dL. Fasting Glucose 104 mg/dL.",
                metadata={
                    "title": "Lipid Profile & Glucose Screening",
                    "date": "2021-06-12",
                    "hospital_name": "Quest Diagnostics"
                }
            ),
            score=0.98
        ),
        SearchResult(
            chunk=DocumentChunk(
                chunk_id="chk_02",
                document_id="rep_008",
                page_number=2,
                chunk_index=1,
                text="Comprehensive Metabolic & Lipid Panel: Total Cholesterol 198 mg/dL. LDL 112 mg/dL.",
                metadata={
                    "title": "Comprehensive Metabolic & Lipid Panel",
                    "date": "2026-06-15",
                    "hospital_name": "Metro General Hospital"
                }
            ),
            score=0.96
        )
    ]

    rag_context = builder.build_context(search_results)
    assert rag_context.total_sources == 2
    assert len(rag_context.citations) == 2

    cit1 = rag_context.citations[0]
    assert cit1["reportId"] == "rep_002"
    assert cit1["reportTitle"] == "Lipid Profile & Glucose Screening"
    assert cit1["date"] == "2021-06-12"
    assert "242 mg/dL" in cit1["excerpt"]
    assert cit1["confidenceScore"] >= 0.95

    assert "Quest Diagnostics" in rag_context.formatted_context
    assert "Metro General Hospital" in rag_context.formatted_context
