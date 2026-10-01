from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import create_access_token
from backend.app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from backend.app.services.auth_service import authenticate_user, create_user, get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    user = create_user(db, user_in)
    access_token = create_access_token(user.id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            avatarUrl=user.avatar_url,
            phoneNumber=user.phone_number,
            preferences=user.preferences or {},
            createdAt=user.created_at.isoformat() if user.created_at else None,
            updatedAt=user.updated_at.isoformat() if user.updated_at else None
        )
    )


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    access_token = create_access_token(user.id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            avatarUrl=user.avatar_url,
            phoneNumber=user.phone_number,
            preferences=user.preferences or {},
            createdAt=user.created_at.isoformat() if user.created_at else None,
            updatedAt=user.updated_at.isoformat() if user.updated_at else None
        )
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
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


@router.post("/refresh", response_model=Token)
def refresh_token(current_user: User = Depends(get_current_user)):
    access_token = create_access_token(current_user.id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
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
    )


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully from session."}
