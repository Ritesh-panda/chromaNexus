import pytest
from backend.app.ai.rag.classifier import QueryClassifier, QueryIntent


def test_classify_lab_intent():
    classifier = QueryClassifier()
    res = classifier.classify("What was my highest recorded cholesterol reading?")
    assert res.primary_intent == QueryIntent.LAB_HISTORY
    assert "cholesterol" in res.keywords_matched


def test_classify_medication_intent():
    classifier = QueryClassifier()
    res = classifier.classify("What dosage of Metformin and Lisinopril was prescribed?")
    assert res.primary_intent == QueryIntent.MEDICATION_HISTORY
    assert any(k in res.keywords_matched for k in ["metformin", "lisinopril", "dosage"])


def test_classify_mri_report_intent():
    classifier = QueryClassifier()
    res = classifier.classify("What did the MRI scan show about my right knee meniscus?")
    assert res.primary_intent == QueryIntent.REPORT_CONTENT
    assert "mri" in res.keywords_matched
    assert "meniscus" in res.keywords_matched


def test_classify_timeline_intent():
    classifier = QueryClassifier()
    res = classifier.classify("When in 2019 was I hospitalized for Dengue Fever?")
    assert res.primary_intent in [QueryIntent.TIMELINE, QueryIntent.MIXED_CLINICAL]
    assert "2019" in res.keywords_matched or "when" in res.keywords_matched


def test_classify_mixed_clinical_intent():
    classifier = QueryClassifier()
    res = classifier.classify("How did my HbA1c lab level change after I started taking Metformin?")
    assert res.primary_intent == QueryIntent.MIXED_CLINICAL
    assert res.is_hybrid_required is True
    assert QueryIntent.LAB_HISTORY in res.intents
    assert QueryIntent.MEDICATION_HISTORY in res.intents
