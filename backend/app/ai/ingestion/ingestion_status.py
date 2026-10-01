import threading
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class IngestionStage(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    OCR_REQUIRED = "OCR_REQUIRED"
    EXTRACTING = "EXTRACTING"
    INDEXING = "INDEXING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IngestionStatus(BaseModel):
    document_id: str
    status: IngestionStage = IngestionStage.RECEIVED
    progress_percent: int = 0
    current_stage: str = "Document received and queued for processing"
    error_message: Optional[str] = None
    extracted_counts: Dict[str, int] = Field(default_factory=lambda: {
        "diseases": 0,
        "medications": 0,
        "lab_results": 0,
        "procedures": 0
    })
    indexed_chunks_count: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IngestionStatusRegistry:
    """
    Thread-safe live ingestion task status tracker.
    Provides real-time progress polling for frontend upload modals.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(IngestionStatusRegistry, cls).__new__(cls)
                cls._instance._statuses = {}
        return cls._instance

    def set_status(
        self,
        document_id: str,
        stage: IngestionStage,
        progress: int,
        message: str,
        error: Optional[str] = None,
        extracted_counts: Optional[Dict[str, int]] = None,
        indexed_chunks: Optional[int] = None
    ) -> IngestionStatus:
        with self._lock:
            current = self._statuses.get(document_id) or IngestionStatus(document_id=document_id)
            current.status = stage
            current.progress_percent = progress
            current.current_stage = message
            current.error_message = error
            current.updated_at = datetime.now(timezone.utc)

            if extracted_counts is not None:
                current.extracted_counts = extracted_counts
            if indexed_chunks is not None:
                current.indexed_chunks_count = indexed_chunks

            self._statuses[document_id] = current
            return current

    def get_status(self, document_id: str) -> IngestionStatus:
        with self._lock:
            if document_id in self._statuses:
                return self._statuses[document_id]
            return IngestionStatus(
                document_id=document_id,
                status=IngestionStage.COMPLETED,
                progress_percent=100,
                current_stage="Document processed and indexed"
            )


# Global singleton registry
ingestion_registry = IngestionStatusRegistry()
