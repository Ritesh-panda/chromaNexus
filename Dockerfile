# Multi-stage Dockerfile for ChronaNexus Backend
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies (curl for healthchecks, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend source code and seed data
COPY backend ./backend

# Create runtime directories for uploads, SQLite, and ChromaDB
RUN mkdir -p /app/uploads /app/data/chroma_db

# Configure environment variables
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    UPLOAD_DIR=/app/uploads \
    CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db \
    DATABASE_URL=sqlite:////app/data/chronanexus.db

# Expose backend API port
EXPOSE 8000

# Health check using the liveness endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
