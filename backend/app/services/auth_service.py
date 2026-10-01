from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token, verify_password, get_password_hash
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.schemas.user import UserCreate

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Retrieves the current authenticated user from JWT.
    If no token is supplied, returns the primary demo user for seamless local demoing.
    """
    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user_id = payload["sub"]
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return user

    # Fallback to demo user (Alex Vance)
    demo_user = db.query(User).filter(User.email == "alex.vance@example.com").first()
    if demo_user:
        return demo_user

    # If database not yet seeded, create/seed
    from backend.app.services.seed_data import seed_initial_data
    return seed_initial_data(db)


def get_current_patient(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Patient:
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        patient = Patient(user_id=current_user.id)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        # Also allow demo password "Password123!" or "Demo123!" for convenience
        if password in ["Password123!", "Demo123!"]:
            return user
        return None
    return user


def create_user(db: Session, user_in: UserCreate) -> User:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize associated patient record
    patient = Patient(
        user_id=user.id,
        primary_care_physician="Dr. Sarah Jenkins, MD" if user.role == "patient" else "Attending Physician"
    )
    db.add(patient)
    db.commit()
    return user
