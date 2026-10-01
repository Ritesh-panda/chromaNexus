from typing import Optional
from backend.app.ai.ocr.base import OCRProvider, OCRResult, OCROutputPage
from backend.app.ai.ocr.tesseract import TesseractOCRProvider
from backend.app.ai.ocr.mock_ocr import MockOCRProvider
from backend.app.core.config import settings


def get_ocr_provider(provider_name: Optional[str] = None) -> OCRProvider:
    """
    Factory to retrieve OCR Provider based on configuration or override.
    Defaults to Tesseract if available, with automatic fallback to MockOCR.
    """
    prov = (provider_name or getattr(settings, "OCR_PROVIDER", "auto")).lower()

    if prov == "tesseract":
        tess = TesseractOCRProvider()
        if tess.is_available():
            return tess
        return MockOCRProvider()

    elif prov in ["mock", "test", "simulated"]:
        return MockOCRProvider()

    # 'auto' or unspecified: prefer tesseract if available, else mock
    tess = TesseractOCRProvider()
    if tess.is_available():
        return tess
    return MockOCRProvider()


__all__ = [
    "OCRProvider",
    "OCRResult",
    "OCROutputPage",
    "TesseractOCRProvider",
    "MockOCRProvider",
    "get_ocr_provider"
]
