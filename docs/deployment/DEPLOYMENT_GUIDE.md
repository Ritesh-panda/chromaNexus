# ChronaNexus — Production Deployment & Operations Guide

## 1. System Architecture Overview

ChronaNexus is an on-premises, privacy-first clinical timeline, evidence grounding, and medical document intelligence platform designed to run in air-gapped or strictly controlled healthcare environments.

### Core Architecture Components
1. **Application Backend**:
   - Framework: FastAPI (Python 3.11–3.13) with ASGI server (Uvicorn).
   - Relational Database: SQLite (local file-based, WAL mode enabled) or PostgreSQL (via SQLAlchemy 2.0 async/sync engine).
   - Configuration & Security: Pydantic Settings with strict startup validation (`app.core.config`).
2. **Vector Database**:
   - Engine: ChromaDB (persistent local vector store in `data/chroma_db`).
   - Embedding Model: Local `sentence-transformers/all-MiniLM-L6-v2` running entirely on CPU/GPU without remote telemetry.
3. **Clinical Inference**:
   - Engine: Local Ollama daemon (`http://localhost:11434` or Docker service `http://ollama:11434`).
   - Default Behavior: Zero remote cloud calls. Offline inference fallback is enforced by default; external models cannot be used unless explicitly configured and opted into.
4. **Web Frontend**:
   - Framework: React 18, TypeScript, Tailwind CSS, Lucide icons, Vite build pipeline.
   - Delivery: Served via Nginx reverse proxy or static file host.

---

## 2. Configuration & Environment Variables

ChronaNexus validates all critical runtime settings at startup before binding network sockets. If an invalid or unresolvable configuration is detected (e.g. malformed JWT secret in production mode or unresolvable database path), startup fails immediately with an actionable error.

### Environment Variable Reference

| Variable | Default Value | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Runtime environment (`development`, `staging`, `production`). In `production`, default insecure keys are rejected. |
| `SECRET_KEY` | *(Placeholder in dev)* | Cryptographic HMAC secret for JWT session tokens. Must be >= 32 characters in production. |
| `ALGORITHM` | `HS256` | JWT signature algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime before refresh is required. |
| `DATABASE_URL` | `sqlite:///./chronanexus.db` | SQLAlchemy connection string. |
| `CHROMA_PERSIST_DIRECTORY` | `./data/chroma_db` | Persistent filesystem directory for ChromaDB vector embeddings. |
| `CHROMA_COLLECTION_NAME` | `chronanexus_clinical_chunks` | ChromaDB collection identifier. |
| `UPLOAD_DIR` | `./data/uploads` | Path for encrypted/isolated medical document storage. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Endpoint for local LLM inference daemon. |
| `OLLAMA_MODEL` | `llama3.2:3b` | Default clinical reasoning model tag. |
| `ALLOW_CLOUD_INFERENCE` | `false` | Strict safety gate. Cloud APIs are completely blocked when `false`. |
| `LOG_LEVEL` | `INFO` | Application log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `STRICT_SECURITY` | `false` (default) | When `true`, enforces production-grade header validation and cookie constraints. |

---

## 3. Local Development Deployment

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Node.js 18+ and npm
- Ollama installed locally (for clinical reasoning generation)

### Step 1: Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### Step 2: Frontend Setup
```bash
# Navigate to workspace root
cd ..

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

---

## 4. Production Containerized Deployment (Docker & Compose)

ChronaNexus includes a production multi-stage `Dockerfile` and a `docker-compose.yml` service definition.

### Directory Structure Requirements
Ensure the following directories exist with correct write permissions:
```bash
mkdir -p data/uploads data/chroma_db
```

### Starting the Services with Docker Compose
```bash
# Build and launch all services in detached mode
docker-compose up -d --build

# View operational logs
docker-compose logs -f backend
```

### Service Map in Compose
- `backend`: Exposes port `8000`. Mounts `./data/uploads` and `./data/chroma_db` as persistent host volumes.
- `ollama`: Exposes port `11434`. Runs local inference daemon with isolated model volume `ollama_models`.

---

## 5. Reverse Proxy Configuration (Nginx)

For clinical deployments, terminate SSL/TLS at a reverse proxy and enforce security headers.

### Sample Nginx Configuration Snippet
```nginx
server {
    listen 443 ssl http2;
    server_name clinical.local;

    ssl_certificate /etc/ssl/certs/chronanexus.crt;
    ssl_certificate_key /etc/ssl/private/chronanexus.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Maximum upload size for multi-page medical imaging/PDFs
    client_max_body_size 50M;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:;" always;

    # Frontend Static Assets
    location / {
        root /var/www/chronanexus/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API & WebSocket Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
    }

    # Health & Readiness Probes
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
    location /ready {
        proxy_pass http://127.0.0.1:8000/ready;
    }
}
```

---

## 6. Health & Readiness Monitoring

ChronaNexus implements separate liveness and readiness endpoints:

### Liveness Probe (`GET /health` or `GET /api/v1/health`)
- Returns `{"status": "healthy", "service": "chronanexus-backend", "version": "1.0.0-rc1"}` with HTTP 200.
- Purpose: Orchestrator (Docker/Kubernetes) liveness check to confirm process responsiveness.

### Readiness Probe (`GET /ready` or `GET /api/v1/ready`)
- Evaluates operational sub-systems:
  - **Relational Database**: Runs `SELECT 1` query via active session.
  - **Vector Store (ChromaDB)**: Validates persistent client heartbeat and collection availability.
  - **Upload Storage**: Verifies filesystem write accessibility.
  - **Inference Service**: Checks Ollama HTTP reachability.
- Returns HTTP 200 (`"status": "ready"`) if all critical systems are operational.
- Returns HTTP 503 (`"status": "degraded"` or `"unavailable"`) if a critical dependency is down.
