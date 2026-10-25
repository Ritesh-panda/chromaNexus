# ChronaNexus — Troubleshooting & Diagnostic Guide

This guide provides practical solutions for common installation, configuration, runtime, and dependency issues encountered when setting up and testing **ChronaNexus**.

Each entry provides:
- **Symptom**: What you see on screen or in logs.
- **Likely Cause**: Why the issue is occurring.
- **Diagnostic Command**: Safe command to inspect the issue.
- **Recovery Steps**: Concrete steps to resolve the problem.

---

## 1. Environment & Setup Issues

### Issue 1.1: PowerShell Script Execution Policy Error
- **Symptom**: When activating the virtual environment (`.\venv\Scripts\activate`), PowerShell prints:
  ```text
  File ...\venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
  ```
- **Likely Cause**: Windows PowerShell restricts running unsigned scripts by default.
- **Diagnostic Command**:
  ```powershell
  Get-ExecutionPolicy
  ```
- **Recovery Steps**:
  Run this command in your active PowerShell window (it only affects the current terminal session safely):
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\venv\Scripts\activate
  ```

---

### Issue 1.2: Missing Python Dependencies (`ModuleNotFoundError`)
- **Symptom**: Backend startup fails with:
  ```text
  ModuleNotFoundError: No module named 'fitz' (or 'chromadb', 'fastapi', 'sentence_transformers')
  ```
- **Likely Cause**: Dependencies were installed outside the virtual environment, or `pymupdf` was omitted.
- **Diagnostic Command**:
  ```powershell
  # Verify you are inside (venv) and check installed packages:
  pip list | Select-String "fastapi|fitz|chromadb|PyMuPDF"
  ```
- **Recovery Steps**:
  Ensure your virtual environment is active, then install all dependencies:
  ```powershell
  pip install --upgrade pip
  pip install -r requirements.txt pymupdf
  ```

---

### Issue 1.3: Port 8000 Already in Use (Backend Port Conflict)
- **Symptom**: `uvicorn` fails to start with:
  ```text
  [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): only one usage of each socket address is normally permitted
  ```
- **Likely Cause**: A previous uvicorn instance or another service is already using port 8000.
- **Diagnostic Command**:
  ```powershell
  # Find the process ID listening on port 8000:
  netstat -ano | findstr :8000
  ```
- **Recovery Steps**:
  - **Option A**: Terminate the lingering process using its PID:
    ```powershell
    Stop-Process -Id <PID> -Force
    ```
  - **Option B**: Run Uvicorn on an alternate port (e.g., 8001):
    ```powershell
    uvicorn app.main:app --port 8001 --reload
    ```
    *(Note: If changing to port 8001, create a `.env` in the project root with `VITE_API_BASE_URL="http://localhost:8001/api/v1"` so the frontend points to the new port).*

---

### Issue 1.4: Port 5173 Already in Use (Frontend Port Conflict)
- **Symptom**: Vite dev server displays:
  ```text
  Port 5173 is in use, trying another one...
  ➜ Local: http://localhost:5174/
  ```
- **Likely Cause**: Another Vite or Node process is active.
- **Recovery Steps**:
  You can use `http://localhost:5174` normally! ChronaNexus includes `http://localhost:5174` in its default CORS configuration. If you prefer port 5173, close other running Node windows.

---

## 2. Database & Vector Store Issues

### Issue 2.1: SQLite Database Locked (`sqlite3.OperationalError: database is locked`)
- **Symptom**: An API request times out or logs `database is locked`.
- **Likely Cause**: Multiple backend processes or an open database browser holds an exclusive transaction lock on the SQLite file.
- **Diagnostic Command**:
  ```powershell
  Get-Process python
  ```
- **Recovery Steps**:
  1. Close any SQLite GUI tools (DB Browser for SQLite, DBeaver) inspecting `chronanexus.db`.
  2. If multiple Uvicorn instances are running, close all Python terminals and restart just one.
  3. ChronaNexus uses SQLite WAL (Write-Ahead Logging) mode, which allows concurrent readers alongside writers. Do not delete `chronanexus.db` to fix a lock.

---

### Issue 2.2: Vector Store Directory Permission Error
- **Symptom**: Server logs show:
  ```text
  Chroma persist directory './data/chroma_db' cannot be created or is read-only.
  ```
- **Likely Cause**: The directory was created by an administrator or has restrictive folder permissions.
- **Recovery Steps**:
  Ensure the `data/` directory is writable by your user account:
  ```powershell
  New-Item -ItemType Directory -Force -Path "data\chroma_db"
  ```

---

## 3. AI & Inference Issues (Ollama)

### Issue 3.1: Ollama Not Running (`ConnectionRefusedError: [Errno 111]`)
- **Symptom**: Backend logs show:
  ```text
  Cannot connect to Ollama daemon at http://localhost:11434. Connection refused.
  ```
- **Likely Cause**: The Ollama background service is not started.
- **Diagnostic Command**:
  ```powershell
  curl http://localhost:11434
  ```
- **Recovery Steps**:
  1. Launch Ollama from your Start Menu / Applications.
  2. Verify that the Ollama icon appears in your Windows system tray.
  3. Re-run `curl http://localhost:11434` to confirm `Ollama is running`.
  4. Check the ChronaNexus readiness probe at `http://localhost:8000/ready`.

---

### Issue 3.2: Configured Model Missing (`model 'llama3.2:3b' not found`)
- **Symptom**: Ingestion or chat logs display:
  ```text
  ollama._types.ResponseError: model 'llama3.2:3b' not found, try pulling it first
  ```
- **Likely Cause**: Ollama is running, but the specific model weights have not been downloaded.
- **Diagnostic Command**:
  ```powershell
  ollama list
  ```
- **Recovery Steps**:
  Pull the required models:
  ```powershell
  ollama pull llama3.2:3b
  ollama pull all-minilm
  ```

---

### Issue 3.3: Chat Request Times Out on CPU
- **Symptom**: When asking a complex question in `/chat`, the assistant takes more than 30 seconds to reply, or the browser shows a timeout toast.
- **Likely Cause**: On computers without a dedicated NVIDIA GPU, local LLM inference runs on CPU threads, which can take 5–15 seconds per turn.
- **Recovery Steps**:
  1. The API client timeout is set to 60,000 ms (60 seconds) in `src/services/axios.ts`, which accommodates most CPUs.
  2. Ensure your computer is plugged into power and not in "Battery Saver" mode.
  3. Close heavy background applications (video editors, games) while testing local inference.

---

## 4. Document Ingestion & OCR Issues

### Issue 4.1: Scanned Document Reports `[OCR_FAILED]`
- **Symptom**: In the vault inspector, a scanned PDF shows text containing:
  ```text
  [OCR_FAILED: Tesseract OCR engine is not installed or available on PATH]
  ```
- **Likely Cause**: Tesseract OCR is not installed or not added to your system environment variables.
- **Diagnostic Command**:
  ```powershell
  tesseract --version
  ```
- **Recovery Steps**:
  - If you need OCR for scanned images: Install Tesseract using the UB-Mannheim installer ([github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)), ensure `C:\Program Files\Tesseract-OCR` is in your `PATH`, and restart your terminal.
  - If you do not need OCR: Native digital PDFs work 100% out of the box via PyMuPDF without Tesseract! ChronaNexus safely marks missing OCR scans so you know OCR was skipped.

---

### Issue 4.2: Duplicate Upload Rejection (HTTP 409 Conflict)
- **Symptom**: Uploading a document produces an error:
  ```text
  Duplicate document detected. This exact file has already been uploaded for this patient.
  ```
- **Likely Cause**: ChronaNexus computes a SHA-256 binary hash of every uploaded file. If the exact same file is already in your vault, it rejects the upload to prevent duplicate records and corrupted statistics.
- **Recovery Steps**:
  - This is expected system behavior, not a defect!
  - To upload a new version, modify the file content or upload a different diagnostic report.

---

### Issue 4.3: Empty or Unsupported Document Upload (HTTP 400 Bad Request)
- **Symptom**: Upload modal displays `"Invalid file format"` or `"Uploaded file is empty"`.
- **Likely Cause**: ChronaNexus accepts only `.pdf` and `.txt` files up to 50 MB. Files with 0 bytes or unsupported extensions (e.g., `.docx`, `.xlsx`, `.exe`) are rejected.
- **Recovery Steps**:
  - Export Word documents or spreadsheets to standard PDF format before uploading.
  - Verify that the test file has a file size greater than 0 bytes.

---

## 5. Frontend & Network Issues

### Issue 5.1: Network Error / API Calls Failing in Browser
- **Symptom**: The frontend shows red toast alerts: `"Network Error"` or `"Failed to fetch"`.
- **Likely Cause**: The FastAPI backend is not running, or CORS origins do not match.
- **Diagnostic Command**:
  Open your browser DevTools (`F12`), go to the **Console** tab, and look for red error messages.
- **Recovery Steps**:
  1. Verify the backend is running in Terminal 1.
  2. Test `http://localhost:8000/health` in your browser.
  3. Ensure `BACKEND_CORS_ORIGINS` in `backend/.env` includes `http://localhost:5173`.

---

### Issue 5.2: Vite Build Warning Regarding Large Chunks
- **Symptom**: During `npm run build`, Vite prints:
  ```text
  (!) Some chunks are larger than 500 kB after minification.
  ```
- **Likely Cause**: Full medical chart bundles (Recharts, Lucide, Tailwind) are bundled together.
- **Recovery Steps**:
  - This is an informational warning, not a build error. The build succeeds with code 0 (`✓ built in Xs`). No action is required.

---

## 6. Diagnostic Command Quick Reference

Keep this quick reference handy when troubleshooting:

```powershell
# 1. Check Python version (Must be 3.11+)
python --version

# 2. Check Node version (Must be 18+)
node --version

# 3. Check Git version
git --version

# 4. Check Backend Health
curl http://localhost:8000/health

# 5. Check System Readiness (Database, Storage, Inference)
curl http://localhost:8000/ready

# 6. Check Ollama Status
curl http://localhost:11434

# 7. Check Downloaded Ollama Models
ollama list

# 8. Check Tesseract OCR
tesseract --version

# 9. Run Automated Test Verification
python -m pytest backend/tests/test_rc1_release_gates.py -v

# 10. Run Frontend Typecheck & Build
npm run build
```
