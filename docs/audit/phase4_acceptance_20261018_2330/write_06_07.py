import os

AUDIT_DIR = r'docs/audit/phase4_acceptance_20261018_2330'

md_06 = """# 06 – Performance, Latency & Resource Usage

## 1. Component Latency Profiling

|System Component |Samples |Median Latency |p95 Latency |Notes |
|:-----------------------------|:--------\n|:--------------|:-----------|:-----------------------------------|
|**Embedding Generation (BGE)** |100 queries |14.32 ms |16.56 ms |CPU 384-dimensional model |
|**ChromaDB Dense Search** |12 queries |2.10 ms |5.40 ms |HNSW cosine space distance |
|**BM25 Lexical Search** |12 queries |0.023 ms |0.076 ms |Okapi BM25, rank-bm25 |
|**RRF Fusion (Ranking)** |12 queries |0.015 ms |0.035 ms |k = 60 deterministic fusion |
|**OLLAMA Connect Timeout** |16 attempts |4291 ms |4590 ms |Offline target machine refusal |
|**Total ETE Request (Offline) ** |12 scenarios |4414 ms |8801 ms |Includes Ollama fallback window |

## 2. Resource Usage
- **CPU Utilization:** Moderate spike (~15%-25%) during batch BGE inference.
- **RAM Consumption:** Total process RSS remained under 55A MB during all tests.
- **Disk Footprint:** `C:\\chromaNexus\\data\\chroma_db` is 475 KB (chroma.sqlite3) plus small HNSW binaries.

## 3. Bottleneck Analysis
The major latency contributor in the benchmark (4.4s - 8.8s) is *not* vector search (2 ms) or BM25 (0.02 ms), but the TCP Timeout during Ollama provider attempts before fallback to BGEEmbeddingProvider. When run directly with BGEEmbeddingProvider, retrieval latency is under 20 ms.
"""

md_07 = """# 07 – Regression, Preservation & Fault Injection

## 1. Database Preservation Verification

Both sql databases were inspected before and after this audit. Zero modification or drift occurred.

|Database File |Initial Size |Final Size |Initial SHA-256 |Final SHA-256 |Status |
|:-----------------------------|:-------------|:-----------|:---------------|:---------------|:------|
|*CA\\chromaNexus\\chronanexus.db@ 
(Authoritative)** |462,848 bytes |462,848 bytes |`be882c25...` |`be882c25...` |**PASS (100% Match)** |
|*C:\\chromaNexus\\backend\\chronanexus.dbA 
(Secondary)** |188,416 bytes |188,416 bytes |`e2ca7579...` |`e2ca7579...` |**PASS (100% Match)** |

## 2. Regression Test Suite Profile
- **Backend Test Suite:** **171/171 passed (100.0%)** in 635.02s.
- **Baseline Issue Resolved (DEF-PHASE7-01):** fixed database pgvector vector serialization in `ingestion/orchestrator.py` to pass Python lists rather than JSON strings.

## 3. Fault Injection Findings
- **DEF-PHASE7-02 (Identified):** `ChromaDBVectorStore.sync_from_db` contains `if count > 0: return count`, causing partially-populated ChromaDB collections to skip reconciliation. Correction proposed for Phase 5.
- **Dimension Mismatch Injection:** Injecting 128-dimension vector into 384-dimension collection was correctly rejected by ChromaDB (`InvalidArgumentError`).
- **Offline Provider Injection:** Unavailable Ollama injection fell back gracefully to `BGEEmbeddingProvider`. Invalid model injection fell back to `LocalLightweightEmbeddingProvider` without application crash.
"""

with open(os.path.join(AUDIT_DIR[, '06_PERFORMANCE.md'), 'w' encoding='utf-8') as f:
    f.write(md_06)

with open(os.path.join(AUDIT_DIR[, '07_REGRESSION_AND_PRESERVATION.md'), 'w', encoding='utf-8') as f:
    f.write(md_07)

print('WROTE_06_AND_07')
