import pytest
from backend.app.ai.ocr.base import OCRProvider, OCRResult
from backend.app.ai.ocr.mock_ocr import MockOCRProvider
from backend.app.ai.ocr.tesseract import TesseractOCRProvider
from backend.app.ai.ocr import get_ocr_provider


def test_mock_ocr_provider():
    provider = MockOCRProvider()
    assert provider.is_available() is True
    
    # Test OCR extraction from mock image bytes
    result_text = provider.extract_text_from_image_bytes(b"dummy-image-bytes")
    assert isinstance(result_text, str)
    assert len(result_text) > 0
    assert provider.provider_name == "mock_ocr"


def test_mock_ocr_pdf_extraction():
    provider = MockOCRProvider()
    result = provider.extract_text_from_pdf_bytes(b"dummy-scanned-pdf-bytes")
    assert isinstance(result, OCRResult)
    assert len(result.pages) >= 1
    assert result.pages[0].page_number == 1
    assert "DIAGNOSTIC IMAGING" in result.full_text or "REPORT" in result.full_text


def test_tesseract_ocr_graceful_availability():
    # Tesseract might or might not be installed on host system, but provider must not raise unhandled exception
    tesseract = TesseractOCRProvider()
    # is_available check returns boolean without crashing
    avail = tesseract.is_available()
    assert isinstance(avail, bool)


def test_get_ocr_provider_factory():
    mock_prov = get_ocr_provider(provider_name="mock")
    assert isinstance(mock_prov, MockOCRProvider)
    
    auto_prov = get_ocr_provider(provider_name="auto")
    assert isinstance(auto_prov, OCRProvider)

