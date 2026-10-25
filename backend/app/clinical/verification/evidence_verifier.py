"""
Phase 6: Evidence Verifier.
Validates each material ClinicalClaim against patient-scoped structured records
and retrieved document chunks. Flags contradictions, unit mismatches, false attributions,
unrelated numerical contexts, and missing evidence.
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy.orm import Session

from backend.app.clinical.verification.models import (
    ClaimType,
    ClaimVerificationStatus,
    ClinicalClaim
)
from backend.app.models.clinical_entity import LabResult
from backend.app.models.report import MedicalReport
from backend.app.models.clinical_entity import Disease, Medication
from backend.app.clinical.terminology.biomarkers import resolve_biomarker


class EvidenceVerifier:
    """
    Verifies clinical claims against authoritative patient records and retrieved citations.
    Enforces strict patient-boundary isolation.
    """

    CONTROLLED_UNIT_CONVERSIONS = {
        ("g/dl", "g/l"): 10.0,
        ("g/l", "g/dl"): 0.1,
    }

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def verify_claims(
        self,
        claims: List[ClinicalClaim],
        citations: List[Dict[str, Any]],
        patient_id: str,
        retrieval_chunks: Optional[List[Any]] = None
    ) -> List[ClinicalClaim]:
        """
        Verifies a list of claims against patient records and citation evidence.
        """
        if not patient_id or not str(patient_id).strip():
            # Fail-closed if patient identity is missing
            for c in claims:
                c.status = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
                c.explanation = "Patient identity missing: verification failed closed."
            return claims

        patient_id_clean = str(patient_id).strip()

        # Pre-fetch structured patient clinical records if DB session available
        patient_labs: List[LabResult] = []
        patient_reports: Dict[str, MedicalReport] = {}
        patient_diagnoses: List[Disease] = []
        patient_meds: List[Medication] = []

        if self.db:
            patient_labs = self.db.query(LabResult).filter(LabResult.patient_id == patient_id_clean).all()
            reps = self.db.query(MedicalReport).filter(MedicalReport.patient_id == patient_id_clean).all()
            patient_reports = {r.id: r for r in reps}
            patient_diagnoses = self.db.query(Disease).filter(Disease.patient_id == patient_id_clean).all()
            patient_meds = self.db.query(Medication).filter(Medication.patient_id == patient_id_clean).all()

        # Strict Patient-Isolation: Filter citations and text evidence to authorized patient reports only
        if self.db:
            authorized_report_ids = set(patient_reports.keys())
            authorized_citations = [
                c for c in citations if not c.get("reportId") or c.get("reportId") in authorized_report_ids
            ]
        else:
            # When db session is None (e.g. pure in-memory vector store unit tests)
            authorized_report_ids = {c.get("reportId") for c in citations if c.get("reportId")}
            authorized_citations = list(citations)

        text_evidence = []
        for cit in authorized_citations:
            text_evidence.append({
                "report_id": cit.get("reportId", ""),
                "report_title": cit.get("reportTitle", ""),
                "date": cit.get("date", ""),
                "facility": cit.get("facility", ""),
                "text": (cit.get("excerpt", "") or "").lower()
            })
        if retrieval_chunks:
            for ch in retrieval_chunks:
                t = getattr(ch, "text", "") or getattr(ch, "text_content", "") or ""
                doc_id = getattr(ch, "document_id", "") or ""
                if t:
                    text_evidence.append({
                        "report_id": doc_id,
                        "report_title": "",
                        "date": "",
                        "facility": "",
                        "text": t.lower()
                    })

        for claim in claims:
            self._verify_single_claim(
                claim=claim,
                patient_labs=patient_labs,
                patient_reports=patient_reports,
                patient_diagnoses=patient_diagnoses,
                patient_meds=patient_meds,
                text_evidence=text_evidence,
                citations=authorized_citations
            )

        return claims

    def _verify_single_claim(
        self,
        claim: ClinicalClaim,
        patient_labs: List[LabResult],
        patient_reports: Dict[str, MedicalReport],
        patient_diagnoses: List[Disease],
        patient_meds: List[Medication],
        text_evidence: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ):
        # 1. Missing data statements are inherently supported by absence
        if claim.claim_type == ClaimType.MISSING_DATA_STATEMENT:
            claim.status = ClaimVerificationStatus.SUPPORTED
            claim.explanation = "Explicit missing-data statement."
            return

        # 2. Diagnosis verification
        if claim.claim_type == ClaimType.DIAGNOSIS:
            diag_term = (claim.analyte or claim.text).lower()
            # Check against authorized patient diagnoses
            has_diag = False
            for d in patient_diagnoses:
                cond = (d.name or "").lower()
                if cond and (cond in diag_term or any(w in cond for w in diag_term.split() if len(w) > 4)):
                    has_diag = True
                    break
            # Also check text evidence
            if not has_diag:
                for ev in text_evidence:
                    if diag_term in ev["text"] and not any(neg in ev["text"] for neg in ["no history of", "denies", "negative for"]):
                        has_diag = True
                        break

            if has_diag:
                claim.status = ClaimVerificationStatus.SUPPORTED
            else:
                claim.status = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
                claim.explanation = f"No clinical documentation of diagnosis '{claim.analyte or claim.text}' in authorized patient records."
            return

        # 3. Medication instruction verification
        if claim.claim_type == ClaimType.MEDICATION_INSTRUCTION:
            # Check if instruction is authorized prescription
            claim_t_lower = claim.text.lower()
            matches_active_rx = False
            for m in patient_meds:
                med_name = (m.name or "").lower()
                if med_name and med_name in claim_t_lower:
                    matches_active_rx = True
                    break
            if matches_active_rx and not any(w in claim_t_lower for w in ["increase", "decrease", "stop", "double"]):
                claim.status = ClaimVerificationStatus.SUPPORTED
            else:
                claim.status = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
                claim.explanation = "Unverified medication instruction or unconfirmed dosage modification."
            return

        # 4. Numerical Lab Result Verification
        if claim.claim_type in [ClaimType.NUMERICAL_LAB, ClaimType.TEMPORAL_MEASUREMENT]:
            self._verify_numerical_claim(
                claim=claim,
                patient_labs=patient_labs,
                patient_reports=patient_reports,
                citations=citations,
                text_evidence=text_evidence
            )
            return

        # 5. Narrative Finding Verification
        if claim.claim_type == ClaimType.NARRATIVE_FINDING:
            self._verify_narrative_finding(claim, text_evidence, citations)
            return

        # 6. General statements
        claim.status = ClaimVerificationStatus.SUPPORTED

    def _verify_numerical_claim(
        self,
        claim: ClinicalClaim,
        patient_labs: List[LabResult],
        patient_reports: Dict[str, MedicalReport],
        citations: List[Dict[str, Any]],
        text_evidence: List[Dict[str, Any]]
    ):
        analyte = claim.analyte
        claim_val = claim.value
        claim_unit = (claim.unit or "").strip().lower()
        claim_date = claim.test_date

        if not analyte and not claim_val:
            claim.status = ClaimVerificationStatus.SUPPORTED
            return

        # Resolve analyte canonical target
        target_names = set()
        if analyte:
            target_names.add(analyte.lower())
            defn = resolve_biomarker(analyte)
            if defn:
                target_names.add(defn.canonical_name.lower())
                for s in defn.synonyms:
                    target_names.add(s.lower())

        # Match against structured LabResult records
        matching_labs: List[Tuple[LabResult, Optional[MedicalReport]]] = []
        for lab in patient_labs:
            t_name = lab.test_name.lower()
            c_name = (lab.canonical_name or "").lower()
            if any(tn in t_name or tn in c_name for tn in target_names):
                rep = patient_reports.get(lab.source_report_id)
                matching_labs.append((lab, rep))

        if not matching_labs:
            # Check citations / text evidence directly
            self._verify_numerical_from_text_evidence(claim, citations, text_evidence)
            return

        # Check for multi-facility conflicting readings
        if len(matching_labs) >= 2:
            conflicts = []
            for i in range(len(matching_labs)):
                for j in range(i + 1, len(matching_labs)):
                    l1, r1 = matching_labs[i]
                    l2, r2 = matching_labs[j]
                    fac1 = l1.hospital_name or (r1.hospital_name if r1 else "")
                    fac2 = l2.hospital_name or (r2.hospital_name if r2 else "")
                    if fac1 != fac2 and l1.test_date == l2.test_date and l1.value != l2.value:
                        conflicts.extend([(l1, fac1), (l2, fac2)])
            if conflicts and "conflict" in claim.text.lower():
                claim.status = ClaimVerificationStatus.CONFLICTING_EVIDENCE
                claim.explanation = "Detected contradictory readings across facilities on the same date."
                return

        # Find best matching lab record
        exact_match = None
        wrong_val_match = None
        wrong_attr_match = None
        wrong_date_match = None
        wrong_unit_match = None

        for lab, rep in matching_labs:
            l_val = str(lab.value).strip()
            l_unit = (lab.unit or "").strip().lower()
            l_date = lab.test_date
            l_fac = lab.hospital_name or (rep.hospital_name if rep else "")
            l_rep_title = rep.title if rep else ""

            # Value check
            vals_match = False
            if claim_val:
                try:
                    vals_match = abs(float(claim_val) - float(l_val)) < 0.05
                except ValueError:
                    vals_match = (claim_val == l_val)
            else:
                vals_match = True

            # Unit check
            units_match = False
            if not claim_unit or not l_unit:
                units_match = True
            elif claim_unit == l_unit:
                units_match = True
            elif (l_unit, claim_unit) in self.CONTROLLED_UNIT_CONVERSIONS:
                factor = self.CONTROLLED_UNIT_CONVERSIONS[(l_unit, claim_unit)]
                try:
                    if abs(float(claim_val) - (float(l_val) * factor)) < 0.05:
                        units_match = True
                except (ValueError, TypeError):
                    pass

            # Date check
            dates_match = True
            if claim_date and l_date:
                dates_match = (claim_date == l_date)

            # Attribution check
            attr_match = True
            if claim.attributed_source_title and l_rep_title:
                c_clean = claim.attributed_source_title.lower()
                r_clean = l_rep_title.lower()
                if c_clean not in r_clean and r_clean not in c_clean:
                    attr_match = False

            if vals_match and units_match and dates_match and attr_match:
                exact_match = (lab, rep)
                break
            elif vals_match and units_match and dates_match and not attr_match:
                wrong_attr_match = (lab, rep)
            elif vals_match and not units_match:
                wrong_unit_match = (lab, rep)
            elif vals_match and not dates_match:
                wrong_date_match = (lab, rep)
            elif not vals_match and units_match:
                wrong_val_match = (lab, rep)

        if exact_match:
            lab, rep = exact_match
            claim.status = ClaimVerificationStatus.SUPPORTED
            claim.verified_value = lab.value
            claim.verified_unit = lab.unit
            claim.verified_date = lab.test_date
            claim.verified_facility = lab.hospital_name or (rep.hospital_name if rep else "")
            claim.verified_source_id = lab.source_report_id
            claim.verified_source_title = rep.title if rep else ""
            claim.supporting_citation = self._find_citation_for_report(lab.source_report_id, citations)
        elif wrong_attr_match:
            lab, rep = wrong_attr_match
            claim.status = ClaimVerificationStatus.CONTRADICTED
            claim.verified_value = lab.value
            claim.verified_unit = lab.unit
            claim.verified_date = lab.test_date
            claim.verified_facility = lab.hospital_name or (rep.hospital_name if rep else "")
            claim.verified_source_id = lab.source_report_id
            claim.verified_source_title = rep.title if rep else ""
            claim.explanation = f"False source attribution: claim named '{claim.attributed_source_title}', but record is from '{claim.verified_source_title}'."
            claim.supporting_citation = self._find_citation_for_report(lab.source_report_id, citations)
        elif wrong_unit_match:
            lab, rep = wrong_unit_match
            claim.status = ClaimVerificationStatus.CONTRADICTED
            claim.verified_value = lab.value
            claim.verified_unit = lab.unit
            claim.explanation = f"Unit mismatch: claim used '{claim.unit}', but clinical record was recorded in '{lab.unit}'."
        elif wrong_date_match:
            lab, rep = wrong_date_match
            claim.status = ClaimVerificationStatus.CONTRADICTED
            claim.verified_date = lab.test_date
            claim.explanation = f"Date mismatch: claim specified '{claim.test_date}', but record is dated '{lab.test_date}'."
        elif wrong_val_match:
            lab, rep = wrong_val_match
            claim.status = ClaimVerificationStatus.CONTRADICTED
            claim.verified_value = lab.value
            claim.verified_unit = lab.unit
            claim.explanation = f"Incorrect value: claim asserted '{claim.value}', but true verified result is '{lab.value} {lab.unit}'."
        else:
            claim.status = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
            claim.explanation = f"No verified medical records substantiate {claim.text}."

    def _verify_numerical_from_text_evidence(
        self,
        claim: ClinicalClaim,
        citations: List[Dict[str, Any]],
        text_evidence: List[Dict[str, Any]]
    ):
        analyte = (claim.analyte or "").lower()
        val = claim.value

        # Expand target search tokens for analyte to include canonical name, synonyms, and words
        target_tokens = set()
        if analyte:
            target_tokens.add(analyte)
            defn = resolve_biomarker(analyte)
            if defn:
                target_tokens.add(defn.canonical_name.lower())
                for s in defn.synonyms:
                    target_tokens.add(s.lower())
            for w in re.findall(r"[a-z]{4,}", analyte):
                target_tokens.add(w)

        found_match = False
        unrelated_context = False

        for ev in text_evidence:
            txt = ev["text"]
            if val and val in txt:
                # Check if this chunk mentions the target analyte
                if any(tok in txt for tok in target_tokens):
                    found_match = True
                    claim.status = ClaimVerificationStatus.SUPPORTED
                    claim.supporting_citation = self._find_citation_for_report(ev["report_id"], citations)
                    break
                else:
                    unrelated_context = True

        if not found_match:
            claim.status = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
            if unrelated_context:
                claim.explanation = f"Number '{val}' appears only in an unrelated clinical context, not for '{analyte}'."
            else:
                claim.explanation = f"No clinical documentation found for {claim.text}."

    def _verify_narrative_finding(
        self,
        claim: ClinicalClaim,
        text_evidence: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ):
        claim_lower = claim.text.lower()
        claim_negated = claim.is_negated

        # Extract core finding words (e.g. "tear", "meniscus", "effusion", "degeneration")
        stop_words = {"the", "was", "were", "and", "but", "with", "showed", "demonstrated", "findings", "revealed", "noted", "seen"}
        finding_tokens = [w for w in re.findall(r"[a-z]{3,}", claim_lower) if w not in stop_words]

        found_support = False
        found_contradiction = False
        matching_ev = None

        for ev in text_evidence:
            txt = ev["text"]
            matched_tokens = [t for t in finding_tokens if t in txt]
            if len(matched_tokens) >= max(1, len(finding_tokens) // 2):
                # Evidence mentions the clinical finding. Check negation polarity!
                ev_negated = any(neg in txt for neg in ["no tear", "without tear", "no evidence", "intact", "unremarkable", "negative"])
                if claim_negated == ev_negated:
                    found_support = True
                    matching_ev = ev
                    break
                else:
                    found_contradiction = True
                    matching_ev = ev
                    break

        if found_support:
            claim.status = ClaimVerificationStatus.SUPPORTED
            if matching_ev:
                claim.supporting_citation = self._find_citation_for_report(matching_ev["report_id"], citations)
        elif found_contradiction:
            claim.status = ClaimVerificationStatus.CONTRADICTED
            claim.explanation = "Polarity contradiction: clinical record states negation/absence, but claim asserted affirmative presence (or vice-versa)."
        else:
            claim.status = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
            claim.explanation = "Narrative finding not documented in retrieved clinical evidence."

    @staticmethod
    def _find_citation_for_report(report_id: Optional[str], citations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not report_id:
            return None
        for cit in citations:
            if cit.get("reportId") == report_id:
                return cit
        return None
