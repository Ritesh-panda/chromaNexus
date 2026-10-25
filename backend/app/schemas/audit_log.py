from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    id: str
    timestamp: str
    actorId: Optional[str] = None
    patientId: Optional[str] = None
    action: str
    outcome: str
    resourceType: Optional[str] = None
    resourceId: Optional[str] = None
    correlationId: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ipAddress: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    total: int
    items: List[AuditLogResponse]
    logs: Optional[List[AuditLogResponse]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.logs is None:
            self.logs = self.items
