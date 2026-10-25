# ChronaNexus — Phase 1: Retrieval-Stage Diagnostic Report & Baseline Evaluation

## 1. Executive Summary & Objective

In Phase 1 of the approved 10-Phase Roadmap, our primary mission was to **empirically measure and diagnose the current retrieval performance of ChronaNexus** before performing any schema migrations, dependency installations, or frontend redesigns.

To establish an uncompromised, objective baseline:
1. We verified the local Windows 11 AMD64 host environment, active services, and dependency tree.
2. We audited the exact execution paths across all 11 stages of the ChronaNexus retrieval and reasoning pipeline.
3. We constructed a reproducible, zero-leakage synthetic evaluation benchmark ([`tests/benchmarks/retrieval_benchmark.py`](file:///C:/chromaNexus/tests/benchmarks/retrieval_benchmark.py)) implementing the 12 clinical scenario categories specified in Phase 2.
4. We executed the benchmark against the live ChronaNexus Python codebase in an isolated synthetic database (zero interaction with `chronanexus.db`), recording empirical pass/fail statuses, stage-by-stage failure points, latencies, and retrieved context.

### Baseline Benchmark Headline Metrics
- **Total Scenarios Evaluated**: 12
- **Scenarios Passed**: 7 (58.3%)
- **Scenarios Failed**: 5 (41.7%)
- **Average Retrieval Query Latency**: **6,070 ms** (severely degraded by repeated Ollama connection timeouts before falling back)
- **Baseline JSON Artifact**: [`tests/benchmarks/baseline_results.json`](file:///C:/chromaNexus/tests/benchmarks/baseline_results.json)

---

## 2. Environment & Service Verification

Before benchmarking, we probed the actual runtime environment:
- **Operating System**: Windows 11 Home / Pro (AMD64), 16 GB Physical RAM, CPU-only inference.
- **Python Runtime**: Python 3.13.7 (MSC v.1944 64-bit AMD64).
- **Installed Packages**: `torch 2.14.0`, `sentence-transformers 6.1.0`, `transformers 5.17.0`, `PyMuPDF 1.27.2.3`, `fastapi 0.135.3`, `pydantic 2.13.3`, `SQLAlchemy 2.0.54`, `pytest 9.1.1`, `pgvector 0.5.1`, `psycopg 3.3.6`, `onnxruntime 1.30.0`, `RapidFuzz 3.14.6`.
- **PostgreSQL Service**: `postgresql-x64-17` service is present and `Running` in Windows Service Manager.
- **Ollama Service**: **NOT installed in PATH** and **HTTP server unreachable** (`[WinError 10061]` connection refused on `http://localhost:11434`).
- **Database in Use**: ChronaNexus backend currently operates on SQLite (`sqlite:///./chronanexus.db`). No `.env` overrides exist.

---

## 3. Stage-by-Stage Retrieval Diagnostic Analysis

We traced the 12 clinical retrieval scenarios through the 11 sequential stages of the pipeline:

```
[Document Upload] ➔ [Extraction / OCR] ➔ [Clinical Extraction & Persistence] ➔ [Chunking & Metadata]
       ➔ [Embedding Generation] ➔ [Candidate Retrieval] ➔ [Structured / Keyword Retrieval]
       ➔ [Ranking & Fusion] ➔ [Conversation Context Resolution] ➔ [Answer Generation] ➔ [Citation Verification]
```

### Stage 1: Document Upload & Ingestion
- **Observed Behavior**: Files are ingested via FastAPI `upload` endpoints into `uploads/`. Metadata records are inserted into `MedicalReport`.
- **Status**: **Functional**. Checksum deduplication is currently missing (addressed in Phase 3).

### Stage 2: Text Extraction & OCR
- **Observed Behavior**: PyMuPDF extracts plain text streams. Scanned PDFs without text fallback to OCR.
- **Status**: **Functional** for single-column text; fails to preserve table geometry across multi-column laboratory panels.

### Stage 3: Clinical Extraction & Persistence
- **Observed Behavior**: `LLMClinicalExtractor` ([`backend/app/ai/clinical_extractor/llm_extractor.py:57`](file:///C:/chromaNexus/backend/app/ai/clinical_extractor/llm_extractor.py#L57)) constructs a prompt with `text[:3000]`.
- **Defect Identified**: Any lab values, medication orders, or diagnoses appearing after character offset 3,000 are **silently dropped from extraction**. In addition, patient allergies (`Patient.known_allergies`) are stored as unstructured text in `patient.known_allergies` and are **never indexed into clinical entity tables**, directly causing **Scenario 4 (`Medication and allergy cross-referencing`) to fail**.

### Stage 4: Chunking and Metadata
- **Observed Behavior**: Text chunker splits text by token/character counts (450 chars).
- **Status**: **Functional**, but lacks layout awareness, splitting lab result rows across chunk boundaries.

### Stage 5: Embedding Generation
- **Observed Behavior**: `OllamaEmbeddingProvider` attempts to connect to `http://localhost:11434/api/embed`. Because Ollama is offline, each call blocks for HTTP connection timeout (~2-4 seconds) and prints:
  ```
  Ollama embedding request failed for model 'all-minilm': [WinError 10061] No connection could be made because the target machine actively refused it. Falling back to LocalLightweightEmbeddingProvider.
  ```
- **Defect Identified**: `LocalLightweightEmbeddingProvider` hashes character tokens using SHA-256 modulo primes ([`backend/app/ai/embeddings.py:58-60`](file:///C:/chromaNexus/backend/app/ai/embeddings.py#L58-L60)). Cosine similarity between "elevated arterial pressure" and "hypertension" is exactly **0.0000**.
- **Impact**: **Scenario 10 (`Synonyms and alternate clinical terminology`) fails completely** at the vector level.

### Stage 6: Candidate Retrieval (Vector Store)
- **Observed Behavior**: Under SQLite, `PostgresVectorStore.similarity_search` ([`backend/app/ai/retrieval.py:281-317`](file:///C:/chromaNexus/backend/app/ai/retrieval.py#L281-L317)) executes a full table scan, loading all chunks into Python memory and running cosine similarity in a Python `for` loop.
- **Impact**: In **Scenario 9 (`Newly uploaded relevant reports`)**, when a user queries for a newly added report with distinct wording, the hash-based vector scan produces near-zero scores and fails to retrieve the chunk.

### Stage 7: Structured & Keyword Retrieval
- **Observed Behavior**: `StructuredRetriever` queries `LabResult`, `Medication`, and `Disease` tables.
- **Defect Identified**: It uses strict substring filtering: `if not any(k.lower() in t_name for k in query_keywords): continue` ([`backend/app/ai/rag/structured_retriever.py:50`](file:///C:/chromaNexus/backend/app/ai/rag/structured_retriever.py#L50)).
- **Impact**: Queries using clinical synonyms ("renal impairment" for "Serum Creatinine") return 0 structured matches.

### Stage 8: Ranking and Fusion
- **Observed Behavior**: `HybridRetriever.retrieve()` collects structured clinical results (assigned static scores 0.95–0.96) and vector search results (assigned raw dot products), sorting them by score.
- **Defect Identified**: Lack of calibrated Reciprocal Rank Fusion (RRF). In **Scenario 1 (`Exact numerical values and unit handling`)**, generic medication and disease records with static 0.96 scores outranked the specific lab result containing `Potassium 4.8 mEq/L`, pushing the target evidence out of the top 4 elements.

### Stage 9: Conversation Context Resolution
- **Observed Behavior**: `ConversationQueryResolver` analyzes conversation history using a hardcoded `TAXONOMY` dictionary ([`backend/app/ai/rag/query_resolver.py:32-120`](file:///C:/chromaNexus/backend/app/ai/rag/query_resolver.py#L32-L120)).
- **Defect Identified**: When evaluating **Scenario 5 (`Multi-turn follow-up and topic continuity`)**:
  - Turn 1: "What pulmonary conditions have been diagnosed?" (Answer: Moderate Persistent Asthma).
  - Turn 2: "What inhaler dose was prescribed for that condition?"
  - Result: `ConversationQueryResolver` matched "inhaler" to the generic `medications` topic, overwrote the query with `Lisinopril Metformin Atorvastatin`, completely lost the Asthma context, and retrieved hypertension medications! **Scenario 5 failed**.

### Stage 10: Answer Generation
- **Observed Behavior**: The system prompt passes context to the LLM. In unit tests, `MockDeterministicLLMProvider` hardcodes expected responses for specific string triggers ("highest", "hba1c", "knee"), which concealed retrieval defects in earlier test runs.
- **Status**: In live operation, if retrieval delivers corrupted or empty context, the LLM hallucinates or generates ungrounded answers.

### Stage 11: Citation Verification
- **Observed Behavior**: `RAGPipeline` directly attaches all retrieved context items as citations unless the answer matches an explicit missing-data pattern ([`backend/app/ai/rag/pipeline.py:144-148`](file:///C:/chromaNexus/backend/app/ai/rag/pipeline.py#L144-L148)).
- **Impact**: In **Scenario 12**, querying about liver enzymes (ALT/AST) attached citations from **five separate reports** (including Fasten Glucose, HbA1c, and an Endocrine Panel), demonstrating severe citation over-attachment and lack of token-level support verification.

---

## 4. Benchmark Scenario Results Matrix

| Scenario ID | Category & Name | Result | Earliest Failure Stage | Root Cause / Diagnostic Observation |
|:---|:---|:---:|:---:|:---|
| **SC-01** | Exact Numerical Values & Units | **FAIL** | `ranking_and_fusion` | Structured retriever found Potassium 4.8 mEq/L, but static relevance weighting allowed unrelated diagnoses to outrank it. |
| **SC-02** | Date-Specific Temporal Queries | **PASS** | `none` | Successfully retrieved both 2023 (0.95 mg/dL) and 2024 (1.28 mg/dL) creatinine readings. |
| **SC-03** | Latest vs. Historical Biomarkers | **PASS** | `none` | Top-ranked glucose element was the latest 2025 reading (108 mg/dL) over 2023 (142 mg/dL). |
| **SC-04** | Medication & Allergy Cross-Ref | **FAIL** | `clinical_extraction_persistence` | Query "Can I take Amoxicillin?" retrieved zero allergy records; Penicillin allergy is unindexed in clinical entity tables. |
| **SC-05** | Multi-Turn Follow-Up & Topic Continuity | **FAIL** | `conversation_context_resolution` | QueryResolver hardcoded taxonomy mapped "inhaler" to generic medications (Lisinopril/Metformin), dropping Asthma context. |
| **SC-06** | Contradictory Records Across Labs | **PASS** | `none` | Correctly retrieved both Metro Health (6.8%) and St. Jude (7.4%) HbA1c readings from different facilities. |
| **SC-07** | Unsupported Questions (Hallucination Check) | **PASS** | `none` | Query for nonexistent colonoscopy procedure correctly returned 0 citations and refused to invent findings. |
| **SC-08** | Patient Isolation (Zero Leakage) | **PASS** | `none` | Query under Patient Alpha for Knee MRI (which belongs to Patient Beta) retrieved 0 leaked chunks. |
| **SC-09** | Newly Uploaded Relevant Reports | **FAIL** | `candidate_retrieval` | Dynamically ingested bronchitis report was missed by vector retrieval due to hash-embedding mismatch. |
| **SC-10** | Synonyms & Alternate Terminology | **FAIL** | `embedding_generation` | SHA-256 hash embeddings produced 0.00 cosine similarity between "elevated arterial pressure" and "hypertension". |
| **SC-11** | Multi-Page Reports (>3,000 Chars) | **PASS\*** | `none` | Passed in synthetic test because chunks were indexed directly; in live ingestion, `llm_extractor` truncates text to 3,000 chars. |
| **SC-12** | Citation Relevance & Claim Support | **PASS\*** | `citation_verification` | Passed assertion because correct report was included, but **attached 4 unrelated reports as citations**, confirming over-citation defect. |

---

## 5. Ranked List of Confirmed Retrieval Root Causes

Based on empirical benchmark failures, here is the prioritized ranking of defects:

### Rank 1: Pseudo-Semantic Hash Embeddings (CRITICAL)
- **Source**: [`backend/app/ai/embeddings.py:27-60`](file:///C:/chromaNexus/backend/app/ai/embeddings.py#L27-L60)
- **Defect**: SHA-256 token hashing modulo primes creates pseudo-random vectors with zero semantic geometry. Causes 100% failure on clinical synonyms, paraphrasing, and cross-terminology retrieval when Ollama is offline.
- **Evidence**: Empirical cosine similarity between "elevated arterial pressure" and "hypertension" is `0.0`.

### Rank 2: Rigid Hardcoded Taxonomy in QueryResolver (CRITICAL)
- **Source**: [`backend/app/ai/rag/query_resolver.py:32-120`](file:///C:/chromaNexus/backend/app/ai/rag/query_resolver.py#L32-L120)
- **Defect**: Uses a static dictionary of 7 conditions. Overwrites follow-up queries with arbitrary hardcoded drug names (e.g. injects Lisinopril/Metformin into an Asthma inhaler question).
- **Evidence**: Scenario 5 failure: mapped inhaler question to `medications` topic, dropping Asthma context.

### Rank 3: Absence of True Reciprocal Rank Fusion (HIGH)
- **Source**: [`backend/app/ai/rag/hybrid_retriever.py:120-165`](file:///C:/chromaNexus/backend/app/ai/rag/hybrid_retriever.py#L120-L165)
- **Defect**: Merges structured results (static 0.96) and vector scores without reciprocal rank scoring ($1 / (k + rank)$), allowing irrelevant diagnoses to displace exact lab evidence.
- **Evidence**: Scenario 1 failure: Potassium 4.8 mEq/L was retrieved from DB but displaced from top 4 results.

### Rank 4: Disconnected Patient Allergy Knowledge (HIGH)
- **Source**: [`backend/app/models/patient.py:45`](file:///C:/chromaNexus/backend/app/models/patient.py#L45) & [`backend/app/ai/rag/structured_retriever.py:80`](file:///C:/chromaNexus/backend/app/ai/rag/structured_retriever.py#L80)
- **Defect**: Allergies are stored as an unstructured JSON array on `Patient` and are never queried during medication safety or antibiotic inquiries.
- **Evidence**: Scenario 4 failure: "Can I take Amoxicillin?" failed to surface the patient's severe Penicillin allergy.

### Rank 5: Fixed 3,000-Character Extraction Truncation (MEDIUM)
- **Source**: [`backend/app/ai/clinical_extractor/llm_extractor.py:57`](file:///C:/chromaNexus/backend/app/ai/clinical_extractor/llm_extractor.py#L57)
- **Defect**: Hardcoded `text[:3000]` cuts off multi-page documents, discarding pages 2 through 4 of standard laboratory and hospital discharge reports.

### Rank 6: Latency Degradation via Unindexed SQLite Python Scan (MEDIUM)
- **Source**: [`backend/app/ai/retrieval.py:281-317`](file:///C:/chromaNexus/backend/app/ai/retrieval.py#L281-L317)
- **Defect**: SQLite vector fallback deserializes every chunk in the database and computes dot products in a Python loop.

---

## 6. Proposed Minimal Fixes for Each Confirmed Failure

| Defect | Root Cause File | Proposed Minimal Fix | Roadmap Phase |
|:---|:---|:---|:---:|
| **Semantic Embedding Collapse** | `embeddings.py` | Integrate local ONNX/PyTorch `bge-small-en-v1.5` (already available via `sentence-transformers 6.1.0` in the local Python environment) for true offline semantic embeddings without relying on Ollama. | **Phase 4** |
| **Taxonomy Keyword Overwriting** | `query_resolver.py` | Replace static drug-name expansion with clinical entity coreference extraction (preserving the active antecedent from prior turns). | **Phase 5** |
| **Score Inversion in Fusion** | `hybrid_retriever.py` | Implement standard Reciprocal Rank Fusion (RRF, $k=60$) adapted from Health Assistant, scoring candidates by reciprocal rank rather than raw confidence. | **Phase 4** |
| **Allergy Disconnection** | `structured_retriever.py` | Add `retrieve_allergies()` to `StructuredRetriever` and cross-reference antibiotic classes (e.g. Penicillin class includes Amoxicillin, Ampicillin). | **Phase 2 & 5** |
| **3,000-Char Truncation** | `llm_extractor.py` | Implement sliding window chunking with map-reduce extraction across all document pages. | **Phase 3** |
| **SQLite Vector Table Scan** | `retrieval.py` | Transition local vector storage to **ChromaDB persistent client** (or SQLite-VSS extension), providing indexed HNSW nearest-neighbor search. | **Phase 4** |

---

## 7. Architectural Decision: Local Vector Store Engine (ChromaDB vs. PostgreSQL + pgvector)

A critical architectural question is whether to use **ChromaDB** or **PostgreSQL + pgvector** as the local vector engine for ChronaNexus.

### Comparative Evaluation

| Evaluation Criterion | Option A: ChromaDB (Embedded Local Persistent Client) | Option B: PostgreSQL + pgvector | Evidence & Assessment |
|:---|:---|:---|:---|
| **Compatibility with Current Code** | **High**: Can be dropped in behind `VectorStore` interface ([`retrieval.py:11`](file:///C:/chromaNexus/backend/app/ai/retrieval.py#L11)) with zero frontend changes. | **Moderate**: `PostgresVectorStore` already exists in code, but requires running PostgreSQL as an active server. | Option A fits cleanly into existing adapter interface. |
| **Local Deployment Overhead** | **Zero**: Pure Python embedded database; runs inside the FastAPI process. No background service needed. | **Medium-High**: Requires PostgreSQL Windows service running, pgvector extension installed, and database user setup. | On client laptops, running an external DB service introduces failure modes. |
| **Hardware & Memory Footprint** | **Minimal (~50–100 MB RAM)**: Loads only active patient collection index into memory on query. | **Moderate (~250–500 MB RAM)** for PostgreSQL service background workers. | Option A is optimal for 16 GB laptop with CPU-only inference. |
| **Patient Data Isolation** | **Native**: Separate Chroma collection per patient (`patient_{patient_id}`) ensures absolute isolation at the storage level. | **Query Filter**: Requires SQL `WHERE patient_id = :pat_id` on every query. Vulnerable to filter omission bugs. | Option A provides physical multi-tenant isolation out of the box. |
| **Filtering & Metadata** | **Native**: Supports dict-based metadata filtering (`where={"report_date": ...}`). | **Native**: SQL relational joins and WHERE clauses. | Tie. |
| **Migration & Re-indexing Cost** | **Low**: Creating collections from existing SQLite chunks is a single fast Python script. | **Moderate**: Requires running Alembic pgvector migrations and database connection strings. | Option A requires zero server configuration. |

### Architectural Recommendation
**We recommend Option A (ChromaDB Local Persistent Client) for local single-process deployment**, with **PostgreSQL + pgvector retained as an optional enterprise deployment backend**.

*Approval Flag*: This decision is registered as **DEC-02** in `docs/open-source-analysis/07_DECISION_REGISTER.md` and requires explicit user confirmation before Phase 4.

---

## 8. Summary of Phase 1 Deliverables & Files Created

1. **Synthetic Retrieval Benchmark**: [`tests/benchmarks/retrieval_benchmark.py`](file:///C:/chromaNexus/tests/benchmarks/retrieval_benchmark.py)
   - 12 comprehensive clinical scenarios implemented with pure synthetic data.
   - Independent database isolation (creates and drops `synthetic_benchmark.db`).
2. **Baseline Results Output**: [`tests/benchmarks/baseline_results.json`](file:///C:/chromaNexus/tests/benchmarks/baseline_results.json)
   - Machine-readable JSON recording pass/fail, latencies, failure stages, and evidence snippets.
3. **Retrieval-Stage Diagnostic Report**: This document ([`docs/open-source-analysis/PHASE_1_RETRIEVAL_DIAGNOSTIC.md`](file:///C:/chromaNexus/docs/open-source-analysis/PHASE_1_RETRIEVAL_DIAGNOSTIC.md)).
4. **Development Memory Update**: Appended Phase 1 milestone record to [`docs/DEVELOPMENT_MEMORY.md`](file:///C:/chromaNexus/docs/DEVELOPMENT_MEMORY.md).

---

## 9. Stopping Condition & Request for Approval

In accordance with Section 7 of the user prompt:
- **Phase 1 is complete.**
- **No production data or existing databases were altered.**
- **No external code was copied.**
- **We are paused and awaiting explicit user review and approval before proceeding to Phase 2 (Database Schema & Clinical Data Provenance).**
