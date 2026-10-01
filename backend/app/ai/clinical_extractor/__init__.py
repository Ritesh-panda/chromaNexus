from typing import Optional
from backend.app.ai.clinical_extractor.models import ExtractedClinicalEntity
from backend.app.ai.clinical_extractor.validator import (
    ClinicalDataValidator,
    ValidatedLab,
    ValidatedMedication,
    ValidatedDisease
)
from backend.app.ai.clinical_extractor.base import ClinicalEntityExtractor
from backend.app.ai.clinical_extractor.rule_based import RuleBasedClinicalExtractor
from backend.app.ai.clinical_extractor.llm_extractor import LLMClinicalExtractor


def get_clinical_extractor(method: str = "hybrid") -> ClinicalEntityExtractor:
    """
    Factory to retrieve configured clinical entity extractor.
    'rule_based', 'llm', or 'hybrid' (LLM with rule-based fallback).
    """
    if method == "rule_based":
        return RuleBasedClinicalExtractor()
    elif method == "llm":
        return LLMClinicalExtractor()
    return LLMClinicalExtractor()


__all__ = [
    "ExtractedClinicalEntity",
    "ClinicalDataValidator",
    "ValidatedLab",
    "ValidatedMedication",
    "ValidatedDisease",
    "ClinicalEntityExtractor",
    "RuleBasedClinicalExtractor",
    "LLMClinicalExtractor",
    "get_clinical_extractor"
]
