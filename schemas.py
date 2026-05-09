from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ── AUTH ──────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── MEETINGS ──────────────────────────────────
class MeetingResponse(BaseModel):
    id: int
    title: Optional[str]
    language: str
    transcription: Optional[str]
    summary: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True