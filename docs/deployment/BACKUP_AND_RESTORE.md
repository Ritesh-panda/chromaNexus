# ChronaNexus — Backup, Restore, and Consistency Guide

## 1. Dual-Store State Architecture

ChronaNexus maintains state across three complementary persistence layers:
1. **Relational Database (`chronanexus.db`)**:
   - Contains structured clinical entities: Patients, Encounters, LabResults, Medications, Diagnoses, TimelineEvents, DoctorSummaries, AuditLogs, and Document metadata with cryptographic SHA-256 hashes.
2. **Vector Store (`data/chroma_db`)**:
   - Contains clinical chunk embeddings, token metadata, and source chunk provenance used by the hybrid retrieval engine.
3. **Document File Store (`data/uploads`)**:
   - Stores raw clinical artifacts (PDFs, images, lab panels) referenced by the `documents` table.

To prevent clinical drift or broken citations, backups across all three layers must be coordinated.

---

## 2. Backup Procedures

### A. Online Relational Database Backup (SQLite)
Do **not** perform raw filesystem copies of `chronanexus.db` while the application is actively writing, as SQLite in WAL (Write-Ahead Logging) mode may leave uncheckpointed transactions in `chronanexus.db-wal`.

Use the SQLite atomic `VACUUM INTO` command:
```bash
# On Linux / Windows PowerShell:
sqlite3 chronanexus.db "VACUUM INTO 'backups/chronanexus_backup_$(date +%Y%m%d_%H%M%S).db';"
```
Or via Python:
```python
import sqlite3
import shutil
from datetime import datetime

timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
backup_path = f"backups/chronanexus_backup_{timestamp}.db"

# Open connection and invoke SQLite online backup API
src = sqlite3.connect("chronanexus.db")
dst = sqlite3.connect(backup_path)
with dst:
    src.backup(dst, pages=100)
dst.close()
src.close()
print(f"Relational backup completed: {backup_path}")
```

### B. Persistent Vector Store & File Archive
ChromaDB persists its SQLite metadata and parquet segment files inside `data/chroma_db`.

```bash
# Ensure backup directory exists
mkdir -p backups/data_snapshot_$(date +%Y%m%d_%H%M%S)

# Copy chroma vector database and file uploads
cp -r data/chroma_db backups/data_snapshot_$(date +%Y%m%d_%H%M%S)/
cp -r data/uploads backups/data_snapshot_$(date +%Y%m%d_%H%M%S)/
```

### C. Unified Backup Manifest Creation
Generate a cryptographic SHA-256 manifest of all backup artifacts:
```bash
# Generate hashes for integrity verification
sha256sum backups/* > backups/checksums.sha256
```

---

## 3. Restoration Procedure

### Step 1: Drain Ingress & Stop Services
```bash
# Stop backend processes to prevent concurrent writes
docker-compose down
# or stop uvicorn process
```

### Step 2: Validate Backup Integrity
```bash
# Verify checksums before restoring
sha256sum -c backups/checksums.sha256
```

### Step 3: Restore State Stores
```bash
# 1. Restore Relational Database
cp backups/chronanexus_backup_YYYYMMDD_HHMMSS.db chronanexus.db

# 2. Restore Persistent Vector Store
rm -rf data/chroma_db
cp -r backups/data_snapshot_YYYYMMDD_HHMMSS/chroma_db data/chroma_db

# 3. Restore Document Files
rm -rf data/uploads
cp -r backups/data_snapshot_YYYYMMDD_HHMMSS/uploads data/uploads
```

---

## 4. Cross-Store Consistency Verification

After restoration, run an integrity audit to verify that all indexed documents in the relational database have matching vector representations in ChromaDB.

Run the built-in diagnostic script:
```python
import sqlite3
import chromadb
from app.core.config import settings

# 1. Connect to relational database
conn = sqlite3.connect("chronanexus.db")
cursor = conn.cursor()
cursor.execute("SELECT id, original_filename, file_hash FROM documents")
documents = cursor.fetchall()
conn.close()

# 2. Connect to ChromaDB
client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
collection = client.get_or_create_collection(settings.CHROMA_COLLECTION_NAME)
vector_count = collection.count()

print(f"Total Relational Documents: {len(documents)}")
print(f"Total Vector Embeddings in '{settings.CHROMA_COLLECTION_NAME}': {vector_count}")

# 3. Verify chunk linkage
missing_docs = []
for doc_id, filename, file_hash in documents:
    results = collection.get(where={"document_id": str(doc_id)})
    if not results["ids"]:
        missing_docs.append((doc_id, filename))

if missing_docs:
    print(f"WARNING: Found {len(missing_docs)} documents without vector embeddings:")
    for m in missing_docs:
        print(f"  - Document ID {m[0]}: {m[1]}")
else:
    print("SUCCESS: 100% Cross-Store Consistency Verified.")
```

---

## 5. Disaster Recovery & Drift Remediation

If vector chunks are lost due to filesystem corruption or partial node failure while the relational database remains intact:
1. Identify missing document records using the consistency verification script above.
2. Trigger the asynchronous re-ingestion pipeline for affected document IDs:
   ```bash
   python -m app.services.ingestion_service --reindex --document-id <DOC_ID>
   ```
3. The ingestion service reads the original PDF from `data/uploads/`, re-chunks text, generates embeddings, and re-populates the Chroma collection with matching chunk metadata without duplicating relational database entries.
