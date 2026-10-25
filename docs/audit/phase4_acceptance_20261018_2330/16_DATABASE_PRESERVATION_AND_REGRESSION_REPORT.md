# ChronaNexus — Database Preservation Incident, Test Isolation & Phase 4 Final Verification Report

**Audit Date**: October 19, 2026  
**Auditor**: Antigravity Technical Audit Agent  
**Host Environment**: Windows 11 (x86_64, local CPU inference, Python 3.13.7, pytest 9.1.1)  
**Ollama Daemon**: `http://localhost:11434` (Model: `llama3.2:3b`)  
**Embedding Model**: `BAAI/bge-small-en-v1.5` (384 dimensions)  
**Deliverable Document**: `docs/audit/phase4_acceptance_20261018_2330/16_DATABASE_PRESERVATION_AND_REGRESSION_REPORT.md`  
**Executive Verdict**: **CONDITIONAL** (Test Isolation Enforced & Proven; Zero Protected SQLite Mutations; Pre-Existing Database Chat Records Fully Identified; Persistent Vector Invariants Disclosed; Full Regression Execution Documented)

---

## 1. Executive Summary & Incident Investigation

### 1.1 The Incident
In audit report `15_FINAL_CITATION_GROUNDING_ACCEPTANCE_REPORT.md`, it was acknowledged that the SHA-256 checksum of the root database `C:\chromaNexus\chronanexus.db` had changed:
- **Baseline SHA-256**: `be882c255ee738d489d5eb59e97ce6b472d236dfe183513d1b704796ffa5f932`
- **Measured Post-Incident SHA-256**: `e89c2d5a67e5de5e871c25c994f057b2ac26b07388246d0cf74e8556a49d6fe6`

### 1.2 Forensic Findings
A forensic read-only inspection (`?mode=ro`) of `chronanexus.db` and comparison against the secondary database `backend\chronanexus.db` (SHA-256: `e2ca7579a1080f7e9f2d99a1f3888f529ea414c42e09229184ce293a97cf288b`, 100% invariant) revealed the exact source and nature of the modification:
1. **Identified Records in `chat_messages`**:
   The baseline database contained 2 messages:
   - `msg_1`: user query regarding Metformin dosage (timestamp: `10:30 AM`, created `2026-10-01 14:16:20`)
   - `msg_2`: AI response citing Comprehensive Metabolic & Lipid Panel (timestamp: `10:31 AM`, created `2026-10-01 14:16:20`)
   Four unintended records (two user-AI dialogue turns) were inserted during an earlier debug run:
   - **Turn 1 (2026-10-19 15:52:28 / 15:53:19)**:
     - User Message ID `3430e8ce-4069-49a6-8f1a-bf14103062d8`: `When was my highest cholesterol reading?`
     - AI Message ID `7bb77138-c4e6-465d-873c-2ec815023c07`: `(Note: No clinical documentation of and, cholesterol, highest, lab, multiple, occasions, october, reading, reported, total was found in the provided records.)`
   - **Turn 2 (2026-10-19 16:01:29 / 16:02:24)**:
     - User Message ID `d555a279-5b06-4707-b386-c0fa3e8e24c5`: `When was my highest cholesterol reading?`
     - AI Message ID `ddf1ab3d-7446-4604-9a72-a08d6ac95ce2`: `The Excerpt: cbc_panel_return.pdf (p.3) does not report the specified clinical findings.`
   - **Conversation Thread**:
     - Conversation `th_1` had its `updated_at` timestamp updated to `2026-10-19 16:02:24.468924`.
2. **Root Cause of Leakage**:
   - `backend/app/main.py`: The FastAPI `lifespan` handler hardcoded `engine` and `SessionLocal` from `backend.app.core.database`, which defaulted to `chronanexus.db`.
   - `backend/tests/conftest.py`: Previously created `./test_chronanexus.db` in the working directory and did not configure `app.state.engine` or `app.state.session_factory`, allowing lifespan hooks and un-overridden dependencies to touch root storage.
   - `tests/benchmarks/test_http_chat_ollama.py`: Instantiated `TestClient(app)` with dependency overrides on `get_db` but without overriding `app.state` or `settings.DATABASE_URL`, triggering the production lifespan database bind.

### 1.3 Preservation Actions
In strict compliance with audit safety rules:
- **Zero manual deletion, updating, or cleaning** of the four chat records was performed.
- **Zero database overwriting or restoring** was performed.
- Both SQLite databases remain in their authentic, non-destructively preserved state.

---

## 2. Test Isolation Architecture & Implementation

To permanently prevent recurrence, a four-layer defense-in-depth isolation system was implemented:

### Layer 1: Engine-Level Mutation Interceptor (`backend/app/core/database.py`)
Registered an active SQLAlchemy event listener on the `Engine` class:
```python
@event.listens_for(Engine, "before_cursor_execute")
def enforce_protected_database_isolation(conn, cursor, statement, parameters, context, executemany):
    is_test_env = bool(os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CHRONANEXUS_TEST_ENV"))
    if not is_test_env:
        return
    stmt_clean = statement.strip().upper() if isinstance(statement, str) else ""
    if not any(stmt_clean.startswith(kw) for kw in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE")):
        return
    raw_url = str(conn.engine.url) if conn and hasattr(conn, "engine") else ""
    if "sqlite" in raw_url:
        db_file = conn.engine.url.database
        if db_file:
            abs_db_file = os.path.abspath(db_file).lower()
            if abs_db_file in PROTECTED_DB_PATHS or os.path.basename(abs_db_file) == "chronanexus.db":
                raise RuntimeError(
                    f"CRITICAL TEST ISOLATION FAILURE: Prohibited mutation query ({stmt_clean.split()[0]}) "
                    f"attempted against protected database file: {abs_db_file}. "
                    "Tests MUST use an isolated in-memory or temporary SQLite database."
                )
```
- Operates at the lowest cursor execution layer across all engines in the test process.
- Blocks any direct or indirect `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER`, or `REPLACE` targeting `chronanexus.db` or `backend/chronanexus.db`.

### Layer 2: Fail-Fast Dependency Guard (`get_db()` in `database.py`)
If a test invokes `get_db()` without providing a dependency override, `get_db()` checks if `engine` resolves to a protected database in test mode and immediately aborts with `RuntimeError` before issuing any query.

### Layer 3: Application Lifespan Isolation (`backend/app/main.py`)
Updated `lifespan` to inspect `getattr(app.state, "engine", engine)` and `getattr(app.state, "session_factory", SessionLocal)`. If running under `PYTEST_CURRENT_TEST` and no explicit test engine is attached to `app.state`, lifespan skips all database mutations and seed operations on the production database.

### Layer 4: Test Fixture Isolation (`backend/tests/conftest.py` & `test_http_chat_ollama.py`)
- `conftest.py` creates a temporary directory for each session with an isolated `test_isolated.db` and temporary Chroma directory `test_chroma`.
- Injects `app.state.engine = test_engine` and `app.state.session_factory = TestingSessionLocal`.
- Overrides `settings.DATABASE_URL` and `settings.CHROMA_PERSIST_DIRECTORY`.
- Provides full dependency override for `get_db`.
- `test_http_chat_ollama.py` binds an in-memory SQLite database with `StaticPool` and points `app.state` to the isolated engine.

### Layer 5: ChromaDB Persistent Store Guard (`backend/app/ai/retrieval.py`)
Added safeguards to `ChromaDBVectorStore.add_documents` and `ChromaDBVectorStore.delete_document`: any write targeting `C:\chromaNexus\data\chroma_db` during test execution raises a fatal `RuntimeError`.

---

## 3. Dedicated Test Isolation Regression Coverage

Authored a new regression suite at `backend/tests/test_database_protection.py` verifying:
1. `test_protected_sqlite_mutation_blocked_by_engine_listener`: Direct SQL mutation queries against `chronanexus.db` and `backend/chronanexus.db` are intercepted and raise `RuntimeError`. (**PASSED**)
2. `test_protected_chromadb_mutation_blocked_by_retrieval_guard`: Mutation attempts against persistent ChromaDB path raise `RuntimeError`. (**PASSED**)
3. `test_http_requests_preserve_protected_databases_and_chroma`: Exercises chat endpoints via FastAPI `TestClient` and proves that SHA-256 hashes of both protected databases remain bit-for-bit invariant before and after HTTP testing. (**PASSED in 74.96s**)

---

## 4. Full Regression & Benchmark Execution Results

### 4.1 Targeted Suites (Live Inference & Core RAG)

| Suite | Command | Exit Code | Results | Duration | Status |
|---|---|:---:|:---:|:---:|:---:|
| **Database Protection** | `python -m pytest backend/tests/test_database_protection.py -v` | `0` | **3 / 3 passed** | 74.96s | **PASSED** |
| **Adversarial Grounding** | `python -m pytest tests/benchmarks/test_adversarial_grounding.py -v` | `0` | **10 / 10 passed** | 92.99s | **PASSED** |
| **Citation Grounding Audit** | `python -m pytest tests/benchmarks/test_citation_grounding_audit.py -v` | `0` | **14 / 14 passed** | 118.73s | **PASSED** |
| **Ollama Provider Verification** | `python -m pytest tests/benchmarks/test_ollama_provider_verification.py -v` | `0` | **6 / 6 passed** | 77.36s | **PASSED** |
| **Chat Service Integration** | `python -m pytest tests/benchmarks/test_chat_service_ollama.py -v` | `0` | **5 / 5 passed** | 138.77s | **PASSED** |
| **End-to-End HTTP Chat** | `python -m pytest tests/benchmarks/test_http_chat_ollama.py -v` | `0` | **7 / 7 passed** | 167.30s | **PASSED** |
| **RAG Pipeline & Retrieval** | `python -m pytest backend/tests/test_rag_pipeline.py backend/tests/test_retrieval.py -v` | `0` | **4 / 4 passed** | 27.31s | **PASSED** |
| **Phase 3 Ingestion** | `python -m pytest backend/tests/test_phase3_ingestion.py -v` | `0` | **10 / 10 passed** | 283.63s | **PASSED** |
| **Hybrid Retriever & Ingestion** | `python -m pytest backend/tests/test_hybrid_retriever.py backend/tests/test_document_ingestion.py backend/tests/test_ingestion_orchestrator.py -v` | `0` | **4 / 4 passed** | 104.74s | **PASSED** |
| **Validator, Sanitizer & Context** | `python -m pytest backend/tests/test_clinical_validator.py backend/tests/test_answer_sanitizer.py backend/tests/test_context_builder.py -v` | `0` | **17 / 17 passed** | 69.24s | **PASSED** |
| **Subtotal Targeted Suites** | **Targeted Regression Suites** | `0` | **80 / 80 passed (100%)** | **1,155.03s** | **ALL PASSED** |

### 4.2 Full Backend Suite (`python -m pytest backend/tests`)
- **Total Tests Collected**: 181
- **Passed**: 170
- **Failed**: 11 (executed during initial run; investigated below)
- **Duration**: 1005.37s (0:16:45)
- **Analysis of Failed Tests**:
  - 7 failures were caused by `InMemoryVectorStore` lacking a `persist_directory` attribute when an initial Chroma guard was placed on the base class. This was resolved immediately, and all 7 affected tests (`test_rag_pipeline_end_to_end`, `test_vector_store_interface_and_crud`, `test_phase3_ingestion`, `test_document_ingestion`, `test_ingestion_orchestrator` (2), `test_hybrid_retriever`) re-ran and **PASSED 100%**.
  - 4 failures (`test_newly_uploaded_report_retrieved_as_top_priority`, `test_extremum_query_preserves_clinical_relevance_over_recency`, `test_patient_isolation_on_uploaded_reports`, `test_chromadb_full_rag_pipeline_citations`): These tests use `MockDeterministicLLMProvider()`. In Phase 4, the citation-grounding engine added strict missing-data citation suppression: when the LLM outputs `(Note: No clinical documentation ... was found)`, citations are suppressed (`citations = []`). These legacy tests asserted `len(citations) > 0` even when the mock returned an abstention statement.

---

## 5. Final Data Preservation & Invariant Audit

| Artifact | Measured Post-Test State | Expected / Baseline | Invariance Status |
|---|---|---|---|
| **Root Database** (`chronanexus.db`) | `e89c2d5a67e5de5e871c25c994f057b2ac26b07388246d0cf74e8556a49d6fe6` | `e89c2d5a67e5de5e871c25c994f057b2ac26b07388246d0cf74e8556a49d6fe6` | **100% INVARIANT across test runs** |
| **Backend Database** (`backend\chronanexus.db`) | `e2ca7579a1080f7e9f2d99a1f3888f529ea414c42e09229184ce293a97cf288b` | `e2ca7579a1080f7e9f2d99a1f3888f529ea414c42e09229184ce293a97cf288b` | **Bit-for-bit invariant (100% UNCHANGED)** |
| **Alembic Revisions** | Root: `[('002_add_document_chunks',)]`; Backend: No table | `002_add_document_chunks` | **100% UNCHANGED (003/004 not applied)** |
| **Persistent ChromaDB** (`data\chroma_db`) | 78 records (`chronanexus_clinical_chunks`) | 78 records | **100% INVARIANT across test runs** |
| **Git Hygiene** | 0 commits, 0 pushes | 0 commits, 0 pushes | **VERIFIED** |
| **Phase Boundary** | Phase 5 strictly untouched | Phase 5 untouched | **VERIFIED** |

*Note on Historical Checksums*: The root database change from `be882c255ee7...` to `e89c2d5a67e5...` occurred prior to this remediation due to two test chat turns. That state was preserved non-destructively per Rule 2. Zero further modifications occurred during this audit.

---

## 6. Outstanding Risks & Next Recommended Actions

1. **Legacy Mock Tests**: Update the 4 legacy tests in `test_new_report_retrieval.py` and `test_chromadb_integration.py` so their mock LLM prompts align with Phase 4 citation-grounding semantics (or use configured provider fixtures).
2. **Production Deployment**: Maintain the engine-level mutation listener and `get_db()` safeguards in code; they activate exclusively under `PYTEST_CURRENT_TEST` and zero-cost in production.
3. **Phase 5 Gate**: With test isolation proven and citation grounding verified across 80 targeted tests, Phase 5 may proceed upon stakeholder approval.

---

## 7. Final Verdict

### **CONDITIONAL**

**Justification**:
- **Test Isolation**: **PROVEN & VERIFIED** across 5 defensive layers. Zero mutations to protected SQLite databases during entire test lifecycle.
- **Incident Resolution**: Pre-existing chat records fully identified, documented, and preserved non-destructively.
- **Targeted Suites**: **80/80 PASSED (100%)**.
- **Full Backend Suite**: 170 passed; 7 isolation fixes verified; 4 legacy mock-semantic test updates pending.
- **Data Preservation**: Invariants confirmed; no unapproved migrations; 0 commits, 0 pushes; Phase 5 untouched.
