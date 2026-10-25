# ChronaNexus — Deep Analysis of 14 Reference Open-Source Repositories

> **Document ID:** `02_REPOSITORY_DEEP_ANALYSIS.md`  
> **Source Document:** `ChronaNexus_Open_Source_Application_Alignment.docx`  
> **Manifest:** `C:\chromaNexus\open-source-references\REPOSITORY_MANIFEST.md`  
> **Analysis Date:** 2026-10-17  
> **Author:** Principal Software Architect & Open-Source Systems Analyst  
> **Status:** Authoritative Repository Deep-Dive  

---

## 1. Introduction & Methodology

This document presents a comprehensive, evidence-based engineering audit of all 14 open-source applications collected in `C:\chromaNexus\open-source-references\`. Every repository was checked out locally in Phase 1 and inspected directly at the source code level.

For each repository, this audit analyzes:
1. **Provenance & Versioning:** Local folder, canonical URL, branch, and commit hash.
2. **Licensing & Reusability:** Root and module licenses, third-party constraints, and commercial reuse flags.
3. **Architecture & Stack:** Language, frameworks, database schemas, and directory topology.
4. **Core Capabilities:** Document ingestion, OCR, clinical entity extraction, data modeling, and AI/RAG subsystems.
5. **Security & Deployment Boundaries:** Local execution vs external API transmission, container requirements.
6. **Classification & Recommendation:** One or more standardized classifications with concrete evidence.

---

## 2. Deep-Dive Repository Evaluations

```
================================================================================
REPOSITORY 1: Health Assistant
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** Health Assistant (`health-assistant-io/health-assistant`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\health-assistant`
- **Canonical Repository URL:** `https://github.com/health-assistant-io/health-assistant`
- **Checked-Out Branch:** `main` | **Commit Hash:** `71866b9b701b07ae014bd5ee2dbef17e0d33ee38`
- **Primary Languages:** Python 3.12 (Backend), TypeScript (Frontend)
- **Frameworks:** FastAPI, SQLAlchemy, Alembic, Celery, LangChain, LangGraph, React, TailwindCSS, Vite.

### 2. Licensing & Legal Observations
- **Root License:** **Apache License 2.0** (`open-source-references/health-assistant/LICENSE`).
- **Permissions:** Highly permissive open-source license. Permits commercial use, modification, distribution, and sublicensing. Requires preservation of copyright notices and disclaimer.
- **Component Licensing:** No restrictive copyleft or noncommercial dependencies detected in core code.
- **Suitability for ChronaNexus:** 100% license-compatible. Direct code reuse, module adaptation, or library extraction is fully permitted under Apache-2.0.

### 3. Architecture & Key Modules
- **Backend Entry Point:** `backend/app/main.py` (FastAPI app with lifespan context and router registration).
- **Core Models:** `backend/app/models/`:
  - `biomarker_model.py`: Longitudinal biomarker observations with reference ranges and units.
  - `anatomy_model.py`: Anatomical structures and systemic mappings.
  - `audit_model.py`: Comprehensive audit event logging (`audit_events` table).
  - `auth_session_model.py`: Multi-device session tracking and token management.
- **Clinical Seed Catalogs:** `backend/data/seeds/`:
  - `biomarker_panels.json`: Standardized clinical lab panels with LOINC codes, reference ranges, and unit definitions.
  - `biomarker_states.json`: Standard clinical qualitative states (High, Low, Normal, Borderline, Critical).
  - `allergies.json`: Standardized allergen catalog with typical reactions and severity levels.
  - `clinical_event_types.json`: Structured event ontology for longitudinal milestones.
- **AI & RAG Pipeline:** `backend/app/ai/`:
  - `processors/ocr/`: `LangChainOCRProcessor` converts images/PDFs/DICOMs to structured text.
  - `processors/nlp/`: `LangChainStructuredExtractor` maps text to structured medical entities via LLM function calling.
  - `assistance/service.py`: `AIAssistanceService` agentic copilot orchestrator.
  - `tools/`: LangChain clinical query tools (`search_biomarkers`, `search_medications`, `search_allergens`) using **Reciprocal Rank Fusion (RRF)** over trigram, full-text, and alias indices.
  - `graphs/`: LangGraph state machine with persistent `AsyncPostgresSaver` checkpointing.

### 4. Technical Assessment & Strengths
- Matches ChronaNexus's technology stack directly: **FastAPI + SQLAlchemy + React**.
- Solves ChronaNexus's exact search defect: Its hybrid biomarker search combines LOINC aliases, full-text search, and trigram matching with Reciprocal Rank Fusion, meaning "blood sugar", "glucose", "FBS", and "A1c" all resolve correctly without brittle hardcoding.
- Implements comprehensive clinical catalogs for allergens, biomarkers, and anatomy.

### 5. Limitations & Caveats
- Uses Celery + Redis for asynchronous background tasks, requiring message broker infrastructure.
- Marked as active beta development; database migrations must be carefully decoupled from their specific tenant model.

### 6. Classification & Recommendation
- **Classification:** **Adapt selected modules** & **Reuse directly** (subject to schema mapping).
- **Primary Reuse Targets:**
  1. `backend/data/seeds/biomarker_panels.json` and `allergies.json` (instant resolution for ChronaNexus's missing clinical ontology).
  2. Hybrid alias search and Reciprocal Rank Fusion tool patterns from `backend/app/ai/tools/`.
  3. `LangChainStructuredExtractor` and prompt guardrails from `backend/app/ai/processors/nlp/`.

---

```
================================================================================
REPOSITORY 2: HealthWallet.me
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** HealthWallet.me (`LifeValue/HealthWallet.me`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\healthwallet-me`
- **Canonical Repository URL:** `https://github.com/LifeValue/HealthWallet.me`
- **Checked-Out Branch:** `master` | **Commit Hash:** `602993e8de9a8c9429e22472c82a05512d8f9add`
- **Primary Languages:** Dart (Flutter), Swift, Kotlin
- **Frameworks:** Flutter, Drift (SQLite ORM for Dart), Bloc state management.

### 2. Licensing & Legal Observations
- **Root License:** **GNU General Public License v3.0 (GPL-3.0)** (`open-source-references/healthwallet-me/LICENSE.md`).
- **Permissions:** Strong copyleft license. Any derivative work or combined program distributed to users must be licensed under GPL-3.0 with source code made available.
- **Suitability for ChronaNexus:** Direct code copying into ChronaNexus is **not recommended** due to copyleft obligations and cross-language incompatibility (Dart vs Python/TypeScript).

### 3. Architecture & Key Modules
- **Application Core:** `lib/app/view/app.dart` and `lib/main.dart`.
- **Database & Offline Vault:** `drift_schemas/my_database/` (versions 1 through 7):
  - SQLite database schemas modeled in Drift for offline-first patient medical record storage.
  - Complete tables for FHIR resources, document scans, cryptographic keys, and patient profiles.
- **Document Scanning & OCR:** `lib/features/scan/`:
  - Camera-based document edge detection, document cropping, and local OCR text extraction.
- **Provider Import Integration:** `assets/readme/fasten_local_import.gif` illustrates its reliance on Fasten Health for provider data sync.

### 4. Technical Assessment & Strengths
- Superb mobile UX for offline-first personal health vaults, QR-code based record sharing, and document scanning.
- Excellent reference for mobile cryptographic key management and local biometric auth.

### 5. Limitations & Caveats
- 100% Flutter/Dart mobile app. Cannot be executed or imported directly into ChronaNexus's React web frontend or FastAPI backend.
- Provider aggregation is not self-contained; it relies on Fasten Health.

### 6. Classification & Recommendation
- **Classification:** **Architecture reference only**.
- **Primary Use:** Study its offline-first data synchronization model, Drift SQLite schema migrations, and patient-owned data export workflows.

---

```
================================================================================
REPOSITORY 3: Fasten Health (On-Prem)
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** Fasten Health On-Prem (`fastenhealth/fasten-onprem`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\fasten-health`
- **Canonical Repository URL:** `https://github.com/fastenhealth/fasten-onprem`
- **Checked-Out Branch:** `main` | **Commit Hash:** `36d92446884e9e20eda8d2b2a0a1115c9c57f7ef`
- **Primary Languages:** Go (Backend), TypeScript / Angular (Frontend)
- **Frameworks:** Go Gin/GORM, Angular, Docker.

### 2. Licensing & Legal Observations
- **Root License:** **GNU General Public License v3.0 (GPL-3.0)** (`open-source-references/fasten-health/LICENSE.md`).
- **Permissions:** Copyleft. Commercial redistribution requires releasing source under GPL-3.0.
- **Suitability for ChronaNexus:** Service integration via external REST API/Docker container is permissible (network boundary); direct source code copying into ChronaNexus would trigger GPL copyleft viral terms.

### 3. Architecture & Key Modules
- **Backend Entry Point:** `backend/cmd/fasten/main.go`.
- **FHIR Normalization & Database:** `backend/pkg/database/`:
  - Normalizes raw clinical data from disparate sources into standardized FHIR R4 Bundles.
  - Relational storage mapping patient demographics, conditions, medications, diagnostic reports, and immunizations.
- **Authentication & Security:** `backend/pkg/auth/`:
  - Local multi-user JWT authentication and role-based access control.

### 4. Technical Assessment & Strengths
- One of the most mature self-hosted personal health record aggregators in open source.
- Substantial data model for personal health record browsing, FHIR Bundle import/export, and family health management.

### 5. Limitations & Caveats
- Stack mismatch: Go backend + Angular frontend. ChronaNexus uses FastAPI (Python) + React.
- Open-source on-premise version disables direct healthcare provider portal scraping (which is reserved for their hosted SaaS product); on-premise works via manual entry or FHIR Bundle upload.
- Large repository footprint (~1.38 GB).

### 6. Classification & Recommendation
- **Classification:** **Architecture reference only** & **Integrate as a separate service** (future consideration for FHIR imports).
- **Primary Use:** Reference for FHIR R4 Bundle parsing, condition categorization, and multi-patient family account modeling.

---

```
================================================================================
REPOSITORY 4: OwnChart
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** OwnChart (`nickpdawson/OwnChart`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\ownchart`
- **Canonical Repository URL:** `https://github.com/nickpdawson/OwnChart`
- **Checked-Out Branch:** `main` | **Commit Hash:** `3dece87abdd4bcecabeba2908b3826fd071db7d9`
- **Primary Languages:** Python (Backend), TypeScript / Next.js (Frontend)
- **Frameworks:** FastAPI, SQLAlchemy, Alembic, Next.js (App Router), TailwindCSS.

### 2. Licensing & Legal Observations
- **Root License:** **PolyForm Noncommercial License 1.0.0** (`open-source-references/ownchart/LICENSE`).
- **Restrictions:** **SOURCE-AVAILABLE, NOT OPEN-SOURCE.** Explicitly forbids commercial use, commercial deployment, or commercial derivative products without written permission from author Nick Dawson.
- **Suitability for ChronaNexus:** **CRITICAL WARNING:** Zero code from OwnChart may be copied into ChronaNexus if ChronaNexus is ever intended for commercial, institutional, or enterprise distribution. It can only be used as an architectural and design reference.

### 3. Architecture & Key Modules
- **Backend Architecture:** `api/ownchart/`:
  - `canonical/`: Canonical health event data schemas.
  - `extract/`: Extraction of clinical events and life events from unstructured text.
  - `ingest/`: Ingestion connectors for Athena, Cerner, Epic, and Apple HealthKit (`docs/HEALTHKIT_MCP_BRIDGE_SPEC.md`).
  - `llm/`: LLM-based narrative generation connecting medical events with life context.
- **Frontend Architecture:** `web/app/`: Next.js application with life-event timeline, clinical dossiers, and evidence-grounded Q&A.

### 4. Technical Assessment & Strengths
- Superb conceptual alignment: OwnChart pioneers the fusion of *clinical records* (diagnoses, labs, prescriptions) with *life events* (relocations, stress, family milestones) into a unified longitudinal narrative.
- Evidence-grounded dossiers: Provides transparent source citations for generated summaries.

### 5. Limitations & Caveats
- Strict PolyForm Noncommercial license creates severe commercial legal risk.
- Early alpha stage (version 0.1).

### 6. Classification & Recommendation
- **Classification:** **Architecture reference only** (Strictly non-code adoption).
- **Primary Use:** Study its philosophical data model linking life events to medical milestones, and replicate these concepts independently in ChronaNexus under Apache/MIT clean-room implementations.

---

```
================================================================================
REPOSITORY 5: ArogyaSutra (Dawn-Of-Justice)
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** ArogyaSutra (`Dawn-Of-Justice/ArogyaSutra`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\arogya-sutra`
- **Canonical Repository URL:** `https://github.com/Dawn-Of-Justice/ArogyaSutra`
- **Checked-Out Branch:** `main` | **Commit Hash:** `de7687b5167beedcc8700127dc2f30d6ee1572cf`
- **Primary Languages:** TypeScript / JavaScript
- **Frameworks:** Next.js, React, AWS CDK, TailwindCSS.

### 2. Licensing & Legal Observations
- **Root License:** **MIT License** (`open-source-references/arogya-sutra/LICENSE`).
- **Permissions:** Permissive. Commercial and noncommercial use, modification, and integration permitted with attribution.
- **Suitability for ChronaNexus:** 100% license-compatible.

### 3. Architecture & Key Modules
- **Advanced RAG Engine:** `src/lib/rag/`:
  - `adaptive.ts`: Adaptive retrieval strategy routing based on query complexity.
  - `corrective.ts`: **Corrective RAG (CRAG)** implementation evaluating retrieval quality before generating answers.
  - `reflective.ts`: **Self-Reflective RAG (Self-RAG)** evaluating hallucination and citation support.
  - `planner.ts`: Multi-step query decomposition for complex longitudinal questions.
  - `retriever.ts`: Hybrid vector and keyword retrieval orchestration.
- **Client-Side Cryptography:** `src/lib/crypto/`:
  - `aesGcm.ts`: AES-256-GCM symmetric encryption for health documents.
  - `rsaOaep.ts`: RSA-OAEP asymmetric key exchange for emergency doctor access.
  - `keyDerivation.ts`: PBKDF2 client-side key derivation.
- **Infrastructure:** `infra/lib/arogyasutra-stack.ts` (AWS CDK deploying Bedrock, Textract, HealthLake, DynamoDB, Cognito).

### 4. Technical Assessment & Strengths
- The RAG architecture in `src/lib/rag/` is state-of-the-art: it explicitly implements **Corrective RAG** and **Self-Reflective RAG**, which directly solve ChronaNexus's citation unreliability and hallucination issues.
- Client-side zero-knowledge encryption models in `src/lib/crypto/` provide an excellent design pattern for patient-controlled privacy.

### 5. Limitations & Caveats
- Deep architectural coupling to proprietary AWS managed services (AWS Bedrock, Textract, Comprehend Medical, HealthLake, DynamoDB).
- Cannot be run locally as a standalone open-source server without replacing all AWS service calls with local equivalents (Ollama, local OCR, SQLite/PostgreSQL).

### 6. Classification & Recommendation
- **Classification:** **Adapt selected modules** & **Architecture reference**.
- **Primary Reuse Targets:**
  1. Adapt the **Corrective RAG (CRAG)** and **Self-Reflective RAG** logic from `src/lib/rag/corrective.ts` and `reflective.ts` into ChronaNexus's Python RAG pipeline (`backend/app/ai/rag/`).
  2. Adopt the emergency temporary doctor access cryptographic protocol from `src/lib/crypto/emergency.ts`.

---

```
================================================================================
REPOSITORY 6: Paperless-ngx
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** Paperless-ngx (`paperless-ngx/paperless-ngx`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\paperless-ngx`
- **Canonical Repository URL:** `https://github.com/paperless-ngx/paperless-ngx`
- **Checked-Out Branch:** `dev` | **Commit Hash:** `0cb2cdbfdd91a2078236f8851cd310261284591c`
- **Primary Languages:** Python 3 (Backend), TypeScript / Angular (Frontend)
- **Frameworks:** Django, Celery, Redis, PostgreSQL/SQLite, OCRmyPDF, Tesseract, Whoosh / Tantivy.

### 2. Licensing & Legal Observations
- **Root License:** **GNU General Public License v3.0 (GPL-3.0)** (`open-source-references/paperless-ngx/LICENSE`).
- **Permissions:** Copyleft. Integration as a separate standalone service via REST API is safe and compliant; direct source file copying into ChronaNexus would impose GPL-3.0 obligations.

### 3. Architecture & Key Modules
- **Ingestion & Parsing Pipeline:** `src/paperless/parsers/`:
  - `document.py`: Base parser interface.
  - Implements industrial-grade PDF consumption using **OCRmyPDF**, deskewing, un-rotation, language detection, and PDF/A archiving.
- **Search Subsystem:** `src/documents/search/`:
  - Full-text search engine with fielded queries, boolean logic, and spelling suggestions.
- **AI Classification:** `src/paperless_ai/`:
  - Automated document classification and metadata tagging.

### 4. Technical Assessment & Strengths
- The gold standard in open-source document ingestion, automated OCR, and archival storage.
- Handles messy real-world scans, multi-page PDFs, mobile photos, and rotation issues effortlessly.

### 5. Limitations & Caveats
- General-purpose document management system; has zero native understanding of clinical entities, LOINC codes, FHIR, or longitudinal health graphs.
- Heavy runtime dependencies (Redis, Celery, Tika, OCRmyPDF, Ghostscript, Unpaper).

### 6. Classification & Recommendation
- **Classification:** **Architecture reference only** & **Integrate as a separate service** (optional enterprise archive).
- **Primary Use:** Adapt its PDF pre-processing pipeline patterns (deskewing, PDF/A conversion, OCRmyPDF invocation) into ChronaNexus's ingestion worker.

---

```
================================================================================
REPOSITORY 7: RAGFlow
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** RAGFlow (`infiniflow/ragflow`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\ragflow`
- **Canonical Repository URL:** `https://github.com/infiniflow/ragflow`
- **Checked-Out Branch:** `main` | **Commit Hash:** `543e16738b4883fcb7e70520e0b5849e7e18c9b7`
- **Primary Languages:** Go (Core Backend Server), Python (DeepDoc Document Vision Engine), TypeScript (React Frontend)
- **Frameworks:** DeepDoc, Infinity / Elasticsearch, OceanBase, Docker.

### 2. Licensing & Legal Observations
- **Root License:** **Apache License 2.0** (`open-source-references/ragflow/LICENSE`).
- **Permissions:** Highly permissive open-source license. Commercial use, modification, and integration fully permitted.
- **Suitability for ChronaNexus:** 100% license-compatible.

### 3. Architecture & Key Modules
- **DeepDoc Document Vision Engine:** `internal/deepdoc/` & `internal/parser/`:
  - Visual layout analysis, optical character recognition, and table structure reconstruction.
  - Recognizes merged cells, column alignments, and nested headers in complex tabular PDFs.
- **Agentic RAG Engine:** `internal/agentic_rag/`:
  - `bm25_service.go`: Industrial-grade Okapi BM25 keyword retrieval.
  - `citations.go`: Mathematical snippet-level citation grounding and attribution scoring.
- **Python SDK:** `sdk/python/ragflow_sdk`:
  - Clean Python library allowing external applications to programmatically create datasets, upload files, and execute hybrid RAG queries.

### 4. Technical Assessment & Strengths
- DeepDoc is by far the most advanced document table parser among all 14 repositories. It specifically solves the problem of lab test tables being flattened into garbled text.
- True hybrid retrieval: Combines BM25 keyword search with dense vector embeddings and reranking.

### 5. Limitations & Caveats
- Massive infrastructure footprint: Requires multiple Docker containers (OceanBase, Infinity/ES, MinIO, Redis) and substantial RAM (>8GB). Running the entire RAGFlow stack locally alongside ChronaNexus is excessively heavy for a lightweight single-machine deployment.

### 6. Classification & Recommendation
- **Classification:** **Adapt selected modules** & **Integrate as a separate service** (for benchmark testing).
- **Primary Reuse Targets:**
  1. Adapt the BM25 retrieval algorithms and citation attribution algorithms from `internal/agentic_rag/bm25_service.go` and `citations.go`.
  2. Study the table-extraction heuristics in DeepDoc to resolve ChronaNexus's lab report parsing failures.
  3. Use `ragflow_sdk` as an external evaluation benchmark against ChronaNexus's native pipeline.

---

```
================================================================================
REPOSITORY 8: OpenEMR
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** OpenEMR (`openemr/openemr`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\openemr`
- **Canonical Repository URL:** `https://github.com/openemr/openemr`
- **Checked-Out Branch:** `master` | **Commit Hash:** `deaac61ccefdb6547a30729a9f746f9ca6922692`
- **Primary Languages:** PHP 8.x, JavaScript, SQL
- **Frameworks:** Symfony components, Twig, MySQL/MariaDB.

### 2. Licensing & Legal Observations
- **Root License:** **GNU General Public License v2.0 / v3.0** (`open-source-references/openemr/LICENSE`).
- **Permissions:** Copyleft.
- **Suitability for ChronaNexus:** Direct code reuse is impossible due to language barrier (PHP vs Python/TypeScript) and GPL copyleft terms.

### 3. Architecture & Key Modules
- **FHIR REST API:** `src/FHIR/` and `src/RestControllers/FHIR/`:
  - Certified ONC HIT / FHIR R4 implementation covering Patient, Condition, Observation, MedicationRequest, AllergyIntolerance, DocumentReference.
- **Terminology & Codes:** `src/Entities/Code.php` and `sql/`:
  - Database tables for ICD-10, SNOMED-CT, RxNorm, and LOINC lookups.

### 4. Technical Assessment & Strengths
- 20+ years of clinical EHR maturity; authoritative reference for clinical compliance, encounter workflows, and billing codes.

### 5. Limitations & Caveats
- Monolithic PHP application tailored to clinical practices and billing, not a patient-first AI assistant.

### 6. Classification & Recommendation
- **Classification:** **Architecture reference only**.
- **Primary Use:** Study its FHIR resource schemas and database mappings for clinical concepts.

---

```
================================================================================
REPOSITORY 9: OpenMRS
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** OpenMRS Core (`openmrs/openmrs-core`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\openmrs`
- **Canonical Repository URL:** `https://github.com/openmrs/openmrs-core`
- **Checked-Out Branch:** `master` | **Commit Hash:** `d4348493a00571bd9e3adea68e8ede99428ddad8`
- **Primary Languages:** Java
- **Frameworks:** Spring, Hibernate, Liquibase, Maven.

### 2. Licensing & Legal Observations
- **Root License:** **Mozilla Public License 2.0 (MPL-2.0)** (`open-source-references/openmrs/LICENSE`).
- **Permissions:** Weak copyleft. File-level copyleft permits integration in larger works if modified files remain MPL-2.0.
- **Suitability for ChronaNexus:** Direct code reuse impossible due to Java runtime and architecture mismatch.

### 3. Architecture & Key Modules
- **Concept Dictionary:** `api/src/main/java/org/openmrs/Concept.java`:
  - Authoritative hierarchical medical concept dictionary model connecting questions, answers, synonyms, and data types.
- **Observations & Encounters:** `api/src/main/java/org/openmrs/Obs.java` and `Encounter.java`.

### 4. Technical Assessment & Strengths
- World-renowned clinical concept dictionary architecture used globally in healthcare deployments.

### 5. Limitations & Caveats
- Heavy enterprise Java stack. Unsuitable for direct integration into ChronaNexus.

### 6. Classification & Recommendation
- **Classification:** **Architecture reference only**.
- **Primary Use:** Study its Observation (`Obs`) and Concept modeling patterns for longitudinal lab tracking.

---

```
================================================================================
REPOSITORY 10: Medplum
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** Medplum (`medplum/medplum`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\medplum`
- **Canonical Repository URL:** `https://github.com/medplum/medplum`
- **Checked-Out Branch:** `main` | **Commit Hash:** `975647371fbd8c3041717ccfa7c8830eaa96b122`
- **Primary Languages:** TypeScript / Node.js, React
- **Frameworks:** Express, PostgreSQL, React, Vite/Turbo monorepo.

### 2. Licensing & Legal Observations
- **Root License:** **Apache License 2.0** (`open-source-references/medplum/LICENSE.txt`).
- **Permissions:** Permissive. 100% license-compatible with ChronaNexus for commercial and noncommercial use.

### 3. Architecture & Key Modules
- **Packages:** `packages/`:
  - `@medplum/fhirtypes`: Authoritative TypeScript type definitions for the entire FHIR R4 standard.
  - `@medplum/core`: FHIR client, JSON schema validators, search query builders, and formatting utilities.
  - `@medplum/react`: React UI components for rendering FHIR resources (Patient, Condition, Observation, AllergyIntolerance, DiagnosticReport).
  - `@medplum/ccda`: C-CDA to FHIR converter.

### 4. Technical Assessment & Strengths
- The premier modern TypeScript FHIR platform. Provides complete type safety and validation for all healthcare resources.
- Direct frontend synergy: ChronaNexus's React 19 frontend can directly consume Medplum's TypeScript types and FHIR normalization helpers.

### 5. Limitations & Caveats
- Full Medplum server stack is complex; running the entire Medplum server is unnecessary when ChronaNexus only needs FHIR schemas and utility functions.

### 6. Classification & Recommendation
- **Classification:** **Reuse directly** (client libraries & TypeScript definitions) & **Adapt selected modules**.
- **Primary Reuse Targets:**
  1. Adopt `@medplum/fhirtypes` and `@medplum/core` in ChronaNexus frontend/backend data contracts.
  2. Adapt FHIR conversion utilities for JSON import/export.

---

```
================================================================================
REPOSITORY 11: OHIF Viewer
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** OHIF Viewer (`OHIF/Viewers`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\ohif-viewer`
- **Canonical Repository URL:** `https://github.com/OHIF/Viewers`
- **Checked-Out Branch:** `master` | **Commit Hash:** `5a78dac37797efa74c10e63ec2028bca0b33e13b`
- **Primary Languages:** JavaScript / TypeScript, React
- **Frameworks:** CornerstoneJS, Webpack, dcmjs.

### 2. Licensing & Legal Observations
- **Root License:** **MIT License** (`open-source-references/ohif-viewer/platform/core/LICENSE`).
- **Permissions:** Permissive. Fully license-compatible.

### 3. Architecture & Key Modules
- **Medical Imaging Web Viewer:** `platform/app/` and `platform/ui/`:
  - Browser-based 2D and 3D rendering of DICOM imaging studies (CT, MRI, X-Ray, Ultrasound).
  - Measurement tracking, annotation tools, and segmentation masks.

### 4. Technical Assessment & Strengths
- Industry standard web viewer for radiology studies.

### 5. Limitations & Caveats
- ChronaNexus MVP is focused on document text/PDF RAG, medical timelines, and biomarker trends. It indexes imaging *reports* (e.g. MRI Knee report findings), but does not currently ingest raw multi-gigabyte DICOM binary slices.

### 6. Classification & Recommendation
- **Classification:** **Defer**.
- **Primary Use:** Preserve for future Phase (Phase 4+) when direct DICOM viewer integration becomes a product requirement.

---

```
================================================================================
REPOSITORY 12: Orthanc
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** Orthanc (`jodogne/OrthancMirror`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\orthanc`
- **Canonical Repository URL:** `https://github.com/jodogne/OrthancMirror` (Mercurial upstream: `https://orthanc.uclouvain.be/hg/orthanc/`)
- **Checked-Out Branch:** `master` | **Commit Hash:** `b0f14963413d3351a72988bc17d3faf934bfbe6e`
- **Primary Languages:** C++
- **Frameworks:** CMake, Boost, DCMTK, SQLite/PostgreSQL.

### 2. Licensing & Legal Observations
- **Root License:** **GNU General Public License v3.0 (GPL-3.0) with OpenSSL exception** (`open-source-references/orthanc/COPYING`).
- **Permissions:** Copyleft.

### 3. Architecture & Key Modules
- **DICOM Server & REST API:** `OrthancServer/Sources/OrthancRestApi/`:
  - High-performance C++ PACS server for receiving, storing, anonymizing, and serving DICOM imaging studies via REST.

### 4. Technical Assessment & Strengths
- Lightweight, self-contained, robust DICOM PACS server with clean REST API endpoints.

### 5. Limitations & Caveats
- C++ binary service. Not needed for ChronaNexus MVP document and lab intelligence.

### 6. Classification & Recommendation
- **Classification:** **Defer**.
- **Primary Use:** Retain as candidate imaging backend alongside OHIF Viewer if direct DICOM ingestion is approved in future phases.

---

```
================================================================================
REPOSITORY 13: GNU Health
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** GNU Health HIS (`gnuhealth/his`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\gnu-health`
- **Canonical Repository URL:** `https://codeberg.org/gnuhealth/his.git`
- **Checked-Out Branch:** `devel` | **Commit Hash:** `5ce62d3d7838b78e4a99d9c229e014082fea5060`
- **Primary Languages:** Python 3
- **Frameworks:** Tryton ERP framework, PostgreSQL.

### 2. Licensing & Legal Observations
- **Root License:** **GNU General Public License v3.0 or later (GPL-3.0+)** (`open-source-references/gnu-health/tryton/health/COPYING`).
- **Permissions:** Copyleft.

### 3. Architecture & Key Modules
- **Tryton Health Modules:** `tryton/`:
  - `health_lab`: Laboratory test definitions and sample tracking.
  - `health_socioeconomics`: Socioeconomic context and lifestyle factors.
  - `health_who_essential_medicines`: WHO Model List of Essential Medicines catalog.
  - `health_genetics`: Genetic and hereditary condition tracking.

### 4. Technical Assessment & Strengths
- Comprehensive holistic view of health, including social determinants of health (SDOH), environmental factors, and lifestyle context.

### 5. Limitations & Caveats
- Deeply tied to the Tryton ERP framework and its proprietary model syntax. Cannot be extracted into FastAPI/SQLAlchemy without a full rewrite.

### 6. Classification & Recommendation
- **Classification:** **Architecture reference only**.
- **Primary Use:** Study its socioeconomic and lifestyle health data models as references for ChronaNexus's patient profile extensions.

---

```
================================================================================
REPOSITORY 14: ArogyaSutra (IITP-CSE)
================================================================================
```
### 1. Overview & Provenance
- **Application Name:** ArogyaSutra Multimodal Framework (`IITP-CSE/ArogyaSutra`)
- **Local Destination Path:** `C:\chromaNexus\open-source-references\arogyasutra-iitp`
- **Canonical Repository URL:** `https://github.com/IITP-CSE/ArogyaSutra`
- **Checked-Out Branch:** `main` | **Commit Hash:** `4ddc2485b782ab2596091ddf22aba656295ee80b`
- **Primary Languages:** Python (PyTorch), Shell
- **Frameworks:** Qwen2.5-VL, Unsloth, Depth-Anything-V2, LLMDet, VERL.

### 2. Licensing & Legal Observations
- **Root License:** **No root LICENSE file found.** Component license at `tools/Depth-Anything-V2/LICENSE` is Apache-2.0.
- **Legal Concern:** In the absence of an explicit root open-source license, copyright remains all rights reserved by the original authors (IIT Patna). Code cannot be legally copied or distributed.

### 3. Architecture & Key Modules
- **Multimodal Research Scripts:** `gen/`, `test/`, `train/`:
  - Benchmark evaluation scripts on MedQA using fine-tuned Qwen2.5-VL-7B vision-language models.
  - Computer vision tool wrappers (depth estimation, object detection in medical images).

### 4. Technical Assessment & Strengths
- State-of-the-art academic research in multimodal medical reasoning and Indic-language medical evaluation.

### 5. Limitations & Caveats
- Has no application server, no API, no database, no patient record management, and no user interface.
- Setup requires heavy GPU clusters (NVIDIA CUDA, Unsloth, SLURM scripts).

### 6. Classification & Recommendation
- **Classification:** **Research only / Defer**.
- **Primary Use:** Keep as an academic reference for multimodal prompt engineering and benchmark evaluation techniques.

---

## 3. Summary of Repository Classifications

| # | Repository | Primary Language | License | Classification | Primary Contribution to ChronaNexus |
|---|---|---|---|---|---|
| 1 | **Health Assistant** | Python / TS | **Apache-2.0** | **Reuse directly / Adapt selected modules** | Biomarker catalogs, LOINC aliases, hybrid search tool with RRF, NLP extraction prompts. |
| 2 | **HealthWallet.me** | Dart | GPL-3.0 | **Architecture reference only** | Offline-first mobile vault, Drift SQLite schema patterns, biometric security. |
| 3 | **Fasten Health** | Go / Angular | GPL-3.0 | **Architecture reference only** | FHIR R4 Bundle normalization, condition tracking, family account models. |
| 4 | **OwnChart** | Python / Next.js | **PolyForm Noncommercial** | **Architecture reference only (Strict)** | Life-event + clinical timeline fusion concepts. Zero code reuse due to license. |
| 5 | **ArogyaSutra (DoJ)** | TypeScript | **MIT** | **Adapt selected modules** | Corrective RAG (CRAG), Self-Reflective RAG (hallucination reduction), client crypto. |
| 6 | **Paperless-ngx** | Python / Angular | GPL-3.0 | **Architecture reference only** | PDF preprocessing, deskewing, OCRmyPDF integration patterns, document archive. |
| 7 | **RAGFlow** | Go / Python | **Apache-2.0** | **Adapt selected modules** | DeepDoc table extraction algorithms, BM25 service, snippet-level citation scoring. |
| 8 | **OpenEMR** | PHP | GPL-2.0/3.0 | **Architecture reference only** | Clinical terminology mappings (SNOMED, RxNorm, LOINC), practice workflows. |
| 9 | **OpenMRS** | Java | MPL-2.0 | **Architecture reference only** | Observation (`Obs`) and Concept Dictionary data modeling. |
| 10 | **Medplum** | TypeScript | **Apache-2.0** | **Reuse directly / Adapt modules** | `@medplum/fhirtypes` and `@medplum/core` for TypeScript FHIR validation and schemas. |
| 11 | **OHIF Viewer** | React / JS | MIT | **Defer** | Future DICOM image series viewer integration (Phase 4+). |
| 12 | **Orthanc** | C++ | GPL-3.0 | **Defer** | Future DICOM server PACS backend integration (Phase 4+). |
| 13 | **GNU Health** | Python (Tryton) | GPL-3.0+ | **Architecture reference only** | Socioeconomic determinants of health (SDOH) and lifestyle data modeling. |
| 14 | **ArogyaSutra (IITP)** | Python (PyTorch) | Unlicensed / None | **Research only / Defer** | Multimodal reasoning prompts; academic reference only. |
