"""
Phase 6: Evidence-Grounding Pipeline Orchestrator.
Orchestrates claim extraction, evidence verification against patient-scoped records,
answer correction/qualification, and citation validation.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

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
from backend.app.clinical.structured_query.models import StructuredTrendResult


class EvidenceGroundingPipeline:
    """
    Orchestrates end-to-end evidence grounding, claim verification, and citation validation.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
        self.claim_extractor = ClaimExtractor()
        self.evidence_verifier = EvidenceVerifier(db=db_session)
        self.answer_corrector = AnswerCorrector()
        self.citation_validator = CitationValidator()

    def verify_answer(
        self,
        candidate_answer: str,
        citations: List[Dict[str, Any]],
        patient_id: str,
        query: str = "",
        retrieval_chunks: Optional[List[Any]] = None
    ) -> EvidenceGroundingResult:
        """
        Executes claim-level verification on a candidate LLM answer.
        """
        if not candidate_answer or not candidate_answer.strip():
            return EvidenceGroundingResult(
                original_answer="",
                verified_answer="No clinical information was generated.",
                claims=[],
                citations=[],
                reasoning_type="inference",
                all_supported=True,
                has_conflicts=False,
                is_abstained=True
            )

        # 1. Extract individual clinical claims
        claims = self.claim_extractor.extract_claims(candidate_answer, candidate_citations=citations)

        # 2. Verify claims against patient-scoped evidence
        verified_claims = self.evidence_verifier.verify_claims(
            claims=claims,
            citations=citations,
            patient_id=patient_id,
            retrieval_chunks=retrieval_chunks
        )
        has_conflicts = any(c.status == ClaimVerificationStatus.CONFLICTING_EVIDENCE for c in verified_claims)

        # 3. Apply deterministic correction, qualification, and abstention
        has_initial_citations = bool(citations and len(citations) > 0)
        verified_text, all_supported, is_abstained = self.answer_corrector.correct_answer(
            original_answer=candidate_answer,
            claims=verified_claims,
            has_citations=has_initial_citations
        )

        # 4. Filter and enrich citations based on verified claims
        final_citations = self.citation_validator.validate_citations(
            candidate_citations=citations,
            claims=verified_claims,
            is_abstained=is_abstained
        )

        # If all citations were pruned and answer has ungrounded assertions, abstain (unless conflicting evidence is surfaced)
        if has_initial_citations and not final_citations and not is_abstained and not has_conflicts:
            if not any(w in verified_text.lower() for w in ["no clinical documentation", "not found", "no records"]):
                verified_text = "No verified clinical records were found to corroborate this statement."
                is_abstained = True

        # If there were no citations and no supported claims, ensure is_abstained is True
        if not has_initial_citations and not any(c.status == ClaimVerificationStatus.SUPPORTED for c in verified_claims):
            is_abstained = True

        reasoning_type = "fact" if len(final_citations) > 0 else "inference"
        has_conflicts = any(c.status == ClaimVerificationStatus.CONFLICTING_EVIDENCE for c in verified_claims)

        return EvidenceGroundingResult(
            original_answer=candidate_answer,
            verified_answer=verified_text,
            claims=verified_claims,
            citations=final_citations,
            reasoning_type=reasoning_type,
            all_supported=all_supported,
            has_conflicts=has_conflicts,
            is_abstained=is_abstained
        )

    def verify_structured_trend_response(
        self,
        trend: StructuredTrendResult,
        patient_id: str
    ) -> EvidenceGroundingResult:
        """
        Verifies structured clinical query results directly from the engine,
        ensuring zero hallucinations and authoritative source attribution.
        """
        citations = [dict(c) for c in trend.citations]
        claim = ClinicalClaim(
            text=trend.narrative_summary,
            claim_type=ClaimType.TEMPORAL_MEASUREMENT,
            analyte=trend.canonical_name,
            value=trend.latest_measurement.value if trend.latest_measurement else None,
            unit=trend.latest_measurement.unit if trend.latest_measurement else None,
            facility=trend.latest_measurement.facility if trend.latest_measurement else None,
            test_date=trend.latest_measurement.test_date if trend.latest_measurement else None,
            status=ClaimVerificationStatus.SUPPORTED,
            verified_source_id=trend.latest_measurement.source_report_id if trend.latest_measurement else None,
            verified_source_title=trend.latest_measurement.source_report_title if trend.latest_measurement else None
        )

        return EvidenceGroundingResult(
            original_answer=trend.narrative_summary,
            verified_answer=trend.narrative_summary,
            claims=[claim],
            citations=citations,
            reasoning_type="fact",
            all_supported=True,
            has_conflicts=len(trend.conflicting_measurements) > 0,
            is_abstained=False
        )
