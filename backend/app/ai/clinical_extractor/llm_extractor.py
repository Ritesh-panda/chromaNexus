import json
import logging
import re
from typing import List, Dict, Any, Optional
from backend.app.ai.clinical_extractor.base import ClinicalEntityExtractor
from backend.app.ai.clinical_extractor.models import ExtractedClinicalEntity
from backend.app.ai.clinical_extractor.rule_based import RuleBasedClinicalExtractor
from backend.app.ai.clinical_extractor.validator import ClinicalDataValidator
from backend.app.ai.extractors.pdf_extractor import ExtractedPage
from backend.app.ai.llm.base import LLMProvider
from backend.app.ai.llm import get_llm_provider

logger = logging.getLogger(__name__)

CLINICAL_EXTRACTION_SYSTEM_PROMPT = """You are ChronaNexus Clinical Extraction Engine.
Extract all clinical entities strictly documented in the provided medical report text into valid JSON format.

JSON Output Schema:
{
  "diseases": [{"name": "string", "icd_code": "string or null", "status": "active|chronic|resolved"}],
  "medications": [{"name": "string", "dosage": "string", "frequency": "string", "route": "oral|IV"}],
  "lab_results": [{"test_name": "string", "value": "string", "unit": "string", "reference_range": "string"}],
  "procedures": [{"name": "string", "date": "string or null"}]
}

Rules:
1. ONLY extract information explicitly present in the text.
2. Return ONLY the raw JSON object, no markdown, no conversational commentary.
"""


class LLMClinicalExtractor(ClinicalEntityExtractor):
    """
    LLM-powered clinical entity extraction supporting complete multi-page documents
    without arbitrary character truncation, with automatic fallback and hybrid merging.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        fallback_extractor: Optional[ClinicalEntityExtractor] = None
    ):
        self.llm = llm_provider or get_llm_provider()
        self.fallback = fallback_extractor or RuleBasedClinicalExtractor()

    def extract_entities(
        self,
        text: str,
        document_id: str,
        pages: Optional[List[ExtractedPage]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ExtractedClinicalEntity]:
        if not text or len(text.strip()) < 20:
            return self.fallback.extract_entities(text, document_id, pages, metadata)

        all_entities: List[ExtractedClinicalEntity] = []

        try:
            if pages and len(pages) > 0:
                # Process page by page to maintain exact page provenance and prevent context truncation
                for page in pages:
                    p_text = page.text.strip()
                    if len(p_text) < 20:
                        continue
                    page_entities = self._extract_chunk(
                        chunk_text=p_text,
                        document_id=document_id,
                        page_number=page.page_number
                    )
                    all_entities.extend(page_entities)
            else:
                # If pages not provided, process in non-truncated segments if length exceeds 3,500
                segments = self._split_text_into_segments(text, max_len=3500)
                for seg_idx, seg in enumerate(segments, start=1):
                    seg_entities = self._extract_chunk(
                        chunk_text=seg,
                        document_id=document_id,
                        page_number=seg_idx
                    )
                    all_entities.extend(seg_entities)

        except Exception as e:
            logger.info(f"LLM extraction unavailable/failed: {str(e)}. Falling back to rule-based extractor.")
            return self.fallback.extract_entities(text, document_id, pages, metadata)

        # Merge with high-precision rule-based entities to ensure no labs/meds missed
        fallback_entities = self.fallback.extract_entities(text, document_id, pages, metadata)
        if not all_entities:
            return fallback_entities

        return self._deduplicate_entities(all_entities + fallback_entities)

    def _extract_chunk(
        self,
        chunk_text: str,
        document_id: str,
        page_number: int
    ) -> List[ExtractedClinicalEntity]:
        """Extracts entities from a bounded chunk using LLM."""
        prompt = f"CLINICAL REPORT TEXT (Page {page_number}):\n{chunk_text}\n\nExtract all entities into the requested JSON schema:"
        response_text = self.llm.generate(
            prompt=prompt,
            system_instruction=CLINICAL_EXTRACTION_SYSTEM_PROMPT,
            temperature=0.0
        )

        clean_json = response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        parsed = json.loads(clean_json)
        entities: List[ExtractedClinicalEntity] = []

        # 1. Parse Diseases
        for d in parsed.get("diseases", []):
            val_d = ClinicalDataValidator.validate_disease(
                name=d.get("name", ""),
                icd_code=d.get("icd_code"),
                status=d.get("status", "active")
            )
            if val_d.is_valid:
                entities.append(ExtractedClinicalEntity(
                    category="disease",
                    name=val_d.name,
                    value=val_d.icd_code,
                    confidence=0.94,
                    source_document_id=document_id,
                    page_number=page_number,
                    extraction_method="llm",
                    metadata={"icd_code": val_d.icd_code}
                ))

        # 2. Parse Medications
        for m in parsed.get("medications", []):
            val_m = ClinicalDataValidator.validate_medication(
                name=m.get("name", ""),
                dosage=m.get("dosage", ""),
                frequency=m.get("frequency", "Daily")
            )
            if val_m.is_valid:
                entities.append(ExtractedClinicalEntity(
                    category="medication",
                    name=val_m.name,
                    value=val_m.dosage,
                    unit=val_m.frequency,
                    confidence=0.94,
                    source_document_id=document_id,
                    page_number=page_number,
                    extraction_method="llm"
                ))

        # 3. Parse Labs
        for l in parsed.get("lab_results", []):
            val_l = ClinicalDataValidator.validate_lab_result(
                test_name=l.get("test_name", ""),
                value_str=l.get("value", ""),
                unit_str=l.get("unit", ""),
                reference_range=l.get("reference_range", "")
            )
            if val_l.is_valid:
                entities.append(ExtractedClinicalEntity(
                    category="lab_value",
                    name=val_l.test_name,
                    value=val_l.value,
                    unit=val_l.unit,
                    confidence=0.95,
                    source_document_id=document_id,
                    page_number=page_number,
                    extraction_method="llm",
                    metadata={"status": val_l.status}
                ))

        return entities

    def _split_text_into_segments(self, text: str, max_len: int = 3500) -> List[str]:
        """Splits long text cleanly along paragraphs or newlines."""
        if len(text) <= max_len:
            return [text]

        segments: List[str] = []
        start = 0
        while start < len(text):
            end = min(start + max_len, len(text))
            if end < len(text):
                split_at = text.rfind("\n\n", start, end)
                if split_at == -1 or split_at <= start:
                    split_at = text.rfind("\n", start, end)
                if split_at > start:
                    end = split_at
            segments.append(text[start:end].strip())
            start = end
        return [s for s in segments if s]

    def _deduplicate_entities(
        self,
        entities: List[ExtractedClinicalEntity]
    ) -> List[ExtractedClinicalEntity]:
        """Deduplicates extracted entities preserving higher confidence and page provenance."""
        seen = {}
        for ent in entities:
            key = (ent.category, ent.name.strip().lower(), str(ent.value or "").strip().lower(), ent.page_number)
            if key not in seen:
                seen[key] = ent
            else:
                if ent.confidence > seen[key].confidence:
                    seen[key] = ent
        return list(seen.values())
