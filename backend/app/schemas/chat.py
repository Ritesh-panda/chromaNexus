from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class CitationSchema(BaseModel):
    reportId: str
    reportTitle: str
    excerpt: str
    date: str
    confidenceScore: float = 0.95
    pageNumber: Optional[int] = None
    facility: Optional[str] = None
    analyte: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None


class MeasurementPointSchema(BaseModel):
    id: str
    test_name: str
    canonical_name: Optional[str] = None
    value: str
    numeric_value: Optional[float] = None
    unit: str
    test_date: str
    facility: str
    source_report_id: Optional[str] = None
    source_report_title: Optional[str] = None
    reference_range: Optional[str] = None
    status: Optional[str] = "normal"
    page_number: Optional[int] = 1


class StructuredTrendSchema(BaseModel):
    query_type: str
    analyte_name: str
    canonical_name: str
    loinc_code: Optional[str] = None
    latest_measurement: Optional[MeasurementPointSchema] = None
    previous_measurement: Optional[MeasurementPointSchema] = None
    all_measurements: List[MeasurementPointSchema] = Field(default_factory=list)
    trend_direction: str
    absolute_change: Optional[float] = None
    percentage_change: Optional[float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    reference_range_status: Optional[str] = None
    conflicting_measurements: List[MeasurementPointSchema] = Field(default_factory=list)
    incompatible_units_detected: bool = False
    has_sufficient_data: bool = False
    time_window_applied: Optional[str] = None
    narrative_summary: str
    citations: List[CitationSchema] = Field(default_factory=list)
    multi_analyte_items: Optional[List[Dict[str, Any]]] = None


class MessageCreate(BaseModel):
    text: str


class MessageResponse(BaseModel):
    id: str
    sender: str  # 'user' | 'ai'
    text: str
    timestamp: str
    reasoningType: Optional[str] = "fact"
    citations: Optional[List[CitationSchema]] = Field(default_factory=list)
    structuredTrend: Optional[StructuredTrendSchema] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Clinical Conversation"


class ConversationResponse(BaseModel):
    id: str
    title: str
    lastMessageDate: str = "Today"
    messageCount: int = 0

    model_config = ConfigDict(from_attributes=True)
