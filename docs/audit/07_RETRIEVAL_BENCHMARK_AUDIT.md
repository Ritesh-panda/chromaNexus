# ChronaNexus Forensic Audit Dossier ? 12-Scenario Retrieval Benchmark Audit

**Document ID:** `07_RETRIEVAL_BENCHMARK_AUDIT.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  
**Benchmark Script:** `tests/benchmarks/retrieval_benchmark.py`  
**Raw Results Path:** `tests/benchmarks/baseline_results.json`  

---

## 1. Quantitative Benchmark Results Summary

```
========================================================================================
                     SYNTHETIC RETRIEVAL BENCHMARK EXECUTION LOG
========================================================================================
Timestamp             : 2026-10-18T11:38:04+00:00 (Reproduced: 2026-10-18T17:18:22+05:30)
Total Scenarios       : 12
Scenarios Passed      : 9 (75.0%)
Scenarios Failed      : 3 (25.0%)
Total Execution Time  : 47.82 seconds
Pass Threshold        : Strict Clinical Grounding & Assertion Verification
========================================================================================
```

---

## 2. Comprehensive 12-Scenario Evaluation Matrix

| Scenario ID & Name | Query Text | Earliest Failure Stage | Actual Result | Root Cause & Evidence Analysis |
|---|---|---|---|---|
| **SC-01**: Exact numerical values and units | *"What was my serum potassium level and unit on September 10, 2024?"* | None | **PASSED** | Structured retriever matched potassium 4.8 mEq/L (Ref: 3.5 - 5.1). Citations verified. |
| **SC-02**: Date-specific & temporal filtering | *"What was my serum creatinine on 2023-04-15 versus 2024-09-10?"* | None | **PASSED** | Retrieved both 2023 (0.95 mg/dL) and 2024 (1.28 mg/dL) records across facilities. |
| **SC-03**: Medication dosage and frequency | *"What is my current prescribed dose and schedule for Metformin?"* | None | **PASSED** | Structured medication retriever found Metformin 500mg BID Oral Active. |
| **SC-04**: Allergy & adverse reaction retrieval | *"Do I have any documented drug allergies and what was the reaction?"* | None | **PASSED** | Retrieved Penicillin allergy (Anaphylaxis / Hives, Severe, Active). |
| **SC-05**: Multi-turn follow-up & continuity | *"What inhaler dose was prescribed for that condition?"* (after Asthma turn) | `conversation_context_resolution` | **FAILED** | `query_resolver.py:32` lacks "asthma" and "pulmonary" in `TAXONOMY`. `active_topic` returned `None`. |
| **SC-06**: Contradictory medical records | *"What was my HbA1c recorded in November 2024 across different facilities?"* | None | **PASSED** | Retrieved both Metro General (6.8%) and St. Jude (7.4%) contradictory values. |
| **SC-07**: Unsupported questions & refusal | *"When was my last colonoscopy performed?"* | None | **PASSED** | System detected zero supporting chunks and returned verified medical absence refusal. |
| **SC-08**: Cross-patient data isolation | *"What were my lab results from Quest Diagnostics?"* (Patient Alpha vs Beta) | None | **PASSED** | Retrieved 4 results for Alpha; 0 leaked records from Patient Beta. Strict isolation verified. |
| **SC-09**: Newly uploaded relevant reports | *"When was I treated for acute bronchitis and what antibiotic was prescribed?"* | `candidate_retrieval` | **FAILED** | Newly inserted chunk not retrieved in top-4 by hash-projection embedding provider. |
| **SC-10**: Clinical terminology & synonyms | *"What treatments are documented for my high blood pressure?"* | `embedding_generation` | **FAILED** | Hash embeddings cannot map "high blood pressure" to indexed "essential hypertension" records. |
| **SC-11**: Multi-page reports & tables | *"What were my complete lipid panel values including triglycerides on June 12, 2021?"* | None | **PASSED** | Multi-page PyMuPDF extraction extracted full table without 3,000-char truncation. |
| **SC-12**: Citation relevance & evidence support | *"What medications am I taking for diabetes and cholesterol?"* | None | **PASSED** | Generated response strictly cited Metformin and Atorvastatin source records. |

---

## 3. Forensic Autopsy of the 3 Benchmark Failures

### Failure 1: Scenario 05 (Multi-Turn Conversational Topic Continuity)
- **Failing Code:** `backend/app/ai/rag/query_resolver.py:32`
- **Root Cause:** The `ConversationQueryResolver` relies on a static dictionary (`TAXONOMY`) containing only `diabetes`, `cholesterol`, and `hypertension`. When turn 1 established an Asthma diagnosis and turn 2 asked *"What inhaler dose was prescribed for that condition?"*, the resolver failed to detect the active topic because pulmonary conditions were absent from `TAXONOMY`.
- **Assertion That Failed:** `assert resolved.active_topic in ["asthma", "pulmonary"]` returned `False`.

### Failure 2: Scenario 09 (Newly Uploaded Report Indexing Synchronization)
- **Failing Code:** `backend/app/ai/embeddings.py:45` & `retrieval.py`
- **Root Cause:** In the baseline environment, `LocalLightweightEmbeddingProvider` generates hash-projected vectors. When a new acute bronchitis report was dynamically ingested during the benchmark run, the cosine similarity between the query vector and document chunk vector scored below existing background documents, failing to place the new report in the top-4 retrieved candidates.

### Failure 3: Scenario 10 (Semantic Synonyms & Terminology)
- **Failing Code:** `backend/app/ai/embeddings.py:55`
- **Root Cause:** The query used the layman phrase *"high blood pressure"*, while indexed records contained *"Essential Hypertension"* and *"Lisinopril 10mg"*. Because `LocalLightweightEmbeddingProvider` hashes individual words using SHA-256, tokens with different character spellings have 0 cosine overlap. Without a real semantic transformer model, semantic synonym mapping is mathematically impossible.

---

## 4. Evaluation of ChromaDB / BGE Comparative Experiment

An isolated benchmark script (`tests/benchmarks/experiment_chroma_bge.py`) was audited:
- **Configuration:** ChromaDB vector database + `BAAI/bge-small-en-v1.5` 384-dimensional dense transformer embeddings.
- **Results:** **10 / 12 Scenarios Passed (83.3%)**.
  - SC-09 (Newly uploaded reports): **PASSED** (BGE semantic scoring brought the bronchitis report to rank 1).
  - SC-10 (Semantic synonyms): **PASSED** (BGE dense vector mapped "high blood pressure" to "hypertension").
  - SC-05 (Multi-turn follow-up): **STILL FAILED** (Query resolver failed before retrieval stage).
- **Critical Architectural Fact:** ChromaDB and BGE are **NOT integrated into the production FastAPI application**. They exist solely in `experiment_chroma_bge.py` operating on an ephemeral database (`exp_synthetic.db`). Wiring them into `backend/app/ai/rag/` is the primary objective of Phase 4.
