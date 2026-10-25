# ChronaNexus ? Citation Grounding Audit Correction Report

**Audit Date**: October 19, 2026  
**Auditor**: Antigravity Technical Audit Agent  
**Host Environment**: Windows 11 (x86_64, local CPU inference)  
**Ollama Endpoint**: `http://localhost:11434`  
**Ollama Model**: `llama3.2:3b`  
**Embedding Model**: `BAAI/bge-small-en-v1.5` (384 dimensions)  
**Deliverable Document**: `docs/audit/phase4_acceptance_20261018_2330/13_CITATION_GROUNDING_CORRECTION_REPORT.md`  
**Executive Verdict**: **PASS** (Strict Assertions Enforced, Citation Attribution Hardened, Claim-Level Boundary Explicitly Documented)

---

## 1. Executive Summary & Weakness Remediation

This audit resolved the permissive assertions identified in the Phase 4 citation-grounding benchmark (`test_citation_grounding_audit.py`) and hardened the production citation filter in `backend/app/ai/rag/pipeline.py`. 

### Summary of Corrected Weaknesses:

1. **Permissive `A or B` Assertions Eliminated**:
   - *Previous Defect*: `test_02` accepted `assert "rep-cbc-01" in rep_ids or "rep-cmp-01" in rep_ids`. This allowed an incorrect Complete Blood Count (`rep-cbc-01`, containing only `WBC: 5.8 x10^3/uL`) to be accepted as supporting evidence for a `potassium: 5.8 mEq/L` claim solely because both contained the token `5.8`.
   - *Correction*: The assertion now strictly mandates `assert "rep-cbc-01" not in rep_ids` and requires exact expected citations `assert rep_ids == ["rep-cmp-01"]`. In production (`pipeline.py`), title matching was hardened: if an answer specifies clinical lab analytes (e.g. `potassium`), candidate reports that lack the claimed analyte are rejected, even if their report title is mentioned in the prompt/answer.

2. **Conflicting Date & Facility Attributions Rejected**:
   - *Previous Defect*: `test_03` accepted `rep-cmp-01` (`Metro Health`, `2026-10-12`) for a claim explicitly asserting `January 1, 2025 at Memorial Hospital` solely because the numeric value `5.8` matched.
   - *Correction*: The assertion now strictly mandates `assert len(rep_ids) == 0`. In production (`pipeline.py`), temporal and institutional contradiction guards were added: when a claim asserts an explicit year (e.g. `2025`) or institutional facility (`Memorial Hospital`), citations with contradictory dates (`2026`) or facilities (`Metro Health`) are rejected.

3. **Separation of Supported Claims from Unsupported Claims**:
   - *Previous Defect*: `test_07` tested a mixed answer with a supported potassium claim and an unsupported cardiac ischemia claim, but only asserted that `rep-cmp-01` was cited.
   - *Correction*: The test now audits both message-level and sentence-level claim support. It verifies that:
     - No candidate report in the corpus is falsely attributed to cardiac ischemia.
     - Sentence-level filtering isolates the supported sentence (`s1` -> `['rep-cmp-01']`) from the unsupported sentence (`s2` -> `[]`, 0 citations).
     - The new `_audit_claim_grounding()` method in `pipeline.py` flags the ungrounded sentence in `unsupported_sentences`.

4. **HTTP Path Verification with Conflicting Date/Facility Query**:
   - Added `test_07_http_incorrect_date_or_facility_handling` in `test_http_chat_ollama.py`. When a patient asks for a lab result at a conflicting date/hospital, the system safely abstains or suppresses `rep_synth_cmp`, returning 0 misleading citations.

---

## 2. Technical Grounding Boundary: Citation Relevance vs Claim Verification

It is critical to formally document the architectural boundary between **citation relevance filtering** and **formal semantic claim verification**:

### What the Current Production Heuristic Can Guarantee:
1. **Unrelated Retrieval Suppression**: Nearest-neighbor chunks retrieved by vector search (e.g., lipid panels or prescriptions for a glucose query) are rejected.
2. **Abstention Gating**: When the model indicates absence of data (via regex patterns `_NO_DATA_REGEX_PATTERNS`), all retrieved citations are suppressed.
3. **Contradiction Filtering**: Reports with explicit date or facility contradictions against the answer text are rejected.
4. **Token Collision Prevention**: Generic integers (e.g. `10` from `10 mg` prescription) are prevented from citing unrelated lab claims (e.g. `10 mg/dL` glucose).
5. **Entity-Specific Attribution**: Reports whose titles match but lack the claimed clinical analyte (e.g. CBC when potassium was claimed) are rejected.

### What the Current Heuristic Cannot Guarantee:
1. **Semantic Entailment (NLI)**: Keyword and entity co-occurrence cannot distinguish between affirmative and negative assertions (e.g., *"Potassium was high"* vs *"Potassium was normal"* both match the entity `potassium` and number `5.8`).
2. **Span-Level Attribution in Mixed Messages**: In a single unified text string, message-level citation arrays attach sources that support *any* part of the text. While sentence-level auditing (`_audit_claim_grounding`) can isolate unsupported sentences programmatically, the standard HTTP API schema (`MessageResponse`) returns citations at the conversation turn level.

### Smallest Safe Next Step:
To avoid adding heavy dependencies or slow secondary LLM passes on CPU:
- Retain the current fast, deterministic heuristic in `_filter_grounded_citations()` and `_audit_claim_grounding()`.
- In Phase 5 UI development, attach citations at the sentence/claim level (inline citation chips `[1]`) using `_audit_claim_grounding()` rather than generic message-footer citation dumps.

---

## 3. Strict Citation Audit Benchmark Matrix

Executed via: `python -m pytest tests/benchmarks/test_citation_grounding_audit.py -v -s`  
Result: **10 passed in 175.31s (Exit Code: 0)**

| Test ID | Scenario Description | Previous Permissive Assertion | Corrected Strict Assertion | Production Result |
| :--- | :--- | :--- | :--- | :---: |
| **test_01** | Exact lab value & unit (`Potassium: 5.8 mEq/L`) | `assert "rep-cmp-01" in rep_ids` | `assert rep_ids == ["rep-cmp-01"]` | **PASSED** |
| **test_02** | Wrong report attribution (CBC claimed for potassium) | `assert "rep-cbc-01" in rep_ids or "rep-cmp-01" in rep_ids` | `assert "rep-cbc-01" not in rep_ids`<br>`assert rep_ids == ["rep-cmp-01"]` | **PASSED** |
| **test_03** | Wrong date & facility (Memorial Hospital, 2025) | `assert any(c["reportId"] == "rep-cmp-01" for c in grounded)` | `assert len(rep_ids) == 0` | **PASSED** |
| **test_04** | Conflicting records across facilities | `assert "rep-glu-01" in rep_ids and "rep-glu-02" in rep_ids` | `assert set(rep_ids) == {"rep-glu-01", "rep-glu-02"}` | **PASSED** |
| **test_05** | Missing evidence baseline | `assert len(grounded) == 0` | `assert len(grounded) == 0` | **PASSED** |
| **test_06** | Abstention phrased differently | `assert len(pipeline._filter_grounded_citations(ans, ...)) == 0` | `assert len(pipeline._filter_grounded_citations(ans, ...)) == 0` (all 4 variants) | **PASSED** |
| **test_07** | Mixed answer: supported CMP + unsupported cardiac | `assert "rep-cmp-01" in rep_ids`<br>`assert "rep-rx-01" not in rep_ids` | `assert rep_ids == ["rep-cmp-01"]`<br>`assert s1_grounded == ["rep-cmp-01"]`<br>`assert len(s2_grounded) == 0`<br>`assert len(audit["unsupported_sentences"]) >= 1` | **PASSED** |
| **test_08** | Unrelated retrieved documents | `assert "rep-glu-01" in rep_ids` | `assert rep_ids == ["rep-glu-01"]` | **PASSED** |
| **test_09** | Repeated dates and similar titles (CMP vs CBC) | `assert "rep-cbc-01" in wbc_rep_ids` | `assert wbc_rep_ids == ["rep-cbc-01"]` | **PASSED** |
| **test_10** | Generic number collision (10 mg vs 10 mg/dL) | `assert "rep-rx-01" not in g10` | `assert "rep-rx-01" not in rep_ids`<br>`assert rep_ids == ["rep-glu-01"]` | **PASSED** |

---

## 4. End-to-End HTTP Chat Path Verification

Executed via: `python -m pytest tests/benchmarks/test_http_chat_ollama.py -v -s`  
Result: **7 passed in 218.67s (Exit Code: 0)**

All HTTP tests executed against real local Ollama `llama3.2:3b` using isolated thread-safe in-memory SQLite (`StaticPool`, `check_same_thread=False`) and temporary ChromaDB directories:

1. **`test_01_http_factual_question`**: Verified factual potassium 5.8 mEq/L extraction; cited `rep_synth_cmp` (Score: 1.0). Cold latency: **59.045s**.
2. **`test_02_http_missing_evidence_abstention`**: Verified model abstention on unrecorded LVEF; citations = `[]` (0 misleading citations).
3. **`test_03_http_conflicting_values`**: Verified extraction of conflicting glucose values (105 mg/dL Metro Health vs 142 mg/dL Valley Lab); both `rep_synth_glu1` and `rep_synth_glu2` cited. Warm latency: **25.078s**.
4. **`test_04_http_ollama_outage_error_handling`**: Verified simulated daemon outage returns explicit error response (`reasoningType="error"`, citations=`[]`, 0 mock generation).
5. **`test_05_http_citation_schema_and_metadata`**: Verified citation payload strictly adheres to `CitationSchema` and is restricted to the requesting synthetic patient.
6. **`test_06_http_configured_provider_verification`**: Verified live provider is `ollama (llama3.2:3b)`.
7. **`test_07_http_incorrect_date_or_facility_handling`**: Verified query for conflicting date/facility (January 1, 2025 at Memorial Hospital) safely abstains or suppresses `rep_synth_cmp` (citations = `[]`).

---

## 5. Comprehensive Regression Test Summary

| Suite Path | Scope | Model | Exit Code | Result | Duration |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `tests/benchmarks/test_citation_grounding_audit.py` | Strict citation & claim audit (10 scenarios) | Heuristic / Unit | 0 | **10/10 passed** | 175.31s |
| `tests/benchmarks/test_http_chat_ollama.py` | End-to-end FastAPI HTTP chat router | Real Ollama `llama3.2:3b` | 0 | **7/7 passed** | 218.67s |
| `tests/benchmarks/test_ollama_provider_verification.py` | Direct provider contract & latency profile | Real Ollama `llama3.2:3b` | 0 | **6/6 passed** | 45.60s |
| `tests/benchmarks/test_chat_service_ollama.py` | Isolated chat service integration | Real Ollama `llama3.2:3b` | 0 | **5/5 passed** | 165.44s |
| `backend/tests/test_rag_pipeline.py` | Base RAG pipeline regression | Mock LLM | 0 | **3/3 passed** | 42.71s |
| **Total** | | | **0** | **31/31 passed** | **647.73s** |

---

## 6. Data Preservation & Working Tree Verification

All testing strictly adhered to zero-side-effect protocols:

| Resource Path | Baseline State | Post-Audit State | Verification Result |
| :--- | :--- | :--- | :---: |
| `chronanexus.db` SHA-256 | `be882c255ee738d489d5eb59e97ce6b472d236dfe183513d1b704796ffa5f932` | `be882c255ee738d489d5eb59e97ce6b472d236dfe183513d1b704796ffa5f932` | **Bit-for-bit Invariant** |
| `backend/chronanexus.db` SHA-256 | `e2ca7579a1080f7e9f2d99a1f3888f529ea414c42e09229184ce293a97cf288b` | `e2ca7579a1080f7e9f2d99a1f3888f529ea414c42e09229184ce293a97cf288b` | **Bit-for-bit Invariant** |
| ChromaDB `chronanexus_clinical_chunks` | 77 vectors | 77 vectors | **Bit-for-bit Invariant** |
| Git Working Tree Status | Working tree uncommitted; 0 commits; 0 pushes | Working tree uncommitted; 0 commits; 0 pushes | **Preserved (0 Commits / 0 Pushes)** |

---

## 7. Deliverables Updated

1. `backend/app/ai/rag/pipeline.py`: Hardened `_filter_grounded_citations()` against title-only false positives and conflicting temporal/facility claims; added `_audit_claim_grounding()`.
2. `tests/benchmarks/test_citation_grounding_audit.py`: Replaced permissive assertions with strict, unambiguous expectations across all 10 clinical scenarios.
3. `tests/benchmarks/test_http_chat_ollama.py`: Added `test_07` verifying HTTP handling of conflicting date/facility queries.
4. `docs/audit/phase4_acceptance_20261018_2330/13_CITATION_GROUNDING_CORRECTION_REPORT.md`: This comprehensive audit report.
5. `docs/DEVELOPMENT_MEMORY.md`: Appended concise audit entry.
