# Project Overview — ChronaNexus

## 1. Executive Summary

**ChronaNexus** is an AI-powered longitudinal medical intelligence platform. Unlike traditional healthcare portals or electronic document repositories that treat patient records as static, isolated PDFs, ChronaNexus ingests multi-format clinical documents (blood panels, diagnostic lab reports, discharge summaries, imaging notes, and prescriptions), extracts clinical entities into structured relational models, maintains an evolving **Patient Memory Graph**, and enables evidence-grounded natural language question-answering with verifiable citations.

The core principle of ChronaNexus is: **"Instead of storing files, ChronaNexus stores clinical understanding."**

---

## 2. Core Capabilities

ChronaNexus is structured around six core processing systems:

1. **Document Vault (`System 1`)**:
   - Secure ingestion and organization of multi-page clinical documents (PDF, scans, text).
   - Dual-scope SHA-256 deduplication: file binary hash (`checksum`) vs. normalized clinical text hash (`content_checksum`).
   - Rejection of duplicate uploads with HTTP 409 Conflict (or idempotent return).
   - Metadata indexing, OCR/text extraction tracking, and document previews.

2. **Medical Understanding Engine (`System 2`)**:
   - Multi-page PyMuPDF extraction with table vector detection (`find_tables()`).
   - Unruled EHR whitespace-aligned lab table formatting into structured Markdown.
   - Clinical entity extraction: diagnoses (ICD-10), medications (dosage, frequency, route, RxNorm), laboratory analytes (LOINC canonical names, values, units, reference ranges), physicians, and healthcare facilities.
   - Page-level provenance capture (`source_page_number`, bounding boxes, extraction confidence).

3. **Patient Memory Engine (`System 3`)**:
   - Relational state graph maintaining patient demographics, chronic/active diseases, ongoing pharmacotherapy regimens, known drug allergies, and cross-reactivity matrices.
   - Automatic merge of newly extracted clinical entities into a unified, living profile.
   - Strict tenant isolation: every clinical entity is foreign-key scoped to `patient_id`.

4. **Medical Timeline Engine (`System 4`)**:
   - Chronological reconstruction of longitudinal health encounters from 2019 to present.
   - Event categorization: diagnoses, medications, lab tests, imaging, hospitalizations.
   - Separation of true encounter date from document upload date (`isUnknownDate` flag for unrecorded dates).
   - Multi-facility conflict detection flagging concurrent encounters across differing hospitals.

5. **Medical Intelligence & Evidence-Grounded Assistant (`System 5`)**:
   - Dual-channel retrieval combining structured SQL queries and dense/lexical hybrid RAG.
   - **Dense Retrieval**: Offline `BAAI/bge-small-en-v1.5` embeddings (384 dimensions) persisted in ChromaDB.
   - **Lexical Retrieval**: In-memory BM25 Okapi retriever with clinical domain tokenization.
   - **Reciprocal Rank Fusion (RRF)**: Merges dense and lexical results with configurable $k=60$.
   - **Structured Query Engine (Phase 5)**: Resolves temporal queries ("latest HbA1c", "previous vs latest glucose", "lab trends over 6 months") directly against structured SQL measurements.
   - **Evidence Grounding & Citation Verification (Phase 6)**: Atomic claim extraction, source reconciliation, multi-facility contradiction detection, clinical negation preservation, and citation purification. Zero fabricated citations; fail-closed abstention when evidence is absent.

6. **Physician Clinical Summary Engine (`System 6`)**:
   - One-click executive digest generation for consulting physicians.
   - Structured tabular briefing: active conditions, active prescriptions, known allergies, abnormal lab panels, key longitudinal milestones.
   - 48-hour time-bound secure sharing and print-optimized PDF generation.

---

## 3. Technology Stack

### Frontend
- **Framework**: React 19 (`19.2.8`), React DOM (`19.2.8`)
- **Language**: TypeScript (`~6.0.2`)
- **Build Tool**: Vite (`8.2.1`)
- **Styling**: Tailwind CSS v4 (`4.3.3`) with `@tailwindcss/vite` and Vanilla CSS design tokens
- **UI Components & Icons**: Custom Apple-inspired Warm Neutral design system, Lucide React (`1.31.0`), Framer Motion (`13.1.0`), Class Variance Authority (`0.7.1`), `clsx`, `tailwind-merge`
- **Charts & Visualization**: Recharts (`3.10.1`)
- **State & Data Fetching**: TanStack React Query (`5.101.4`), React Context API (`AuthContext`, `ThemeContext`, `UIContext`, `UserContext`)
- **Forms & Validation**: React Hook Form (`7.85.0`), Zod (`4.4.3`), `@hookform/resolvers`
- **Routing**: React Router DOM v7 (`7.18.2`)
- **HTTP Client**: Axios (`1.19.0`) with interceptors for token management

### Backend
- **Framework**: FastAPI (`0.141.1`), Starlette (`1.6.0`)
- **Server**: Uvicorn (`0.53.0`, `uvicorn[standard]`)
- **Language & Runtime**: Python 3.10+ (Verified on Python `3.13.7`)
- **ORM & Data Layer**: SQLAlchemy 2.0 (`2.0.54`), Alembic (`1.20.0`)
- **Database Support**: SQLite (default local file `chronanexus.db`), PostgreSQL 17 with `psycopg` (`3.3.6`) and `pgvector` (`0.5.1`)
- **Vector Database**: ChromaDB (`1.5.9`) persisted in `data/chroma_db` (collection `chronanexus_clinical_chunks`)
- **Embeddings**: Sentence-Transformers (`6.1.0`) with local cached `BAAI/bge-small-en-v1.5` (384 dimensions)
- **Document Processing**: PyMuPDF / Fitz (`1.27.2.3`)
- **Validation & Settings**: Pydantic v2 (`2.13.3`), `pydantic-settings` (`2.15.0`)
- **Security & Authentication**: PyJWT (`2.15.1`), Passlib / Bcrypt (`5.0.0`)
- **LLM Reasoning**: Ollama (`llama3.2:3b` at `http://localhost:11434`) with deterministic mock provider fallback for offline testing

---

## 4. Current Implementation Status

| Phase | Description | Status | Verification Evidence |
|---|---|---|---|
| **Phase 0** | Codebase Stabilization & Safe Concurrency | **COMPLETE** | 141 backend pytest tests passing, zero data loss |
| **Phase 1** | Test Baseline & Synthetic Benchmark Fixtures | **COMPLETE** | 12-scenario synthetic benchmark harness (`tests/benchmarks/retrieval_benchmark.py`) |
| **Phase 2** | Database Schema & Clinical Data Provenance | **COMPLETE** | `Allergy` model, LOINC/RxNorm terminology catalogs, Alembic 003 migration |
| **Phase 3** | Complete Document Ingestion & Table Parsing | **COMPLETE** | PyMuPDF table parser, boundary chunking, dual SHA-256 deduplication, Alembic 004 migration |
| **Phase 4** | Hybrid Retrieval, ChromaDB & Ollama Grounding | **COMPLETE** | Dense BGE + BM25 Okapi + RRF, Ollama integration, adversarial grounding audit (Verdict: PASS) |
| **Phase 5** | Structured Clinical Queries & Longitudinal Trends | **COMPLETE** | Deterministic query intent detector, temporal aggregation, unit mismatch blocking, Recharts trend charts |
| **Phase 6** | Claim-Level Evidence Grounding & Verification | **COMPLETE** | Atomic claim decomposition, source reconciliation, multi-facility conflict detection, zero false attribution |
| **Phase 7** | Frontend UI/UX Redesign & Data Remediation | **COMPLETE** | Apple Health warm neutral UI, dynamic DOB age calculation, verified IDs, dark/light theme toggle |

---

## 5. Architectural & System Boundaries

- **Local-First Privacy**: Designed to run on consumer hardware without sending unencrypted health records to external cloud APIs. All document parsing, embeddings, and vector similarity search occur locally.
- **Fail-Closed Patient Identity**: Every RAG and chat interaction requires an authenticated `patient_id`. Requests with missing or invalid patient contexts return fail-closed errors.
- **Strict Database Protection**: Test fixtures and benchmarks are protected by an engine execution listener that intercepts any attempt to mutate production database files during automated test runs.
- **Clinical Non-Prescribing Disclaimer**: All drug-allergy alerts and trend analyses are explicitly categorized as clinical decision support references, not automated prescribing mandates.
