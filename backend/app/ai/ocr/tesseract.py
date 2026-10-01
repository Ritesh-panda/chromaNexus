import io
import logging
from typing import Optional
from backend.app.ai.ocr.base import OCRProvider, OCRResult, OCROutputPage

logger = logging.getLogger(__name__)


class TesseractOCRProvider(OCRProvider):
    """
    Local Tesseract OCR provider using pytesseract and Pillow/PyMuPDF.
    Gracefully handles missing binary without crashing application.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd
        self._available: Optional[bool] = None

    @property
    def provider_name(self) -> str:
        return "tesseract_ocr"

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            import pytesseract
            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            pytesseract.get_tesseract_version()
            self._available = True
        except Exception as e:
            logger.info(f"Tesseract OCR binary not detected on system: {str(e)}")
            self._available = False

        return self._available

    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        if not self.is_available():
            logger.warning("Tesseract OCR is not available on this system.")
            return ""

        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(img).strip()
        except Exception as e:
            logger.error(f"Error performing Tesseract OCR on image: {str(e)}")
            return ""

    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> OCRResult:
        if not self.is_available():
            return OCRResult(
                pages=[],
                full_text="",
                provider_name=self.provider_name,
                success=False,
                error_message="Tesseract OCR engine is not installed or available on this system."
            )

        try:
            import fitz  # PyMuPDF
            import pytesseract
            from PIL import Image

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages: list[OCROutputPage] = []
            combined_texts: list[str] = []

            for page_idx in range(len(doc)):
                page = doc[page_idx]
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                page_text = pytesseract.image_to_string(img).strip()
                pages.append(OCROutputPage(
                    page_number=page_idx + 1,
                    text=page_text,
                    confidence=0.88
                ))
                if page_text:
                    combined_texts.append(page_text)

            full_text = "\n\n".join(combined_texts)
            return OCRResult(
                pages=pages,
                full_text=full_text,
                provider_name=self.provider_name,
                success=True
            )
        except Exception as e:
            logger.error(f"Tesseract PDF OCR execution failed: {str(e)}")
            return OCRResult(
                pages=[],
                full_text="",
                provider_name=self.provider_name,
                success=False,
                error_message=f"Tesseract execution error: {str(e)}"
            )
