# ChronaNexus

> **AI-Powered Longitudinal Medical Intelligence Platform**
> 
> Transforming fragmented medical records into a structured, continuously evolving patient memory layer with privacy-first intelligence.

---

## Overview

**ChronaNexus** is an AI-powered longitudinal medical intelligence platform designed to bridge the gap between disconnected medical documents and holistic clinical understanding. Instead of functioning as a passive file repository or document storage application, ChronaNexus extracts clinical entities, connects health events chronologically, and maintains a continuously updating **Patient Memory Graph**.

Patients and healthcare professionals can interact with years of medical history through natural language, generate instant physician-ready summaries, search lab trends across time, and maintain complete data sovereignty through local-first privacy principles.

---

## Problem Statement

Healthcare data today is deeply fragmented across multiple providers, laboratories, and specialists:

* **Blood Reports** from one diagnostic laboratory.
* **MRI & CT Imaging** from different hospital networks.
* **Prescriptions & Consult Notes** from multiple independent doctors.
* **Discharge Summaries & Vaccination Records** stored in physical binders or email attachments.

None of these documents are connected. When a patient sees a new physician, they are forced to retell years of medical history from memory, hand over stacks of paper PDFs, or repeat expensive diagnostic tests. **ChronaNexus transforms these static PDF files into machine-understandable, connected patient memory.**

---

## Vision & Mission

### Product Vision
Instead of storing files, **ChronaNexus stores understanding.**

```
Traditional File Storage:
PDF ──► PDF ──► PDF ──► PDF (Disconnected Files)

ChronaNexus Patient Memory Graph:
Patient
  ├── Personal Info
  ├── Medical Reports & Vault Files
  ├── Diseases & Chronic Conditions
  ├── Medicines & Dosage Histories
  ├── Doctors & Hospital Contacts
  ├── Lab Results & Vitals Trends
  ├── Surgeries & Procedures
  ├── Allergies & Contraindications
  ├── Longitudinal Timeline
  ├── AI Conversations & Queries
  └── Doctor Executive Summaries
```

### Product Mission
Create a personal AI system capable of understanding an individual's complete medical journey while preserving strict data privacy through local intelligence and isolated patient memory architectures.

---

## Product Philosophy

| ChronaNexus IS NOT ❌ | ChronaNexus IS ✅ |
| :--- | :--- |
| Hospital Management Software (HMS) | Medical Intelligence Platform |
| Doctor Appointment Booking System | Longitudinal Patient Memory Layer |
| Telemedicine / Video Consultation Platform | AI Medical Assistant & Natural Language Q&A |
| Generic Symptom Checker / Medical Chatbot | Intelligent Medical Search Engine |
| Automated Disease Prediction System | Doctor Decision Support Tool |
| File Storage Provider (Google Drive for Health) | Automated Medical Timeline Generator |

---

## Core Systems (System Architecture)

ChronaNexus is structured around six core processing systems:

### 1. Document Vault (`System 1`)
* **Purpose**: Securely ingests and organizes all healthcare documents.
* **Supported Formats**: PDFs, High-Resolution Scans, Prescriptions, MRI/CT Summaries, Lab Reports, X-Rays.
* **Responsibilities**: Drag-and-drop upload, categorization, metadata indexing, search, and document preview.

### 2. Medical Understanding Engine (`System 2`)
* **Purpose**: Converts unstructured clinical text and images into structured medical data.
* **Extracted Entities**: Diseases (ICD codes), Medications (Dosage, Frequency, Route), Physicians, Hospitals, Lab Tests, Values, Dates.

### 3. Patient Memory Engine (`System 3`)
* **Purpose**: The core state graph of ChronaNexus.
* **Functionality**: Merges newly extracted clinical entities into a unified, living profile. Every document upload updates and enriches the patient memory graph automatically.

### 4. Medical Timeline Engine (`System 4`)
* **Purpose**: Automatically constructs an interactive chronological health history line.
* **Events**: Diagnoses, treatments, hospital visits, surgeries, lab tests, and recovery milestones.

### 5. Medical Intelligence Engine (`System 5`)
* **Purpose**: Natural language query engine operating over patient history.
* **Guarantees**: Evidence-grounded answers with direct citations to supporting vault reports, strict fact-vs-inference distinction, and zero medical hallucination.

### 6. Doctor Summary Engine (`System 6`)
* **Purpose**: Generates one-click physician executive summaries.
* **Outputs**: Concise 60-second summary covering active/past conditions, current medications, known allergies, abnormal lab trends, and key risk factors.

---

## Tech Stack

The full-stack platform of ChronaNexus is engineered with enterprise-grade web and API frameworks:

### Frontend
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **React** | `19.2.8` | Core UI Framework |
| **TypeScript** | `~6.0.2` | Type Safety & Strict Verification (`verbatimModuleSyntax`) |
| **Vite** | `^8.2.0` | Ultra-fast build tool & Dev Server |
| **TailwindCSS** | `^4.3.3` | Utility-First Styling Engine with `@tailwindcss/vite` |
| **React Router** | `^7.18.2` | Declarative Client-Side Routing & Protected Route Guards |
| **React Query** | `^5.101.4` | Asynchronous Data Fetching & Caching (`@tanstack/react-query`) |
| **Axios** | `^1.19.0` | Configured HTTP API Client with Bearer Tokens & Interceptors |
| **React Hook Form** | `^7.85.0` | Performant Form Management |
| **Zod** | `^4.4.3` | Schema Validation |
| **Lucide Icons** | `^1.31.0` | Modern Medical & System Icon Set |
| **Framer Motion** | `^13.1.0` | Micro-animations, Transitions, & Modals |
| **Recharts** | `^3.10.1` | Interactive Lab Trends & Vitals Visualizations |

### Backend
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **Python** | `3.13+` | Core Backend Runtime |
| **FastAPI** | `0.115+` | High-performance Async REST API Framework |
| **SQLAlchemy** | `2.0+` | Database ORM & Patient Memory Relational Models |
| **Alembic** | `1.14+` | Database Schema Migrations |
| **Pydantic** | `2.10+` | Request / Response Schema Validation & Serialization |
| **PyJWT & Bcrypt**| `2.10+` | JWT Authentication & Password Hashing |
| **Pytest** | `9.1+` | Automated Backend Unit & Integration Tests |

---

## Backend Architecture

```
backend/
├── app/
│   ├── main.py               # FastAPI entry point with CORS, lifespan DB init, & Swagger docs
│   ├── core/
│   │   ├── config.py         # Pydantic Settings & environment configuration
│   │   ├── database.py       # SQLAlchemy SessionLocal, engine, & Base
│   │   └── security.py       # Bcrypt password hashing & JWT token management
│   ├── models/               # SQLAlchemy Models:
│   │   ├── user.py           # User & authentication credentials
│   │   ├── patient.py        # Patient demographic, physician, & emergency contacts
│   │   ├── report.py         # Medical reports & extracted clinical entities
│   │   ├── disease.py        # Active & past diagnoses with ICD codes
│   │   ├── medication.py     # Active & completed prescriptions
│   │   ├── lab_result.py     # Lab values, reference ranges, & flags
│   │   ├── timeline.py       # Longitudinal timeline milestones
│   │   ├── chat.py           # Multi-turn chat conversations & citations
│   │   └── summary.py        # Clinical doctor summaries
│   ├── schemas/              # Pydantic v2 schemas (ConfigDict(from_attributes=True))
│   ├── routers/              # Modular API endpoints:
│   │   ├── auth.py           # /auth/signup, /auth/login, /auth/me, /auth/logout
│   │   ├── users.py          # /users/me
│   │   ├── patients.py       # /patients/me
│   │   ├── reports.py        # /reports (CRUD)
│   │   ├── documents.py      # /documents/upload, /documents/download
│   │   ├── timeline.py       # /timeline (Year/type filtering)
│   │   ├── chat.py           # /chat/conversations & /chat/conversations/{id}/messages
│   │   ├── summaries.py      # /summaries/latest & /summaries/generate
│   │   └── search.py         # /search?q={query}
│   └── services/             # Storage abstraction, clinical intent matcher, & seeders
├── alembic/                  # Database migration configuration & versions
├── tests/                    # 17 Automated pytest unit & integration tests
├── requirements.txt          # Python backend dependencies
└── .env.example              # Environment variable template
```

---

## Current Progress & Milestones

### Implementation Status:
* ✅ **Phase 1: Frontend Foundation**: 100% Implemented & Verified (Clean TypeScript Build, Zero Lint Errors).
* ✅ **Phase 2: Full-Stack Persistence Layer**: 100% Implemented & Verified (FastAPI, SQLite/PostgreSQL Models, 9 Routers, Storage Abstraction, 17 Pytest Tests PASS, Axios Integration).
* ⏳ **Phase 3: OCR Ingestion & Clinical NLP**: Automated Tesseract/Cloud Vision OCR pipeline and LLM extraction worker.
* ⏳ **Phase 4: Privacy-First Local RAG Engine**: Vector database embeddings & local LLM reasoning.

---

## Getting Started

### 1. Prerequisites
* **Node.js**: `v18.0.0` or higher
* **npm**: `v9.0.0` or higher
* **Python**: `3.10` or higher

### 2. Frontend Setup

```bash
# Navigate into the project directory
cd chromaNexus

# Install frontend dependencies
npm install

# Start Vite dev server (runs on http://localhost:5173)
npm run dev
```

### 3. Backend Setup

```bash
# Navigate into the backend directory
cd backend

# Create and activate virtual environment (optional)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Start FastAPI server (runs on http://localhost:8000)
uvicorn app.main:app --reload --port 8000
```

### 4. Interactive API Documentation
FastAPI automatically generates interactive Swagger and ReDoc documentation:
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc UI: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Running Automated Tests & Quality Checks

```bash
# Run backend pytest suite (17 comprehensive tests)
python -m pytest backend/tests -v

# Run frontend TypeScript type checking & production build
npm run build

# Run Oxlint code quality verification
npm run lint
```

---

## License & Credits

* **Project**: ChronaNexus Capstone Project
* **Lead Engineer / Architect**: Senior Full-Stack Architecture Review
* **License**: MIT License

