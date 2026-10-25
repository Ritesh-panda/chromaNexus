# ChronaNexus Forensic Audit Dossier ? Complete System Architecture

**Document ID:** `03_COMPLETE_SYSTEM_ARCHITECTURE.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  

---

## 1. End-to-End System Architecture Trace

The following diagram represents the actual execution flow traced across the codebase:

```mermaid
graph TD
    subgraph Client ["Frontend Client (React 19 SPA)"]
        UI[User Interface / React Router]
        SC[Axios Service Clients]
        MF[Mock Data Fallback on Error]
        UI -->|User Action| SC
        SC -.->|Catch Network Error| MF
    end

    subgraph API ["API & Security Gateway (FastAPI)"]
        GW[Uvicorn / FastAPI app]
        AUTH[JWT Auth Middleware & Dependency]
        ROUTERS[FastAPI Routers: documents, chat, reports, patients]
        SC -->|HTTP Bearer JWT| GW
        GW --> AUTH
        AUTH --> ROUTERS
    end

    subgraph Ingestion ["Phase 3 Ingestion Pipeline"]
        UP[Upload Endpoint /documents/upload]
        DEDUP[SHA-256 Checksum Deduplication]
        ORCH[DocumentIngestionOrchestrator]
        PEXT[PDFExtractor: PyMuPDF Block & Table Parser]
        CHK[DocumentChunker: Clinical Boundary-Aware]
        CEXT[ClinicalEntityExtractor: LLM / Regex]
        VAL[ClinicalDataValidator: Range & Unit Normalizer]
        
        ROUTERS -->|File Stream| UP
        UP --> DEDUP
        DEDUP -->|Unique File| ORCH
        DEDUP -.->|Duplicate File| CONFLICT[409 Conflict Response]
        ORCH --> PEXT
        PEXT --> CHK
        PEXT --> CEXT
        CEXT --> VAL
    end

    subgraph Persistence ["Relational & Vector Storage"]
        DB[(SQLAlchemy SQLite / Postgres)]
        VEC[(Vector Store: SQLite Scan / pgvector)]
        ORCH -->|Store Reports, Entities, Labs| DB
        CHK -->|Store Document Chunks| DB
        CHK -->|Embed Chunks & Index| VEC
    end

    subgraph RAG ["AI Retrieval & Assistant Pipeline"]
        CHAT[Chat Endpoint /chat/conversations]
        RESOLV[ConversationQueryResolver]
        CLASS[QueryIntentClassifier]
        SRET[StructuredRetriever: SQL Lab & Med Query]
        VRET[VectorRetriever: Top-K Chunk Scan]
        FUSE[ResultFusion: Priority Balanced Fusion]
        RERANK[ClinicalReranker: Heuristic Recency & Intent]
        CTX[RAGContextBuilder: Verified Citations]
        LLM[LLM Provider: Ollama / Gemini / Mock]

        ROUTERS -->|Clinical Query| CHAT
        CHAT --> RESOLV
        RESOLV --> CLASS
        CLASS --> SRET
        CLASS --> VRET
        SRET --> FUSE
        VRET --> FUSE
        FUSE --> RERANK
        RERANK --> CTX
        CTX --> LLM
        LLM -->|Evidence-Grounded Answer| CHAT
    end
```

---

## 2. Ingestion & Extraction Architecture Trace

The document ingestion pipeline processes clinical PDFs from upload to relational and vector storage without arbitrary text truncation.

```mermaid
sequenceDiagram
    autonumber
    actor Patient as Patient / User
    participant Router as documents.py (/upload)
    participant Storage as StorageService (Local Disk)
    participant Orchestrator as DocumentIngestionOrchestrator
    participant Extractor as PDFExtractor (PyMuPDF)
    participant Chunker as DocumentChunker
    participant DB as SQLite / PostgreSQL
    participant VectorStore as VectorStore (SQLite / pgvector)

    Patient->>Router: POST /documents/upload (PDF File)
    Router->>Router: Compute SHA-256 Checksum
    Router->>DB: Query MedicalReport for existing checksum
    alt Duplicate Checksum Found
        Router-->>Patient: 409 Conflict (Duplicate Document Detected)
    else Unique Document
        Router->>Storage: Save file to vault directory
        Router->>DB: Insert MedicalReport (status="processing")
        Router-->>Patient: 201 Created (Upload Queued)
        Router->>Orchestrator: BackgroundTask.process_document()
    end

    Orchestrator->>Extractor: extract_document(file_bytes)
    Extractor->>Extractor: Detect vector tables via page.find_tables()
    Extractor->>Extractor: Extract text blocks sorted by layout (y0, x0)
    Extractor-->>Orchestrator: ExtractedDocument (Complete Text + Tables + BBoxes)
    
    Orchestrator->>Chunker: chunk_document(ExtractedDocument)
    Chunker->>Chunker: Detect clinical section boundaries (LABS, MEDS, PLAN)
    Chunker-->>Orchestrator: List of DocumentChunk (page numbers preserved)

    Orchestrator->>DB: Insert DocumentChunkModel records
    Orchestrator->>VectorStore: add_documents(DocumentChunks)
    Orchestrator->>DB: Update MedicalReport (status="completed", page_count=N)
```

---

## 3. Database Entity-Relationship Model (14 Tables)

```mermaid
erDiagram
    users ||--o{ patients : owns
    patients ||--o{ medical_reports : owns
    patients ||--o{ diseases : has
    patients ||--o{ medications : prescribed
    patients ||--o{ lab_results : has
    patients ||--o{ allergies : has
    patients ||--o{ timeline_events : records
    patients ||--o{ chat_conversations : engages
    patients ||--o{ doctor_summaries : generated_for

    medical_reports ||--o{ document_chunks : divided_into
    medical_reports ||--o{ extracted_entities : sources
    medical_reports ||--o{ lab_results : sources
    medical_reports ||--o{ medications : sources
    medical_reports ||--o{ diseases : sources
    medical_reports ||--o{ timeline_events : sources

    chat_conversations ||--o{ chat_messages : contains

    users {
        string id PK
        string email UK
        string hashed_password
        string role
        datetime created_at
    }

    patients {
        string id PK
        string user_id FK
        string first_name
        string last_name
        string date_of_birth
        string gender
        string blood_group
    }

    medical_reports {
        string id PK
        string patient_id FK
        string title
        string category
        string checksum
        string content_checksum
        integer page_count
        string status
        string storage_path
    }

    document_chunks {
        string id PK
        string document_id FK
        integer page_number
        integer chunk_index
        text text
        string section_type
        json metadata_json
    }

    allergies {
        string id PK
        string patient_id FK
        string allergen
        string reaction
        string severity
        string status
        string source_report_id FK
        integer source_page_number
    }

    lab_results {
        string id PK
        string patient_id FK
        string test_name
        string value
        string unit
        string reference_range
        string status
        string source_report_id FK
        integer source_page_number
    }
```

---

## 4. Patient Isolation Boundaries & Data Flow

```mermaid
graph LR
    subgraph Requests ["Incoming HTTP Requests"]
        Req1[Request Patient Alpha]
        Req2[Request Patient Beta]
    end

    subgraph AuthLayer ["Authentication Layer"]
        JWT1[Verify Token Alpha -> patient_id_alpha]
        JWT2[Verify Token Beta -> patient_id_beta]
        Req1 --> JWT1
        Req2 --> JWT2
    end

    subgraph DataIsolation ["Strict Isolation Filter in Code"]
        SQL1["WHERE patient_id == patient_id_alpha"]
        SQL2["WHERE patient_id == patient_id_beta"]
        VEC1["Filter: metadata['patient_id'] == alpha"]
        VEC2["Filter: metadata['patient_id'] == beta"]
        JWT1 --> SQL1
        JWT1 --> VEC1
        JWT2 --> SQL2
        JWT2 --> VEC2
    end

    subgraph StorageEngine ["Database & Vector Store"]
        DB[(Shared Relational DB)]
        VS[(Shared Vector Index)]
        SQL1 --> DB
        SQL2 --> DB
        VEC1 --> VS
        VEC2 --> VS
    end
```

---

## 5. Deployment and Runtime Dependencies

```mermaid
graph TD
    subgraph Host ["Local Host / Server Environment"]
        VITE[Node.js / Vite Dev Server :5173]
        FASTAPI[Python 3.13 / Uvicorn Server :8000]
        SQLITE[Local SQLite DB: chronanexus.db]
        STORAGE[Local Vault Storage: ./data/storage]
    end

    subgraph External ["Optional / External Services"]
        OLLAMA[Local Ollama Server :11434 - Optional]
        GEMINI[Google Gemini API - Optional]
        PG[PostgreSQL + pgvector - Optional]
    end

    VITE -->|Reverse Proxy / Direct CORS| FASTAPI
    FASTAPI --> SQLITE
    FASTAPI --> STORAGE
    FASTAPI -.->|If Configured| OLLAMA
    FASTAPI -.->|If Configured| GEMINI
    FASTAPI -.->|If Configured| PG
```

---

## 6. Error Handling & Fallback Paths

```mermaid
graph TD
    A[Incoming API Call] --> B{Service Healthy?}
    B -->|Yes| C[Execute Production Service Logic]
    B -->|No / Exception| D[Global Exception Handler]
    
    subgraph FrontendFallback ["Frontend Behavior (src/services)"]
        F1[API Request Fails] --> F2[Catch Block Intercepts]
        F2 --> F3[Return Hardcoded MOCK_DATA]
        F3 --> F4[UI Renders Green Mock State]
        F4 -.-> F5[DEFECT: User unaware backend is down]
    end

    subgraph BackendFallback ["Backend Behavior (backend/app)"]
        E1[LLM / Ollama Unreachable] --> E2[Fallback to MockDeterministicLLMProvider]
        E3[Tesseract OCR Missing] --> E4[Fallback to MockOCRProvider]
        E5[Ollama Embeddings Down] --> E6[Fallback to LocalLightweightEmbeddingProvider]
    end
```
