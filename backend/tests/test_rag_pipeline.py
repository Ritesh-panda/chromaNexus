import pytest
from backend.app.ai.chunker import DocumentChunk
from backend.app.ai.retrieval import InMemoryVectorStore
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider
from backend.app.ai.rag.pipeline import RAGPipeline, RAGResponse


def test_rag_pipeline_end_to_end():
    # 1. Setup in-memory retriever with sample medical chunks
    store = InMemoryVectorStore()
    chunks = [
        DocumentChunk(
            chunk_id="chk_rep_002",
            document_id="rep_002",
            page_number=1,
            chunk_index=0,
            text="Quest Diagnostics Lipid Profile: Total Cholesterol 242 mg/dL on June 12, 2021.",
            metadata={
                "title": "Lipid Profile & Glucose Screening",
                "date": "2021-06-12",
                "patient_id": "pat_001",
                "hospital_name": "Quest Diagnostics"
            }
        ),
        DocumentChunk(
            chunk_id="chk_rep_008",
            document_id="rep_008",
            page_number=1,
            chunk_index=0,
            text="Metro General Metabolic & Lipid Panel: Total Cholesterol 198 mg/dL on June 15, 2026.",
            metadata={
                "title": "Comprehensive Metabolic & Lipid Panel",
                "date": "2026-06-15",
                "patient_id": "pat_001",
                "hospital_name": "Metro General Hospital"
            }
        )
    ]
    store.add_documents(chunks)

    # 2. Setup pipeline with mock LLM
    mock_llm = MockDeterministicLLMProvider()
    pipeline = RAGPipeline(retriever=store, llm=mock_llm)

    # 3. Execute query
    response = pipeline.query("When was my highest recorded cholesterol level?", patient_id="pat_001")

    assert isinstance(response, RAGResponse)
    assert response.reasoning_type == "fact"
    assert response.sources_used > 0
    assert len(response.citations) > 0
    assert "242 mg/dL" in response.answer
    assert response.citations[0]["reportId"] in ["rep_002", "rep_008"]


def test_rag_pipeline_empty_query():
    pipeline = RAGPipeline(llm=MockDeterministicLLMProvider())
    response = pipeline.query("")
    assert "Please provide a valid question" in response.answer
    assert response.sources_used == 0
    assert len(response.citations) == 0


def test_rag_pipeline_no_records_fallback():
    # Empty store
    store = InMemoryVectorStore()
    pipeline = RAGPipeline(retriever=store, llm=MockDeterministicLLMProvider())
    response = pipeline.query("What surgery did I have in 2015?")

    assert isinstance(response, RAGResponse)
    assert response.reasoning_type == "inference"
    assert response.sources_used == 0
    assert len(response.citations) == 0
