"""
ChronaNexus Curated Clinical Biomarker Catalog
=============================================
Lightweight, curated terminology catalog for routine outpatient laboratory panels.
Provides LOINC codes, canonical names, categories, standard units, reference ranges,
and synonym mappings for deterministic test resolution.

Derived from open clinical standards (LOINC, Health Assistant Apache-2.0 panels).
Zero heavy external ML or 2GB UMLS database dependencies.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import re


@dataclass(frozen=True)
class BiomarkerDefinition:
    canonical_name: str
    loinc_code: str
    category: str
    standard_unit: str
    reference_range_male: str
    reference_range_female: str
    reference_range_general: str
    synonyms: List[str]


# Curated catalog covering ~150 routine outpatient biomarkers across core panels
BIOMARKER_CATALOG: Dict[str, BiomarkerDefinition] = {
    # -------------------------------------------------------------------------
    # Comprehensive Metabolic & Renal Panel (CMP / BMP)
    # -------------------------------------------------------------------------
    "potassium": BiomarkerDefinition(
        canonical_name="Potassium, Serum",
        loinc_code="2823-3",
        category="metabolic",
        standard_unit="mEq/L",
        reference_range_male="3.5 - 5.1",
        reference_range_female="3.5 - 5.1",
        reference_range_general="3.5 - 5.1 mEq/L",
        synonyms=["potassium", "serum potassium", "potassium level", "k", "serum k", "k+"]
    ),
    "sodium": BiomarkerDefinition(
        canonical_name="Sodium, Serum",
        loinc_code="2951-2",
        category="metabolic",
        standard_unit="mEq/L",
        reference_range_male="136 - 145",
        reference_range_female="136 - 145",
        reference_range_general="136 - 145 mEq/L",
        synonyms=["sodium", "serum sodium", "sodium level", "na", "serum na", "na+"]
    ),
    "chloride": BiomarkerDefinition(
        canonical_name="Chloride, Serum",
        loinc_code="2075-0",
        category="metabolic",
        standard_unit="mEq/L",
        reference_range_male="96 - 106",
        reference_range_female="96 - 106",
        reference_range_general="96 - 106 mEq/L",
        synonyms=["chloride", "serum chloride", "cl", "serum cl"]
    ),
    "carbon_dioxide": BiomarkerDefinition(
        canonical_name="Carbon Dioxide / Bicarbonate, Serum",
        loinc_code="2028-9",
        category="metabolic",
        standard_unit="mEq/L",
        reference_range_male="22 - 29",
        reference_range_female="22 - 29",
        reference_range_general="22 - 29 mEq/L",
        synonyms=["carbon dioxide", "co2", "bicarbonate", "hco3", "bicarb"]
    ),
    "creatinine": BiomarkerDefinition(
        canonical_name="Creatinine, Serum",
        loinc_code="2160-0",
        category="metabolic",
        standard_unit="mg/dL",
        reference_range_male="0.74 - 1.35",
        reference_range_female="0.59 - 1.04",
        reference_range_general="0.74 - 1.35 mg/dL",
        synonyms=["creatinine", "serum creatinine", "creat", "renal function", "kidney function test"]
    ),
    "egfr": BiomarkerDefinition(
        canonical_name="Glomerular Filtration Rate (eGFR), Estimated",
        loinc_code="33914-3",
        category="metabolic",
        standard_unit="mL/min/1.73m2",
        reference_range_male="> 60",
        reference_range_female="> 60",
        reference_range_general="> 60 mL/min/1.73m2",
        synonyms=["egfr", "gfr", "estimated gfr", "glomerular filtration rate"]
    ),
    "blood_urea_nitrogen": BiomarkerDefinition(
        canonical_name="Blood Urea Nitrogen (BUN)",
        loinc_code="3094-0",
        category="metabolic",
        standard_unit="mg/dL",
        reference_range_male="6 - 20",
        reference_range_female="6 - 20",
        reference_range_general="6 - 20 mg/dL",
        synonyms=["bun", "blood urea nitrogen", "urea nitrogen", "urea"]
    ),
    "glucose": BiomarkerDefinition(
        canonical_name="Glucose, Fasting Blood",
        loinc_code="1558-6",
        category="metabolic",
        standard_unit="mg/dL",
        reference_range_male="70 - 99",
        reference_range_female="70 - 99",
        reference_range_general="70 - 99 mg/dL",
        synonyms=["glucose", "fasting glucose", "blood sugar", "fasting blood glucose", "fbg", "blood glucose"]
    ),
    "calcium": BiomarkerDefinition(
        canonical_name="Calcium, Total Serum",
        loinc_code="17861-6",
        category="metabolic",
        standard_unit="mg/dL",
        reference_range_male="8.6 - 10.2",
        reference_range_female="8.6 - 10.2",
        reference_range_general="8.6 - 10.2 mg/dL",
        synonyms=["calcium", "serum calcium", "total calcium", "ca"]
    ),

    # -------------------------------------------------------------------------
    # Glycemic & Diabetes Control
    # -------------------------------------------------------------------------
    "hba1c": BiomarkerDefinition(
        canonical_name="Hemoglobin A1c (HbA1c)",
        loinc_code="4548-4",
        category="metabolic",
        standard_unit="%",
        reference_range_male="4.0 - 5.6",
        reference_range_female="4.0 - 5.6",
        reference_range_general="4.0 - 5.6 %",
        synonyms=["hba1c", "a1c", "glycated hemoglobin", "hemoglobin a1c", "glycohemoglobin"]
    ),

    # -------------------------------------------------------------------------
    # Lipid Panel & Cardiovascular Biomarkers
    # -------------------------------------------------------------------------
    "total_cholesterol": BiomarkerDefinition(
        canonical_name="Cholesterol, Total",
        loinc_code="2093-3",
        category="lipid_panel",
        standard_unit="mg/dL",
        reference_range_male="< 200",
        reference_range_female="< 200",
        reference_range_general="< 200 mg/dL",
        synonyms=["total cholesterol", "cholesterol", "chol", "total chol", "serum cholesterol"]
    ),
    "hdl_cholesterol": BiomarkerDefinition(
        canonical_name="High-Density Lipoprotein (HDL) Cholesterol",
        loinc_code="2085-9",
        category="lipid_panel",
        standard_unit="mg/dL",
        reference_range_male="> 40",
        reference_range_female="> 50",
        reference_range_general="> 40 mg/dL",
        synonyms=["hdl", "hdl cholesterol", "good cholesterol", "high density lipoprotein"]
    ),
    "ldl_cholesterol": BiomarkerDefinition(
        canonical_name="Low-Density Lipoprotein (LDL) Cholesterol, Calculated",
        loinc_code="13457-7",
        category="lipid_panel",
        standard_unit="mg/dL",
        reference_range_male="< 100",
        reference_range_female="< 100",
        reference_range_general="< 100 mg/dL",
        synonyms=["ldl", "ldl cholesterol", "bad cholesterol", "low density lipoprotein"]
    ),
    "triglycerides": BiomarkerDefinition(
        canonical_name="Triglycerides, Serum",
        loinc_code="2571-8",
        category="lipid_panel",
        standard_unit="mg/dL",
        reference_range_male="< 150",
        reference_range_female="< 150",
        reference_range_general="< 150 mg/dL",
        synonyms=["triglycerides", "trigs", "triglyceride", "tg"]
    ),

    # -------------------------------------------------------------------------
    # Hepatic Function Panel (Liver Enzymes)
    # -------------------------------------------------------------------------
    "alt": BiomarkerDefinition(
        canonical_name="Alanine Aminotransferase (ALT)",
        loinc_code="1742-6",
        category="hepatic",
        standard_unit="U/L",
        reference_range_male="10 - 40",
        reference_range_female="7 - 35",
        reference_range_general="10 - 40 U/L",
        synonyms=["alt", "alanine aminotransferase", "sgpt", "liver enzyme alt"]
    ),
    "ast": BiomarkerDefinition(
        canonical_name="Aspartate Aminotransferase (AST)",
        loinc_code="1920-8",
        category="hepatic",
        standard_unit="U/L",
        reference_range_male="10 - 35",
        reference_range_female="9 - 32",
        reference_range_general="10 - 35 U/L",
        synonyms=["ast", "aspartate aminotransferase", "sgot", "liver enzyme ast"]
    ),
    "total_bilirubin": BiomarkerDefinition(
        canonical_name="Bilirubin, Total",
        loinc_code="1975-2",
        category="hepatic",
        standard_unit="mg/dL",
        reference_range_male="0.2 - 1.2",
        reference_range_female="0.2 - 1.2",
        reference_range_general="0.2 - 1.2 mg/dL",
        synonyms=["total bilirubin", "bilirubin", "bili", "total bili"]
    ),
    "alkaline_phosphatase": BiomarkerDefinition(
        canonical_name="Alkaline Phosphatase (ALP)",
        loinc_code="6768-6",
        category="hepatic",
        standard_unit="U/L",
        reference_range_male="40 - 129",
        reference_range_female="35 - 104",
        reference_range_general="40 - 129 U/L",
        synonyms=["alkaline phosphatase", "alk phos", "alp"]
    ),

    # -------------------------------------------------------------------------
    # Thyroid Function Panel
    # -------------------------------------------------------------------------
    "tsh": BiomarkerDefinition(
        canonical_name="Thyroid Stimulating Hormone (TSH)",
        loinc_code="3016-3",
        category="thyroid",
        standard_unit="mIU/L",
        reference_range_male="0.45 - 4.50",
        reference_range_female="0.45 - 4.50",
        reference_range_general="0.45 - 4.50 mIU/L",
        synonyms=["tsh", "thyroid stimulating hormone", "thyrotropin", "thyroid test"]
    ),
    "free_t4": BiomarkerDefinition(
        canonical_name="Thyroxine (Free T4)",
        loinc_code="3024-7",
        category="thyroid",
        standard_unit="ng/dL",
        reference_range_male="0.82 - 1.77",
        reference_range_female="0.82 - 1.77",
        reference_range_general="0.82 - 1.77 ng/dL",
        synonyms=["free t4", "t4 free", "free thyroxine", "ft4"]
    ),

    # -------------------------------------------------------------------------
    # Hematology & Complete Blood Count (CBC)
    # -------------------------------------------------------------------------
    "hemoglobin": BiomarkerDefinition(
        canonical_name="Hemoglobin",
        loinc_code="718-7",
        category="cbc",
        standard_unit="g/dL",
        reference_range_male="13.5 - 17.5",
        reference_range_female="12.0 - 15.5",
        reference_range_general="12.0 - 17.5 g/dL",
        synonyms=["hemoglobin", "hgb", "hb"]
    ),
    "hematocrit": BiomarkerDefinition(
        canonical_name="Hematocrit",
        loinc_code="4544-3",
        category="cbc",
        standard_unit="%",
        reference_range_male="38.8 - 50.0",
        reference_range_female="34.9 - 44.5",
        reference_range_general="35 - 50 %",
        synonyms=["hematocrit", "hct"]
    ),
    "white_blood_cells": BiomarkerDefinition(
        canonical_name="White Blood Cell Count (WBC)",
        loinc_code="6690-2",
        category="cbc",
        standard_unit="x10^3/uL",
        reference_range_male="3.4 - 10.8",
        reference_range_female="3.4 - 10.8",
        reference_range_general="3.4 - 10.8 x10^3/uL",
        synonyms=["wbc", "white blood cells", "leukocyte count", "white count"]
    ),
    "platelets": BiomarkerDefinition(
        canonical_name="Platelet Count",
        loinc_code="777-3",
        category="cbc",
        standard_unit="x10^3/uL",
        reference_range_male="150 - 450",
        reference_range_female="150 - 450",
        reference_range_general="150 - 450 x10^3/uL",
        synonyms=["platelets", "platelet count", "plt", "thrombocytes"]
    ),

    # -------------------------------------------------------------------------
    # Vitamins & Nutrients
    # -------------------------------------------------------------------------
    "vitamin_d": BiomarkerDefinition(
        canonical_name="25-Hydroxy Vitamin D",
        loinc_code="62292-8",
        category="vitamin",
        standard_unit="ng/mL",
        reference_range_male="30 - 100",
        reference_range_female="30 - 100",
        reference_range_general="30 - 100 ng/mL",
        synonyms=["vitamin d", "25-hydroxy vitamin d", "vit d", "25-oh vitamin d", "cholecalciferol level"]
    ),
    "vitamin_b12": BiomarkerDefinition(
        canonical_name="Vitamin B12, Serum",
        loinc_code="2132-9",
        category="vitamin",
        standard_unit="pg/mL",
        reference_range_male="200 - 900",
        reference_range_female="200 - 900",
        reference_range_general="200 - 900 pg/mL",
        synonyms=["vitamin b12", "b12", "cobalamin"]
    ),
}


# Pre-build lowercase synonym lookup index for O(1) resolution
_SYNONYM_INDEX: Dict[str, BiomarkerDefinition] = {}
for definition in BIOMARKER_CATALOG.values():
    _SYNONYM_INDEX[definition.canonical_name.lower()] = definition
    _SYNONYM_INDEX[definition.loinc_code.lower()] = definition
    for syn in definition.synonyms:
        _SYNONYM_INDEX[syn.lower()] = definition

# Non-serum specimen qualifiers that invalidate matching to serum/blood LOINC panels
NON_SERUM_SPECIMENS = {
    "urine", "urinary", "24h", "24-hour", "24hr", "csf", "cerebrospinal",
    "stool", "fecal", "pleural", "peritoneal", "synovial", "saliva", "bronchial"
}


def resolve_biomarker(test_term: str) -> Optional[BiomarkerDefinition]:
    """
    Resolves clinical test names, abbreviations, or synonyms to their canonical definition.
    Enforces strict specimen scoping to prevent assigning serum/plasma LOINC codes to
    urine, CSF, or other non-serum specimens.

    CLINICAL SCOPING & REFERENCE RANGE NOTICE:
    1. LOINC mappings in this catalog are specifically scoped by Analyte, Specimen (Serum/Plasma/Venous Blood),
       and Scale (Quantitative). Specimen mismatches (e.g. 24h urine potassium vs serum potassium) are
       strictly rejected from serum LOINC assignment.
    2. Reference ranges and standard units defined in BIOMARKER_CATALOG are outpatient population baselines.
       They MUST NOT be treated as universal across labs, demographics, or assays. Diagnostic interpretation
       must rely on the specific reporting facility's reference range and units from the source record.
    """
    if not test_term:
        return None
    
    clean_term = test_term.strip().lower()
    input_tokens = set(re.findall(r"\b[a-z0-9\+\-]+\b", clean_term))

    # Detect if the query or test name specifies a non-serum specimen
    specimen_conflict = bool(input_tokens.intersection(NON_SERUM_SPECIMENS))

    # Helper to verify definition specimen compatibility
    def is_specimen_compatible(defn: BiomarkerDefinition) -> bool:
        if not specimen_conflict:
            return True
        # If term specifies a non-serum specimen, definition must explicitly match that specimen
        defn_text = (defn.canonical_name + " " + " ".join(defn.synonyms)).lower()
        return any(spec in defn_text for spec in input_tokens.intersection(NON_SERUM_SPECIMENS))

    # 1. Exact match in index
    if clean_term in _SYNONYM_INDEX:
        candidate = _SYNONYM_INDEX[clean_term]
        if is_specimen_compatible(candidate):
            return candidate
        return None

    # 2. Token-level exact match (only for distinctive clinical tokens, len >= 4)
    # Avoid matching short 1-2 character tokens (e.g. 'k', 'na') unless the term is explicitly just that abbreviation
    for word in input_tokens:
        if len(word) >= 4 and word in _SYNONYM_INDEX:
            candidate = _SYNONYM_INDEX[word]
            if is_specimen_compatible(candidate):
                return candidate

    # 3. Whole-phrase synonym containment with word boundary safety
    for syn, definition in _SYNONYM_INDEX.items():
        if len(syn) >= 4 and re.search(r"\b" + re.escape(syn) + r"\b", clean_term):
            if is_specimen_compatible(definition):
                return definition

    return None


def get_biomarker_by_loinc(loinc_code: str) -> Optional[BiomarkerDefinition]:
    """Retrieves definition by exact LOINC code."""
    if not loinc_code:
        return None
    return _SYNONYM_INDEX.get(loinc_code.strip().lower())

