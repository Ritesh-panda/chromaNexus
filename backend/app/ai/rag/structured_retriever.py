import logging
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.models.clinical_entity import LabResult, Medication, Disease
from backend.app.models.allergy import Allergy
from backend.app.models.patient import Patient
from backend.app.models.timeline import TimelineEvent
from backend.app.models.report import MedicalReport
from backend.app.clinical.terminology.biomarkers import resolve_biomarker
from backend.app.clinical.terminology.allergies import check_drug_allergy_conflict, find_drug_class

logger = logging.getLogger(__name__)


class StructuredClinicalResult(BaseModel):
    """
    Standard container for structured clinical data retrieved directly from relational DB tables.
    """
    source_type: str  # 'lab_result' | 'medication' | 'disease' | 'allergy' | 'timeline_event' | 'medical_report'
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
    Never relies on fuzzy embeddings for exact numbers, dates, drug dosages, or allergy alerts.
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
            
            # Pre-resolve query keywords to biomarker definitions if possible
            target_loincs = set()
            if query_keywords:
                for kw in query_keywords:
                    defn = resolve_biomarker(kw)
                    if defn:
                        target_loincs.add(defn.loinc_code)

            for r in records:
                # If keywords provided, filter via substring or canonical LOINC match
                if query_keywords:
                    t_name = r.test_name.lower()
                    direct_match = any(k.lower() in t_name for k in query_keywords)
                    
                    # LOINC-based match
                    loinc_match = False
                    if r.loinc_code and r.loinc_code in target_loincs:
                        loinc_match = True
                    else:
                        r_defn = resolve_biomarker(r.test_name)
                        if r_defn and r_defn.loinc_code in target_loincs:
                            loinc_match = True

                    if not (direct_match or loinc_match):
                        continue

                loinc_str = f" (LOINC: {r.loinc_code})" if getattr(r, "loinc_code", None) else ""
                content = (
                    f"Test: {r.test_name}{loinc_str} | Value: {r.value} {r.unit} "
                    f"(Ref: {r.reference_range}) | Status: {r.status.upper()} | Date: {r.test_date}"
                )
                if r.hospital_name:
                    content += f" | Facility: {r.hospital_name}"

                meta = {
                    "test_name": r.test_name,
                    "value": r.value,
                    "unit": r.unit,
                    "status": r.status,
                    "hospital": r.hospital_name,
                    "loinc_code": getattr(r, "loinc_code", None),
                    "canonical_name": getattr(r, "canonical_name", None),
                    "source_page_number": getattr(r, "source_page_number", None),
                    "extraction_confidence": getattr(r, "extraction_confidence", 0.95),
                    "bounding_box": getattr(r, "bounding_box", None),
                }

                results.append(StructuredClinicalResult(
                    source_type="lab_result",
                    source_id=r.id,
                    report_id=r.source_report_id,
                    title=f"Lab: {r.test_name}",
                    date=r.test_date,
                    content=content,
                    metadata=meta,
                    relevance_score=0.96 if r.status in ["high", "low", "critical"] else 0.95
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

                drug_class_str = f" [{m.drug_class}]" if getattr(m, "drug_class", None) else ""
                content = (
                    f"Medication: {m.name}{drug_class_str} | Dosage: {m.dosage} {m.frequency} ({m.route}) | "
                    f"Status: {m.status.upper()} | Started: {m.start_date}"
                )
                if m.end_date:
                    content += f" | Ended: {m.end_date}"
                if m.indication:
                    content += f" | Indication: {m.indication}"
                if m.prescribing_doctor:
                    content += f" | Prescriber: {m.prescribing_doctor}"

                meta = {
                    "name": m.name,
                    "dosage": m.dosage,
                    "frequency": m.frequency,
                    "status": m.status,
                    "indication": m.indication,
                    "drug_class": getattr(m, "drug_class", None),
                    "rxnorm_code": getattr(m, "rxnorm_code", None),
                    "source_page_number": getattr(m, "source_page_number", None),
                    "extraction_confidence": getattr(m, "extraction_confidence", 0.95),
                    "bounding_box": getattr(m, "bounding_box", None),
                }

                results.append(StructuredClinicalResult(
                    source_type="medication",
                    source_id=m.id,
                    report_id=m.source_report_id,
                    title=f"Rx: {m.name} {m.dosage}",
                    date=m.start_date,
                    content=content,
                    metadata=meta,
                    relevance_score=0.96 if m.status == "active" else 0.90
                ))

            return results[:limit]
        except Exception as e:
            logger.error(f"Error in retrieve_medications: {str(e)}")
            return []

    def retrieve_allergies(
        self,
        patient_id: str,
        query_keywords: Optional[List[str]] = None,
        query_text: Optional[str] = None,
        limit: int = 10
    ) -> List[StructuredClinicalResult]:
        """
        Retrieves patient allergies and evaluates potential drug contraindications / cross-reactivities.
        """
        try:
            results: List[StructuredClinicalResult] = []

            # 1. Query structured Allergy table (primary source of truth)
            records = self.db.query(Allergy).filter(Allergy.patient_id == patient_id).all()
            
            # Active allergies used for conflict checking
            active_records = [a for a in records if (a.status or "active").lower() == "active"]
            allergy_names = [a.allergen for a in active_records]

            # 2. Unify with patient.known_allergies to prevent source-of-truth divergence
            patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
            if patient and patient.known_allergies:
                legacy_list = []
                if isinstance(patient.known_allergies, list):
                    legacy_list = [str(x) for x in patient.known_allergies if x]
                elif isinstance(patient.known_allergies, str) and patient.known_allergies.strip():
                    legacy_list = [patient.known_allergies.strip()]
                
                # Append legacy allergens not already represented in structured active allergies
                existing_lower = {a.lower() for a in allergy_names}
                for leg in legacy_list:
                    leg_clean = leg.split("(")[0].strip()
                    if leg_clean.lower() not in existing_lower:
                        allergy_names.append(leg)
                        existing_lower.add(leg_clean.lower())

            # Extract words from query for conflict checking
            full_query_str = (query_text or "") + " " + " ".join(query_keywords or [])
            stopwords = {"i", "a", "an", "the", "can", "for", "my", "to", "take", "do", "is", "in", "of", "and", "or", "what", "be", "am", "are", "on", "at", "by", "with"}
            query_words = [w for w in re.findall(r"\b[a-z0-9\-]+\b", full_query_str.lower()) if len(w) >= 3 and w not in stopwords]

            # 3. Check for specific drug-allergy conflict / cross-reactivity
            detected_conflict = None
            for word in query_words:
                conflict = check_drug_allergy_conflict(word, allergy_names)
                if conflict:
                    detected_conflict = conflict
                    break

            # If conflict detected, inject high-priority clinical safety alert at index 0
            if detected_conflict:
                cand_name = detected_conflict['candidate_drug'].capitalize()
                alert_content = (
                    f"CLINICAL SAFETY ALERT (POTENTIAL CROSS-REACTIVITY): Recorded patient profile indicates an allergy to "
                    f"'{detected_conflict['allergen']}'. Candidate medication '{cand_name}'. "
                    f"{detected_conflict['explanation']}"
                )

                results.append(StructuredClinicalResult(
                    source_type="allergy",
                    source_id="alert_contraindication",
                    report_id=None,
                    title=f"CLINICAL SAFETY ALERT: Potential Cross-Reactivity ({cand_name})",
                    date="CURRENT_SAFETY_PROFILE",
                    content=alert_content,
                    metadata={
                        "conflict": detected_conflict,
                        "candidate_drug": detected_conflict["candidate_drug"],
                        "allergen": detected_conflict["allergen"],
                        "severity": detected_conflict.get("severity", "severe"),
                        "is_definitive_decision": False,
                        "requires_clinical_review": True,
                    },
                    relevance_score=0.99  # Absolute highest priority to safeguard patient
                ))

            # 4. Add structured allergy records
            for a in records:
                reaction_str = f" (Reaction: {a.reaction})" if a.reaction else ""
                classes_str = f" [Class: {', '.join(a.drug_classes)}]" if a.drug_classes else ""
                content = (
                    f"Documented Allergy: {a.allergen} | Severity: {a.severity.upper()}{reaction_str}{classes_str} | "
                    f"Category: {a.category.upper()} | Status: {a.status.upper()}"
                )
                results.append(StructuredClinicalResult(
                    source_type="allergy",
                    source_id=a.id,
                    report_id=a.source_report_id,
                    title=f"Allergy: {a.allergen}",
                    date="ACTIVE",
                    content=content,
                    metadata={
                        "allergen": a.allergen,
                        "severity": a.severity,
                        "reaction": a.reaction,
                        "drug_classes": a.drug_classes,
                        "cross_reactivities": a.cross_reactivities,
                        "source_page_number": a.source_page_number,
                        "extraction_confidence": a.extraction_confidence,
                    },
                    relevance_score=0.97
                ))

            # 5. If only legacy patient.known_allergies were present, format them
            if not records and allergy_names:
                for idx, al_str in enumerate(allergy_names):
                    results.append(StructuredClinicalResult(
                        source_type="allergy",
                        source_id=f"legacy_allergy_{idx}",
                        report_id=None,
                        title=f"Allergy: {al_str}",
                        date="ACTIVE",
                        content=f"Documented Allergy Profile: {al_str} (Verified Patient Record)",
                        metadata={"allergen": al_str},
                        relevance_score=0.97
                    ))

            return results[:limit]
        except Exception as e:
            logger.error(f"Error in retrieve_allergies: {str(e)}")
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

                meta = {
                    "name": d.name,
                    "icd_code": d.icd_code,
                    "status": d.status,
                    "source_page_number": getattr(d, "source_page_number", None),
                    "extraction_confidence": getattr(d, "extraction_confidence", 0.95),
                    "bounding_box": getattr(d, "bounding_box", None),
                }

                results.append(StructuredClinicalResult(
                    source_type="disease",
                    source_id=d.id,
                    report_id=d.source_report_id,
                    title=f"Dx: {d.name}",
                    date=d.diagnosed_date,
                    content=content,
                    metadata=meta,
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
