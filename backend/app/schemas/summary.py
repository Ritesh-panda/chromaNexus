from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DoctorSummaryResponse(BaseModel):
    patientName: str
    age: int
    gender: str
    generatedAt: str
    summaryOverview: str
    currentDiseases: List[Dict[str, Any]] = Field(default_factory=list)
    pastDiseases: List[Dict[str, Any]] = Field(default_factory=list)
    activeMedications: List[Dict[str, Any]] = Field(default_factory=list)
    knownAllergies: List[str] = Field(default_factory=list)
    abnormalLabs: List[Dict[str, Any]] = Field(default_factory=list)
    riskFactors: List[str] = Field(default_factory=list)
    recentReports: List[Dict[str, Any]] = Field(default_factory=list)
    timelineHighlights: List[str] = Field(default_factory=list)
    shareLink: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

