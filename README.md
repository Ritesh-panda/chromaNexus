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

The frontend foundation of ChronaNexus is engineered with modern, enterprise-grade web tools:

| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **React** | `19.2.8` | Core UI Framework |
| **TypeScript** | `~6.0.2` | Type Safety & Strict Verification (`verbatimModuleSyntax`) |
| **Vite** | `^8.2.0` | Ultra-fast build tool & Dev Server |
| **TailwindCSS** | `^4.3.3` | Utility-First Styling Engine with `@tailwindcss/vite` |
| **React Router** | `^7.18.2` | Declarative Client-Side Routing & Protected Route Guards |
| **React Query** | `^5.101.4` | Asynchronous Data Fetching & Caching (`@tanstack/react-query`) |
| **Axios** | `^1.19.0` | HTTP Client Configuration |
| **React Hook Form** | `^7.85.0` | Performant Form Management |
| **Zod** | `^4.4.3` | Schema Validation |
| **Lucide Icons** | `^1.31.0` | Modern Medical & System Icon Set |
| **Framer Motion** | `^13.1.0` | Micro-animations, Transitions, & Modals |
| **Recharts** | `^3.10.1` | Interactive Lab Trends & Vitals Visualizations |
| **Shadcn UI Pattern** | Utility | Reusable Components with `clsx` & `tailwind-merge` (`cn.ts`) |

---

## UI Design Principles

* **Rich Glassmorphism Aesthetics**: Modern dark/light theme palette, HSL background tones (`#0B0F19`), translucent glass cards (`glass-card`), backdrop blur effects, and subtle borders.
* **Privacy Indicators**: Prominent HIPAA compliance badges, isolated vault tags, and local processing status toggles.
* **Accessibility**: ARIA role attributes, keyboard shortcut support (`Cmd + K` search trigger), focus rings, and high contrast text ratios.
* **Responsive Dashboard Layout**: Dynamic sidebar shell with collapsible states, mobile drawer backdrop, top navigation bar, and breadcrumb tracking.

---

## Routing Structure

```
/                            ──► Public Landing Page (Vision, Architecture Showcase, Features)
/login                       ──► Auth: Login Form
/signup                      ──► Auth: Registration Form
/forgot-password             ──► Auth: Password Recovery
/otp-verification            ──► Auth: Two-Factor / OTP Verification
├── [ProtectedRoute Guard]
│   ├── /dashboard           ──► Main Command Center (Vitals, Active Memory, Recent Events)
│   ├── /vault               ──► Document Vault (Grid/List View, Filter, Upload Trigger)
│   ├── /reports             ──► Data Table View of Extracted Clinical Reports
│   ├── /timeline            ──► Interactive Longitudinal Health History Timeline
│   ├── /chat                ──► AI Assistant (Natural Language Q&A with Report Citations)
│   ├── /doctor-summary      ──► One-Click Physician Summary Generator & PDF Exporter
│   ├── /profile             ──► Patient Health Profile (Vitals, Emergency Contacts, Allergies)
│   └── /settings            ──► Account & Privacy Preferences (Data Isolation, Theme)
└── /not-found               ──► Custom 404 Route Fallback
```

---

## Component Architecture

```
src/
├── app/
│   └── providers.tsx         # QueryClientProvider, ThemeProvider, AuthProvider, UserProvider, UIProvider
├── components/
│   ├── cards/                # Domain-specific Cards (ChatBubble, MedicalCard, ReportCard, SummaryCard, TimelineCard)
│   ├── charts/               # Recharts Components (VitalsTrendChart)
│   ├── dialogs/              # Modals (GlobalSearchModal [Cmd+K], UploadModal)
│   ├── layout/               # Shell Layouts (LandingLayout, AuthLayout, DashboardLayout, Sidebar, TopBar, Breadcrumb)
│   └── ui/                   # Reusable UI Primitives (Button, Card, Badge, Input, Modal, Search, Table, Tabs, Toast, Avatar, Skeleton, Loading, EmptyState, ErrorState, Accordion)
├── constants/
│   └── mockData.ts           # Comprehensive Mock Data (Patient, Reports, Diseases, Medications, Timeline, AI Chat)
├── contexts/
│   ├── AuthContext.tsx       # Auth state management
│   ├── ThemeContext.tsx      # Dark/Light/System theme provider
│   ├── UIContext.tsx         # Modals, Toast notifications, and Sidebar toggle state
│   └── UserContext.tsx       # Active patient memory state
├── pages/                    # 11 Application Screen Components
├── routes/                   # AppRoutes router & ProtectedRoute guard
├── services/                 # Service layer modules (auth, report, timeline, summary, chat, axios)
├── types/                    # TypeScript Type Definitions
└── utils/                    # Utility functions (cn.ts)
```

---

## Application Screens

1. **Landing Page (`/`)**: Product showcase highlighting the problem, 6 core systems, microservice pipeline, and interactive platform preview.
2. **Login & Registration (`/login`, `/signup`)**: Secure authentication forms with role selection (`Patient` / `Doctor`) and HIPAA isolation assurances.
3. **Password Recovery & OTP (`/forgot-password`, `/otp-verification`)**: Multi-step identity verification flow.
4. **Dashboard Page (`/dashboard`)**: Primary health portal showing vital trends (HbA1c, Glucose, Cholesterol), active chronic conditions, upcoming reminders, timeline snippet, and quick AI Q&A launcher.
5. **Medical Vault (`/vault`)**: Ingestion hub supporting grid/list views, category filtering (Blood Reports, MRI, Prescriptions, CT, X-Ray), instant search, and upload modal triggers.
6. **Reports Page (`/reports`)**: Structured tabular list of all processed clinical documents with entity confidence scores, parsed metadata, and report view modals.
7. **Timeline Page (`/timeline`)**: Filterable longitudinal event line detailing diagnoses, treatments, lab tests, surgeries, and physician visits from 2019 to 2026.
8. **AI Assistant (`/chat`)**: Conversational interface enabling natural language queries over uploaded patient history, complete with auditable report citations and reasoning badges.
9. **Doctor Summary Page (`/doctor-summary`)**: One-click summary generator producing structured executive notes (Active/Past Diseases, Current Medications, Allergies, Risk Factors, Abnormal Labs) formatted for clinical consultation.
10. **Profile Page (`/profile`)**: Comprehensive patient record detailing blood group, height, weight, primary care physician, emergency contact, insurance details, and allergen list.
11. **Settings Page (`/settings`)**: Theme customization (Light/Dark/System), notification preferences, data isolation toggles, and security audit logs.

---

## Current Progress & Milestones

> [!NOTE]
> **Current Repository Scope**: This repository currently contains the complete **Frontend Architectural Foundation** (UI, Layouts, Screens, Design System, Mock Services, State Contexts, and Client Routing).

### Implementation Status:
* ✅ **Frontend Foundation**: 100% Implemented & Verified (Clean TypeScript Build, Zero Lint Errors).
* ⏳ **Backend Microservices**: Planned for Milestone 2 (Auth Service, Document Storage, Metadata DB).
* ⏳ **AI & OCR Pipeline**: Planned for Milestone 3 (OCR Service, Clinical Entity Extractor, Embedding Generator, Vector Search).
* ⏳ **Local LLM Engine**: Planned for Milestone 4 (Privacy-first local LLM integration & Patient Memory Graph Sync).

---

## Getting Started

### Prerequisites
* **Node.js**: `v18.0.0` or higher
* **npm**: `v9.0.0` or higher

### Installation

```bash
# Clone the repository
git clone https://github.com/codingashutosh441-eng/chromaNexus.git

# Navigate into the project directory
cd chromaNexus

# Install dependencies
npm install
```

### Development Server

```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser to view the application.

### Production Build & Linting

```bash
# Execute TypeScript verification & Vite production build
npm run build

# Execute Oxlint code quality verification
npm run lint

# Preview production build locally
npm run preview
```

---

## Future Roadmap (Reference: `capstone.pdf`)

* **Phase 1 (MVP Foundation)**: User authentication, Document Vault upload, Clinical Entity Extraction, Patient Memory construction, Timeline view, AI Q&A, and Doctor Summary generator (Current Milestone).
* **Phase 2 (Microservices Architecture)**: Ingestion, OCR, Medical Extraction, Memory Graph, Timeline, Search, AI Q&A, and Notification microservices.
* **Phase 3 (Privacy & Security)**: On-device local LLM execution, zero-knowledge encrypted vault storage, and audit logs.
* **Phase 4 (Ecosystem Expansion)**: Family account monitoring, wearable integration (Apple Health, Fitbit), and multi-language support.

---

## License & Credits

* **Project**: ChronaNexus Capstone Project
* **Lead Engineer / Architect**: Senior Frontend Architecture Review
* **License**: MIT License

---
