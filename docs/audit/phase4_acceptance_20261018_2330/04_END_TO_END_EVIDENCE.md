# 04 — End-to-End Upload-to-Answer Evidence

## 1. Synthetic Document Manifest
- **Patient Identifier:** pat_e2e_synth
- **Document Identifier:** 
ep_e2e_synth
- **Report Title:** Comprehensive Cardiac & Metabolic Workup
- **Report Date:** 2026-10-18
- **Page Count:** 2 pages (5 facts on Page 1, 7 facts on Page 2)
- **Chunks Indexed:** 4 chunks

## 2. Query Evidence Matrix

| Query | Target Fact | Retrieved Chunk | Page Provenance | Evidence Retrieved |
| :--- | :--- | :--- | :--- | :--- |
| Left ventricular ejection fraction | 52% systolic function | chk_rep_e2e_synth_p1_c0 | Page 1 | **YES** |
| Historical blood pressure on 2025-04-10 | 152/94 mmHg | chk_rep_e2e_synth_p2_c1 | Page 2 | **YES** |
| Lisinopril dosage | 20mg PO daily | chk_rep_e2e_synth_p2_c0 | Page 2 | **YES** |
| Drug allergies | Sulfa drugs (rash) | chk_rep_e2e_synth_p2_c0 | Page 2 | **YES** |
| Glycated hemoglobin | HbA1c 6.4% | chk_rep_e2e_synth_p2_c0 | Page 2 | **YES** |
| Fasting blood glucose | 108 mg/dL | chk_rep_e2e_synth_p2_c0 | Page 2 | **YES** |
| Thyroid stimulating hormone TSH | Absent (Unanswerable) | None | N/A | **Abstained** |
| Glucose for patient Bob | Wrong patient context | None | N/A | **Isolated** |

## 3. Application Restart Persistence
- Vector count before restart: 4
- Vector count after restart: 4
- Query after reboot: Evidence for 'ejection fraction' 52% retrieved successfully from persistent disk.
- Persistence Status: **PASS**

## 4. LLM Generation Status
- Status: **BLOCKED**
- Reason: Local Ollama daemon offline at http://localhost:11434. Mock responses intentionally avoided per audit rules.
