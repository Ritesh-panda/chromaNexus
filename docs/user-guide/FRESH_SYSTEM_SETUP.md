# ChronaNexus — Fresh-System Installation & Setup Guide

This guide provides complete, step-by-step instructions to install, configure, and launch **ChronaNexus** from scratch on a clean computer.

---

## 1. System Requirements & Dependency Matrix

ChronaNexus is engineered to run locally with zero-telemetry privacy guarantees.

### Hardware Requirements
- **RAM**: Minimum 8 GB (16 GB recommended if running local Ollama inference concurrently).
- **Storage**: Minimum 5 GB free disk space (additional space required if downloading larger LLM weights).
- **CPU**: Modern x86_64 or ARM64 processor (4+ cores recommended).

### Software Requirements Matrix

| Component | Minimum Version | Verified Version | Purpose | Necessity |
|---|---|---|---|---|
| **Operating System** | Windows 10/11, Ubuntu 22.04+, macOS 12+ | Windows 11 Enterprise | Host platform | **Mandatory** |
| **Python** | 3.11+ | 3.13.7 | Backend runtime, ORM, RAG | **Mandatory** |
| **Node.js** | 18.0.0+ | 20.x / 22.x | Frontend JavaScript runtime | **Mandatory** |
| **npm** | 9.0.0+ | 10.x+ | Frontend package manager | **Mandatory** |
| **Git** | 2.30+ | 2.45+ | Repository version control | **Mandatory** |
| **Ollama** | 0.1.30+ | 0.1.x+ | Local offline LLM inference & embeddings | **Recommended** (Falls back to deterministic rule extractor / mock if offline) |
| **Tesseract OCR** | 5.0+ | 5.3+ | Scanned raster image & PDF text recognition | **Optional** (Text-based PDFs work without OCR; missing OCR reports failure defensively) |
| **PyMuPDF (`fitz`)** | 1.24.0+ | 1.27.2 | Vector PDF text and table extraction | **Mandatory for PDFs** |

---

## 2. Step-by-Step Installation

### Step 2.1: Install Base Runtimes

#### A. Install Git
- **Windows**: Download and run the official installer from [git-scm.com](https://git-scm.com/download/win). Keep default installation options.
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install -y git
  ```
- **macOS**:
  ```bash
  xcode-select --install
  ```
- **Verify Git**:
  ```bash
  git --version
  ```

#### B. Install Python
- **Windows**: Download Python 3.11, 3.12, or 3.13 from [python.org](https://www.python.org/downloads/).
  > ⚠️ **CRITICAL ON WINDOWS**: Check the box **"Add python.exe to PATH"** before clicking Install.
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install -y python3 python3-pip python3-venv
  ```
- **macOS**:
  ```bash
  brew install python@3.12
  ```
- **Verify Python**:
  ```bash
  python --version
  pip --version
  ```

#### C. Install Node.js
- Download and install the LTS version of Node.js (v20.x or v22.x) from [nodejs.org](https://nodejs.org/).
- **Verify Node.js & npm**:
  ```bash
  node --version
  npm --version
  ```

---

### Step 2.2: Clone the Repository

Open your terminal or PowerShell and navigate to the directory where you want to keep the project:

```powershell
# Clone the repository
git clone <REPOSITORY_URL> chronanexus

# Enter repository root
cd chronanexus
```

Check the repository status:
```powershell
git status
```
Expected output: `On branch main` or the release branch, clean working tree.

---

### Step 2.3: Configure Local AI Inference (Ollama)

ChronaNexus is pre-configured to use **Ollama** for zero-telemetry, local-only clinical inference and embeddings.

1. **Download Ollama**: Download the installer for your OS from [ollama.com/download](https://ollama.com/download).
2. **Install and Launch**: Complete the installation. Ollama will start automatically and sit in your system tray or run as a background service.
3. **Verify Ollama is Running**:
   Open a browser or run in terminal:
   ```powershell
   curl http://localhost:11434
   ```
   Expected response: `Ollama is running`
4. **Pull Required Models**:
   ChronaNexus uses `llama3.2:3b` for clinical reasoning and summarization, and `all-minilm` for embeddings:
   ```powershell
   ollama pull llama3.2:3b
   ollama pull all-minilm
   ```
5. **Verify Installed Models**:
   ```powershell
   ollama list
   ```
   You should see `llama3.2:3b` and `all-minilm` in the list.

> 💡 **Offline / Low-Resource Fallback**: If Ollama is not installed or your computer has limited RAM, ChronaNexus will still boot! Clinical entity extraction uses deterministic rule-based matching, and the RAG engine will report that the LLM is in offline/mock mode without crashing.

---

### Step 2.4: Configure OCR (Optional — For Scanned Documents)

ChronaNexus extracts clean, digital text from native PDFs without any third-party tools via PyMuPDF. However, if you plan to upload **scanned paper printouts or image-only PDFs**, install Tesseract OCR:

- **Windows**:
  1. Download the 64-bit installer from the UB-Mannheim Tesseract project: [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki).
  2. Run the installer (default path: `C:\Program Files\Tesseract-OCR`).
  3. Add `C:\Program Files\Tesseract-OCR` to your system `PATH` environment variable.
  4. Verify in a new terminal:
     ```powershell
     tesseract --version
     ```
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt install -y tesseract-ocr
  tesseract --version
  ```
- **macOS**:
  ```bash
  brew install tesseract
  tesseract --version
  ```

> 🛡️ **Defensive Failure Guard**: If Tesseract is not installed and you upload a scanned image PDF, ChronaNexus will safely mark the document as `[OCR_FAILED: OCR engine unavailable]` and notify you. It will **never fabricate fake medical entities**.

---

### Step 2.5: Backend Setup & Configuration

1. **Open PowerShell / Terminal** and navigate to the `backend` folder:
   ```powershell
   cd backend
   ```

2. **Create Python Virtual Environment**:
   ```powershell
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   - **Windows PowerShell**:
     ```powershell
     # If you encounter a script execution policy restriction, run:
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     .\venv\Scripts\activate
     ```
   - **Windows Command Prompt (cmd.exe)**:
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```
   Your prompt will now show `(venv)`.

4. **Install Backend Dependencies**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt pymupdf
   ```

5. **Create Backend Environment File**:
   Copy the provided `.env.example` template:
   - **Windows PowerShell**:
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Linux / macOS**:
     ```bash
     cp .env.example .env
     ```

6. **Review Environment Settings (`backend/.env`)**:
   The defaults in `.env.example` are pre-tuned for instant local development:
   ```ini
   ENVIRONMENT="development"
   DATABASE_URL="sqlite:///./chronanexus.db"
   STORAGE_BACKEND="local"
   UPLOAD_DIR="./uploads"
   VECTOR_STORE_BACKEND="chroma"
   CHROMA_PERSIST_DIRECTORY="./data/chroma_db"
   LLM_PROVIDER="ollama"
   OLLAMA_BASE_URL="http://localhost:11434"
   OLLAMA_MODEL="llama3.2:3b"
   EMBEDDING_PROVIDER="ollama"
   OLLAMA_EMBEDDING_MODEL="all-minilm"
   OCR_PROVIDER="auto"
   ```
   *No edits are necessary for standard local testing.*

7. **Verify Database Initialization**:
   You do not need to run manual SQL setup scripts. When the FastAPI application boots, it automatically creates all SQLite tables and seeds the standard demonstration patient profile (**Alex Vance**).

8. **Start the Backend Server**:
   ```powershell
   uvicorn app.main:app --port 8000 --reload
   ```
   Expected console output:
   ```text
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   INFO:     Started reloader process
   INFO:     Application startup complete.
   ```
   **Keep this terminal window open.**

---

### Step 2.6: Frontend Setup & Configuration

1. **Open a SECOND Terminal / PowerShell window**.
2. **Navigate to the repository root directory**:
   ```powershell
   cd chronanexus
   ```
3. **Install Frontend Dependencies**:
   ```powershell
   npm install
   ```
   Expected output: `added XXX packages in Xs` with zero errors.

4. **Verify TypeScript Compilation**:
   ```powershell
   npm run build
   ```
   Expected output: `✓ built in Xs` without any TypeScript or Rollup errors.

5. **Start the Frontend Development Server**:
   ```powershell
   npm run dev
   ```
   Expected console output:
   ```text
     VITE v8.2.x  ready in 450 ms

     ➜  Local:   http://localhost:5173/
     ➜  Network: use --host to expose
     ➜  press h + enter to show help
   ```
   **Keep this second terminal window open.**

---

## 3. Verifying the System

Open your web browser (Chrome, Edge, Firefox, or Brave) and perform the initial verification checks:

### Check 1: Backend Health Probe
Visit: [http://localhost:8000/health](http://localhost:8000/health)  
Expected JSON response:
```json
{
  "status": "healthy",
  "service": "ChronaNexus Medical Intelligence Platform",
  "version": "1.0.0"
}
```

### Check 2: Multi-Subsystem Readiness Probe
Visit: [http://localhost:8000/ready](http://localhost:8000/ready)  
Expected JSON response:
```json
{
  "status": "ready",
  "service": "ChronaNexus Medical Intelligence Platform",
  "environment": "development",
  "version": "1.0.0",
  "components": {
    "database": { "status": "connected" },
    "vector_store": { "backend": "chroma", "status": "operational" },
    "storage": { "path": "./uploads", "status": "writable" },
    "inference_provider": { "provider": "ollama", "status": "available" }
  }
}
```

### Check 3: Interactive API Documentation (Swagger)
Visit: [http://localhost:8000/docs](http://localhost:8000/docs)  
Verify that all 12 API router groups are listed (`Authentication`, `Users`, `Patients`, `Reports`, `Document Vault`, `Timeline`, `AI Clinical Assistant`, `Doctor Summary Engine`, `Search`, `Audit Logs`, `FHIR R4 Export`, and `Purge Engine`).

### Check 4: Frontend Web Application
Visit: [http://localhost:5173](http://localhost:5173)  
1. You will be greeted by the **ChronaNexus Landing Page**.
2. Click **"Sign In"** in the top navigation bar.
3. Sign in using the pre-seeded demo credentials:
   - **Email**: `alex.vance@example.com`
   - **Password**: `Password123!`
4. You will be redirected to the **Longitudinal Dashboard** showing Alex Vance's health records, active conditions, and vitals.

---

## 4. "You Are Ready to Test When..." Checklist

Before beginning the functional test plan, verify that every item on this checklist is checked:

- [ ] **Terminal 1** is running the FastAPI backend on `http://localhost:8000` with no error traces.
- [ ] **Terminal 2** is running the Vite dev server on `http://localhost:5173`.
- [ ] `http://localhost:8000/health` returns status `"healthy"`.
- [ ] `http://localhost:8000/ready` returns status `"ready"`.
- [ ] Ollama service is running (`curl http://localhost:11434` returns `Ollama is running`).
- [ ] `llama3.2:3b` and `all-minilm` are listed in `ollama list`.
- [ ] You can log in at `http://localhost:5173/login` using `alex.vance@example.com` / `Password123!`.
- [ ] You can view documents in the **Medical Vault** (`http://localhost:5173/vault`).

You are now ready to proceed to [USER_MANUAL.md](file:///./USER_MANUAL.md) and [END_TO_END_TEST_PLAN.md](file:///./END_TO_END_TEST_PLAN.md).
