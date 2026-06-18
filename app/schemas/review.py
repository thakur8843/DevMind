from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CodeReviewRequest(BaseModel):
    code: str = Field(..., min_length=10, description="Source code to review")
    language: str = Field(default="python", description="Programming language")
    session_id: Optional[str] = None


class CodeReviewResponse(BaseModel):
    id: int
    session_id: str
    language: str
    review: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3)
    session_id: str


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[str] = []


class ErrorResponse(BaseModel):
    detail: str
    request_id: Optional[str] = None
    path: Optional[str] = None
