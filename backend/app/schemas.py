from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "citizen"  # citizen | officer | admin (admin should be seeded, not self-registered)
    department: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Complaints ----------
class ComplaintCreate(BaseModel):
    title: str
    description: str
    complaint_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area: Optional[str] = None


class AIAnalysis(BaseModel):
    category: str
    department: str
    priority: str
    summary: str
    sentiment: str
    score: float


class ComplaintOut(BaseModel):
    id: int
    complaint_code: str
    title: str
    description: str
    complaint_type: str
    image_path: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area: Optional[str] = None
    ai_category: Optional[str] = None
    ai_department: Optional[str] = None
    ai_priority: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_sentiment: Optional[str] = None
    ai_score: Optional[float] = None
    status: str
    duplicate_of_id: Optional[int] = None
    support_count: int
    citizen_id: int
    assigned_officer_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DuplicateWarning(BaseModel):
    is_duplicate: bool
    existing_complaint: Optional[ComplaintOut] = None
    similarity: Optional[float] = None


class StatusUpdate(BaseModel):
    status: str
    remarks: Optional[str] = None


class FeedbackCreate(BaseModel):
    rating: int
    comment: Optional[str] = None


class ChatQuery(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
