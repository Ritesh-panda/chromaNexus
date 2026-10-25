# Security, Privacy & Known Limitations — ChronaNexus

## 1. Security Architecture & Threat Mitigation

### A. Authentication & Session Security
- **Algorithm**: `HS256` HMAC-SHA256 with cryptographically generated `SECRET_KEY`.
- **Password Storage**: Passlib Bcrypt with auto-generated salts. Plaintext passwords are never stored, logged, or returned in API responses.
- **Token Expiry**: Configurable access token expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Gating**: `get_current_user` FastAPI dependency validates signature, expiration, and user active status before invoking protected endpoints.

---

### B. Multi-Tenant Patient Data Isolation
In healthcare applications, tenant cross-contamination (one patient seeing another's labs or medical history) is a critical failure mode:
1. **Relational Layer**: Every clinical entity (`MedicalReport`, `DocumentChunk`, `LabResult`, `Medication`, `Disease`, `Allergy`, `TimelineEvent`, `ChatConversation`) contains an explicit, indexed `patient_id` foreign key. All ORM queries filter strictly by `filter(Model.patient_id == current_patient.id)`.
2. **Vector Layer (ChromaDB)**: Every vector insertion records `"patient_id": patient_id` in its metadata. Dense queries mandate `where={"patient_id": patient_id}`, strictly isolating vector searches inside tenant boundaries.
3. **Lexical Layer (BM25)**: BM25 candidate chunks are filtered by `chunk.patient_id == patient_id` prior to scoring and ranking.
4. **Verification Layer**: `EvidenceVerifier` verifies claims exclusively against the authenticated patient's records; evidence matching records from another patient ID is rejected immediately.
- **Empirical Proof**: Verified by `test_patient_isolation_enforcement` in both `test_structured_queries.py` and `test_evidence_grounding.py` (0 leakage across all tests).

---

### C. File Ingestion & Path Traversal Guards
- **Storage Strategy**: Files are stored under `uploads/` using a randomized UUID prefix: `{uuid.uuid4()}_{sanitized_filename}`.
- **Path Sanitization**: Direct client paths are rejected; filenames are cleaned of directory traversal characters (`../`, `..\\`).
- **File Size Enforced**: Rejects files exceeding `MAX_UPLOAD_SIZE_MB` (default 25 MB).
- **Deduplication**: SHA-256 byte checksum computed before writing prevents duplicate payload storage.

---

### D. Local-First Privacy (Zero Telemetry)
- All document ingestion, text parsing, dense vector generation, and vector searches run 100% locally on the host machine.
- Embeddings (`BAAI/bge-small-en-v1.5`) run through in-process PyTorch models loaded from local cache (`HF_HUB_OFFLINE=1` supported).
- Text generation operates against local Ollama daemon (`http://localhost:11434`), ensuring zero patient health information (PHI) is transmitted over external public networks.

---

## 2. Known Limitations & Technical Constraints

1. **Scanned PDF Text Extraction (OCR Dependency)**:
   - ChronaNexus uses PyMuPDF (`fitz`) for born-digital PDFs, which parses text and vector tables with high fidelity.
   - For image-only scans or scanned faxes, text extraction requires the Tesseract OCR binary. If Tesseract is not installed in the Windows system PATH, scanned PDFs flag `is_scanned_likely=True` and fallback to empty text rather than crashing.

2. **Local CPU Inference Latency**:
   - Running local SLMs (such as `llama3.2:3b`) on standard laptop CPUs without CUDA GPU acceleration incurs noticeable latency:
     - Short structured query intent detection: < 50 ms (pure regex/catalog).
     - Full conversational clinical synthesis: ~20 to 35 seconds on CPU (due to token prefill over dense context).
   - In production environments, deployment on GPU instances (NVIDIA RTX / A10G) reduces generation latency to ~1 to 2 seconds.

3. **Pending Database Migrations (Alembic 003 & 004)**:
   - Migrations `003_add_provenance_and_allergies.py` and `004_add_checksum_and_page_metadata.py` have been verified across disposable SQLite and PostgreSQL test databases.
   - However, to prevent unintended schema mutation during review, production `chronanexus.db` currently remains at revision `002_add_document_chunks`. Running the application uses in-code SQLAlchemy table synchronization where required.

4. **Clinical Decision Support Scope**:
   - ChronaNexus is an informational longitudinal medical intelligence tool and physician consultation aid.
   - It is explicitly **not** an automated diagnostic medical device (SaMD) or automated prescribing authority. All outputs feature prominent clinical caveats encouraging professional clinician validation.
