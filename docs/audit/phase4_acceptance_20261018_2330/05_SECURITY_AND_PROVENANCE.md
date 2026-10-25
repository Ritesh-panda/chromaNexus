# 05 — Security, Patient Isolation & Citation Provenance

## 1. Patient Isolation Security Gate
Isolation was tested with synthetic conflicting patient records (pat_alice vs pat_bob).

| System Layer | Request Context | Enforced Mechanism | Cross-Patient Leakage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SQL Relational** | Alice queries | WHERE patient_id = :pat_id | 0 rows from Bob | **PASS** |
| **ChromaDB Dense** | Alice queries | ilter_metadata={'patient_id': 'pat_alice'} | 0 chunks from Bob | **PASS** |
| **BM25 Lexical** | Alice queries | ilter_metadata={'patient_id': 'pat_alice'} | 0 tokens from Bob | **PASS** |
| **Hybrid RRF** | Alice queries | Scoped RRF candidate set | 0 elements from Bob | **PASS** |
| **Negative Query** | Alice requests Bob data | Strict patient context filter | 0 leaks | **PASS** |

**Total Cross-Patient Leakage Events: 0 (100.0% Pass Rate)**

## 2. Citation Provenance Fields
Every retrieved chunk carries verified provenance metadata:
- document_id / 
eport_id: Stable identifier linking to SQL medical_reports.id.
- page_number: 1-indexed document page number.
- chunk_id: Deterministic chunk identifier (chk_{doc_id}_p{page}_c{idx}).
- 	ext: Verifiable excerpt of source clinical text.
