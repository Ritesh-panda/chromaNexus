import json
import logging
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
    LLM-powered clinical entity extraction with automatic fallback to RuleBasedClinicalExtractor.
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
        # If text is too short, return fallback
        if not text or len(text.strip()) < 30:
            return self.fallback.extract_entities(text, document_id, pages, metadata)

        # Attempt LLM extraction
        try:
            prompt = f"CLINICAL REPORT TEXT:\n{text[:3000]}\n\nExtract all entities into the requested JSON schema:"
            response_text = self.llm.generate(
                prompt=prompt,
                system_instruction=CLINICAL_EXTRACTION_SYSTEM_PROMPT,
                temperature=0.0
            )

            # Strip possible markdown code blocks
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
                        extraction_method="llm",
                        metadata={"status": val_l.status}
                    ))

            # If LLM returned results, return them. Otherwise combine with fallback.
            if entities:
                return entities

        except Exception as e:
            logger.info(f"LLM extraction fallback to rule-based: {str(e)}")

        # Fallback to rule-based extractor
        return self.fallback.extract_entities(text, document_id, pages, metadata)
