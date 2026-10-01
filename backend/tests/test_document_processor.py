import pytest
from backend.app.ai.document_processor import DocumentProcessor, ProcessedDocument, ProcessedPage


def test_clean_text_normalizes_whitespace_and_linebreaks():
    dirty_text = "  Patient Name:   Alex Vance \r\n\r\n\r\n\r\nDiagnosis:   Type 2  Diabetes \x00\x08  \n"
    cleaned = DocumentProcessor.clean_text(dirty_text)
    
    assert "\r" not in cleaned
    assert "\x00" not in cleaned
    assert "\x08" not in cleaned
    assert "Patient Name: Alex Vance" in cleaned
    assert "Diagnosis: Type 2 Diabetes" in cleaned
    assert "\n\n\n" not in cleaned


def test_process_raw_text_single_page():
    processor = DocumentProcessor()
    raw = "Hospital: Metro General Hospital\nDate: 2026-06-15\nPatient was examined."
    doc = processor.process_text(
        raw_text=raw,
        document_id="doc_123",
        metadata={"category": "blood_report", "patient_id": "pat_001"}
    )

    assert isinstance(doc, ProcessedDocument)
    assert doc.document_id == "doc_123"
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1
    assert "Metro General Hospital" in doc.pages[0].text
    assert doc.metadata["category"] == "blood_report"
    assert doc.total_characters > 0


def test_process_pages_explicit_multi_page():
    processor = DocumentProcessor()
    pages_input = [
        {"page_number": 1, "text": "Page 1: Clinical notes and initial evaluation."},
        {"page_number": 2, "text": "Page 2: Lab results and follow-up plan."}
    ]
    doc = processor.process_pages(
        pages_input=pages_input,
        document_id="doc_multi_01",
        metadata={"title": "Comprehensive Follow-Up"}
    )

    assert len(doc.pages) == 2
    assert doc.pages[0].page_number == 1
    assert doc.pages[1].page_number == 2
    assert "Page 1: Clinical notes" in doc.pages[0].text
    assert "Page 2: Lab results" in doc.pages[1].text
    assert doc.metadata["title"] == "Comprehensive Follow-Up"
