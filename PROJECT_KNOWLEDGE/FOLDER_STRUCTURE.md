# Complete Folder Structure & File Inventory — ChronaNexus

## 1. Directory Tree Overview

```
chromaNexus/
├── .gitignore                                # Git ignore configuration
├── .oxlintrc.json                            # Oxlint fast linter configuration
├── Capstone_Weekly_Diary.txt                 # Capstone academic weekly progress log
├── ChronaNexus_Open_Source_Alignment.docx   # Academic alignment dossier
├── README.md                                 # Main project documentation and setup guide
├── capstone.pdf                              # Capstone project report / specification
├── chronanexus.db                            # Root SQLite development database (authoritative)
├── test_chronanexus.db                       # Auxiliary test database artifact
├── index.html                                # Frontend HTML5 entry point
├── package.json                              # Node.js dependencies, scripts, and build metadata
├── package-lock.json                         # Exact locked npm dependency tree
├── tsconfig.json                             # Base TypeScript project reference config
├── tsconfig.app.json                         # Application-specific TypeScript config
├── tsconfig.node.json                        # Node/Vite-specific TypeScript config
├── vite.config.ts                            # Vite build tool and plugin configuration
│
├── backend/                                  # FastAPI Python backend application
│   ├── alembic.ini                           # Alembic database migration configuration
│   ├── chronanexus.db                        # Secondary backend local SQLite database
│   ├── requirements.txt                      # Python dependencies manifest
│   ├── alembic/                              # Alembic migration environment
│   │   ├── env.py                            # Migration runner and SQLAlchemy metadata loader
│   │   ├── script.py.mako                    # Migration file generation template
│   │   └── versions/                         # Sequential database migration scripts
│   │       ├── 001_initial_schema.py         # Initial database tables
│   │       ├── 002_add_document_chunks.py    # Document chunks table
│   │       ├── 003_add_provenance_and_allergies.py # Structured allergies and provenance
│   │       └── 004_add_checksum_and_page_metadata.py # SHA-256 deduplication and page count
│   ├── app/                                  # Core application package
│   │   ├── __init__.py                       # Package marker
│   │   ├── main.py                           # FastAPI application entry point and lifespan
│   │   ├── core/                             # Foundational runtime configuration
│   │   │   ├── config.py                     # Pydantic BaseSettings, env resolution, constants
│   │   │   ├── database.py                   # SQLAlchemy engine, session maker, DB protection
│   │   │   └── security.py                   # Password hashing, JWT token generation/validation
│   │   ├── models/                           # SQLAlchemy relational ORM models
│   │   │   ├── __init__.py                   # Model registry and re-exports
│   │   │   ├── user.py                       # User account model (auth, role)
│   │   │   ├── patient.py                    # Patient demographic and clinical baseline model
│   │   │   ├── report.py                     # Medical report metadata and document text
│   │   │   ├── document_chunk.py             # Ingested text chunks with embedding references
│   │   │   ├── clinical_entity.py            # LabResult, Medication, Disease, ExtractedEntity
│   │   │   ├── allergy.py                    # Structured patient allergy and severity model
│   │   │   ├── timeline.py                   # Longitudinal timeline events
│   │   │   ├── chat.py                       # ChatConversation, ChatMessage, Citations
│   │   │   └── summary.py                    # DoctorSummary cached digest model
│   │   ├── schemas/                          # Pydantic v2 validation and serialization schemas
│   │   │   ├── __init__.py                   # Schema re-exports
│   │   │   ├── user.py                       # User request/response schemas
│   │   │   ├── patient.py                    # Patient demographic, clinical, and lab trend schemas
│   │   │   ├── report.py                     # MedicalReport upload and detail schemas
│   │   │   ├── timeline.py                   # TimelineEvent and filter schemas
│   │   │   ├── chat.py                       # Message, conversation, and trend schemas
│   │   │   ├── summary.py                    # Doctor summary response schemas
│   │   │   └── search.py                     # Global multi-entity search schemas
│   │   ├── routers/                          # FastAPI REST API route endpoints
│   │   │   ├── __init__.py                   # Router collection and prefix definitions
│   │   │   ├── auth.py                       # /auth (login, signup, password reset)
│   │   │   ├── users.py                      # /users (profile, preferences)
│   │   │   ├── patients.py                   # /patients (demographics, diagnoses, meds, labs)
│   │   │   ├── reports.py                    # /reports (report CRUD, download, inspect)
│   │   │   ├── documents.py                  # /documents (PDF upload, deduplication, OCR worker)
│   │   │   ├── timeline.py                   # /timeline (chronological events, facilities, filters)
│   │   │   ├── chat.py                       # /chat (conversations, messages, grounded RAG)
│   │   │   ├── summaries.py                  # /summaries (physician summary generation, share links)
│   │   │   └── search.py                     # /search (unified multi-entity query)
│   │   ├── services/                         # Business logic and coordination services
│   │   │   ├── auth_service.py               # Authentication, credentials verification, tokens
│   │   │   ├── chat_service.py               # Conversational workflow, thread state, RAG execution
│   │   │   ├── seed_data.py                  # Initial demo patient profile (Alex Vance) seeding
│   │   │   ├── storage_service.py            # Local disk filesystem document storage manager
│   │   │   └── summary_service.py            # Clinical summary compilation and formatting
│   │   ├── clinical/                         # Domain-specific clinical reasoning modules
│   │   │   ├── terminology/                  # Standardized clinical ontology catalogs
│   │   │   │   ├── biomarkers.py             # Curated LOINC outpatient catalog (~150 biomarkers)
│   │   │   │   └── allergies.py              # Drug class definitions & cross-reactivity engine
│   │   │   ├── structured_query/             # Phase 5 temporal and longitudinal query engine
│   │   │   │   ├── models.py                 # Structured query types, trends, time windows
│   │   │   │   ├── detector.py               # Query intent and analyte resolution detector
│   │   │   │   └── engine.py                 # Parameterized SQL query executor and comparator
│   │   │   └── verification/                 # Phase 6 evidence grounding and claim verification
│   │   │       ├── models.py                 # Clinical claims, verification statuses, evidence
│   │   │       ├── claim_extractor.py        # Atomic clinical statement and analyte extractor
│   │   │       ├── evidence_verifier.py      # Multi-source patient record verifier
│   │   │       ├── answer_corrector.py       # Attribution correction, caveat synthesis, abstention
│   │   │       ├── citation_validator.py     # Dangling citation elimination and purification
│   │   │       └── pipeline.py               # Unified evidence grounding coordination pipeline
│   │   └── ai/                               # NLP, RAG, and document ingestion subsystem
│   │       ├── chunker.py                    # Clinical boundary & atomic table-aware chunker
│   │       ├── embeddings.py                 # Sentence-transformers BGE-small dense embeddings
│   │       ├── retrieval.py                  # ChromaDB, PostgresVectorStore, in-memory vector stores
│   │       ├── document_ingestion.py         # Full-document extraction orchestrator
│   │       ├── extractors/                   # Document format text extractors
│   │       │   ├── pdf_extractor.py          # PyMuPDF vector table detection & aligned parsing
│   │       │   └── ocr_extractor.py          # Scanned image OCR extractor (Tesseract wrapper)
│   │       ├── clinical_extractor/           # Clinical entity extraction workers
│   │       │   └── llm_extractor.py          # Page-by-page LLM and rule-based entity extractor
│   │       ├── ingestion/                    # Ingestion pipeline orchestration
│   │       │   └── orchestrator.py           # DocumentIngestionOrchestrator coordination
│   │       ├── llm/                          # Large Language Model abstraction providers
│   │       │   ├── ollama_provider.py        # Local Ollama client (llama3.2:3b)
│   │       │   ├── mock_provider.py          # Deterministic offline test mock provider
│   │       │   └── base.py                   # BaseLLMProvider interface
│   │       └── rag/                          # Retrieval-Augmented Generation subsystem
│   │           ├── pipeline.py               # Main RAGPipeline coordinator
│   │           ├── hybrid_retriever.py       # Dense ChromaDB + Lexical BM25 retriever
│   │           ├── bm25_retriever.py         # In-memory BM25 Okapi lexical retriever
│   │           ├── structured_retriever.py   # Direct SQL clinical entity retriever
│   │           ├── fusion.py                 # Reciprocal Rank Fusion (RRF) rank merger
│   │           ├── reranker.py               # Cross-encoder / heuristic result reranker
│   │           ├── classifier.py             # Clinical query intent classifier
│   │           └── query_resolver.py         # Multi-turn contextual query resolver
│   └── tests/                                # Backend automated pytest suite (190+ tests)
│       ├── conftest.py                       # Pytest fixtures, test database setup, mock engines
│       ├── test_allergy_and_provenance.py    # Structured allergy and LOINC terminology tests
│       ├── test_answer_sanitizer.py          # Clinical answer sanitization tests
│       ├── test_auth.py                      # Authentication, signup, and login endpoint tests
│       ├── test_chat.py                      # Conversational chat router tests
│       ├── test_chromadb_integration.py      # Persistent ChromaDB vector integration tests
│       ├── test_chromadb_sync.py             # SQL-to-Chroma reconciliation tests
│       ├── test_chunker.py                   # Boundary and table row chunking tests
│       ├── test_clinical_entity_extractor.py # Regex and LLM clinical entity extraction tests
│       ├── test_clinical_validator.py        # Clinical assertion validation tests
│       ├── test_context_builder.py           # RAG prompt context builder tests
│       ├── test_database_protection.py       # Engine-level production database mutation guards
│       ├── test_documents_api.py             # Document upload, preview, and delete API tests
│       ├── test_document_chunk_model.py      # DocumentChunk ORM model tests
│       ├── test_document_ingestion.py        # End-to-end ingestion and parsing tests
│       ├── test_document_processor.py        # Document preprocessing tests
│       ├── test_embeddings.py                # BGE dense and hash embedding tests
│       ├── test_evidence_grounding.py        # Phase 6 evidence grounding and citation tests (17 tests)
│       ├── test_hybrid_retriever.py          # Dense + BM25 fusion retrieval tests
│       ├── test_ingestion_orchestrator.py    # DocumentIngestionOrchestrator unit tests
│       ├── test_llm_providers.py             # Ollama and mock LLM provider tests
│       ├── test_new_report_retrieval.py      # New report priority retrieval tests
│       ├── test_ocr_providers.py             # OCR ingestion tests
│       ├── test_patient_memory.py            # Patient state graph merge tests
│       ├── test_pdf_extractor.py             # PyMuPDF table and multi-page tests
│       ├── test_phase3_ingestion.py          # Phase 3 deduplication and table row tests (10 tests)
│       ├── test_phase4_hybrid_retrieval.py   # Phase 4 BGE + BM25 + RRF tests
│       ├── test_postgres_vector_store.py     # Vector store backend tests
│       ├── test_query_classifier.py          # Query classifier taxonomy tests
│       ├── test_query_resolver.py            # Contextual query resolution tests
│       ├── test_rag_evaluation.py            # Retrieval-Augmented Generation evaluation
│       ├── test_rag_pipeline.py              # Core RAG pipeline execution tests
│       ├── test_reports.py                   # Medical report router and service tests
│       ├── test_reranker.py                  # Reranking score tests
│       ├── test_result_fusion.py             # RRF rank combination tests
│       ├── test_retrieval.py                 # Vector similarity search tests
│       ├── test_search.py                    # Global search router tests
│       ├── test_structured_queries.py        # Phase 5 temporal trend queries (14 tests)
│       ├── test_structured_retriever.py      # SQL structured entity retrieval tests
│       ├── test_summaries.py                 # Doctor summary compilation tests
│       ├── test_timeline.py                  # Timeline event aggregation tests
│       └── test_timeline_and_lab_trends.py   # Phase 5/7 timeline and lab trends API (14 tests)
│
├── src/                                      # React 19 + TypeScript frontend application
│   ├── App.css                               # Root application CSS utilities
│   ├── App.tsx                               # Application root component with QueryClient
│   ├── index.css                             # Tailwind CSS v4 setup, design tokens, @custom-variant
│   ├── main.tsx                              # React DOM root entry point with ThemeProvider
│   ├── app/                                  # App-level provider wrappers
│   │   └── providers.tsx                     # QueryClientProvider and Context wrappers
│   ├── assets/                               # Static images and icons
│   │   ├── hero.png                          # Landing page hero visual
│   │   ├── react.svg                         # React framework logo
│   │   └── vite.svg                          # Vite build tool logo
│   ├── components/                           # Reusable UI component library
│   │   ├── cards/                            # Specialized domain card components
│   │   │   ├── ChatBubble.tsx                # Chat dialogue bubble with reasoning and trends
│   │   │   ├── ClinicalTrendCard.tsx         # Phase 5 metric tiles, badges, and conflict alerts
│   │   │   ├── MedicalCard.tsx               # General medical entity display card
│   │   │   ├── ReportCard.tsx                # Document card with OCR confidence & inspect
│   │   │   ├── SummaryCard.tsx               # Doctor summary section card
│   │   │   └── TimelineCard.tsx              # Chronological milestone encounter card
│   │   ├── charts/                           # Data visualization charts
│   │   │   ├── ClinicalTrendChart.tsx        # Phase 5/7 Recharts temporal biomarker trend line
│   │   │   └── VitalsTrendChart.tsx          # Dashboard sample longitudinal biomarker area chart
│   │   ├── dialogs/                          # Modal dialog overlays
│   │   │   ├── GlobalSearchModal.tsx         # Command-K global search dialog across entities
│   │   │   └── UploadModal.tsx               # Drag-and-drop clinical document uploader
│   │   ├── layout/                           # Screen framing and navigation chrome
│   │   │   ├── AuthLayout.tsx                # Two-pane authentication layout with theme toggle
│   │   │   ├── Breadcrumb.tsx                # Hierarchical navigation breadcrumb bar
│   │   │   ├── DashboardLayout.tsx           # Main workspace layout with responsive drawer
│   │   │   ├── LandingLayout.tsx             # Public landing page container
│   │   │   ├── Sidebar.tsx                   # Collapsible desktop sidebar & mobile drawer
│   │   │   └── TopBar.tsx                    # Header with search, quick actions, theme picker
│   │   └── ui/                               # Primitives inspired by Apple design system
│   │       ├── Accordion.tsx                 # Collapsible disclosure panels
│   │       ├── Avatar.tsx                    # User and patient avatar indicator
│   │       ├── Badge.tsx                     # Status, category, and security indicator badges
│   │       ├── Button.tsx                    # Primary, secondary, outline, and ghost buttons
│   │       ├── Card.tsx                      # Base inset container with card header/body
│   │       ├── EmptyState.tsx                # Friendly zero-data illustration state
│   │       ├── ErrorState.tsx                # Non-blocking error alert banner
│   │       ├── Input.tsx                     # Accessible text input with show/hide password
│   │       ├── Loading.tsx                   # Pulse and spinner indicators
│   │       ├── Modal.tsx                     # Accessible dialog modal primitive
│   │       ├── Search.tsx                    # Search bar with clear button
│   │       ├── Skeleton.tsx                  # Shimmer loading skeleton placeholders
│   │       ├── Table.tsx                     # Dense clinical tabular data container
│   │       ├── Tabs.tsx                      # Category and view switcher tabs
│   │       └── Toast.tsx                     # Animated notification toast alerts
│   ├── constants/                            # Static constants and fallback data
│   │   └── mockData.ts                       # Rich demo dataset (Alex Vance profile, reports, labs)
│   ├── contexts/                             # Global application state management
│   │   ├── AuthContext.tsx                   # Authentication session, login, signup, logout
│   │   ├── ThemeContext.tsx                  # Light / Dark / System mode state management
│   │   ├── UIContext.tsx                     # Sidebar open, search modal, upload modal, toasts
│   │   └── UserContext.tsx                   # Current authenticated patient demographic state
│   ├── pages/                                # Screen views mapped to application routes
│   │   ├── Auth/                             # Authentication views
│   │   │   ├── ForgotPasswordPage.tsx        # Password recovery email request
│   │   │   ├── LoginPage.tsx                 # User sign-in with remember me & demo autofill
│   │   │   ├── OTPVerificationPage.tsx       # Two-factor verification code entry
│   │   │   └── SignupPage.tsx                # Patient / Clinician account registration
│   │   ├── Chat/                             # AI Clinical Assistant
│   │   │   └── AIChatPage.tsx                # 3-pane clinical workspace with contextual memory
│   │   ├── Dashboard/                        # Patient home overview
│   │   │   └── DashboardPage.tsx             # Apple Health inset card, vitals, active regimens
│   │   ├── DoctorSummary/                    # Physician consultation digest
│   │   │   └── DoctorSummaryPage.tsx         # Structured report, sticky anchor bar, PDF export
│   │   ├── Landing/                          # Public marketing landing
│   │   │   └── LandingPage.tsx               # Product overview, capabilities, privacy pledge
│   │   ├── NotFound/                         # Error handling view
│   │   │   └── NotFoundPage.tsx              # Clean 404 route fallback
│   │   ├── Profile/                          # Patient profile management
│   │   │   └── ProfilePage.tsx               # Personal demographics, emergency contacts
│   │   ├── Reports/                          # Document inspection view
│   │   │   └── ReportsPage.tsx               # Clinical document gallery and entity view
│   │   ├── Settings/                         # User preferences and privacy
│   │   │   └── SettingsPage.tsx              # Account settings, data export, theme, notifications
│   │   ├── Timeline/                         # Longitudinal health milestones
│   │   │   └── TimelinePage.tsx              # Interactive year scrubber, filters, event cards
│   │   └── Vault/                            # Document storage and security
│   │       └── VaultPage.tsx                 # Document grid/table, indexed storage volume
│   ├── routes/                               # Route definitions and access control
│   │   ├── AppRoutes.tsx                     # Central React Router route configuration
│   │   └── ProtectedRoute.tsx                # Authentication gate redirecting unauthenticated users
│   ├── services/                             # API communication abstraction services
│   │   ├── axios.ts                          # Configured Axios instance with interceptors
│   │   ├── auth.service.ts                   # Login, signup, token storage, logout API calls
│   │   ├── chat.service.ts                   # Conversation threads, message delivery, offline fallback
│   │   ├── patient.service.ts                # Patient profile, diagnoses, medications, lab trends
│   │   ├── report.service.ts                 # Document fetch, deletion, entity inspection API
│   │   ├── search.service.ts                 # Global search query API
│   │   ├── summary.service.ts                # Doctor summary compilation and share token API
│   │   ├── timeline.service.ts               # Timeline events, facilities, and filter API
│   │   └── index.ts                          # Services unified re-export
│   ├── types/                                # TypeScript interface definitions
│   │   ├── chat.ts                           # ChatMessage, Citation, StructuredTrendData
│   │   ├── disease.ts                        # Disease, DiagnosisStatus
│   │   ├── labResult.ts                      # LabResult, LabStatus, LabCategory
│   │   ├── medication.ts                     # Medication, MedicationStatus
│   │   ├── notification.ts                   # In-app notification structure
│   │   ├── patient.ts                        # Patient, EmergencyContact, InsuranceProvider
│   │   ├── report.ts                         # MedicalReport, ReportCategory, ProcessingStatus
│   │   ├── summary.ts                        # DoctorSummary data model
│   │   ├── timeline.ts                       # TimelineEvent, TimelineFilter
│   │   ├── user.ts                           # User, UserRole
│   │   └── index.ts                          # Types unified re-export
│   └── utils/                                # Utility helper functions
│       └── cn.ts                             # Tailwind class merger using clsx + tailwind-merge
│
├── tests/                                    # System benchmarks and evaluation harnesses
│   ├── backend_regression_results.xml        # JUnit XML output of test executions
│   └── benchmarks/                           # Automated benchmarks and comparative experiments
│       ├── baseline_results.json             # Baseline retrieval benchmark run data
│       ├── experiment_chroma_bge.py          # BGE + ChromaDB vs. SQLite Hash comparative harness
│       ├── experiment_comparison_results.json # Comparative experimental results
│       ├── exp_synthetic.db                  # Ephemeral database for comparative benchmark
│       ├── retrieval_benchmark.py            # 12-scenario synthetic clinical benchmark harness
│       ├── strengthened_retrieval_results.json # Hard-negative retrieval benchmark results
│       ├── synthetic_benchmark.db            # Ephemeral database for synthetic benchmark
│       ├── test_adversarial_grounding.py     # 10-case adversarial citation grounding tests
│       ├── test_chat_service_ollama.py       # Live Ollama chat service integration tests
│       ├── test_citation_grounding_audit.py  # 14-scenario citation grounding audit tests
│       ├── test_http_chat_ollama.py          # End-to-end FastAPI TestClient chat endpoint tests
│       ├── test_migration_003_disposable.py  # Disposable SQLite Alembic 003 migration verification
│       ├── test_ollama_provider_verification.py # Direct Ollama provider connection and latency tests
│       └── test_strengthened_retrieval_eval.py # Precision/Recall evaluation with hard negatives
│
├── data/                                     # Runtime persistent data storage
│   ├── chroma/                               # Legacy ChromaDB directory
│   └── chroma_db/                            # Production ChromaDB persistence directory
│       └── chroma.sqlite3                    # ChromaDB metadata and collection index
│
├── docs/                                     # Architectural documentation and audit archives
│   ├── Capstone_Weekly_Diary.txt             # Academic milestone tracker
│   ├── DEVELOPMENT_MEMORY.md                 # Master historical engineering journal (2,220+ lines)
│   ├── audit/                                # Audit archives and evidence reports
│   │   └── phase4_acceptance_20261018_2330/  # 18 formal acceptance audit reports
│   └── open-source-analysis/                 # Evaluation of 14 reference repositories
│       ├── 01_CURRENT_STATE_AUDIT.md
│       ├── 02_REPOSITORY_DEEP_ANALYSIS.md
│       ├── 03_FUNCTION_ALIGNMENT_MATRIX.md
│       ├── 04_INTEGRATION_OPTIONS.md
│       ├── 05_TARGET_ARCHITECTURE.md
│       ├── 06_IMPLEMENTATION_ROADMAP.md
│       ├── 07_DECISION_REGISTER.md
│       ├── 08_OPEN_SOURCE_LICENSE_REGISTER.md
│       ├── 09_EXECUTIVE_SUMMARY.md
│       └── PHASE_1_RETRIEVAL_DIAGNOSTIC.md
│
└── open-source-references/                   # Cloned reference repositories (for architecture comparison)
```
