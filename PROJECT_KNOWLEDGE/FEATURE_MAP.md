# Feature-to-Code Map — ChronaNexus

This document maps every implemented platform capability to its exact backend and frontend source files, execution pathways, inputs, outputs, relevant tests, and extension points.

---

## 1. Authentication & Session Management

- **Description**: Secure registration, login, JWT token issuance, session refresh, and protected route gating.
- **Backend Implementation**:
  - Router: `backend/app/routers/auth.py`
  - Service: `backend/app/services/auth_service.py`
  - Security Core: `backend/app/core/security.py`
  - Model: `backend/app/models/user.py`
- **Frontend Implementation**:
  - Context: `src/contexts/AuthContext.tsx`
  - Service: `src/services/auth.service.ts`
  - Routing: `src/routes/ProtectedRoute.tsx`, `src/routes/AppRoutes.tsx`
  - Pages: `src/pages/Auth/LoginPage.tsx`, `src/pages/Auth/SignupPage.tsx`, `src/pages/Auth/ForgotPasswordPage.tsx`
- **Execution Path**: User credentials -> `POST /api/v1/auth/login` -> `auth_service.authenticate_user()` -> `verify_password()` -> `create_access_token()` -> Bearer token stored in browser localStorage.
- **Relevant Tests**: `backend/tests/test_auth.py`
- **Extension Point**: Add multi-factor authentication or OAuth provider in `backend/app/routers/auth.py` and `src/pages/Auth/OTPVerificationPage.tsx`.

---

## 2. Document Ingestion, Table Parsing & Deduplication

- **Description**: Ingests multi-page PDFs, detects tables, converts unruled lab tables to Markdown, protects atomic table rows, extracts entities, and enforces dual SHA-256 deduplication.
- **Backend Implementation**:
  - Router: `backend/app/routers/documents.py`
  - PDF Extractor: `backend/app/ai/extractors/pdf_extractor.py`
  - Clinical Chunker: `backend/app/ai/chunker.py`
  - Ingestion Orchestrator: `backend/app/ai/ingestion/orchestrator.py`
  - Models: `backend/app/models/report.py`, `backend/app/models/document_chunk.py`
- **Frontend Implementation**:
  - Modal: `src/components/dialogs/UploadModal.tsx`
  - Service: `src/services/report.service.ts`
- **Execution Path**: PDF upload -> `POST /api/v1/documents/upload` -> binary SHA-256 check -> `PyMuPDF` table detection & page block extraction -> `ClinicalChunker.chunk_document()` -> BGE embedding -> ChromaDB vector insertion -> SQL `DocumentChunk` and `MedicalReport` update.
- **Relevant Tests**: `backend/tests/test_phase3_ingestion.py`, `backend/tests/test_pdf_extractor.py`, `backend/tests/test_chunker.py`
- **Extension Point**: Extend OCR support for image formats in `backend/app/ai/extractors/ocr_extractor.py`.

---

## 3. Medical Document Vault

- **Description**: Document explorer providing category filtering, search, dynamic indexed storage volume calculations, and document detail inspection.
- **Backend Implementation**:
  - Router: `backend/app/routers/reports.py`
  - Service: `backend/app/services/storage_service.py`
- **Frontend Implementation**:
  - Page: `src/pages/Vault/VaultPage.tsx`
  - Card: `src/components/cards/ReportCard.tsx`
  - Service: `src/services/report.service.ts`
- **Execution Path**: `GET /api/v1/reports` -> filtered by category/query -> rendered in responsive grid/table with real computed storage size (`totalIndexedBytes`).
- **Relevant Tests**: `backend/tests/test_reports.py`, `backend/tests/test_documents_api.py`
- **Extension Point**: Add batch document export / zip download in `backend/app/routers/reports.py`.

---

## 4. Longitudinal Health Timeline & Multi-Facility Aggregator

- **Description**: Aggregates diagnoses, medications, lab tests, and hospital encounters into a unified chronological stream from 2019 to present. Distinguishes clinical encounter dates from document upload dates and flags cross-facility concurrent conflicts.
- **Backend Implementation**:
  - Router: `backend/app/routers/timeline.py`
  - Models: `backend/app/models/timeline.py`, `backend/app/models/clinical_entity.py`
  - Schemas: `backend/app/schemas/timeline.py`
- **Frontend Implementation**:
  - Page: `src/pages/Timeline/TimelinePage.tsx`
  - Card: `src/components/cards/TimelineCard.tsx`
  - Service: `src/services/timeline.service.ts`
- **Execution Path**: `GET /api/v1/timeline` -> queries `TimelineEvent`, `MedicalReport`, `Disease`, `Medication` -> sorts chronologically -> flags `isUnknownDate` and cross-facility conflicts on identical dates -> returns JSON.
- **Relevant Tests**: `backend/tests/test_timeline.py`, `backend/tests/test_timeline_and_lab_trends.py`
- **Extension Point**: Add calendar month clustering and export to iCal in `backend/app/routers/timeline.py`.

---

## 5. Clinical Biomarker Lab Trends & Analytical Graphing

- **Description**: Longitudinal tracking of patient lab analytes across time. Evaluates values, detects incompatible units, flags cross-facility contradictions, and computes percentage changes with LOINC standardization.
- **Backend Implementation**:
  - Router: `backend/app/routers/patients.py` (`/me/labs/analytes`, `/me/labs/trends`)
  - Terminology Catalog: `backend/app/clinical/terminology/biomarkers.py`
  - Models: `backend/app/models/clinical_entity.py`
- **Frontend Implementation**:
  - Chart: `src/components/charts/ClinicalTrendChart.tsx`
  - Card: `src/components/cards/ClinicalTrendCard.tsx`
  - Service: `src/services/patient.service.ts`
- **Execution Path**: `GET /api/v1/patients/me/labs/trends?analyte=...` -> LOINC canonical lookup -> queries `lab_results` -> chronological sorting -> unit validation -> percentage delta -> rendered in accessible Recharts line graph.
- **Relevant Tests**: `backend/tests/test_timeline_and_lab_trends.py`, `backend/tests/test_structured_queries.py`
- **Extension Point**: Support multi-analyte dual Y-axis comparison in `ClinicalTrendChart.tsx`.

---

## 6. Structured Clinical Queries & Temporal Reasoning (Phase 5)

- **Description**: Deterministic handling of specific clinical inquiries ("What was my latest glucose?", "Compare previous vs latest cholesterol", "Which lab values increased in the past 6 months?") directly against SQL measurements without stochastic LLM hallucination.
- **Backend Implementation**:
  - Models: `backend/app/clinical/structured_query/models.py`
  - Intent Detector: `backend/app/clinical/structured_query/detector.py`
  - Query Engine: `backend/app/clinical/structured_query/engine.py`
  - Router: `backend/app/routers/chat.py`
  - Service: `backend/app/services/chat_service.py`
- **Frontend Implementation**:
  - Bubble Integration: `src/components/cards/ChatBubble.tsx`
  - Types: `src/types/chat.ts` (`StructuredTrendData`, `MeasurementPoint`)
- **Execution Path**: User chat message -> `StructuredQueryDetector.detect_intent()` -> `StructuredClinicalQueryEngine.execute()` -> parameterized SQL query on `lab_results` -> trend classification -> returned inside `ChatMessage.structuredTrend`.
- **Relevant Tests**: `backend/tests/test_structured_queries.py` (14 comprehensive tests)
- **Extension Point**: Add renal function (eGFR vs Creatinine) calculated ratios in `engine.py`.

---

## 7. Hybrid RAG Pipeline & Multi-Stage Retrieval (Phase 4)

- **Description**: Dual-channel dense vector + lexical keyword retrieval merged via Reciprocal Rank Fusion ($k=60$).
- **Backend Implementation**:
  - Coordinator: `backend/app/ai/rag/pipeline.py`
  - Hybrid Retriever: `backend/app/ai/rag/hybrid_retriever.py`
  - Lexical Retriever: `backend/app/ai/rag/bm25_retriever.py`
  - Vector Store: `backend/app/ai/retrieval.py` (`ChromaDBVectorStore`)
  - Embeddings: `backend/app/ai/embeddings.py` (`BGEEmbeddingProvider`)
  - Reranker: `backend/app/ai/rag/reranker.py`
- **Execution Path**: Query -> `HybridRetriever.retrieve()` -> ChromaDB query (top 15) + BM25Okapi query (top 15) -> Reciprocal Rank Fusion -> Top 5 fused chunks -> RAG context builder -> Ollama LLM.
- **Relevant Tests**: `backend/tests/test_rag_pipeline.py`, `backend/tests/test_hybrid_retriever.py`, `backend/tests/test_chromadb_sync.py`
- **Extension Point**: Configure reranker cross-encoder model in `reranker.py` for fine-grained semantic scoring.

---

## 8. Claim-Level Evidence Grounding & Citation Verification (Phase 6)

- **Description**: Decomposes generated AI answers into individual clinical assertions, cross-checks every claim against authenticated patient database records and retrieved chunks, corrects false report attributions, detects multi-facility contradictions, and strips ungrounded citations.
- **Backend Implementation**:
  - Models: `backend/app/clinical/verification/models.py`
  - Claim Extractor: `backend/app/clinical/verification/claim_extractor.py`
  - Evidence Verifier: `backend/app/clinical/verification/evidence_verifier.py`
  - Answer Corrector: `backend/app/clinical/verification/answer_corrector.py`
  - Citation Validator: `backend/app/clinical/verification/citation_validator.py`
  - Pipeline: `backend/app/clinical/verification/pipeline.py`
- **Frontend Implementation**:
  - Citations Display: `src/components/cards/ChatBubble.tsx`
- **Execution Path**: Raw LLM answer text -> `ClaimExtractor.extract_claims()` -> `EvidenceVerifier.verify_claim()` -> `AnswerCorrector.reconcile()` -> `CitationValidator.purify_citations()` -> verified answer string + enriched citations.
- **Relevant Tests**: `backend/tests/test_evidence_grounding.py` (17 tests), `tests/benchmarks/test_adversarial_grounding.py` (10 tests)
- **Extension Point**: Add natural language inference (NLI) contradiction scoring model for complex narrative clinical notes.

---

## 9. Drug-Allergy & Cross-Reactivity Safety Engine

- **Description**: Immunological cross-reactivity warning system linking structured patient drug allergies with proposed medications (e.g., Penicillin allergy cross-reacting with Amoxicillin or Cephalosporins).
- **Backend Implementation**:
  - Model: `backend/app/models/allergy.py`
  - Engine: `backend/app/clinical/terminology/allergies.py`
  - Structured Retriever: `backend/app/ai/rag/structured_retriever.py`
- **Frontend Implementation**:
  - Pill Alert: `src/pages/Dashboard/DashboardPage.tsx`
  - Summary Table: `src/pages/DoctorSummary/DoctorSummaryPage.tsx`
- **Execution Path**: Medication query or review -> `retrieve_allergies()` -> checks patient `Allergy` records -> evaluates beta-lactam / cephalosporin cross-reactivity rules -> attaches `CLINICAL SAFETY ALERT` with non-prescribing disclaimer.
- **Relevant Tests**: `backend/tests/test_allergy_and_provenance.py`
- **Extension Point**: Expand catalog to food-drug interactions in `backend/app/clinical/terminology/allergies.py`.

---

## 10. Physician Clinical Summary & Secure Sharing

- **Description**: Automated medical history digest structured specifically for physician review and consultations. Includes sticky section navigation, abnormal lab alerts, and 48-hour password-protected share token generation.
- **Backend Implementation**:
  - Router: `backend/app/routers/summaries.py`
  - Service: `backend/app/services/summary_service.py`
  - Model: `backend/app/models/summary.py`
- **Frontend Implementation**:
  - Page: `src/pages/DoctorSummary/DoctorSummaryPage.tsx`
  - Service: `src/services/summary.service.ts`
- **Execution Path**: `GET /api/v1/summaries/doctor-summary` -> compiles active diagnoses, medications, abnormal labs, and timeline highlights -> rendered with sticky anchor navigation and print CSS styles (`print:hidden`).
- **Relevant Tests**: `backend/tests/test_summaries.py`
- **Extension Point**: Add PDF server-side rendering using ReportLab or WeasyPrint.

---

## 11. Global Search (Command-K)

- **Description**: Fast keyboard-accessible global search across all clinical documents, diagnoses, medications, and timeline milestones.
- **Backend Implementation**:
  - Router: `backend/app/routers/search.py`
- **Frontend Implementation**:
  - Modal: `src/components/dialogs/GlobalSearchModal.tsx`
  - Service: `src/services/search.service.ts`
  - Trigger: `src/components/layout/TopBar.tsx`
- **Execution Path**: User types `Ctrl+K` or `Cmd+K` -> `GET /api/v1/search?q=...` -> searches across SQL entities -> grouped results displayed with instant navigation shortcuts.
- **Relevant Tests**: `backend/tests/test_search.py`
- **Extension Point**: Add search history caching in browser localStorage.

---

## 12. Apple-Inspired UI/UX & Class-Based Theme Switching

- **Description**: Warm neutral Apple-inspired healthcare design system with class-based Light, Dark, and System mode switching.
- **Frontend Implementation**:
  - CSS & Tokens: `src/index.css` (`@custom-variant dark (&:where(.dark, .dark *));`)
  - Context: `src/contexts/ThemeContext.tsx`
  - Header Toggle: `src/components/layout/TopBar.tsx`
  - Auth Toggle: `src/components/layout/AuthLayout.tsx`
- **Execution Path**: Theme selection -> updates `ThemeContext` state -> updates `document.documentElement` class list -> persists in `localStorage.setItem('chronanexus_theme')`.
- **Extension Point**: Add high-contrast accessibility theme in `src/index.css`.
