import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.ai.document_processor import ProcessedDocument, ProcessedPage


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    page_number: int
    chunk_index: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    character_count: int = 0


class DocumentChunker:
    """
    Splits ProcessedDocuments into deterministic, page-aware chunks.
    Preserves document identity, page numbers, indices, and metadata.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk_document(self, doc: ProcessedDocument) -> List[DocumentChunk]:
        """
        Chunks all pages of a ProcessedDocument, preserving page contexts.
        """
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page in doc.pages:
            page_chunks = self._chunk_page(
                page=page,
                document_id=doc.document_id,
                base_metadata=doc.metadata,
                start_index=global_chunk_idx
            )
            chunks.extend(page_chunks)
            global_chunk_idx += len(page_chunks)

        return chunks

    def _chunk_page(
        self,
        page: ProcessedPage,
        document_id: str,
        base_metadata: Dict[str, Any],
        start_index: int
    ) -> List[DocumentChunk]:
        """
        Splits a single page into overlapping text chunks.
        """
        text = page.text.strip()
        if not text:
            return []

        chunks: List[DocumentChunk] = []
        text_len = len(text)

        # If text is smaller than chunk_size, return single chunk
        if text_len <= self.chunk_size:
            chunk_id = f"{document_id}_p{page.page_number}_c{start_index}"
            meta = {
                **base_metadata,
                "document_id": document_id,
                "page_number": page.page_number,
                "chunk_index": start_index
            }
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                page_number=page.page_number,
                chunk_index=start_index,
                text=text,
                metadata=meta,
                character_count=text_len
            ))
            return chunks

        start = 0
        local_idx = 0
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # If not at the end of the text, look for a separator to split cleanly
            if end < text_len:
                split_point = -1
                for sep in self.separators:
                    if sep == "":
                        split_point = end
                        break
                    last_sep = text.rfind(sep, start, end)
                    if last_sep != -1 and last_sep > start:
                        split_point = last_sep + len(sep)
                        break
                
                if split_point != -1 and split_point > start:
                    end = split_point

            chunk_text = text[start:end].strip()
            if chunk_text:
                curr_idx = start_index + local_idx
                chunk_id = f"{document_id}_p{page.page_number}_c{curr_idx}"
                meta = {
                    **base_metadata,
                    "document_id": document_id,
                    "page_number": page.page_number,
                    "chunk_index": curr_idx
                }
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    page_number=page.page_number,
                    chunk_index=curr_idx,
                    text=chunk_text,
                    metadata=meta,
                    character_count=len(chunk_text)
                ))
                local_idx += 1

            if end >= text_len:
                break
                
            start = max(start + 1, end - self.chunk_overlap)

        return chunks
