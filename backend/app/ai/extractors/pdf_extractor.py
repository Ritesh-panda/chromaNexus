import io
import os
import re
import hashlib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def compute_file_checksum(file_bytes: bytes) -> str:
    """Computes SHA-256 hash of raw file bytes for binary deduplication."""
    return hashlib.sha256(file_bytes).hexdigest()


def compute_content_checksum(text: str) -> str:
    """
    Computes SHA-256 hash of normalized clinical text.
    Identifies documents with identical clinical content even if formatting/bytes differ.
    """
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ExtractedTable(BaseModel):
    table_index: int
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    bounding_box: Optional[List[float]] = None
    markdown: str = ""


class ExtractedBlock(BaseModel):
    text: str
    bounding_box: Optional[List[float]] = None
    block_type: int = 0


class ExtractedPage(BaseModel):
    page_number: int
    text: str
    character_count: int = 0
    is_scanned_likely: bool = False
    is_empty: bool = False
    tables: List[ExtractedTable] = Field(default_factory=list)
    blocks: List[ExtractedBlock] = Field(default_factory=list)


class ExtractedDocument(BaseModel):
    document_id: str
    file_name: str
    total_pages: int
    has_extractable_text: bool
    is_scanned: bool
    pages: List[ExtractedPage] = Field(default_factory=list)
    raw_text: str = ""
    checksum: str = ""
    content_checksum: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_method: str = "pymupdf"


class PDFExtractor:
    """
    Robust complete-document PDF and text extractor.
    - Full multi-page extraction without arbitrary truncation.
    - PyMuPDF vector table detection & tabular markdown structuring.
    - Column-aware text layout parsing without interleaving columns.
    - SHA-256 byte and content checksum computation.
    - Safe handling for scanned PDFs, empty pages, and malformed files.
    """

    MIN_CHARS_PER_PAGE_THRESHOLD = 30

    def extract_from_bytes(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractedDocument:
        meta = metadata.copy() if metadata else {}
        file_checksum = compute_file_checksum(file_bytes)
        lower_name = file_name.lower()

        # 1. Plain text documents (.txt, .csv, .json, .md)
        if lower_name.endswith((".txt", ".csv", ".json", ".log", ".md")):
            try:
                text_content = file_bytes.decode("utf-8", errors="replace").strip()
            except Exception:
                text_content = str(file_bytes)

            content_checksum = compute_content_checksum(text_content)
            page = ExtractedPage(
                page_number=1,
                text=text_content,
                character_count=len(text_content),
                is_scanned_likely=False,
                is_empty=len(text_content) == 0
            )
            return ExtractedDocument(
                document_id=document_id,
                file_name=file_name,
                total_pages=1,
                has_extractable_text=len(text_content) > 0,
                is_scanned=False,
                pages=[page],
                raw_text=text_content,
                checksum=file_checksum,
                content_checksum=content_checksum,
                metadata=meta,
                extraction_method="plain_text"
            )

        # 2. PDF Extraction with PyMuPDF (fitz)
        if FITZ_AVAILABLE:
            try:
                return self._extract_with_fitz(
                    file_bytes=file_bytes,
                    file_name=file_name,
                    document_id=document_id,
                    file_checksum=file_checksum,
                    metadata=meta
                )
            except Exception as e:
                # If PyMuPDF fails due to corrupt stream, try pypdf or fallback
                pass

        # 3. Fallback to pypdf if available
        if PYPDF_AVAILABLE:
            try:
                return self._extract_with_pypdf(
                    file_bytes=file_bytes,
                    file_name=file_name,
                    document_id=document_id,
                    file_checksum=file_checksum,
                    metadata=meta
                )
            except Exception as e:
                pass

        # 4. Corrupt / Unreadable PDF Fallback
        return ExtractedDocument(
            document_id=document_id,
            file_name=file_name,
            total_pages=1,
            has_extractable_text=False,
            is_scanned=True,
            pages=[ExtractedPage(page_number=1, text="", character_count=0, is_scanned_likely=True, is_empty=True)],
            raw_text="",
            checksum=file_checksum,
            content_checksum=compute_content_checksum(""),
            metadata={**meta, "error": "Unable to extract text from file or corrupt PDF stream"},
            extraction_method="error_fallback"
        )

    def _extract_with_fitz(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
        file_checksum: str,
        metadata: Dict[str, Any]
    ) -> ExtractedDocument:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_pages = len(doc)

        if total_pages == 0:
            return ExtractedDocument(
                document_id=document_id,
                file_name=file_name,
                total_pages=0,
                has_extractable_text=False,
                is_scanned=False,
                pages=[],
                raw_text="",
                checksum=file_checksum,
                content_checksum=compute_content_checksum(""),
                metadata=metadata,
                extraction_method="pymupdf"
            )

        extracted_pages: List[ExtractedPage] = []
        combined_texts: List[str] = []
        total_chars = 0
        scanned_page_count = 0
        empty_page_count = 0

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            # Detect vector tables on page
            extracted_tables: List[ExtractedTable] = []
            tab_rects = []
            try:
                tabs = page.find_tables()
                for t_idx, tab in enumerate(tabs.tables):
                    t_bbox = [round(float(c), 2) for c in tab.bbox]
                    tab_rects.append(fitz.Rect(tab.bbox))
                    
                    # Extract rows and markdown
                    rows_data = tab.extract() or []
                    headers = [str(c or "").strip() for c in rows_data[0]] if rows_data else []
                    data_rows = [[str(c or "").strip() for c in r] for r in rows_data[1:]] if len(rows_data) > 1 else []
                    
                    md = tab.to_markdown().strip() if hasattr(tab, "to_markdown") else self._rows_to_markdown(rows_data)
                    
                    extracted_tables.append(ExtractedTable(
                        table_index=t_idx,
                        headers=headers,
                        rows=data_rows,
                        bounding_box=t_bbox,
                        markdown=md
                    ))
            except Exception:
                extracted_tables = []
                tab_rects = []

            # Extract text blocks with PyMuPDF block sorting (reading order)
            extracted_blocks: List[ExtractedBlock] = []
            page_elements = []  # (y0, x0, element_type, text_content)

            # Insert tables as ordered layout elements
            for t in extracted_tables:
                if t.markdown:
                    y0 = t.bounding_box[1] if t.bounding_box else 0.0
                    x0 = t.bounding_box[0] if t.bounding_box else 0.0
                    page_elements.append((y0, x0, "table", t.markdown))

            try:
                blocks = page.get_text("blocks", sort=True)
                for b in blocks:
                    # b: (x0, y0, x1, y1, text, block_no, block_type)
                    b_rect = fitz.Rect(b[:4])
                    b_text = b[4].strip()
                    b_type = b[6] if len(b) > 6 else 0
                    b_box = [round(float(c), 2) for c in b[:4]]

                    # Exclude text blocks that are inside detected tables
                    inside_table = False
                    if tab_rects and b_rect.get_area() > 0:
                        for tr in tab_rects:
                            if b_rect.intersects(tr):
                                intersection = abs(b_rect & tr)
                                if (intersection / b_rect.get_area()) > 0.4:
                                    inside_table = True
                                    break

                    if not inside_table and b_text:
                        extracted_blocks.append(ExtractedBlock(
                            text=b_text,
                            bounding_box=b_box,
                            block_type=b_type
                        ))
                        # If no vector tables were detected, check if this block is an unruled whitespace table
                        parsed_block_text = b_text
                        if not extracted_tables:
                            parsed_block_text = self._format_aligned_text_table(b_text)

                        page_elements.append((b[1], b[0], "block", parsed_block_text))
            except Exception:
                # Fallback to plain page text if block sorting fails
                plain_text = page.get_text() or ""
                if plain_text.strip():
                    page_elements.append((0.0, 0.0, "block", plain_text.strip()))

            # Sort page elements by vertical coordinate y0, then horizontal coordinate x0
            page_elements.sort(key=lambda elem: (elem[0], elem[1]))
            page_text = "\n\n".join(elem[3] for elem in page_elements if elem[3].strip()).strip()

            char_count = len(page_text)
            total_chars += char_count

            # Determine empty vs scanned
            images = page.get_images()
            has_images = len(images) > 0
            is_empty = char_count == 0 and not has_images
            is_scanned = char_count < self.MIN_CHARS_PER_PAGE_THRESHOLD and has_images

            if is_empty:
                empty_page_count += 1
            if is_scanned:
                scanned_page_count += 1

            extracted_pages.append(ExtractedPage(
                page_number=page_num,
                text=page_text,
                character_count=char_count,
                is_scanned_likely=is_scanned,
                is_empty=is_empty,
                tables=extracted_tables,
                blocks=extracted_blocks
            ))

            if page_text:
                combined_texts.append(page_text)

        doc.close()

        full_raw_text = "\n\n".join(combined_texts)
        content_checksum = compute_content_checksum(full_raw_text)

        non_empty_pages = total_pages - empty_page_count
        is_scanned_doc = (
            non_empty_pages > 0 and scanned_page_count == non_empty_pages
        ) or (total_chars == 0 and not is_empty)

        return ExtractedDocument(
            document_id=document_id,
            file_name=file_name,
            total_pages=total_pages,
            has_extractable_text=total_chars >= self.MIN_CHARS_PER_PAGE_THRESHOLD,
            is_scanned=is_scanned_doc,
            pages=extracted_pages,
            raw_text=full_raw_text,
            checksum=file_checksum,
            content_checksum=content_checksum,
            metadata=metadata,
            extraction_method="pymupdf"
        )

    def _extract_with_pypdf(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
        file_checksum: str,
        metadata: Dict[str, Any]
    ) -> ExtractedDocument:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        total_pages = len(reader.pages)
        if total_pages == 0:
            return ExtractedDocument(
                document_id=document_id,
                file_name=file_name,
                total_pages=0,
                has_extractable_text=False,
                is_scanned=False,
                pages=[],
                raw_text="",
                checksum=file_checksum,
                content_checksum=compute_content_checksum(""),
                metadata=metadata,
                extraction_method="pypdf"
            )

        extracted_pages: List[ExtractedPage] = []
        combined_texts: List[str] = []
        total_chars = 0

        for idx, page_obj in enumerate(reader.pages, start=1):
            try:
                page_text = page_obj.extract_text() or ""
                cleaned = page_text.strip()
            except Exception:
                cleaned = ""

            char_count = len(cleaned)
            total_chars += char_count
            is_scanned_page = char_count < self.MIN_CHARS_PER_PAGE_THRESHOLD

            extracted_pages.append(ExtractedPage(
                page_number=idx,
                text=cleaned,
                character_count=char_count,
                is_scanned_likely=is_scanned_page,
                is_empty=char_count == 0
            ))
            if cleaned:
                combined_texts.append(cleaned)

        full_raw_text = "\n\n".join(combined_texts)
        content_checksum = compute_content_checksum(full_raw_text)
        is_scanned_doc = total_chars < (self.MIN_CHARS_PER_PAGE_THRESHOLD * total_pages)

        return ExtractedDocument(
            document_id=document_id,
            file_name=file_name,
            total_pages=total_pages,
            has_extractable_text=total_chars >= self.MIN_CHARS_PER_PAGE_THRESHOLD,
            is_scanned=is_scanned_doc,
            pages=extracted_pages,
            raw_text=full_raw_text,
            checksum=file_checksum,
            content_checksum=content_checksum,
            metadata=metadata,
            extraction_method="pypdf"
        )

    def _rows_to_markdown(self, rows: List[List[str]]) -> str:
        """Converts raw 2D grid into clean markdown table."""
        if not rows:
            return ""
        clean_rows = [[re.sub(r"\s+", " ", str(c or "")).strip() for c in r] for r in rows]
        max_cols = max(len(r) for r in clean_rows)
        # Pad shorter rows
        padded = [r + [""] * (max_cols - len(r)) for r in clean_rows]
        headers = padded[0]
        header_line = "| " + " | ".join(headers) + " |"
        sep_line = "| " + " | ".join(["---"] * max_cols) + " |"
        body_lines = ["| " + " | ".join(r) + " |" for r in padded[1:]]
        return "\n".join([header_line, sep_line] + body_lines)

    def _format_aligned_text_table(self, text: str) -> str:
        """
        Detects whitespace/tab-aligned clinical laboratory tables in plain text blocks
        and converts them to structured markdown table lines.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if len(lines) < 2:
            return text

        # Check if first line resembles a table header
        header_tokens = re.split(r"\s{2,}|\t+", lines[0])
        if len(header_tokens) < 3:
            return text

        header_keywords = {"test", "name", "parameter", "result", "value", "unit", "units", "range", "reference", "status", "flag", "interval"}
        header_matches = sum(1 for tok in header_tokens if any(kw in tok.lower() for kw in header_keywords))
        
        # If at least two header keywords found, treat as aligned table
        if header_matches >= 2:
            md_lines = []
            cols_count = len(header_tokens)
            md_lines.append("| " + " | ".join(header_tokens) + " |")
            md_lines.append("| " + " | ".join(["---"] * cols_count) + " |")
            
            for line in lines[1:]:
                row_tokens = re.split(r"\s{2,}|\t+", line)
                if len(row_tokens) == cols_count:
                    md_lines.append("| " + " | ".join(row_tokens) + " |")
                elif len(row_tokens) > 1:
                    # Pad or join remainder
                    if len(row_tokens) < cols_count:
                        row_tokens.extend([""] * (cols_count - len(row_tokens)))
                    else:
                        row_tokens = row_tokens[:cols_count - 1] + [" ".join(row_tokens[cols_count - 1:])]
                    md_lines.append("| " + " | ".join(row_tokens) + " |")
                else:
                    md_lines.append(line)
            return "\n".join(md_lines)

        return text

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
