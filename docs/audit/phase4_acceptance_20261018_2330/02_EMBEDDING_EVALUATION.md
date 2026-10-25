# 02 — Embedding Model Evaluation & Numerical Integrity

## 1. Model Identity and Configuration
- **Model Name:** BAAI/bge-small-en-v1.5
- **Output Dimension:** 384
- **Execution Device:** CPU (Intel64 Family 6 Model 186)
- **Local Model Path:** C:\Users\Ritesh Panda\.cache\huggingface\hub\models--BAAI--bge-small-en-v1.5
- **Offline Loading:** Verified under HF_HUB_OFFLINE=1 (zero network access required).
- **Model Cold Load Latency:** 107.4 ms.

## 2. Numerical Integrity (100 Representative Clinical Inputs)
- **384-Dimension Verification:** 100 / 100 (100.0% PASS).
- **Vector Norms:** L2 norms = 1.0000 (unit normalized within 1e-3).
- **Finiteness:** 0 NaN or Infinite components detected.
- **Batch vs Single Determinism:** Maximum component difference = 1.19e-07.
- **Empty / Whitespace Safety:** Handled safely without crash.
- **Embedding Latency:** Median = 14.32 ms, p95 = 16.56 ms.

## 3. Controlled Semantic Evaluation (100 Clinical Pairs)

| Embedding Strategy | Mean Positive Similarity | Mean Hard Negative Similarity | Similarity Separation |
| :--- | :--- | :--- | :--- |
| **BAAI/bge-small-en-v1.5** | **0.7813** | **0.7485** | **+0.0328** |
| **SHA-256 Hash Fallback** | 0.1236 | 0.1248 | -0.0012 |

## 4. Hard Negative Analysis & Thresholds
Clinical hard negatives (e.g. 'Serum Potassium 4.8 mEq/L on Sept 15' vs 'Serum Potassium 3.5 mEq/L on Aug 10') share >90% vocabulary. Dense cosine similarity alone is ~0.75, showing why BM25 exact lexical matching and RRF fusion are mandatory for numerical and date accuracy.
