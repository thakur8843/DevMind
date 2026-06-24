from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    email            = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password  = Column(String(256), nullable=False)
    is_active        = Column(Boolean, default=True, nullable=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    # relationships — lets you do user.reviews in Python
    # back_populates connects to relationship() in review.py
    reviews = relationship("CodeReview", back_populates="user")
    chats   = relationship("ChatHistory", back_populates="user")


# from sqlalchemy import Column, Integer, String, DateTime, Boolean
# from sqlalchemy.sql import func
# from sqlalchemy.orm import relationship
# from app.db.database import Base


# class User(Base):
#     __tablename__ = "users"

#     id            = Column(Integer, primary_key=True, index=True)
#     email         = Column(String(128), unique=True, nullable=False, index=True)
#     hashed_password = Column(String(256), nullable=False)
#     is_active     = Column(Boolean, default=True)
#     created_at    = Column(DateTime(timezone=True), server_default=func.now())

#     # relationship — lets you do user.reviews in Python, no extra query
#     reviews  = relationship("CodeReview", back_populates="user")
#     chats    = relationship("ChatHistory", back_populates="user")