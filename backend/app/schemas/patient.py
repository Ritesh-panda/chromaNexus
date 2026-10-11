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
    dateOfBirth: Optional[str] = "1988-04-12"
    gender: str = "male"
    bloodGroup: str = "O+"
    heightCm: float = 175.0
    weightKg: float = 78.0
    primaryCarePhysician: str = "Dr. Sarah Jenkins, MD"
    emergencyContact: Dict[str, Any] = Field(default_factory=lambda: {
        "name": "Elena Vance",
        "relationship": "Spouse",
        "phone": "+1 (555) 987-6543"
    })
    insurance: Optional[Dict[str, Any]] = Field(default_factory=lambda: {
        "providerName": "BlueCross Shield Pro",
        "policyNumber": "BCS-99281-X",
        "groupNumber": "GRP-8812",
        "validUntil": "2027-12-31"
    })
    knownAllergies: List[str] = Field(default_factory=lambda: [
        "Penicillin (Moderate Rash)",
        "Sulfa Drugs (Anaphylaxis Risk)"
    ])


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


