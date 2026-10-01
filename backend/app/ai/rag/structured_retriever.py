import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.models.clinical_entity import LabResult, Medication, Disease
from backend.app.models.timeline import TimelineEvent
from backend.app.models.report import MedicalReport

logger = logging.getLogger(__name__)


class StructuredClinicalResult(BaseModel):
    """
    Standard container for structured clinical data retrieved directly from relational DB tables.
    """
    source_type: str  # 'lab_result' | 'medication' | 'disease' | 'timeline_event' | 'medical_report'
    source_id: str
    report_id: Optional[str] = None
    title: str
    date: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = 0.95


class StructuredRetriever:
    """
    Direct SQL/ORM Retriever for structured patient records.
    Never relies on fuzzy embeddings for exact numbers, dates, or drug dosages.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def retrieve_labs(
        self,
        patient_id: str,
        query_keywords: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[StructuredClinicalResult]:
        try:
            q = self.db.query(LabResult).filter(LabResult.patient_id == patient_id)
            records = q.order_by(LabResult.test_date.desc()).all()

            results: List[StructuredClinicalResult] = []
            for r in records:
                # If keywords provided, filter
                if query_keywords:
                    t_name = r.test_name.lower()
                    if not any(k.lower() in t_name for k in query_keywords):
                        continue

                content = (
                    f"Test: {r.test_name} | Value: {r.value} {r.unit} "
                    f"(Ref: {r.reference_range}) | Status: {r.status.upper()} | Date: {r.test_date}"
                )
                if r.hospital_name:
                    content += f" | Facility: {r.hospital_name}"

                results.append(StructuredClinicalResult(
                    source_type="lab_result",
                    source_id=r.id,
                    report_id=r.source_report_id,
                    title=f"Lab: {r.test_name}",
                    date=r.test_date,
                    content=content,
                    metadata={
                        "test_name": r.test_name,
                        "value": r.value,
                        "unit": r.unit,
                        "status": r.status,
                        "hospital": r.hospital_name
                    },
                    relevance_score=0.98 if r.status in ["high", "low", "critical"] else 0.92
                ))

            return results[:limit]
        except Exception as e:
            logger.error(f"Error in retrieve_labs: {str(e)}")
            return []

    def retrieve_medications(
        self,
        patient_id: str,
        query_keywords: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[StructuredClinicalResult]:
        try:
            q = self.db.query(Medication).filter(Medication.patient_id == patient_id)
            records = q.order_by(Medication.start_date.desc()).all()

            results: List[StructuredClinicalResult] = []
            for m in records:
                if query_keywords:
                    m_name = m.name.lower()
                    m_ind = (m.indication or "").lower()
                    if not any(k.lower() in m_name or k.lower() in m_ind for k in query_keywords):
                        continue

                content = (
                    f"Medication: {m.name} | Dosage: {m.dosage} {m.frequency} ({m.route}) | "
                    f"Status: {m.status.upper()} | Started: {m.start_date}"
                )
                if m.end_date:
                    content += f" | Ended: {m.end_date}"
                if m.indication:
                    content += f" | Indication: {m.indication}"
                if m.prescribing_doctor:
                    content += f" | Prescriber: {m.prescribing_doctor}"

                results.append(StructuredClinicalResult(
                    source_type="medication",
                    source_id=m.id,
                    report_id=m.source_report_id,
                    title=f"Rx: {m.name} {m.dosage}",
                    date=m.start_date,
                    content=content,
                    metadata={
                        "name": m.name,
                        "dosage": m.dosage,
                        "frequency": m.frequency,
                        "status": m.status,
                        "indication": m.indication
                    },
                    relevance_score=0.96 if m.status == "active" else 0.90
                ))

            return results[:limit]
        except Exception as e:
            logger.error(f"Error in retrieve_medications: {str(e)}")
            return []

    def retrieve_diagnoses(
        self,
        patient_id: str,
        limit: int = 10
    ) -> List[StructuredClinicalResult]:
        try:
            q = self.db.query(Disease).filter(Disease.patient_id == patient_id)
            records = q.order_by(Disease.diagnosed_date.desc()).all()

            results: List[StructuredClinicalResult] = []
            for d in records:
                content = f"Diagnosis: {d.name}"
                if d.icd_code:
                    content += f" (ICD: {d.icd_code})"
                content += f" | Status: {d.status.upper()} | Diagnosed: {d.diagnosed_date}"
                if d.treating_doctor:
                    content += f" | Doctor: {d.treating_doctor}"

                results.append(StructuredClinicalResult(
                    source_type="disease",
                    source_id=d.id,
                    report_id=d.source_report_id,
                    title=f"Dx: {d.name}",
                    date=d.diagnosed_date,
                    content=content,
                    metadata={
                        "name": d.name,
                        "icd_code": d.icd_code,
                        "status": d.status
                    },
                    relevance_score=0.95
                ))

            return results[:limit]
        except Exception as e:
            logger.error(f"Error in retrieve_diagnoses: {str(e)}")
            return []

    def retrieve_timeline(
        self,
        patient_id: str,
        limit: int = 10
    ) -> List[StructuredClinicalResult]:
        try:
            q = self.db.query(TimelineEvent).filter(TimelineEvent.patient_id == patient_id)
            records = q.order_by(TimelineEvent.date.desc()).all()

            results: List[StructuredClinicalResult] = []
            for t in records:
                content = (
                    f"Timeline Event ({t.year}): {t.title} | Type: {t.event_type.upper()} | "
                    f"Date: {t.date} | Details: {t.description}"
                )
                if t.facility:
                    content += f" | Facility: {t.facility}"

                results.append(StructuredClinicalResult(
                    source_type="timeline_event",
                    source_id=t.id,
                    report_id=t.source_report_id,
                    title=t.title,
                    date=t.date,
                    content=content,
                    metadata={
                        "year": t.year,
                        "event_type": t.event_type,
                        "severity": t.severity
                    },
                    relevance_score=0.92
                ))

            return results[:limit]
        except Exception as e:
            logger.error(f"Error in retrieve_timeline: {str(e)}")
            return []
