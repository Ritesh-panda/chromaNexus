# Dependencies & Configuration Guide — ChronaNexus

## 1. Runtime Requirements

| Component | Minimum Version | Verified Active Version | Notes |
|---|---|---|---|
| **Python** | `>= 3.10` | `3.13.7` (Windows 64-bit) | Standard CPython distribution |
| **Node.js** | `>= 18.0.0` | `v22.x` / `v20.x` | Required for building Vite client bundle |
| **npm** | `>= 9.0.0` | `10.x` | Standard package manager |
| **Hardware** | 8 GB RAM, 4 CPU cores | 16 GB RAM, AMD64 | Runs completely on consumer laptops without GPU |
| **Ollama** | Optional for testing | `llama3.2:3b` | Only needed for live generative AI responses |

---

## 2. Backend Python Dependencies (`backend/requirements.txt`)

```text
fastapi>=0.115.0          # High-performance async web framework
uvicorn[standard]>=0.30.0 # ASGI web server with uvloop/httptools
sqlalchemy>=2.0.30        # Modern 2.0 ORM and SQL toolkit
alembic>=1.13.0           # Database schema migrations
pydantic>=2.8.0           # Data validation and settings management
pydantic-settings>=2.4.0  # Environment variable parsing
pyjwt>=2.9.0              # JSON Web Token authentication
passlib[bcrypt]>=1.7.4    # Password hashing and verification
python-multipart>=0.0.9   # Multipart file upload parsing
pytest>=8.0.0             # Automated test framework
httpx>=0.27.0             # Async HTTP client for Ollama and TestClient
python-dotenv>=1.0.1      # .env configuration loader
pgvector>=0.2.0           # PostgreSQL pgvector extension support
psycopg[binary]>=3.1.0    # PostgreSQL modern database driver
PyMuPDF>=1.24.0           # Complete multi-page PDF & vector table extraction
chromadb>=0.5.0           # Local vector database
sentence-transformers>=3.0.0 # Dense neural embedding generation (BGE)
```

---

## 3. Frontend Node Dependencies (`package.json`)

### Core Runtime Dependencies
- `react` (`^19.2.8`), `react-dom` (`^19.2.8`): React 19 UI library.
- `react-router-dom` (`^7.18.2`): Declarative client-side routing.
- `axios` (`^1.19.0`): Promise-based HTTP client for backend REST communication.
- `@tanstack/react-query` (`^5.101.4`): Server-state synchronization, caching, and background refetching.
- `recharts` (`^3.10.1`): Declarative charting library for clinical biomarkers and longitudinal trajectories.
- `framer-motion` (`^13.1.0`): Fluid micro-animations and layout transitions.
- `lucide-react` (`^1.31.0`): Standardized healthcare and UI iconography.
- `clsx` (`^2.1.1`), `tailwind-merge` (`^3.6.0`), `class-variance-authority` (`^0.7.1`): Dynamic utility class synthesis.
- `react-hook-form` (`^7.85.0`), `zod` (`^4.4.3`), `@hookform/resolvers` (`^5.7.1`): Type-safe form validation.

### Development Dependencies
- `vite` (`^8.2.0`), `@vitejs/plugin-react` (`^6.0.4`): Fast ESM bundler and HMR dev server.
- `tailwindcss` (`^4.3.3`), `@tailwindcss/vite` (`^4.3.3`): Tailwind CSS v4 engine.
- `typescript` (`~6.0.2`): Static typing and compilation.
- `oxlint` (`^1.75.0`): Rust-based ultra-fast JavaScript/TypeScript linter.

---

## 4. Environment Variables & Configuration (`backend/app/core/config.py`)

All configuration is managed through Pydantic `BaseSettings` reading from environment variables or `.env` file at the project root.

| Variable Name | Default Value | Description | Sensitivity |
|---|---|---|---|
| `PROJECT_NAME` | `"ChronaNexus"` | Application display name | Public |
| `VERSION` | `"1.0.0"` | API semantic version | Public |
| `API_V1_STR` | `"/api/v1"` | REST API base route prefix | Public |
| `SECRET_KEY` | *Generated / Configured* | Cryptographic key for JWT tokens | **Confidential / Redacted** |
| `ALGORITHM` | `"HS256"` | JWT token hashing algorithm | Standard |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60 * 24 * 7` (7 days) | JWT session validity duration | Configurable |
| `DATABASE_URL` | `"sqlite:///./chronanexus.db"` | SQLAlchemy connection string | Local / Secure |
| `POSTGRES_SERVER` | `"localhost"` | PostgreSQL host (when using Postgres) | Configurable |
| `POSTGRES_PORT` | `5432` | PostgreSQL port | Configurable |
| `POSTGRES_DB` | `"chronanexus"` | PostgreSQL database name | Configurable |
| `POSTGRES_USER` | `"postgres"` | PostgreSQL username | Configurable |
| `POSTGRES_PASSWORD` | `""` | PostgreSQL password | **Confidential / Redacted** |
| `CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:3000", "http://localhost:4173"]` | Allowed CORS origins for web client | Security Rule |
| `UPLOAD_DIR` | `"./uploads"` | Directory for stored documents | Local Storage |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum single-file upload size cap | Operational |
| `CHROMA_PERSIST_DIRECTORY` | `"./data/chroma_db"` | Vector database persistent directory | Storage |
| `CHROMA_COLLECTION_NAME` | `"chronanexus_clinical_chunks"` | Active vector collection identifier | Architecture |
| `EMBEDDING_MODEL_NAME` | `"BAAI/bge-small-en-v1.5"` | Dense embedding model name | NLP Model |
| `EMBEDDING_DIMENSION` | `384` | Embedding dimensionality | Architecture |
| `OLLAMA_BASE_URL` | `"http://localhost:11434"` | Local Ollama SLM HTTP endpoint | Network |
| `OLLAMA_MODEL` | `"llama3.2:3b"` | Active Ollama model identifier | AI Model |
| `OLLAMA_TIMEOUT_SECONDS` | `90.0` | Max wait time for CPU text generation | Operational |
| `CHRONANEXUS_TEST_ENV` | `""` (Set to `"1"` during tests) | Test isolation flag blocking DB writes | Safety Guard |

---

## 5. Security & Secret Handling Rules

1. **No Hardcoded Secrets**: Secrets must never be committed to Git. The `.gitignore` file explicitly excludes `.env`, `*.db`, `uploads/`, `node_modules/`, and `venv/`.
2. **Database Write Interceptor in Test Mode**: When `PYTEST_CURRENT_TEST` or `CHRONANEXUS_TEST_ENV=1` is active, the engine execution listener in `backend/app/core/database.py` blocks any `INSERT`, `UPDATE`, or `DELETE` targeting `chronanexus.db`.
