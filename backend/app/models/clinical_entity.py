import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # 'disease' | 'medication' | 'lab_value' | 'procedure' | 'allergy'
    name = Column(String(255), nullable=False)
    confidence = Column(Float, default=0.95)
    value = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    report = relationship("MedicalReport", back_populates="extracted_entities")


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    icd_code = Column(String(50), nullable=True)
    status = Column(String(50), default="active")  # 'active' | 'resolved' | 'chronic' | 'in_remission'
    diagnosed_date = Column(String(50), nullable=False)
    resolved_date = Column(String(50), nullable=True)
    treating_doctor = Column(String(255), nullable=True)
    source_report_id = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="diseases")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    route = Column(String(50), default="oral")
    start_date = Column(String(50), nullable=False)
    end_date = Column(String(50), nullable=True)
    status = Column(String(50), default="active")  # 'active' | 'discontinued' | 'as_needed' | 'completed'
    prescribing_doctor = Column(String(255), nullable=True)
    indication = Column(String(255), nullable=True)
    source_report_id = Column(String(36), nullable=True)

    patient = relationship("Patient", back_populates="medications")


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    test_name = Column(String(255), nullable=False)
    category = Column(String(50), default="metabolic")  # 'lipid_panel' | 'metabolic' | 'cbc' | 'thyroid' | 'vitamin' | 'other'
    value = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=False)
    reference_range = Column(String(100), nullable=False)
    status = Column(String(50), default="normal")  # 'normal' | 'high' | 'low' | 'critical'
    test_date = Column(String(50), nullable=False)
    source_report_id = Column(String(36), nullable=True)
    hospital_name = Column(String(255), nullable=True)

    patient = relationship("Patient", back_populates="lab_results")
