from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StructuredQueryType(str, Enum):
    LATEST_VALUE = "latest_value"
    PREVIOUS_AND_LATEST = "previous_and_latest"
    MEASUREMENT_HISTORY = "measurement_history"
    DIRECTION_OF_CHANGE = "direction_of_change"
    COMPARISON_ACROSS_SOURCES = "comparison_across_sources"
    REFERENCE_RANGE_COMPARISON = "reference_range_comparison"
    ALL_INCREASING = "all_increasing"
    ALL_DECREASING = "all_decreasing"
    HIGHEST_VALUE = "highest_value"
    LOWEST_VALUE = "lowest_value"


class TrendDirection(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"
    CONFLICTING = "conflicting"
    INCOMPATIBLE_UNITS = "incompatible_units"
    NOT_FOUND = "not_found"


class TimeWindow(BaseModel):
    days: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    descriptor: Optional[str] = None


class MeasurementPoint(BaseModel):
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


class StructuredQueryIntent(BaseModel):
    is_structured_query: bool = False
    query_type: Optional[StructuredQueryType] = None
    analyte_term: Optional[str] = None
    canonical_name: Optional[str] = None
    loinc_code: Optional[str] = None
    time_window: Optional[TimeWindow] = None
    is_multi_analyte: bool = False
    is_generic_latest: bool = False
    raw_query: str = ""


class StructuredTrendResult(BaseModel):
    query_type: StructuredQueryType
    analyte_name: str
    canonical_name: str
    loinc_code: Optional[str] = None
    latest_measurement: Optional[MeasurementPoint] = None
    previous_measurement: Optional[MeasurementPoint] = None
    all_measurements: List[MeasurementPoint] = Field(default_factory=list)
    trend_direction: TrendDirection
    absolute_change: Optional[float] = None
    percentage_change: Optional[float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    reference_range_status: Optional[str] = None  # 'normal' | 'high' | 'low' | 'unavailable'
    conflicting_measurements: List[MeasurementPoint] = Field(default_factory=list)
    incompatible_units_detected: bool = False
    has_sufficient_data: bool = False
    time_window_applied: Optional[str] = None
    narrative_summary: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    multi_analyte_items: Optional[List[Dict[str, Any]]] = None
