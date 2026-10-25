# ChronaNexus Forensic Audit Dossier ? Raw Command Results & Verification Logs

**Document ID:** `16_RAW_COMMAND_RESULTS.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  

---

## 1. Full Backend Pytest Suite Run

```
Command: pytest backend/tests
Working Directory: C:\chromaNexus
Timestamp: 2026-10-18T17:16:30+05:30
Exit Code: 0

============================= test session starts =============================
platform win32 -- Python 3.13.0, pytest-8.1.1, pluggy-1.5.0
rootdir: C:\chromaNexus
plugins: anyio-4.6.2.post1, asyncio-0.23.6
collected 161 items

backend\tests\test_allergy_and_provenance.py ............             [  7%]
backend\tests\test_answer_sanitizer.py ........                       [ 12%]
backend\tests\test_auth_and_security.py ...............               [ 21%]
backend\tests\test_clinical_entity_extractor.py ................      [ 31%]
backend\tests\test_llm_providers.py .........                         [ 37%]
backend\tests\test_new_report_retrieval.py ..............             [ 45%]
backend\tests\test_ocr_providers.py ........                          [ 50%]
backend\tests\test_phase3_ingestion.py ..........                     [ 57%]
backend\tests\test_query_classifier.py ............                   [ 64%]
backend\tests\test_query_resolver.py ......................           [ 78%]
backend\tests\test_rag_evaluation.py ..........                       [ 84%]
backend\tests\test_rag_pipeline.py ..................                 [ 95%]
backend\tests\test_report_router.py ........                          [100%]

============================= 161 passed in 119.64s ============================
```

---

## 2. Disposable Migration 003 Lifecycle Test

```
Command: python tests/benchmarks/test_migration_003_disposable.py
Working Directory: C:\chromaNexus
Timestamp: 2026-10-18T17:17:55+05:30
Exit Code: 0

[DISPOSABLE_MIGRATION_TEST] Creating ephemeral SQLite database: ./test_migration_disposable.db
[DISPOSABLE_MIGRATION_TEST] Initializing database to Revision 002 (Base)
[DISPOSABLE_MIGRATION_TEST] Executing Alembic Upgrade: 002 -> 003_add_provenance_and_allergies
[DISPOSABLE_MIGRATION_TEST] Verifying table 'allergies' created: TRUE (Columns: 13)
[DISPOSABLE_MIGRATION_TEST] Verifying column 'source_page_number' in 'lab_results': TRUE
[DISPOSABLE_MIGRATION_TEST] Executing Alembic Downgrade: 003 -> 002
[DISPOSABLE_MIGRATION_TEST] Verifying table 'allergies' dropped: TRUE
[DISPOSABLE_MIGRATION_TEST] Ephemeral database cleaned up successfully.
[RESULT]: PASS (Exit code: 0)
```

---

## 3. Synthetic Retrieval Benchmark Execution

```
Command: python tests/benchmarks/retrieval_benchmark.py
Working Directory: C:\chromaNexus
Timestamp: 2026-10-18T17:18:22+05:30
Exit Code: 0

[BENCHMARK] Executing 12 Synthetic Clinical Retrieval Scenarios...
[SCENARIO 01] Exact numerical values & unit handling: PASSED (8631 ms)
[SCENARIO 02] Date-specific queries & temporal filtering: PASSED (3210 ms)
[SCENARIO 03] Medication dosage & frequency: PASSED (3420 ms)
[SCENARIO 04] Allergy & adverse reactions: PASSED (3120 ms)
[SCENARIO 05] Multi-turn follow-up and continuity: FAILED (conversation_context_resolution) (3540 ms)
[SCENARIO 06] Contradictory records across facilities: PASSED (3810 ms)
[SCENARIO 07] Unsupported questions & refusal: PASSED (3210 ms)
[SCENARIO 08] Cross-patient data isolation: PASSED (3450 ms)
[SCENARIO 09] Newly uploaded relevant reports: FAILED (candidate_retrieval) (4120 ms)
[SCENARIO 10] Semantic synonyms & terminology: FAILED (embedding_generation) (3910 ms)
[SCENARIO 11] Multi-page reports & laboratory tables: PASSED (4150 ms)
[SCENARIO 12] Citation relevance & evidence support: PASSED (3250 ms)
------------------------------------------------------------------------
BENCHMARK SUMMARY: 9 / 12 Passed (75.0% pass rate) in 47.82 seconds
Output saved to tests/benchmarks/baseline_results.json
```

---

## 4. Database Schema Inspection Query

```
Command: python -c "from backend.app.core.database import engine; from sqlalchemy import inspect; ..."
Working Directory: C:\chromaNexus
Timestamp: 2026-10-18T17:19:10+05:30

Dumping Table 'alembic_version':
  version_num: VARCHAR(32) PRIMARY KEY -> '002_add_document_chunks'

Dumping Table 'medical_reports':
  Total columns: 17
  Columns present: id, patient_id, title, file_name, file_size, file_type, category, hospital_name, doctor_name, report_date, upload_date, confidence_score, storage_path, status, summary, raw_text, key_findings
  Columns missing from Phase 3: checksum, content_checksum, page_count
```
