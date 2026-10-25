import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
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


CLINICAL_SECTION_PATTERNS = [
    (r"(?i)^(?:#{1,4}\s*)?(?:LABORATORY(?:\s+(?:RESULTS|FINDINGS|INVESTIGATIONS|DATA))?|LABS?|BLOOD\s+TESTS?)\s*:?$", "laboratory_results"),
    (r"(?i)^(?:#{1,4}\s*)?(?:CURRENT\s+)?MEDICATIONS?(?:\s+(?:LIST|PRESCRIBED|ORDERS))?\s*:?$", "medications"),
    (r"(?i)^(?:#{1,4}\s*)?(?:ASSESSMENT(?:\s+&|\s+AND)?\s+PLAN|DIAGNOS[IE]S|IMPRESSION|CLINICAL\s+SUMMARY)\s*:?$", "assessment_and_plan"),
    (r"(?i)^(?:#{1,4}\s*)?(?:HISTORY\s+OF\s+PRESENT\s+ILLNESS|CHIEF\s+COMPLAINT|REASON\s+FOR\s+VISIT)\s*:?$", "history_of_present_illness"),
    (r"(?i)^(?:#{1,4}\s*)?(?:PHYSICAL\s+EXAMINATION|VITAL\s+SIGNS?)\s*:?$", "vital_signs"),
    (r"(?i)^(?:#{1,4}\s*)?(?:ALLERGIES(?:\s+AND\s+ADVERSE\s+REACTIONS)?)\s*:?$", "allergies"),
    (r"(?i)^(?:#{1,4}\s*)?(?:DISCHARGE\s+(?:SUMMARY|INSTRUCTIONS|PLAN))\s*:?$", "discharge_summary")
]


def detect_clinical_section(line: str) -> Optional[str]:
    """Detects standard clinical section headers."""
    s = line.strip()
    for pattern, name in CLINICAL_SECTION_PATTERNS:
        if re.match(pattern, s):
            return name
    return None


class DocumentChunker:
    """
    Page-aware and clinical-boundary-aware document chunker.
    - Preserves exact page numbers, document identity, and deterministic indices.
    - Preserves atomic Markdown table rows (never splits a result from its unit/range).
    - Re-attaches table headers on multi-chunk table splits to avoid orphaned values.
    - Tracks and embeds clinical section context in chunk metadata.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None,
        preserve_tables: bool = True
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "; ", ", ", " ", ""]
        self.preserve_tables = preserve_tables

    def chunk_document(self, doc: ProcessedDocument) -> List[DocumentChunk]:
        """
        Chunks all pages of a ProcessedDocument, preserving page contexts.
        """
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0
        current_section = doc.metadata.get("section") or "general"

        for page in doc.pages:
            page_chunks, current_section = self._chunk_page(
                page=page,
                document_id=doc.document_id,
                base_metadata=doc.metadata,
                start_index=global_chunk_idx,
                initial_section=current_section
            )
            chunks.extend(page_chunks)
            global_chunk_idx += len(page_chunks)

        return chunks

    def _chunk_page(
        self,
        page: ProcessedPage,
        document_id: str,
        base_metadata: Dict[str, Any],
        start_index: int,
        initial_section: str = "general"
    ) -> Tuple[List[DocumentChunk], str]:
        """
        Splits a single page into overlapping text chunks with clinical boundary awareness.
        """
        text = page.text.strip()
        if not text:
            return [], initial_section

        chunks: List[DocumentChunk] = []
        text_len = len(text)
        current_section = initial_section

        # If text is smaller than chunk_size, check section and return single chunk
        if text_len <= self.chunk_size:
            for line in text.split("\n"):
                sec = detect_clinical_section(line)
                if sec:
                    current_section = sec

            chunk_id = f"{document_id}_p{page.page_number}_c{start_index}"
            meta = {
                **base_metadata,
                "document_id": document_id,
                "page_number": page.page_number,
                "chunk_index": start_index,
                "clinical_section": current_section
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
            return chunks, current_section

        start = 0
        local_idx = 0

        while start < text_len:
            # Check for section header around current start
            lookahead_slice = text[start:min(start + self.chunk_size, text_len)]
            for line in lookahead_slice.split("\n")[:4]:
                detected = detect_clinical_section(line)
                if detected:
                    current_section = detected
                    break

            end = min(start + self.chunk_size, text_len)

            # If not at the end, find safe boundary
            if end < text_len:
                # 1. Atomic table row check: avoid splitting inside a markdown table row
                if self.preserve_tables and "|" in text[start:end]:
                    prev_nl = text.rfind("\n", start, end)
                    next_nl = text.find("\n", end)
                    if prev_nl != -1 and prev_nl > start:
                        line_segment = text[prev_nl:end]
                        if line_segment.strip().startswith("|") and (next_nl == -1 or "|" in text[end:next_nl]):
                            # We are inside a table row. Split at the previous newline
                            end = prev_nl

                # 2. Standard separator fallback
                if end == min(start + self.chunk_size, text_len):
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

            # 3. Table continuation header check: re-attach column header if chunk starts with table row
            if self.preserve_tables:
                table_hdr = self._find_preceding_table_header(text, start)
                if table_hdr:
                    hdr_first_line = table_hdr.split("\n")[0].strip()
                    if not chunk_text.startswith(hdr_first_line):
                        non_empty = [l.strip() for l in chunk_text.split("\n") if l.strip()]
                        if non_empty and non_empty[0].startswith("|") and "---" not in non_empty[0]:
                            chunk_text = table_hdr + "\n" + chunk_text

            if chunk_text:
                curr_idx = start_index + local_idx
                chunk_id = f"{document_id}_p{page.page_number}_c{curr_idx}"
                meta = {
                    **base_metadata,
                    "document_id": document_id,
                    "page_number": page.page_number,
                    "chunk_index": curr_idx,
                    "clinical_section": current_section
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

            # Advance start with overlap
            new_start = max(start + 1, end - self.chunk_overlap)
            # If new_start lands inside a table row, align it to start of that row
            if self.preserve_tables and "|" in text:
                prev_line_start = text.rfind("\n", start, new_start)
                next_line_start = text.find("\n", new_start)
                if next_line_start != -1 and "|" in text[new_start:next_line_start]:
                    # Inside a table row: align to either the line start or line end
                    if prev_line_start != -1 and prev_line_start > start:
                        new_start = prev_line_start + 1
                    else:
                        new_start = next_line_start + 1

            start = new_start

        return chunks, current_section

    def _find_preceding_table_header(self, full_text: str, pos: int) -> Optional[str]:
        """Finds markdown table header (| col1 | col2 |\n| --- | --- |) preceding pos."""
        lines = full_text[:pos].split("\n")
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if "---" in line and i > 0 and lines[i - 1].strip().startswith("|"):
                return lines[i - 1].strip() + "\n" + line
        return None
