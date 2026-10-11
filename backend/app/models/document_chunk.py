import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from backend.app.core.database import Base


class DocumentChunkModel(Base):
    """
    SQLAlchemy model for document chunks and vector embeddings.
    Uses pgvector (VECTOR type, dim=384) for vector similarity search in PostgreSQL.
    """
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=True, index=True)
    chunk_id = Column(String(100), nullable=False, unique=True, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    content = Column(Text, nullable=False)
    
    # Store embedding using pgvector Vector(384)
    embedding = Column(Vector(384), nullable=True)
    chunk_metadata = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    report = relationship("MedicalReport", backref="chunks")
    patient = relationship("Patient", backref="document_chunks")
