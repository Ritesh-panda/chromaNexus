"""
Tests for ConversationQueryResolver — the general conversation-context mechanism for ChronaNexus AI Chat.

Covers:
  1. Overview / broad health-status questions
  2. Standalone specific queries (HbA1c, cholesterol, etc.)
  3. Pronoun follow-up:   "What is my HbA1c?"  -> "Has it improved?"
  4. Comparison follow-up: "What is my highest cholesterol?" -> "Has that improved?"
  5. Imaging elliptical follow-up: "What did my MRI show?" -> "Does the scan mention anything else?"
  6. Explicit topic continuation: "What about my knee?"
  7. Topic switch: HbA1c turn -> "What about my cholesterol?"
  8. History-less queries resolve normally (no crash, no follow-up flag)
  9. Medication follow-up via pronoun
  10. Full history format is bounded (<=6 messages, assistant messages truncated at 300 chars)
"""

import pytest
from backend.app.ai.rag.query_resolver import ConversationQueryResolver, ResolvedQuery
from backend.app.ai.rag.classifier import QueryIntent


@pytest.fixture
def resolver():
    return ConversationQueryResolver()


def _user(text):
    return {"sender": "user", "text": text}


def _ai(text):
    return {"sender": "ai", "text": text}


class TestOverviewQueries:

    def test_health_status_is_overview(self, resolver):
        resolved = resolver.resolve("What is my health status?")
        assert resolved.is_overview is True
        assert resolved.is_follow_up is False
        assert resolved.intent == QueryIntent.MIXED_CLINICAL
        assert resolved.active_topic == "health_overview"

    def test_how_am_i_is_overview(self, resolver):
        resolved = resolver.resolve("How am I right now according to my reports?")
        assert resolved.is_overview is True
        assert resolved.intent == QueryIntent.MIXED_CLINICAL

    def test_overall_health_is_overview(self, resolver):
        resolved = resolver.resolve("Give me an overall summary of my current health")
        assert resolved.is_overview is True

    def test_overview_with_history_retains_flag(self, resolver):
        history = [
            _user("What is my HbA1c?"),
            _ai("Your latest HbA1c is 7.8% from the June 2026 lab panel."),
        ]
        resolved = resolver.resolve("How am I right now?", conversation_history=history)
        assert resolved.is_overview is True
        assert resolved.intent == QueryIntent.MIXED_CLINICAL

    def test_overview_resolved_query_unchanged(self, resolver):
        q = "What is my health status?"
        resolved = resolver.resolve(q)
        assert resolved.resolved_query == q


class TestStandaloneQueries:

    def test_latest_hba1c_no_history(self, resolver):
        resolved = resolver.resolve("What is my latest HbA1c?")
        assert resolved.is_follow_up is False
        assert resolved.active_topic == "diabetes"
        assert resolved.intent in [QueryIntent.LAB_HISTORY, QueryIntent.MIXED_CLINICAL]

    def test_highest_cholesterol_no_history(self, resolver):
        resolved = resolver.resolve("What is my highest cholesterol reading?")
        assert resolved.is_follow_up is False
        assert resolved.active_topic == "cholesterol"

    def test_blood_pressure_medication(self, resolver):
        resolved = resolver.resolve("What dosage of Lisinopril was prescribed?")
        assert resolved.is_follow_up is False
        assert resolved.active_topic == "hypertension"

    def test_knee_mri_standalone(self, resolver):
        resolved = resolver.resolve("What did the MRI show about my right knee?")
        assert resolved.is_follow_up is False
        assert resolved.active_topic == "knee"

    def test_empty_query_returns_blank(self, resolver):
        resolved = resolver.resolve("")
        assert resolved.original_query == ""
        assert resolved.is_follow_up is False
        assert resolved.is_overview is False


class TestPronounFollowUp:

    def test_has_it_improved_after_hba1c(self, resolver):
        history = [
            _user("What is my latest HbA1c?"),
            _ai("Your latest HbA1c is 7.8% measured in June 2026 from the Metro General Metabolic Panel."),
        ]
        resolved = resolver.resolve("Has it improved?", conversation_history=history)
        assert resolved.is_follow_up is True
        assert resolved.active_topic == "diabetes"
        assert resolved.intent in [QueryIntent.LAB_HISTORY, QueryIntent.MIXED_CLINICAL]
        rq = resolved.resolved_query.lower()
        assert "diabetes" in rq or "hba1c" in rq

    def test_is_it_normal_after_hba1c(self, resolver):
        history = [
            _user("What is my latest HbA1c?"),
            _ai("Your HbA1c is 7.8%."),
        ]
        resolved = resolver.resolve("Is it normal?", conversation_history=history)
        assert resolved.is_follow_up is True
        assert resolved.active_topic == "diabetes"

    def test_that_pronoun_after_cholesterol(self, resolver):
        history = [
            _user("What is my highest cholesterol?"),
            _ai("Your highest recorded Total Cholesterol was 242 mg/dL in June 2021."),
        ]
        resolved = resolver.resolve("Has that improved?", conversation_history=history)
        assert resolved.is_follow_up is True
        assert resolved.active_topic == "cholesterol"
        assert resolved.intent in [QueryIntent.LAB_HISTORY, QueryIntent.MIXED_CLINICAL]

    def test_this_pronoun_after_hypertension(self, resolver):
        history = [
            _user("What is my blood pressure medication?"),
            _ai("You have been prescribed Lisinopril 10 mg daily."),
        ]
        resolved = resolver.resolve("Has this changed?", conversation_history=history)
        assert resolved.is_follow_up is True
        assert resolved.active_topic == "hypertension"

    def test_they_pronoun_after_medications(self, resolver):
        history = [
            _user("What medications am I taking?"),
            _ai("You are prescribed Metformin 500 mg twice daily and Lisinopril 10 mg daily."),
        ]
        resolved = resolver.resolve("Are they still prescribed?", conversation_history=history)
        assert resolved.is_follow_up is True
        assert resolved.active_topic is not None


class TestComparisonFollowUp:

    def test_comparison_includes_trend_terms(self, resolver):
        history = [
            _user("What is my highest recorded HbA1c?"),
            _ai("Your highest HbA1c was 9.2% measured in March 2021."),
        ]
        resolved = resolver.resolve("Has it gotten better?", conversation_history=history)
        assert resolved.is_follow_up is True
        rq = resolved.resolved_query.lower()
        assert "trend" in rq or "trajectory" in rq

    def test_stable_comparison_word(self, resolver):
        history = [
            _user("What is my cholesterol?"),
            _ai("Your Total Cholesterol is 198 mg/dL as of June 2026."),
        ]
        resolved = resolver.resolve("Is it stable?", conversation_history=history)
        assert resolved.is_follow_up is True
        assert resolved.active_topic == "cholesterol"

    def test_comparison_without_prior_topic_stays_standalone(self, resolver):
        resolved = resolver.resolve("Has it improved?", conversation_history=[])
        assert isinstance(resolved, ResolvedQuery)
        assert resolved.is_follow_up is False


class TestImagingFollowUp:

    def test_scan_follow_up_after_knee_mri(self, resolver):
        history = [
            _user("What did the MRI show about my right knee meniscus?"),
            _ai("The MRI report from Metro General shows a medial meniscus grade II strain."),
        ]
        resolved = resolver.resolve("Does the scan mention anything else?", conversation_history=history)
        assert resolved.is_follow_up is True
        assert resolved.active_topic == "knee"
        assert resolved.intent == QueryIntent.REPORT_CONTENT

    def test_imaging_follow_up_without_prior_topic_handles_gracefully(self, resolver):
        resolved = resolver.resolve("What does the scan say?", conversation_history=[])
        assert isinstance(resolved, ResolvedQuery)


class TestExplicitTopicContinuation:

    def test_what_about_cholesterol(self, resolver):
        history = [
            _user("What is my HbA1c?"),
            _ai("Your HbA1c is 7.8%."),
        ]
        resolved = resolver.resolve("What about my cholesterol?", conversation_history=history)
        assert resolved.active_topic == "cholesterol"
        assert resolved.is_follow_up is True

    def test_what_about_knee(self, resolver):
        history = [
            _user("What medications am I on?"),
            _ai("You are on Metformin and Lisinopril."),
        ]
        resolved = resolver.resolve("What about my knee injury?", conversation_history=history)
        assert resolved.active_topic == "knee"

    def test_explicit_topic_expansion_included(self, resolver):
        resolved = resolver.resolve("What about my cholesterol?")
        rq = resolved.resolved_query.lower()
        assert "cholesterol" in rq


class TestTopicSwitch:

    def test_hba1c_then_cholesterol_switches_topic(self, resolver):
        history = [
            _user("What is my HbA1c?"),
            _ai("Your HbA1c is 7.8%."),
            _user("Has it improved?"),
            _ai("Your HbA1c was 9.2% in 2021 and is now 7.8% - improved."),
        ]
        resolved = resolver.resolve("What is my total cholesterol?", conversation_history=history)
        assert resolved.active_topic == "cholesterol"

    def test_cholesterol_then_hypertension(self, resolver):
        history = [
            _user("What is my cholesterol?"),
            _ai("Total Cholesterol 198 mg/dL."),
        ]
        resolved = resolver.resolve("What is my blood pressure medication?", conversation_history=history)
        assert resolved.active_topic == "hypertension"


class TestNoHistory:

    def test_none_history_does_not_crash(self, resolver):
        resolved = resolver.resolve("What is my HbA1c?", conversation_history=None)
        assert isinstance(resolved, ResolvedQuery)
        assert resolved.active_topic == "diabetes"

    def test_empty_list_history_does_not_crash(self, resolver):
        resolved = resolver.resolve("What is my cholesterol?", conversation_history=[])
        assert isinstance(resolved, ResolvedQuery)
        assert resolved.active_topic == "cholesterol"

    def test_formatted_history_is_empty_string(self, resolver):
        resolved = resolver.resolve("What is my HbA1c?", conversation_history=None)
        assert resolved.formatted_history == ""


class TestHistoryFormatting:

    def test_history_bounded_to_last_6_messages(self, resolver):
        history = [
            _user("msg 1"), _ai("resp 1"),
            _user("msg 2"), _ai("resp 2"),
            _user("msg 3"), _ai("resp 3"),
            _user("msg 4"), _ai("resp 4"),
        ]
        resolved = resolver.resolve("Has it improved?", conversation_history=history)
        assert "msg 1" not in resolved.formatted_history

    def test_ai_message_truncated_at_300_chars(self, resolver):
        long_response = "A" * 500
        history = [_user("What is my HbA1c?"), _ai(long_response)]
        resolved = resolver.resolve("Has it improved?", conversation_history=history)
        for line in resolved.formatted_history.split("\n"):
            if "Assistant:" in line:
                text_part = line[len("Assistant: "):]
                assert len(text_part) <= 303, f"Line too long: {len(text_part)} chars"

    def test_history_formatted_with_patient_and_assistant_roles(self, resolver):
        history = [
            _user("What is my HbA1c?"),
            _ai("Your HbA1c is 7.8%."),
        ]
        resolved = resolver.resolve("Has it improved?", conversation_history=history)
        # Neutral Q:/A: labels are used to prevent LLM from echoing "Patient:" in its answer
        assert "Q:" in resolved.formatted_history
        assert "A:" in resolved.formatted_history


class TestKeywordExtraction:

    def test_diabetes_query_has_relevant_keywords(self, resolver):
        resolved = resolver.resolve("What is my HbA1c?")
        kw_lower = [k.lower() for k in resolved.keywords]
        assert any(k in kw_lower for k in ["hba1c", "a1c", "diabetes", "glucose", "glycemic"])

    def test_cholesterol_query_has_relevant_keywords(self, resolver):
        resolved = resolver.resolve("What is my cholesterol?")
        kw_lower = [k.lower() for k in resolved.keywords]
        assert any(k in kw_lower for k in ["cholesterol", "lipid", "ldl", "hdl"])

    def test_follow_up_retains_prior_topic_keywords(self, resolver):
        history = [
            _user("What is my HbA1c?"),
            _ai("Your HbA1c is 7.8%."),
        ]
        resolved = resolver.resolve("Has it improved?", conversation_history=history)
        kw_lower = [k.lower() for k in resolved.keywords]
        assert any(k in kw_lower for k in ["hba1c", "a1c", "diabetes", "glucose"])

    def test_overview_has_overview_keywords(self, resolver):
        resolved = resolver.resolve("What is my health status?")
        kw_lower = [k.lower() for k in resolved.keywords]
        assert any(k in kw_lower for k in ["health", "status", "overview", "summary"])


# ==============================================================================
# Regression: Comparison follow-up topic priority
# ==============================================================================

class TestComparisonFollowUpPriority:
    """
    Regression suite for the two-pass _find_prior_topic fix.
    Bug: AI answers mention multiple domains causing an older topic to override the current one.
    Fix: user messages scanned first (highest priority), AI messages second (fallback).
    """

    def test_cholesterol_then_has_that_improved_resolves_to_cholesterol(self, resolver):
        history = [
            _user("What about my cholesterol?"),
            _ai("Your latest recorded Total Cholesterol is 198 mg/dL (June 15, 2026)."),
        ]
        resolved = resolver.resolve("Has that improved?", conversation_history=history)
        assert resolved.active_topic == "cholesterol", (
            f"Expected 'cholesterol', got '{resolved.active_topic}'. "
            "'Has that improved?' after cholesterol MUST resolve to cholesterol."
        )
        assert resolved.is_follow_up is True

    def test_diabetes_then_has_it_improved_resolves_to_diabetes(self, resolver):
        history = [
            _user("What about my diabetes?"),
            _ai("Your records show Type 2 Diabetes. Latest HbA1c: 6.7%."),
        ]
        resolved = resolver.resolve("Has it improved?", conversation_history=history)
        assert resolved.active_topic == "diabetes", (
            f"Expected 'diabetes', got '{resolved.active_topic}'."
        )
        assert resolved.is_follow_up is True

    def test_mri_then_cholesterol_then_has_that_improved_is_cholesterol(self, resolver):
        """Three-turn: MRI -> cholesterol -> 'Has that improved?' must equal cholesterol."""
        history = [
            _user("What did my MRI show?"),
            _ai(
                "The MRI of your right knee (August 10, 2022) showed Grade II degenerative "
                "signal changes in the posterior horn of the medial meniscus. "
                "No displaced meniscal flap tear was identified."
            ),
            _user("What about my cholesterol?"),
            _ai(
                "Your latest recorded Total Cholesterol is 198 mg/dL (June 15, 2026). "
                "You are prescribed Atorvastatin 10 mg daily."
            ),
        ]
        resolved = resolver.resolve("Has that improved?", conversation_history=history)
        assert resolved.active_topic == "cholesterol", (
            f"Expected 'cholesterol', got '{resolved.active_topic}'. "
            "After 'What about my cholesterol?' the follow-up must remain cholesterol."
        )
        assert resolved.is_follow_up is True
        assert "meniscus" not in resolved.resolved_query.lower(), \
            "Resolved query must NOT contain knee/meniscus terms."

    def test_long_history_user_message_priority_wins(self, resolver):
        """Full 10-message history: most-recent user question (cholesterol) must win."""
        history = [
            _user("What did my MRI show?"),
            _ai("Your knee MRI showed Grade II medial meniscus changes."),
            _user("Does it mention a tear?"),
            _ai("No displaced meniscal flap tear in the knee."),
            _user("What kind of tear does it mention?"),
            _ai("The knee MRI does not mention a specific tear type."),
            _user("What about my diabetes?"),
            _ai("Your HbA1c is 6.7% as of June 15, 2026. Type 2 Diabetes Mellitus."),
            _user("What about my cholesterol?"),
            _ai("Your Total Cholesterol is 198 mg/dL. Atorvastatin 10 mg daily."),
        ]
        resolved = resolver.resolve("Has that improved?", conversation_history=history)
        assert resolved.active_topic == "cholesterol", (
            f"Expected 'cholesterol', got '{resolved.active_topic}'."
        )


class TestFindPriorTopicPriority:
    """Unit tests for the two-pass _find_prior_topic implementation."""

    def test_user_message_beats_ai_message_different_topic(self, resolver):
        history = [
            _user("What is my cholesterol?"),
            _ai("Your Total Cholesterol is 198 mg/dL. No knee or meniscus concerns."),
        ]
        assert resolver._find_prior_topic(history) == "cholesterol"

    def test_user_message_beats_ai_with_earlier_taxonomy_keyword(self, resolver):
        """AI mentions HbA1c (diabetes = first in taxonomy) but user asked cholesterol."""
        history = [
            _user("What about my cholesterol?"),
            _ai("Cholesterol is 198 mg/dL. HbA1c was 6.7% last check."),
        ]
        assert resolver._find_prior_topic(history) == "cholesterol"

    def test_empty_history_returns_none(self, resolver):
        assert resolver._find_prior_topic([]) is None

    def test_message_without_sender_key_defaults_to_user(self, resolver):
        history = [{"text": "What about my diabetes?"}]
        assert resolver._find_prior_topic(history) == "diabetes"


class TestMissingDataCitationSuppression:
    """Tests for RAGPipeline._answer_indicates_missing_data."""

    @pytest.fixture
    def pipeline(self):
        from backend.app.ai.rag.pipeline import RAGPipeline
        from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider
        return RAGPipeline(llm=MockDeterministicLLMProvider())

    def test_do_not_contain_triggers(self, pipeline):
        assert pipeline._answer_indicates_missing_data(
            "The available records do not contain a kidney-function result."
        ) is True

    def test_does_not_contain_triggers(self, pipeline):
        assert pipeline._answer_indicates_missing_data(
            "The records do not contain information about kidney function."
        ) is True

    def test_records_do_not_include_triggers(self, pipeline):
        assert pipeline._answer_indicates_missing_data(
            "Your records do not include any vitamin D measurements."
        ) is True

    def test_not_documented_triggers(self, pipeline):
        assert pipeline._answer_indicates_missing_data(
            "Kidney function is not documented in the available records."
        ) is True

    def test_normal_answer_does_not_trigger(self, pipeline):
        assert pipeline._answer_indicates_missing_data(
            "Your latest recorded Total Cholesterol is 198 mg/dL (June 15, 2026)."
        ) is False

    def test_hba1c_answer_does_not_trigger(self, pipeline):
        assert pipeline._answer_indicates_missing_data(
            "Your HbA1c is 6.7% as of June 15, 2026."
        ) is False

    def test_empty_answer_does_not_crash(self, pipeline):
        assert pipeline._answer_indicates_missing_data("") is False
