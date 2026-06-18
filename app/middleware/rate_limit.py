from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import get_settings

settings = get_settings()

# One limiter instance shared across the app
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Return a clean JSON 429 instead of slowapi's default HTML error."""
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded. Max {settings.rate_limit_per_minute} requests/minute.",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )
