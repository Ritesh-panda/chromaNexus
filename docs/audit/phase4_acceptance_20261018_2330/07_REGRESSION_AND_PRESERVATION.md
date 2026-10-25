# 07 — Regression, Preservation & Fault Injection

## 1. Database Integrity Verification
Both SQLite database files were inspected before and after testing.

| Database File | Initial Size | Final Size | Initial SHA-256 | Final SHA-256 | Integrity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| C:\chromaNexus\chronanexus.db (Authoritative) | 462,848 bytes | 462,848 bytes | e882c255ee... | e882c255ee... | **100% PRESERVED** |
| C:\chromaNexus\backend\chronanexus.db (Secondary) | 188,416 bytes | 188,416 bytes | e2ca7579a10... | e2ca7579a10... | **100% PRESERVED** |

## 2. Regression Test Results
- **Full Backend Suite:** 171 passed out of 171 collected (100.0%) in 635.02s.
- **Synthetic Benchmark Suite:** 12 passed out of 12 scenarios (100.0%).

## 3. Fault Injection Findings
- **DEF-PHASE4-01 (Fixed):** Resolved pgvector string serialization error in orchestrator.py during Stage 0.
- **DEF-PHASE4-02 (Documented Gap):** Identified early-exit defect in ChromaDBVectorStore.sync_from_db() when count > 0.
- **Dimension Mismatch (Tested):** ChromaDB correctly rejected 128-dimension input with InvalidArgumentError.
- **Offline Provider Fallback (Tested):** Offline Ollama requests successfully fell back to local cached BGEEmbeddingProvider.
