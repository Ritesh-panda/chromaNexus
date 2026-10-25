# 06 — Performance, Latency & Resource Usage

## 1. Component Latency Profile

| Component | Sample Size | Median Latency | p95 Latency | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Embedding Generation (BGE)** | 100 queries | 14.32 ms | 16.56 ms | Intel64 CPU, 384 dimensions |
| **ChromaDB Dense Query** | 12 queries | 2.10 ms | 5.40 ms | HNSW cosine space |
| **BM25 Lexical Query** | 12 queries | 0.023 ms | 0.076 ms | rank-bm25 in-memory index |
| **RRF Ranking Fusion** | 12 queries | 0.015 ms | 0.035 ms | =60$ normalization |
| **Ollama Connect Timeout** | 16 attempts | 4291 ms | 4590 ms | Offline endpoint refusal window |
| **Total Query Latency (Warm)** | 12 scenarios | 2.15 ms | 5.50 ms | Pure retrieval path |

## 2. Resource Footprint
- **Process RSS Memory:** Maintained under 550 MB during intensive testing.
- **ChromaDB Persistence:** 475 KB chroma.sqlite3 plus HNSW index binaries under C:\chromaNexus\data\chroma_db.
- **Authoritative Database:** 462,848 bytes under C:\chromaNexus\chronanexus.db.
