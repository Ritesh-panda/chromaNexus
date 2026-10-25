"""
ChronaNexus Clinical Terminology Package
Provides LOINC biomarker mapping and drug-allergy cross-reactivity intelligence.
"""

from backend.app.clinical.terminology.biomarkers import (
    BIOMARKER_CATALOG,
    BiomarkerDefinition,
    resolve_biomarker,
    get_biomarker_by_loinc,
)
from backend.app.clinical.terminology.allergies import (
    DRUG_CLASS_CATALOG,
    find_drug_class,
    check_drug_allergy_conflict,
)

__all__ = [
    "BIOMARKER_CATALOG",
    "BiomarkerDefinition",
    "resolve_biomarker",
    "get_biomarker_by_loinc",
    "DRUG_CLASS_CATALOG",
    "find_drug_class",
    "check_drug_allergy_conflict",
]
