from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.core.security import decode_access_token

# tells FastAPI: token lives in Authorization: Bearer <token> header
# also makes Swagger UI show Authorize button automatically
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
bearer_scheme = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    JWT dependency — replaces verify_api_key on all routes.

    Flow:
      1. extracts JWT from Authorization: Bearer <token> header
      2. decodes + verifies signature and expiry
      3. gets user_id from payload
      4. fetches User from PostgreSQL
      5. returns User object — injected into any route

    Usage in routes:
      current_user: User = Depends(get_current_user)

    Phase 2 extension:
      agents use current_user.id to scope their actions
      "whose repo am I analyzing?"
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token=credentials.credentials
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise credentials_error

    return user

# from fastapi import Security, HTTPException, status
# from fastapi.security import APIKeyHeader
# from app.core.config import get_settings

# settings = get_settings()

# api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# async def verify_api_key(api_key: str = Security(api_key_header)):
#     """
#     FastAPI dependency — add to any route that needs protection.
#     Usage:  router = APIRouter(dependencies=[Depends(verify_api_key)])
    
#     Phase 2 extension: swap this out for JWT + user identity
#     so agents can scope their actions to the authenticated user.
#     """
#     if not api_key or api_key != settings.api_key:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or missing API key. Pass X-API-Key header.",
#         )
#     return api_key
