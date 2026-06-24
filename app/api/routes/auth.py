from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import register_user, login_user
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new account.
    Password hashed with bcrypt before storage.
    Plain text password never saved anywhere.
    """
    user = register_user(request, db)
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=str(user.created_at),
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email + password.
    Returns JWT token valid for 30 minutes.
    Use as: Authorization: Bearer <access_token>
    """
    return login_user(request, db)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns current user profile.
    Frontend calls this on app load to verify token is still valid.
    Good for: checking if session expired, showing user email in UI.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=str(current_user.created_at),
    )