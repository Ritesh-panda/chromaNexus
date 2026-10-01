from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.app.ai.clinical_extractor.models import ExtractedClinicalEntity
from backend.app.ai.extractors.pdf_extractor import ExtractedPage


class ClinicalEntityExtractor(ABC):
    """
    Abstract interface for extracting structured medical entities from clinical text.
    """

    @abstractmethod
    def extract_entities(
        self,
        text: str,
        document_id: str,
        pages: Optional[List[ExtractedPage]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ExtractedClinicalEntity]:
        """Extract structured clinical entities preserving document and page provenance."""
        pass
