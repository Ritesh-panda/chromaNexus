from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ExtractedClinicalEntity(BaseModel):
    category: str  # 'disease' | 'medication' | 'lab_value' | 'procedure' | 'vital_sign' | 'allergy'
    name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    confidence: float = 0.95
    source_document_id: str = ""
    page_number: int = 1
    excerpt: str = ""
    extraction_method: str = "rule_based"  # 'rule_based' | 'llm' | 'hybrid'
    metadata: Dict[str, Any] = Field(default_factory=dict)
