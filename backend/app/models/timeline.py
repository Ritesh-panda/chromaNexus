import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    event_type = Column(String(50), nullable=False)  # 'diagnosis', 'medication_start', 'lab_test', 'imaging', 'surgery', etc.
    severity = Column(String(50), default="medium")  # 'low' | 'medium' | 'high' | 'critical'
    doctor_name = Column(String(255), nullable=True)
    facility = Column(String(255), nullable=True)
    source_report_id = Column(String(36), nullable=True)
    source_report_title = Column(String(255), nullable=True)
    connected_entities = Column(JSON, nullable=True, default=lambda: {
        "diseases": [],
        "medications": [],
        "labResults": []
    })

    patient = relationship("Patient", back_populates="timeline_events")
