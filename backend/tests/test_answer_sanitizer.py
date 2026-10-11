"""
Tests for RAGPipeline._sanitize_answer — the defense-in-depth post-processor
that strips LLM response artifacts without altering medical content.
"""

import pytest
from backend.app.ai.rag.pipeline import RAGPipeline
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider


@pytest.fixture
def pipeline():
    return RAGPipeline(llm=MockDeterministicLLMProvider())


class TestSanitizeAnswer:

    def test_strips_patient_echo_prefix(self, pipeline):
        """'Patient: What about my diabetes?' on first line is removed."""
        raw = "Patient: What about my diabetes?\n\nYour records show Type 2 Diabetes."
        result = pipeline._sanitize_answer(raw, "What about my diabetes?")
        assert not result.startswith("Patient:")
        assert "Type 2 Diabetes" in result

    def test_strips_user_echo_prefix(self, pipeline):
        raw = "User: What is my HbA1c?\nYour latest HbA1c is 7.8%."
        result = pipeline._sanitize_answer(raw, "What is my HbA1c?")
        assert not result.startswith("User:")
        assert "7.8%" in result

    def test_strips_q_echo_prefix(self, pipeline):
        raw = "Q: Has it improved?\nYour HbA1c improved from 9.2% to 7.8%."
        result = pipeline._sanitize_answer(raw, "Has it improved?")
        assert not result.startswith("Q:")
        assert "9.2%" in result

    def test_preserves_answer_with_no_echo(self, pipeline):
        """Answers that start correctly are not modified."""
        raw = "Your records show Type 2 Diabetes Mellitus diagnosed on September 18, 2023."
        result = pipeline._sanitize_answer(raw, "What about my diabetes?")
        assert result == raw

    def test_strips_based_on_conversation_opener(self, pipeline):
        raw = "Based on our conversation history, your HbA1c is 7.8%."
        result = pipeline._sanitize_answer(raw, "What is my HbA1c?")
        assert not result.lower().startswith("based on our conversation")
        assert "7.8%" in result

    def test_strips_as_discussed_opener(self, pipeline):
        raw = "As we discussed earlier, your cholesterol was 242 mg/dL."
        result = pipeline._sanitize_answer(raw, "What is my cholesterol?")
        assert not result.lower().startswith("as we discussed")
        assert "242 mg/dL" in result

    def test_strips_as_mentioned_opener(self, pipeline):
        raw = "As mentioned previously, your latest HbA1c is 6.7%."
        result = pipeline._sanitize_answer(raw, "What is my HbA1c?")
        assert not result.lower().startswith("as mentioned")
        assert "6.7%" in result

    def test_preserves_non_echo_patient_reference_in_body(self, pipeline):
        """'Patient: Alex Vance' in the middle of an answer body is NOT stripped."""
        raw = "Your records show the following.\nPatient: Alex Vance | HbA1c 7.8%."
        result = pipeline._sanitize_answer(raw, "What is my HbA1c?")
        # The first line "Your records show..." is not an echo so nothing is removed
        assert "Alex Vance" in result

    def test_empty_answer_returns_empty(self, pipeline):
        assert pipeline._sanitize_answer("", "anything") == ""

    def test_capitalizes_remainder_after_meta_strip(self, pipeline):
        """After stripping a meta opener, the first character of the remainder is capitalized."""
        raw = "Based on our conversation history, your HbA1c is 7.8%."
        result = pipeline._sanitize_answer(raw, "What is my HbA1c?")
        assert result[0].isupper()
