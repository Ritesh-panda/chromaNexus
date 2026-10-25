# Operational Runbook — ChronaNexus

## 1. Quick Start Commands (Verified)

### Backend (FastAPI + Uvicorn)

Open a PowerShell terminal in the project directory:

```powershell
# Option A: Run directly from the project root (Recommended)
python -m uvicorn backend.app.main:app --reload --port 8000

# Option B: Run from inside the backend/ directory
cd backend
uvicorn app.main:app --reload --port 8000
```

> **Backend URL**: [http://localhost:8000](http://localhost:8000)  
> **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)  
> **Alternative ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Frontend (React 19 + Vite)

Open a second PowerShell terminal in the project directory:

```powershell
# 1. Install frontend dependencies (if not already installed)
npm install

# 2. Start Vite development server with HMR
npm run dev
```

> **Development Web App**: [http://localhost:5173](http://localhost:5173)

---

### Production Build & Preview

```powershell
# Compile production bundle (TypeScript typecheck + Vite build)
npm run build

# Serve compiled production bundle locally
npm run preview
```

> **Preview Web App**: [http://localhost:4173](http://localhost:4173)

---

## 2. Automated Quality & Test Commands (Verified)

```powershell
# 1. Run frontend ultra-fast Oxlint linter
npm run lint

# 2. Run frontend TypeScript strict type check
npx tsc -b

# 3. Run complete backend unit & integration pytest suite (190+ tests)
python -m pytest backend/tests -q

# 4. Run targeted Phase 5 structured clinical queries test suite
python -m pytest backend/tests/test_structured_queries.py -v

# 5. Run targeted Phase 6 claim grounding test suite
python -m pytest backend/tests/test_evidence_grounding.py -v

# 6. Run adversarial citation grounding benchmark
python -m pytest tests/benchmarks/test_adversarial_grounding.py -v

# 7. Run 12-scenario synthetic clinical retrieval benchmark
python tests/benchmarks/retrieval_benchmark.py
```

---

## 3. Troubleshooting & Common Pitfalls

### Pitfall 1: `ModuleNotFoundError: No module named 'backend'`
- **Cause**: Running `uvicorn app.main:app` from within `backend/` when `backend/` was not in Python's `sys.path`.
- **Solution**: Resolved permanently in `backend/app/main.py` via automatic path bootstrapping (`_project_root = str(Path(__file__).resolve().parent.parent.parent); sys.path.insert(0, _project_root)`). You can now run from either root or `backend/`.

### Pitfall 2: Dark Mode Forcing Across Entire App
- **Cause**: Tailwind CSS v4 defaults to `@media (prefers-color-scheme: dark)` which overrides in-app settings if the host Windows OS is set to Dark Mode.
- **Solution**: Resolved in `src/index.css` by declaring `@custom-variant dark (&:where(.dark, .dark *));`. Dark mode is now class-driven and strictly respects the in-app sun/moon toggle.

### Pitfall 3: Cascading Red Error Toasts in Chat
- **Cause**: In `src/contexts/UIContext.tsx`, `addToast` was recreated on every render, triggering an infinite `useEffect` re-fetch loop in `AIChatPage.tsx` when the backend was offline.
- **Solution**: `addToast` is now stabilized with `useCallback`, and `chat.service.ts` includes graceful try/catch fallbacks for offline mode.

### Pitfall 4: `RuntimeError: Production database mutation blocked in test environment`
- **Cause**: An automated test attempted to write directly to `chronanexus.db` instead of an isolated temporary test database.
- **Solution**: This is an intentional security guard in `backend/app/core/database.py`. Tests must use the `test_db` fixture from `backend/tests/conftest.py` which provisions an isolated SQLite database or in-memory `StaticPool`.

### Pitfall 5: Ollama Connection Refused (`http://localhost:11434`)
- **Cause**: Local Ollama service is not running.
- **Solution**: Start Ollama by running `ollama serve` in a separate terminal. In automated tests, the application automatically uses the offline `MockDeterministicLLMProvider` so tests pass even without Ollama installed.
