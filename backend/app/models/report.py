import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String(50), default="application/pdf")
    category = Column(String(50), default="blood_report")
    hospital_name = Column(String(255), nullable=False)
    doctor_name = Column(String(255), nullable=True)
    report_date = Column(String(50), nullable=False)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), default="completed")  # 'completed' | 'processing' | 'pending' | 'failed'
    confidence_score = Column(Float, default=0.98)
    raw_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    storage_path = Column(String(500), nullable=True)

    # Checksums and page metadata (Phase 3)
    checksum = Column(String(64), nullable=True, index=True)
    content_checksum = Column(String(64), nullable=True)
    page_count = Column(Integer, default=1, nullable=True)

    patient = relationship("Patient", back_populates="reports")
    extracted_entities = relationship("ExtractedEntity", back_populates="report", cascade="all, delete-orphan")
