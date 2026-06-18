from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import get_settings

settings = get_settings()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    FastAPI dependency — add to any route that needs protection.
    Usage:  router = APIRouter(dependencies=[Depends(verify_api_key)])
    
    Phase 2 extension: swap this out for JWT + user identity
    so agents can scope their actions to the authenticated user.
    """
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Pass X-API-Key header.",
        )
    return api_key
