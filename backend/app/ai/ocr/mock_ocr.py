from backend.app.ai.ocr.base import OCRProvider, OCRResult, OCROutputPage


class MockOCRProvider(OCRProvider):
    """
    Deterministic Mock OCR Provider for unit testing, CI/CD, and offline verification.
    """

    def __init__(self, simulated_text: str = ""):
        self.simulated_text = simulated_text or (
            "ST. JUDE DIAGNOSTIC IMAGING — RADIOLOGY REPORT\n"
            "Patient: Alex Vance | Examination: MRI Right Knee Joint | Date: 2022-08-10\n"
            "Clinical Indication: Chronic right knee joint discomfort.\n"
            "Findings: Grade II degenerative signal alteration in the posterior horn of the medial meniscus. "
            "Cruciate and collateral ligaments are anatomically intact. No displaced meniscal flap tear.\n"
            "Impression: Grade II medial meniscus degenerative changes without displaced tear."
        )

    @property
    def provider_name(self) -> str:
        return "mock_ocr"

    def is_available(self) -> bool:
        return True

    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        return self.simulated_text

    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> OCRResult:
        page = OCROutputPage(
            page_number=1,
            text=self.simulated_text,
            confidence=0.96
        )
        return OCRResult(
            pages=[page],
            full_text=self.simulated_text,
            provider_name=self.provider_name,
            success=True
        )
