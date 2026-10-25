# ChronaNexus Forensic Audit Dossier ? Data Model & Migrations

**Document ID:** `04_DATA_MODEL_AND_MIGRATIONS.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  

---

## 1. Relational Schema Architecture (14 Models)

ChronaNexus implements a comprehensive clinical relational schema in SQLAlchemy (`backend/app/models/`):

| Model Name | Table Name | Primary Key | Foreign Keys | Key Columns | Evidence Path |
|---|---|---|---|---|---|
| `User` | `users` | `id` (UUID str) | None | `email` (unique), `hashed_password`, `role`, `is_active` | `backend/app/models/user.py:10` |
| `Patient` | `patients` | `id` (UUID str) | `user_id -> users.id` | `first_name`, `last_name`, `dob`, `gender`, `blood_group` | `backend/app/models/patient.py:10` |
| `MedicalReport` | `medical_reports` | `id` (UUID str) | `patient_id -> patients.id` | `title`, `category`, `storage_path`, `checksum`, `content_checksum`, `page_count` | `backend/app/models/report.py:12` |
| `DocumentChunkModel` | `document_chunks` | `id` (UUID str) | `document_id -> medical_reports.id` | `page_number`, `chunk_index`, `text`, `section_type`, `metadata_json` | `backend/app/models/document_chunk.py:10` |
| `ExtractedEntity` | `extracted_entities` | `id` (UUID str) | `report_id -> medical_reports.id`, `patient_id -> patients.id` | `entity_type`, `entity_value`, `normalized_code`, `confidence_score` | `backend/app/models/clinical_entity.py:15` |
| `Disease` | `diseases` | `id` (UUID str) | `patient_id -> patients.id`, `source_report_id -> medical_reports.id` | `name`, `icd10_code`, `diagnosed_date`, `status`, `severity` | `backend/app/models/clinical_entity.py:45` |
| `Medication` | `medications` | `id` (UUID str) | `patient_id -> patients.id`, `source_report_id -> medical_reports.id` | `name`, `dosage`, `frequency`, `route`, `start_date`, `status` | `backend/app/models/clinical_entity.py:75` |
| `LabResult` | `lab_results` | `id` (UUID str) | `patient_id -> patients.id`, `source_report_id -> medical_reports.id` | `test_name`, `value`, `unit`, `reference_range`, `status`, `source_page_number` | `backend/app/models/clinical_entity.py:105` |
| `Allergy` | `allergies` | `id` (UUID str) | `patient_id -> patients.id`, `source_report_id -> medical_reports.id` | `allergen`, `reaction`, `severity`, `status`, `source_page_number` | `backend/app/models/allergy.py:10` |
| `TimelineEvent` | `timeline_events` | `id` (UUID str) | `patient_id -> patients.id`, `source_report_id -> medical_reports.id` | `event_date`, `event_type`, `title`, `description`, `significance` | `backend/app/models/timeline.py:10` |
| `ChatConversation` | `chat_conversations` | `id` (UUID str) | `patient_id -> patients.id` | `title`, `created_at`, `updated_at` | `backend/app/models/chat.py:10` |
| `ChatMessage` | `chat_messages` | `id` (UUID str) | `conversation_id -> chat_conversations.id` | `sender`, `text`, `citations_json`, `created_at` | `backend/app/models/chat.py:35` |
| `DoctorSummary` | `doctor_summaries` | `id` (UUID str) | `patient_id -> patients.id` | `summary_type`, `content_json`, `generated_at` | `backend/app/models/summary.py:10` |
| `AlembicVersion` | `alembic_version` | `version_num` | None | Tracks migration state in relational DB | `backend/alembic/env.py` |

---

## 2. Alembic Migration Graph

The migration chain consists of 4 linear revisions:

```
[001_initial_schema]
         ?  (Initial users, patients, reports, entities, diseases, meds, labs, timeline, chat)
         ?
[002_add_document_chunks]
         ?  (Added document_chunks table and pgvector extension support)
         ?
[003_add_provenance_and_allergies]
         ?  (Added allergies table, source_page_number, bounding_box, extraction_confidence)
         ?
[004_add_checksum_and_page_metadata]
            (Added checksum, content_checksum, page_count to medical_reports)
```

---

## 3. Database State & Schema Divergence Verification

An automated schema dump of the persistent root database (`chronanexus.db`) reveals a **major divergence between Python ORM models and persistent DB columns**:

### Evidence: `alembic_version` in `chronanexus.db`
```sql
SELECT version_num FROM alembic_version;
-- Result: '002_add_document_chunks'
```

### Table Column Comparison: `medical_reports`
| Column Name | Defined in ORM Model (`report.py`)? | Present in Migration 004? | Present in Persistent `chronanexus.db`? |
|---|---|---|---|
| `id` | YES | YES | YES |
| `patient_id` | YES | YES | YES |
| `title` | YES | YES | YES |
| `category` | YES | YES | YES |
| `storage_path` | YES | YES | YES |
| `status` | YES | YES | YES |
| **`checksum`** | **YES** | **YES (Rev 004)** | **NO ? MISSING FROM PERSISTENT DB** |
| **`content_checksum`** | **YES** | **YES (Rev 004)** | **NO ? MISSING FROM PERSISTENT DB** |
| **`page_count`** | **YES** | **YES (Rev 004)** | **NO ? MISSING FROM PERSISTENT DB** |

### Table Column Comparison: `lab_results`
| Column Name | Defined in ORM Model (`clinical_entity.py`)? | Present in Migration 003? | Present in Persistent `chronanexus.db`? |
|---|---|---|---|
| `id` | YES | YES | YES |
| `patient_id` | YES | YES | YES |
| `test_name` | YES | YES | YES |
| `value`, `unit` | YES | YES | YES |
| **`source_page_number`** | **YES** | **YES (Rev 003)** | **NO ? MISSING FROM PERSISTENT DB** |
| **`bounding_box`** | **YES** | **YES (Rev 003)** | **NO ? MISSING FROM PERSISTENT DB** |
| **`extraction_confidence`**| **YES** | **YES (Rev 003)** | **NO ? MISSING FROM PERSISTENT DB** |

### Why Tests Passed While Persistent Database Remained Unmigrated
In `backend/tests/conftest.py`, automated tests create an ephemeral SQLite database (`test_chronanexus.db`) using `Base.metadata.create_all(bind=test_engine)`. Because `Base.metadata.create_all` generates tables directly from current Python classes, the test database always had the newest columns. Alembic was never invoked during unit test execution, leaving `chronanexus.db` at revision 002.

---

## 4. Safe Migration Procedure

To bring `chronanexus.db` into full compliance with Phase 3 without data loss:

### Step 1: Backup Persistent Database
```bash
cp chronanexus.db chronanexus_backup_rev002_$(date +%Y%m%d_%H%M%S).db
```

### Step 2: Validate Migration Upgrade on Disposable Copy
```bash
python tests/benchmarks/test_migration_003_disposable.py
# Verified: EXITED 0 (Clean migration lifecycle)
```

### Step 3: Proposed Execution Command
```bash
# In backend directory:
alembic upgrade head
```

### Step 4: Verification Query
```sql
SELECT version_num FROM alembic_version;
-- Expected: '004_add_checksum_and_page_metadata'
PRAGMA table_info(medical_reports);
-- Must show 'checksum', 'content_checksum', 'page_count'
```
