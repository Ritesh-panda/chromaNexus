# ChronaNexus Forensic Audit Dossier ? Phase-by-Phase Development History

**Document ID:** `05_PHASE_BY_PHASE_HISTORY.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  

---

## 1. Roadmap Overview & Implementation Status

The project roadmap comprises ten defined development phases. Forensic inspection establishes the true completion state:

```
Phase 1: Baseline Retrieval Diagnostics          [VERIFIED ? TESTED] (9/12 pass)
Phase 2: Database Schema & Clinical Provenance  [PARTIALLY VERIFIED] (151 tests pass; unmigrated DB)
Phase 3: Document Ingestion, Tables & Checksums [VERIFIED ? TESTED] (161 tests pass)
Phase 4: Hybrid Retrieval: BM25, ChromaDB & RRF [NOT STARTED IN APP] (Experiment only)
Phase 5: Structured Queries & Temporal Trends   [PARTIALLY IMPLEMENTED]
Phase 6: Evidence Grounding & Citations         [PARTIALLY IMPLEMENTED]
Phase 7: Timeline & Trend Visualizations        [UNVERIFIED END-TO-END]
Phase 8: Vault Improvements & Doctor Summaries  [PARTIALLY IMPLEMENTED]
Phase 9: Security, Audit Logging & FHIR R4      [PLANNED / NOT STARTED]
Phase 10: Production Packaging & Packaging      [PLANNED / NOT STARTED]
```

---

## 2. Detailed Phase Audit

### Phase 1: Baseline Testing & Synthetic Retrieval Benchmark
- **Original Objective:** Establish quantitative baseline for clinical question answering across 12 realistic scenarios.
- **Historical Claims:** Phase 1 baseline initially achieved 7/12 passing scenarios; improved to 9/12.
- **Current Verification:** Running `tests/benchmarks/retrieval_benchmark.py` reproduces **9/12 passes (75.0%)**.
- **Failing Scenarios:**
  - SC-05 (Multi-turn follow-up): Fails at `conversation_context_resolution`.
  - SC-09 (Newly uploaded reports): Fails at `candidate_retrieval`.
  - SC-10 (Semantic synonyms): Fails at `embedding_generation`.
- **Verdict:** `VERIFIED ? TESTED`.

### Phase 2: Database Schema & Clinical Provenance Foundations
- **Original Objective:** Establish relational models for clinical entities with source report and page provenance, plus comprehensive allergy tracking.
- **Actual Implementation:** Created `Allergy` model (`backend/app/models/allergy.py`), added `source_page_number`, `bounding_box`, and `extraction_confidence` to `LabResult` and `ExtractedEntity`.
- **Test Results:** 151 backend tests passed (`backend/tests/test_allergy_and_provenance.py`).
- **Critical Discrepancy:** Migration 003 was **not applied** to persistent `chronanexus.db`.
- **Verdict:** `PARTIALLY VERIFIED` (Code verified; persistent database unmigrated).

### Phase 3: Document Ingestion, Table Parsing & Checksum Deduplication
- **Original Objective:** Complete multi-page PDF extraction without 3,000-char truncation, layout block sorting, vector table extraction (`page.find_tables()`), clinical boundary chunking, and SHA-256 deduplication.
- **Actual Implementation:**
  - `backend/app/ai/extractors/pdf_extractor.py`: PyMuPDF layout parsing, table markdown formatting, SHA-256 binary and normalized text hashing.
  - `backend/app/ai/chunker.py`: `detect_clinical_section` preserving table rows and headers across boundaries.
  - `backend/app/routers/documents.py`: 409 Conflict rejection on duplicate uploads.
  - Migration 004: Added `checksum`, `content_checksum`, `page_count`.
- **Test Results:** 161 backend tests passed (`test_phase3_ingestion.py` has 10 dedicated tests).
- **Benchmark SC-11 Result:** Scenario 11 (multi-page >3,000 char reports & tables) **passed**.
- **Defects Identified:**
  - Scanned PDF detection does not run OCR; falls back to mock text.
  - Concurrent duplicate upload race condition due to lack of DB unique constraint.
- **Verdict:** `VERIFIED ? TESTED`.

### Phase 4: Hybrid Retrieval: BM25, ChromaDB & Reciprocal Rank Fusion
- **Original Objective:** Upgrade retrieval from SQLite scan to BM25 keyword search + ChromaDB vector search + BGE embeddings + Reciprocal Rank Fusion (RRF).
- **Reported Experiment:** `tests/benchmarks/experiment_chroma_bge.py` achieved 10/12 passes on disposable `exp_synthetic.db` and `exp_chroma_data/`.
- **Actual Application State:** Zero references to BM25 or RRF in `backend/app/ai/rag/`. ChromaDB is **not imported** in `pipeline.py` or `retrieval.py`. The application still uses `LocalLightweightEmbeddingProvider` and SQLite full-scan.
- **Verdict:** `NOT STARTED IN APP` (Isolated benchmark experiment only).

### Phases 5?10 Status Summary
- **Phase 5 (Structured Clinical Queries):** `StructuredRetriever` queries SQL tables; verified in unit tests, but temporal trend queries are unverified against live dynamic uploads.
- **Phase 6 (Evidence-Grounded Assistant):** Citations are coarsely attached per chunk (`pipeline.py:145`). Granular sentence-level entailment verification is not implemented.
- **Phase 7 (Timeline & Trends):** Frontend components render rich graphs using Recharts, but rely on mock fallback data when API fails.
- **Phase 8 (Vault Improvements & Doctor Summaries):** Backend `/summaries/generate` endpoint exists; frontend doctor summary page uses mock fallback.
- **Phase 9 (Security & FHIR R4):** Planned; no FHIR export or audit logging code exists.
- **Phase 10 (Production Packaging):** Planned; no Dockerfile or production orchestration exists.
