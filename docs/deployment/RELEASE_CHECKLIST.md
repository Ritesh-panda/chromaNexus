# ChronaNexus — Release Candidate Pre-Flight Checklist & Operational Gates

## 1. Release Identification
- **Release Version**: `v1.0.0-rc1` (Release Candidate 1)
- **Target Target Environment**: On-Premises Clinical Desktop / Private Cloud Healthcare Enclave
- **Release Date**: October 2026
- **Architecture**: Air-Gapped Privacy-Preserving Clinical Timeline & Evidence-Grounded Vault

---

## 2. Pre-Flight Verification Checklist

### A. Environment & Configuration Security
- [x] **Zero Secret Leakage**: No hardcoded production API tokens, private clinical keys, or passwords in repository or git history.
- [x] **Safe Defaults**: `ENVIRONMENT=development` by default; setting `ENVIRONMENT=production` fails startup if `SECRET_KEY` is default or insecure.
- [x] **Strict Offline Enforcement**: `ALLOW_CLOUD_INFERENCE=false` enforced. Cloud APIs cannot be invoked without explicit operator opt-in.
- [x] **Sanitized Operational Logging**: Patient PHI, raw medical transcripts, passwords, and tokens are scrubbed from log streams.
- [x] **Startup Validation**: `validate_runtime_configuration()` executes prior to network socket binding.

### B. Data Store & State Invariants
- [x] **Relational Schema Integrity**: SQLite database passes `PRAGMA integrity_check` and `PRAGMA foreign_key_check`.
- [x] **Chroma Vector Store Intact**: Persistent collection `chronanexus_clinical_chunks` verified (78 baseline chunks preserved).
- [x] **Deduplication Engine**: SHA-256 duplicate document prevention active; duplicate uploads reuse existing indexed chunks.
- [x] **Isolated Purge Capability**: Verified two-phase soft preview and hard token-confirmed purge with cross-patient isolation.

### C. Automated Test Coverage Sign-Off
- [x] **Unit & Component Tests**: Ingestion, Chunking, Extraction, Timeline assembling passing.
- [x] **Phase 8 Vault & Summary Tests**: Document filtering, timeline query, and doctor summary generation passing (15/15).
- [x] **Phase 9 Security, Audit & FHIR Tests**: IDOR blocking, path traversal prevention, FHIR R4 bundling, audit logs passing (9/9).
- [x] **Phase 10 Health & Readiness Probes**: Liveness `/health` and multi-dependency `/ready` passing.
- [x] **Phase 10 End-to-End Validation**: Complete 10-step clinical lifecycle workflow passing on isolated synthetic fixtures.
- [x] **Phase 10 Retrieval & Grounding Benchmark**: 10-scenario synthetic benchmark suite evaluated with metrics logged.

### D. Packaging & Deployment Deliverables
- [x] `.env.example` in root and `backend/.env.example`.
- [x] Multi-stage `Dockerfile` and `docker-compose.yml`.
- [x] Operational deployment, backup, and rollback runbooks in `docs/deployment/`.

---

## 3. Documented Known Limitations

1. **Relational Database Concurrency (SQLite)**:
   - ChronaNexus defaults to SQLite in WAL mode for simplicity and zero-configuration on-premises deployment. While SQLite handles hundreds of concurrent readers efficiently, it supports only one concurrent writer. High-throughput hospital EHR ingestion (> 50 writes/second) should configure PostgreSQL via `DATABASE_URL`.
2. **Local Inference Hardware Requirements**:
   - Running local LLM inference via Ollama (`llama3.2:3b` or `mistral:7b`) requires at least 8 GB RAM (16 GB recommended) and modern CPU AVX2 instructions or a compatible GPU (NVIDIA CUDA / Apple Metal). On resource-constrained hardware, inference responses will exhibit higher latency (~3–8s).
3. **FHIR R4 Validation Scope**:
   - The FHIR export module implements standard HL7 FHIR R4 `Bundle`, `Patient`, `Observation`, `Condition`, `MedicationStatement`, and `DocumentReference` schemas and passes internal schema validators. However, full official validation via the external HL7 Java Validator CLI (`org.hl7.fhir.validator.jar`) requires an external Java runtime not packaged in this repository.
4. **Audit Trail Immutability**:
   - Audit logs are stored in a dedicated relational table with append-only application constraints. While tamper-resistant against application-level users, absolute cryptographic non-repudiation requires piping operational logs to a write-once WORM storage layer or external SIEM in production.

---

## 4. Go / No-Go Decision Gate

| Gate | Requirement | Status | Verification Evidence |
|---|---|---|---|
| **Gate 1: Safety & Privacy** | Zero cross-patient access, sanitized logs, cloud inference off | **GO** | IDOR tests pass; path traversal blocked; `ALLOW_CLOUD_INFERENCE=false`. |
| **Gate 2: Functional Core** | End-to-end clinical workflow operational | **GO** | 10-step synthetic validation suite passes 100%. |
| **Gate 3: Retrieval & Grounding** | Deterministic citation tracking and hallucination avoidance | **GO** | Benchmark runner achieves 75% citation precision and 0% unsupported claims. |
| **Gate 4: Packaging** | Health checks, Docker, configuration templates verified | **GO** | `/health` & `/ready` operational; Docker config validated. |
| **Final Decision** | **RELEASE CANDIDATE 1 (RC1) APPROVED FOR PILOT VALIDATION** | **READY** | All gates cleared. Ready for staging deployment and clinical advisory review. |
