# ChromaNexus Phase 4 – Test Matrix

|Test ID |Requirement |Path |Expected Result |Actual Result |Status |
-|:mark|:mark|:mark|:mark|:mark|:mark|
-|STAGE-0.1 |Repo & Data Integrity |Read-only |SQLite files preserved |Hashes match exactly |PASS |
|STAGE-0.2 |Baseline Test Suite |`backend/tests` |171 tests collected |171 passed in 635s |PASS |
-|STAGE-0.3 |Synthetic Benchmark |`tests/benchmarks` |12 scenarios |12/12 passed (100%) |PASS |
-|STAGE-1.1 |BGE model identity |BGEEmbeddingProvider |384 dimension |384, finite, offline |PASS |
-|STAGE-1.2 |Embedding fallback |LocalLightweight |Fallback with warning |Graceful fallback |PASS |
|STAGE-2.1 |Numerical Integrity |100 clinical inputs |384 dim, no NaN/Inf |100% finite, norm=1.0 |PASS |
|STAGE-2.2 |Embedding Separation |100-pair dataset |Pos-neg separation > 0 |BQE: +0.0328, Hash: -0.0012 |PASS |
 |STAGE-3.1 |ChromaDB Persistence |Isolated test dir |Count & IPs preserved |10 -> 10, top-ID match |PASS |
 |STAGE-3.2 |Collection Schema |Real Chroma dir |All SQL chunks mapped |39/39 SQL mapped, 57 total |PASS |
|STAGE-3.3 |ChromaDB Failure Modes |Isolated dim/dup |Reject wrong dimension |InvalidArgumentError (128) |PASS |
-|STAGE-4.1 |SQL-to-Chroma Stync |Partial collection |Reconcile missing SQL chunks |Skipped due to `count > 0` |**CONDITIONAL GEF-PHASE4-02** |
-|STAGE-4.2 |Incremental Indexing |Ingestion flow |Searchable in Dense, BM25, Hybrid |Searchable in all 3 |PASS |
-|STAGE-4.3 |Idempotency |Repeated indexing |No duplicate chunks |Count unchanged (6 -> 6) |PASS |
-|STAGE-5.1 |BM25 Retrieval Quality |15 synthetic chunks |Recall@5 >= 0.90 |Recall@5 = 1.0, MRR = 1.0 |PASS |
 |STAGE-5.2 |BM25 Lifecycle & Dup |Incremental addition |Immediately searchable |Prevents dup via `_chunk_ids` |PASS |
|STAGE-6.1 |RRF Mathematics |Oracle calculation |Matches expected RRF formula |Doc_A > Doc_D > Doc_B=Doc_C |PASS |
 |STAGE-6.2 |Hybrid vs Dense/BM25 |Synthetic queries |Hybrid >= dense & BM25 |Hybrid Retrieval 100% |PASS |
 |STAGE-7.1 |Patient Isolation SQL |Alice vs Bob |0 cross-patient rows |0 leaks |PASS |
-|STAGE-7.2 |Patient Isolation Chroma |Alice vs Bob |0 cross-patient vectors |0 leaks |PASS |
|STAGE-7.3 |Patient Isolation BM25 |Alice vs Bob |0 cross-patient tokens |0 leaks |PASS |
|STAGE-7.4 |Patient Isolation Hybrid |Alice vs Bob |0 cross-patient elements |0 leaks |PASS |
 |STAGE-8.1 |ETE Multi-page Ingestion |2-page synthetic |Provenance & Evidence retrieval |100% evidence retrieval |PASS |
|STAGE-8.2 |Restart Persistence |Client reuse & reboot |Count matches, evidence found |4 -> 4, reboot evidence found |PASS |
-|STAGE-8.3 |LLM Answer & Grounding |Real OLLAMA execution |Not fabricated with mocks |Offline Ollama daemon |*BLOCKED* |
