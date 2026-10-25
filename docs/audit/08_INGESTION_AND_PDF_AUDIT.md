# ChronaNexus Forensic Audit Dossier ? Document Ingestion & Extraction Audit

**Document ID:** `08_INGESTION_AND_PDF_AUDIT.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  

---

## 1. Document Extraction Pipeline Audit

The ingestion pipeline (`backend/app/ai/extractors/pdf_extractor.py`) was audited across five key technical capabilities:

### 1. Multi-Page Extraction Without Arbitrary Truncation
- **Implementation:** `PDFExtractor._extract_with_fitz()` iterates through all pages of the document (`for page_idx in range(total_pages)`).
- **Evidence:** Source code inspection confirms that the arbitrary 3,000-character truncation limit present in early drafts has been **completely eliminated**.
- **Verification:** `test_multipage_pdf_complete_extraction_no_truncation` in `test_phase3_ingestion.py` passes with a 4-page, 8,000-character test document.

### 2. Table Parsing & Bounding Box Preservation
- **Implementation:** Lines 202?230 use PyMuPDF's native table detection:
  ```python
  tabs = page.find_tables()
  for t_idx, tab in enumerate(tabs.tables):
      t_bbox = [round(float(c), 2) for c in tab.bbox]
      rows_data = tab.extract() or []
      md = tab.to_markdown().strip()
  ```
- **Finding:** Vector tables are extracted as markdown, keeping test names, numerical values, units, and reference ranges unified. Table bounding boxes are recorded to prevent duplicate text extraction from overlapping text blocks.

### 3. Clinical Boundary-Aware Chunking
- **Implementation:** `DocumentChunker` (`backend/app/ai/chunker.py`) uses `CLINICAL_SECTION_PATTERNS` to identify clinical headers (`LABORATORY RESULTS`, `MEDICATIONS`, `ASSESSMENT & PLAN`, `ALLERGIES`).
- **Finding:** Chunks preserve page numbers (`page_number`), chunk indexes, and section metadata. If a laboratory table spans multiple rows, it is kept intact within a single chunk where possible.

### 4. Checksum Deduplication Architecture
- **Binary Checksum:** SHA-256 of raw file bytes (`hashlib.sha256(file_bytes).hexdigest()`).
- **Content Checksum:** SHA-256 of whitespace-normalized lowercase text (`compute_content_checksum()`).
- **Endpoint Behavior:** In `backend/app/routers/documents.py:84`, duplicate binary uploads return HTTP `409 Conflict` with `DUPLICATE_DOCUMENT` code and reference to the existing report ID.

---

## 2. Ingestion Defect Investigations

### Investigation A: Scanned PDF Detection vs Real OCR Execution
- **User Question:** *Does scanned-PDF detection actually result in OCR, or merely record a flag?*
- **Audit Finding:** **It merely records a flag; zero OCR is performed on host.**
- **Evidence:**
  1. `pdf_extractor.py:302` sets `is_scanned = char_count < MIN_CHARS_PER_PAGE_THRESHOLD and has_images`.
  2. `TesseractOCRProvider.is_available()` returns `False` on the host system because the Tesseract binary is not installed in the operating system PATH.
  3. The factory `get_ocr_provider()` in `backend/app/ai/ocr/__init__.py:31` falls back to `MockOCRProvider`.
  4. `MockOCRProvider` returns a hardcoded string: *"ST. JUDE DIAGNOSTIC IMAGING ? RADIOLOGY REPORT... MRI Right Knee Joint"*.
- **Verdict:** Scanned PDF ingestion in production will fail to extract real patient text.

### Investigation B: Duplicate Upload Race Condition
- **User Question:** *Investigate possible duplicate-upload race conditions.*
- **Audit Finding:** **Confirmed Race Condition Defect.**
- **Evidence:**
  In `backend/app/routers/documents.py`:
  ```python
  # Line 84: Python query check
  existing_report = db.query(MedicalReport).filter(
      MedicalReport.patient_id == current_patient.id,
      MedicalReport.checksum == file_checksum
  ).first()
  if existing_report:
      raise HTTPException(status_code=409, detail="Duplicate document detected")
  ...
  # Line 115: Insert into database
  db.add(report)
  db.commit()
  ```
  In `backend/app/models/report.py:46`:
  ```python
  checksum = Column(String(64), nullable=True, index=True)
  ```
  There is **NO database-level `UniqueConstraint('patient_id', 'checksum')`**. If two concurrent requests upload the identical PDF at the same millisecond, both will pass line 84 before either commits line 115, resulting in duplicate records in `medical_reports`.
