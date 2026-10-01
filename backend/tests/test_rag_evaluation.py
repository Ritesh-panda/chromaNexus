import pytest
from backend.app.ai.rag.evaluator import RAGEvaluator, EvaluationTestCase
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider


from backend.app.ai.rag.classifier import QueryIntent


def test_rag_evaluation_single_case():
    mock_llm = MockDeterministicLLMProvider()
    pipeline = RAGPipeline(llm=mock_llm)
    evaluator = RAGEvaluator(pipeline=pipeline)
    case = EvaluationTestCase(
        id="test_chol_01",
        category="Lab",
        query="When was my highest recorded total cholesterol?",
        expected_intent=QueryIntent.LAB_HISTORY,
        expected_source_types=["structured_lab_result"],
        expected_keywords_in_answer=["242 mg/dL", "June 12, 2021"],
        expected_citations=[]
    )



    res = evaluator.evaluate_test_case(case)
    assert res.passed is True
    assert res.keywords_matched is True
    assert res.hallucination_detected is False


def test_rag_evaluation_benchmark_suite(db_session):
    pipeline = RAGPipeline(
        llm=MockDeterministicLLMProvider(),
        db_session=db_session
    )
    evaluator = RAGEvaluator(pipeline=pipeline)
    summary = evaluator.run_all(patient_id="pat_001")

    assert summary["total_cases"] == 10
    assert summary["passed_cases"] >= 8
    assert summary["pass_rate"] >= 80.0
