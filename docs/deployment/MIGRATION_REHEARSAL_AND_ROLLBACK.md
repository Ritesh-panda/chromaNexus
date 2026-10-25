# ChronaNexus — Schema Migration Rehearsal & Rollback Runbook

## 1. Safety Principles & Policy

1. **Zero Untested In-Place Migrations**:
   - Never apply Alembic migrations directly to persistent production databases (`chronanexus.db`) without first executing a rehearsal on an isolated, disposable copy.
2. **Snapshot-First Requirement**:
   - Prior to executing any schema change, take an immutable SQLite snapshot (`VACUUM INTO`) and record its SHA-256 fingerprint.
3. **Dual-Store Awareness**:
   - Verify if the schema change affects tables linked to vector store metadata (e.g. `documents`, `patients`, `timeline_events`).

---

## 2. Disposable Database Migration Rehearsal

A migration rehearsal verifies that all schema additions, index definitions, foreign key constraints, and column defaults compile and execute cleanly against realistic clinical schemas without data loss.

### Step-by-Step Rehearsal Script

```bash
# 1. Create a disposable temporary sandbox directory
mkdir -p /tmp/chronanexus_migration_rehearsal
cd backend

# 2. Clone the current production database snapshot into the sandbox
cp ../chronanexus.db /tmp/chronanexus_migration_rehearsal/rehearsal.db

# 3. Inspect pending Alembic revisions
alembic current
alembic heads

# 4. Execute the migration against the rehearsal database
DATABASE_URL="sqlite:////tmp/chronanexus_migration_rehearsal/rehearsal.db" alembic upgrade head

# 5. Verify database integrity post-migration
sqlite3 /tmp/chronanexus_migration_rehearsal/rehearsal.db "PRAGMA integrity_check;"
sqlite3 /tmp/chronanexus_migration_rehearsal/rehearsal.db "PRAGMA foreign_key_check;"

# 6. Verify table counts match expected baselines
sqlite3 /tmp/chronanexus_migration_rehearsal/rehearsal.db "SELECT count(*) FROM patients;"
sqlite3 /tmp/chronanexus_migration_rehearsal/rehearsal.db "SELECT count(*) FROM documents;"
sqlite3 /tmp/chronanexus_migration_rehearsal/rehearsal.db "SELECT count(*) FROM lab_results;"

# 7. Clean up the rehearsal sandbox
rm -rf /tmp/chronanexus_migration_rehearsal
```

If all checks return `ok` and record counts are preserved, the migration revision is certified for scheduled deployment.

---

## 3. Production Migration Procedure

Once the rehearsal passes and an operational maintenance window is active:

1. **Stop active API workers**:
   ```bash
   systemctl stop chronanexus-backend # or docker-compose stop backend
   ```
2. **Take immediate pre-migration snapshot**:
   ```bash
   sqlite3 chronanexus.db "VACUUM INTO 'backups/pre_migration_$(date +%Y%m%d_%H%M%S).db';"
   sha256sum chronanexus.db > backups/pre_migration_sha256.txt
   ```
3. **Execute Alembic upgrade**:
   ```bash
   cd backend
   alembic upgrade head
   ```
4. **Validate application readiness**:
   ```bash
   python -c "from app.db.session import SessionLocal; from app.models import Patient; db = SessionLocal(); print('Patients:', db.query(Patient).count()); db.close()"
   ```
5. **Restart backend services**:
   ```bash
   systemctl start chronanexus-backend # or docker-compose up -d backend
   curl http://localhost:8000/ready
   ```

---

## 4. Rollback & Downgrade Runbook

If a migration fails mid-execution, causes database lock errors, or breaks downstream queries:

### Option A: Clean Alembic Downgrade (If transaction was successful but defects detected)
```bash
cd backend
# Rollback one revision
alembic downgrade -1

# Verify schema
alembic current
```

> **Note on SQLite Schema Downgrades**: SQLite has limited native support for `ALTER TABLE DROP COLUMN`. In Alembic, migrations must utilize `batch_alter_table` mode to safely recreate tables during downgrades. If a migration does not support clean downgrade, execute Option B immediately.

### Option B: Disaster Rollback from Pre-Migration Snapshot
```bash
# 1. Stop backend service
systemctl stop chronanexus-backend

# 2. Archive the failed database state for post-mortem analysis
mv chronanexus.db chronanexus_failed_migration_$(date +%Y%m%d_%H%M%S).db

# 3. Restore the pre-migration snapshot
cp backups/pre_migration_*.db chronanexus.db

# 4. Verify restored hash
sha256sum chronanexus.db
cat backups/pre_migration_sha256.txt

# 5. Restart backend service
systemctl start chronanexus-backend
curl http://localhost:8000/ready
```
