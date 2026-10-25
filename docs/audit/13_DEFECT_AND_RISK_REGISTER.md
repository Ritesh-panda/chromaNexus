# ChronaNexus Forensic Audit Dossier ? Prioritized Defect & Risk Register

**Document ID:** `13_DEFECT_AND_RISK_REGISTER.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  

---

## 1. Defect Prioritization Overview

Defects are classified under strict impact criteria:
- **P0 ? Critical:** Confirmed severe privacy leakage, cross-patient data exposure, or irreversible clinical data loss. (Count: 0)
- **P1 ? High:** Core workflow is broken, clinical data cannot be processed, or persistent database is out of sync. (Count: 3)
- **P2 ? Medium:** Important capability incomplete, concurrency race condition, or user-facing error masking. (Count: 4)
- **P3 ? Low:** Maintainability, documentation divergence, or secondary optimization gap. (Count: 3)

---

## 2. Comprehensive Defect Catalog

### [DEF-01] Persistent Database `chronanexus.db` Unmigrated at Revision 002
- **Severity:** `P1 ? HIGH` | **Confidence:** `VERIFIED ? STATIC`
- **Affected Files:** `chronanexus.db`, `backend/alembic/versions/003_*.py`, `004_*.py`
- **Evidence:** `SELECT version_num FROM alembic_version` in `chronanexus.db` returns `'002_add_document_chunks'`.
- **Actual Behavior:** Columns `checksum`, `content_checksum`, `page_count` in `medical_reports` and `source_page_number` in `lab_results` are missing from persistent DB.
- **Expected Behavior:** Persistent DB should be at revision `'004_add_checksum_and_page_metadata'`.
- **User Impact:** Any application run using persistent `chronanexus.db` will crash on SQL queries querying Phase 3 columns.
- **Suggested Remediation:** Execute `alembic upgrade head` after creating a verified file backup.

### [DEF-02] Scanned PDF Ingestion Fails Real OCR (Mock Fallback Active)
- **Severity:** `P1 ? HIGH` | **Confidence:** `VERIFIED ? TESTED`
- **Affected Files:** `backend/app/ai/extractors/pdf_extractor.py:302`, `backend/app/ai/ocr/tesseract.py:30`, `mock_ocr.py:10`
- **Evidence:** `TesseractOCRProvider.is_available()` returns `False` on host. Factory falls back to `MockOCRProvider`.
- **Actual Behavior:** Scanned PDFs emit fake text for "Alex Vance Right Knee MRI" instead of real patient contents.
- **Expected Behavior:** Real optical character recognition on scanned page images using Tesseract or PaddleOCR.
- **User Impact:** Patients uploading scanned prescriptions or non-searchable clinical reports cannot extract their records.
- **Suggested Remediation:** Bundle Tesseract OCR binary in deployment environment or integrate a robust offline OCR engine.

### [DEF-03] Conversational Follow-Up Resolution Fails for Non-Hardcoded Diseases (SC-05)
- **Severity:** `P1 ? HIGH` | **Confidence:** `VERIFIED ? TESTED`
- **Affected Files:** `backend/app/ai/rag/query_resolver.py:32`
- **Evidence:** In benchmark SC-05, turn 1 asks about Asthma; turn 2 asks about inhaler dose; `active_topic` returns `None`.
- **Actual Behavior:** Query resolver dictionary `TAXONOMY` only includes diabetes, cholesterol, hypertension; lacks pulmonary/asthma.
- **Expected Behavior:** General query resolver should resolve pronouns and elliptical references for any clinical domain.
- **User Impact:** Patients inquiring about respiratory, orthopedic, or gastrointestinal conditions lose context on turn 2.
- **Suggested Remediation:** Expand taxonomy with clinical dictionary or use lightweight grammar-based topic extraction.

### [DEF-04] Concurrent Duplicate Upload Causes Duplicate Database Records (Race Condition)
- **Severity:** `P2 ? MEDIUM` | **Confidence:** `VERIFIED ? STATIC`
- **Affected Files:** `backend/app/routers/documents.py:84-115`, `backend/app/models/report.py:46`
- **Evidence:** Checksum existence is checked via a Python query before insertion; `medical_reports` lacks a database unique constraint on `(patient_id, checksum)`.
- **Actual Behavior:** Concurrent upload requests with identical bytes both pass line 84 before either commits line 115.
- **Expected Behavior:** Database constraint guarantees atomicity and rejects concurrent duplicate inserts.
- **Suggested Remediation:** Add `UniqueConstraint('patient_id', 'checksum', name='uq_patient_report_checksum')` to `MedicalReport`.

### [DEF-05] Frontend Services Silently Swallow Network Errors and Display Mock Data
- **Severity:** `P2 ? MEDIUM` | **Confidence:** `VERIFIED ? STATIC`
- **Affected Files:** `src/services/report.service.ts:45`, `patient.service.ts:16`, `timeline.service.ts:25`
- **Evidence:** `try ... catch` blocks return `MOCK_REPORTS`, `MOCK_PATIENT`, `MOCK_TIMELINE_EVENTS`.
- **Actual Behavior:** UI displays rich mock clinical records even when FastAPI backend is offline.
- **Expected Behavior:** UI should surface clear error states, connection warnings, and retry buttons.
- **User Impact:** Users and developers are deceived into believing live API integration is functioning.
- **Suggested Remediation:** Replace mock fallbacks in API services with explicit error throws and user-facing error toasts.

### [DEF-06] Newly Uploaded Reports Not Immediately Indexed in Active Vector Search (SC-09)
- **Severity:** `P2 ? MEDIUM` | **Confidence:** `VERIFIED ? TESTED`
- **Affected Files:** `backend/app/ai/embeddings.py:45`, `retrieval.py`
- **Evidence:** In benchmark SC-09, newly ingested acute bronchitis report was not retrieved in top-4 candidates.
- **Actual Behavior:** Hash vector distance failed to rank new document chunk above pre-existing chunks.
- **Expected Behavior:** Newly uploaded reports immediately rank in top-K for relevant queries.
- **Suggested Remediation:** Transition to ChromaDB dense vector store and BGE semantic embeddings (Phase 4).

### [DEF-07] Hash-Based Embedding Provider Cannot Resolve Clinical Semantic Synonyms (SC-10)
- **Severity:** `P2 ? MEDIUM` | **Confidence:** `VERIFIED ? TESTED`
- **Affected Files:** `backend/app/ai/embeddings.py:45`
- **Evidence:** In benchmark SC-10, query *"high blood pressure"* failed to retrieve records for *"essential hypertension"*.
- **Actual Behavior:** Hash-projection provider hashes different character tokens into independent vector dimensions.
- **Expected Behavior:** Semantic embedding model maps clinical synonyms into proximal vector space.
- **Suggested Remediation:** Adopt dense transformer model (`BAAI/bge-small-en-v1.5`) in application pipeline.

### [DEF-08] BM25 Keyword Search and Reciprocal Rank Fusion Absent From Main Application
- **Severity:** `P3 ? LOW` | **Confidence:** `VERIFIED ? STATIC`
- **Affected Files:** `backend/app/ai/rag/`
- **Evidence:** Zero occurrences of `bm25` or `rrf` in application codebase.
- **Actual Behavior:** Retrieval currently fuses structured SQL queries and vector scan without BM25.
- **Expected Behavior:** Full hybrid retrieval combining BM25 keyword matching and dense vector search via RRF.
- **Suggested Remediation:** Implement `BM25Retriever` using `rank_bm25` in Phase 4.

### [DEF-09] Citation Verification is Coarse Whole-Chunk Rather Than Claim-Verified
- **Severity:** `P2 ? MEDIUM` | **Confidence:** `VERIFIED ? STATIC`
- **Affected Files:** `backend/app/ai/rag/pipeline.py:145`
- **Evidence:** Citations are appended directly from retrieved chunk metadata without sentence-level NLI verification.
- **Actual Behavior:** If a chunk contains 3 facts, the citation is attached even if the generated answer only references 1 fact.
- **Expected Behavior:** Granular claim-level evidence verification (scheduled for Phase 6).
- **Suggested Remediation:** Implement sentence-level citation verification in Phase 6.

### [DEF-10] Documentation Lag in Development Memory File
- **Severity:** `P3 ? LOW` | **Confidence:** `VERIFIED ? STATIC`
- **Affected Files:** `docs/DEVELOPMENT_MEMORY.md:25`
- **Evidence:** Memory file states: *"Current Development Phase: Phase 1 ? Frontend scaffold and verification... No real backend or LLM is connected yet."*
- **Actual Behavior:** Backend FastAPI, RAG, and Phase 3 ingestion were subsequently implemented without updating memory header.
- **Expected Behavior:** Documentation should reflect current Phase 3 completion status.
- **Suggested Remediation:** Update `DEVELOPMENT_MEMORY.md` to reflect verified Phase 3 state.
