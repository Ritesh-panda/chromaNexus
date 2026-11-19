"""
Phase 6: Clinical Claim Extractor.
Decomposes candidate answers into granular, verifiable clinical claims
with explicit entity, value, unit, date, facility, and source attribution.
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set

from backend.app.clinical.verification.models import ClaimType, ClinicalClaim
from backend.app.clinical.terminology.biomarkers import resolve_biomarker, BIOMARKER_CATALOG


class ClaimExtractor:
    """
    Decomposes an LLM candidate response into individual material factual claims.
    Distinguishes lab measurements, diagnoses, medication instructions, narrative findings,
    and explicit missing-data statements.
    """

    KNOWN_CLINICAL_UNITS = {
        "x10^3/ul", "x10^6/ul", "x10^3", "x10^6", "k/ul", "m/ul",
        "meq/l", "mg/dl", "g/dl", "g/l", "mmol/l", "umol/l",
        "u/l", "iu/l", "pg", "fl", "%", "mcg", "mg", "g", "ml", "l",
        "uiu/ml", "ng/dl", "bpm", "mmhg"
    }

    MONTH_NAMES = {
        "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
        "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
        "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12
    }

    DIAGNOSIS_PATTERNS = [
        r"\b(?:diagnosed\s+with|diagnosis\s+of|confirmed\s+case\s+of|suffers?\s+from|condition\s+of)\s+([a-zA-Z0-9\s\-]{3,40}?)(?=[,.;]|\band\b|\bwith\b|\Z)",
        r"\b(?:you\s+have|patient\s+has)\s+([a-zA-Z0-9\s\-]{3,40}?\s+(?:diabetes|hypertension|disease|syndrome|carcinoma|infection|deficiency|failure|disorder|neuropathy|retinopathy|nephropathy))\b",
        r"\b([a-zA-Z0-9\s\-]{3,40}?\s+(?:diabetes|mellitus|hypertension|hyperlipidemia|disease|syndrome|disorder))\s*[-–—:]\s*(?:diagnosed|documented|recorded|active)",
        r"\b([a-zA-Z0-9\s\-]{3,40}?)\s+(?:was\s+diagnosed|diagnosed\s+on)\b"
    ]

    MEDICATION_INSTRUCTION_PATTERNS = [
        r"\b(?:take|taking|start|stop|increase|decrease|prescribed|prescription|dosage|dose|regimen)\b",
        r"\b(?:metformin|amoxicillin|atorvastatin|lisinopril|levothyroxine|amlodipine|omeprazole|losartan|gabapentin|hydrochlorothiazide|insulin|aspirin)\b",
        r"\b(?:tablets?|capsules?|mg\s+orally|twice\s+daily|once\s+daily|with\s+meals)\b"
    ]

    NEGATION_PATTERNS = [
        r"\b(?:no|not|without|denies|negative\s+for|ruled\s+out|unremarkable|intact|free\s+of|normal\s+limits)\b",
        r"\b(?:did\s+not\s+(?:show|reveal|demonstrate|indicate))\b"
    ]

    MISSING_DATA_PATTERNS = [
        r"\b(?:do|does|did)\s+not\s+(?:contain|include|mention|show|indicate)\b",
        r"\bno\s+(?:clinical\s+)?(?:records?|information|data|documentation|evidence|trace|mention)\b",
        r"\b(?:was|were|is|are)\s+not\s+(?:found|reported|documented|provided|available|present)\b",
        r"\bnot\s+found\s+in\s+(?:the\s+)?records?\b",
        r"\bcannot\s+(?:find|locate)\b"
    ]

    def extract_claims(self, text: str, candidate_citations: Optional[List[Dict[str, Any]]] = None) -> List[ClinicalClaim]:
        """
        Decomposes input text into granular ClinicalClaims with classified claim types.
        """
        if not text or not text.strip():
            return []

        raw_sentences = self._decompose_sentences(text)
        claims: List[ClinicalClaim] = []

        cand_facilities = set()
        cand_report_titles = set()
        if candidate_citations:
            for c in candidate_citations:
                if c.get("facility"):
                    cand_facilities.add(c.get("facility").lower().strip())
                if c.get("reportTitle"):
                    cand_report_titles.add(c.get("reportTitle").lower().strip())

        for sent in raw_sentences:
            claim = self._parse_single_claim(sent, cand_facilities, cand_report_titles)
            claims.append(claim)

        return claims

    def _decompose_sentences(self, text: str) -> List[str]:
        """
        Splits text by sentence boundaries, bullet points, and newlines, but also decomposes compound clauses
        joining supported factual claims with ungrounded medical claims.
        """
        split_sents = []
        # Pre-split on newlines and markdown list items so each distinct proposition is verified independently
        lines = re.split(r"\r?\n+", text)
        for line in lines:
            line_clean = line.strip().lstrip("-*•> ").strip()
            if not line_clean:
                continue

            for s in re.split(r"(?<=[.!?])\s+|;\s*", line_clean):
                s = s.strip()
                if not s:
                    continue

                # Split compound conjunctions where a secondary medical claim is appended
                subparts = re.split(
                    r"(?<=,)\s+(?:and\s+you|and\s+the\s+patient|and\s+were|and\s+was|and\s+have|and\s+has|and\s+should|but\s+you|but\s+the\s+patient)\s+",
                    s,
                    flags=re.IGNORECASE
                )
                if len(subparts) > 1:
                    p0 = subparts[0].rstrip(",").strip()
                    if p0:
                        split_sents.append(p0 + ".")
                    for sp in subparts[1:]:
                        sp_clean = sp.rstrip(".!?").strip()
                        if sp_clean:
                            if not sp_clean.lower().startswith(("you", "the patient", "patient")):
                                sp_clean = "You " + sp_clean
                            split_sents.append(sp_clean + ".")
                else:
                    split_sents.append(s)

        return split_sents

    def _parse_single_claim(
        self,
        sent: str,
        cand_facilities: Set[str],
        cand_report_titles: Set[str]
    ) -> ClinicalClaim:
        clean_text = re.sub(r"[*_#`]", "", sent).strip()
        sent_lower = clean_text.lower()

        # 1. Missing Data Check
        if any(re.search(pat, sent_lower) for pat in self.MISSING_DATA_PATTERNS):
            return ClinicalClaim(
                text=sent,
                claim_type=ClaimType.MISSING_DATA_STATEMENT
            )

        # 2. Medication Instruction Check
        has_drug = any(re.search(r"\b" + re.escape(d) + r"\b", sent_lower) for d in [
            "metformin", "amoxicillin", "atorvastatin", "lisinopril", "levothyroxine",
            "amlodipine", "omeprazole", "losartan", "gabapentin", "hydrochlorothiazide",
            "insulin", "aspirin", "antibiotic", "statin"
        ])
        has_action = any(re.search(r"\b" + re.escape(a) + r"\b", sent_lower) for a in [
            "take", "taking", "start", "stop", "increase", "decrease", "dose", "dosage", "prescribed", "modify", "adjust"
        ])
        is_generic_advisory = any(w in sent_lower for w in ["discuss", "consult", "doctor", "physician", "provider"])
        if has_drug and has_action and not is_generic_advisory:
            return ClinicalClaim(
                text=sent,
                claim_type=ClaimType.MEDICATION_INSTRUCTION
            )

        # 3. Diagnosis Check
        for pat in self.DIAGNOSIS_PATTERNS:
            m_diag = re.search(pat, sent_lower)
            if m_diag:
                diag_cand = m_diag.group(1).strip().strip("*_ \t")
                return ClinicalClaim(
                    text=sent,
                    claim_type=ClaimType.DIAGNOSIS,
                    analyte=diag_cand
                )

        for known_diag in ["type 2 diabetes", "diabetes mellitus", "diabetes", "hyperlipidemia", "hypertension"]:
            if known_diag in sent_lower:
                return ClinicalClaim(
                    text=sent,
                    claim_type=ClaimType.DIAGNOSIS,
                    analyte=known_diag
                )

        # 4. Dates & Years (Mask dates before extracting numeric lab values)
        full_dates = self._parse_full_dates(sent)
        date_str = f"{full_dates[0][0]:04d}-{full_dates[0][1]:02d}-{full_dates[0][2]:02d}" if full_dates else None

        date_mask_pat = (
            r"\b(19\d\d|20\d\d)[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b|"
            r"\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](19\d\d|20\d\d)\b|"
            r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(?:0?[1-9]|[12]\d|3[01]),?\s+(?:19\d\d|20\d\d)\b|"
            r"\b(?:0?[1-9]|[12]\d|3[01])\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*,?\s+(?:19\d\d|20\d\d)\b"
        )
        s_no_dates = re.sub(date_mask_pat, " ", sent, flags=re.IGNORECASE)
        s_no_years = re.sub(r"\b(19\d\d|20\d\d)\b", " ", s_no_dates)

        # 5. Extract Numbers
        # Mask duration / frequency / non-clinical lifestyle units so they are not mistaken for lab measurements
        duration_pat = r"\b(?:\d+(?:\s*-\s*\d+)?|\d+\.?\d*)\s*(?:minutes?|mins?|hours?|hrs?|seconds?|secs?|days?|weeks?|months?|years?|times?|steps?|sessions?|reps?|sets?)\b"
        s_no_durations = re.sub(duration_pat, " ", s_no_years, flags=re.IGNORECASE)
        s_no_ordinals = re.sub(r"\b(?:step|phase|section|option|tip|point|rule)\s+\d+\b", " ", s_no_durations, flags=re.IGNORECASE)
        nums = re.findall(r"\b(?:\d+\.\d+|\d+)\b", s_no_ordinals)

        # 6. Extract Units
        unit_tokens = re.findall(r"[a-z0-9%\^/]+", sent_lower)
        units_found = [tok for tok in unit_tokens if tok in self.KNOWN_CLINICAL_UNITS]
        unit_str = units_found[0] if units_found else None

        # 7. Extract Facility
        facility = self._extract_facility(sent, cand_facilities)

        # 8. Extract Attributed Source Title
        attributed_src = self._extract_attributed_source(sent, cand_report_titles)

        # 9. Extract Analyte (strip attributed source title so title words don't hijack analyte)
        sent_for_analyte = sent_lower
        if attributed_src:
            sent_for_analyte = sent_for_analyte.replace(attributed_src.lower(), " ")
        analyte_name = self._extract_analyte_name(sent_for_analyte)

        # 10. Extract Negation
        is_negated = any(re.search(pat, sent_lower) for pat in self.NEGATION_PATTERNS)

        # Determine Claim Type
        if any(w in sent_lower for w in ["conflict", "conflicting", "discrepanc", "highest", "lowest", "peak", "trend", "increased", "decreased", "stable", "history"]):
            claim_type = ClaimType.TEMPORAL_MEASUREMENT
        elif nums and analyte_name and (unit_str or any(re.search(r"\b" + re.escape(w) + r"\b", sent_lower) for w in ["was", "is", "level", "reading", "result", "measured", "value", "recorded", "documented"])):
            # Check if this sentence is purely general lifestyle/exercise advice rather than a patient lab measurement
            is_lifestyle_advice = any(w in sent_lower for w in [
                "exercise", "aerobic", "walking", "cycling", "swimming", "workout", "routine",
                "diet", "carbohydrate", "hydration", "drink", "water", "sleep", "rest", "lifestyle",
                "recommended", "aim for", "guidelines"
            ]) and not any(w in sent_lower for w in ["your latest", "your recorded", "result was", "level was", "reading was"])
            if is_lifestyle_advice:
                claim_type = ClaimType.GENERAL_STATEMENT
            else:
                claim_type = ClaimType.NUMERICAL_LAB
        elif any(w in sent_lower for w in ["tear", "effusion", "mri", "x-ray", "ct", "ultrasound", "scan", "findings", "degeneration", "intact"]):
            claim_type = ClaimType.NARRATIVE_FINDING
        else:
            claim_type = ClaimType.GENERAL_STATEMENT

        val_str = nums[0] if nums else None
        num_val = float(val_str) if val_str else None

        return ClinicalClaim(
            text=sent,
            claim_type=claim_type,
            analyte=analyte_name,
            value=val_str,
            numeric_value=num_val,
            unit=unit_str,
            test_date=date_str,
            facility=facility,
            attributed_source_title=attributed_src,
            is_negated=is_negated
        )

    def _extract_analyte_name(self, sent_lower: str) -> Optional[str]:
        # Check explicit measurement pattern: "[analyte] was/is/level/result <num>"
        m_direct = re.search(r"\b(?:your|my|the)?\s*([a-zA-Z\s]{3,25}?)\s*(?:is|was|level|reading|level was|of|result)\s*(?:[0-9]+(?:\.[0-9]+)?)", sent_lower)
        if m_direct:
            cand = m_direct.group(1).strip()
            if cand and cand not in {"records", "report", "lab", "test", "result", "doctor"}:
                res = resolve_biomarker(cand)
                if res:
                    return res.canonical_name
                # Also check common list
                for term, canonical in [
                    ("potassium", "Potassium, Serum"),
                    ("cholesterol", "Cholesterol, Total"),
                    ("glucose", "Glucose, Fasting Blood"),
                    ("troponin", "Troponin"),
                    ("hemoglobin", "Hemoglobin"),
                    ("creatinine", "Creatinine, Serum"),
                ]:
                    if term in cand:
                        return canonical

        # Multi-word aliases first
        common_analytes = [
            ("non-hdl cholesterol", "Non-HDL Cholesterol"),
            ("non-hdl", "Non-HDL Cholesterol"),
            ("ldl cholesterol", "Low-Density Lipoprotein (LDL) Cholesterol, Calculated"),
            ("ldl-c", "Low-Density Lipoprotein (LDL) Cholesterol, Calculated"),
            ("ldl", "Low-Density Lipoprotein (LDL) Cholesterol, Calculated"),
            ("hdl cholesterol", "High-Density Lipoprotein (HDL) Cholesterol"),
            ("hdl-c", "High-Density Lipoprotein (HDL) Cholesterol"),
            ("hdl", "High-Density Lipoprotein (HDL) Cholesterol"),
            ("triglycerides", "Triglycerides, Serum"),
            ("triglyceride", "Triglycerides, Serum"),
            ("total cholesterol", "Cholesterol, Total"),
            ("cholesterol", "Cholesterol, Total"),
            ("fasting blood sugar", "Glucose, Fasting Blood"),
            ("fasting glucose", "Glucose, Fasting Blood"),
            ("glucose", "Glucose, Fasting Blood"),
            ("potassium", "Potassium, Serum"),
            ("sodium", "Sodium, Serum"),
            ("hemoglobin a1c", "Hemoglobin A1c (HbA1c)"),
            ("hba1c", "Hemoglobin A1c (HbA1c)"),
            ("a1c", "Hemoglobin A1c (HbA1c)"),
            ("hemoglobin", "Hemoglobin"),
            ("creatinine", "Creatinine, Serum"),
            ("blood urea nitrogen", "Blood Urea Nitrogen (BUN)"),
            ("bun", "Blood Urea Nitrogen (BUN)"),
            ("platelets", "Platelet Count"),
            ("platelet", "Platelet Count"),
            ("white blood cells", "White Blood Cell Count (WBC)"),
            ("wbc", "White Blood Cell Count (WBC)"),
            ("tsh", "Thyroid Stimulating Hormone (TSH)"),
            ("uric acid", "Uric Acid"),
            ("troponin", "Troponin"),
        ]
        for term, canonical in common_analytes:
            if re.search(r"\b" + re.escape(term) + r"\b", sent_lower):
                return canonical

        # Check biomarker catalog synonyms
        for key, defn in BIOMARKER_CATALOG.items():
            for syn in defn.synonyms:
                if re.search(r"\b" + re.escape(syn.lower()) + r"\b", sent_lower):
                    return defn.canonical_name

        return None

    def _extract_facility(self, sent: str, cand_facilities: Set[str]) -> Optional[str]:
        sent_lower = sent.lower()
        for cf in cand_facilities:
            if cf in sent_lower:
                return cf.title()

        fac_match = re.search(r"\b(?:at|from)\s+([A-Za-z0-9\.\'\-]+(?:\s+[A-Za-z0-9\.\'\-]+){0,4}(?:\s+(?:Hospital|Clinic|Center|Health|Lab|Laboratory|System|Diagnostics))?)\b", sent, re.IGNORECASE)
        if fac_match:
            cand = fac_match.group(1).strip()
            if cand.lower() not in {"the comprehensive", "the complete", "the diagnostic", "the outpatient"}:
                return cand
        return None

    def _extract_attributed_source(self, sent: str, cand_titles: Set[str]) -> Optional[str]:
        sent_lower = sent.lower()
        for ct in cand_titles:
            clean_ct = ct.split("(")[0].strip()
            if clean_ct and len(clean_ct) > 3 and clean_ct in sent_lower:
                return ct.title()

        # Check explicit report phrases
        m_rep = re.search(r"\b(?:in|from|according\s+to|per)\s+(?:the\s+)?([A-Za-z0-9\s\-&]+?\s+(?:Report|Panel|Profile|Screening|Analysis|Summary))\b", sent, re.IGNORECASE)
        if m_rep:
            return m_rep.group(1).strip().title()

        return None

    @classmethod
    def _parse_full_dates(cls, text: str) -> List[Tuple[int, int, int]]:
        found = []
        if not text:
            return found
        # 1. ISO: YYYY-MM-DD
        for m in re.finditer(r"\b(19\d\d|20\d\d)[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b", text):
            found.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
        # 2. US: MM/DD/YYYY
        for m in re.finditer(r"\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](19\d\d|20\d\d)\b", text):
            found.append((int(m.group(3)), int(m.group(1)), int(m.group(2))))
        # 3. Month Day, Year
        for m in re.finditer(r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(0?[1-9]|[12]\d|3[01]),?\s+(19\d\d|20\d\d)\b", text, re.I):
            found.append((int(m.group(3)), cls.MONTH_NAMES[m.group(1).lower()], int(m.group(2))))
        # 4. Day Month Year
        for m in re.finditer(r"\b(0?[1-9]|[12]\d|3[01])\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?),?\s+(19\d\d|20\d\d)\b", text, re.I):
            found.append((int(m.group(3)), cls.MONTH_NAMES[m.group(2).lower()], int(m.group(1))))
        return found
