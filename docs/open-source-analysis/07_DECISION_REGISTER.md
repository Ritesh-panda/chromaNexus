# ChronaNexus — Architecture & Strategy Decision Register

> **Document ID:** `07_DECISION_REGISTER.md`  
> **Date:** 2026-10-17  
> **Author:** Principal Software Architect & Technical Lead  
> **Status:** Pending User Approval  

---

## 1. Overview

This Decision Register records every major architectural, strategic, and licensing choice evaluated during Phase 2. Decisions are categorized by impact, with explicit flags denoting choices that require the user's formal sign-off before Phase 3 implementation begins.

---

## 2. Decision Records

### DEC-01: Strategic Integration Approach
- **Decision Question:** Should ChronaNexus adopt Strategy A (selective module adaptation), Strategy B (separate microservices integration), or Strategy C (major subsystem replacement)?
- **Options Considered:**
  1. *Strategy A:* Retain ChronaNexus as the unified application and adapt proven modules from Health Assistant, RAGFlow, ArogyaSutra, and Medplum.
  2. *Strategy B:* Run Paperless-ngx, RAGFlow, and Medplum as separate Docker containers connected via REST APIs.
  3. *Strategy C:* Replace ChronaNexus's backend entirely with Health Assistant or Fasten Health.
- **Evidence:** Audit Document 01 demonstrated that ChronaNexus's frontend and API layer are functioning cleanly, while its failures are concentrated in parsing, embeddings, and taxonomy. Document 04 proved Strategy B requires 4 databases and > 12 GB RAM, while Strategy C would discard months of verified React progress and 144 passing tests.
- **Recommendation:** **Adopt Strategy A (Selective Module Adaptation & Clean-Room Reuse).**
- **Confidence:** **High (95%)**
- **Risks:** Requires hands-on software engineering to integrate algorithms rather than launching off-the-shelf containers.
- **Requires User Approval:** **YES (Crucial Architectural Direction)**
- **Current Status:** **PROPOSED — AWAITING USER APPROVAL**

---

### DEC-02: Dense Vector Embedding Architecture
- **Decision Question:** How should local semantic vector embeddings be generated in ChronaNexus to eliminate hash-collision defects?
- **Options Considered:**
  1. *Option 1:* Mandate that users install and run external Ollama daemon with `all-minilm`.
  2. *Option 2:* Keep the current `LocalLightweightEmbeddingProvider` CPU hash projector.
  3. *Option 3:* Bundle an in-process neural embedder (`fastembed` with `BAAI/bge-small-en-v1.5`, ONNX Runtime).
- **Evidence:** Audit Document 01 revealed that when Ollama is offline, Option 2 produces pseudo-embeddings using SHA-256 token hashing, resulting in orthogonal vectors for synonyms like "hypertension" and "blood pressure". Option 1 fails if the user does not have Ollama installed or running. Option 3 runs in-process on CPU via ONNX Runtime in < 15ms per chunk with zero external services and an Apache-2.0 license.
- **Recommendation:** **Adopt Option 3 (`fastembed` with BGE-small-en-v1.5) as the default local embedder**, while preserving Ollama as an optional external configuration.
- **Confidence:** **Very High (98%)**
- **Risks:** Adds `fastembed` (~40MB ONNX model download on first build).
- **Requires User Approval:** **YES**
- **Current Status:** **PROPOSED — AWAITING USER APPROVAL**

---

### DEC-03: Document Ingestion & Table Extraction Engine
- **Decision Question:** How should ChronaNexus extract text and tables from complex medical laboratory reports?
- **Options Considered:**
  1. *Option 1:* Continue using `pypdf` native stream extraction.
  2. *Option 2:* Deploy full RAGFlow DeepDoc engine (Go/C++ backend).
  3. *Option 3:* Integrate Python-native layout and table extraction using `pdfplumber` + PyMuPDF.
- **Evidence:** `pypdf` extracts text in stream order, interweaving multi-column lab test rows and destroying tabular relationships. RAGFlow DeepDoc is superior but requires C++ bindings and heavy infrastructure. `pdfplumber` provides native Python table cell bounding box extraction with zero container dependencies.
- **Recommendation:** **Adopt Option 3 (`pdfplumber` + PyMuPDF)** with layout heuristics inspired by RAGFlow DeepDoc.
- **Confidence:** **High (90%)**
- **Risks:** Requires tuning table border extraction parameters for non-bordered clinic reports.
- **Requires User Approval:** No (Implementation Detail)
- **Current Status:** **RECOMMENDED**

---

### DEC-04: Clinical Terminology Catalogs & LOINC Aliases
- **Decision Question:** How should ChronaNexus resolve medical synonyms (e.g., matching "blood sugar" to "fasting blood glucose") without hardcoding?
- **Options Considered:**
  1. *Option 1:* Keep the hardcoded 7-condition dictionary in `classifier.py` and `query_resolver.py`.
  2. *Option 2:* Call an external cloud medical ontology API (e.g. NIH UMLS or AWS Comprehend Medical).
  3. *Option 3:* Import Health Assistant's verified JSON seed catalogs (`biomarker_panels.json`, `allergies.json`, `clinical_event_types.json`) under Apache-2.0 into local backend data directories.
- **Evidence:** Option 1 fails for any condition outside the 7 hardcoded items. Option 2 violates the privacy-first, local-only mandate. Option 3 provides standardized LOINC panels, reference ranges, and aliases in pure JSON with zero runtime latency or external network dependency.
- **Recommendation:** **Adopt Option 3 (Import Health Assistant's seed catalogs).**
- **Confidence:** **Very High (99%)**
- **Risks:** Minimal; catalogs are static JSON files.
- **Requires User Approval:** No (Data Asset Import)
- **Current Status:** **RECOMMENDED**

---

### DEC-05: Citation Grounding & Hallucination Guardrails
- **Decision Question:** How should ChronaNexus prevent fabricated citations and ungrounded statements in AI chat?
- **Options Considered:**
  1. *Option 1:* Keep the current keyword-matching suppressor (`_answer_indicates_missing_data`).
  2. *Option 2:* Adapt ArogyaSutra's Self-Reflective RAG (Self-RAG) reflection tokens and RAGFlow's mathematical attribution scoring.
  3. *Option 3:* Rely purely on LLM system prompt instructions.
- **Evidence:** Option 1 is brittle; LLMs frequently rephrase missing-data statements using words not in the regex list. Option 3 frequently suffers from LLM instruction drift. Option 2 evaluates answer sentences against retrieved snippets, stripping unsupported claims and suppressing citations when factual support is absent.
- **Recommendation:** **Adopt Option 2 (Self-Reflective RAG + Attribution Scoring).**
- **Confidence:** **High (92%)**
- **Risks:** Slight increase in generation verification latency (~150ms).
- **Requires User Approval:** No (Algorithmic Improvement)
- **Current Status:** **RECOMMENDED**

---

### DEC-06: Handling of PolyForm Noncommercial Repository (OwnChart)
- **Decision Question:** How should ChronaNexus treat code and assets from the OwnChart repository?
- **Options Considered:**
  1. *Option 1:* Copy OwnChart's extraction and timeline code into ChronaNexus.
  2. *Option 2:* Strictly treat OwnChart as an **architecture reference only**; do not copy any source code or assets.
- **Evidence:** OwnChart is licensed under **PolyForm Noncommercial License 1.0.0**, which explicitly forbids commercial, enterprise, or institutional deployment. Copying code from OwnChart into ChronaNexus would create a severe legal encumbrance on the entire project.
- **Recommendation:** **Adopt Option 2 (Strict Clean-Room Architecture Reference).** Replicate the conceptual ideas (fusing life events with medical records) independently using original ChronaNexus code.
- **Confidence:** **100% (Strict Legal Compliance)**
- **Risks:** Zero. Eliminates copyright infringement risk.
- **Requires User Approval:** **YES (Legal Policy Confirmation)**
- **Current Status:** **PROPOSED — AWAITING USER APPROVAL**

---

### DEC-07: Scope Boundary for Medical Imaging (OHIF Viewer & Orthanc)
- **Decision Question:** Should full DICOM imaging viewers (OHIF) and DICOM servers (Orthanc) be integrated in Phase 3?
- **Options Considered:**
  1. *Option 1:* Integrate OHIF Viewer and Orthanc in Phase 3 alongside document RAG.
  2. *Option 2:* Defer OHIF Viewer and Orthanc to Phase 4; focus Phase 3 strictly on document RAG, clinical timeline, biomarker trajectories, and medical vault.
- **Evidence:** ChronaNexus MVP requirements (as defined in `capstone.pdf` and alignment document) prioritize document intelligence, lab trends, and longitudinal chat over raw DICOM PACS image manipulation. OHIF and Orthanc add over 1 GB of code and substantial deployment complexity without benefiting text document RAG.
- **Recommendation:** **Adopt Option 2 (Defer to Phase 4).**
- **Confidence:** **Very High (95%)**
- **Risks:** DICOM pixel slice viewing will not be available in Phase 3; radiological PDF reports will continue to be fully indexed.
- **Requires User Approval:** **YES (Scope Prioritization)**
- **Current Status:** **PROPOSED — AWAITING USER APPROVAL**

---

### DEC-08: Dedicated AllergyIntolerance Model vs Static JSON
- **Decision Question:** Should patient drug and environmental allergies remain as a static JSON array on the `Patient` model or migrate to a first-class relational table?
- **Options Considered:**
  1. *Option 1:* Keep `known_allergies` JSON array on `Patient`.
  2. *Option 2:* Create a dedicated `AllergyIntolerance` table with substance, reaction, severity, and diagnosed date.
- **Evidence:** Static JSON cannot be indexed effectively, cannot store reaction severity or verification status, and cannot support relational SQL queries like "what severe allergies does the patient have?". Health Assistant, Medplum, and OpenEMR all model allergies as first-class clinical entities.
- **Recommendation:** **Adopt Option 2 (Create dedicated `AllergyIntolerance` table via Alembic migration).**
- **Confidence:** **High (95%)**
- **Risks:** Requires an Alembic database migration.
- **Requires User Approval:** No (Data Model Hygiene)
- **Current Status:** **RECOMMENDED**

---

## 3. Summary of Major Decisions Requiring User Approval

| Decision ID | Summary of Decision Requiring Sign-Off | Recommended Choice |
|---|---|---|
| **DEC-01** | Integration Strategy Direction | **Strategy A:** Selective Module Adaptation & Clean-Room Reuse. |
| **DEC-02** | Local Embedding Architecture | Bundle in-process `fastembed` (BGE-small-en-v1.5) ONNX model for zero-daemon local search. |
| **DEC-06** | OwnChart Licensing Boundary | Strict clean-room architecture reference; zero code copying from PolyForm Noncommercial code. |
| **DEC-07** | Medical Imaging Scope Boundary | Defer OHIF Viewer & Orthanc DICOM PACS to Phase 4; focus Phase 3 on document RAG & lab trends. |
