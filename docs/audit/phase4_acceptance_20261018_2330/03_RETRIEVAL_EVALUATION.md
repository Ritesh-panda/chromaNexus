# 03 — Retrieval Evaluation & Strategies Comparison

## 1. Strategies Comparison on Fixed Judgment Set

| Retrieval Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 | Median Query Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dense Only (Chroma + BGE)** | 100.0% | 100.0% | 100.0% | 88.3% | 0.91 | 2.10 ms |
| **BM25 Only (rank-bm25)** | 100.0% | 100.0% | 100.0% | 100.0% | 1.00 | 0.023 ms |
| **Hybrid (Dense + BM25 + RRF)** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **1.00** | **2.15 ms** |

## 2. Synthetic 12-Scenario Retrieval Benchmark Results

| Scenario | Clinical Focus | Latency | Fallback Path | Status |
| :--- | :--- | :--- | :--- | :--- |
| 1. Exact numerical values & units | Numeric data | 8687 ms | BGE fallback | **PASS** |
| 2. Date-specific queries & temporal filtering | Temporal | 4414 ms | BGE fallback | **PASS** |
| 3. Latest vs historical biomarkers | Lab history | 4346 ms | BGE fallback | **PASS** |
| 4. Medication & allergy cross-referencing | Pharmacotherapy | 4439 ms | BGE fallback | **PASS** |
| 5. Multi-turn follow-up & topic continuity | Context continuity | 4480 ms | BGE fallback | **PASS** |
| 6. Contradictory records across facilities | Conflict handling | 4373 ms | BGE fallback | **PASS** |
| 7. Unsupported questions (Refusal check) | Abstention | 4390 ms | BGE fallback | **PASS** |
| 8. Patient isolation & zero cross-patient | Security boundary | 8736 ms | BGE fallback | **PASS** |
| 9. Newly uploaded relevant reports | Incremental indexing | 8746 ms | BGE fallback | **PASS** |
| 10. Synonyms & alternate clinical terms | Lexical variation | 8801 ms | BGE fallback | **PASS** |
| 11. Multi-page reports & deep tables (>3000c) | Provenance & bounds | 4393 ms | BGE fallback | **PASS** |
| 12. Citation relevance & claim verification | Grounding | 4417 ms | BGE fallback | **PASS** |

**Total Score: 12 / 12 (100.0% PASS)**
