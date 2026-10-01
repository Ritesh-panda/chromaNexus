from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class UserPreferences(BaseModel):
    theme: str = "system"
    language: str = "en"
    notifications: Dict[str, bool] = Field(default_factory=lambda: {
        "email": True,
        "sms": False,
        "criticalAlerts": True,
        "aiDigest": True
    })
    privacy: Dict[str, bool] = Field(default_factory=lambda: {
        "strictDataIsolation": True,
        "localAiProcessingOnly": True,
        "auditableLogsEnabled": True
    })


class UserBase(BaseModel):
    name: str
    email: str
    role: str = "patient"
    avatarUrl: Optional[str] = None
    phoneNumber: Optional[str] = None


class UserCreate(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=6)
    role: str = "patient"


class UserLogin(BaseModel):
    email: str
    password: str
    rememberMe: Optional[bool] = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phoneNumber: Optional[str] = None
    avatarUrl: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    id: str
    preferences: Dict[str, Any]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: Optional[str] = None
