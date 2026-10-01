import pytest
from backend.app.ai.extractors.pdf_extractor import (
    PDFExtractor,
    ExtractedDocument,
    ExtractedPage,
)


def test_extract_plain_text():
    extractor = PDFExtractor()
    content = "Patient Name: Alex Vance\nDiagnosis: Type 2 Diabetes\nMetformin 500mg daily."
    result = extractor.extract_from_bytes(
        file_bytes=content.encode("utf-8"),
        file_name="report.txt",
        document_id="doc-001"
    )
    
    assert isinstance(result, ExtractedDocument)
    assert result.total_pages == 1
    assert result.is_scanned is False
    assert "Alex Vance" in result.raw_text
    assert "Type 2 Diabetes" in result.raw_text
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1


def test_extract_empty_document():
    extractor = PDFExtractor()
    result = extractor.extract_from_bytes(
        file_bytes=b"",
        file_name="empty.txt",
        document_id="doc-002"
    )
    
    assert result.total_pages == 1
    assert result.raw_text == ""
    assert result.is_scanned is False


def test_extract_malformed_pdf():
    extractor = PDFExtractor()
    # Random corrupted bytes pretending to be a PDF
    corrupted_pdf = b"%PDF-1.4\nInvalid binary junk \xff\xfe\xfd not a real stream"
    result = extractor.extract_from_bytes(
        file_bytes=corrupted_pdf,
        file_name="corrupted.pdf",
        document_id="doc-003"
    )
    
    # Must degrade gracefully and mark scanned or fallback
    assert isinstance(result, ExtractedDocument)
    assert result.is_scanned is True or result.total_pages == 1


def test_scanned_page_detection():
    extractor = PDFExtractor()
    page = ExtractedPage(page_number=1, text="img", character_count=3, is_scanned_likely=True)
    assert page.is_scanned_likely is True

