import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class DoctorSummary(Base):
    __tablename__ = "doctor_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_name = Column(String(255), nullable=False)
    age = Column(Integer, default=38)
    gender = Column(String(50), default="Male (38M)")
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    summary_overview = Column(Text, nullable=False)
    current_diseases = Column(JSON, default=list)
    past_diseases = Column(JSON, default=list)
    active_medications = Column(JSON, default=list)
    known_allergies = Column(JSON, default=list)
    abnormal_labs = Column(JSON, default=list)
    risk_factors = Column(JSON, default=list)
    recent_reports = Column(JSON, default=list)
    timeline_highlights = Column(JSON, default=list)
    share_token = Column(String(100), unique=True, nullable=True, index=True)

    patient = relationship("Patient", back_populates="summaries")
