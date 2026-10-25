from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.services.auth_service import get_current_user, get_current_patient
from backend.app.services.purge_service import get_purge_preview, execute_patient_purge

router = APIRouter(prefix="/patients/me/purge", tags=["Patient Data Purge"])


class PurgeConfirmRequest(BaseModel):
    purgeToken: Optional[str] = Field(None, description="15-minute confirmation token issued by purge preview")
    confirmationPhrase: Optional[str] = Field(None, description="Must exactly match 'PERMANENTLY DELETE MY DATA'")
    confirmation_token: Optional[str] = None
    confirmation_phrase: Optional[str] = None

    @property
    def token(self) -> str:
        return self.purgeToken or self.confirmation_token or ""

    @property
    def phrase(self) -> str:
        return self.confirmationPhrase or self.confirmation_phrase or ""


@router.post("/request")
def request_purge_preview(
    current_user: User = Depends(get_current_user),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Step 1 of Purge Workflow:
    Returns the exact scope of data to be destroyed and generates a 15-minute confirmation token.
    """
    preview = get_purge_preview(db=db, patient=current_patient, actor_id=current_user.id)
    return preview


@router.post("/confirm")
def confirm_and_execute_purge(
    confirm_in: PurgeConfirmRequest,
    current_user: User = Depends(get_current_user),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Step 2 of Purge Workflow:
    Requires valid confirmation token and exact confirmation phrase to permanently delete data across
    files, ChromaDB vectors, and relational database records.
    """
    success, result = execute_patient_purge(
        db=db,
        patient=current_patient,
        purge_token=confirm_in.token,
        confirmation_phrase=confirm_in.phrase,
        actor_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

    return result
