# ChronaNexus ? False Source Attribution and Exact-Value Grounding Report

**Audit Date**: October 19, 2026  
**Auditor**: Antigravity Technical Audit Agent  
**Host Environment**: Windows 11 (x86_64, local CPU inference)  
**Ollama Daemon**: `http://localhost:11434` (Model: `llama3.2:3b`)  
**Embedding Model**: `BAAI/bge-small-en-v1.5` (384 dimensions)  
**Deliverable Document**: `docs/audit/phase4_acceptance_20261018_2330/14_SOURCE_ATTRIBUTION_AND_VALUE_GROUNDING_REPORT.md`  
**Executive Verdict**: **PASS** (Source-Claim Incoherence Eliminated, Multi-Source Reconciliation Enforced, Strict Numeric/Unit/Date/Facility Grounding Verified)

---

## 1. Executive Summary & Defect Remediation

In the previous Phase 4 citation-grounding implementation, an answer could name an incorrect clinical source (e.g., *"According to the Complete Blood Count, your potassium was 5.8 mEq/L"*) while the citation filter attached a different, valid report (`rep-cmp-01` Comprehensive Metabolic Panel). This created a **source-attribution mismatch**: the visible answer text displayed a false statement asserting the Complete Blood Count reported potassium, while the attached citation card showed the Comprehensive Metabolic Panel.

This remediation addresses this defect at the foundational pipeline level:
1. **Answer-to-Evidence Reconciliation**: When an answer text names a report that does not report the specified finding, the pipeline detects the mismatch and either:
   - **Corrects the answer text** to attribute the value to the true report (CMP) if unambiguous evidence exists; or
   - **Abstains from the claim** and explicitly notes that the named source does not support the finding.
2. **Exact Clinical Fact Grounding**: Verified clinical claims are extracted into structured tuples `(analyte, value, unit, ref_range, date, facility)`. A citation is retained only when the claim's analyte, value, unit, date, and facility match without contradiction.
3. **Multi-Source Handling**: Discrepant readings across multiple facilities (e.g. 105 mg/dL at Metro Health vs 142 mg/dL at Valley Lab) preserve both valid citations and retain facility attribution.
4. **Mixed Answer Handling**: In responses containing both verified and ungrounded claims, supported claims receive citations while unverified diagnostic assertions are explicitly qualified as lacking clinical documentation in the records.

---

## 2. Root Cause Analysis & Exact Files Changed

### Root Cause
The previous implementation only operated as an output filter on the list of citations (`_filter_grounded_citations`), returning a subset of retrieved `citations`. It treated the raw LLM answer string as read-only. Consequently:
- If the LLM hallucinated a report title in the text (*"According to CBC, potassium is 5.8 mEq/L"*), the filter suppressed CBC and returned CMP based on numerical/analyte overlap.
- The user interface presented a discordant pair: an answer claiming CBC reported the result, accompanied by a citation pointing to CMP.
- Furthermore, generic token overlap previously allowed reference-range bounds (e.g. `3.5` from `Ref: 3.5-5.0`) or integers (e.g. `10 mg` Lisinopril) to mistakenly ground unrelated claims (e.g. `10 mg/dL` glucose).

### Exact Files Changed
1. **`backend/app/ai/rag/pipeline.py`**:
   - Implemented `_extract_clinical_facts_from_citations(citations)`: Parses candidate excerpts into structured clinical facts with analyte names, measured values, units, reference range boundaries, dates, and facility names.
   - Implemented `_reconcile_and_ground_answer(answer, citations)`: Reconciles answer sentences against structured clinical facts. Replaces falsely attributed report titles with unambiguous true sources, eliminates ungrounded citations, and flags unverified claims.
   - Integrated into `RAGPipeline.query()`: Returns reconciled answer text and verified citations.
   - Maintained `_filter_grounded_citations()` and `_audit_claim_grounding()` for backwards compatibility.
2. **`tests/benchmarks/test_citation_grounding_audit.py`**:
   - Expanded from 10 to 14 strict clinical verification scenarios covering: wrong source attribution reconciliation, exact analyte/value/unit matching, cross-analyte collisions, decimal/integer collisions, reference range bounds vs measured values, conflicting measurements across facilities, date/facility attribution mismatches, and mixed supported/unsupported claims.

---

## 3. Before and After Examples

### Example A: Wrong Source Attribution (CBC vs CMP)
- **Clinical Evidence**: Comprehensive Metabolic Panel reports `Potassium: 5.8 mEq/L`. Complete Blood Count reports `WBC: 5.8 x10^3/uL`, no potassium.
- **Raw LLM Answer**: *"According to the Complete Blood Count, your potassium was 5.8 mEq/L."*
- **Before Fix**:
  - Answer Text: *"According to the Complete Blood Count, your potassium was 5.8 mEq/L."* (Unchanged)
  - Attached Citations: `['rep-cmp-01']` (CMP citation attached to false CBC text)
  - Result: **Discordant / False attribution**
- **After Fix**:
  - Answer Text: *"According to the Comprehensive Metabolic Panel, your potassium was 5.8 mEq/L."* (Reconciled)
  - Attached Citations: `['rep-cmp-01']`
  - Result: **Grounded & Consistent**

### Example B: Decimal vs Integer Collision (10 mg Lisinopril vs 10 mg/dL Glucose)
- **Clinical Evidence**: Outpatient Glucose has `105 mg/dL`. Prescription Record has `Lisinopril 10 mg`.
- **Claim**: *"Your fasting blood glucose was 10 mg/dL."*
- **Before Fix**: `10` in prescription record risked citation attachment.
- **After Fix**:
  - Answer Text: Flagged as unverified finding without documentation.
  - Attached Citations: `[]` (0 citations)
  - Result: **Safe rejection**

### Example C: Reference Range Lower Bound vs Measured Value
- **Clinical Evidence**: CMP reports `Potassium: 5.8 mEq/L [HIGH] (Ref: 3.5-5.0)`.
- **Claim**: *"Your potassium was 3.5 mEq/L in the Comprehensive Metabolic Panel."*
- **Before Fix**: Substring `3.5` present in excerpt permitted citation.
- **After Fix**: `3.5` recognized as reference range lower bound, not patient measured value.
  - Attached Citations: `[]` (0 citations)
  - Result: **Safe rejection**

### Example D: Conflicting Measurements Across Facilities
- **Clinical Evidence**: Metro Health Outpatient Fasting Glucose `105 mg/dL` on 2026-09-01; Valley Lab Diagnostic Endocrinology Panel `142 mg/dL` on 2026-09-05.
- **Claim**: *"Your fasting glucose results show discrepant readings across facilities: 105 mg/dL at Metro Health on 2026-09-01 (Outpatient Fasting Glucose) and 142 mg/dL at Valley Lab on 2026-09-05 (Diagnostic Endocrinology Panel)."*
- **After Fix**: Both `rep-glu-01` and `rep-glu-02` correctly verified and retained.

---

## 4. Comprehensive Test Matrix

| # | Test Scenario | Claim / Input | Expected Grounding Outcome | Result |
|---|---------------|---------------|----------------------------|--------|
| 1 | Exact lab value & unit | Potassium 5.8 mEq/L (CMP) | Citation attached (`rep-cmp-01`) | **PASS** |
| 2 | Wrong source attribution | Potassium 5.8 mEq/L attributed to CBC | Text reconciled to CMP; CMP cited | **PASS** |
| 3 | Correct analyte, wrong value | Potassium 3.8 mEq/L (Evidence: 5.8) | 0 citations | **PASS** |
| 4 | Correct value, wrong analyte | Sodium 5.8 mEq/L (Evidence: Potassium 5.8) | 0 citations | **PASS** |
| 5 | Incorrect unit | Potassium 5.8 mg/dL (Evidence: mEq/L) | 0 citations | **PASS** |
| 6 | Decimal vs integer collision | Glucose 10 mg/dL (Evidence: 105 mg/dL, Lisinopril 10 mg) | 0 citations | **PASS** |
| 7 | Reference range bound | Potassium 3.5 mEq/L (Evidence: 3.5 is ref bound) | 0 citations | **PASS** |
| 8 | Conflicting facility measurements | Metro Health 105 mg/dL & Valley Lab 142 mg/dL | Both citations retained (`rep-glu-01`, `rep-glu-02`) | **PASS** |
| 9 | Conflicting date & facility | Potassium 5.8 on 2025-01-01 at Memorial Hospital | 0 citations | **PASS** |
| 10 | Missing evidence abstention | LVEF not reported in echo records | 0 citations | **PASS** |
| 11 | Rephrased abstention | EF never evaluated in patient history | 0 citations | **PASS** |
| 12 | Mixed claims | Potassium 5.8 (supported) + severe cardiac ischemia (unsupported) | CMP cited; ischemia explicitly flagged as unverified | **PASS** |
| 13 | Cross-analyte value collision | WBC 140 x10^3/uL (140 belongs to Sodium) | 0 citations | **PASS** |
| 14 | Multiple reports similar values | 105 mg/dL glucose on 2026-09-01 | Only Outpatient Glucose cited (`rep-glu-01`) | **PASS** |

---

## 5. Test Execution Results

### Layer 1: Unit & Benchmark Grounding Tests (Mock/Synthetic Fixtures)
- **Command**: `python -m pytest tests/benchmarks/test_citation_grounding_audit.py -v -s`
- **Exit Code**: `0`
- **Results**: 14 passed, 0 failed, 0 skipped
- **Runtime**: 148.07s (0:02:28)

### Layer 2: RAG Pipeline Base Regressions
- **Command**: `python -m pytest backend/tests/test_rag_pipeline.py -v`
- **Exit Code**: `0`
- **Results**: 3 passed, 0 failed, 0 skipped
- **Runtime**: 34.37s

### Layer 3: Direct LLM Provider Tests (Live Ollama Inference)
- **Command**: `python -m pytest tests/benchmarks/test_ollama_provider_verification.py -v`
- **Exit Code**: `0`
- **Results**: 6 passed, 0 failed, 0 skipped
- **Runtime**: 67.03s (0:01:07)

### Layer 4: Chat Service Integration Tests (Live Ollama Inference)
- **Command**: `python -m pytest tests/benchmarks/test_chat_service_ollama.py -v`
- **Exit Code**: `0`
- **Results**: 5 passed, 0 failed, 0 skipped
- **Runtime**: 241.63s (0:04:01)

### Layer 5: End-to-End HTTP Endpoint Tests (FastAPI TestClient + Live Ollama Inference)
- **Command**: `python -m pytest tests/benchmarks/test_http_chat_ollama.py -v -s`
- **Exit Code**: `0`
- **Results**: 7 passed, 0 failed, 0 skipped
  - `test_01_http_factual_question`: PASSED (Cold latency: 71.589s, live Ollama answer text & citation verified)
  - `test_02_http_missing_evidence_abstention`: PASSED (Abstention verified, citations: 0)
  - `test_03_http_conflicting_values`: PASSED (Warm latency: 37.199s, citations: `['rep_synth_glu1', 'rep_synth_glu2']`)
  - `test_04_http_ollama_outage_error_handling`: PASSED (Explicit HTTP 500 error, zero silent mock fallback)
  - `test_05_http_citation_schema_and_metadata`: PASSED (Page, snippet, title schema validated)
  - `test_06_http_configured_provider_verification`: PASSED (`ollama:llama3.2:3b` verified)
  - `test_07_http_incorrect_date_or_facility_handling`: PASSED (Unverified date/facility rejected, citations: 0)
- **Runtime**: 289.34s (0:04:49)

**Cumulative Verification**: 35 passed across 5 test suites with 0 failures and 0 skips.

---

## 6. Mandatory Data Preservation Audit

| Artifact | Reference / Expected State | Post-Remediation Measured State | Verification Status |
|----------|----------------------------|---------------------------------|---------------------|
| Root Database (`C:\chromaNexus\chronanexus.db`) | `be882c255ee738d489d5eb59e97ce6b472d236dfe183513d1b704796ffa5f932` | `be882c255ee738d489d5eb59e97ce6b472d236dfe183513d1b704796ffa5f932` | **VERIFIED (Unchanged)** |
| Backend Database (`C:\chromaNexusackend\chronanexus.db`) | `e2ca7579a1080f7e9f2d99a1f3888f529ea414c42e09229184ce293a97cf288b` | `e2ca7579a1080f7e9f2d99a1f3888f529ea414c42e09229184ce293a97cf288b` | **VERIFIED (Unchanged)** |
| Persistent Chroma Collection (`chronanexus_clinical_chunks`) | 77 records (`C:/chromaNexus/data/chroma_db`) | 77 records | **VERIFIED (Unchanged)** |
| Alembic Migrations | No 003 / 004 applied to production DB | Clean (isolated in-memory test DB used) | **VERIFIED** |
| Git Hygiene | Clean commit tree (0 commits, 0 pushes) | 0 commits, 0 pushes | **VERIFIED** |

---

## 7. Remaining Limitations & Boundaries

1. **Heuristic Clinical Tuple Extraction vs. Full NLI Engine**:
   - Fact extraction currently utilizes structured regex patterns tailored to clinical laboratory panels, prescriptions, and vital signs.
   - It does not perform full natural language inference (NLI) on arbitrary narrative clinical notes (e.g. nuanced surgical history or complex multi-clause pathology impressions).
   - This boundary is strictly respected: heuristic extraction is NOT labeled as formal clinical validation or semantic entailment.
2. **Local CPU Inference Latency**:
   - `llama3.2:3b` runs locally via CPU on Windows. Cold latency is ~71s, warm latency is ~25-37s per generation.
   - For interactive production environments, a dedicated GPU or streaming token transport is required.
3. **Phase Scope**:
   - This remediation was strictly confined to Phase 4 citation and source-attribution correctness. Phase 5 work was not started.

---

## 8. Final Verdict

### **PASS**

All acceptance criteria are satisfied:
1. Wrong source attributions are actively reconciled in the answer text, eliminating discordance with citation cards.
2. Exact value, unit, analyte, date, and facility matching prevents misleading citations via token overlap.
3. Multi-source records and mixed sentences are evaluated claim-by-claim.
4. Regression suites passed across unit, service, HTTP, and live-Ollama layers (35/35 tests passing).
5. Data preservation was verified with matching SHA-256 hashes and 77 Chroma vector records intact.
