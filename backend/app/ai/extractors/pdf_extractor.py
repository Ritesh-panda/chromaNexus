import io
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class ExtractedPage(BaseModel):
    page_number: int
    text: str
    character_count: int = 0
    is_scanned_likely: bool = False


class ExtractedDocument(BaseModel):
    document_id: str
    file_name: str
    total_pages: int
    has_extractable_text: bool
    is_scanned: bool
    pages: List[ExtractedPage] = Field(default_factory=list)
    raw_text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_method: str = "native_pdf"


class PDFExtractor:
    """
    Robust PDF and Text Document Extractor.
    Extracts text preserving page numbers and detects whether a document
    contains native text or is scanned/image-only.
    """

    MIN_CHARS_PER_PAGE_THRESHOLD = 30  # Fewer characters than this on average suggests scanned PDF

    def extract_from_bytes(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractedDocument:
        meta = metadata.copy() if metadata else {}
        lower_name = file_name.lower()

        # 1. Handle Plain Text files (.txt, .csv, .json)
        if lower_name.endswith((".txt", ".csv", ".json", ".log", ".md")):
            try:
                text_content = file_bytes.decode("utf-8", errors="replace").strip()
            except Exception:
                text_content = str(file_bytes)

            page = ExtractedPage(
                page_number=1,
                text=text_content,
                character_count=len(text_content),
                is_scanned_likely=False
            )
            return ExtractedDocument(
                document_id=document_id,
                file_name=file_name,
                total_pages=1,
                has_extractable_text=len(text_content) > 0,
                is_scanned=False,
                pages=[page],
                raw_text=text_content,
                metadata=meta,
                extraction_method="plain_text"
            )

        # 2. Handle PDF files
        if not PYPDF_AVAILABLE:
            # Fallback when pypdf is not installed: attempt simple text decode or treat as scanned
            cleaned = self._fallback_pdf_text_extract(file_bytes)
            has_text = len(cleaned) > 20
            page = ExtractedPage(
                page_number=1,
                text=cleaned,
                character_count=len(cleaned),
                is_scanned_likely=not has_text
            )
            return ExtractedDocument(
                document_id=document_id,
                file_name=file_name,
                total_pages=1,
                has_extractable_text=has_text,
                is_scanned=not has_text,
                pages=[page],
                raw_text=cleaned,
                metadata=meta,
                extraction_method="fallback_decoder"
            )

        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
            if total_pages == 0:
                return ExtractedDocument(
                    document_id=document_id,
                    file_name=file_name,
                    total_pages=0,
                    has_extractable_text=False,
                    is_scanned=True,
                    pages=[],
                    raw_text="",
                    metadata=meta,
                    extraction_method="pypdf"
                )

            extracted_pages: List[ExtractedPage] = []
            combined_texts: List[str] = []
            total_chars = 0

            for idx, page_obj in enumerate(reader.pages, start=1):
                try:
                    page_text = page_obj.extract_text() or ""
                    cleaned_page = page_text.strip()
                except Exception:
                    cleaned_page = ""

                char_count = len(cleaned_page)
                total_chars += char_count
                is_scanned_page = char_count < self.MIN_CHARS_PER_PAGE_THRESHOLD

                extracted_pages.append(ExtractedPage(
                    page_number=idx,
                    text=cleaned_page,
                    character_count=char_count,
                    is_scanned_likely=is_scanned_page
                ))
                if cleaned_page:
                    combined_texts.append(cleaned_page)

            full_text = "\n\n".join(combined_texts)
            avg_chars = total_chars / total_pages if total_pages > 0 else 0
            is_scanned_doc = avg_chars < self.MIN_CHARS_PER_PAGE_THRESHOLD or total_chars == 0

            return ExtractedDocument(
                document_id=document_id,
                file_name=file_name,
                total_pages=total_pages,
                has_extractable_text=total_chars >= self.MIN_CHARS_PER_PAGE_THRESHOLD,
                is_scanned=is_scanned_doc,
                pages=extracted_pages,
                raw_text=full_text,
                metadata=meta,
                extraction_method="pypdf"
            )

        except Exception as e:
            # Handle corrupt/malformed PDF
            return ExtractedDocument(
                document_id=document_id,
                file_name=file_name,
                total_pages=1,
                has_extractable_text=False,
                is_scanned=True,
                pages=[ExtractedPage(page_number=1, text="", character_count=0, is_scanned_likely=True)],
                raw_text="",
                metadata={**meta, "error": f"Failed to parse PDF: {str(e)}"},
                extraction_method="error_fallback"
            )

    def extract_from_file_path(
        self,
        file_path: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractedDocument:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        return self.extract_from_bytes(
            file_bytes=file_bytes,
            file_name=file_name,
            document_id=document_id,
            metadata=metadata
        )

    def _fallback_pdf_text_extract(self, file_bytes: bytes) -> str:
        """Lightweight byte regex text stream extraction for environments without pypdf."""
        try:
            raw = file_bytes.decode("latin-1", errors="ignore")
            # Extract plain text enclosed in stream or BT/ET markers
            matches = re.findall(r"\((.*?)\)[\s]*T[jd]", raw)
            if matches:
                return " ".join(matches).strip()
        except Exception:
            pass
        return ""
