import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {
    "password", "token", "secret", "raw_text", "summary", 
    "api_key", "authorization", "credit_card", "ssn", "credentials"
}


def sanitize_details(details: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Recursively removes sensitive keys, credentials, and full PHI bodies from audit metadata."""
    if not details or not isinstance(details, dict):
        return None
    sanitized = {}
    for k, v in details.items():
        if any(sens in k.lower() for sens in SENSITIVE_KEYS):
            continue
        elif isinstance(v, dict):
            sanitized[k] = sanitize_details(v)
        elif isinstance(v, (str, int, float, bool, list)):
            if isinstance(v, str) and len(v) > 300:
                sanitized[k] = v[:300] + "... [TRUNCATED]"
            else:
                sanitized[k] = v
        else:
            sanitized[k] = str(v)
    return sanitized


def log_audit_event(
    db: Session,
    action: str,
    outcome: str = "SUCCESS",
    actor_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> Optional[AuditLog]:
    """
    Safely creates an immutable audit record in the database.
    Catches errors defensively to avoid crashing application workflows.
    """
    try:
        clean_details = sanitize_details(details)
        log_entry = AuditLog(
            timestamp=datetime.now(timezone.utc),
            actor_id=actor_id,
            patient_id=patient_id,
            action=action.upper(),
            outcome=outcome.upper(),
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            details=clean_details,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:
        logger.error(f"Audit logging failed: {e}", exc_info=False)
        try:
            db.rollback()
        except Exception:
            pass
        return None


def query_audit_logs(
    db: Session,
    patient_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[AuditLog]:
    """
    Queries audit logs strictly filtered by authorized patient or actor scope.
    """
    query = db.query(AuditLog)
    if patient_id and actor_id:
        query = query.filter((AuditLog.patient_id == patient_id) | (AuditLog.actor_id == actor_id))
    elif patient_id:
        query = query.filter(AuditLog.patient_id == patient_id)
    elif actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    else:
        # Prevent unrestricted queries
        return []

    if action and action != "all":
        query = query.filter(AuditLog.action == action.upper())
    if outcome and outcome != "all":
        query = query.filter(AuditLog.outcome == outcome.upper())

    return query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
