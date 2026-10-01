import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProcessedPage(BaseModel):
    page_number: int
    text: str


class ProcessedDocument(BaseModel):
    document_id: str
    pages: List[ProcessedPage] = Field(default_factory=list)
    raw_text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    total_characters: int = 0


class DocumentProcessor:
    """
    Standardized document processing layer.
    Cleans extraction artifacts, normalizes whitespace, and structures page-level text.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Normalizes whitespace, fixes line endings, and strips common OCR/PDF extraction noise.
        """
        if not text:
            return ""
        
        # Replace Windows / Mac line breaks
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Remove non-printable control characters except standard tabs and newlines
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", cleaned)
        
        # Collapse 3+ consecutive newlines into 2
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        
        # Collapse multiple spaces or tabs into a single space
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        
        # Strip trailing/leading whitespace per line
        lines = [line.strip() for line in cleaned.split("\n")]
        cleaned = "\n".join(lines).strip()
        
        return cleaned

    def process_text(
        self,
        raw_text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessedDocument:
        """
        Processes single or multi-page raw text without explicit page markers.
        """
        cleaned = self.clean_text(raw_text)
        meta = metadata.copy() if metadata else {}
        
        # Single synthesized page if no page breakdown provided
        pages = [ProcessedPage(page_number=1, text=cleaned)] if cleaned else []
        
        return ProcessedDocument(
            document_id=document_id,
            pages=pages,
            raw_text=cleaned,
            metadata=meta,
            total_characters=len(cleaned)
        )

    def process_pages(
        self,
        pages_input: List[Dict[str, Any]],
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessedDocument:
        """
        Processes explicit list of pages: [{"page_number": 1, "text": "..."}].
        """
        processed_pages: List[ProcessedPage] = []
        combined_texts: List[str] = []
        meta = metadata.copy() if metadata else {}

        for p in pages_input:
            p_num = int(p.get("page_number", len(processed_pages) + 1))
            raw_p_text = str(p.get("text", ""))
            cleaned_p = self.clean_text(raw_p_text)
            if cleaned_p:
                processed_pages.append(ProcessedPage(page_number=p_num, text=cleaned_p))
                combined_texts.append(cleaned_p)

        full_raw = "\n\n".join(combined_texts)
        
        return ProcessedDocument(
            document_id=document_id,
            pages=processed_pages,
            raw_text=full_raw,
            metadata=meta,
            total_characters=len(full_raw)
        )
