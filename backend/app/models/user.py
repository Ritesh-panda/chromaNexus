import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="patient")  # 'patient' | 'doctor' | 'admin'
    avatar_url = Column(String(500), nullable=True)
    phone_number = Column(String(50), nullable=True)
    preferences = Column(JSON, nullable=True, default=lambda: {
        "theme": "system",
        "language": "en",
        "notifications": {
            "email": True,
            "sms": False,
            "criticalAlerts": True,
            "aiDigest": True
        },
        "privacy": {
            "strictDataIsolation": True,
            "localAiProcessingOnly": True,
            "auditableLogsEnabled": True
        }
    })
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    patient_profile = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
