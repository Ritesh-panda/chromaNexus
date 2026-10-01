import pytest
from backend.app.ai.clinical_extractor.rule_based import RuleBasedClinicalExtractor
from backend.app.ai.clinical_extractor.llm_extractor import LLMClinicalExtractor
from backend.app.ai.clinical_extractor import get_clinical_extractor
from backend.app.ai.llm.mock_provider import MockDeterministicLLMProvider
from backend.app.ai.extractors.pdf_extractor import ExtractedPage


def test_rule_based_extractor():
    extractor = RuleBasedClinicalExtractor()
    sample_text = (
        "Patient: Alex Vance. Date: 2024-03-15.\n"
        "Diagnosed with Type 2 Diabetes and Hypertension.\n"
        "Prescribed Metformin 500mg daily and Lisinopril 10mg.\n"
        "Recent Fasting Blood Glucose: 135 mg/dL. HbA1c: 6.9 %.\n"
        "Resting Blood Pressure: 130/85 mmHg."
    )
    
    entities = extractor.extract_entities(text=sample_text, document_id="doc-123")
    assert len(entities) > 0
    
    categories = [e.category for e in entities]
    assert "disease" in categories
    assert "medication" in categories
    assert "lab_value" in categories
    
    for entity in entities:
        assert entity.source_document_id == "doc-123"
        assert entity.confidence > 0.0
        assert entity.extraction_method == "rule_based"


def test_llm_extractor_fallback():
    mock_llm = MockDeterministicLLMProvider()
    extractor = LLMClinicalExtractor(llm_provider=mock_llm)
    
    sample_text = "Patient has Asthma and takes Albuterol 90mcg."
    entities = extractor.extract_entities(text=sample_text, document_id="doc-456")
    
    assert len(entities) > 0


def test_extractor_preserves_page_provenance():
    extractor = RuleBasedClinicalExtractor()
    page = ExtractedPage(page_number=2, text="Blood Pressure: 120/80 mmHg", character_count=30)
    entities = extractor.extract_entities(
        text="Blood Pressure: 120/80 mmHg",
        document_id="doc-789",
        pages=[page]
    )
    
    assert len(entities) > 0
    assert entities[0].source_document_id == "doc-789"
    assert entities[0].page_number == 2
    assert entities[0].excerpt != ""

