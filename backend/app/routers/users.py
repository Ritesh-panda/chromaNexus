from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.user import UserResponse, UserUpdate
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        avatarUrl=current_user.avatar_url,
        phoneNumber=current_user.phone_number,
        preferences=current_user.preferences or {},
        createdAt=current_user.created_at.isoformat() if current_user.created_at else None,
        updatedAt=current_user.updated_at.isoformat() if current_user.updated_at else None
    )


@router.put("/me", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.phoneNumber is not None:
        current_user.phone_number = user_update.phoneNumber
    if user_update.avatarUrl is not None:
        current_user.avatar_url = user_update.avatarUrl
    if user_update.preferences is not None:
        current_prefs = current_user.preferences or {}
        current_prefs.update(user_update.preferences)
        current_user.preferences = current_prefs

    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        avatarUrl=current_user.avatar_url,
        phoneNumber=current_user.phone_number,
        preferences=current_user.preferences or {},
        createdAt=current_user.created_at.isoformat() if current_user.created_at else None,
        updatedAt=current_user.updated_at.isoformat() if current_user.updated_at else None
    )
