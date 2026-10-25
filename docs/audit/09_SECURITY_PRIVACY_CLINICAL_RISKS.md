# ChronaNexus Forensic Audit Dossier ? Security, Privacy & Clinical Reliability

**Document ID:** `09_SECURITY_PRIVACY_CLINICAL_RISKS.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  

---

## 1. Security & Privacy Findings Matrix

| Finding ID | Severity | Category | Description | Status & Evidence |
|---|---|---|---|---|
| **SEC-01** | `HIGH` | Cryptographic Secrets | Default development JWT secret key in configuration | `backend/app/core/config.py:15` sets `SECRET_KEY = "dev_secret_key_change_in_production"`. |
| **SEC-02** | `HIGH` | Prompt Injection | Clinical text concatenated directly into LLM prompts | Extracted PDF text inserted into RAG prompt without XML boundaries or sanitization. |
| **SEC-03** | `MEDIUM` | Resource Exhaustion | No file size or page count limits on upload | `documents.py` does not enforce maximum file size or maximum page count before PyMuPDF parsing. |
| **SEC-04** | `LOW` | Transport Security | Insecure local HTTP default for CORS | `main.py:48` allows `http://localhost:5173` without HTTPS enforcement. |
| **SEC-05** | `CRITICAL` | Compliance | Lack of HIPAA audit logging and encryption at rest | No persistent access audit log table exists; SQLite DB stores PHI unencrypted on local disk. |

---

## 2. Patient Data Isolation Audit

The isolation of patient health information (PHI) was audited across database queries and vector retrieval:
- **Relational Layer:** Audited every query in `backend/app/routers/`. All queries explicitly filter by `patient_id == current_patient.id`.
- **Benchmark SC-08 Verification:** In `retrieval_benchmark.py:eval_scenario_08_patient_isolation`, Patient Alpha requested labs; exactly 4 Alpha records were retrieved, with 0 leaked records from Patient Beta.
- **Finding:** Patient isolation is **verified in code and tests**, but relies entirely on developer diligence in writing `WHERE patient_id == ...` rather than PostgreSQL Row Level Security (RLS).

---

## 3. Clinical Reliability & Decision Support Risk

1. **Non-Certified Medical Device:** ChronaNexus is an academic prototype and is **not certified by the FDA, CE, or CDSCO** as a medical device or Clinical Decision Support (CDS) tool.
2. **Hallucination Risk:** When the LLM provider is active, hallucinations in laboratory reference ranges or medication dosages could lead to severe clinical harm if used by patients or clinicians without primary source record verification.
3. **Mock Data Deception:** The frontend's silent fallback to `MOCK_DATA` when API calls fail could lead a user to believe that simulated vitals or medications represent their actual clinical history.
