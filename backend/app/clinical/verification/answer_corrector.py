"""
Phase 6: Answer Corrector.
Transforms candidate answers based on verification outcomes:
preserves supported claims, corrects false attributions and numerical errors when authoritative,
surfaces conflicting multi-facility evidence, qualifies or rewrites unsupported claims,
and safely abstains when evidence is absent.
"""

import re
from typing import List, Dict, Any, Tuple

from backend.app.clinical.verification.models import (
    ClaimType,
    ClaimVerificationStatus,
    ClinicalClaim
)


class AnswerCorrector:
    """
    Applies deterministic correction, qualification, and abstention rules to candidate answers.
    """

    GENERIC_STOPWORDS = {
        "patient", "health", "metro", "hospital", "reference", "ref", "date",
        "high", "normal", "low", "result", "results", "test", "level", "panel",
        "report", "documented", "diagnostic", "outpatient", "oral", "daily",
        "your", "yours", "were", "with", "from", "also", "have", "has", "had", "been",
        "these", "this", "that", "excerpt", "page", "labs", "count", "blood", "intake",
        "records", "record", "found", "provided", "files", "data", "claim", "unverified",
        "according", "complete", "order", "profile", "screening", "study", "exam",
        "examination", "note", "notes", "encounter", "findings", "history", "clinical",
        "the", "was", "is", "are", "you", "and", "but", "also", "for", "about",
        "diagnosed", "take", "taking", "start", "stop", "should", "prescribed", "mg"
    }

    def correct_answer(
        self,
        original_answer: str,
        claims: List[ClinicalClaim],
        has_citations: bool
    ) -> Tuple[str, bool, bool]:
        """
        Synthesizes the corrected answer.
        Returns: (verified_answer_text, all_supported_flag, is_abstained_flag)
        """
        if not claims:
            return original_answer, True, False

        # Check if entire answer is an explicit missing data statement
        if all(c.claim_type == ClaimType.MISSING_DATA_STATEMENT for c in claims):
            return original_answer, True, True

        supported_claims = [c for c in claims if c.status == ClaimVerificationStatus.SUPPORTED]
        reconciled_claims = [c for c in claims if c.status == ClaimVerificationStatus.CONTRADICTED and c.verified_source_title]
        conflicting_claims = [c for c in claims if c.status == ClaimVerificationStatus.CONFLICTING_EVIDENCE]
        unsupported_claims = [c for c in claims if c.status == ClaimVerificationStatus.INSUFFICIENT_EVIDENCE or (c.status == ClaimVerificationStatus.CONTRADICTED and not c.verified_source_title)]

        # Case 1: All claims unsupported and no citations available -> Clean Abstention
        if not supported_claims and not conflicting_claims and not reconciled_claims:
            abstention_text = "No clinical documentation matching your request was found in your verified medical records."
            return abstention_text, False, True

        reconstructed_sentences: List[str] = []

        for claim in claims:
            # 1. Supported Claim
            if claim.status == ClaimVerificationStatus.SUPPORTED:
                reconstructed_sentences.append(claim.text)
                continue

            # 2. Conflicting Evidence
            if claim.status == ClaimVerificationStatus.CONFLICTING_EVIDENCE:
                reconstructed_sentences.append(
                    f"Your records show conflicting results across different clinical reports for {claim.analyte or 'this test'}. "
                    "Both measurements are preserved accurately from their respective facilities."
                )
                continue

            # 3. Contradicted False Source Attribution
            if claim.status == ClaimVerificationStatus.CONTRADICTED and claim.verified_source_title:
                # Find phrase like "In the [Title]" or replace attributed_source_title
                corrected_text = claim.text
                if claim.attributed_source_title and claim.attributed_source_title.lower() in claim.text.lower():
                    corrected_text = re.sub(
                        re.escape(claim.attributed_source_title),
                        claim.verified_source_title,
                        claim.text,
                        flags=re.IGNORECASE
                    )
                else:
                    m_rep_in = re.search(r"\b(?:in|from|according to)\s+(?:the\s+)?([A-Za-z0-9\s\-&]+?(?:Report|Panel|Profile|Screening|Analysis|Summary))", claim.text, re.IGNORECASE)
                    if m_rep_in:
                        corrected_text = claim.text[:m_rep_in.start(1)] + claim.verified_source_title + claim.text[m_rep_in.end(1):]
                    else:
                        corrected_text = f"According to {claim.verified_source_title}, {claim.text}"
                reconstructed_sentences.append(corrected_text)
                continue

            # 4. Contradicted Value with Authoritative Ground Truth
            if claim.status == ClaimVerificationStatus.CONTRADICTED and claim.verified_value and claim.value:
                # Correct wrong value if authoritative
                corrected_text = re.sub(
                    r"\b" + re.escape(claim.value) + r"\b",
                    claim.verified_value,
                    claim.text
                )
                reconstructed_sentences.append(corrected_text)
                continue

            # 5. Unsupported Diagnosis Claim
            if claim.claim_type == ClaimType.DIAGNOSIS:
                diag_term = claim.analyte or "the specified condition"
                reconstructed_sentences.append(
                    f"No clinical documentation of {diag_term} was found in the provided records."
                )
                continue

            # 6. Unsupported Medication Instruction
            if claim.claim_type == ClaimType.MEDICATION_INSTRUCTION:
                reconstructed_sentences.append(
                    "No clinical documentation supporting the specified medication modification was found in the provided records."
                )
                continue

            # 7. Narrative finding or general unsupported claim: Safe Qualification
            claim_words = [w for w in re.findall(r"[a-zA-Z]{3,}", claim.text.lower()) if w not in self.GENERIC_STOPWORDS]
            target_str = " ".join(claim_words) if claim_words else (claim.analyte or "the specified clinical findings")
            reconstructed_sentences.append(
                f"No clinical documentation of {target_str} was found in the provided records."
            )

        final_text = " ".join(reconstructed_sentences).strip()
        all_supported = (len(unsupported_claims) == 0 and len(conflicting_claims) == 0)

        # Defense-in-depth: if citations are absent and text contains affirmative clinical assertions, abstain
        if not has_citations and not any(w in final_text.lower() for w in ["no clinical documentation", "not found", "no records"]):
            final_text = "No verified clinical records were found to corroborate this statement."
            all_supported = False

        return final_text, all_supported, False
