# AI Agent Handoff Briefing — ChronaNexus

> [!IMPORTANT]
> **MANDATORY INSTRUCTION FOR FUTURE AI AGENTS**:  
> Read this document completely **before** inspecting code, proposing modifications, running migrations, or executing destructive terminal commands in this repository.

---

## 1. Project Identity & Workspace Boundaries

- **Project Name**: ChronaNexus (Longitudinal Medical Intelligence Platform)
- **Active Workspace Root**: `C:\chromaNexus` (also aliased via Windows Directory Junction at `c:\Users\Ritesh Panda\OneDrive\Desktop\chromaNexus`)
- **Primary Domain**: Privacy-first clinical document understanding, patient memory graphing, longitudinal biomarker trend analytics, and evidence-grounded clinical QA.
- **Current Milestone**: Phase 7 Completed (Apple Health UI/UX redesign, clinical data integrity remediation, Phase 5 structured queries, Phase 6 evidence grounding).

---

## 2. Core Architecture Cheat-Sheet

1. **FastAPI Backend (`backend/app/main.py`)**:
   - Entry point: `uvicorn app.main:app` or `python -m uvicorn backend.app.main:app`.
   - Core routers: `auth`, `patients`, `documents`, `reports`, `timeline`, `chat`, `summaries`, `search`.
   - Autoseeds demo patient (Alex Vance) on startup in `lifespan`.
2. **React 19 Frontend (`src/main.tsx`, `src/App.tsx`)**:
   - Dev server: `npm run dev` (Vite, port 5173).
   - Production preview: `npm run preview` (port 4173).
   - Styling: Apple-inspired warm neutral design system in `src/index.css` (`@custom-variant dark`).
3. **Dual-Channel Retrieval**:
   - Structured Query Engine (`backend/app/clinical/structured_query/`): Handles "latest", "previous vs latest", "trends over time" using parameterized SQL queries.
   - Hybrid RAG (`backend/app/ai/rag/`): Dense ChromaDB (`BAAI/bge-small-en-v1.5`, 384 dimensions) + Lexical BM25 Okapi fused via Reciprocal Rank Fusion ($k=60$).
4. **Evidence Grounding Subsystem (`backend/app/clinical/verification/`)**:
   - Atomic clinical claim decomposition, patient record verification, false source attribution correction, and dangling citation purification. Zero fabricated citations.

---

## 3. Strict Safety & Non-Destructive Rules

1. **DO NOT Run Destructive Migrations or Reset Databases**:
   - `chronanexus.db` and `backend/chronanexus.db` are protected.
   - An execution interceptor in `backend/app/core/database.py` deliberately crashes any test that attempts to mutate production database files. Always use isolated test fixtures (`test_db`).
2. **DO NOT Rewrite Existing Journal Entries**:
   - Always append chronological notes to `docs/DEVELOPMENT_MEMORY.md`. Never delete or overwrite earlier entries.
3. **DO NOT Force Dark Mode**:
   - Tailwind CSS v4 class-based dark mode is governed by `@custom-variant dark (&:where(.dark, .dark *));`. Never reintroduce media-query defaults that override the user's manual theme selection.
4. **DO NOT Alter API Contracts**:
   - Keep frontend TypeScript interfaces (`src/types/`) and backend Pydantic schemas (`backend/app/schemas/`) strictly in sync.

---

## 4. Key Verification Commands

```powershell
# Frontend Verification
npm run lint         # Oxlint fast linter (Must exit with code 0)
npx tsc -b           # TypeScript compiler (Must exit with code 0)
npm run build        # Production build verification

# Backend Verification
python -m pytest backend/tests -q                                # Full backend test suite (190+ tests)
python -m pytest backend/tests/test_structured_queries.py -v     # Phase 5 structured queries
python -m pytest backend/tests/test_evidence_grounding.py -v     # Phase 6 evidence grounding
python tests/benchmarks/retrieval_benchmark.py                   # 12-scenario synthetic benchmark
```

---

## 5. Knowledge Base Navigation Index

Before taking on any task, review the corresponding in-depth knowledge base document in `PROJECT_KNOWLEDGE/`:

1. [Project Overview](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/PROJECT_OVERVIEW.md) — Purpose, technology stack, and capabilities.
2. [Folder Structure & Inventory](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/FOLDER_STRUCTURE.md) — File-by-file directory map.
3. [System Architecture](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/ARCHITECTURE.md) — Mermaid diagrams, execution pathways, and interfaces.
4. [Feature-to-Code Map](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/FEATURE_MAP.md) — Exact file locations for every feature.
5. [Data Flow & Persistence](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/DATA_FLOW.md) — SQL schemas, ChromaDB vectors, and file storage.
6. [Dependencies & Configuration](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/DEPENDENCIES_AND_CONFIGURATION.md) — Manifests and environment settings.
7. [Operational Runbook](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/RUNBOOK.md) — Startup commands and troubleshooting solutions.
8. [Testing & Quality Assurance](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/TESTING_AND_QUALITY.md) — Test suites, static analysis, and invariants.
9. [Security & Limitations](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/SECURITY_AND_LIMITATIONS.md) — Threat model, isolation proofs, and known gaps.
10. [Change & Extension Guide](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/CHANGE_GUIDE.md) — Safe recipes for modifying the codebase.
11. [Inspection & Audit Report](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/chromaNexus/PROJECT_KNOWLEDGE/INSPECTION_REPORT.md) — Empirical evidence log and uninspected areas.
