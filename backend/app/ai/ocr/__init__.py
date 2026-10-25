import logging
from typing import Optional
from backend.app.ai.ocr.base import OCRProvider, OCRResult, OCROutputPage
from backend.app.ai.ocr.tesseract import TesseractOCRProvider
from backend.app.ai.ocr.mock_ocr import MockOCRProvider
from backend.app.core.config import settings

logger = logging.getLogger(__name__)



def get_ocr_provider(provider_name: Optional[str] = None) -> OCRProvider:
    """
    Factory to retrieve OCR Provider based on configuration or override.
    Returns TesseractOCRProvider when configured or auto-detected.
    Never silently substitutes MockOCRProvider when real OCR is requested.
    MockOCRProvider is only returned when explicitly requested (e.g. 'mock', 'test').
    """
    prov = (provider_name or getattr(settings, "OCR_PROVIDER", "auto")).lower()

    if prov == "tesseract":
        return TesseractOCRProvider()

    elif prov in ["mock", "test", "simulated"]:
        return MockOCRProvider()

    # 'auto': Use real Tesseract if available; if not available, return TesseractOCRProvider
    # so that missing engine is accurately reported rather than silently fabricating clinical text.
    tess = TesseractOCRProvider()
    if tess.is_available():
        return tess

    # In explicit dev/test when mock is allowed or requested
    env = getattr(settings, "ENVIRONMENT", "development").lower()
    if env not in ["production", "staging"]:
        logger.warning("Real OCR engine (Tesseract) not found. Returning TesseractOCRProvider with unavailable status.")
        return tess

    return tess



__all__ = [
    "OCRProvider",
    "OCRResult",
    "OCROutputPage",
    "TesseractOCRProvider",
    "MockOCRProvider",
    "get_ocr_provider"
]
