from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class OCROutputPage(BaseModel):
    page_number: int
    text: str
    confidence: float = 0.90


class OCRResult(BaseModel):
    pages: List[OCROutputPage] = Field(default_factory=list)
    full_text: str = ""
    provider_name: str = ""
    success: bool = True
    error_message: Optional[str] = None


class OCRProvider(ABC):
    """
    Abstract interface for Optical Character Recognition (OCR) engines.
    Allows pluggable Tesseract, Cloud Vision (AWS/GCP/Azure), or Mock OCR providers.
    """

    @abstractmethod
    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> OCRResult:
        """Extract text from a scanned/image-based PDF binary."""
        pass

    @abstractmethod
    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        """Extract text from a single image binary (PNG/JPEG/TIFF)."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the underlying OCR engine/binary is operational."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
