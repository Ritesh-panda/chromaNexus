from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DoctorQuestionsUpdate(BaseModel):
    questions: List[str] = Field(default_factory=list)


class DoctorSummaryResponse(BaseModel):
    patientName: str
    age: Optional[int] = None
    gender: Optional[str] = None
    bloodGroup: Optional[str] = None
    primaryCarePhysician: Optional[str] = None
    insurance: Optional[Dict[str, Any]] = None
    generatedAt: str
    summaryOverview: str
    currentDiseases: List[Dict[str, Any]] = Field(default_factory=list)
    pastDiseases: List[Dict[str, Any]] = Field(default_factory=list)
    activeMedications: List[Dict[str, Any]] = Field(default_factory=list)
    historicalMedications: List[Dict[str, Any]] = Field(default_factory=list)
    knownAllergies: List[Any] = Field(default_factory=list)
    abnormalLabs: List[Dict[str, Any]] = Field(default_factory=list)
    recentLabs: List[Dict[str, Any]] = Field(default_factory=list)
    proceduresAndImaging: List[Dict[str, Any]] = Field(default_factory=list)
    timelineHighlights: List[Any] = Field(default_factory=list)
    conflictingInformation: List[Dict[str, Any]] = Field(default_factory=list)
    missingDataDisclosures: List[str] = Field(default_factory=list)
    doctorQuestions: List[str] = Field(default_factory=list)
    clinicianNotice: str = (
        "NOTICE TO CLINICIANS: This clinical digest was deterministically compiled from indexed medical "
        "documents on ChronaNexus. It provides longitudinal reference data and does not constitute an automated "
        "diagnosis, treatment recommendation, or prescribing directive. All findings must be clinically verified "
        "with original primary sources."
    )
    riskFactors: List[str] = Field(default_factory=list)
    recentReports: List[Dict[str, Any]] = Field(default_factory=list)
    shareLink: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
