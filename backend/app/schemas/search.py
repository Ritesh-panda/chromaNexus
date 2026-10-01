from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    type: str  # 'report' | 'disease' | 'timeline' | 'medication'
    route: str


class GlobalSearchResponse(BaseModel):
    query: str
    totalMatches: int
    reports: List[Dict[str, Any]] = Field(default_factory=list)
    diseases: List[Dict[str, Any]] = Field(default_factory=list)
    timelineEvents: List[Dict[str, Any]] = Field(default_factory=list)
    medications: List[Dict[str, Any]] = Field(default_factory=list)
