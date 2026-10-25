import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from backend.app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    actor_id = Column(String(36), nullable=True, index=True)
    patient_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    outcome = Column(String(50), nullable=False, default="SUCCESS")  # "SUCCESS", "DENIED", "FAILED", "PARTIAL"
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    correlation_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
