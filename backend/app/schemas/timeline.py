from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ConnectedEntitiesSchema(BaseModel):
    diseases: Optional[List[str]] = Field(default_factory=list)
    medications: Optional[List[str]] = Field(default_factory=list)
    labResults: Optional[List[str]] = Field(default_factory=list)


class TimelineEventBase(BaseModel):
    date: str
    year: int
    title: str
    description: str
    type: str  # 'diagnosis' | 'medication_start' | 'medication_stop' | 'lab_test' | 'imaging' | 'surgery' | 'medical_report' | 'hospital_visit'
    severity: Optional[str] = "medium"
    doctorName: Optional[str] = None
    facility: Optional[str] = None
    sourceReportId: Optional[str] = None
    sourceReportTitle: Optional[str] = None
    connectedEntities: Optional[Dict[str, Any]] = None
    uploadDate: Optional[str] = None
    isUnknownDate: Optional[bool] = False
    hasConflict: Optional[bool] = False
    conflictDetails: Optional[str] = None


class TimelineEventCreate(TimelineEventBase):
    pass


class TimelineEventResponse(TimelineEventBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


class TimelineFacilityResponse(BaseModel):
    facilities: List[str]


class TimelineFilterSummary(BaseModel):
    totalEvents: int
    eventTypes: List[str]
    facilities: List[str]
    years: List[int]
    dateRange: Dict[str, Optional[str]]
