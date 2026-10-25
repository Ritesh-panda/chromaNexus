# ChronaNexus Forensic Audit Dossier ? Next-Phase Readiness Decision

**Document ID:** `15_NEXT_PHASE_READINESS.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  
**Recommended Next Phase:** `PHASE 4 ? HYBRID RETRIEVAL (BM25, CHROMADB, BGE, AND RECIPROCAL RANK FUSION)`

---

## 1. Readiness Gate Evaluation

Before proceeding to Phase 4, the audit establishes **four mandatory prerequisites** that must be resolved:

```
[PREREQUISITE 1] SAFE PERSISTENT DATABASE MIGRATION
Action: Apply Alembic migrations 003 and 004 to persistent chronanexus.db.
Status: PENDING USER APPROVAL (Script tested in test_migration_003_disposable.py).

[PREREQUISITE 2] RESOLVE CONCURRENT UPLOAD RACE CONDITION
Action: Add UniqueConstraint('patient_id', 'checksum') to MedicalReport model.
Status: READY FOR IMPLEMENTATION.

[PREREQUISITE 3] EXPAND QUERY RESOLVER TAXONOMY
Action: Add respiratory/pulmonary and general entity terms to query_resolver.py.
Status: RESOLVES BENCHMARK SCENARIO 05.

[PREREQUISITE 4] REPLACE SILENT FRONTEND MOCK FALLBACKS
Action: Replace silent catches in src/services/*.ts with explicit error toasts.
Status: REQUIRED FOR TRUE USER-VISIBLE VERIFICATION.
```

---

## 2. Phase 4 Detailed Specification

- **Objective:** Upgrade the retrieval engine from SQLite full-table cosine scan to production-grade hybrid retrieval combining BM25 keyword matching, ChromaDB dense vector indexing with `BAAI/bge-small-en-v1.5`, and Reciprocal Rank Fusion (RRF).
- **Scope:**
  1. Integrate ChromaDB persistent vector store in `backend/app/ai/retrieval.py`.
  2. Implement `BGEEmbeddingProvider` using `fastembed` or `sentence-transformers` (offline, CPU-optimized).
  3. Implement `BM25KeywordRetriever` in `backend/app/ai/rag/bm25_retriever.py` using `rank_bm25`.
  4. Implement Reciprocal Rank Fusion (`RRFusion`) in `backend/app/ai/rag/fusion.py` using standard reciprocal rank constant $k=60$.
  5. Expand `query_resolver.py` to fix SC-05.
- **Out of Scope for Phase 4:**
  - Sentence-level natural language inference citation checking (Phase 6).
  - FHIR R4 schema export (Phase 9).
  - Production containerization (Phase 10).
- **Measurable Acceptance Criteria:**
  1. Synthetic retrieval benchmark pass rate improves from **9/12 (75.0%) to ? 11/12 (91.7%)**.
  2. Scenario 05 (Follow-up query) **PASSES**.
  3. Scenario 09 (Newly uploaded reports) **PASSES**.
  4. Scenario 10 (Clinical semantic synonyms) **PASSES**.
  5. 161 existing backend tests continue to pass without regression.
