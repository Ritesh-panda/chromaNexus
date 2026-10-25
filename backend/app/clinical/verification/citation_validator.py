"""
Phase 6: Citation Validator.
Validates that returned citations are grounded in verified claims.
Enforces attribution precision, provenance preservation, and citation suppression
for absent or unverified data.
"""

from typing import List, Dict, Any, Set
from backend.app.clinical.verification.models import (
    ClaimVerificationStatus,
    ClinicalClaim
)


class CitationValidator:
    """
    Validates and purifies citation links for clinical answers.
    Ensures zero dangling citations, rejects unrelated numerical coincidences,
    and preserves structured provenance metadata.
    """

    def validate_citations(
        self,
        candidate_citations: List[Dict[str, Any]],
        claims: List[ClinicalClaim],
        is_abstained: bool
    ) -> List[Dict[str, Any]]:
        """
        Filters and validates citations against verified claims.
        """
        # If the answer is an abstention or missing data statement, suppress ALL citations
        if is_abstained or not candidate_citations:
            return []

        # Collect report IDs that genuinely support at least one verified claim
        grounded_report_ids: Set[str] = set()
        supporting_metadata_by_id: Dict[str, Dict[str, Any]] = {}

        for claim in claims:
            if claim.status in [ClaimVerificationStatus.SUPPORTED, ClaimVerificationStatus.CONTRADICTED]:
                if claim.verified_source_id:
                    grounded_report_ids.add(claim.verified_source_id)
                    supporting_metadata_by_id[claim.verified_source_id] = {
                        "analyte": claim.analyte,
                        "value": claim.value,
                        "unit": claim.unit,
                        "facility": claim.facility,
                        "date": claim.test_date
                    }
                elif claim.supporting_citation and claim.supporting_citation.get("reportId"):
                    r_id = claim.supporting_citation.get("reportId")
                    grounded_report_ids.add(r_id)
                    supporting_metadata_by_id[r_id] = {
                        "analyte": claim.analyte,
                        "value": claim.value,
                        "unit": claim.unit,
                        "facility": claim.facility,
                        "date": claim.test_date
                    }

        validated_citations: List[Dict[str, Any]] = []
        seen_ids = set()

        for cit in candidate_citations:
            r_id = cit.get("reportId", "")
            if r_id in grounded_report_ids and r_id not in seen_ids:
                seen_ids.add(r_id)
                enriched = dict(cit)
                # Enrich with provenanced metadata if present
                meta = supporting_metadata_by_id.get(r_id, {})
                for k, v in meta.items():
                    if v and not enriched.get(k):
                        enriched[k] = v
                validated_citations.append(enriched)

        return validated_citations
