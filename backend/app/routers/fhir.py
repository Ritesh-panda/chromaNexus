from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.services.auth_service import get_current_user, get_current_patient
from backend.app.services.fhir_service import generate_fhir_r4_bundle_for_patient, validate_fhir_r4_bundle
from backend.app.services.audit_service import log_audit_event

router = APIRouter(prefix="/fhir", tags=["FHIR R4 Export"])


@router.get("/export")
def export_fhir_bundle(
    current_user: User = Depends(get_current_user),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Exports authenticated patient records as a validated HL7 FHIR R4 Bundle.
    Records an immutable audit trail entry without storing clinical PHI.
    """
    bundle = generate_fhir_r4_bundle_for_patient(db, current_patient)
    is_valid, validation_errors = validate_fhir_r4_bundle(bundle)

    if not is_valid:
        log_audit_event(
            db=db,
            action="FHIR_EXPORT",
            outcome="FAILED",
            actor_id=current_user.id,
            patient_id=current_patient.id,
            resource_type="bundle",
            details={"error_count": len(validation_errors), "sample_error": validation_errors[0] if validation_errors else "Validation failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FHIR R4 validation error: {validation_errors[:3]}"
        )

    # Log successful audit event
    log_audit_event(
        db=db,
        action="FHIR_EXPORT",
        outcome="SUCCESS",
        actor_id=current_user.id,
        patient_id=current_patient.id,
        resource_type="bundle",
        resource_id=bundle["id"],
        details={"resource_count": bundle.get("total", 0), "bundle_type": "collection"}
    )

    headers = {
        "Content-Disposition": f"attachment; filename=chronanexus_fhir_r4_{current_patient.id[:8]}.json"
    }
    return JSONResponse(content=bundle, headers=headers)
