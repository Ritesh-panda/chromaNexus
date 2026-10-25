# ChronaNexus — User Manual & Testing Suite

Welcome to the independent documentation and testing package for **ChronaNexus** (`v1.0.0-rc1`).

This documentation is designed for an independent tester or developer starting with a **completely fresh computer**. It provides everything needed to clone the repository, install every dependency, start the application, use every implemented feature, run end-to-end tests, troubleshoot issues, and report reproducible bugs.

---

## 📚 Guide Directory & Recommended Reading Order

To test ChronaNexus efficiently, follow the guides in this exact sequence:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          START HERE                                    │
│   Step 1: docs/user-guide/FRESH_SYSTEM_SETUP.md                        │
│   Install prerequisites, clone repo, configure environment, and start  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│   Step 2: docs/user-guide/USER_MANUAL.md                               │
│   Learn every screen, feature, button, workflow, and limitation        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│   Step 3: docs/user-guide/END_TO_END_TEST_PLAN.md                      │
│   Execute structured test scenarios (A through N) with synthetic data  │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│  docs/user-guide/TROUBLESHOOTING.md  │  │ docs/user-guide/             │
│  Fix errors, port conflicts,         │  │ TEST_RESULTS_TEMPLATE.md     │
│  Ollama, OCR, and database issues    │  │ Record test outcomes & status│
└──────────────────────────────────────┘  └──────────────┬───────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────┐
                                          │ docs/user-guide/             │
                                          │ BUG_REPORT_TEMPLATE.md       │
                                          │ File reproducible defect logs│
                                          └──────────────────────────────┘
```

---

## 📑 File Index

| Document | Purpose | Target Audience |
|---|---|---|
| [FRESH_SYSTEM_SETUP.md](file:///./FRESH_SYSTEM_SETUP.md) | Step-by-step setup guide for a brand-new machine: OS requirements, Python, Node.js, Git, Ollama, OCR, database init, and first launch verification. | New testers, QA engineers, developers |
| [USER_MANUAL.md](file:///./USER_MANUAL.md) | Complete user guide detailing every page: Vault, Ingestion, Timeline, Lab Trends, AI Assistant, Doctor Summary, FHIR Export, Audit Logs, and Data Purge. | Testers, clinicians, end users |
| [END_TO_END_TEST_PLAN.md](file:///./END_TO_END_TEST_PLAN.md) | Structured test matrix and 14 comprehensive scenarios (Scenarios A through N) covering positive flows, edge cases, IDOR security, and failure modes. | QA testers, acceptance reviewers |
| [TROUBLESHOOTING.md](file:///./TROUBLESHOOTING.md) | Diagnostic guide covering port conflicts, model timeouts, missing OCR engines, SQLite locks, Chroma issues, and Windows execution policies. | Anyone encountering runtime errors |
| [BUG_REPORT_TEMPLATE.md](file:///./BUG_REPORT_TEMPLATE.md) | Standardized bug report template with severity definitions, sanitized log submission rules, and reproduction checklists. | Testers logging defects |
| [TEST_RESULTS_TEMPLATE.md](file:///./TEST_RESULTS_TEMPLATE.md) | Execution log, checklist, and sign-off scorecard for recording test results. | QA testers submitting final test runs |

---

## ⚠️ Critical Safety & Testing Rules

1. **Synthetic Data Only**: Always use synthetic, fictional medical records. **Never upload real patient records, personal medical files, real IDs, or real names.**
2. **Local Privacy**: ChronaNexus is configured by default for zero-telemetry, air-gapped local execution. Do not configure external cloud AI providers with sensitive data.
3. **No Secret Commits**: Never commit `.env` files, API keys, passwords, or personal credentials to Git.
4. **Isolated Test Databases**: Acceptance tests and destructive purge tests must run against isolated local test data. Do not use non-disposable databases for destructive testing.
5. **No Production Claims Without Validation**: Internal schema validation is not official HL7 validator certification. Always report verified findings based strictly on actual system behavior.

---

## 🚀 Quick Launch Summary (For Experienced Users)

If your system already has Python 3.11+, Node.js 18+, Git, and Ollama installed:

```powershell
# 1. Clone repository
git clone <REPOSITORY_URL> chronanexus
cd chronanexus

# 2. Setup backend
cd backend
python -m venv venv
.\venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt pymupdf
Copy-Item .env.example .env     # Linux/macOS: cp .env.example .env
uvicorn app.main:app --port 8000 --reload

# 3. Setup frontend (in a separate terminal at project root)
npm install
npm run dev
```

Then navigate to:
- **Web Application**: `http://localhost:5173`
- **Backend API Docs**: `http://localhost:8000/docs`
- **Health Probe**: `http://localhost:8000/health`
- **Readiness Probe**: `http://localhost:8000/ready`
- **Default Demo Account**: `alex.vance@example.com` / `Password123!`
