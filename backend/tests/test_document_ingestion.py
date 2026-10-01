import pytest
from backend.app.ai.document_ingestion import DocumentIngestionPipeline, IngestionResult
from backend.app.ai.retrieval import InMemoryVectorStore


def test_document_ingestion_pipeline():
    vector_store = InMemoryVectorStore()
    pipeline = DocumentIngestionPipeline(vector_store=vector_store)

    raw_text = """
    QUEST DIAGNOSTICS CLINICAL REPORT
    Patient: Alex Vance | Date: 2021-06-12
    Lipid Panel Results:
    Total Cholesterol: 242 mg/dL (High, Reference: <200)
    Fasting Blood Sugar: 104 mg/dL
    End of Report.
    """

    res = pipeline.ingest_document(
        raw_text=raw_text,
        document_id="rep_002",
        metadata={"category": "blood_report", "patient_id": "pat_001"}
    )

    assert isinstance(res, IngestionResult)
    assert res.success is True
    assert res.total_chunks >= 1
    assert res.total_characters > 0

    # Search in vector store
    search_res = vector_store.similarity_search("What was my total cholesterol?", top_k=1)
    assert len(search_res) == 1
    assert "242 mg/dL" in search_res[0].chunk.text
