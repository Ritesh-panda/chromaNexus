import pytest
from backend.app.ai.rag.fusion import FusedElement
from backend.app.ai.rag.reranker import ClinicalReranker
from backend.app.ai.rag.classifier import QueryIntent


def test_clinical_reranker_intent_boost():
    reranker = ClinicalReranker()

    elements = [
        FusedElement(
            id="1",
            source_type="report_chunk",
            title="Knee MRI Excerpt",
            date="2022-08-10",
            content="Grade II signal alteration posterior horn medial meniscus.",
            score=0.70
        ),
        FusedElement(
            id="2",
            source_type="structured_lab_result",
            title="Lipid Panel",
            date="2026-06-15",
            content="Total Cholesterol: 198 mg/dL.",
            score=0.70
        )
    ]

    # For a lab query, structured_lab_result should be boosted higher than report_chunk
    reranked_lab = reranker.rerank(elements, "What was my cholesterol level?", QueryIntent.LAB_HISTORY)
    assert reranked_lab[0].id == "2"

    # For an MRI query, report_chunk should be boosted higher than lab
    reranked_mri = reranker.rerank(elements, "What did the MRI say about the knee meniscus?", QueryIntent.REPORT_CONTENT)
    assert reranked_mri[0].id == "1"
