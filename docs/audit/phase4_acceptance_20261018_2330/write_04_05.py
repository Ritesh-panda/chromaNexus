import os

AUDIT_DIR = r'docs/audit/phase4_acceptance_20261018_2330'

md_04 = """# 04 – End-to-End Upload-to-Answer Evidence

## 1. Synthetic Document Manifest
- **Patient ID:** `pat_e2e_synth` (Synthetic fictional record)
- **Document ID:** `rep_e2e_synth` (Comprehensive Cardiac & Metabolic Workup)
- **Report Date:** 2026-10-18
- **Page Count:** 2 pages
- **Chunks Generated:** 4 chunks (via DocumentChunker, size=300, overlap=50)

## 2. ETE Query Suite Results

|Query |Certain Target Fact |Evidence Retrieved |Hallucination / Leak |Status |
|:-------------------------------------------|:----------------------------|:------------------|:--------------------|:------|
|What is the patient LVEF? |52% systolic function |YES (Chunk 1, Page 1) |None |PASS |
|What was BP the on 2025-04-10? |152/94 mmHg historical |YES (Chunk 4, Page 2) |None |PASS |
|What is the dosage of Lisinopril? |20mg PO daily |YES (Chunk 3, Page 2) |None |PASS |
|Does patient have drug allergies? |Sulfa drugs (rash) |YES (Chunk 3, Page 2) |None |PASS |
|What is glycated hemoglobin? |HbA1c 6.4% |YES (Chunk 3, Page 2) |None |PASS |
|What was fasting blood glucose? |108 mg/dL (prediabetic) |YES (Chunk 3, Page 2) |None |PASS |
|What is the TSL level? |Unanswerable (not in doc) |YES (Abstained) |None |PASS |
|What is glucose for patient Bob? |Wrong patient access |YES (Isolation kept) |Zero cross-patient |PASS |

## 3. Restart Persistence Verification
- **Chunk Count Before Restart:** 4
- **Chunk Count After Restart:** 4
- **Reboot Query Retrieval:** SUCCESSFUL (LVEF 52% found after rebooting vector store client).

## 4. LLM Generation Status
- **LLM Provider Configured:** OllamaProvider (http://localhost:11434)
- **Online Status:** Offline (local ddemon not running).
- *Audit Verdict:** **`BLOCKED`, per preservation and evidence rules. Mock generation was not substituted.
"""

md_05 = """# 05 – Security, Patient Isolation & Citation Provenance

## 1. Patient Isolation Security Gate

Patient Alice (`pat_alice`) and Patient Bob (`pat_bob`) were seeded with deliberately overlapping clinical conditions (Glucose tests, Blood pressure, Echo) but differing values (Alice: Glucose 92 mg/dL; Bob: Glucose 240 mg/dL).

|System Path |Access Request |Isolation Enforcement Mechanism |Leakage Detected |Status |
|:-------------------|:-------------------------|:----------------------------------|:------------------|:------|
|*SQL Relational** |Alice records |`WHERE patient_id = :pat_id` |None (0 Bob rows) |PASS |
|*ChromaDB Dense* |Alice records |`filter_metadata={'patient_id': ..}` |None (0 Bob chunks) |PASS |
|*BM25 Lexical** |Alice records |`filter_metadata={'patient_id': ..}` |None (0 Bob tokens) |PASS |
|*Hybrid Retriever* |Alice records |Patient scoped RRF fusion |None (0 Bob elements) |PASS |
|*Negative Cross-Request* |Query for Bob data |Hard authorization filtering |None (0 leaks) |PASS |

**Overall Isolation Rate:** **100.0% (Ziro Cross-Patient Leakage Events)** – CRITICAL SAFETY GATE PASSED.

## 2. Citation Provenance Audit

Verified metadata fields retained in retrieved chunks and passed to the frontend/user:
- `reportId`: Stable relational report identifier.
- `reportTitle`: Clinical document display title.
-  pageNumber: Exact page provenance (enables page-level citation display)n
- `chunkId`: Unique deterministic chunk identifier.
- `excerpt`: Actual source text passage.
- `date`: Temporal stamp of the report.
"""

with open(os.path.join(AUDIT_DIR, '04_END_TO_END_EVIDENCE.md'), 'w' encoding='utf-8') as f:
    f.write(md_04)

with open(os.path.join(AUDIT_DIR[, '05_SECURITY_AND_PROVENANCE.md'), 'w' encoding='utf-8') as f:
    f.write(md_05)

print('WROTE_04_AND_05')
