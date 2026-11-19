# ChronaNexus

> **AI-Powered Longitudinal Medical Intelligence and Auditable Clinical Decision-Support Platform**
> 
> *A B.Tech Capstone Project in Computer Science and Business Systems (CSBS)*  
> **School of Computer Science and Engineering (SCOPE), VIT-AP University, Amaravati**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18%2F19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange.svg)](https://www.trychroma.com)
[![HL7 FHIR](https://img.shields.io/badge/Standard-HL7_FHIR_v4.0.1-firebrick.svg)](https://hl7.org/fhir/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Table of Contents
- [Executive Overview](#-executive-overview)
- [The Clinical Problem & Motivation](#-the-clinical-problem--motivation)
- [System Architecture](#-system-architecture)
  - [Two-Tier Asymmetric Hybrid Verification Engine](#1-two-tier-asymmetric-hybrid-verification-engine)
  - [Unified Gateway & Micro-Service Topology](#2-unified-gateway--micro-service-topology)
  - [Patient Memory State Graph](#3-patient-memory-state-graph)
- [Core Features & Modules](#-core-features--modules)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Academic Deliverables & Research Publication](#-academic-deliverables--research-publication)
- [Quickstart & Installation Guide](#-quickstart--installation-guide)
  - [Prerequisites](#1-prerequisites)
  - [Option A: One-Click Full-Stack + Cloudflare Tunnel (Recommended)](#option-a-one-click-full-stack--cloudflare-tunnel-recommended)
  - [Option B: Manual Development Setup](#option-b-manual-development-setup)
- [Default Demonstration Accounts](#-default-demonstration-accounts)
- [Automated Testing & Release Gates](#-automated-testing--release-gates)
- [Security, Privacy & Compliance](#-security-privacy--compliance)
- [Project Team & Faculty Guidance](#-project-team--faculty-guidance)
- [License](#-license)

---

## 🔬 Executive Overview

**ChronaNexus** is an enterprise-grade medical intelligence platform engineered to solve the **retrieval-verification gap** in longitudinal healthcare informatics. Instead of functioning as a passive PDF repository or a generic generative chatbot prone to medical hallucinations, ChronaNexus extracts clinical entities across multi-year patient trajectories, resolves lab unit discrepancies via stoichiometric conversion, and enforces deterministic verification guardrails before any clinical statement is presented to a physician or patient.

### Key Performance Capabilities:
* **Evidence-Grounded Querying**: 100% of generated responses are cross-referenced with exact document citations, bounding box pages, and audit timestamps.
* **Asymmetric Hybrid Verification**: Combines zero-tolerance symbolic safety rules (holding absolute veto power) with lightweight neural bi-encoders (`all-MiniLM-L6-v2`) for semantic matching.
* **Deterministic Unit Normalization**: Bidirectional conversion across key analyte standards (Creatinine, Glucose, Hemoglobin, Potassium, Sodium) with exact stoichiometric precision tolerance.
* **Longitudinal Lifecycle Tracking**: Detects multi-encounter treatment cessations, drug-drug contraindications, and decouples Review of Systems (ROS) symptom denials from confirmed primary diagnoses.

---

## 🏥 The Clinical Problem & Motivation

Modern patient data is deeply fragmented across disparate healthcare systems:
1. **Multi-Encounter Discontinuation Errors**: A medication prescribed in Encounter 1 (e.g., Lisinopril) may be discontinued in Encounter 3 due to adverse angioedema. Standard RAG pipelines retrieve the prescription passage and falsely assert the patient remains on active therapy.
2. **Measurement Heterogeneity**: Labs alternate between conventional and SI units (e.g., $1.2\text{ mg/dL}$ vs. $106.1\ \mu\text{mol/L}$ Serum Creatinine). General LLMs fail strict stoichiometric conversions.
3. **Review of Systems (ROS) Negation Leakage**: Routine symptom denials (*"Patient denies acute chest pain"*) documented in the same clinical note as primary diagnoses (*"Assessment: Systolic heart failure"*) mislead standard negation extractors into binding across sentence boundaries.
4. **Epistemic Modality Conflation**: Generative models frequently drop conditional hedges (*"If ejection fraction drops below 35%, refer for surgery"*), asserting prospective hypothetical rules as completed historical facts.

**ChronaNexus resolves this retrieval-verification gap by validating assertions through deterministic symbolic constraints before evidence presentation.**

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT / WEB INTERFACE                          │
│               React 18/19 · TypeScript · TailwindCSS v4                │
│    (Interactive Timeline, Vitals Charts, Medical Vault, AI Chat)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST / SSE
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   UNIFIED GATEWAY PROXY (:3000)                        │
│             Reverse Proxy Routing · Static Frontend Serving             │
│        /api/v1/* ──► FastAPI (:8000)   |   /* ──► Vite (:5173)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        ▼                                                       ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│       FASTAPI BACKEND (:8000)   │   │     CHRONANEXUS AI ENGINE       │
│  - JWT Auth & RBAC Security     │   │  - Tier 1: Symbolic Guardrails  │
│  - SQLModel / SQLAlchemy ORM    │   │    * Stoichiometric Normalizer  │
│  - PyMuPDF Ingestion Pipeline   │   │    * Lifecycle Tracker (DDI)    │
│  - Audit Trail & Sanitization   │   │    * Entity-Anchored Negation   │
│  - HL7 FHIR v4.0.1 Serializer   │   │    * Epistemic Modality Filter  │
└───────────────┬─────────────────┘   │  - Tier 2: Bi-Encoder (MiniLM)  │
                │                     └────────────────┬────────────────┘
        ┌───────┴───────┐                              │
        ▼               ▼                              ▼
┌──────────────┐ ┌──────────────┐             ┌─────────────────┐
│ SQLite DB    │ │ Uploads Dir  │             │ ChromaDB Vector │
│ chronanexus  │ │ Encrypted    │             │ data/chroma_db/ │
│ .db (Rel.)   │ │ PDFs / Scans │             │ Persist Store   │
└──────────────┘ └──────────────┘             └─────────────────┘
```

### 1. Two-Tier Asymmetric Hybrid Verification Engine
* **Tier 1 (Deterministic Symbolic Guardrails)**: Holds absolute veto power.
  * *Analyte Normalizer*: Exact stoichiometric conversion with $\pm 0.05$ absolute or $\le 5\%$ relative rounding tolerance. Explicitly rejects assay allowable error to avoid false positives.
  * *Timeline Tracker*: Temporal state machine verifying medication initiation, titrations, and explicit multi-encounter cessations.
  * *Entity-Anchored Negation Scoper*: Isolates negation scope strictly within syntactic sentence boundaries.
  * *Epistemic Modality Filter*: Detects prospective verbs (*recommend, suggest, consider, monitor for*) and suppresses them from being asserted as historical diagnoses.
* **Tier 2 (Dense Neural Alignment)**:
  * Invoked **strictly and only if Tier 1 detects no clinical violations**.
  * Evaluates semantic paraphrasing via sentence embeddings (`all-MiniLM-L6-v2`) under a dual decision threshold:
    $$\text{Cosine Similarity} \ge 0.58 \quad \text{AND} \quad \text{Lexical Overlap} \ge 0.10$$

### 2. Unified Gateway & Micro-Service Topology
* Port `3000` hosts `gateway.py`, a lightweight, non-blocking asynchronous reverse proxy that routes incoming traffic transparently:
  * `/api/v1/*` and `/docs` $\longrightarrow$ FastAPI Core on Port `8000`
  * Static UI and client routes $\longrightarrow$ Vite Frontend on Port `5173`
* Enables seamless single-port tunneling via Cloudflare without CORS discrepancies or cookie partitioning issues.

### 3. Patient Memory State Graph
Instead of isolated files, ChronaNexus constructs an interconnected longitudinal graph:
```
Patient Record
  ├── Demographics & Emergency Contacts
  ├── Active & Historical Conditions (ICD-10 Mapped)
  ├── Medication Lifecycle (Prescription, Dosage, Discontinuation Reason)
  ├── Structured Lab Results & Physiological Trends (LOINC Normalized)
  ├── Longitudinal Timeline Milestones (Encounter Anchored)
  ├── Verified Citations & Bounding Boxes
  └── Cryptographically Auditable Access Logs
```

---

## ⚡ Core Features & Modules

1. **Medical Document Vault**:
   * Drag-and-drop ingestion of laboratory blood panels, discharge summaries, imaging reports, and handwritten prescriptions.
   * Native PyMuPDF text and coordinate extraction with multi-page preview and metadata tagging.
2. **Interactive Longitudinal Health Timeline**:
   * Chronologically sorts clinical milestones across years with category filtering (Surgeries, Inpatient Admissions, Prescriptions, Abnormal Labs).
3. **Physiological Vitals & Lab Trends**:
   * Interactive Recharts visualizations plotting longitudinal trends (HbA1c, Fasting Blood Glucose, Serum Creatinine, Blood Pressure).
   * Visual normal reference band indicators and threshold breach alerts.
4. **Physician Executive Summary Generator**:
   * 60-second synthesized briefing designed for clinical handoffs: active diagnoses, current medication regimen, critical contraindications, and pending investigations.
5. **Conversational Evidence Engine**:
   * Multi-turn clinical chat grounded in patient records. Every sentence is backed by interactive citations that highlight the source PDF text.
6. **HL7 FHIR v4.0.1 Data Portability**:
   * One-click export/import of patient records into standardized HL7 FHIR JSON bundles (`Patient`, `Condition`, `MedicationRequest`, `Observation`, `DiagnosticReport`).
7. **Privacy-First Data Sovereignty**:
   * Local-first execution; runs fully offline with local Ollama models (`llama3.2:3b`, `all-minilm`) with zero cloud data leakage.

---

## 💻 Tech Stack

### Frontend Architecture
| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Framework** | React | `18 / 19` | High-performance component-based client |
| **Language** | TypeScript | `5.8+` | Strict static typing (`verbatimModuleSyntax`) |
| **Build Tool** | Vite | `^6.0 / ^8.0` | Sub-second HMR and optimized production bundling |
| **Styling** | TailwindCSS | `v4` | Utility-first glassmorphism clinical UI design |
| **State & Cache** | TanStack React Query | `^5.0` | Asynchronous server-state synchronization |
| **Routing** | React Router | `^7.0` | Protected client-side routing & auth guards |
| **Visualizations** | Recharts | `^3.0` | Longitudinal physiological trend charts |
| **Icons & Motion** | Lucide Icons & Framer Motion | Latest | Accessible clinical iconography & fluid transitions |

### Backend Architecture
| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Runtime** | Python | `3.11 – 3.13` | High-performance asynchronous runtime |
| **Web Framework**| FastAPI | `0.115+` | Async REST API, OpenAPI docs, dependency injection |
| **Database ORM** | SQLAlchemy / SQLModel | `2.0+` | Relational models and schema management |
| **Database** | SQLite / PostgreSQL | `3.45+` | ACID-compliant relational patient store |
| **Vector DB** | ChromaDB | `0.5+` | Persistent cosine distance vector indexing |
| **Embeddings** | OnnxRuntime / Ollama | Latest | Dense bi-encoder sentence representations |
| **PDF Extraction**| PyMuPDF (fitz) | `1.24+` | High-speed layout-preserving text & bbox extraction |
| **Security** | PyJWT & Passlib (Bcrypt) | `2.10+` | Token authentication and password hashing |
| **Testing** | Pytest & HTTPX | `8.0+` | Automated regression test suites |

---

## 📁 Repository Structure

```
chromaNexus/
├── backend/                       # FastAPI Backend Application
│   ├── app/
│   │   ├── main.py                # FastAPI entry point, CORS, lifespan startup
│   │   ├── core/                  # Configuration, database engine, JWT security
│   │   ├── models/                # SQLAlchemy relational entity models
│   │   ├── schemas/               # Pydantic validation schemas
│   │   ├── routers/               # Modular REST endpoints (auth, patients, vault, chat)
│   │   ├── services/              # Ingestion, FHIR export, seeder, audit services
│   │   └── ai/                    # Hybrid symbolic-neural verification pipeline
│   ├── tests/                     # Automated backend unit & integration tests
│   └── requirements.txt           # Python backend dependencies
├── src/                           # React + TypeScript Frontend Application
│   ├── components/                # Modular UI widgets, charts, and layout components
│   ├── pages/                     # Application routes (Dashboard, Vault, Timeline, Chat)
│   ├── services/                  # Axios HTTP client, API connectors
│   ├── hooks/                     # Custom React hooks (auth, query, responsive layout)
│   ├── types/                     # TypeScript clinical interfaces and API schemas
│   └── index.css                  # TailwindCSS clinical theme and glassmorphism tokens
├── docs/                          # Project Documentation & Master Deliverables
│   ├── ChronaNexus_Capstone_Project_Report.pdf  # 98-Page Official Capstone Thesis
│   ├── ChronaNexus_Capstone_Project_Report.md   # Full Thesis Text in Markdown
│   ├── Capstone_Weekly_Diary.txt                # 26-Week Capstone Logbook
│   ├── user-guide/                # User Manual, Troubleshooting, & Setup Guides
│   ├── deployment/                # Production Deployment, Backup, & Rollback Guides
│   └── open-source-analysis/      # Open-Source Clinical Alignment Matrices
├── report_v2/                     # Master LaTeX Source for Capstone Project Report
│   ├── main.tex                   # XeLaTeX master document (98 pages)
│   ├── frontmatter/               # Official VIT-AP frontmatter (Title, Cert, Ack, Dec)
│   ├── chapters/                  # Chapters 1 to 11 + Team Biodata with portraits
│   └── figures/                   # System architecture diagrams, UML charts, logos
├── research/                      # Academic Research & Conference Publications
│   └── IEEE_PUBLICATION_FINAL/    # Primary Camera-Ready IEEE Conference Manuscript
│       ├── manuscript_modified2/  # Final 8-Page Camera-Ready Source (Lowest AI content)
│       │   ├── IEEE_PAPER1_FINAL.pdf # Compiled IEEE 8-Page PDF
│       │   ├── IEEE_PAPER1_FINAL.tex # Master IEEEtran LaTeX source
│       │   └── references.bib        # BibTeX bibliography
│       ├── manuscript/            # Promoted primary publication mirror
│       ├── frozen/                # Frozen empirical benchmark prediction datasets
│       └── audits/                # Compliance and statistical validity audits
├── data/                          # Persistent Local Data Stores
│   └── chroma_db/                 # Active persistent ChromaDB vector store
├── uploads/                       # Secure directory for uploaded clinical PDF records
├── gateway.py                     # High-performance Unified Reverse Proxy (Port 3000)
├── start_tunnel_service.py        # 1-Click production launcher (Backend + Frontend + Cloudflare)
├── start_local.py                 # Local offline runner (Backend + Frontend)
├── chronanexus.db                 # Seeded SQLite database with clinical demo data
└── package.json                   # Frontend npm package manifest
```

---

## 🎓 Academic Deliverables & Research Publication

### 1. Capstone Project Report (98 Pages)
* **Location**: [`docs/ChronaNexus_Capstone_Project_Report.pdf`](docs/ChronaNexus_Capstone_Project_Report.pdf)
* **Master Source**: [`report_v2/main.tex`](report_v2/main.tex)
* **Affiliation**: School of Computer Science and Engineering (SCOPE), VIT-AP University.
* **Layout**: Complete phase-by-phase engineering thesis comprising UML diagrams (Activity, Class, Component, State Machine), implementation details, test pyramid metrics, and framed student biodatas.

### 2. Camera-Ready IEEE Research Paper (8 Pages)
* **Title**: *ChronaNexus: Clinical Claim Verification over Longitudinal Electronic Health Records via Asymmetric Hybrid Symbolic-Neural Inference, and a Study on Benchmark Leakage*
* **Location**: [`research/IEEE_PUBLICATION_FINAL/manuscript_modified2/IEEE_PAPER1_FINAL.pdf`](research/IEEE_PUBLICATION_FINAL/manuscript_modified2/IEEE_PAPER1_FINAL.pdf)
* **Authors**: Ritesh Ranjan Panda, K Siddharth Pattnaik, Ashutosh Dash, Ayush Rakesh Meshram, and Dr. Sambhudutta Nanda.
* **Key Findings**: Demonstrates 86.00% overall verification accuracy on a 500-claim longitudinal benchmark, proves the trade-off of neural bi-encoders on treatment recall vs specificity, and presents a rigorous analysis of surface-cue lexical leakage in synthetic clinical testbeds.

---

## 🚀 Quickstart & Installation Guide

### 1. Prerequisites
* **Operating System**: Windows 10/11, macOS, or Ubuntu 22.04+
* **Python**: `3.11` to `3.13` (Ensure `python` is added to your PATH)
* **Node.js**: `v18.0.0` or higher (`v20+` LTS recommended)
* **npm**: `v9.0.0` or higher
* *(Optional)* **Ollama**: For local offline neural inference (`ollama pull llama3.2:3b` and `ollama pull all-minilm`)

---

### Option A: One-Click Full-Stack + Cloudflare Tunnel (Recommended)

To launch the backend, frontend, gateway, and a live public Cloudflare tunnel with a single command:

```powershell
python start_tunnel_service.py
```

* Automatically binds FastAPI to `http://127.0.0.1:8000`.
* Launches Vite on `http://127.0.0.1:5173`.
* Activates the Unified Gateway on `http://127.0.0.1:3000`.
* Establishes a zero-trust tunnel and writes the live public URL to `TUNNEL_PUBLIC_URL.txt`.

---

### Option B: Manual Development Setup

#### Step 1: Backend Setup
```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a Python virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt pymupdf

# 4. Start the FastAPI server (Runs on port 8000)
uvicorn app.main:app --reload --port 8000
```

#### Step 2: Frontend Setup (In a separate terminal at project root)
```bash
# 1. Install frontend packages
npm install

# 2. Start Vite development server (Runs on port 5173)
npm run dev
```

#### Step 3: Access the Platform
* **Web UI**: [http://localhost:5173](http://localhost:5173)
* **Unified Gateway**: [http://localhost:3000](http://localhost:3000)
* **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🔑 Default Demonstration Accounts

The database comes pre-seeded with longitudinal clinical test cases:

| Role | Email | Password | Clinical Trajectory Profile |
| :--- | :--- | :--- | :--- |
| **Patient (Primary)** | `alex.vance@example.com` | `Password123!` | Type 2 Diabetes, Hypertension, Multi-Year Lab Panels & Prescriptions |
| **Physician / Clinician** | `doctor.smith@example.com` | `DoctorPass123!` | Provider access for executive clinical summaries & timeline audits |

---

## 🧪 Automated Testing & Release Gates

ChronaNexus enforces automated testing across all architecture tiers:

```bash
# Run backend pytest suite (unit, integration, and security gates)
pytest backend/tests/ -v

# Run frontend TypeScript type verification & production build
npm run build

# Run Oxlint static code analysis
npm run lint
```

### Verified Release Gates:
* ✅ **100% Pass Rate** across 33 critical backend unit, benchmark, and regression test suites.
* ✅ **IDOR Protection & Path Traversal Mitigations** verified against adversarial requests.
* ✅ **Zero Cross-Patient Leakage**: Vector queries strictly isolated by `patient_id` metadata filtering.
* ✅ **Missing-OCR Resilience**: Graceful fallbacks when ingesting noisy or unreadable clinical scans.

---

## 🛡️ Security, Privacy & Compliance

* **Local-First Processing**: Patient data and vector embeddings reside on local disk (`chronanexus.db`, `data/chroma_db/`), preventing unconsented third-party cloud sharing.
* **Role-Based Access Control (RBAC)**: Enforces distinct scopes between patients, attending physicians, and administrative audit roles.
* **Audit Trail Sanitization**: All API access, search queries, and document downloads are recorded in structured audit logs with masked PII.
* **Two-Phase Cryptographic Patient Purge**: Complies with GDPR/HIPAA "Right to be Forgotten" via complete relational deletion and vector tombstoning.

---

## 👥 Project Team & Faculty Guidance

### Capstone Project Team
* **Ritesh Ranjan Panda** — `23BCB7045` *(Computer Science & Business Systems)*
* **K Siddharth Pattnaik** — `23BCB7018` *(Computer Science & Business Systems)*
* **Ashutosh Dash** — `23BCB7106` *(Computer Science & Business Systems)*
* **Ayush Rakesh Meshram** — `23BCB7111` *(Computer Science & Business Systems)*

### Faculty Supervisor & Guide
* **Dr. Sambhudutta Nanda**  
  Associate Professor, School of Electronics Engineering (SENSE)  
  *VIT-AP University, Amaravati, Andhra Pradesh, India*

### Departmental Leadership
* **Dr. Anil V. Turukmane**, Professor & HoD, Department of Networking and Security
* **Dr. S. Sudhakar Ilango**, Dean, School of Computer Science and Engineering (SCOPE)
* **Dr. Saroj Kumar Panigrahy**, Associate Dean, School of Computer Science and Engineering (SCOPE)

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.  
*Academic and research components are governed by standard academic attribution guidelines.*
