# ChronaNexus — Current State Architecture and Retrieval Audit

> **Document ID:** `01_CURRENT_STATE_AUDIT.md`  
> **Repository:** ChronaNexus (`C:\chromaNexus`)  
> **Audit Date:** 2026-10-17  
> **Author:** Principal Software Architect & AI/RAG Engineer  
> **Status:** Authoritative Baseline Audit  

---

## 1. Executive Overview & Repository Condition

ChronaNexus is designed as a privacy-first, longitudinal medical intelligence platform. The project is split into:
1. A **modern React 19 + TypeScript + Vite + TailwindCSS 4 frontend** (`src/`) featuring an Apple Health-inspired design system with comprehensive pages for Dashboard, Medical Vault, Reports Directory, Medical Timeline, AI Chat Assistant, Doctor Summary, Patient Profile, and Settings.
2. A **FastAPI + SQLAlchemy backend** (`backend/app/`) with support for SQLite (`chronanexus.db`) and PostgreSQL + pgvector (`document_chunks`), structured domain models, document ingestion pipeline, clinical entity extraction, hybrid retrieval, and AI clinical assistant services.

### 1.1 Git Status & Workspace Integrity
- **Current Branch:** `main` (synchronized with `origin/main`).
- **Working Tree Cleanliness:** Clean. The only modified tracked file is `.gitignore` (which safely ignores `/open-source-references/`). Untracked files include the user's specification `ChronaNexus_Open_Source_Application_Alignment.docx` and the newly created `docs/open-source-analysis/` deliverable directory.
- **Reference Repositories:** All 14 reference repositories are isolated inside `C:\chromaNexus\open-source-references\` and excluded from Git tracking.
- **Database File:** `chronanexus.db` (184 KB SQLite file with seeded demonstration patient Alex Vance `pat_alex_vance_001`).

---

## 2. System Inventory & File Manifest

### 2.1 Backend Architecture (`backend/app/`)

| Module / Directory | Key Files | Functional Purpose |
|---|---|---|
| **Core** | `core/config.py`, `core/database.py`, `core/security.py` | Pydantic Settings (CORS, token expiration, database URL, LLM/OCR configurations), SQLAlchemy SessionLocal factory, and password hashing / JWT generation. |
| **Domain Models** | `models/user.py`, `models/patient.py`, `models/report.py`, `models/clinical_entity.py`, `models/timeline.py`, `models/chat.py`, `models/summary.py`, `models/document_chunk.py` | Relational tables for Users, Patients, Medical Reports, Extracted Entities, Diseases, Medications, Lab Results, Timeline Events, Chat Threads/Messages, Doctor Summaries, and Document Chunks (with pgvector embedding column). |
| **API Routers** | `routers/auth.py`, `routers/users.py`, `routers/patients.py`, `routers/reports.py`, `routers/documents.py`, `routers/timeline.py`, `routers/chat.py`, `routers/summaries.py`, `routers/search.py` | FastAPI endpoint definitions mounted at `/api/v1` for patient onboarding, vault upload/download, timeline events, AI conversational Q&A, and clinical summaries. |
| **Domain Services** | `services/auth_service.py`, `services/chat_service.py`, `services/summary_service.py`, `services/storage_service.py`, `services/seed_data.py` | Business logic for session authentication, chat orchestration, longitudinal summary compilation, local file storage, and demo database seeding. |
| **Document Ingestion** | `ai/extractors/pdf_extractor.py`, `ai/document_processor.py`, `ai/chunker.py`, `ai/ocr/`, `ai/ingestion/orchestrator.py`, `ai/ingestion/ingestion_status.py` | Text extraction from PDF/TXT, character cleanup, OCR fallback (Tesseract/Mock), entity extraction dispatch, document chunking (500 chars / 100 overlap), and status tracking. |
| **Clinical Extraction** | `ai/clinical_extractor/rule_based.py`, `ai/clinical_extractor/llm_extractor.py`, `ai/clinical_extractor/validator.py` | Dual extraction strategy: regular expression entity matching + LLM JSON schema extraction with range and status validation. |
| **Embeddings & Vector Store** | `ai/embeddings.py`, `ai/retrieval.py` | Embedding provider abstraction (Ollama `all-minilm` + fallback CPU hash projector `LocalLightweightEmbeddingProvider`), `InMemoryVectorStore`, and `PostgresVectorStore`. |
| **RAG Retrieval Engine** | `ai/rag/classifier.py`, `ai/rag/query_resolver.py`, `ai/rag/structured_retriever.py`, `ai/rag/hybrid_retriever.py`, `ai/rag/fusion.py`, `ai/rag/reranker.py`, `ai/rag/context_builder.py`, `ai/rag/prompts.py`, `ai/rag/pipeline.py` | Multi-stage RAG: rule-based intent classification, conversation topic resolution, structured relational SQL queries, vector search, rank fusion, clinical reranking, context assembly, and guardrailed generation. |
| **LLM Providers** | `ai/llm/base.py`, `ai/llm/ollama.py`, `ai/llm/gemini.py`, `ai/llm/mock_provider.py` | Provider abstraction supporting local Ollama (Llama 3.2 3B), Google Gemini Flash, and deterministic offline mock provider. |

### 2.2 Frontend Architecture (`src/`)

| Module / Directory | Key Files | Functional Purpose |
|---|---|---|
| **App Shell & Layout** | `components/layout/DashboardLayout.tsx`, `Sidebar.tsx`, `TopBar.tsx`, `AuthLayout.tsx`, `LandingLayout.tsx` | Apple-inspired warm neutral layout (`#FAF8F5`), responsive mobile drawer, navigation, global search modal trigger (`⌘K`), theme toggling. |
| **Pages** | `pages/Dashboard/`, `pages/Vault/`, `pages/Reports/`, `pages/Chat/`, `pages/Timeline/`, `pages/DoctorSummary/`, `pages/Profile/`, `pages/Settings/`, `pages/Auth/` | 11 complete pages implementing patient health overview, document vault, master-detail reports, 3-panel chat workspace, year-scrubber timeline, doctor summary note with print/PDF, and profile/security settings. |
| **API Client & Services** | `services/axios.ts`, `services/chat.service.ts`, `services/report.service.ts`, `services/patient.service.ts`, `services/timeline.service.ts`, `services/summary.service.ts` | Axios instance configured for `http://localhost:8000/api/v1` with Bearer auth token interceptors and fallback to mock data on network error. |
| **Contexts & State** | `contexts/AuthContext.tsx`, `contexts/ThemeContext.tsx`, `contexts/UIContext.tsx`, `contexts/UserContext.tsx` | Application session state, theme persistence in `localStorage`, sidebar open/close state, and synchronized patient profile. |
| **UI Component Library** | `components/ui/` (15 components: Button, Card, Table, Modal, Badge, Input, Search, Tabs, Toast, EmptyState, etc.) | Standardized design token components matching the Apple Health aesthetic. |

---

## 3. Comprehensive Feature-by-Feature Status Audit

| # | ChronaNexus Feature | Current Implementation Location | Current Status | Evidence from Source Code | Known Limitations & Root Cause | Recommended Next Action |
|---|---|---|---|---|---|---|
| 1 | **Patient Onboarding & Authentication** | Backend: `routers/auth.py`, `services/auth_service.py`<br>Frontend: `pages/Auth/LoginPage.tsx`, `SignupPage.tsx`, `OTPVerificationPage.tsx` | **Implemented** (Basic JWT) | `auth_service.py:L14-L65` implements password hashing (bcrypt) and JWT generation (`HS256`). Frontend has complete form validation. | OTP verification is client-side simulated; no SMS gateway (Twilio) or email SMTP verification service configured. | Add production email/SMS OTP delivery and OAuth2/OIDC provider support. |
| 2 | **Patient Data Isolation** | Backend: `models/patient.py`, `routers/chat.py:L22`, `routers/documents.py:L81`, `ai/retrieval.py:L227` | **Partially Implemented** | All API routes enforce `current_patient: Patient = Depends(get_current_patient)` and filter DB queries by `patient_id`. | `retrieval.py:L227` filters by `patient_id` in metadata, but SQLite fallback in `retrieval.py:L278` queries all chunks into Python memory before filtering. Multitenant row-level security (RLS) is not enforced at the database engine level. | Migrate to PostgreSQL with native Row-Level Security (RLS) policies. |
| 3 | **Medical Document Upload** | Backend: `routers/documents.py:L45-L120`, `services/storage_service.py`<br>Frontend: `components/dialogs/UploadModal.tsx`, `pages/Vault/VaultPage.tsx` | **Implemented** | Multipart file upload at `/documents/upload` stores files to `./uploads` and registers `MedicalReport` record with background ingestion task. | Upload only accepts `.pdf` and `.txt`. Medical imaging (DICOM), `.docx`, `.png`, and `.jpeg` scans cannot be uploaded via the current API filter (`ALLOWED_EXTENSIONS = {".pdf", ".txt"}`). | Expand allowed formats to include DICOM, JPEG, PNG, TIFF with MIME validation. |
| 4 | **PDF Parsing & OCR** | Backend: `ai/extractors/pdf_extractor.py:L33-L168`, `ai/ocr/tesseract.py:L9-L100` | **Partially Implemented / Fragile** | `pdf_extractor.py` uses `pypdf` native text extraction. `tesseract.py` uses `pytesseract` + `fitz` (PyMuPDF). | 1. No layout analysis: multi-column lab reports get interleaved into garbled text.<br>2. No table structure extraction: numerical lab tables lose row/column relationships.<br>3. Tesseract binary is not installed on Windows host by default, causing OCR fallback to fail silently. | Integrate structured document parsing with table awareness (DeepDoc / OCRmyPDF / LayoutLM). |
| 5 | **Structured Clinical Fact Extraction** | Backend: `ai/clinical_extractor/rule_based.py`, `llm_extractor.py`, `validator.py` | **Broken / Mock Fallback** | `rule_based.py:L16-L98` hardcodes 9 lab tests, 6 medications, 6 diseases, and 3 procedures.<br>`llm_extractor.py:L57` truncates input text to `text[:3000]`. | Ingested reports outside the 9 hardcoded lab tests or 6 medications produce zero structured domain entities unless an external LLM is reachable and returns valid JSON within 3000 chars. | Adopt a comprehensive clinical ontology extractor (LOINC, SNOMED CT, RxNorm) and full-document chunked entity extraction. |
| 6 | **Medical Vault & Document Management** | Backend: `routers/documents.py:L141-L191`<br>Frontend: `pages/Vault/VaultPage.tsx` | **Implemented** | List, download, delete, category filtering, search, and dynamic byte calculation (`VaultPage.tsx`). | Document deletion deletes file from disk and deletes DB row, but does not cleanly scrub vector chunks from `InMemoryVectorStore` or verify cascade deletion in SQLite. | Add explicit vector chunk cleanup on document deletion. |
| 7 | **Document Indexing & Re-indexing** | Backend: `ai/ingestion/orchestrator.py:L173-L215` | **Partially Implemented / Missing Re-indexing** | Document chunking (`DocumentChunker`, 500 chars / 100 overlap) and insertion into `DocumentChunkModel`. | 1. Chunking is naive character-length sliding window without semantic or section boundary awareness.<br>2. There is **no re-indexing endpoint** in the backend API to re-embed or re-parse existing documents when models or schemas change. | Implement section-aware chunking and an administrative re-indexing API endpoint. |
| 8 | **Hybrid Retrieval** | Backend: `ai/rag/classifier.py`, `structured_retriever.py`, `hybrid_retriever.py`, `fusion.py`, `reranker.py` | **Broken / Unreliable** | Detailed analysis in Section 4 below. Intent classification relies on keyword sets; vector search falls back to token hash projections; structured queries use string substring matching. | 1. Semantic search fails when Ollama is offline.<br>2. Structured queries miss lab tests due to nomenclature mismatches (e.g. "Lipid Panel" vs "Cholesterol").<br>3. Reciprocal Rank Fusion uses hardcoded priority weights. | Implement true hybrid dense-sparse retrieval (BM25 + BGE/BioBERT) with clinical alias expansion. |
| 9 | **Follow-up Questions & Context** | Backend: `ai/rag/query_resolver.py:L25-L100`, `routers/chat.py:L100-L104` | **Partially Implemented / Hardcoded** | Bounded history (last 6 messages) passed to `query_resolver.py`. Taxonomy dictionary expands 7 specific conditions (diabetes, cholesterol, hypertension, knee, kidney, heart, dengue). | Any conversation topic outside the 7 hardcoded taxonomy entries fails pronoun resolution and topic continuation. | Replace hardcoded taxonomy with an LLM-based or embedding-based query reformulation step. |
| 10 | **Citation & Evidence Provenance** | Backend: `ai/rag/context_builder.py:L40-L80`, `ai/rag/pipeline.py:L144-L148`, `ai/rag/pipeline.py:L226-L256` | **Partially Implemented / Heuristic** | Context builder constructs `CitationSchema` with document ID, page number, and text excerpt.<br>`_answer_indicates_missing_data` suppresses citations via regex. | Citations are linked based on retrieved chunks rather than verified answer generation attribution. The LLM can generate text not supported by the cited chunk. | Implement sentence-level citation verification (Self-RAG / Corrective RAG attribution). |
| 11 | **Laboratory Values & Trend Analysis** | Backend: `models/clinical_entity.py:L58-L74`, `routers/patients.py`<br>Frontend: `components/charts/VitalsTrendChart.tsx` | **Partially Implemented / Demo Data in UI** | `LabResult` model stores test name, value, unit, reference range, status, test date.<br>`VitalsTrendChart.tsx` displays Recharts trend line. | Frontend chart explicitly flags laboratory time-series as sample/demo because the backend lacks a dedicated longitudinal biomarker time-series aggregation endpoint. | Build a dedicated biomarker aggregation and trajectory analytics API route. |
| 12 | **Medication & Allergy History** | Backend: `models/clinical_entity.py:L39-L56`, `models/patient.py:L29-L32` | **Partially Implemented** | `Medication` model stores name, dosage, frequency, route, start/end dates, status, doctor. | Allergies are stored as a static JSON array on the `Patient` model (`known_allergies`). There is no dedicated `Allergy` entity table, no severity/reaction model, and no drug-allergy interaction checking. | Create a dedicated `AllergyIntolerance` table and clinical allergy checking service. |
| 13 | **Longitudinal Timeline** | Backend: `models/timeline.py`, `routers/timeline.py`<br>Frontend: `pages/Timeline/TimelinePage.tsx` | **Partially Implemented** | `TimelineEvent` model with year, date, title, description, event type, severity, and connected entities. Frontend has year scrubber. | Ingestion orchestrator does **not** auto-generate timeline events from uploaded medical reports. Timeline events only exist via manual POST or initial seed data. | Add an automatic timeline milestone synthesis stage to the document ingestion pipeline. |
| 14 | **Doctor-Ready Summaries** | Backend: `services/summary_service.py:L10-L55`, `routers/summaries.py`<br>Frontend: `pages/DoctorSummary/DoctorSummaryPage.tsx` | **Partially Implemented / Hardcoded Demographics** | Generates summary object with active conditions, medications, abnormal labs, 48-hr share token, and PDF print stylesheet. | `summary_service.py:L32-L45` hardcodes `age=38`, `gender="Male (38M)"`, and specific CAD risk factors for any patient profile. | Compute patient age dynamically from `date_of_birth` and derive clinical risk factors from actual medical entities. |
| 15 | **Privacy, Audit & Data Deletion** | Backend: `routers/documents.py:L173`, `models/user.py:L29` | **Partially Implemented / Missing Audit Log** | User preferences store privacy flags (`strictDataIsolation`, `localAiProcessingOnly`, `auditableLogsEnabled`). | There is no `AuditEvent` or `AuditLog` table in the database to record data access, exports, document deletions, or AI queries. Full patient data export (ZIP/JSON) is missing. | Implement structured audit event logging and a one-click patient data export service. |
| 16 | **Local Model Operation & External Transmission** | Backend: `core/config.py:L21-L28`, `ai/llm/ollama.py`, `ai/embeddings.py:L76` | **Implemented (Architecture) / Offline Fallback Issues** | Config supports Ollama (`llama3.2:3b`, `all-minilm`) for 100% on-device processing. | When Ollama is offline or uninstalled, the system falls back to `MockDeterministicLLMProvider` and `LocalLightweightEmbeddingProvider` (hash projection) rather than an embedded neural model (e.g. ONNX / fastembed). | Bundle an in-process local embedding model (e.g. `fastembed` with BAAI/bge-small-en-v1.5) that requires no external daemon. |
| 17 | **Error Handling & Empty States** | Frontend: `components/ui/EmptyState.tsx`, `ErrorState.tsx`, `Loading.tsx`<br>Backend: FastAPI exception handlers | **Implemented** | All 11 pages implement dedicated loading skeletons, empty state illustrations, and error alerts. | Backend returns generic 500 on unhandled ingestion errors without updating `IngestionStatus` to FAILED in all code paths. | Wrap all pipeline workers in comprehensive error-trapping with user-visible retry states. |
| 18 | **Automated Testing & End-to-End Verification** | Backend: `backend/tests/` (33 test files)<br>Frontend: `npm run build`, `npm run lint` | **Implemented (Unit/Integration)** | 144 backend pytest tests pass cleanly; frontend compiles with 0 TypeScript errors. | Tests heavily mock external services (`MockDeterministicLLMProvider`, `LocalLightweightEmbeddingProvider`, `InMemoryVectorStore`). True end-to-end integration with real PDF OCR and vector search has not been benchmarked. | Build an end-to-end clinical retrieval benchmark using standardized medical evaluation documents. |

---

## 4. Deep-Dive Retrieval Diagnosis: Why Results Are Unreliable

The user's problem statement notes:  
> *"Our current retrieval implementation has produced unreliable results. Instead of immediately patching it, we want to investigate whether existing open-source applications can provide proven functionality that we can reuse, adapt, or integrate."*

A thorough source-level inspection reveals **five root causes** directly responsible for the unreliable retrieval:

### Root Cause 1: Pseudo-Embeddings via CPU Token Hash Projection
- **File:** `backend/app/ai/embeddings.py:L34-L74` (`LocalLightweightEmbeddingProvider`)
- **Evidence:** When Ollama is not running on `http://localhost:11434`, the system falls back to:
  ```python
  # Deterministic token-frequency + hash-projection approach
  vector = [0.0] * self._dim
  words = text.lower().split()
  for i, word in enumerate(words):
      h = hashlib.sha256(word.encode("utf-8")).digest()
      for j in range(0, min(len(h) - 4, self._dim), 4):
          idx = (int.from_bytes(h[j:j+4], "big") + i) % self._dim
          weight = (len(word) / 10.0) * (1.0 / (1.0 + 0.05 * i))
          vector[idx] += weight
  ```
- **Consequence:** This is not a semantic embedding model; it is a hash trick. Words that share no letters have zero similarity. "Hypertension" and "high blood pressure" have orthogonal vectors. "Lipids" and "cholesterol" have orthogonal vectors. "Hgb A1c" and "glycated hemoglobin" have orthogonal vectors. Vector retrieval against this store returns random nearest neighbors based on character hash collisions.

### Root Cause 2: SQLite Table-Scan Vector Search
- **File:** `backend/app/ai/retrieval.py:L270-L318` (`PostgresVectorStore.similarity_search` SQLite branch)
- **Evidence:** When running on SQLite (the default development database `chronanexus.db`), the store executes:
  ```python
  db_chunks = query_obj.all()
  for item in db_chunks:
      emb = item.embedding
      sim = sum(q * e for q, e in zip(query_emb, emb))
  ```
- **Consequence:** Every query loads all chunks into memory and iterates through Python floats. There is no vector index, no Approximate Nearest Neighbor (ANN), no spatial partition, and no BM25 keyword index participating in vector scoring.

### Root Cause 3: Brittle Rule-Based Classification and Incomplete Taxonomy
- **File:** `backend/app/ai/rag/classifier.py:L33-L70` and `backend/app/ai/rag/query_resolver.py:L32-L100`
- **Evidence:** The classifier and query resolver rely on static Python sets:
  - `LAB_KEYWORDS`: 28 hardcoded terms.
  - `MEDICATION_KEYWORDS`: 23 hardcoded terms.
  - `TAXONOMY`: Exactly 7 clinical topics (`diabetes`, `cholesterol`, `hypertension`, `knee`, `kidney`, `heart`, `dengue`).
- **Consequence:** If a patient asks about *asthma*, *thyroid*, *amoxicillin*, *penicillin allergy*, *gallstones*, *lumbar spine*, or *COVID-19*, the resolver cannot determine the active topic, misclassifies the intent as `GENERAL_DOCUMENT_QUERY`, and fails to route the search to the appropriate tables or keywords.

### Root Cause 4: Rigid SQL Substring Matching in Structured Retrieval
- **File:** `backend/app/ai/rag/structured_retriever.py:L47-L51`
- **Evidence:**
  ```python
  if query_keywords:
      t_name = r.test_name.lower()
      if not any(k.lower() in t_name for k in query_keywords):
          continue
  ```
- **Consequence:** If a user queries for "cholesterol" and the laboratory report stores "Lipid Panel" or "Lipid Profile (Standard)", the query keyword `"cholesterol"` does not appear in `"lipid panel"`. The structured retriever discards the exact matching record. The user receives a response claiming no records exist.

### Root Cause 5: Text Truncation in Clinical Extraction
- **File:** `backend/app/ai/clinical_extractor/llm_extractor.py:L57`
- **Evidence:**
  ```python
  prompt = f"CLINICAL REPORT TEXT:\n{text[:3000]}\n\nExtract all entities into the requested JSON schema:"
  ```
- **Consequence:** Multi-page PDF reports (such as a 4-page comprehensive metabolic panel or hospital discharge summary) are truncated at 3,000 characters (approximately 450 words). Any lab tests, medications, or discharge diagnoses located on pages 2, 3, or 4 are discarded before entity extraction even begins.

---

## 5. Summary of Audit Findings

1. **Frontend UI Quality:** The frontend is in an exceptional state — fully implemented, Apple-inspired, accessible, responsive, and completely wired to API client endpoints.
2. **Backend API Foundations:** The FastAPI routes, Pydantic schemas, and SQLAlchemy models provide a solid structural skeleton.
3. **Core Architectural Gaps:** The unreliability reported by the user stems from naive text extraction, a 3,000-character extraction bottleneck, pseudo-hash vector embeddings, static keyword taxonomy sets, and the lack of a standardized clinical terminology catalog.
4. **Conclusion:** Rather than writing complex NLP parsers, terminology mappings, and vector engines from scratch, ChronaNexus should systematically leverage proven components from the 14 reference repositories analyzed in Deliverable 2.
