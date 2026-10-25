"""
Phase 6: Evidence-Grounded Assistant & Citation Verification Package.
"""

from backend.app.clinical.verification.models import (
    ClaimType,
    ClaimVerificationStatus,
    ClinicalClaim,
    EvidenceGroundingResult
)
from backend.app.clinical.verification.claim_extractor import ClaimExtractor
from backend.app.clinical.verification.evidence_verifier import EvidenceVerifier
from backend.app.clinical.verification.answer_corrector import AnswerCorrector
from backend.app.clinical.verification.citation_validator import CitationValidator
from backend.app.clinical.verification.pipeline import EvidenceGroundingPipeline

__all__ = [
    "ClaimType",
    "ClaimVerificationStatus",
    "ClinicalClaim",
    "EvidenceGroundingResult",
    "ClaimExtractor",
    "EvidenceVerifier",
    "AnswerCorrector",
    "CitationValidator",
    "EvidenceGroundingPipeline"
]
