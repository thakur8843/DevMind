
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class CodeReviewRequest(BaseModel):
    code: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Source code to review"
    )
    language: str = Field(
        default="python",
        max_length=32,
        description="Programming language"
    )
    session_id: Optional[str] = Field(
        default=None,
        max_length=64,
    )

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        allowed = [
            "python", "javascript", "typescript",
            "java", "go", "rust", "cpp", "c",
            "ruby", "php", "swift", "kotlin"
        ]
        if v.lower() not in allowed:
            raise ValueError(f"Language must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("session_id must be alphanumeric with - or _ only")
        return v


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
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
    )
    session_id: str = Field(
        ...,
        max_length=64,
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("session_id must be alphanumeric with - or _ only")
        return v


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[str] = []


class ErrorResponse(BaseModel):
    detail: str
    request_id: Optional[str] = None
    path: Optional[str] = None



# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import datetime


# class CodeReviewRequest(BaseModel):
#     code: str = Field(..., min_length=10, description="Source code to review")
#     language: str = Field(default="python", description="Programming language")
#     session_id: Optional[str] = None


# class CodeReviewResponse(BaseModel):
#     id: int
#     session_id: str
#     language: str
#     review: str
#     status: str
#     created_at: datetime

#     class Config:
#         from_attributes = True


# class ChatRequest(BaseModel):
#     question: str = Field(..., min_length=3)
#     session_id: str


# class ChatResponse(BaseModel):
#     answer: str
#     session_id: str
#     sources: list[str] = []


# class ErrorResponse(BaseModel):
#     detail: str
#     request_id: Optional[str] = None
#     path: Optional[str] = None

