import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("devmind.errors")


def register_error_handlers(app):
    """
    Register all global exception handlers on the FastAPI app.
    Call this in main.py after app is created.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            f"HTTP {exc.status_code} on {request.method} {request.url.path} "
            f"[{request_id[:8]}]: {exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "request_id": request_id,
                "path": request.url.path,
            },
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "unknown")
        errors = [
            {"field": " → ".join(str(l) for l in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        logger.warning(f"Validation error [{request_id[:8]}]: {errors}")
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed",
                "errors": errors,
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"Unhandled {type(exc).__name__} on {request.method} {request.url.path} "
            f"[{request_id[:8]}]: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error. Check server logs.",
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )
