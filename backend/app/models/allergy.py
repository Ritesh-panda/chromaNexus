import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    allergen = Column(String(255), nullable=False)
    category = Column(String(50), default="medication")  # 'medication' | 'food' | 'environmental' | 'other'
    severity = Column(String(50), default="moderate")  # 'mild' | 'moderate' | 'severe' | 'life-threatening'
    reaction = Column(String(255), nullable=True)
    drug_classes = Column(JSON, nullable=True)  # List[str] e.g. ["Penicillins", "Beta-lactam antibacterials"]
    cross_reactivities = Column(JSON, nullable=True)  # List[str] e.g. ["amoxicillin", "ampicillin", "augmentin"]
    status = Column(String(50), default="active")  # 'active' | 'resolved' | 'suspected'
    source_report_id = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)

    # Source Provenance Fields
    source_page_number = Column(Integer, nullable=True)
    bounding_box = Column(JSON, nullable=True)  # e.g. {"x0": 72, "y0": 150, "x1": 520, "y1": 165, "page": 1}
    extraction_confidence = Column(Float, nullable=True, default=None)


    patient = relationship("Patient", back_populates="allergies")
