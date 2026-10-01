from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ExtractedEntitySchema(BaseModel):
    category: str  # 'disease' | 'medication' | 'lab_value' | 'procedure' | 'allergy'
    name: str
    confidence: float = 0.95
    value: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReportBase(BaseModel):
    title: str
    fileName: str
    fileSize: int = 0
    fileType: str = "application/pdf"
    category: str = "blood_report"
    hospitalName: str
    doctorName: Optional[str] = None
    reportDate: str
    status: str = "completed"
    confidenceScore: float = 0.98
    rawText: Optional[str] = None
    summary: Optional[str] = None
    fileUrl: Optional[str] = None


class ReportCreate(BaseModel):
    title: str
    category: str
    hospitalName: str
    doctorName: Optional[str] = None
    reportDate: Optional[str] = None


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    hospitalName: Optional[str] = None
    doctorName: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None


class ReportResponse(ReportBase):
    id: str
    uploadDate: Optional[str] = None
    extractedEntities: List[ExtractedEntitySchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

