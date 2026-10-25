# System Architecture — ChronaNexus

## 1. High-Level Architectural Paradigm

ChronaNexus is built as a **privacy-first, dual-channel clinical intelligence architecture**. It deliberately separates:
1. **Deterministic Structured Data Processing**: Relational SQL tables for patients, diagnoses, medications, laboratory measurements, allergies, and timeline encounters.
2. **Dense & Lexical Vector RAG**: ChromaDB dense vector embeddings (`bge-small-en-v1.5`) combined with BM25 Okapi lexical ranking and Reciprocal Rank Fusion (RRF) for unstructured clinical prose and document passages.
3. **Claim-Level Evidence Grounding**: An in-tree validation layer that decomposes generated answers into atomic assertions and verifies every factual statement against authoritative patient records before returning to the user.

```mermaid
graph TD
    User([Authenticated Patient / Clinician]) <-->|HTTPS / REST| Frontend[React 19 + TypeScript SPA]
    
    subgraph Frontend Subsystem
        Router[AppRoutes & ProtectedRoute]
        Pages[Dashboard / Vault / Timeline / Chat / DoctorSummary]
        Contexts[AuthContext, UserContext, ThemeContext, UIContext]
        APIClient[Axios Client with Bearer Interceptor]
    end
    
    Frontend <-->|JSON / Multipart| Backend[FastAPI Backend Application]
    
    subgraph Backend Subsystem
        Routers[FastAPI Routers: auth, patients, documents, chat, timeline, summaries]
        Lifespan[Lifespan Startup & Table Seeding]
        CoreConfig[Core Config & Database Protection Guards]
        
        subgraph Ingestion Pipeline
            PDFExtractor[PyMuPDF Multi-Page & Vector Table Extractor]
            Chunker[Clinical Boundary & Table-Aware Chunker]
            EntityExtractor[LLM & Regex Clinical Extractor]
            Deduplicator[Dual-Scope SHA-256 Deduplicator]
        end
        
        subgraph Dual-Channel Retrieval
            IntentDetector[Structured Query Detector]
            SQLQueryEngine[Structured Clinical Query Engine]
            HybridRetriever[Hybrid Retriever: Dense ChromaDB + Lexical BM25]
            Fusion[Reciprocal Rank Fusion - RRF k=60]
        end
        
        subgraph Reasoning & Verification
            LLMProvider[Ollama llama3.2:3b / Deterministic Mock]
            GroundingPipeline[Evidence Grounding & Citation Verifier]
            AnswerCorrector[Answer-Evidence Reconciler & Corrector]
        end
    end
    
    subgraph Storage & Persistence
        SQLite[(SQLite / PostgreSQL: chronanexus.db)]
        ChromaStore[(Persistent ChromaDB: data/chroma_db)]
        DiskStore[Local File System: uploads/]
    end
    
    PDFExtractor --> DiskStore
    Chunker --> SQLite
    Chunker --> ChromaStore
    EntityExtractor --> SQLite
    
    SQLQueryEngine <--> SQLite
    HybridRetriever <--> ChromaStore
    HybridRetriever <--> SQLite
    
    Backend <-->|HTTP localhost:11434| Ollama[Local Ollama SLM Daemon]
```

---

## 2. Ingestion & Document Processing Pipeline (System 1 & 2)

When a document is uploaded through `POST /api/v1/documents/upload`, the application executes a complete multi-stage pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor Client as Frontend (UploadModal)
    participant Router as documents.py
    participant Dedupe as SHA-256 Deduplicator
    participant Storage as storage_service.py
    participant Extractor as pdf_extractor.py
    participant Chunker as chunker.py
    participant Embeddings as embeddings.py
    participant Chroma as retrieval.py (ChromaDB)
    participant DB as SQLite / PostgreSQL
    
    Client->>Router: POST /api/v1/documents/upload (Multipart PDF)
    Router->>Dedupe: Calculate file binary SHA-256 checksum
    alt Checksum exists in DB and on_duplicate != 'return_existing'
        Router-->>Client: HTTP 409 Conflict (Duplicate Document)
    else Unique Document
        Router->>Storage: Persist file to uploads/{uuid}_{filename}
        Router->>DB: Create MedicalReport (status="processing")
        Router->>Extractor: extract_document(filepath)
        Note over Extractor: PyMuPDF find_tables()<br/>Whitespace EHR table format<br/>Page-level block sorting
        Extractor-->>Router: full_text, tables, page_metadata, content_checksum
        Router->>Chunker: chunk_document(full_text, pages)
        Note over Chunker: Atomic table row protection<br/>Table header continuation repetition<br/>Clinical section boundary tags
        Chunker-->>Router: chunks (metadata with source_page_number)
        Router->>Embeddings: embed_texts(chunk_texts)
        Embeddings-->>Router: dense vectors (384-dim BGE)
        Router->>Chroma: add_documents(vectors, metadata, patient_id)
        Router->>DB: Store DocumentChunk records & ExtractedEntity
        Router->>DB: Update MedicalReport (status="completed", page_count, checksum)
        Router-->>Client: HTTP 201 Created (MedicalReportSchema)
    end
```

---

## 3. Dual-Channel Clinical Retrieval & Evidence Grounding (System 5)

When a query is submitted through `POST /api/v1/chat/conversations/{id}/messages`, the system routes between structured SQL aggregation and hybrid RAG:

```mermaid
flowchart TD
    Q[User Clinical Query] --> Classifier[Clinical Query Classifier & Detector]
    
    Classifier -->|Structured Query Intent: latest, previous vs latest, time-window trend| StructBranch[Phase 5: Structured Clinical Query Engine]
    Classifier -->|Narrative Question, Diagnosis, Medication Question| HybridBranch[Phase 4: Hybrid RAG Pipeline]
    
    subgraph Structured Branch
        StructBranch --> AnalyteMatch[LOINC Catalog & Synonym Matching]
        AnalyteMatch --> ParamSQL[Parameterized SQL on lab_results table]
        ParamSQL --> OrderFilter[Chronological Sorting & Window Filtering]
        OrderFilter --> UnitCheck{Unit Mismatch?}
        UnitCheck -->|Yes| BlockComp[Block Math Comparison & Flag Warning]
        UnitCheck -->|No| CalcTrend[Calculate Delta, % Change, Trend Direction]
        CalcTrend --> ConflictCheck{Multi-Facility Conflict?}
        ConflictCheck -->|Yes| AlertConflict[Attach Multi-Facility Conflict Warning]
        ConflictCheck -->|No| NarrativeGen[Generate Non-Diagnostic Structured Narrative]
        BlockComp --> TrendData[StructuredTrendData Payload]
        AlertConflict --> TrendData
        NarrativeGen --> TrendData
    end
    
    subgraph Hybrid Branch
        HybridBranch --> ChromaDense[ChromaDB Dense Vector Search: Top 15]
        HybridBranch --> BM25Lex[BM25 Okapi Lexical Search: Top 15]
        ChromaDense --> RRF[Reciprocal Rank Fusion k=60]
        BM25Lex --> RRF
        RRF --> ContextBuilder[RAG Context Builder: Token Window & Citations]
        ContextBuilder --> OllamaGen[Ollama llama3.2:3b Answer Generation]
    end
    
    TrendData --> GroundingPipeline[Phase 6: Evidence Grounding & Verification Pipeline]
    OllamaGen --> GroundingPipeline
    
    subgraph Phase 6 Verification Subsystem
        GroundingPipeline --> ClaimDecomp[Atomic Clinical Claim Extractor]
        ClaimDecomp --> Verifier[Patient-Scoped Evidence Verifier]
        Verifier --> Reconciler[Answer Corrector & Attribution Reconciler]
        Reconciler --> CiteValidator[Citation Purifier: Remove False Collisions]
    end
    
    CiteValidator --> FinalResponse[Verified ChatMessage with Citations & Trends]
    FinalResponse --> Client([Frontend ChatBubble Display])
```

---

## 4. Key Subsystem Interfaces & Protocols

| Subsystem | Primary Interface File | Input Protocol | Output Protocol | Persistence Target |
|---|---|---|---|---|
| **REST API** | `backend/app/main.py` | HTTP/1.1 JSON, Multipart Form | JSON Pydantic Schemas | SQLite / PostgreSQL |
| **Document Storage** | `backend/app/services/storage_service.py` | Raw Byte Stream | UUID-prefixed file on disk | `uploads/` |
| **Relational DB** | `backend/app/core/database.py` | SQLAlchemy ORM Sessions | Python Models / Row Tuples | `chronanexus.db` |
| **Vector DB** | `backend/app/ai/retrieval.py` | 384-dim Floats + Metadata Dict | Ranked Document Chunks | `data/chroma_db/` |
| **Local LLM** | `backend/app/ai/llm/ollama_provider.py` | Prompt Strings via HTTP POST | Streamed / Chunked Text | `http://localhost:11434` |
| **Dense Embedder** | `backend/app/ai/embeddings.py` | Normalized Text Strings | L2-normalized 384-dim Arrays | In-memory BGE model |
| **Frontend State** | `src/contexts/` & `src/services/` | Axios HTTP JSON payloads | React Component State & Hooks | Browser localStorage |
