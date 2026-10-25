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
    response = pipeline.query("", patient_id="pat_001")
    assert "Please provide a valid question" in response.answer
    assert response.sources_used == 0
    assert len(response.citations) == 0


def test_rag_pipeline_no_records_fallback():
    # Empty store
    store = InMemoryVectorStore()
    pipeline = RAGPipeline(retriever=store, llm=MockDeterministicLLMProvider())
    response = pipeline.query("What surgery did I have in 2015?", patient_id="pat_001")

    assert isinstance(response, RAGResponse)
    assert response.reasoning_type == "inference"
    assert response.sources_used == 0
    assert len(response.citations) == 0


def test_rag_pipeline_missing_patient_id_fails_closed():
    """Requirement 1: Missing patient identity must fail closed with explicit safe error."""
    pipeline = RAGPipeline(llm=MockDeterministicLLMProvider())
    
    # Empty string patient_id
    resp_empty = pipeline.query("What was my cholesterol level?", patient_id="")
    assert resp_empty.reasoning_type == "error"
    assert resp_empty.sources_used == 0
    assert len(resp_empty.citations) == 0
    assert "patient identity is required" in resp_empty.answer.lower()
    
    # None patient_id
    resp_none = pipeline.query("What was my cholesterol level?", patient_id=None)
    assert resp_none.reasoning_type == "error"
    assert resp_none.sources_used == 0
    assert len(resp_none.citations) == 0
    assert "patient identity is required" in resp_none.answer.lower()


def test_rag_pipeline_mixed_supported_and_unsupported_claim():
    """Requirement 3: Mixed claim in a single compound sentence must preserve supported fact and rewrite unsupported diagnosis."""
    pipeline = RAGPipeline(llm=MockDeterministicLLMProvider())
    citations = [{
        "reportId": "rep_cmp_01",
        "reportTitle": "Comprehensive Metabolic Panel",
        "date": "2026-10-12",
        "facility": "Metro Health",
        "excerpt": "Comprehensive Metabolic Panel (2026-10-12) - Metro Health\nPotassium: 5.8 mEq/L [HIGH] (Ref: 3.5-5.0)"
    }]

    answer = "Your potassium level was 5.8 mEq/L at Metro Health on 2026-10-12, and you have severe cardiac ischemia."
    rec_ans, rec_cits = pipeline._reconcile_and_ground_answer(answer, citations)

    # Supported fact must be preserved and cited
    assert len(rec_cits) == 1
    assert rec_cits[0]["reportId"] == "rep_cmp_01"
    assert "5.8 mEq/L" in rec_ans
    
    # Unsupported diagnosis must NEVER remain as an affirmative fact
    assert "you have severe cardiac ischemia" not in rec_ans.lower()
    assert "No clinical documentation of severe cardiac ischemia" in rec_ans


def test_rag_pipeline_unsupported_diagnosis_rewritten_safely():
    """Requirement 3: Unsupported diagnosis must be rewritten as explicit absence of documentation."""
    pipeline = RAGPipeline(llm=MockDeterministicLLMProvider())
    citations = [{
        "reportId": "rep_cbc_01",
        "reportTitle": "Complete Blood Count",
        "date": "2026-10-10",
        "facility": "Metro Health",
        "excerpt": "Complete Blood Count (2026-10-10)\nWBC: 7.2 x10^3/uL"
    }]

    answer = "You were diagnosed with stage 4 chronic kidney disease."
    rec_ans, rec_cits = pipeline._reconcile_and_ground_answer(answer, citations)

    assert len(rec_cits) == 0
    assert "you were diagnosed with" not in rec_ans.lower()
    assert "No clinical documentation of stage chronic kidney disease" in rec_ans or "No clinical documentation of" in rec_ans


def test_rag_pipeline_unsupported_medication_instruction_rewritten_safely():
    """Requirement 3: Unsupported medication instruction must not stand as patient-specific fact."""
    pipeline = RAGPipeline(llm=MockDeterministicLLMProvider())
    citations = [{
        "reportId": "rep_cbc_01",
        "reportTitle": "Complete Blood Count",
        "date": "2026-10-10",
        "facility": "Metro Health",
        "excerpt": "Complete Blood Count (2026-10-10)\nWBC: 7.2 x10^3/uL"
    }]

    answer = "Start taking 50mg of prednisone daily for inflammation."
    rec_ans, rec_cits = pipeline._reconcile_and_ground_answer(answer, citations)

    assert len(rec_cits) == 0
    assert "start taking 50mg of prednisone" not in rec_ans.lower()
    assert "No clinical documentation of" in rec_ans
    assert "prednisone" in rec_ans.lower()


def test_rag_pipeline_fully_unsupported_answer_fails_safe():
    """Requirement 3: Fully fabricated answer must receive 0 citations and be completely disclaimed."""
    pipeline = RAGPipeline(llm=MockDeterministicLLMProvider())
    citations = [{
        "reportId": "rep_cbc_01",
        "reportTitle": "Complete Blood Count",
        "date": "2026-10-10",
        "facility": "Metro Health",
        "excerpt": "Complete Blood Count (2026-10-10)\nWBC: 7.2 x10^3/uL"
    }]

    answer = "You underwent coronary artery bypass surgery in 2024 and have active heart failure."
    rec_ans, rec_cits = pipeline._reconcile_and_ground_answer(answer, citations)

    assert len(rec_cits) == 0
    assert "you underwent coronary artery bypass" not in rec_ans.lower()
    assert "No clinical documentation" in rec_ans
