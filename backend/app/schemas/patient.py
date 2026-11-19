from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class EmergencyContactSchema(BaseModel):
    name: str
    relationship: str
    phone: str


class InsuranceProviderSchema(BaseModel):
    providerName: str
    policyNumber: str
    groupNumber: str
    validUntil: str


class PatientBase(BaseModel):
    dateOfBirth: Optional[str] = None
    gender: Optional[str] = "unspecified"
    bloodGroup: Optional[str] = None
    heightCm: Optional[float] = None
    weightKg: Optional[float] = None
    primaryCarePhysician: Optional[str] = None
    emergencyContact: Optional[Dict[str, Any]] = None
    insurance: Optional[Dict[str, Any]] = None
    knownAllergies: List[str] = Field(default_factory=list)


class PatientUpdate(BaseModel):
    dateOfBirth: Optional[str] = None
    gender: Optional[str] = None
    bloodGroup: Optional[str] = None
    heightCm: Optional[float] = None
    weightKg: Optional[float] = None
    primaryCarePhysician: Optional[str] = None
    emergencyContact: Optional[Dict[str, Any]] = None
    insurance: Optional[Dict[str, Any]] = None
    knownAllergies: Optional[List[str]] = None


class PatientResponse(PatientBase):
    id: str
    userId: str

    model_config = ConfigDict(from_attributes=True)


class DiseaseResponse(BaseModel):
    id: str
    name: str
    icdCode: Optional[str] = None
    status: str = "active"
    diagnosedDate: str
    resolvedDate: Optional[str] = None
    treatingDoctor: Optional[str] = None
    sourceReportId: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MedicationResponse(BaseModel):
    id: str
    name: str
    dosage: str
    frequency: str
    route: Optional[str] = "oral"
    startDate: str
    endDate: Optional[str] = None
    status: str = "active"
    prescribingDoctor: Optional[str] = None
    indication: Optional[str] = None
    sourceReportId: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LabResultResponse(BaseModel):
    id: str
    testName: str
    category: str = "metabolic"
    value: str
    unit: str
    referenceRange: str
    status: str = "normal"
    testDate: str
    sourceReportId: Optional[str] = None
    hospitalName: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)




class AnalyteSummarySchema(BaseModel):
    testName: str
    canonicalName: str
    loincCode: Optional[str] = None
    count: int
    latestDate: Optional[str] = None
    latestValue: Optional[str] = None
    unit: Optional[str] = None
    referenceRange: Optional[str] = None
    facilities: List[str] = Field(default_factory=list)


class AnalyteListResponse(BaseModel):
    analytes: List[AnalyteSummarySchema]
