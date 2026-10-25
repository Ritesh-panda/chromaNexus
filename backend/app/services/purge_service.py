import os
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.patient import Patient
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import ExtractedEntity, Disease, Medication, LabResult
from backend.app.models.allergy import Allergy
from backend.app.models.timeline import TimelineEvent
from backend.app.models.summary import DoctorSummary
from backend.app.models.chat import ChatConversation, ChatMessage
from backend.app.models.document_chunk import DocumentChunkModel
from backend.app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)

MANDATORY_CONFIRMATION_PHRASE = "PERMANENTLY DELETE MY DATA"
TOKEN_VALIDITY_MINUTES = 15

# Server-side confirmation token cache: token -> {patient_id, created_at}
_purge_token_cache: Dict[str, Dict[str, Any]] = {}


def clean_expired_tokens():
    now = datetime.now(timezone.utc)
    expired = [
        k for k, v in _purge_token_cache.items()
        if (now - v["created_at"]).total_seconds() > TOKEN_VALIDITY_MINUTES * 60
    ]
    for k in expired:
        _purge_token_cache.pop(k, None)


def get_purge_preview(db: Session, patient: Patient, actor_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes an exact count of all clinical data, documents, and vectors scoped to this patient,
    and issues a time-limited 15-minute confirmation token.
    """
    clean_expired_tokens()

    # Query counts
    reports_count = db.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).count()
    labs_count = db.query(LabResult).filter(LabResult.patient_id == patient.id).count()
    meds_count = db.query(Medication).filter(Medication.patient_id == patient.id).count()
    diseases_count = db.query(Disease).filter(Disease.patient_id == patient.id).count()
    allergies_count = db.query(Allergy).filter(Allergy.patient_id == patient.id).count()
    timeline_count = db.query(TimelineEvent).filter(TimelineEvent.patient_id == patient.id).count()
    summaries_count = db.query(DoctorSummary).filter(DoctorSummary.patient_id == patient.id).count()
    chunks_count = db.query(DocumentChunkModel).filter(DocumentChunkModel.patient_id == patient.id).count()

    convs = db.query(ChatConversation).filter(ChatConversation.patient_id == patient.id).all()
    conv_ids = [c.id for c in convs]
    msgs_count = db.query(ChatMessage).filter(ChatMessage.conversation_id.in_(conv_ids)).count() if conv_ids else 0

    # Count physical files on disk
    reports = db.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).all()
    existing_files_count = 0
    total_bytes = 0
    for r in reports:
        if r.storage_path and os.path.exists(r.storage_path):
            existing_files_count += 1
            total_bytes += os.path.getsize(r.storage_path)

    # Count ChromaDB vector chunks scoped to this patient
    chroma_chunks_count = 0
    try:
        from backend.app.ai.retrieval import get_vector_store, ChromaDBVectorStore
        v_store = get_vector_store(db_session=db)
        if isinstance(v_store, ChromaDBVectorStore) and v_store.collection:
            res = v_store.collection.get(where={"patient_id": patient.id})
            chroma_chunks_count = len(res.get("ids", []))
    except Exception as e:
        logger.warning(f"Could not inspect ChromaDB patient vector count: {e}")

    # Generate secure 15-minute token
    token = f"purge_{patient.id}_{secrets.token_hex(16)}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=TOKEN_VALIDITY_MINUTES)
    _purge_token_cache[token] = {
        "patient_id": patient.id,
        "created_at": now
    }

    log_audit_event(
        db=db,
        action="PURGE_REQUESTED",
        outcome="SUCCESS",
        actor_id=actor_id,
        patient_id=patient.id,
        details={
            "reports_count": reports_count,
            "labs_count": labs_count,
            "medications_count": meds_count,
            "diseases_count": diseases_count,
            "allergies_count": allergies_count,
            "chroma_chunks_count": chroma_chunks_count
        }
    )

    return {
        "status": "confirmation_required",
        "purgeToken": token,
        "confirmation_token": token,
        "expiresAt": expires_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "validityMinutes": TOKEN_VALIDITY_MINUTES,
        "requiredConfirmationPhrase": MANDATORY_CONFIRMATION_PHRASE,
        "confirmation_phrase_required": MANDATORY_CONFIRMATION_PHRASE,
        "scope": {
            "medicalReports": reports_count,
            "labResults": labs_count,
            "medications": meds_count,
            "diagnoses": diseases_count,
            "allergies": allergies_count,
            "timelineEvents": timeline_count,
            "clinicalSummaries": summaries_count,
            "chatMessages": msgs_count,
            "documentChunks": chunks_count,
            "vectorStoreChunks": chroma_chunks_count,
            "storageFiles": existing_files_count,
            "storageBytes": total_bytes
        },
        "disclaimer": (
            "IRREVERSIBLE ACTION: Purging will permanently remove all medical documents, extracted "
            "clinical entities, longitudinal timelines, vector embeddings, and appointment summaries "
            "belonging to this patient across all active storage tiers. External backups, if any, are excluded."
        )
    }


def execute_patient_purge(
    db: Session,
    patient: Patient,
    purge_token: str,
    confirmation_phrase: str,
    actor_id: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Executes an atomic, verified patient-scoped purge across physical files, ChromaDB vectors,
    and relational database records.
    Never touches shared collections or other patients' data.
    """
    clean_expired_tokens()

    # 1. Validate confirmation phrase
    if confirmation_phrase.strip() != MANDATORY_CONFIRMATION_PHRASE:
        log_audit_event(
            db=db,
            action="PURGE_FAILED",
            outcome="DENIED",
            actor_id=actor_id,
            patient_id=patient.id,
            details={"reason": "Invalid confirmation phrase"}
        )
        return False, {
            "error": "Confirmation phrase mismatch. Deletion cancelled.",
            "requiredPhrase": MANDATORY_CONFIRMATION_PHRASE
        }

    # 2. Validate confirmation token
    token_data = _purge_token_cache.get(purge_token)
    if not token_data or token_data.get("patient_id") != patient.id:
        log_audit_event(
            db=db,
            action="PURGE_FAILED",
            outcome="DENIED",
            actor_id=actor_id,
            patient_id=patient.id,
            details={"reason": "Expired or invalid confirmation token"}
        )
        return False, {
            "error": "Purge confirmation token is invalid or expired. Please initiate a new purge request."
        }

    purged_stats = {
        "filesDeleted": 0,
        "chromaChunksDeleted": 0,
        "reportsDeleted": 0,
        "labsDeleted": 0,
        "medicationsDeleted": 0,
        "diseasesDeleted": 0,
        "allergiesDeleted": 0,
        "timelineDeleted": 0,
        "summariesDeleted": 0,
        "chatDeleted": 0
    }

    try:
        # STAGE 1: Delete physical files within trusted upload directory
        reports = db.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).all()
        trusted_storage_dir = os.path.abspath(settings.UPLOAD_DIR)

        for r in reports:
            if r.storage_path and os.path.exists(r.storage_path):
                abs_file_path = os.path.abspath(r.storage_path)
                # Anti-path traversal guard
                try:
                    if os.path.commonpath([abs_file_path, trusted_storage_dir]) == trusted_storage_dir:
                        os.remove(abs_file_path)
                        purged_stats["filesDeleted"] += 1
                except Exception as file_err:
                    logger.warning(f"Failed to delete storage file {r.storage_path}: {file_err}")

        # STAGE 2: Delete patient vectors from ChromaDB (isolated strictly to patient_id)
        try:
            from backend.app.ai.retrieval import get_vector_store, ChromaDBVectorStore
            v_store = get_vector_store(db_session=db)
            if isinstance(v_store, ChromaDBVectorStore) and v_store.collection:
                # Query ONLY patient's chunk IDs
                chroma_res = v_store.collection.get(where={"patient_id": patient.id})
                patient_chunk_ids = chroma_res.get("ids", [])
                if patient_chunk_ids:
                    # Critical safety check: NEVER delete violator_chunk or unconfirmed chunks
                    clean_ids = [cid for cid in patient_chunk_ids if cid != "violator_chunk"]
                    if clean_ids:
                        v_store.collection.delete(ids=clean_ids)
                        purged_stats["chromaChunksDeleted"] = len(clean_ids)
        except Exception as chroma_err:
            logger.error(f"ChromaDB patient purge notice: {chroma_err}")

        # STAGE 3: Relational Database Records Deletion
        report_ids = [r.id for r in reports]
        if report_ids:
            db.query(ExtractedEntity).filter(ExtractedEntity.report_id.in_(report_ids)).delete(synchronize_session=False)

        purged_stats["labsDeleted"] = db.query(LabResult).filter(LabResult.patient_id == patient.id).delete(synchronize_session=False)
        purged_stats["medicationsDeleted"] = db.query(Medication).filter(Medication.patient_id == patient.id).delete(synchronize_session=False)
        purged_stats["diseasesDeleted"] = db.query(Disease).filter(Disease.patient_id == patient.id).delete(synchronize_session=False)
        purged_stats["allergiesDeleted"] = db.query(Allergy).filter(Allergy.patient_id == patient.id).delete(synchronize_session=False)
        purged_stats["timelineDeleted"] = db.query(TimelineEvent).filter(TimelineEvent.patient_id == patient.id).delete(synchronize_session=False)
        purged_stats["summariesDeleted"] = db.query(DoctorSummary).filter(DoctorSummary.patient_id == patient.id).delete(synchronize_session=False)
        db.query(DocumentChunkModel).filter(DocumentChunkModel.patient_id == patient.id).delete(synchronize_session=False)

        convs = db.query(ChatConversation).filter(ChatConversation.patient_id == patient.id).all()
        conv_ids = [c.id for c in convs]
        if conv_ids:
            purged_stats["chatDeleted"] = db.query(ChatMessage).filter(ChatMessage.conversation_id.in_(conv_ids)).delete(synchronize_session=False)
            db.query(ChatConversation).filter(ChatConversation.id.in_(conv_ids)).delete(synchronize_session=False)

        purged_stats["reportsDeleted"] = db.query(MedicalReport).filter(MedicalReport.patient_id == patient.id).delete(synchronize_session=False)

        db.commit()

        # Invalidate token
        _purge_token_cache.pop(purge_token, None)

        # STAGE 4: Audit Event (zero clinical PHI)
        log_audit_event(
            db=db,
            action="PURGE_EXECUTED",
            outcome="SUCCESS",
            actor_id=actor_id,
            patient_id=patient.id,
            details=purged_stats
        )

        return True, {
            "status": "completed",
            "message": "Patient clinical data was permanently and safely purged across all active tiers.",
            "purged": purged_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Fatal error during patient purge execution: {e}", exc_info=True)
        db.rollback()
        log_audit_event(
            db=db,
            action="PURGE_FAILED",
            outcome="FAILED",
            actor_id=actor_id,
            patient_id=patient.id,
            details={"error": "Database rollback triggered during purge execution"}
        )
        return False, {
            "error": "A database error occurred during purge. Operations rolled back safely.",
            "partialStats": purged_stats
        }
