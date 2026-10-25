from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from backend.app.services.auth_service import get_current_user, get_current_patient
from backend.app.services.audit_service import query_audit_logs

router = APIRouter(prefix="/audit", tags=["Audit Logging"])


@router.get("/logs", response_model=AuditLogListResponse)
def get_audit_logs(
    action: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Returns audit trail entries strictly scoped to the authenticated user and their patient profile.
    Cross-patient log inspection is blocked.
    """
    logs = query_audit_logs(
        db=db,
        patient_id=current_patient.id,
        actor_id=current_user.id,
        action=action,
        outcome=outcome,
        limit=limit,
        offset=offset
    )

    formatted = [
        AuditLogResponse(
            id=l.id,
            timestamp=l.timestamp.isoformat(),
            actorId=l.actor_id,
            patientId=l.patient_id,
            action=l.action,
            outcome=l.outcome,
            resourceType=l.resource_type,
            resourceId=l.resource_id,
            correlationId=l.correlation_id,
            details=l.details,
            ipAddress=l.ip_address
        ) for l in logs
    ]

    return AuditLogListResponse(total=len(formatted), items=formatted)
