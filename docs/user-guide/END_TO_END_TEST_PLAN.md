# ChronaNexus — End-to-End Functional Test Plan

This document provides an ordered, comprehensive test plan for an independent tester or QA engineer verifying **ChronaNexus** (`v1.0.0-rc1`).

---

## 🔒 Tester Privacy & Safety Rules

Before executing any tests, review and adhere to these mandatory safety rules:

1. **Synthetic Data Only**: All tests must use synthetic, fictional patient records and dates. **Never upload real medical records, lab reports, doctor letters, or personal identity documents.**
2. **Local Privacy Boundary**: Keep inference local (`LLM_PROVIDER="ollama"`). Do not configure third-party cloud API keys with test patient data.
3. **No Secret Commits**: Keep `.env` files, JWT keys, and tokens out of version control.
4. **Isolated Purge Testing**: Never test the data purge workflow against a database containing important records. Only execute purge tests on disposable synthetic accounts.
5. **No Blind Trust in HTTP 200**: Verify that returned clinical values, units, and dates are medically coherent and accurately match the source document.
6. **Stop on Leakage**: If you ever observe records from Patient A appearing in Patient B's view, **stop the test immediately and log a Critical bug**.

---

## 📋 Comprehensive Functional Test Matrix

| Test ID | Category | Scenario / Feature | Input / Synthetic Data | Expected Outcome | Status |
|---|---|---|---|---|---|
| **TC-SET-01** | Setup | Backend Liveness Probe | `GET /health` | HTTP 200 with `status: "healthy"` | [ ] PASS / FAIL |
| **TC-SET-02** | Setup | Multi-Component Readiness | `GET /ready` | HTTP 200 with DB, vector store, and storage status | [ ] PASS / FAIL |
| **TC-SET-03** | Setup | Frontend Build Verification | `npm run build` | 0 TypeScript errors, bundle generated | [ ] PASS / FAIL |
| **TC-AUTH-01**| Auth | Valid Demo Sign-In | `alex.vance@example.com` / `Password123!` | Login succeeds, redirected to `/dashboard` | [ ] PASS / FAIL |
| **TC-AUTH-02**| Auth | Invalid Password Rejection | `alex.vance@example.com` / `WrongPass!` | HTTP 401 with `"Invalid email or password."` | [ ] PASS / FAIL |
| **TC-AUTH-03**| Auth | New Patient Registration | Name: `Jordan Smith`, Email: `jordan@test.com` | Account created, associated `Patient` record created | [ ] PASS / FAIL |
| **TC-AUTH-04**| Auth | Duplicate Registration | Existing email address | HTTP 409 Conflict rejection | [ ] PASS / FAIL |
| **TC-AUTH-05**| Auth | Sign Out Workflow | Click Sign Out button | JWT cleared from `localStorage`, redirected to `/login` | [ ] PASS / FAIL |
| **TC-VAULT-01**| Vault | Text-based PDF Upload | Synthetic CBC Lab Report (`.pdf`) | Status progresses to `COMPLETED`; document listed | [ ] PASS / FAIL |
| **TC-VAULT-02**| Vault | Duplicate File Detection | Upload exact same PDF a second time | HTTP 409 Conflict; `"Duplicate document detected"` | [ ] PASS / FAIL |
| **TC-VAULT-03**| Vault | Document Search by Text | Search query `"Glucose"` or `"Metformin"` | Filtered list showing only matching documents | [ ] PASS / FAIL |
| **TC-VAULT-04**| Vault | Filter by Category | Select category `"Blood Report"` | Only blood reports displayed; counts match badge | [ ] PASS / FAIL |
| **TC-VAULT-05**| Vault | Sort by Clinical vs Upload | Toggle Sort By dropdown | Order updates according to test date vs upload date | [ ] PASS / FAIL |
| **TC-VAULT-06**| Vault | Document Multi-Tab Inspector | Click on any document card | Inspect Overview, Extracted Text, Linked Entities | [ ] PASS / FAIL |
| **TC-VAULT-07**| Vault | Document Deletion | Click Delete on uploaded document | Document removed from vault and storage cleanly | [ ] PASS / FAIL |
| **TC-OCR-01** | OCR | Scanned Image PDF Detection | Synthetic image-only PDF | Flagged as `is_scanned: true` by PyMuPDF | [ ] PASS / FAIL |
| **TC-OCR-02** | OCR | Missing OCR Engine Guard | Upload scan when Tesseract missing | Safely marked `[OCR_FAILED]`; no fake data fabricated | [ ] PASS / FAIL |
| **TC-TIME-01** | Timeline | Longitudinal Chronology | Synthetic reports with multiple dates | Events sorted in chronological order | [ ] PASS / FAIL |
| **TC-TIME-02** | Timeline | Event Provenance Link | Click "View Source Report" on timeline | Source document modal opens with matching details | [ ] PASS / FAIL |
| **TC-TIME-03** | Timeline | Event Type Filtering | Filter by `"Encounters"` or `"Diagnostics"` | Only matching milestones displayed | [ ] PASS / FAIL |
| **TC-LAB-01** | Labs | Historical Trend Chart | Select `"Fasting Plasma Glucose"` | Line chart renders all measurements chronologically | [ ] PASS / FAIL |
| **TC-LAB-02** | Labs | Reference Range & Abnormal Flags| Review Glucose reading of 132 mg/dL | Flagged with red `HIGH` badge against normal range | [ ] PASS / FAIL |
| **TC-LAB-03** | Labs | Trend Delta Calculation | Compare earliest vs latest HbA1c | Calculates exact delta (e.g. `-0.6%`) | [ ] PASS / FAIL |
| **TC-CHAT-01** | AI Chat | Factual Retrieval with Citations | *"What was my last glucose reading?"* | AI answers with exact value and clickable `[1]` citation | [ ] PASS / FAIL |
| **TC-CHAT-02** | AI Chat | Embedded Trend in Chat | *"Show my potassium trend"* | AI response includes interactive `ClinicalTrendCard` | [ ] PASS / FAIL |
| **TC-CHAT-03** | AI Chat | Missing Evidence Rejection | *"What were my prostate biopsy findings?"* | AI explicitly states no evidence exists in records | [ ] PASS / FAIL |
| **TC-CHAT-04** | AI Chat | Multi-Turn Thread Continuity | Create new conversation thread | Thread saved in left sidebar; message history persists | [ ] PASS / FAIL |
| **TC-SUM-01** | Summary | Doctor-Ready Summary Generation | Visit `/doctor-summary` | Assembles briefing, conditions, meds, and abnormal labs | [ ] PASS / FAIL |
| **TC-SUM-02** | Summary | Add Appointment Question | Type question and click "Add Question" | Question appears in appointment discussion list | [ ] PASS / FAIL |
| **TC-SUM-03** | Summary | Save Doctor Questions | Click "Save Questions" | Questions persisted to database via API | [ ] PASS / FAIL |
| **TC-SUM-04** | Summary | Print / Export PDF | Click "Print / Export PDF" | Print preview displays cleanly formatted medical brief | [ ] PASS / FAIL |
| **TC-SUM-05** | Summary | Physician Share Link | Click "Generate Physician Link" | Generates secure unguessable UUID-based share token | [ ] PASS / FAIL |
| **TC-FHIR-01** | FHIR | Export HL7 FHIR R4 Bundle | Click "Export FHIR R4 Bundle" in Settings | Downloads valid JSON bundle with Patient & Observations | [ ] PASS / FAIL |
| **TC-FHIR-02** | FHIR | Patient Scoping Verification | Inspect downloaded FHIR JSON | All resource `subject.reference` match target patient ID | [ ] PASS / FAIL |
| **TC-SEC-01** | Security| Cross-Patient Access (IDOR) | Query Patient B's report using Patient A's token | Server returns HTTP 404 or HTTP 403 (Zero leakage) | [ ] PASS / FAIL |
| **TC-SEC-02** | Security| Path Traversal Mitigation | Request download with `../../etc/passwd` | Server returns HTTP 400 or HTTP 403 Forbidden | [ ] PASS / FAIL |
| **TC-AUD-01** | Audit | View Audit Log Trail | Visit Settings > Privacy & FHIR R4 | Table displays logged actions, timestamps, and actors | [ ] PASS / FAIL |
| **TC-AUD-02** | Audit | PHI Sanitization Check | Inspect details in audit log table | Passwords, tokens, and raw narratives are redacted | [ ] PASS / FAIL |
| **TC-PURG-01**| Purge | Purge Preview Request | Click "Request Purge Preview" in Danger Zone| Displays scoped record count and 15-min token | [ ] PASS / FAIL |
| **TC-PURG-02**| Purge | Phrase Mismatch Rejection | Type wrong phrase e.g. `"DELETE"` | Confirmation rejected with error alert | [ ] PASS / FAIL |
| **TC-PURG-03**| Purge | Atomic Purge Execution | Type exact phrase on disposable test account | Data permanently deleted; control accounts intact | [ ] PASS / FAIL |
| **TC-REC-01** | Recovery| Service Recovery After Restart | Terminate backend and restart | Data loads intact without corruption | [ ] PASS / FAIL |
| **TC-REC-02** | Recovery| Offline LLM Graceful Fallback | Stop Ollama and ask chat question | Displays clear warning rather than crashing server | [ ] PASS / FAIL |

---

## 🧪 Detailed End-to-End Scenarios

### Scenario A — First-Time System Setup & Health Check
- **Objective**: Verify that a clean system boots the backend and frontend with healthy dependency checks.
- **Steps**:
  1. Follow [FRESH_SYSTEM_SETUP.md](file:///./FRESH_SYSTEM_SETUP.md) to install dependencies and start both servers.
  2. In your browser, open `http://localhost:8000/health`. Verify `status: "healthy"`.
  3. Open `http://localhost:8000/ready`. Verify `database`, `vector_store`, and `storage` are operational.
  4. Open `http://localhost:5173`. Confirm the landing page loads cleanly.

### Scenario B — Document Ingestion & Provenance Tracking
- **Objective**: Ingest a synthetic medical PDF and verify full extraction and entity linking.
- **Synthetic Test Data**:
  Create a simple synthetic text file or PDF named `Synthetic_Blood_Panel_2024.txt` with content:
  ```text
  METRO GENERAL HOSPITAL - LABORATORY REPORT
  Patient Name: Alex Vance | Date: 2024-05-10
  Attending Physician: Dr. Sarah Jenkins, MD

  COMPREHENSIVE METABOLIC PANEL:
  Fasting Blood Glucose: 112 mg/dL [Reference: 70-99] (HIGH)
  Hemoglobin A1c: 6.5 % [Reference: 4.0-5.6] (HIGH)
  Potassium: 4.2 mEq/L [Reference: 3.5-5.0] (NORMAL)
  Serum Creatinine: 0.9 mg/dL [Reference: 0.6-1.2] (NORMAL)
  ```
- **Steps**:
  1. Go to **Medical Vault** (`http://localhost:5173/vault`) and click **`Upload Document`**.
  2. Select the file, choose category `Blood Report`, set Hospital to `Metro General Hospital`, and click **`Upload & Process`**.
  3. Observe the progress modal move through `RECEIVED` -> `PROCESSING` -> `EXTRACTING` -> `INDEXING` -> `COMPLETED`.
  4. Open the document card and inspect the **Extracted Text** and **Linked Clinical Records** tabs.
  5. Verify that Glucose, HbA1c, and Potassium are correctly extracted.

### Scenario C — Duplicate Document Detection (Deduplication)
- **Objective**: Confirm that uploading the exact same binary file twice triggers duplicate prevention.
- **Steps**:
  1. In the **Medical Vault**, click **`Upload Document`**.
  2. Upload the exact same file (`Synthetic_Blood_Panel_2024.txt`) without modifying its contents.
  3. Click **`Upload & Process`**.
- **Expected Outcome**:
  - Upload fails with HTTP 409 Conflict.
  - UI displays: `"Duplicate document detected. This exact file has already been uploaded for this patient."`
  - No duplicate record appears in the vault list.

### Scenario D — Scanned Document OCR & Defensive Failure Handling
- **Objective**: Verify how the system handles scanned image-only PDFs.
- **Steps**:
  1. Upload a synthetic scanned image-only PDF (e.g. an image placed inside a PDF wrapper without digital text).
  2. Observe the ingestion pipeline.
- **Expected Outcome**:
  - If Tesseract is installed and on PATH: OCR runs, extracts the rasterized text, and completes.
  - If Tesseract is **not** installed: PyMuPDF marks `is_scanned: true`. The backend catches the missing engine defensively, logs a warning, and sets the text to `[OCR_FAILED: OCR engine unavailable]`. **It does not fabricate fake clinical data.**

### Scenario E — Longitudinal Timeline Assembly
- **Objective**: Confirm that multi-facility reports are integrated into a single chronological timeline.
- **Steps**:
  1. Navigate to **Timeline** (`http://localhost:5173/timeline`).
  2. Inspect the chronological ordering of milestones from 2023 to 2024.
  3. Click on the 2023 Hypertension diagnosis card.
  4. Click **`View Source Report`**.
- **Expected Outcome**:
  - The underlying clinical document opens in a modal, showing the exact clinic encounter note where hypertension was diagnosed.

### Scenario F — Laboratory Trends & Multi-Facility Analysis
- **Objective**: Verify historical analyte tracking, abnormal flags, and delta calculations.
- **Steps**:
  1. On the **Timeline** page, locate the **Biomarker Lab Trends** card.
  2. Select **`Fasting Plasma Glucose`** from the analyte selector.
  3. Review the plotted points (e.g., September 2023: 132 mg/dL [HIGH] vs March 2024: 118 mg/dL).
  4. Select **`Hemoglobin A1c`**.
- **Expected Outcome**:
  - Chart renders historical points chronologically.
  - Delta is calculated (e.g., -0.5% or -14.0 mg/dL).
  - Out-of-range points display abnormal badges.

### Scenario G — Evidence-Grounded AI Queries & Hallucination Rejection
- **Objective**: Test that AI reasoning cites evidence and refuses to answer unsupported questions.
- **Steps**:
  1. Navigate to **AI Assistant** (`http://localhost:5173/chat`).
  2. **Test Query 1 (Answerable Fact)**:  
     Type: *"What was my latest glucose reading and is it normal?"*  
     *Verify*: AI responds with the exact value, cites the report with `[1]`, and notes it is slightly above reference range.
  3. **Test Query 2 (Historical Comparison)**:  
     Type: *"How has my HbA1c changed over time?"*  
     *Verify*: AI compares the 2023 reading against the 2024 reading with badge `[COMPARISON]`.
  4. **Test Query 3 (Unanswerable / Hallucination Trap)**:  
     Type: *"What were the findings of my colonoscopy biopsy?"*  
     *Verify*: AI clearly states: *"Your medical records contain no documentation or findings regarding a colonoscopy biopsy."* **No hallucinated details are invented.**

### Scenario H — Doctor-Ready Summary Generation & PDF Export
- **Objective**: Verify physician brief generation, custom question editing, and print formatting.
- **Steps**:
  1. Navigate to **Doctor Summary** (`http://localhost:5173/doctor-summary`).
  2. Verify that active conditions (Type 2 Diabetes, Hypertension), medications (Metformin, Lisinopril), and abnormal labs are listed.
  3. Scroll to **Appointment Questions & Discussion Notes**.
  4. Type: *"Should we reduce my Metformin dosage given my improved HbA1c?"* and click **`Add Question`**.
  5. Click **`Save Questions`**. Refresh the page to confirm the question persisted.
  6. Click **`Print / Export PDF`**.
- **Expected Outcome**:
  - Browser print preview opens with clean, publication-ready clinical formatting without navigation bars.

### Scenario I — HL7 FHIR R4 Bundle Export
- **Objective**: Verify standard clinical data export and JSON schema structure.
- **Steps**:
  1. Navigate to **Settings** (`/settings`) > **Privacy & FHIR R4** tab.
  2. Click **`Export FHIR R4 Bundle`**.
  3. Open the downloaded `chronanexus_fhir_r4_bundle.json` in a text editor.
- **Expected Outcome**:
  - JSON contains `"resourceType": "Bundle"` and `"type": "collection"`.
  - Entries contain valid `Patient`, `Observation`, `Condition`, `MedicationStatement`, and `DocumentReference` resources.
  - All `subject.reference` fields match the authenticated patient's ID.

### Scenario J — Cross-Patient Data Isolation (Security & IDOR)
- **Objective**: Ensure that Patient A cannot view, download, or query Patient B's records.
- **Steps**:
  1. Note Patient A's document ID from the vault inspector (e.g. `rep_001`).
  2. Log out and register a new test user (Patient B).
  3. Attempt to access Patient A's document directly via API or browser:  
     `GET http://localhost:8000/api/v1/reports/rep_001` with Patient B's token.
- **Expected Outcome**:
  - Server returns **HTTP 404 Not Found** or **HTTP 403 Forbidden**.
  - Patient B's vault and timeline show **0 records** from Patient A.
  - Audit log records a security authorization event.

### Scenario K — Security Audit Trail Logging
- **Objective**: Verify that sensitive actions are recorded with sanitized metadata.
- **Steps**:
  1. In **Settings** > **Privacy & FHIR R4**, scroll to the **Security Audit Trail** table.
  2. Look for recent events (`DOCUMENT_UPLOAD`, `SUMMARY_GENERATED`, `FHIR_EXPORT`).
- **Expected Outcome**:
  - Events have precise timestamps, action names, actor IDs, and `SUCCESS` outcomes.
  - Details do not contain raw passwords, session keys, or un-sanitized medical notes.

### Scenario L — Two-Phase Irreversible Patient Data Purge
- **Objective**: Verify GDPR-compliant data erasure with two-phase token confirmation on a disposable account.
- **Steps**:
  1. **Log in as the disposable test user created in Scenario J (DO NOT use the default demo account).**
  2. Upload one test document to give the user data to purge.
  3. Navigate to **Settings** > **Account Data & Purge** tab (`danger`).
  4. Click **`Request Purge Preview`**. Review the scoped record count.
  5. Test negative case: Type `"DELETE"` and click Confirm. Verify it is rejected with an error.
  6. Type the exact phrase: `DELETE MY CLINICAL MEMORY PERMANENTLY`.
  7. Click **`Confirm & Execute Permanent Purge`**.
- **Expected Outcome**:
  - System executes atomic deletion across SQLite, Chroma, and uploads.
  - User is logged out.
  - Log back in with the primary demo account (`alex.vance@example.com`) and verify all Alex Vance data is **100% intact**.

### Scenario M — Service Recovery & Offline Fallbacks
- **Objective**: Test system resilience when background services are stopped or restarted.
- **Steps**:
  1. Stop Ollama in your system tray or task manager.
  2. Go to **AI Assistant** (`/chat`) and send a query: *"What are my medications?"*
  3. Verify the frontend displays a graceful error message without crashing.
  4. Restart Ollama. Re-send the query and verify normal operation resumes.

### Scenario N — Viewport Responsiveness & Usability
- **Objective**: Validate user experience across mobile, tablet, and desktop viewports.
- **Steps**:
  1. Press `F12` in Chrome/Edge and toggle **Device Toolbar** (`Ctrl+Shift+M`).
  2. Test viewport widths:
     - Mobile: `390px` (iPhone 14)
     - Tablet: `768px` (iPad Mini)
     - Desktop: `1440px`
  3. Verify hamburger menu on mobile, responsive table wrapping, and modal visibility.
