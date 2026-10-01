from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class CitationSchema(BaseModel):
    reportId: str
    reportTitle: str
    excerpt: str
    date: str
    confidenceScore: float = 0.95


class MessageCreate(BaseModel):
    text: str


class MessageResponse(BaseModel):
    id: str
    sender: str  # 'user' | 'ai'
    text: str
    timestamp: str
    reasoningType: Optional[str] = "fact"
    citations: Optional[List[CitationSchema]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Clinical Conversation"


class ConversationResponse(BaseModel):
    id: str
    title: str
    lastMessageDate: str = "Today"
    messageCount: int = 0

    model_config = ConfigDict(from_attributes=True)

