# ChronaNexus — Functional Alignment Matrix

> **Document ID:** `03_FUNCTION_ALIGNMENT_MATRIX.md`  
> **Source Document:** `ChronaNexus_Open_Source_Application_Alignment.docx`  
> **Date:** 2026-10-17  
> **Author:** Principal Software Architect & Healthcare Data Systems Specialist  
> **Status:** Authoritative Functional Matrix  

---

## 1. Evaluation Methodology & Scoring Scale

Every repository is evaluated against ChronaNexus's 20 core clinical, technical, and privacy requirements using the standardized 0–5 qualitative alignment scale:

- **5 — Direct fit:** Existing functionality matches the ChronaNexus requirement with minimal or no modification. Compatible stack and license.
- **4 — Strong fit:** Most of the required functionality exists; manageable adaptation or refactoring required.
- **3 — Partial fit:** Implements a useful module, workflow, or algorithm, but key capabilities or stack alignments are missing.
- **2 — Indirect fit:** Useful primarily as an architectural pattern, concept reference, or separate subsystem.
- **1 — Minimal fit:** Only a narrow, isolated, or future-facing contribution.
- **0 — No meaningful fit:** Functionality absent, incompatible, or unrelated.

*Note: Alignment scores reflect qualitative technical fit based on direct source code inspection and do not represent comparative benchmark measurements.*

---

## 2. Comprehensive 20-Feature Alignment Matrix

| # | ChronaNexus Feature | Health Assistant | Health Wallet | Fasten Health | Own Chart | ArogyaSutra (DoJ) | Paperless -ngx | RAG Flow | Open EMR | Open MRS | Med plum | OHIF Viewer | Orthanc | GNU Health | ArogyaSutra (IITP) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Personal Record Aggregation** | 4 | 4 | 5 | 4 | 3 | 2 | 2 | 3 | 3 | 4 | 0 | 0 | 2 | 0 |
| 2 | **Patient Medical Vault** | 4 | 5 | 4 | 4 | 4 | 4 | 3 | 2 | 2 | 3 | 1 | 1 | 2 | 0 |
| 3 | **PDF / Scanned Ingestion** | 4 | 3 | 2 | 3 | 3 | 5 | 5 | 2 | 1 | 2 | 0 | 0 | 1 | 0 |
| 4 | **OCR & Table Extraction** | 3 | 3 | 1 | 2 | 3 | 4 | 5 | 1 | 0 | 1 | 0 | 0 | 0 | 2 |
| 5 | **Structured Fact Extraction** | 5 | 3 | 2 | 3 | 4 | 2 | 4 | 2 | 2 | 3 | 0 | 0 | 1 | 2 |
| 6 | **Terminology & Normalization** | 5 | 3 | 4 | 2 | 3 | 0 | 2 | 5 | 5 | 5 | 0 | 0 | 4 | 1 |
| 7 | **Hybrid Search & Retrieval** | 5 | 1 | 2 | 3 | 4 | 3 | 5 | 1 | 1 | 3 | 0 | 0 | 1 | 2 |
| 8 | **Citations & Provenance** | 4 | 1 | 1 | 4 | 5 | 2 | 5 | 1 | 1 | 2 | 0 | 0 | 0 | 1 |
| 9 | **Longitudinal AI Chat** | 5 | 0 | 1 | 4 | 4 | 1 | 4 | 0 | 0 | 2 | 0 | 0 | 0 | 2 |
| 10 | **Conversational Continuity** | 4 | 0 | 0 | 4 | 4 | 0 | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 1 |
| 11 | **Lab Results & Trends** | 5 | 3 | 4 | 4 | 3 | 0 | 1 | 4 | 4 | 4 | 0 | 0 | 3 | 0 |
| 12 | **Medication & Allergy History** | 5 | 4 | 4 | 3 | 3 | 0 | 0 | 5 | 4 | 5 | 0 | 0 | 4 | 0 |
| 13 | **Longitudinal Timeline** | 4 | 3 | 4 | 5 | 4 | 1 | 1 | 3 | 3 | 3 | 1 | 0 | 2 | 0 |
| 14 | **Doctor-Ready Summaries** | 4 | 2 | 2 | 4 | 3 | 0 | 2 | 3 | 2 | 3 | 0 | 0 | 2 | 0 |
| 15 | **Patient Export & Sharing** | 4 | 5 | 4 | 3 | 4 | 2 | 2 | 3 | 2 | 4 | 0 | 0 | 2 | 0 |
| 16 | **FHIR Interoperability** | 4 | 4 | 5 | 2 | 3 | 0 | 1 | 5 | 4 | 5 | 2 | 1 | 2 | 0 |
| 17 | **Auth & Authorization** | 4 | 4 | 4 | 3 | 4 | 3 | 3 | 4 | 4 | 5 | 1 | 2 | 3 | 0 |
| 18 | **Privacy-First / Local Deploy** | 5 | 5 | 4 | 4 | 1 | 4 | 3 | 3 | 3 | 3 | 3 | 4 | 3 | 1 |
| 19 | **Medical Imaging Support** | 2 | 1 | 1 | 0 | 1 | 0 | 1 | 3 | 1 | 2 | 5 | 5 | 2 | 2 |
| 20 | **Monitoring & Evaluation** | 4 | 1 | 2 | 2 | 3 | 3 | 4 | 2 | 3 | 3 | 1 | 1 | 2 | 3 |

---

## 3. Feature-by-Feature Deep Analysis & Recommendations

### Feature 1: Personal Medical Record Aggregation
- **Best Implementation:** **Fasten Health (On-Prem)** (Score: 5)  
  *Evidence:* `backend/pkg/database/` implements multi-source record consolidation, unifying patient encounters, diagnoses, medications, and labs into normalized patient charts.
- **Strongest Alternative:** **Health Assistant** (Score: 4)  
  *Evidence:* `backend/app/facade/bundle.py` aggregates clinical instances across documents and integrations.
- **Maturity:** Production-oriented (Fasten Health / Health Assistant).
- **Recommendation:** **Study / Adapt Fasten Health's data aggregation models** into ChronaNexus's patient profile services.

### Feature 2: Patient-Owned Medical Vault
- **Best Implementation:** **HealthWallet.me** (Score: 5)  
  *Evidence:* `drift_schemas/my_database/` implements a 100% offline-first, client-side encrypted document and record vault.
- **Strongest Alternative:** **Health Assistant** (Score: 4)  
  *Evidence:* `backend/app/instances/document.py` manages uploaded documents with dedup keys (`d1o2c3u4m5e6_add_document_integration_dedup.py`).
- **Maturity:** Production-oriented.
- **Recommendation:** **Retain ChronaNexus's current React/FastAPI Vault**; adapt Health Assistant's document deduplication and HealthWallet's offline encryption concepts.

### Feature 3: PDF and Scanned-Document Ingestion
- **Best Implementation:** **Paperless-ngx** (Score: 5)  
  *Evidence:* `src/paperless/parsers/` provides industrial-strength automated ingestion with OCRmyPDF, deskewing, un-rotation, and PDF/A generation.
- **Strongest Alternative:** **RAGFlow** (Score: 5)  
  *Evidence:* `internal/deepdoc/` implements deep learning layout-aware PDF document parsing.
- **Maturity:** Production-oriented.
- **Recommendation:** **Adapt Paperless-ngx's PDF preprocessing pipeline** (using OCRmyPDF + PyMuPDF) in ChronaNexus's `DocumentIngestionOrchestrator` to replace the fragile `pypdf` native reader.

### Feature 4: OCR and Layout/Table Extraction
- **Best Implementation:** **RAGFlow** (Score: 5)  
  *Evidence:* `internal/deepdoc/` and `internal/parser/tableutil/` reconstruct merged cells, nested headers, and multi-column clinical tables.
- **Strongest Alternative:** **Paperless-ngx** (Score: 4)  
  *Evidence:* `src/paperless/parsers/` integrates OCRmyPDF with Tesseract hOCR output.
- **Maturity:** Production-oriented.
- **Recommendation:** **Adapt table-parsing algorithms from RAGFlow DeepDoc** or incorporate `pdfplumber`/`tabula` table extractors into ChronaNexus to prevent lab table character flattening.

### Feature 5: Structured Medical Fact Extraction
- **Best Implementation:** **Health Assistant** (Score: 5)  
  *Evidence:* `backend/app/ai/processors/nlp/` implements `LangChainStructuredExtractor` injecting LLM tools with Pydantic schemas, backed by standardized catalogs (`backend/data/seeds/`).
- **Strongest Alternative:** **ArogyaSutra (DoJ)** (Score: 4)  
  *Evidence:* `src/lib/aws/extraction.ts` maps AWS Comprehend Medical entities into FHIR models.
- **Maturity:** Production-oriented.
- **Recommendation:** **Reuse and adapt Health Assistant's structured extractor** into ChronaNexus's `LLMClinicalExtractor` to replace the 3,000-character truncation and 9-item regex limitation.

### Feature 6: Clinical Terminology and Normalization
- **Best Implementation:** **Health Assistant** (Score: 5) & **Medplum** (Score: 5)  
  *Evidence:* Health Assistant provides verified seed catalogs for LOINC lab panels (`backend/data/seeds/biomarker_panels.json`) and allergen classifications (`allergies.json`). Medplum provides exhaustive FHIR R4 TypeScript definitions (`packages/fhirtypes/`).
- **Strongest Alternative:** **OpenEMR** (Score: 5)  
  *Evidence:* `src/Entities/Code.php` maps SNOMED CT, LOINC, and RxNorm tables.
- **Maturity:** Production-ready.
- **Recommendation:** **Directly import Health Assistant's seed JSON files** into ChronaNexus (`backend/app/data/seeds/`) and adopt `@medplum/fhirtypes` in the frontend.

### Feature 7: Hybrid Search and Retrieval
- **Best Implementation:** **Health Assistant** (Score: 5) & **RAGFlow** (Score: 5)  
  *Evidence:* Health Assistant (`backend/app/ai/tools/`) executes multi-index search (trigram + full-text + LOINC alias matching) fused via **Reciprocal Rank Fusion (RRF)**. RAGFlow (`internal/agentic_rag/bm25_service.go`) implements enterprise BM25 + dense vector fusion.
- **Strongest Alternative:** **ArogyaSutra (DoJ)** (Score: 4)  
  *Evidence:* `src/lib/rag/retriever.ts` implements adaptive hybrid vector-keyword retrieval.
- **Maturity:** Production-ready.
- **Recommendation:** **Adapt Health Assistant's RRF and clinical alias search** into ChronaNexus's `HybridRetriever`. Pair with an embedded dense retriever (`fastembed` with `bge-small-en-v1.5`) to eliminate token-hash pseudo-embeddings.

### Feature 8: Medical Document Citations and Evidence Provenance
- **Best Implementation:** **RAGFlow** (Score: 5) & **ArogyaSutra (DoJ)** (Score: 5)  
  *Evidence:* RAGFlow (`internal/agentic_rag/citations.go`) computes sentence-level mathematical attribution scores. ArogyaSutra (`src/lib/rag/reflective.ts`) uses **Self-RAG** reflection tokens (`[Supported]`, `[Partially Supported]`, `[No Support]`) to audit generated answers.
- **Strongest Alternative:** **OwnChart** (Score: 4)  
  *Evidence:* `api/ownchart/extract/` creates transparent provenance links for clinical dossiers.
- **Maturity:** Production-ready (RAGFlow) / Advanced implementation (ArogyaSutra).
- **Recommendation:** **Adapt ArogyaSutra's Self-RAG reflection and RAGFlow's attribution scoring** into ChronaNexus's `RAGPipeline` to eliminate irrelevant citations.

### Feature 9: AI Chat Over Longitudinal Medical Records
- **Best Implementation:** **Health Assistant** (Score: 5)  
  *Evidence:* `backend/app/ai/assistance/service.py` and `backend/app/ai/agents/chat_agent.py` implement an agentic clinical assistant with dynamic tool calling, patient memory inspection, and HITL verification.
- **Strongest Alternative:** **OwnChart** (Score: 4) & **ArogyaSutra (DoJ)** (Score: 4)  
  *Evidence:* OwnChart's conversational narrative Q&A (`api/ownchart/llm/`).
- **Maturity:** Production-oriented.
- **Recommendation:** **Adapt Health Assistant's agentic tool-calling architecture** into ChronaNexus's `services/chat_service.py`.

### Feature 10: Follow-up Questions and Conversational Continuity
- **Best Implementation:** **Health Assistant** (Score: 4) & **RAGFlow** (Score: 4)  
  *Evidence:* Health Assistant persists conversation state via LangGraph `AsyncPostgresSaver` checkpointer (`backend/app/ai/graphs/checkpointer.py`). RAGFlow maintains conversational context trees (`internal/agentic_rag/agent.go`).
- **Strongest Alternative:** **OwnChart** (Score: 4)  
  *Evidence:* `api/ownchart/llm/` models multi-turn longitudinal health discussions.
- **Maturity:** Production-oriented.
- **Recommendation:** **Replace ChronaNexus's 7-condition static taxonomy** (`query_resolver.py`) with an LLM-guided query reformulator utilizing conversation history.

### Feature 11: Laboratory Results and Trends
- **Best Implementation:** **Health Assistant** (Score: 5)  
  *Evidence:* `backend/app/models/biomarker_model.py` and `backend/app/services/analytics_service.py` calculate longitudinal trajectories, baseline deltas, unit conversions, and out-of-range anomaly detection.
- **Strongest Alternative:** **Fasten Health** (Score: 4) & **OwnChart** (Score: 4)  
  *Evidence:* Fasten Health's observation dashboard (`frontend/src/app/`).
- **Maturity:** Production-ready.
- **Recommendation:** **Adapt Health Assistant's `analytics_service.py`** into ChronaNexus to provide real backend API endpoints for `VitalsTrendChart.tsx`.

### Feature 12: Medication and Allergy History
- **Best Implementation:** **Health Assistant** (Score: 5) & **Medplum** (Score: 5)  
  *Evidence:* Health Assistant provides full relational models and services for allergies (`app/services/allergy_service.py`), medications, and drug catalogs. Medplum provides validated FHIR `MedicationRequest` and `AllergyIntolerance` schemas.
- **Strongest Alternative:** **OpenEMR** (Score: 5)  
  *Evidence:* `src/Services/AllergyIntoleranceService.php`.
- **Maturity:** Production-ready.
- **Recommendation:** **Add a dedicated `AllergyIntolerance` table to ChronaNexus** using Health Assistant's schema and seed catalog, replacing the current static JSON array on `Patient`.

### Feature 13: Longitudinal Medical Timeline
- **Best Implementation:** **OwnChart** (Score: 5)  
  *Evidence:* `web/app/(app)/timeline/` and `api/ownchart/canonical/` model health events fused with life context into a rich, navigable chronological narrative.
- **Strongest Alternative:** **Health Assistant** (Score: 4) & **ArogyaSutra (DoJ)** (Score: 4)  
  *Evidence:* ArogyaSutra (`src/hooks/useTimeline.ts` and `src/services/timeline.service.ts`).
- **Maturity:** Production-ready.
- **Recommendation:** **Retain ChronaNexus's existing Year-Scrubber Timeline UI**; adapt OwnChart's concept of auto-generating timeline milestones during document ingestion.

### Feature 14: Doctor-Ready Summaries
- **Best Implementation:** **Health Assistant** (Score: 4) & **OwnChart** (Score: 4)  
  *Evidence:* Health Assistant's clinical examination reports and OwnChart's clinical dossiers compile comprehensive, multi-domain provider briefs.
- **Strongest Alternative:** **ChronaNexus Existing Frontend** (Score: 4)  
  *Evidence:* ChronaNexus's `DoctorSummaryPage.tsx` already features a clean, Apple-inspired physician note layout with sticky section navigation and print stylesheets.
- **Maturity:** Production-ready UI / Backend needs dynamic calculation.
- **Recommendation:** **Retain ChronaNexus's Doctor Summary UI**; remediate `summary_service.py` to calculate dynamic patient age, active conditions, and verified risk factors instead of hardcoded strings.

### Feature 15: Patient Data Export and Sharing
- **Best Implementation:** **HealthWallet.me** (Score: 5)  
  *Evidence:* `lib/features/records/` provides export to encrypted JSON, PDF clinical summaries, and QR-code peer sharing.
- **Strongest Alternative:** **Medplum** (Score: 4) & **Fasten Health** (Score: 4)  
  *Evidence:* Exporting full patient records as standardized FHIR R4 Bundles.
- **Maturity:** Production-ready.
- **Recommendation:** **Implement a standard FHIR Bundle JSON and ZIP export endpoint** in ChronaNexus (`/patients/{id}/export`).

### Feature 16: FHIR Interoperability
- **Best Implementation:** **Medplum** (Score: 5) & **Fasten Health** (Score: 5)  
  *Evidence:* Medplum is a 100% native FHIR R4 platform with TypeScript types and validators. Fasten Health ingests and normalizes FHIR Bundles.
- **Strongest Alternative:** **OpenEMR** (Score: 5)  
  *Evidence:* Certified ONC FHIR R4 API.
- **Maturity:** Production-ready.
- **Recommendation:** **Use `@medplum/fhirtypes`** for client-side typing and export validation.

### Feature 17: Authentication and Authorization
- **Best Implementation:** **Medplum** (Score: 5) & **Health Assistant** (Score: 4)  
  *Evidence:* Medplum implements full SMART-on-FHIR, OAuth2, and RBAC. Health Assistant implements session tracking and BYOK scoped provider configuration.
- **Strongest Alternative:** **Fasten Health** (Score: 4)  
  *Evidence:* `backend/pkg/auth/`.
- **Maturity:** Production-ready.
- **Recommendation:** **Retain ChronaNexus's JWT auth**; adapt Health Assistant's session tracking model (`auth_session_model.py`) for multi-device management in Settings.

### Feature 18: Privacy-First / Local Deployment
- **Best Implementation:** **Health Assistant** (Score: 5) & **HealthWallet.me** (Score: 5)  
  *Evidence:* Health Assistant provides full offline local model deployment via Ollama/vLLM without external telemetry. HealthWallet is 100% on-device.
- **Strongest Alternative:** **Fasten Health** (Score: 4) & **OwnChart** (Score: 4)  
  *Evidence:* Fully self-hosted on-premises deployment configurations.
- **Maturity:** Production-ready.
- **Recommendation:** **Bundle local, in-process neural embeddings (`fastembed`)** into ChronaNexus so privacy-first local search works out of the box even when Ollama is not configured.

### Feature 19: Medical Imaging Support (DICOM)
- **Best Implementation:** **OHIF Viewer** (Score: 5) & **Orthanc** (Score: 5)  
  *Evidence:* OHIF Viewer provides modern 2D/3D in-browser DICOM rendering. Orthanc provides a lightweight C++ PACS DICOM server.
- **Strongest Alternative:** **OpenEMR** (Score: 3)  
  *Evidence:* Built-in DICOM viewer templates.
- **Maturity:** Production-ready.
- **Recommendation:** **Defer to Phase 4**. ChronaNexus MVP indexes imaging *reports* and text summaries; raw DICOM binary viewing is not required for the text/RAG milestone.

### Feature 20: Monitoring, Evaluation & Quality Assurance
- **Best Implementation:** **Health Assistant** (Score: 4) & **RAGFlow** (Score: 4)  
  *Evidence:* Health Assistant (`backend/tests/`) provides extensive unit test suites for AI task dispatch, BYOK contracts, and tenant isolation. RAGFlow (`test/benchmark/`) provides quantitative evaluation suites for retrieval accuracy.
- **Strongest Alternative:** **ArogyaSutra (IITP-CSE)** (Score: 3)  
  *Evidence:* MedQA evaluation benchmarks.
- **Maturity:** Production-ready.
- **Recommendation:** **Adopt a fixed synthetic evaluation dataset** based on RAGFlow's benchmark metrics (Recall@5, reciprocal rank, citation precision) to validate ChronaNexus's retrieval pipeline.

---

## 4. Key Strategic Conclusions from Matrix

1. **Top Contributor for Clinical Engine:** **Health Assistant** is the highest-value match across clinical models, LOINC catalogs, allergy tracking, and hybrid Reciprocal Rank Fusion search.
2. **Top Contributor for Document Vision:** **RAGFlow DeepDoc** and **Paperless-ngx** provide the exact solutions needed to fix PDF layout corruption and table flattening.
3. **Top Contributor for RAG Guardrails:** **ArogyaSutra (DoJ)** provides the Corrective RAG (CRAG) and Self-Reflective citation audit mechanisms needed to stop fabricated or unrelated citations.
4. **Top Contributor for Interoperability:** **Medplum** provides the standard TypeScript types and FHIR validation libraries.
5. **Immediate Architectural Simplification:** Deferring OHIF Viewer, Orthanc, OpenMRS, and GNU Health prevents bloat and keeps ChronaNexus focused strictly on its core mission: an intelligent, privacy-first personal medical memory platform.
