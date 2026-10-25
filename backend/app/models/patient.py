import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    date_of_birth = Column(String(50), nullable=True)
    gender = Column(String(20), default="other")  # 'male' | 'female' | 'other'
    blood_group = Column(String(10), default="O+")
    height_cm = Column(Float, default=175.0)
    weight_kg = Column(Float, default=78.0)
    primary_care_physician = Column(String(255), default="Dr. Sarah Jenkins, MD")
    emergency_contact = Column(JSON, default=lambda: {
        "name": "Elena Vance",
        "relationship": "Spouse",
        "phone": "+1 (555) 987-6543"
    })
    insurance = Column(JSON, nullable=True, default=lambda: {
        "providerName": "BlueCross Shield Pro",
        "policyNumber": "BCS-99281-X",
        "groupNumber": "GRP-8812",
        "validUntil": "2027-12-31"
    })
    known_allergies = Column(JSON, default=lambda: [
        "Penicillin (Moderate Rash)",
        "Sulfa Drugs (Anaphylaxis Risk)"
    ])

    user = relationship("User", back_populates="patient_profile")
    reports = relationship("MedicalReport", back_populates="patient", cascade="all, delete-orphan")
    diseases = relationship("Disease", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="patient", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="patient", cascade="all, delete-orphan")
    summaries = relationship("DoctorSummary", back_populates="patient", cascade="all, delete-orphan")
    conversations = relationship("ChatConversation", back_populates="patient", cascade="all, delete-orphan")
    allergies = relationship("Allergy", back_populates="patient", cascade="all, delete-orphan")

