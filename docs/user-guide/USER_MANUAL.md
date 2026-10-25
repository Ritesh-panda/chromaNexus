# ChronaNexus — Complete User Manual

Welcome to the **ChronaNexus User Manual**. This document walks through every user-facing screen, workflow, and interactive capability in ChronaNexus (`v1.0.0-rc1`).

---

## 1. Product Introduction & Core Philosophy

### What is ChronaNexus?
ChronaNexus is a **Privacy-First Longitudinal Medical Intelligence Platform**. Unlike standard document vaults or cloud drives (e.g., Google Drive or Dropbox) that store medical records as passive, disconnected PDF files, ChronaNexus actively parses, understands, and connects health records into an evolving **Patient Memory Graph**.

```
Standard File Storage:
[Blood_Report.pdf] ── (Disconnected) ── [MRI_Scan.pdf] ── (Disconnected) ── [Prescription.pdf]

ChronaNexus Patient Memory Graph:
                      ┌─── Diseases & ICD Codes
                      ├─── Medications & Dosage Histories
                      ├─── Lab Trends & Biomarker Ranges
[Medical Documents] ──┼─── Multi-Hospital Timeline Events
                      ├─── Evidence-Grounded AI Chat
                      └─── Doctor-Ready 60-Second Summaries
```

### Key Conceptual Distinctions
To get the most out of ChronaNexus, understand how data flows through the platform:

1. **Source Medical Records**: The original raw PDF or text documents uploaded to the vault.
2. **Extracted Document Text**: High-fidelity text, layout blocks, and tables extracted via PyMuPDF or Tesseract OCR.
3. **Structured Clinical Entities**: Formal medical concepts extracted from documents and stored in relational tables:
   - **Diseases & Conditions**: Linked with ICD-10 diagnostic codes, diagnosis dates, and treating physicians.
   - **Medications**: Tracked with dosages, administration frequencies, routes, and start/stop dates.
   - **Lab Results**: Structured numerical values, units, reference ranges, and abnormal high/low flags.
4. **Retrieved Evidence**: Semantic chunks and keyword-indexed snippets retrieved dynamically when answering questions.
5. **Grounded AI Explanations**: Answers synthesized by local AI that include direct, clickable source citations back to specific reports.
6. **Doctor-Ready Summaries**: Formatted clinical briefings designed for a physician appointment.

> ⚖️ **Important Medical & Regulatory Notice**:  
> ChronaNexus is designed as a personal health organization and clinical decision-support tool. It does **not** provide independent medical diagnosis or replace consultation with a licensed physician. All testing should be performed using **synthetic, fictional patient data**.

---

## 2. Navigation & Interface Layout

Once logged in, ChronaNexus presents a clean, responsive medical interface:

- **Top Navigation Bar**:
  - **Global Search Bar**: Quick-search documents, lab results, and diagnoses.
  - **Quick Upload Button (`+ Upload Report`)**: Opens the document ingestion modal from any page.
  - **Theme Switcher**: Instant toggle between Light Mode and Dark Mode.
  - **User Profile Menu**: Displays active patient avatar, name, and sign-out button.
- **Sidebar Navigation**:
  - 📊 **Dashboard** (`/dashboard`): High-level overview of health records and recent activity.
  - 📁 **Medical Vault** (`/vault`): Central repository for viewing, searching, and managing files.
  - 📄 **Reports** (`/reports`): Direct document index view.
  - ⏳ **Timeline** (`/timeline`): Interactive chronological health milestone map and lab trend explorer.
  - 💬 **AI Assistant** (`/chat`): Evidence-grounded natural language Q&A.
  - 🩺 **Doctor Summary** (`/doctor-summary`): One-click appointment brief and question prep.
  - 👤 **Profile** (`/profile`): Demographics, primary care physician, and insurance details.
  - ⚙️ **Settings** (`/settings`): Theme, notifications, security, FHIR R4 export, audit logs, and data purge.

---

## 3. Detailed Feature Walkthrough

### 3.1 Authentication & Patient Access

#### Sign In (`/login`)
- **Accessing the Screen**: Navigate to `http://localhost:5173/login`.
- **Pre-Seeded Demo Account**:
  - **Email**: `alex.vance@example.com`
  - **Password**: `Password123!` (or `Demo123!`)
- **Form Fields**: Email address, Password, and "Remember Me" checkbox.
- **Security Guardrails**:
  - Invalid credentials display an explicit error alert: `"Invalid email or password."`
  - Successful authentication stores an encrypted JWT bearer token in your browser session (`localStorage`).
  - Passwords are never returned in API payloads or logged in audit events.

#### Sign Up (`/signup`)
- **Creating a New Account**: Enter full name, email, password, and select role (`Patient` or `Doctor`).
- **Automatic Patient Scoping**: When a new user registers, ChronaNexus automatically provisions a corresponding `Patient` record, ensuring strict multi-tenant isolation from day one.

#### Password Reset & OTP (`/forgot-password`, `/otp-verification`)
- Demonstration workflows for simulated email recovery and 6-digit OTP verification.

#### Sign Out
- Click the profile avatar in the upper right or sidebar and select **Sign Out**. The session token is cleared and you are redirected to the login screen.

---

### 3.2 Medical Document Vault (`/vault`)

The **Medical Vault** is the foundational repository for all your health records.

```
┌────────────────────────────────────────────────────────────────────────┐
│  📁 Medical Vault                           [ + Upload Document ]      │
├────────────────────────────────────────────────────────────────────────┤
│  🔍 Search documents...           Category: [All]   Facility: [All]    │
│  Sort By: [Clinical Date ▼]        Order: [Descending]                 │
├────────────────────────────────────────────────────────────────────────┤
│  [Blood Reports (3)]  [Prescriptions (2)]  [MRI/Imaging (1)]           │
├────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┐  ┌─────────────────────────┐              │
│  │ Comprehensive Panel     │  │ Knee MRI Diagnostic     │              │
│  │ Metro Health • 2024-03  │  │ St. Jude Hospital • 2023│              │
│  │ [View] [Download] [Del] │  │ [View] [Download] [Del] │              │
│  └─────────────────────────┘  └─────────────────────────┘              │
└────────────────────────────────────────────────────────────────────────┘
```

#### Uploading a Document
1. Click **`Upload Document`** (or use the top bar `+ Upload Report` button).
2. **Drag and Drop** a file or click to browse.
   - **Supported File Types**: Digital PDF (`.pdf`) and Plain Text (`.txt`).
   - **File Size**: Up to 50 MB.
3. Select the document **Category**:
   - `Blood Report` (CBC, Metabolic Panel, Lipid Panel, etc.)
   - `Prescription` (Outpatient physician orders)
   - `MRI / CT / Imaging` (Radiology impressions and reports)
   - `Discharge Summary` (Inpatient hospitalization records)
4. (Optional) Provide **Hospital/Facility Name**, **Attending Doctor**, and **Clinical Report Date**.
5. Click **`Upload & Process`**.

#### Ingestion Pipeline & Status Tracking
Once uploaded, ChronaNexus runs an asynchronous background ingestion pipeline:
1. `RECEIVED` (5%): Document binary saved and SHA-256 checksum calculated.
2. `PROCESSING` (15%): PDF layout parsed; PyMuPDF extracts text, columns, and tabular blocks.
3. `OCR_REQUIRED` (30%): If an image-only scanned PDF is detected, Tesseract OCR is triggered.
4. `EXTRACTING` (50%): Clinical entities (diseases, drugs, labs) extracted and linked.
5. `INDEXING` (80%): Text chunked into 500-character segments with 100-character overlap and indexed into ChromaDB.
6. `COMPLETED` (100%): Document is fully searchable, grounded, and ready for queries.

#### Duplicate Detection (409 Conflict)
If you attempt to upload a file that is byte-identical to a document already in your vault:
- ChronaNexus calculates the binary SHA-256 checksum.
- The server halts the upload and returns **HTTP 409 Conflict**.
- The UI displays an alert: `"Duplicate document detected. This exact file has already been uploaded for this patient."`
- This prevents duplicate clutter and skewed lab trend statistics.

#### Search, Filtering, and Sorting
- **Instant Search**: Type any query (e.g. `"Glucose"`, `"Dr. Jenkins"`, `"Knee"`, or `"Hypertension"`).
- **Category Filter**: Filter to view only Blood Reports, Prescriptions, Imaging, or Discharge Summaries.
- **Facility Filter**: Filter records by treating hospital or lab network.
- **Sort Controls**: Toggle between sorting by **Clinical Date** (when the test took place) vs **Upload Date** (when you added the file to ChronaNexus).

#### Document Inspection Modal
Clicking on any document card opens the comprehensive multi-tab inspector:
- **Overview Tab**: Shows file size, SHA-256 checksum, upload timestamp, clinical date, confidence score, and document status.
- **Extracted Text Tab**: Displays the exact text extracted from the file, broken down page-by-page.
- **Linked Clinical Records Tab**: Shows all diseases, medications, and lab results that the system automatically parsed from this specific document.
- **Raw Text Tab**: Displays complete raw text buffer.

---

### 3.3 Patient Longitudinal Timeline (`/timeline`)

The **Medical Timeline** solves the problem of disconnected paper dates by reconstructing a single, continuous narrative of your healthcare journey.

```
2024 ──● March 18: Comprehensive Metabolic Panel (Metro Health Diagnostic)
       │           HbA1c: 6.7% (Improved), Fasting Glucose: 118 mg/dL
       │           [View Source Report]
       │
2023 ──● November 04: Primary Care Consultation (Dr. Sarah Jenkins)
       │              Diagnosed: Essential Hypertension (ICD-10: I10)
       │              Prescribed: Lisinopril 10mg daily
       │
       ──● September 18: Endocrinology Initial Encounter
                         Diagnosed: Type 2 Diabetes Mellitus (ICD-10: E11.9)
```

#### Key Capabilities
- **Multi-Source Synthesis**: Automatically merges events from formal timeline entries, medical reports, disease diagnoses, new medication start dates, and significant lab tests.
- **Clinical Date vs Upload Date**: Events are plotted strictly according to the **clinical event date**, not when you uploaded the PDF months later.
- **Interactive Event Cards**: Each card displays event type, date, title, facility, treating physician, and connected entities.
- **Source Document Traceability**: Clicking **`View Source Report`** on any event opens the underlying vault document that established that medical fact.
- **Year & Type Filtering**: Quickly jump to specific years (e.g. `2024`, `2023`) or filter by event type (`Diagnostics`, `Encounters`, `Prescriptions`, `Surgeries`).

---

### 3.4 Biomarker Lab Trends & Visualization

Located within the **Timeline** screen and directly inside **AI Chat**, the **Biomarker Trends Engine** tracks your vital lab numbers over time.

```
Analyte: [ Fasting Plasma Glucose ▼ ]   Window: [ Past 1 Year ▼ ]

  140 ┬
      │              ● 132 mg/dL (High - 2023-09-18)
  120 ┼───────────────────────● 118 mg/dL (2024-03-18)
      │  Reference Range: 70 - 99 mg/dL
  100 ┴────────────────────────────────────────────────
      Delta: -14.0 mg/dL (-10.6% Improvement)
```

#### How to Use Lab Trends
1. On the Timeline page, scroll to the **Biomarker Lab Trends** panel.
2. Select an analyte from the dropdown (e.g., **Fasting Plasma Glucose**, **Hemoglobin A1c**, **Potassium**, or **Total Cholesterol**).
3. The interactive **Recharts** chart plots every historical measurement chronologically.
4. **Key Features to Inspect**:
   - **Reference Range Bands**: Shaded area indicating normal physiological boundaries.
   - **Abnormal Flags**: Markers clearly highlight `HIGH` or `LOW` measurements.
   - **Trend Delta**: Displays absolute and percentage change between earliest and latest tests (e.g. `HbA1c decreased by -0.6%`).
   - **Multi-Facility Reconciliation**: Seamlessly plots measurements taken at different hospitals, noting the facility source on each point.

---

### 3.5 AI Clinical Assistant (`/chat`)

The **AI Clinical Assistant** enables natural-language dialogue over your complete medical history with zero-hallucination guarantees.

```
User: What is my latest HbA1c reading and how has it changed?

ChronaNexus AI: [FACT]
Your latest Hemoglobin A1c is 6.7% recorded on March 18, 2024 at Metro Health Diagnostic [1].
This represents a decrease of 0.5% from your previous reading of 7.2% on September 18, 2023 [2],
indicating improved glycemic management.

Citations:
[1] Metro Health Diagnostic Lab Report • Page 1
[2] Endocrinology Progress Note • Page 2
```

#### How the Assistant Works
- **Evidence Grounding**: The assistant does not generate speculative advice. Every medical claim is verified against your retrieved vault chunks.
- **Reasoning Badges**:
  - `[FACT]`: Direct factual retrieval from your records.
  - `[INFERENCE]`: A logical deduction grounded in multiple verified findings.
  - `[COMPARISON]`: Longitudinal comparison between two or more historical dates.
- **Clickable Inline Citations**: Each claim is accompanied by bracketed citation chips (`[1]`, `[2]`). Clicking a citation chip highlights the exact report and page where that finding was documented.
- **Embedded Lab Trend Cards**: When asking about specific lab tests (e.g., *"Show my potassium trend"*), the assistant embeds an interactive trend chart directly inside the chat bubble!
- **Disclose Missing Evidence**: If you ask about a condition or test that does not exist in your records (e.g., *"What were my PSA prostate biopsy results?"*), the assistant will explicitly state:  
  `"Your medical records contain no documentation or evidence regarding PSA or prostate biopsy."`

---

### 3.6 Doctor-Ready Summary (`/doctor-summary`)

The **Doctor-Ready Summary** generates a structured, high-density clinical briefing designed to be reviewed by a physician in under 60 seconds.

#### Summary Sections
1. **Patient Overview & Demographics**: Name, Age, Gender, DOB, Blood Type, Primary Care Physician.
2. **Clinical Briefing**: High-level synthesis of primary diagnoses and current health status.
3. **Chronic & Active Conditions**: Listed with ICD-10 diagnostic codes, diagnosis dates, and source reports.
4. **Active & Past Medications**: Detailed table showing medication name, dosage, frequency, route, and prescribing physician.
5. **Abnormal Lab Results & Trends**: Consolidated view of all out-of-range lab markers with historical direction.
6. **Appointment Questions & Discussion Notes**: An interactive section where you can prepare questions for your doctor.

#### Appointment Question Builder
- Type a question in the input field (e.g., *"Can we discuss adjusting my Lisinopril dosage based on my normal BP readings?"*) and click **`Add Question`**.
- Reorder or delete questions as needed.
- Click **`Save Questions`** to persist them directly to your clinical profile.

#### Export and Sharing
- **Print / Save as PDF**: Click the **`Print / Export PDF`** button to trigger the browser's native print engine. The page includes custom print stylesheets that strip navigation bars and format the briefing cleanly across standard Letter/A4 paper.
- **Physician Share Link**: Click **`Generate Physician Link`** to create a secure, unguessable share token.

---

### 3.7 Settings, Privacy & Governance (`/settings`)

The **Settings** page provides centralized management of user preferences, security controls, standard FHIR exports, audit logs, and data sovereignty.

```
┌────────────────────────────────────────────────────────────────────────┐
│  ⚙️ Settings                                                           │
│  [ Theme ]  [ Notifications ]  [ Security ]  [ Privacy ]  [ Danger ]   │
└────────────────────────────────────────────────────────────────────────┘
```

#### Tab 1: Theme & Appearance
- Choose between **Light Mode** (optimized for clinical contrast) and **Dark Mode** (eye-friendly OLED dark palette).

#### Tab 2: Notifications
- Configure alerts for critical lab results, document processing updates, and monthly summaries.

#### Tab 3: Security & 2FA
- Manage passwords and simulated two-factor authentication safeguards.

#### Tab 4: Privacy & FHIR R4 Export
- **Export HL7 FHIR R4 Bundle**:
  1. Click the **`Export FHIR R4 Bundle`** button.
  2. Your browser downloads a standardized `chronanexus_fhir_r4_bundle.json` file.
  3. The bundle structures your health data according to international HL7 standards:
     - `Bundle` (Collection container)
     - `Patient` (Demographics and identifiers)
     - `Observation` (Laboratory measurements with LOINC codes)
     - `Condition` (Diagnoses with ICD-10 codes)
     - `MedicationStatement` (Active and past drug regimens)
     - `DocumentReference` (Vault reports with checksum metadata)
- **Security Audit Trail**:
  - Displays a live table of all sensitive operations performed on your data.
  - Logs event timestamp, action type (`DOCUMENT_UPLOAD`, `SUMMARY_GENERATED`, `FHIR_EXPORT`, etc.), actor ID, and outcome (`SUCCESS` or `DENIED`).
  - **PHI Sanitization**: Audit logs strictly exclude raw medical narratives, passwords, and tokens.

#### Tab 5: Account Data & Purge (`Danger Zone`)
ChronaNexus provides an irrevocable, verifiable data purge mechanism in compliance with GDPR Right to Erasure:
1. Click **`Request Purge Preview`**.
2. A modal displays the exact scope of records scheduled for deletion (e.g., X documents, Y lab results, Z Chroma vector embeddings).
3. The server generates a short-lived **15-minute confirmation token**.
4. To confirm, you must manually type the confirmation phrase:  
   `DELETE MY CLINICAL MEMORY PERMANENTLY`
5. Click **`Confirm & Execute Permanent Purge`**.
6. The system permanently deletes your relational records, file binaries, and vector chunks in an atomic sequence. Other patients remain 100% untouched.

---

## 4. Feature Availability & Dependency Matrix

| Feature | Works Without Ollama? | Works Without Tesseract OCR? | Notes |
|---|---|---|---|
| **User Sign-In & Registration** | ✅ Yes | ✅ Yes | Fully offline, SQLite/PostgreSQL auth. |
| **Document Vault Upload (Text PDF)** | ✅ Yes | ✅ Yes | Uses native PyMuPDF vector text extraction. |
| **Document Vault Upload (Scanned PDF)** | ✅ Yes | ⚠️ Requires Tesseract | Safely reports `[OCR_FAILED]` if Tesseract is missing. |
| **Duplicate Document Rejection** | ✅ Yes | ✅ Yes | Uses binary SHA-256 checksums. |
| **Longitudinal Timeline** | ✅ Yes | ✅ Yes | Deterministic relational assembly. |
| **Biomarker Lab Trends** | ✅ Yes | ✅ Yes | Deterministic structured query engine. |
| **Doctor-Ready Summary** | ✅ Yes | ✅ Yes | Assembled from structured clinical entities. |
| **AI Assistant (Grounded Chat)** | ⚠️ Uses local fallback | ✅ Yes | Connects to local Ollama (`llama3.2:3b`); falls back to rule matcher if offline. |
| **HL7 FHIR R4 Export** | ✅ Yes | ✅ Yes | Pure JSON serialization. |
| **Security Audit Logs** | ✅ Yes | ✅ Yes | Relational logging. |
| **Safe Patient Purge** | ✅ Yes | ✅ Yes | Relational, file, and vector store deletion. |
