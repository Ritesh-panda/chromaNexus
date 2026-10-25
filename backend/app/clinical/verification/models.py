"""
Phase 6: Evidence-Grounded Assistant & Citation Verification Data Models.
Defines claim types, verification statuses, clinical claims, and grounding results.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    NUMERICAL_LAB = "numerical_lab"
    TEMPORAL_MEASUREMENT = "temporal_measurement"
    DIAGNOSIS = "diagnosis"
    MEDICATION_INSTRUCTION = "medication_instruction"
    NARRATIVE_FINDING = "narrative_finding"
    MISSING_DATA_STATEMENT = "missing_data_statement"
    GENERAL_STATEMENT = "general_statement"


class ClaimVerificationStatus(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"


class ClinicalClaim(BaseModel):
    text: str
    claim_type: ClaimType = ClaimType.GENERAL_STATEMENT
    analyte: Optional[str] = None
    value: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    test_date: Optional[str] = None
    facility: Optional[str] = None
    attributed_source_title: Optional[str] = None
    is_negated: bool = False

    # Verification outcome
    status: ClaimVerificationStatus = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
    verified_value: Optional[str] = None
    verified_unit: Optional[str] = None
    verified_date: Optional[str] = None
    verified_facility: Optional[str] = None
    verified_source_id: Optional[str] = None
    verified_source_title: Optional[str] = None
    supporting_citation: Optional[Dict[str, Any]] = None
    contradiction_details: Optional[str] = None
    explanation: Optional[str] = None


class EvidenceGroundingResult(BaseModel):
    original_answer: str
    verified_answer: str
    claims: List[ClinicalClaim] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning_type: str = "fact"  # 'fact' or 'inference'
    all_supported: bool = True
    has_conflicts: bool = False
    is_abstained: bool = False
