# ChronaNexus — Bug Report Template

When discovering an issue or unexpected behavior during testing, use this standardized template to document the defect.

---

## 🔒 Confidentiality & Privacy Reminders
- **DO NOT include real patient medical records, personal names, real IDs, or real phone numbers.**
- **DO NOT include private passwords, JWT secret keys, API tokens, or `.env` credentials.**
- Sanitize all terminal logs and error traces before attaching them.

---

## 🐞 Bug Report Form

### 1. Header Information
- **Bug ID**: `BUG-XXXX` *(e.g. BUG-001)*
- **Title**: *[Concise summary: Action + Failure + Context, e.g. "Document upload fails with 500 error when filename contains spaces"]*
- **Feature / Screen**: *[Vault / Ingestion / Timeline / Lab Trends / AI Assistant / Doctor Summary / Settings / Auth]*
- **Date Discovered**: *[YYYY-MM-DD]*
- **Tester Name / Handle**: *[Tester Name]*

### 2. Severity Classification
Select one severity level:
- [ ] **Critical**: Cross-patient data leakage (IDOR), unrequested destructive data loss, authentication bypass, or severe security vulnerability.
- [ ] **High**: Core workflow completely blocked (e.g., cannot upload valid PDFs, timeline crashes, AI chat fails completely, cannot log in).
- [ ] **Medium**: Secondary feature broken or incorrect clinical calculation (e.g., lab delta calculation inverted, sort order broken, filter not applying).
- [ ] **Low**: Cosmetic visual glitch, minor layout misalignment, styling issue, or typo.

### 3. Test Environment
- **Operating System**: *[e.g. Windows 11 Enterprise (64-bit) / Ubuntu 22.04 / macOS Sonoma]*
- **Python Version**: *[e.g. Python 3.13.7]*
- **Node.js & npm Version**: *[e.g. Node v20.11.0, npm 10.2.4]*
- **Browser & Version**: *[e.g. Chrome 124.0.x / Edge 124.0.x / Firefox 125.0]*
- **Local AI Provider**: *[e.g. Ollama v0.1.32 with llama3.2:3b / Offline / Mock]*
- **OCR Engine**: *[e.g. Tesseract 5.3.3 installed / Not installed]*
- **Database**: *[e.g. SQLite local (`chronanexus.db`)]*

### 4. Preconditions
*List any state or synthetic data required before reproducing the issue:*
- *Example: User logged in as Alex Vance.*
- *Example: At least two blood reports with different dates already uploaded in the vault.*

### 5. Exact Steps to Reproduce
*Provide clear, numbered steps that anyone can follow to trigger the bug:*
1. Navigate to `http://localhost:5173/...`
2. Click on `...`
3. Enter input: `"..."`
4. Click button `...`
5. Observe the error.

### 6. Expected Behavior
*What should have happened according to the documentation or clinical specifications?*
- *Example: The document should finish processing and appear in the vault with status COMPLETED.*

### 7. Actual Behavior
*What actually occurred? Include exact error messages and visual symptoms.*
- *Example: The upload progress bar hung at 15% and a red toast appeared saying "Internal Server Error".*

### 8. Reproduction Frequency
- [ ] **Always (100% of attempts)**
- [ ] **Intermittent (Reproduces under specific conditions, ~50%)**
- [ ] **Rare / Once (Could not reliably trigger again)**

### 9. Supporting Evidence & Logs

#### A. Browser Console Logs (F12 > Console)
```text
[Paste relevant browser console error messages here]
```

#### B. Backend Terminal Output / Uvicorn Traceback
```text
[Paste sanitized backend terminal traceback here (no credentials or tokens)]
```

#### C. Screenshots / Media References
- *Attach or reference screenshot files: e.g. `screenshot_upload_error_2026-10-25.png`*

### 10. Additional Notes & Workaround
*Did you find a temporary workaround? Any additional observations?*
- *Example: Renaming the file to remove special characters allowed the upload to proceed normally.*
