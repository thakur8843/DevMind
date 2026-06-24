from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Float, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum





class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class CodeReview(Base):
    __tablename__ = "code_reviews"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="reviews")
    language = Column(String(32), default="python")
    code_snippet = Column(Text, nullable=False)
    review_result = Column(Text, nullable=True)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    # Phase 2 hook: confidence score for HitL threshold
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ChatHistory(Base):

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="chats")
    role = Column(String(16), nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RequestLog(Base):
    """Middleware writes every request here — useful for debugging + analytics."""
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), index=True)   # UUID
    method = Column(String(10))
    path = Column(String(256))
    status_code = Column(Integer)
    process_time_ms = Column(Float)
    client_ip = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
