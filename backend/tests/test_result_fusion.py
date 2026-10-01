import pytest
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import SearchResult
from backend.app.ai.rag.structured_retriever import StructuredClinicalResult
from backend.app.ai.rag.fusion import ResultFusion, FusedElement


def test_result_fusion_combines_and_deduplicates():
    fusion = ResultFusion(max_items=5)

    structured = [
        StructuredClinicalResult(
            source_type="lab_result",
            source_id="lab_01",
            report_id="rep_002",
            title="Lab: Total Cholesterol",
            date="2021-06-12",
            content="Total Cholesterol: 242 mg/dL (High)",
            relevance_score=0.98
        )
    ]

    vector_results = [
        SearchResult(
            chunk=DocumentChunk(
                chunk_id="chk_01",
                document_id="rep_002",
                page_number=1,
                chunk_index=0,
                text="Quest Diagnostics Lipid Profile: Total Cholesterol 242 mg/dL.",
                metadata={"title": "Lipid Profile", "date": "2021-06-12"}
            ),
            score=0.95
        )
    ]

    fused = fusion.fuse(structured, vector_results)

    assert len(fused) == 2
    assert all(isinstance(x, FusedElement) for x in fused)
    assert fused[0].source_type == "structured_lab_result"
    assert fused[1].source_type == "report_chunk"
    assert fused[0].score >= fused[1].score
