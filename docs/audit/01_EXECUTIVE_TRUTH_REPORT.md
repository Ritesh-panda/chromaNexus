# ChronaNexus Forensic Audit Dossier ? Executive Truth Report

**Document ID:** `01_EXECUTIVE_TRUTH_REPORT.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  
**Overall Verdict:** `ACADEMIC PROTOTYPE ? NOT READY FOR PRODUCTION OR CLINICAL DECISION SUPPORT`

---

## 1. Executive Summary

ChronaNexus is designed as an AI-powered longitudinal medical intelligence platform that ingests unstructured clinical PDFs, extracts structured clinical entities (diseases, medications, laboratory results, vitals, allergies), constructs a patient memory timeline, and answers natural-language clinical queries strictly grounded in the patient's records.

An exhaustive, forensic, evidence-based audit of `C:/chromaNexus` reveals that **Phase 1 (Baseline retrieval diagnostics), Phase 2 (Database schema & provenance foundations), and Phase 3 (Ingestion pipeline, table parsing, boundary-aware chunking, and checksum deduplication) are implemented in code and backed by 161 passing backend tests**. 

However, the audit establishes **critical divergences between claims, temporary test environments, and actual persistent runtime state**:
1. **The persistent production database (`chronanexus.db`) is stuck at Alembic revision `002_add_document_chunks`**. Migrations 003 (`003_add_provenance_and_allergies`) and 004 (`004_add_checksum_and_page_metadata`) have **never been applied** to the persistent database. They only executed inside disposable temporary test databases created during automated test runs.
2. **The frontend application silently masks backend outages and missing endpoints**. Every major frontend service (`report.service.ts`, `patient.service.ts`, `timeline.service.ts`, `chat.service.ts`) wraps API calls in `try ... catch` blocks that silently fall back to hardcoded `MOCK_DATA`. If the backend is completely offline, the web UI still displays rich mock patient profiles, charts, and reports, creating a dangerous false impression of working end-to-end integration.
3. **Scanned PDF Optical Character Recognition (OCR) is completely non-functional**. The Tesseract OCR binary is **not installed on the host system** (`TesseractOCRProvider.is_available() == False`). When scanned PDFs with zero extractable text are encountered, the system merely flags `is_scanned_likely=True` and falls back to a deterministic `MockOCRProvider` that emits hardcoded sample text for "Alex Vance MRI Right Knee". Real scanned patient documents cannot be extracted.
4. **Semantic embeddings and ChromaDB are NOT integrated into the production application path**. While a benchmark experiment (`tests/benchmarks/experiment_chroma_bge.py`) demonstrated 10/12 scenario passes using ChromaDB and `BAAI/bge-small-en-v1.5`, the actual application (`backend/app/ai/rag/pipeline.py` and `embeddings.py`) still uses `LocalLightweightEmbeddingProvider` (a CPU hash-projection vectorizer) and `PostgresVectorStore` with SQLite full-table cosine scan fallback. Because hash vectors lack semantic awareness, medical synonym queries fail in production.
5. **Multi-turn conversational topic resolution fails for non-hardcoded medical conditions**. The query resolver relies on a static dictionary taxonomy that only covers diabetes, cholesterol, and hypertension. When asked follow-up questions about pulmonary conditions or asthma (Scenario 5), it fails to detect the active topic and loses conversational continuity.

---

## 2. Incontrovertible Truth Matrix

| Domain / Feature | Stated Claim / Roadmap Status | Actual Verified State | Evidence Standard | Direct Code / Command Evidence |
|---|---|---|---|---|
| **Multi-Page PDF Extraction** | Extracts full documents without arbitrary 3,000-char truncation | **VERIFIED TRUE** | `VERIFIED ? TESTED` | `backend/app/ai/extractors/pdf_extractor.py:152` uses PyMuPDF block parsing; tests pass in `test_phase3_ingestion.py`. |
| **Laboratory Table Parsing** | Detects multi-column tables, headers, and bounding boxes | **VERIFIED TRUE** | `VERIFIED ? TESTED` | `backend/app/ai/extractors/pdf_extractor.py:202` (`page.find_tables()`); extracts headers & data rows to markdown. |
| **Document Checksum Deduplication** | SHA-256 binary and normalized text deduplication | **VERIFIED TRUE** (with concurrency caveat) | `VERIFIED ? TESTED` | `pdf_extractor.py:19-29`; `documents.py:84-114`; 409 Conflict returned on duplicate upload. |
| **Allergy & Provenance Schema** | Models for allergies and source page provenance | **VERIFIED IN CODE & TEST DB ONLY** | `PARTIALLY VERIFIED` | `backend/app/models/allergy.py`; tested on disposable DB; **NOT present** in persistent `chronanexus.db`. |
| **Persistent DB Schema** | Stated to reflect Phase 3 schema | **CONTRADICTED ? UNMIGRATED** | `CONTRADICTED` | `chronanexus.db` Alembic version is `002_add_document_chunks`. Missing `checksum`, `page_count`, `allergies`. |
| **OCR for Scanned PDFs** | OCR fallback for scanned reports | **MOCKED / INOPERABLE** | `FAILED` | Tesseract binary not installed; `pdf_extractor.py:302` only flags; falls back to `MockOCRProvider`. |
| **Hybrid Retrieval (BM25 + RRF)** | Stated as Phase 4 capability | **NOT IMPLEMENTED IN APP** | `NOT TESTED` | Zero occurrences of BM25 or RRF in `backend/app/ai/rag/`. Currently fuses SQL + hash vector search. |
| **ChromaDB + BGE Vector Store** | Reported 10/12 benchmark result | **ISOLATED EXPERIMENT ONLY** | `PARTIALLY VERIFIED` | Runs exclusively in `tests/benchmarks/experiment_chroma_bge.py` on ephemeral DB; not wired to FastAPI. |
| **Synthetic Retrieval Benchmark** | 12 clinical retrieval scenarios | **9 / 12 PASSED (75.0%)** | `VERIFIED ? TESTED` | `tests/benchmarks/retrieval_benchmark.py`: SC-05, SC-09, SC-10 failed. Output logged in `baseline_results.json`. |
| **Frontend Real Data Display** | UI displays live patient data from DB | **PARTIAL / MOCK FALLBACK** | `PARTIALLY VERIFIED` | `src/services/*.ts` catch blocks return `MOCK_DATA` on error; masks backend status from end user. |
| **Concurrent Upload Safety** | Safe deduplication under concurrency | **FAILED (Race Condition)** | `VERIFIED ? STATIC` | `documents.py:84` does Python query before insert; no DB `UniqueConstraint('patient_id', 'checksum')`. |
| **Citation Verification** | Sentence-level evidence support verification | **NOT IMPLEMENTED (Planned P6)** | `PARTIALLY VERIFIED` | Whole-chunk citation attachment in `pipeline.py:145`; no granular NLI or entailment verification. |

---

## 3. High-Priority Defects Summary

```
========================================================================================
                         HIGH-PRIORITY DEFECT SUMMARY
========================================================================================
[DEF-01] P1 - HIGH    : Persistent database chronanexus.db has not been migrated (at Rev 002).
[DEF-02] P1 - HIGH    : Scanned PDF OCR is non-functional; host lacks Tesseract; MockOCR emits fake data.
[DEF-03] P1 - HIGH    : Conversational follow-up resolution fails for conditions outside hardcoded taxonomy (SC-05).
[DEF-04] P2 - MEDIUM  : Concurrent duplicate file uploads cause duplicate DB records (race condition).
[DEF-05] P2 - MEDIUM  : Frontend services silently swallow backend errors and render mock data.
[DEF-06] P2 - MEDIUM  : Newly uploaded reports not immediately indexed in active vector search (SC-09).
[DEF-07] P2 - MEDIUM  : Hash-based embedding provider cannot resolve clinical semantic synonyms (SC-10).
[DEF-08] P3 - LOW     : Documentation lag ? DEVELOPMENT_MEMORY.md states backend is not connected.
========================================================================================
```

---

## 4. Phase Verification Status

- **Phase 1 (Baseline Testing & Retrieval Diagnostics):** `VERIFIED ? TESTED` (9/12 on baseline; benchmark script exists and runs reproducibly).
- **Phase 2 (Database Schema & Clinical Provenance):** `PARTIALLY VERIFIED` (Code and unit tests complete; persistent database unmigrated).
- **Phase 3 (Complete-Document Ingestion & Checksum Deduplication):** `VERIFIED ? TESTED` (Multi-page extraction, vector tables, chunking, deduplication verified via 161 tests).
- **Phase 4 (Hybrid Retrieval: BM25, ChromaDB, RRF):** `NOT STARTED IN APP` (Tested in standalone experiment only; not integrated).
- **Phase 5 (Structured Clinical Queries & Trends):** `PARTIALLY IMPLEMENTED` (SQL querying implemented in `structured_retriever.py`, but temporal trend visualization relies on mock frontend data).
- **Phase 6 (Evidence-Grounded Assistant & Citations):** `PARTIALLY IMPLEMENTED` (Coarse chunk citations attached; sentence-level citation verification not implemented).
- **Phase 7 (Timeline & Lab Trend Visualizations):** `UNVERIFIED END-TO-END` (Frontend components exist with Recharts, but rely on mock fallback).
- **Phase 8 (Vault Improvements & Doctor Summaries):** `PARTIALLY IMPLEMENTED` (Backend summary router exists; frontend uses mock fallback).
- **Phase 9 (Security, Audit Logging, FHIR R4 Export):** `NOT IMPLEMENTED / PLANNED`.
- **Phase 10 (End-to-End Packaging & Production Deployment):** `NOT IMPLEMENTED / PLANNED`.

---

## 5. Auditor's Formal Conclusion

ChronaNexus possesses a **well-engineered, highly capable Phase 3 core**: PyMuPDF extraction, layout block sorting, clinical section boundary detection, table markdown preservation, and SHA-256 deduplication are fully verified and backed by 161 passing automated tests.

However, **ChronaNexus is an academic capstone prototype and is NOT ready for production or clinical deployment**. Before any clinical usage can be contemplated, the persistent database must be safely migrated, the frontend silent mock fallbacks must be replaced with explicit error handling, true semantic embeddings (ChromaDB + BGE) must be wired into the application runtime, an actual OCR engine must be provisioned, and sentence-level citation verification must be implemented.
