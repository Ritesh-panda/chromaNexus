import re
from typing import List, Dict, Any, Optional
from backend.app.ai.clinical_extractor.base import ClinicalEntityExtractor
from backend.app.ai.clinical_extractor.models import ExtractedClinicalEntity
from backend.app.ai.clinical_extractor.validator import ClinicalDataValidator
from backend.app.ai.extractors.pdf_extractor import ExtractedPage


class RuleBasedClinicalExtractor(ClinicalEntityExtractor):
    """
    Deterministic clinical entity extraction using regular expressions and clinical terminology catalogs.
    Preserves exact provenance (document ID, page number, context excerpt).
    """

    # Clinical Lab Patterns: name, regex for value + unit
    LAB_PATTERNS = [
        (
            "Total Cholesterol",
            r"(?:Total\s+Cholesterol|Cholesterol,?\s*Total)[:\s]+([\d\.]+)\s*(mg/dL|mmol/L)?",
            "mg/dL",
            "<200 mg/dL"
        ),
        (
            "HbA1c",
            r"(?:HbA1c|Hemoglobin\s+A1c|Glycated\s+Hemoglobin)[:\s]+([\d\.]+)\s*(%)?",
            "%",
            "4.0 - 5.6%"
        ),
        (
            "Fasting Blood Glucose",
            r"(?:Fasting\s+(?:Plasma\s+)?Glucose|Fasting\s+Blood\s+Sugar|FBS)[:\s]+([\d\.]+)\s*(mg/dL|mmol/L)?",
            "mg/dL",
            "70 - 99 mg/dL"
        ),
        (
            "LDL Cholesterol",
            r"(?:LDL\s+Cholesterol|LDL-C)[:\s]+([\d\.]+)\s*(mg/dL|mmol/L)?",
            "mg/dL",
            "<100 mg/dL"
        ),
        (
            "HDL Cholesterol",
            r"(?:HDL\s+Cholesterol|HDL-C)[:\s]+([\d\.]+)\s*(mg/dL|mmol/L)?",
            "mg/dL",
            ">40 mg/dL"
        ),
        (
            "Platelet Count",
            r"(?:Platelet\s+Count|Platelets)[:\s]+([\d,]+)\s*(/cumm|cells/mcL|k/uL)?",
            "cells/mcL",
            "150,000 - 450,000"
        ),
        (
            "Resting Blood Pressure",
            r"(?:Blood\s+Pressure|BP|Resting\s+BP)[:\s]+(\d{2,3}/\d{2,3})\s*(mmHg)?",
            "mmHg",
            "<120/80 mmHg"
        ),
        (
            "Serum Creatinine",
            r"(?:Serum\s+Creatinine|Creatinine)[:\s]+([\d\.]+)\s*(mg/dL|umol/L)?",
            "mg/dL",
            "0.7 - 1.3 mg/dL"
        ),
        (
            "Vitamin D (25-OH)",
            r"(?:Vitamin\s+D|25-OH\s+Vitamin\s+D)[:\s]+([\d\.]+)\s*(ng/mL|nmol/L)?",
            "ng/mL",
            "30 - 100 ng/mL"
        )
    ]

    # Medication Patterns: name, dosage regex
    MEDICATION_PATTERNS = [
        ("Metformin", r"\bMetformin(?:\s+HCl)?\s+(\d+\s*(?:mg|g))\s*(BID|TID|QD|once daily|twice daily)?\b"),
        ("Lisinopril", r"\bLisinopril\s+(\d+\s*(?:mg))\s*(QD|BID|once daily|daily)?\b"),
        ("Atorvastatin", r"\bAtorvastatin(?:\s+Calcium)?\s+(\d+\s*(?:mg))\s*(QD|at bedtime|once daily)?\b"),
        ("Cholecalciferol", r"\b(?:Cholecalciferol|Vitamin\s+D3)\s+(\d+[\d,]*\s*(?:IU|mcg))\s*(weekly|QD|daily)?\b"),
        ("Amlodipine", r"\bAmlodipine\s+(\d+\s*(?:mg))\s*(QD|once daily)?\b"),
        ("Omeprazole", r"\bOmeprazole\s+(\d+\s*(?:mg))\s*(QD|before breakfast)?\b")
    ]

    # Disease Patterns: name, ICD code, regex keywords
    DISEASE_PATTERNS = [
        ("Type 2 Diabetes Mellitus", "E11.9", [r"\b(?:Type\s+2\s+Diabetes(?:\s+Mellitus)?|T2DM)\b"]),
        ("Essential (Primary) Hypertension", "I10", [r"\b(?:Essential\s+(?:primary\s+)?hypertension|HTN|Hypertension)\b"]),
        ("Hyperlipidemia", "E78.5", [r"\b(?:Hyperlipidemia|Hypercholesterolemia|Dyslipidemia)\b"]),
        ("Dengue Hemorrhagic Fever", "A91", [r"\b(?:Dengue(?:\s+Hemorrhagic)?\s+Fever)\b"]),
        ("Medial Meniscus Degenerative Alteration", "M23.2", [r"\b(?:meniscus\s+(?:tear|degeneration|signal\s+alteration))\b"]),
        ("Vitamin D Deficiency", "E55.9", [r"\b(?:Vitamin\s+D\s+Deficiency)\b"])
    ]

    # Procedure Patterns
    PROCEDURE_PATTERNS = [
        ("3.0T MRI Right Knee Joint", r"\b(?:MRI\s+(?:of\s+)?(?:Right\s+)?Knee(?:\s+Joint)?)\b"),
        ("Echocardiogram (2D Echo)", r"\b(?:Echocardiogram|2D\s+Echo|Echocardiography)\b"),
        ("Inpatient Hospitalization & Platelet Monitoring", r"\b(?:Inpatient\s+stay|Hospital\s+admission|Hospitalization)\b")
    ]

    def extract_entities(
        self,
        text: str,
        document_id: str,
        pages: Optional[List[ExtractedPage]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ExtractedClinicalEntity]:
        entities: List[ExtractedClinicalEntity] = []
        doc_pages = pages or [ExtractedPage(page_number=1, text=text, character_count=len(text))]

        for page in doc_pages:
            p_text = page.text
            p_num = page.page_number
            if not p_text.strip():
                continue

            # 1. Extract Labs
            for lab_name, pattern, default_unit, ref_range in self.LAB_PATTERNS:
                for match in re.finditer(pattern, p_text, re.IGNORECASE):
                    val_str = match.group(1).replace(",", "")
                    unit_str = match.group(2) or default_unit
                    
                    validated = ClinicalDataValidator.validate_lab_result(
                        test_name=lab_name,
                        value_str=val_str,
                        unit_str=unit_str,
                        reference_range=ref_range
                    )

                    if validated.is_valid:
                        start_pos = max(0, match.start() - 30)
                        end_pos = min(len(p_text), match.end() + 30)
                        excerpt = p_text[start_pos:end_pos].strip()

                        entities.append(ExtractedClinicalEntity(
                            category="lab_value",
                            name=lab_name,
                            value=validated.value,
                            unit=validated.unit,
                            confidence=0.98,
                            source_document_id=document_id,
                            page_number=p_num,
                            excerpt=excerpt,
                            extraction_method="rule_based",
                            metadata={"reference_range": ref_range, "status": validated.status}
                        ))

            # 2. Extract Medications
            for med_name, pattern in self.MEDICATION_PATTERNS:
                for match in re.finditer(pattern, p_text, re.IGNORECASE):
                    dosage_str = match.group(1) if match.lastindex and match.lastindex >= 1 else ""
                    freq_str = match.group(2) if match.lastindex and match.lastindex >= 2 else "Daily"

                    validated = ClinicalDataValidator.validate_medication(
                        name=med_name,
                        dosage=dosage_str,
                        frequency=freq_str or "Daily"
                    )

                    if validated.is_valid:
                        start_pos = max(0, match.start() - 25)
                        end_pos = min(len(p_text), match.end() + 25)
                        excerpt = p_text[start_pos:end_pos].strip()

                        entities.append(ExtractedClinicalEntity(
                            category="medication",
                            name=med_name,
                            value=validated.dosage,
                            unit=validated.frequency,
                            confidence=0.97,
                            source_document_id=document_id,
                            page_number=p_num,
                            excerpt=excerpt,
                            extraction_method="rule_based",
                            metadata={"route": validated.route}
                        ))

            # 3. Extract Diseases
            for disease_name, icd_code, regex_list in self.DISEASE_PATTERNS:
                for pat in regex_list:
                    match = re.search(pat, p_text, re.IGNORECASE)
                    if match:
                        start_pos = max(0, match.start() - 30)
                        end_pos = min(len(p_text), match.end() + 30)
                        excerpt = p_text[start_pos:end_pos].strip()

                        entities.append(ExtractedClinicalEntity(
                            category="disease",
                            name=disease_name,
                            value=icd_code,
                            unit=None,
                            confidence=0.96,
                            source_document_id=document_id,
                            page_number=p_num,
                            excerpt=excerpt,
                            extraction_method="rule_based",
                            metadata={"icd_code": icd_code}
                        ))
                        break  # Match once per page

            # 4. Extract Procedures / Imaging
            for proc_name, pat in self.PROCEDURE_PATTERNS:
                match = re.search(pat, p_text, re.IGNORECASE)
                if match:
                    start_pos = max(0, match.start() - 30)
                    end_pos = min(len(p_text), match.end() + 30)
                    excerpt = p_text[start_pos:end_pos].strip()

                    entities.append(ExtractedClinicalEntity(
                        category="procedure",
                        name=proc_name,
                        value="completed",
                        unit=None,
                        confidence=0.95,
                        source_document_id=document_id,
                        page_number=p_num,
                        excerpt=excerpt,
                        extraction_method="rule_based"
                    ))

        return entities
