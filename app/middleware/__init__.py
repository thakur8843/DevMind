from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.auth import get_current_user          # ← CHANGED
from app.middleware.error_handler import register_error_handlers

__all__ = [
    "LoggingMiddleware",
    "limiter",
    "rate_limit_exceeded_handler",
    "get_current_user",                                   # ← CHANGED
    "register_error_handlers",
]